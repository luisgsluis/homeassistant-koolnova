# Koolnova Home Assistant Integration

[![HACS badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom integration for Home Assistant that lets you control Koolnova HVAC systems via the Koolnova REST API.

## 📍 Full Documentation

For developers and advanced users, see the detailed docs:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** – Architecture and import rules
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** – Common problems and solutions
- **[DEV_ENV.md](docs/DEV_ENV.md)** – Development\-environment setup
- **[API.md](docs/API.md)** – Koolnova API reference
- **[RELEASE.md](docs/RELEASE.md)** – Release history and process

### Features

- 🌡️ Per-₆ zone temperature control
- ❄️ HVAC mode control (COOL / HEAT / AUTO / OFF)
- 🌬️ Fan-speed control
- 🏠 Global project control
- 🔔 Smart polling (sensor updates every minute, cached projects)
- 📍️ Advanced UI configuration

### Installation

#### HACS (recommended)
1. Add this repository as a custom integration in HACS.
2. Search for \"Koolnova\" in the store.
3. Install it and restart Home Assistant.

#### Manual
1. Copy `custom_components/koolnova/` into your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Configure the integration via the UI.

### Configuration

1. Open **Configuration → Devices & Services → Add Integration**.
2. Search for \"Koolnova\".
3. Enter your Koolnova app credentials.
4. (Optional) Adjust advanced options.

#### Available Options

- **Update interval** – 30 – 3600 seconds
- **Project–level HVAC modes** – select available modes
- **Zone–level HVAC modes** – select per-zone modes
- **Temperature range** – configurable min / max values

### Support

- **Issues**: [GitHub Issues](https://github.com/luisgsluis/homeassistant-koolnova/issues)
- **Documentation**: the `docs/` folder
- **License**: MIT
