# Development

How the integration is built, how to test it, and how to publish a version.
For the Koolnova API see [API.md](API.md); for usage problems, [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Architecture

The integration is `custom_components/koolnova/`: one module per Home Assistant platform
(`climate`, `sensor`, `switch`, `binary_sensor`), a `coordinator.py` that does the polling, a
`config_flow.py` for setup and options, `const.py` for limits and the Koolnova code <-> HA mode
mappings, `brand/` (see its README) and `koolnova_api/`, the vendored REST client (`client.py`,
`session.py`, `const.py`, `exceptions.py`). `manifest.json`'s version must match the git tag.

### Vendored API client — the import rule

`koolnova_api/` is a local fork of the `koolnova-api` client (credit to the original author). It
lives inside the repository and is **not** a PyPI dependency: the PyPI package name collided with
the local module and made every call fail with 404.

```python
from .koolnova_api.client import KoolnovaAPIRestClient   # ✅
import koolnova_api.client                               # ❌ absolute import breaks the integration
```

Never use an absolute `koolnova_api` import, and never add the PyPI package to `manifest.json`. After touching imports, clear the Python cache (`__pycache__`) before testing.

### Entity scopes

`climate.py` exposes three classes that translate through the mappings in `const.py`
(`KOOLNOVA_TO_HVAC_MODE`, `KOOLNOVA_ZONE_STATUS_TO_HVAC`, `KOOLNOVA_TO_FAN` and their
inverses; the project one, `HVAC_TO_KOOLNOVA_MODE_CANDIDATES`, is written by hand because several
codes share an HA mode, and `mode_code_for` picks the code from the project's `TopicModes`):

- `KoolnovaProjectEntity` — the whole project: global HVAC mode, ECO, stop.
- `KoolnovaZoneEntity` — one per sensor/room: setpoint, status, fan speed.
- `KoolnovaHubEntity` — one per **legacy hub** (only created when the account has a hub): ON/OFF as
  HVACMode AUTO/OFF plus the behavior mode (manual / auto / planning). Backed by the
  reverse-engineered endpoints in `docs/API.md#hub--legacy-controller-endpoints`.

`binary_sensor.py` adds one `KoolnovaConnectivitySensor` per project (online/offline), on top of the
connectivity `SensorEntity` in `sensor.py` that also reports RSSI and per-room last-update.

### Two polling rates

The coordinator refreshes **sensors** every cycle, but the (more expensive) **project** list only
every `project_update_frequency` cycles, caching the rest (`DEFAULT_PROJECT_UPDATE_FREQUENCY` in
`const.py`).

After a project mode change (`async_update_project_data` with `mode`), the cycles read the
**projects instead of the sensors** (same number of requests) until the system reports the
requested mode or `MODE_CHANGE_TIMEOUT` passes. Meanwhile the requested mode stays in the cache
and the project entity's `pending_mode` attribute shows it; on timeout the real mode is shown and
a persistent notification is created. These cycles fire `koolnova_update_completed` with
`update_type: "projects_only"`.

Option changes (interval, offered modes, temperature range) reload the coordinator's configuration
without reloading the whole config entry (`async_reload_entry` in `__init__.py`).

### Limits imposed by Koolnova

Koolnova bans your IP automatically if their API is polled too often, and also on repeated failed
logins (the exact rate is in [API.md](API.md)). Hence `MIN_UPDATE_INTERVAL` (`const.py`; the
coordinator clamps older, more aggressive configurations to it) and `AUTH_FAILURE_COOLDOWN`
(`koolnova_api/const.py`), a cooldown after a failed login. **Do not lower them.**

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

**Never put real credentials in a test.**

`tests/test_sensor.py` and `tests/test_climate.py` cover the sensor and climate platforms (entity
creation, late-reporting zones, availability, service-call failures) and the coordinator cache
with fakes, but need Home Assistant itself, so they skip where HA isn't installed (including CI).
Run them inside the HA container, each as its own process (other modules stub
`custom_components` in `sys.modules`): copy `tests/` and `custom_components/` to a scratch dir in
the container and run `python -m unittest tests.test_sensor -v` from there, e.g. with
`kubectl -n homelab exec deploy/homeassistant -c homeassistant -- …` and `kubectl cp`.

`config_flow.py` is not covered: it needs a live Home Assistant instance and a real Koolnova
account to mean anything.

## Test environment

Home Assistant runs in the cluster (`deploy/homeassistant` in namespace `homelab`, container
`homeassistant`; its `/config` is a PVC). The integration under test lives in
`/config/custom_components/koolnova` inside that container: copy your changes there, then restart
HA with `kubectl -n homelab rollout restart deploy/homeassistant`.

### Before pushing

1. Restart HA (above).
2. No errors in `kubectl -n homelab logs deploy/homeassistant` or in `home-assistant.log`.
3. Setup from the UI works.
4. The `climate.koolnova_*` entities respond: temperature, mode and fan.

### Verifying Lovelace rendering with Playwright

The unit suite cannot exercise the Lovelace dashboard, and visual bugs there are expensive to chase
blind (e.g. `stack` is **not** a valid card type — the registered type is `vertical-stack`). When a
dashboard change must be verified, render it headlessly with Playwright instead of asking the user
to reload. Needs Playwright with a Chromium (the system `/usr/bin/chromium` via `executable_path`, launched
headless with `--no-sandbox --disable-gpu --disable-dev-shm-usage`) and a long-lived HA token.
Log in without the UI by injecting `hassTokens` into `localStorage` through `add_init_script`
(`hassUrl`, `clientId`, `access_token`, `refresh_token`, far-future `expires`, `token_type`),
open the dashboard URL with `wait_until="domcontentloaded"`, wait for the cards to render, and
screenshot or read them.

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
> fails with `Downloading … failed with (No content to download)`. Tag `vX.Y.Z` ↔ version `X.Y.Z`
> (the `v` prefix belongs to the tag only). Never publish a release whose tag or name does not
> match the manifest version: it becomes "latest" and breaks installs for everyone.

1. Bump `"version"` in `custom_components/koolnova/manifest.json`.
2. Add the matching entry to [CHANGELOG.md](../CHANGELOG.md).
3. `git commit -m "vX.Y.Z: …"`
4. `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. `git push origin main --tags`
6. Create the GitHub release from that tag, with no custom assets.

### `hacs.json`

Only a small set of keys is allowed (see the current `hacs.json`). Integration metadata (`domain`,
`config_flow`, `iot_class`, `integration_type`…) belongs in `manifest.json`; putting it here makes
the `hacsjson` check fail with *extra keys not allowed*.

