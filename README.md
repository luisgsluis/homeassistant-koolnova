# Koolnova Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]

Home Assistant integration for Koolnova climate control systems.

## Features

- **Project Control**: Change between COOL/HEAT modes
- **Zone Control**: Individual room temperature and fan control  
- **Global Temperature**: Set temperature for all zones at once
- **Configurable Options**: Customize update intervals, temperature ranges, and available modes
- **Real-time Updates**: Monitor temperature and status changes

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/luisgsluis/homeassistant-koolnova`
6. Select category "Integration"
7. Click "Add"
8. Install the integration
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/luisgsluis/homeassistant-koolnova/releases)
2. Extract the files
3. Copy the `custom_components/koolnova` folder to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Configuration

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for "Koolnova"
4. Enter your Koolnova account credentials
5. Configure options (update interval, temperature ranges, etc.)

## Entities Created

- **Project Entity**: `climate.koolnova_project_name`
  - Control global HVAC mode (COOL/HEAT)
  - Set temperature for all zones
- **Zone Entities**: `climate.koolnova_room_name`
  - Individual room temperature control
  - Fan speed control (LOW/MEDIUM/HIGH/AUTO)
  - Zone mode control (OFF/AUTO)

## Configuration Options

- **Update Interval**: 5-300 seconds (default: 10)
- **Project HVAC Modes**: Available modes for project control
- **Zone HVAC Modes**: Available modes for zone control
- **Temperature Range**: Configurable min/max temperatures
- **Temperature Precision**: 0.5°C or 1.0°C steps

## Requirements

- Home Assistant 2023.7.3 or newer
- Python 3.11+
- Koolnova account with API access

## Troubleshooting

### Common Issues

**Integration not loading**
- Check Home Assistant logs for errors
- Verify your credentials are correct
- Ensure your Koolnova account has API access

**Entities not updating**
- Check the update interval in integration options
- Verify network connectivity to api.koolnova.com

### Debug Logging

Add this to your `configuration.yaml`:
logger:
logs:
custom_components.koolnova: debug

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Built using the [koolnova-api](https://pypi.org/project/koolnova-api/) Python library
- Thanks to the Home Assistant community for guidance and support

[releases-shield]: https://img.shields.io/github/release/luisgsluis/homeassistant-koolnova.svg
[releases]: https://github.com/luisgsluis/homeassistant-koolnova/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/luisgsluis/homeassistant-koolnova.svg
[commits]: https://github.com/luisgsluis/homeassistant-koolnova/commits/main