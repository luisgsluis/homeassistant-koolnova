# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A custom Home Assistant integration (HACS) for Koolnova HVAC systems. It talks to the (undocumented,
reverse-engineered) Koolnova cloud REST API at `https://api.koolnova.com/` to expose zones and the
global project as `climate` entities.

## Repository layout (HACS-required shape)

```
custom_components/koolnova/   ← the actual integration (domain "koolnova")
├── __init__.py                setup/unload of the config entry, wires the coordinator
├── config_flow.py             UI config flow (credentials + options)
├── const.py                   DOMAIN, defaults/limits, HVAC/fan code<->HA mappings
├── coordinator.py             DataUpdateCoordinator: polls projects + sensors
├── climate.py                 KoolnovaProjectEntity (global) + KoolnovaZoneEntity (per room)
├── manifest.json              version MUST match the git tag (see Releases below)
├── strings.json / translations/  config flow i18n (en, es)
└── koolnova_api/               vendored REST client (no PyPI dependency, see below)
    ├── client.py               KoolnovaAPIRestClient: get_project, get_sensors, update_sensor, update_project
    ├── session.py              auth/session handling, token lifecycle
    ├── exceptions.py           KoolnovaError
    └── const.py                COMMON_HEADERS / PATCH_HEADERS required by the API
hacs.json                      HACS metadata, "domain" MUST match manifest.json
docs/                          architecture, API reference, release process, troubleshooting
```

Root must stay HACS-standard: no custom zips, no `zip_release`. HACS installs straight from the
GitHub repo/release, so `custom_components/koolnova/`, `hacs.json`, and `README.md` must exist at
the paths shown above.

## Architecture notes that span multiple files

- **Vendored API client, not a PyPI package.** `koolnova_api/` used to be installed from PyPI as
  `koolnova-api` (hyphen), which collided with the local module `koolnovaapi` and caused 404s. It is
  now a local package named `koolnova_api` (underscore), imported only via relative imports
  (`from .koolnova_api.client import ...`). Never reintroduce an absolute `import koolnova_api` or
  add the PyPI package as a dependency — see `docs/ARCHITECTURE.md` and `docs/TROUBLESHOOTING.md`.
- **Two entity scopes.** `climate.py` has `KoolnovaProjectEntity` (controls the whole project: global
  HVAC mode, eco, stop) and `KoolnovaZoneEntity` (one per sensor/room: setpoint, status, fan speed).
  Both translate through the code maps in `const.py` (`KOOLNOVA_TO_HVAC_MODE`,
  `KOOLNOVA_ZONE_STATUS_TO_HVAC`, `KOOLNOVA_TO_FAN` and their auto-generated inverses).
- **Coordinator does two polling rates.** `coordinator.py` refreshes sensors on every update but only
  refreshes the (more expensive) project list every `project_update_frequency` cycles, caching the
  rest — see `DEFAULT_PROJECT_UPDATE_FREQUENCY` in `const.py`.
  Options changes (interval, HVAC modes offered, temp range) reload the coordinator's config without a
  full entry reload (`async_reload_entry` in `__init__.py`).
- **The API is brittle and undocumented.** It requires browser-like headers on every request
  (`User-Agent`, `origin`, `referer` — see `COMMON_HEADERS`/`PATCH_HEADERS` in `koolnova_api/const.py`);
  missing them produces 400/404s that look like auth failures. Session tokens expire after ~1h
  (`TOKEN_LIFETIME` in `client.py`, refreshed at 50 min). Full endpoint/payload reference lives in
  `docs/API.md`.

## Releases (HACS versioning)

The tag and `manifest.json`'s `"version"` **must be identical** (no `v` prefix mismatch) or HACS
fails with "No content to download". Process, documented in `docs/RELEASE.md`:

1. Bump `"version"` in `custom_components/koolnova/manifest.json`.
2. Commit, then `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
3. `git push origin main --tags`.
4. Create the GitHub release from that tag (standard GitHub release, no custom zip assets).

## Working here

- There is no automated test suite in this repo (a prior `tests/` directory held ad-hoc,
  credential-bearing API exploration scripts and was purged from history — do not recreate that
  pattern; if you add tests, use mocked HTTP responses, never real Koolnova credentials).
- This integration can only really be exercised against a live Home Assistant instance + a real
  Koolnova account, which Claude Code cannot do here — reason about changes against `docs/API.md`
  and existing tests/mocks rather than assuming behavior.
