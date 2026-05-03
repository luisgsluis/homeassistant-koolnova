# Architecture of the Koolnova Integration

The Koolnova integration for Home Assistant is built as a custom integration that consumes the Koolnova REST API to control HVAC systems.

## ⚠️ Resolved Import Architecture

### Original Problem
A critical import conflict existed between:
- **PyPI package** `koolnova-api` (with a hyphen) – an external distribution that was installed.
- **Local module** `koolnovaapi` (without hyphen) – the forked source code.

### Implemented Solution
- Removed the conflicting PyPI package.
- Renamed the local module to `koolnova_api` (underscore).
- Implemented **relative imports** to avoid clashes with global packages.
- Added an `__init__.py` so the directory is recognized as a valid Python package.

### Benefits
- ✅ **No external dependencies** – only local code is used.
- ✅ **Stable imports** – no more conflicts with PyPI packages.
- ✅ **Simplified maintenance** – all code is under local control.
- ✅ **Optimized performance** – no overhead from external packages.

## File Structure

- **`__init__.py`** – Sets up and unloads the integration; registers platforms and handles the lifecycle.
- **`coordinator.py`** – `DataUpdateCoordinator` for API polling; manages periodic data refresh, caching, and error handling.
- **`climate.py`** – HVAC entities (global project and individual zones); maps Home Assistant HVAC modes to Koolnova codes; validates temperature ranges.
- **`config_flow.py`** – UI configuration flow; validates credentials and offers advanced options (intervals, modes, ranges).
- **`const.py`** – Constants and mapping tables (e.g., `KOOLNOVA_TO_HVAC_MODE`, `KOOLNOVA_ZONE_STATUS_TO_HVAC`, `KOOLNOVA_TO_FAN`).

## API Client Architecture

- **`koolnova_api/`**
  - `client.py` – Core client for API calls.
  - `session.py` – Handles authentication and session persistence.
  - `exceptions.py` – Custom exception definitions.
  - `const.py` – API-specific constants.
  - `__init__.py` – Makes the directory a proper Python package.

## Data Flow

1. **Configuration** – User supplies credentials via the config flow.
2. **Polling** – The coordinator periodically fetches projects and sensors.
3. **Entities** – Climate entities for the project and each zone are created.
4. **Control** – Changes from Home Assistant are sent through the API and cached locally.

## Dependencies

- Home Assistant Core
- Standard Python libraries
- Custom Koolnova API client (local)