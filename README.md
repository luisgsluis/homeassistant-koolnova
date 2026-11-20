# Koolnova for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![release](https://img.shields.io/github/v/release/luisgsluis/homeassistant-koolnova)](https://github.com/luisgsluis/homeassistant-koolnova/releases)

Custom integration that controls **Koolnova** HVAC systems from Home Assistant through their cloud
API. Zones, the project as a whole, and (on legacy accounts) the physical hub are exposed as
`climate` entities, plus a connectivity binary sensor per project.

Requires Home Assistant 2026.11.0 or newer (since 2.1.1 the climate entities use properties that older versions do not read) and a Koolnova app account.

> ⚠️ Koolnova bans your IP automatically if their API is polled too often, and also on repeated
> failed logins (limits in [docs/API.md](docs/API.md)). The integration enforces a minimum interval
> and backs off after a failed login on purpose — do not force it lower.

## Features

- ❄️ **HVAC modes per zone and globally** (COOL / HEAT / AUTO / OFF)
- 🌡️ **Target temperature** per zone and global median across zones
- 🌬️ **Fan speed** per zone (LOW / MEDIUM / HIGH / AUTO)
- 🏠 **Global project control** (mode, ECO, stop) on a single `climate` entity
- 🧊 **Hub control** on legacy accounts: one `climate` entity per hub with ON/OFF and the behavior
  mode (manual / auto / planning)
- 📶 **Connectivity binary sensor** per project (online/offline)
- 💧 **Per-zone humidity and CO₂**: a `sensor` per room that reports one
  (`sensor.koolnova_<room>_humidity`, `sensor.koolnova_<room>_co2`)
- 🔌 **Per-zone on/off**: a `switch` per room (`switch.koolnova_<room>_power`) toggles the zone
  straight from the dashboard; zone `climate` modes display as **On/Off** instead of Auto/Off (the
  codes sent to the API are unchanged)
- 🛡️ **Robust against the brittle API**: retries with exponential backoff on timeouts, network
  errors, rate limiting (429) and server errors (5xx); auto-refreshes the session token on 401;
  a per-request timeout; falls back to the `/devices/` endpoint when the main ones fail
- 🔄 **Staggered polling**: sensors every cycle, the more expensive project list cached
- 🎛️ **Setup and intervals configurable from the UI**
- 🌍 Translations: English, Spanish, Italian

## Entities

| Entity | Domain | Purpose |
|---|---|---|
| `climate.koolnova_*` (project) | climate | Global control: target temperature (median of zones), project HVAC mode, on/off (Off turns every zone off and remembers which were on; turning back on restores those), ECO/stop attributes |
| `climate.koolnova_*` (zone) | climate | One per room: temperature, setpoint, HVAC mode, fan speed |
| `climate.koolnova_hub_*` | climate | Legacy hub, one per hub: ON/OFF + manual / auto / planning |
| `switch.koolnova_<room>_power` | switch | One per room: power on/off toggle |
| `sensor.koolnova_<room>_humidity` | sensor | One per room that reports humidity: relative humidity (%) |
| `sensor.koolnova_<room>_co2` | sensor | One per room that reports CO₂ (ppm) |
| `sensor.koolnova_*` (connectivity) | sensor | Online/offline + WiFi signal, last sync, per-room last update as attributes. Its `entity_id` follows your HA language (e.g. `sensor.koolnova_<project>_estado_de_conectividad`); before this change it was registered in the `climate` domain |
| `binary_sensor.koolnova_connectivity_status` | binary_sensor | Online/offline per project, ready for automations |

The integration also fires a `koolnova_update_completed` event after every poll with counts and a
`lastsync` timestamp — handy for automation triggers. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Dashboards

No dashboard ships with the integration — you build one from the entities above. Two starting
points are documented in [docs/DASHBOARDS.md](docs/DASHBOARDS.md): a **plain Home Assistant** one
(core `thermostat` + `tile` cards, no extra dependency) and a
**[Mushroom](https://github.com/piitaya/lovelace-mushroom)** one (more compact). That doc also
covers other patterns, like grouping fan control by floor instead of by zone.

## Installation

### HACS (recommended)

1. HACS → ⋮ menu → **Custom repositories** → add
   `https://github.com/luisgsluis/homeassistant-koolnova` with category *Integration*.
2. Search for **Koolnova**, download it and restart Home Assistant.

### Manual

Copy `custom_components/koolnova/` into the `custom_components` directory of your configuration
and restart Home Assistant.

## Configuration

**Settings → Devices & services → Add integration → Koolnova**, using your Koolnova app
credentials.

Options available afterwards through *Configure* (defaults and allowed ranges: `const.py`):
update interval, project refresh frequency, offered project and zone HVAC modes, temperature range
and precision, and API request timeout.

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — version history
- [docs/DASHBOARDS.md](docs/DASHBOARDS.md) — example Lovelace dashboards
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common problems
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — architecture, test environment and releases
- [docs/API.md](docs/API.md) — the Koolnova API, documented by reverse engineering

## Disclaimer

Unofficial project, not affiliated with Koolnova. It relies on an undocumented API that the
manufacturer may change or shut down at any time. The REST client bundled in `koolnova_api/` is a
fork of the `koolnova-api` package, with credit to its original author.

MIT licensed · [Issues](https://github.com/luisgsluis/homeassistant-koolnova/issues)

## Looking for Contributors

Koolnova for Home Assistant is a side project I maintain solo, and I'm looking for people to bring
into it as contributors — not a queue for feature requests. If you want to actually work on
something, open an issue to introduce yourself and what you'd want to tackle.
