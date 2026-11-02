# Changelog

Every published version of the integration. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versioning follows
[SemVer](https://semver.org/): the git tag and the `"version"` field in `manifest.json` are always
identical (see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#publishing-a-release)).

## [2.1.0] — 2026-11-02

### Added

- **Per-zone humidity sensors** (thanks to @50bbx). `GET /topics/sensors/` returns a `humidity`
  field (relative humidity, %) for each zone. Every zone that reports a value gets a
  `sensor.koolnova_<room>_humidity` entity (device class `humidity`, state class `measurement`).
  No extra API calls: the value comes from the sensors request the integration already makes. See
  [docs/API.md](docs/API.md).
- **Per-zone CO₂ sensors.** Same mechanism for the `co2` field: `sensor.koolnova_<room>_co2`
  (device class `carbon_dioxide`, ppm), only for zones that report a value.

### Changed

- Humidity and CO₂ entities are created **as soon as a zone starts reporting a value**, not only at
  startup. Previously a probe that began reporting after Home Assistant started needed an
  integration reload to show up. Zones that return `null` still get no entity.

## [2.0.3] — 2026-08-18

### Added

- **Configurable API request timeout.** The per-request HTTP timeout for Koolnova API calls (auth
  and data endpoints alike) was hardcoded at 60 s. It is now a *Configure* option on the
  integration, defaulting to **45 s** — the value recommended by Koolnova support — with a
  configurable range of 5–300 s. The change applies without a full entry reload: the new timeout is
  pushed to the live HTTP session. See [docs/API.md](docs/API.md).

## [2.0.2] — 2026-08-17

### Added

- **`compressor_mode` attribute** on the project entity: the raw cool/heat selection, independent
  of on/off. `hvac_mode`/`state` fold on/off into the report (`off` whenever most zones are off,
  regardless of the last selected mode), which made it impossible for a dashboard to tell "off in
  cool mode" from "off in heat mode" — e.g. to conditionally show/hide a card by mode without it
  also disappearing whenever the project is off. `compressor_mode` always reflects the last
  cool/heat selection.
- **[docs/DASHBOARDS.md](docs/DASHBOARDS.md)**: example Lovelace dashboards — one with plain Home
  Assistant cards, one with [Mushroom](https://github.com/piitaya/lovelace-mushroom) — plus patterns
  for shared per-floor fan hardware and mode-based conditional visibility. Linked from the README.

## [2.0.1] — 2026-08-17

### Added

- **Global on/off for the project entity.** `KoolnovaProjectEntity` (`climate.koolnova_<project>`,
  e.g. "Control Global") now supports `TURN_ON`/`TURN_OFF`: turning on pushes `auto` status to every
  zone, turning off pushes `off` status to every zone — the same per-zone mechanism already used by
  `async_set_preset_mode`. The project's own `mode`/`is_stop` fields are echoed back by the API but
  were confirmed not to drive the hardware, so they are no longer written by these actions.

### Fixed

- The project entity's `hvac_mode` no longer clamps to `off` whenever the real mode falls outside
  the configured (selectable) `project_hvac_modes`. It now reports `off` based on the aggregated
  zone status (same aggregate as `preset_mode`) and the compressor mode (`cool`/`heat`) otherwise,
  so the on/off toggle in the UI reflects what actually happened instead of always showing off.

## [2.0.0] — 2026-08-16

### Added

- **Hub control on legacy accounts.** A `KoolnovaHubEntity` climate entity is created per physical
  hub with ON/OFF (AUTO/OFF) and the behavior mode (manual / auto / planning). Only present when the
  account actually has a hub (the `/modules/` endpoint answers nothing on newer zone-based systems).
  The reverse-engineered hub endpoints (`/modules/`, `/hub/{id}/state`, `/hub/{id}/mode/…`,
  `/hub/{id}/Manual/…`) are documented in [docs/API.md](docs/API.md).
- **Connectivity binary sensor per project** (`binary_sensor.koolnova_connectivity_status`), a
  proper on/off entity ready for automations alongside the existing connectivity sensor.
- **Per-zone on/off**: a `switch` entity per room (`switch.koolnova_<room>_power`) turns the zone
  on/off directly from the dashboard (OFF = status `02`, ON = AUTO). Zone `climate` entities also
  support `TURN_ON`/`TURN_OFF`, and their HVAC modes are relabelled in the UI as **On/Off** instead
  of Auto/Off (the codes sent to the API are unchanged).
- **Italian translation** (`translations/it.json`).
- **`/devices/` fallback**: when the main `topics` endpoints fail, the coordinator retries through
  `/devices/` so the integration degrades instead of going unavailable.

### Changed

- **Resilient API client.** `rest_request` now retries with exponential backoff on network errors,
  timeouts, rate limiting (429, honouring `Retry-After`) and server errors (5xx); a 401 refreshes
  the session token once and retries; every request gets a 60 s timeout instead of hanging forever.
  The anti-ban protections from earlier releases (minimum 30 s poll interval, cooldown after a
  failed login) are unchanged.
- **Internal:** the `koolnova_update_completed` event now also carries `hubs_count`.

## [1.4.0] — 2026-08-01

### Changed — breaking

- **The connectivity entity's attributes were renamed to snake_case identifiers.** They used to be
  display strings with Spanish text and accents baked in, which forced that language on every
  dashboard and template that read them.

  | Before | Now |
  |---|---|
  | `Señal WiFi` | `wifi_signal` |
  | `Online` | `online` |
  | `Última actualización` | `last_update` |
  | `Última actualización <room>` (one per room) | `rooms_last_update`, a mapping keyed by room name |

  The display text now lives in the translation files, so Home Assistant shows the attributes
  localised in English and Spanish instead of hard-coding either.

  **If you read these attributes**, update your templates:

  ```jinja
  {{ state_attr('<entity>', 'wifi_signal') }}
  {{ state_attr('<entity>', 'last_update') }}
  {{ state_attr('<entity>', 'rooms_last_update')['Kitchen'] }}
  ```

  The per-room attributes were merged into one mapping because dynamically named attributes cannot
  be declared in the translation files, and so could never be localised.

### Added

- Attribute translations for the connectivity entity (`state_attributes` in `strings.json` and
  `translations/{en,es}.json`), declared under both the `climate` and `sensor` domains.
- Tests covering the translation files and the attribute keys, so display strings cannot creep back
  into the keys.

## [1.3.2] — 2026-07-06

### Added
- Brand icon and logo served by the integration itself from
  `custom_components/koolnova/brand/`. Since HA 2026.3 these local images take priority over the
  brands CDN, so the integration shows its logo without depending on `home-assistant/brands` —
  which **no longer accepts custom integrations** (its bot closes the PR automatically, following
  the February 2026 `brands-proxy-api` change).

## [1.3.1] — 2026-07-05

### Fixed
- **Login regression introduced in 1.3.0.** 1.3.0 sent the user identifier in the `username` field
  of the `/auth/v2/login/` payload; the API answers `400 "Unable to log in with provided
  credentials"` for `username` and `200` for `email`. Reverted to `email`.

  The original `404` in issue #4 was never caused by the field name but by the missing
  browser-like headers — which 1.3.0 did add correctly and are kept here.

## [1.3.0] — 2026-07-04

### Fixed
- **Broken authentication (issue #4).** Since May 2026 the API answers `404` on `/auth/v2/login/`
  to requests that do not look like they come from a browser. The client now sends a modern Chrome
  `User-Agent` plus the `sec-ch-ua*` / `sec-fetch-*` headers.
- `hacs.json` contained keys that are not allowed, which made the `hacsjson` check fail; the
  validation workflow passes again (`brands` is skipped since this is a custom repository).

### Security
- Ban protection: Koolnova bans your IP automatically if polled more often than once every 30 s
  (confirmed by their support). The minimum and default interval are now 30 s, and the coordinator
  clamps configurations created before that limit existed.
- Ban protection: 5-minute cooldown after a failed login before retrying; repeated failed logins
  also trigger an IP ban.
- Debug logs no longer include the login payload (it contained the password) or the token.

### Removed
- Dead code inherited from the original project (pool and hub methods, ~110 lines) and the implicit
  `dateutil` dependency.

### Unchanged
- Default HVAC modes stay as they were.

## [1.2.6] — 2026-07-04

### Security
- Removed the `tests/` directory and purged it from git history: it contained API exploration
  scripts with plaintext credentials. Commit history was rewritten.

### Added
- HACS/hassfest validation workflow (`.github/workflows/validate.yml`).
- `CLAUDE.md` with the repository working rules.

### Fixed
- Broken link to the troubleshooting documentation in the README.

## [1.2.0]

### Fixed
- **404 errors on every API call.** The local module was named `koolnovaapi` and collided with the
  `koolnova-api` PyPI package. It was renamed to `koolnova_api` (underscore), vendored inside the
  repository, given an `__init__.py`, and is now always imported relatively. The integration no
  longer has external dependencies.

## [1.1.0]

### Added
- Global project control alongside per-zone control.

### Fixed
- Errors when updating sensors.
- Optimised HVAC mappings and coordinator polling.

## [1.0.0]

Initial release: projects and zones as `climate` entities, with temperature and mode control.

[2.0.0]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v2.0.0
[1.4.0]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.4.0
[1.3.2]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.3.2
[1.3.1]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.3.1
[1.3.0]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.3.0
[1.2.6]: https://github.com/luisgsluis/homeassistant-koolnova/releases/tag/v1.2.6
[1.2.0]: https://github.com/luisgsluis/homeassistant-koolnova/commits/main
[1.1.0]: https://github.com/luisgsluis/homeassistant-koolnova/commits/main
[1.0.0]: https://github.com/luisgsluis/homeassistant-koolnova/commits/main
