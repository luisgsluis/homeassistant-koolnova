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

# Project HA modes, in the order they are shown. Which of them an installation
# offers comes from its TopicModes configuration (see enabled_hvac_modes below);
# the "Project HVAC Modes" option only narrows that list down.
AVAILABLE_PROJECT_HVAC_MODES = [HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY]
DEFAULT_PROJECT_HVAC_MODES = list(AVAILABLE_PROJECT_HVAC_MODES)  # no filtering
DEFAULT_ZONE_HVAC_MODES = [HVACMode.OFF, HVACMode.AUTO]

DEFAULT_MIN_TEMP = 21.0       # default value
MIN_CONFIGURABLE_TEMP = 15.0  # customisable minimum
DEFAULT_MAX_TEMP = 27.0       # default value
MAX_CONFIGURABLE_TEMP = 35.0  # customisable maximum
DEFAULT_TEMP_PRECISION = 0.5

# Options offered for zone HVAC modes
AVAILABLE_ZONE_HVAC_MODES = [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]
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

# Project (system) modes. The codes and their meaning come from Koolnova's own
# web app (app.koolnova.com, the `app-topic-modes` component); which of them a
# given installation offers comes from its "TopicModes" configuration, a string
# of "0"/"1" where the character at index N enables mode N.
#   0 ventilation, 1 cooling (air), 2 heating (air), 3 dehumidification,
#   4 radiant floor, 5 floor cooling + cold air, 6 radiant floor + hot air
KOOLNOVA_TO_HVAC_MODE = {
    "0": HVACMode.FAN_ONLY,
    "1": HVACMode.COOL,
    "2": HVACMode.HEAT,
    "3": HVACMode.DRY,
    "4": HVACMode.HEAT,
    "5": HVACMode.COOL,
    "6": HVACMode.HEAT,
}

# Several codes mean the same HA mode, so the inverse is written by hand: the
# first code the installation enables is the one sent (air before floor).
HVAC_TO_KOOLNOVA_MODE_CANDIDATES = {
    HVACMode.FAN_ONLY: ["0"],
    HVACMode.COOL: ["1", "5"],
    HVACMode.HEAT: ["2", "6", "4"],
    HVACMode.DRY: ["3"],
}

# Codes assumed when the project carries no TopicModes value (older API answer,
# or the fallback data source): cooling and heating by air, the two modes the
# integration offered before TopicModes was read.
FALLBACK_PROJECT_MODE_CODES = ["1", "2"]


def enabled_mode_codes(topic_modes):
    """Codes enabled by a TopicModes string ("11110001" -> ["0", "1", "2", "3"]).

    Positions without a known code are ignored. None or "" means unknown, and
    FALLBACK_PROJECT_MODE_CODES is used.
    """
    if not topic_modes or not isinstance(topic_modes, str):
        return list(FALLBACK_PROJECT_MODE_CODES)
    return [str(i) for i, flag in enumerate(topic_modes)
            if flag == "1" and str(i) in KOOLNOVA_TO_HVAC_MODE]


def enabled_hvac_modes(topic_modes):
    """HA modes the installation offers, in AVAILABLE_PROJECT_HVAC_MODES order."""
    codes = enabled_mode_codes(topic_modes)
    return [mode for mode in AVAILABLE_PROJECT_HVAC_MODES
            if any(code in codes for code in HVAC_TO_KOOLNOVA_MODE_CANDIDATES[mode])]


def mode_code_for(hvac_mode, topic_modes):
    """Koolnova code to send for an HA mode, or None if the installation doesn't enable it."""
    codes = enabled_mode_codes(topic_modes)
    return next((code for code in HVAC_TO_KOOLNOVA_MODE_CANDIDATES.get(hvac_mode, [])
                 if code in codes), None)


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
