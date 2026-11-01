"""Constants for the Koolnova integration."""

from datetime import timedelta
from homeassistant.components.climate import (
    HVACMode,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO
)

DOMAIN = "koolnova"
PLATFORMS = ["climate", "binary_sensor", "switch", "sensor"]

# CONFIGURABLE: defaults and limits.
# IMPORTANT: Koolnova bans IPs automatically when the API is polled more than
# once every 30 seconds (confirmed by their support, see issue #4).
DEFAULT_UPDATE_INTERVAL = 30  # seconds
MIN_UPDATE_INTERVAL = 30      # configurable minimum (limit imposed by Koolnova)
MAX_UPDATE_INTERVAL = 3600    # configurable maximum
DEFAULT_PROJECT_UPDATE_FREQUENCY = 10  # refresh projects every N updates
MIN_PROJECT_UPDATE_FREQUENCY = 1      # configurable minimum (always refresh)
MAX_PROJECT_UPDATE_FREQUENCY = 300    # configurable maximum

# Per-request HTTP timeout for Koolnova API calls (seconds).
# 45s is the value recommended by Koolnova support (see docs/API.md).
DEFAULT_REQUEST_TIMEOUT = 45   # seconds
MIN_REQUEST_TIMEOUT = 5        # configurable minimum
MAX_REQUEST_TIMEOUT = 300      # configurable maximum

DEFAULT_PROJECT_HVAC_MODES = [HVACMode.COOL, HVACMode.HEAT]
DEFAULT_ZONE_HVAC_MODES = [HVACMode.OFF, HVACMode.AUTO]

DEFAULT_MIN_TEMP = 21.0       # default value
MIN_CONFIGURABLE_TEMP = 15.0  # customisable minimum
DEFAULT_MAX_TEMP = 27.0       # default value
MAX_CONFIGURABLE_TEMP = 35.0  # customisable maximum
DEFAULT_TEMP_PRECISION = 0.5

# Options offered for HVAC modes
AVAILABLE_HVAC_MODES = [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]
AVAILABLE_TEMP_PRECISIONS = [0.5, 1.0]

# Configuration keys
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PROJECT_UPDATE_FREQUENCY = "project_update_frequency"
CONF_PROJECT_HVAC_MODES = "project_hvac_modes"
CONF_ZONE_HVAC_MODES = "zone_hvac_modes"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TEMP_PRECISION = "temp_precision"
CONF_REQUEST_TIMEOUT = "request_timeout"

# HVAC mode mappings for projects - only the forward definition is written by hand
KOOLNOVA_TO_HVAC_MODE = {
    "1": HVACMode.COOL,
    "2": HVACMode.OFF,
    "4": HVACMode.HEAT,
    "6": HVACMode.AUTO
}

# Inverse mapping, generated automatically, for project HVAC
HVAC_TO_KOOLNOVA_MODE = {v: k for k, v in KOOLNOVA_TO_HVAC_MODE.items()}

# Status mappings for sensors/zones - only the forward definition is written by hand
KOOLNOVA_ZONE_STATUS_TO_HVAC = {
    "00": HVACMode.COOL,
    "01": HVACMode.HEAT,
    "02": HVACMode.OFF,
    "03": HVACMode.AUTO
}

# Inverse mapping, generated automatically, for zone status
HVAC_TO_KOOLNOVA_ZONE_STATUS = {v: k for k, v in KOOLNOVA_ZONE_STATUS_TO_HVAC.items()}

# Fan mode mappings - only the forward definition is written by hand
KOOLNOVA_TO_FAN = {
    "1": FAN_LOW,
    "2": FAN_MEDIUM,
    "3": FAN_HIGH,
    "4": FAN_AUTO
}

# Inverse mapping, generated automatically, for fan speed
FAN_TO_KOOLNOVA = {v: k for k, v in KOOLNOVA_TO_FAN.items()}

# Retry constants (not configurable)
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 2
