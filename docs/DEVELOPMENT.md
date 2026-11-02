# Development

How the integration is built, how to test it, and how to publish a version.
For the Koolnova API see [API.md](API.md); for usage problems, [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Architecture

```
custom_components/koolnova/
├── __init__.py        config entry setup/unload, creates the coordinator
├── config_flow.py     UI setup (credentials) and options
├── const.py           DOMAIN, limits, Koolnova code <-> HA mode mappings
├── coordinator.py     DataUpdateCoordinator: does the polling
├── climate.py         entities: project (global) and zone (per room)
├── sensor.py          per-zone humidity and CO2 sensors (created when a zone starts reporting)
├── manifest.json      version must match the git tag
├── brand/             icon and logo served by HA (see its README)
└── koolnova_api/      vendored REST client
    ├── client.py      get_project, get_sensors, update_sensor, update_project
    ├── session.py     login and token lifecycle
    ├── const.py       URLs and required headers
    └── exceptions.py  KoolnovaError
```

### Vendored API client — the import rule

`koolnova_api/` is a local fork of the `koolnova-api` client (credit to the original author). It
lives inside the repository and is **not** a PyPI dependency, because the `koolnova-api` package
(hyphen) collided with the local module — previously named `koolnovaapi` (no separator) — and
caused 404 errors on every call.

```python
from .koolnova_api.client import KoolnovaAPIRestClient   # ✅
from koolnovaapi.client import KoolnovaAPIRestClient     # ❌ breaks the integration
```

Never reintroduce an absolute `koolnova_api` import, and never add the PyPI package to
`manifest.json`. After touching imports, clear the Python cache (`__pycache__`) before testing.

### Entity scopes

`climate.py` exposes classes that translate through the mappings in `const.py`
(`KOOLNOVA_TO_HVAC_MODE`, `KOOLNOVA_ZONE_STATUS_TO_HVAC`, `KOOLNOVA_TO_FAN` and their
auto-generated inverses):

- `KoolnovaProjectEntity` — the whole project: global HVAC mode, ECO, stop.
- `KoolnovaZoneEntity` — one per sensor/room: setpoint, status, fan speed.
- `KoolnovaHubEntity` — one per **legacy hub** (only created when the account has a hub): ON/OFF as
  HVACMode AUTO/OFF plus the behavior mode (manual / auto / planning). Backed by the
  reverse-engineered endpoints in `docs/API.md#hub--legacy-controller-endpoints`.

`binary_sensor.py` adds one `KoolnovaConnectivitySensor` per project (online/offline), on top of the
connectivity `SensorEntity` in `climate.py` that also reports RSSI and per-room last-update.

### Two polling rates

The coordinator refreshes **sensors** every cycle, but the (more expensive) **project** list only
every `project_update_frequency` cycles, caching the rest (`DEFAULT_PROJECT_UPDATE_FREQUENCY` = 10
in `const.py`).

Option changes (interval, offered modes, temperature range) reload the coordinator's configuration
without reloading the whole config entry (`async_reload_entry` in `__init__.py`).

### Limits imposed by Koolnova

Koolnova bans your IP automatically if their API is polled more often than once every 30 s, and
also on repeated failed logins. Hence `MIN_UPDATE_INTERVAL` is 30 s (the coordinator clamps older,
more aggressive configurations to it) and a 300 s cooldown exists after a failed login. **Do not
lower these limits.**

## Tests

The vendored client is covered by `tests/`, which runs on the standard library alone — no pytest,
no Home Assistant install:

```bash
python3 -m unittest discover -s tests -t . -v
```

Every HTTP call is mocked. The suite pins down the things that have actually broken in production:
the `email` login field, the browser headers, `PUT` vs `PATCH` per endpoint, the auth-failure
cooldown, the code tables, the retry/backoff and 401-refresh behaviour of `rest_request`, and the
hub endpoints. CI runs it on every push (`.github/workflows/validate.yml`).

`tests/test_integration.py` goes a step further: it points the real client + session at a local
`http.server` (no mocks on `requests.Session`) and exercises login, the 401 refresh and the retry
paths over a real socket. It still never touches api.koolnova.com, so no credentials are involved.

**Never put real credentials in a test.** An earlier `tests/` directory held API exploration
scripts with a plaintext password and had to be purged from git history in v1.2.6.

`tests/test_sensor.py` covers the sensor platform (entity creation, late-reporting zones, availability)
and the coordinator cache with a fake coordinator, but it needs Home Assistant itself, so it skips
where HA isn't installed (including CI). Run it inside the HA container, as a separate process:

```bash
docker exec homeassistant rm -rf /tmp/kr && docker exec homeassistant mkdir /tmp/kr
docker cp tests homeassistant:/tmp/kr/tests && docker cp custom_components homeassistant:/tmp/kr/custom_components
docker exec -w /tmp/kr homeassistant python -m unittest tests.test_sensor -v
```

The rest of the HA side (`climate.py`, `config_flow.py`) is not covered: it needs a live Home
Assistant instance and a real Koolnova account to mean anything.

## Test environment

Development happens against a Home Assistant instance in Docker, editing the integration directly
in its configuration directory:

```bash
$HOME/docker/homeassistant/config/custom_components/koolnova
docker restart homeassistant
```

### Before pushing

1. `docker restart homeassistant`
2. No errors in `docker logs homeassistant` or in `home-assistant.log`.
3. Setup from the UI works.
4. The `climate.koolnova_*` entities respond: temperature, mode and fan.

### Verifying Lovelace rendering with Playwright

The unit suite cannot exercise the Lovelace dashboard, and visual bugs there are expensive to chase
blind (e.g. `stack` is **not** a valid card type — the registered type is `vertical-stack`). When a
dashboard change must be verified, render it headlessly with Playwright instead of asking the user
to reload:

```python
# Requires: pip install playwright, a chromium (e.g. /usr/bin/chromium), and
# a long-lived HA token. Injects hassTokens so no login is needed.
import json, time
from playwright.sync_api import sync_playwright

TOKEN = open("/home/admin/.config/ha-token").read().strip()
BASE = "http://localhost:8123"  # or the Pi's LAN IP

tokens = {
    "hassUrl": BASE, "clientId": BASE + "/",
    "access_token": TOKEN, "refresh_token": TOKEN,
    "expires": int(time.time() * 1000) + 10 * 365 * 24 * 3600 * 1000,
    "token_type": "Bearer",
}
init = f"localStorage.setItem('hassTokens', JSON.stringify({json.dumps(tokens)}))"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", headless=True,
                                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    ctx = browser.new_context()
    ctx.add_init_script(init)
    page = ctx.new_page()
    page.goto(f"{BASE}/control-timbre/clima", wait_until="domcontentloaded")
    page.wait_for_timeout(15000)
    # Walk shadow DOM (DocumentFragment shadow roots have nodeType 11) to read cards.
    page.screenshot(path="/tmp/ha_dash.png")
    browser.close()
```

Two gotchas that cost real debugging time:

- **Shadow roots are `DocumentFragment` (nodeType 11).** A walker that only descends into element
  and text nodes finds *nothing* inside web components — descend into every `node.shadowRoot` and
  iterate `childNodes` for fragments too. `document.querySelector("hui-view")` never pierces shadow
  DOM either.
- **A broken card type renders `HUI-ERROR-CARD` with "Error de configuración".** The error string
  `unknown type encountered: X` means `X` is not a registered Lovelace card type in this HA version
  (`stack` → use `vertical-stack`; `tile`/`grid`/`thermostat` are valid). Count `HUI-ERROR-CARD`
  nodes and dump their text to see exactly which card failed and why.

Entity-state relabels for custom entities follow the same rule: the frontend looks up
`component.<platform>.entity.<domain>.<translation_key>.state.<state>` (the `entity` category), so
the override must live under `"entity": {"climate": {"<translation_key>": {"state": {...}}}}` in
`strings.json` / `translations/*.json` — placing it under `entity_component` is silently ignored.

## Publishing a release

HACS installs straight from the GitHub repository, so the root must keep the standard shape:
`custom_components/koolnova/`, `hacs.json` and `README.md` where they are, with no ZIPs and no
`zip_release`.

> **The tag and the `"version"` field in `manifest.json` must be identical.** If they differ, HACS
> fails with `Downloading … failed with (No content to download)`. Tag `v1.3.2` ↔ version `1.3.2`
> (the `v` prefix belongs to the tag only). Never publish a release whose tag or name does not
> match the manifest version: it becomes "latest" and breaks installs for everyone.

1. Bump `"version"` in `custom_components/koolnova/manifest.json`.
2. Add the matching entry to [CHANGELOG.md](../CHANGELOG.md).
3. `git commit -m "vX.Y.Z: …"`
4. `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. `git push origin main --tags`
6. Create the GitHub release from that tag, with no custom assets.

### `hacs.json`

Only a small set of keys is allowed. Integration metadata (`domain`, `config_flow`, `iot_class`,
`integration_type`…) belongs in `manifest.json`; putting it here makes the `hacsjson` check fail
with *extra keys not allowed*.

```json
{
  "name": "Koolnova",
  "homeassistant": "2025.12.0",
  "render_readme": true,
  "country": ["ES"],
  "hide_default_branch": false
}
```
