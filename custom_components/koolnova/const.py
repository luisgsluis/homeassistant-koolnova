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
PLATFORMS = ["climate"]

# CONFIGURABLES: Valores por defecto y limites
DEFAULT_UPDATE_INTERVAL = 10  # segundos
MIN_UPDATE_INTERVAL = 5       # minimo configurable
MAX_UPDATE_INTERVAL = 300     # maximo configurable

DEFAULT_PROJECT_HVAC_MODES = [HVACMode.COOL, HVACMode.HEAT]
DEFAULT_ZONE_HVAC_MODES = [HVACMode.OFF, HVACMode.AUTO]

DEFAULT_MIN_TEMP = 21.0       # valor por defecto
MIN_CONFIGURABLE_TEMP = 15.0  # minimo personalizable
DEFAULT_MAX_TEMP = 27.0       # valor por defecto  
MAX_CONFIGURABLE_TEMP = 35.0  # maximo personalizable
DEFAULT_TEMP_PRECISION = 0.5

# Opciones disponibles para modos HVAC
AVAILABLE_HVAC_MODES = [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]
AVAILABLE_TEMP_PRECISIONS = [0.5, 1.0]

# Claves de configuracion
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PROJECT_HVAC_MODES = "project_hvac_modes"
CONF_ZONE_HVAC_MODES = "zone_hvac_modes"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TEMP_PRECISION = "temp_precision"

# HVAC Mode mappings para proyectos - OPTIMIZADO: Solo definicion principal
KOOLNOVA_TO_HVAC_MODE = {
    "1": HVACMode.COOL,
    "2": HVACMode.OFF, 
    "4": HVACMode.AUTO,
    "6": HVACMode.HEAT
}

# Generar mapeo inverso automaticamente para project HVAC
HVAC_TO_KOOLNOVA_MODE = {v: k for k, v in KOOLNOVA_TO_HVAC_MODE.items()}

# Status mappings para sensores/zonas - OPTIMIZADO: Solo definicion principal
KOOLNOVA_ZONE_STATUS_TO_HVAC = {
    "00": HVACMode.COOL,
    "01": HVACMode.HEAT,
    "02": HVACMode.OFF,
    "03": HVACMode.AUTO
}

# Generar mapeo inverso automaticamente para zone status
HVAC_TO_KOOLNOVA_ZONE_STATUS = {v: k for k, v in KOOLNOVA_ZONE_STATUS_TO_HVAC.items()}

# Fan Mode mappings - OPTIMIZADO: Solo definicion principal
KOOLNOVA_TO_FAN = {
    "1": FAN_LOW,
    "2": FAN_MEDIUM,
    "3": FAN_HIGH,
    "4": FAN_AUTO
}

# Generar mapeo inverso automaticamente para fan speed
FAN_TO_KOOLNOVA = {v: k for k, v in KOOLNOVA_TO_FAN.items()}

# Retry constants (no configurables)
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 2
