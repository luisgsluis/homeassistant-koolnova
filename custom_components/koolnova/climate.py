# koolnova/climate.py

"""Climate entities for Koolnova."""

import asyncio
import logging
import statistics
from collections import Counter
from datetime import datetime
from requests.exceptions import HTTPError

from homeassistant.components.climate import (
    ClimateEntity,
    HVACMode,
    ClimateEntityFeature,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.components.persistent_notification import async_create
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    KOOLNOVA_TO_HVAC_MODE,
    HVAC_TO_KOOLNOVA_MODE,
    KOOLNOVA_ZONE_STATUS_TO_HVAC,
    HVAC_TO_KOOLNOVA_ZONE_STATUS,
    KOOLNOVA_TO_FAN,
    FAN_TO_KOOLNOVA,
    DEFAULT_PROJECT_HVAC_MODES,
    DEFAULT_ZONE_HVAC_MODES,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_TEMP_PRECISION,
    CONF_PROJECT_HVAC_MODES,
    CONF_ZONE_HVAC_MODES,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_TEMP_PRECISION,
)
from .coordinator import KoolnovaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _fallo(hass, titulo: str, mensaje: str, err: Exception) -> None:
    """Notificación persistente y error al llamador: una automatización o la UI tienen que enterarse de que no
    se aplicó (antes se tragaba y el servicio parecía haber ido bien)."""
    _LOGGER.error("%s: %s", mensaje, err)
    async_create(hass, f"{mensaje}: {err}", title=titulo)
    raise HomeAssistantError(f"{mensaje}: {err}") from err


def _resultado_global(hass, titulo: str, que: str, result: dict) -> None:
    """Resultado de un cambio aplicado a todas las zonas: aviso si alguna falló, error si fallaron todas."""
    ok, mal = result.get("updated", 0), result.get("failed", 0)
    if not mal:
        _LOGGER.info("%s: %d zonas", que, ok)
        return
    texto = f"{que}: {ok} zonas bien, {mal} con error"
    async_create(hass, texto, title=titulo)
    if not ok:
        raise HomeAssistantError(texto)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Koolnova climate entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    if coordinator.data.get("projects"):
        proj = coordinator.data["projects"][0]
        entities.append(KoolnovaProjectEntity(coordinator, entry, proj))

    # Add the single connectivity sensor
    entities.append(KoolnovaConnectivitySensor(coordinator, entry))

    # Legacy hub controllers (only present on accounts that have a hub)
    if coordinator.data.get("hubs"):
        for hub in coordinator.data["hubs"]:
            entities.append(KoolnovaHubEntity(coordinator, entry, hub))

    for sensor in coordinator.data.get("sensors", []):
        entities.append(KoolnovaZoneEntity(coordinator, entry, sensor))

    async_add_entities(entities, update_before_add=False)

class KoolnovaProjectEntity(ClimateEntity):
    """Project entity with global control: temperature, project HVAC mode, zone fan speed, and zone HVAC mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "koolnova_project" # Key HA uses to look up specific translations.

    def __init__(self, coordinator, config_entry, project):
        """Initialize the project entity."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._project = project

        self._attr_unique_id = f"{config_entry.entry_id}_project"
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.PRESET_MODE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_should_poll = False

        self._global_fan_mode = FAN_AUTO
        self._global_zone_hvac_mode = HVACMode.AUTO

    def _get_config_value(self, key, default):
        """Get configuration value from options or data."""
        return self.config_entry.options.get(key, self.config_entry.data.get(key, default))

    def _get_project_hvac_modes(self):
        """Get configured project HVAC modes."""
        mode_values = self._get_config_value(CONF_PROJECT_HVAC_MODES, [mode.value for mode in DEFAULT_PROJECT_HVAC_MODES])
        return [HVACMode(value) for value in mode_values]

    def _get_zone_hvac_modes(self):
        """Get configured zone HVAC modes."""
        mode_values = self._get_config_value(CONF_ZONE_HVAC_MODES, [mode.value for mode in DEFAULT_ZONE_HVAC_MODES])
        return [HVACMode(value) for value in mode_values]

    def _get_min_temp(self):
        """Get configured minimum temperature."""
        return self._get_config_value(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)

    def _get_max_temp(self):
        """Get configured maximum temperature."""
        return self._get_config_value(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)

    def _get_temp_precision(self):
        """Get configured temperature precision."""
        return self._get_config_value(CONF_TEMP_PRECISION, DEFAULT_TEMP_PRECISION)

    @property
    def hvac_modes(self):
        """Return configured project HVAC modes."""
        return self._get_project_hvac_modes()

    @property
    def fan_modes(self):
        """Return list of available fan modes for global zone control."""
        return [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]

    @property
    def fan_mode(self):
        """Return current global fan mode."""
        return self._global_fan_mode

    @property
    def preset_modes(self):
        """Return available zone HVAC modes as custom preset modes."""
        # Return the raw values ('off', 'auto'): they are the keys used in the translation files.
        return [mode.value for mode in self._get_zone_hvac_modes()]

    @property
    def preset_mode(self):
        """Return most common zone HVAC mode among all zones."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return None

        modes = []
        for sensor in sensors:
            status = sensor.get("Room_status", "02")
            hvac_mode = KOOLNOVA_ZONE_STATUS_TO_HVAC.get(status, HVACMode.OFF)
            if hvac_mode in self._get_zone_hvac_modes():
                modes.append(hvac_mode.value)

        if modes:
            # Return the most common mode, if tie, Counter.most_common returns first one
            return Counter(modes).most_common(1)[0][0]
        return None

    @property
    def min_temp(self):
        """Return configured minimum temperature."""
        return self._get_min_temp()

    @property
    def max_temp(self):
        """Return configured maximum temperature."""
        return self._get_max_temp()

    @property
    def precision(self):
        """Return configured temperature precision."""
        return self._get_temp_precision()

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    def _update_project_data(self):
        """Update local project data from coordinator."""
        for project in self.coordinator.data.get("projects", []):
            if project.get("Topic_id") == self._project.get("Topic_id"):
                self._project = project
                break

    @property
    def hvac_mode(self):
        """Return current project HVAC mode.

        The project's own `mode`/`is_stop` fields are echoed back by the API
        but don't drive the hardware (confirmed live): the real global on/off
        is per-zone status, same as `preset_mode` below. Off is reported when
        most zones are off (or there are none); otherwise the project's
        compressor mode (cool/heat) is reported, even if it falls outside the
        configured (selectable) project_hvac_modes.
        """
        self._update_project_data()
        if self.preset_mode in (None, HVACMode.OFF.value):
            return HVACMode.OFF
        return KOOLNOVA_TO_HVAC_MODE.get(self._project["Mode"], HVACMode.OFF)

    @property
    def native_target_temperature(self):
        """Return median of zones' target temperatures."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return None

        temps = [
            sensor["Room_setpoint_temp"]
            for sensor in sensors
            if sensor.get("Room_setpoint_temp") is not None
        ]

        if temps:
            return statistics.median(temps)
        return None

    @property
    def native_current_temperature(self):
        """Return average temperature of all zones, rounded to nearest 0.5."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return None

        temps = [
            sensor["Room_actual_temp"]
            for sensor in sensors
            if sensor.get("Room_actual_temp") is not None
        ]

        if temps:
            avg_temp = sum(temps) / len(temps)
            return round(avg_temp * 2) / 2
        return None

    @property
    def available(self):
        """Return if entity is available."""
        self._update_project_data()
        return self._project.get("is_online", False) and self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        self._update_project_data()
        sensors = self.coordinator.data.get("sensors", [])
        sensors_count = len(sensors)

        # Take system connectivity from the sensors: they are fresher than the project
        system_connectivity = {}
        if sensors:
            topic_info = sensors[0].get("topic_info", {})  # Cualquier sensor tiene los mismos datos globales
            system_connectivity = {
                "system_rssi": topic_info.get("rssi"),
                "online_status": topic_info.get("is_online"),  # fresher than the project copy
                "last_sync": topic_info.get("last_sync"),      # fresher than the project copy
            }

        zone_status_breakdown = {}
        zone_fan_breakdown = {}
        for sensor in sensors:
            status = sensor.get("Room_status", "02")
            hvac_mode = KOOLNOVA_ZONE_STATUS_TO_HVAC.get(status, "unknown")
            mode_name = hvac_mode.value if hasattr(hvac_mode, 'value') else str(hvac_mode)
            zone_status_breakdown[mode_name] = zone_status_breakdown.get(mode_name, 0) + 1

            fan_speed = sensor.get("Room_speed", "4")
            fan_mode = KOOLNOVA_TO_FAN.get(fan_speed, "unknown")
            zone_fan_breakdown[fan_mode] = zone_fan_breakdown.get(fan_mode, 0) + 1

        attrs = {
            "eco_mode": self._project["eco"],
            "is_stop": self._project.get("is_stop"),
            # Raw compressor mode (cool/heat), independent of on/off: unlike `hvac_mode`/`state`
            # (which report off whenever most zones are off), this keeps reporting the last
            # cool/heat selection even while the project is off, for dashboards that need to
            # distinguish "off in cool mode" from "off in heat mode".
            "compressor_mode": KOOLNOVA_TO_HVAC_MODE.get(self._project["Mode"], HVACMode.OFF).value,
            "total_zones": sensors_count,
            "control_type": "global_controller",
            "configured_project_modes": [mode.value for mode in self._get_project_hvac_modes()],
            "configured_zone_modes": [mode.value for mode in self._get_zone_hvac_modes()],
            "global_fan_mode": self._global_fan_mode,
            "global_zone_hvac_mode": self._global_zone_hvac_mode.value,
            "zones_status_breakdown": zone_status_breakdown,
            "zones_fan_breakdown": zone_fan_breakdown,
        }

        # Agregar datos de conectividad del sistema (desde sensores)
        if system_connectivity.get("system_rssi") is not None:
            attrs["system_rssi"] = system_connectivity["system_rssi"]
        if system_connectivity.get("online_status") is not None:
            attrs["online_status"] = system_connectivity["online_status"]
        if system_connectivity.get("last_sync"):
            try:
                attrs["last_sync"] = datetime.fromisoformat(system_connectivity["last_sync"])
            except (ValueError, TypeError):
                attrs["last_sync"] = system_connectivity["last_sync"]

        return attrs

    async def async_set_hvac_mode(self, hvac_mode):
        """Set project HVAC mode."""
        if hvac_mode not in self.hvac_modes:
            _LOGGER.error("Unsupported project HVAC mode: %s. Available: %s", hvac_mode, self.hvac_modes)
            return

        koolnova_mode = HVAC_TO_KOOLNOVA_MODE.get(hvac_mode)
        if not koolnova_mode:
            _LOGGER.error("HVAC mode not mapped: %s", hvac_mode)
            return

        body = {"mode": koolnova_mode}

        try:
            await self.coordinator.async_update_project_data(self._project["Topic_id"], body)
            _LOGGER.info("Project mode updated to %s", hvac_mode)
        except Exception as err:
            _fallo(self.hass, "Koolnova Project Mode", "Error updating project mode", err)

    async def async_set_fan_mode(self, fan_mode):
        """Set global fan mode for ALL zones."""
        if fan_mode not in self.fan_modes:
            _LOGGER.error("Unsupported fan mode: %s. Available: %s", fan_mode, self.fan_modes)
            return

        speed_code = FAN_TO_KOOLNOVA.get(fan_mode)
        if not speed_code:
            _LOGGER.error("Fan mode not mapped: %s", fan_mode)
            return

        _LOGGER.info("Setting global fan mode to %s (speed: %s) for all zones", fan_mode, speed_code)
        try:
            result = await self.coordinator.async_update_all_sensors_fan_speed(speed_code)
        except Exception as err:
            _fallo(self.hass, "Koolnova Global Fan Control", "Error setting global fan mode", err)
        if result.get("updated", 0):      # el modo mostrado solo cambia si alguna zona lo aceptó
            self._global_fan_mode = fan_mode
            self.async_write_ha_state()
        _resultado_global(self.hass, "Koolnova Global Fan Control", f"Global fan mode {fan_mode}", result)

    async def async_set_preset_mode(self, preset_mode: str):
        """Set global zone HVAC mode for ALL zones."""
        if preset_mode not in self.preset_modes:
            _LOGGER.error("Unsupported preset mode: %s. Available: %s", preset_mode, self.preset_modes)
            return

        try:
            hvac_mode = HVACMode(preset_mode)
        except ValueError:
            _LOGGER.error("Invalid preset mode value received: %s", preset_mode)
            return

        status_code = HVAC_TO_KOOLNOVA_ZONE_STATUS.get(hvac_mode)
        if not status_code:
            _LOGGER.error("Zone HVAC mode not mapped: %s", hvac_mode)
            return

        _LOGGER.info("Setting global zone HVAC mode to %s (status: %s) for all zones", hvac_mode, status_code)
        await self._set_all_zones_status(hvac_mode, status_code, f"Global zone HVAC mode {preset_mode}")

    async def _set_all_zones_status(self, hvac_mode, status_code, que):
        """Mismo estado en todas las zonas; el modo global mostrado solo cambia si alguna lo aceptó."""
        try:
            result = await self.coordinator.async_update_all_sensors_status(status_code)
        except Exception as err:
            _fallo(self.hass, "Koolnova Global Zone Control", f"Error: {que}", err)
        if result.get("updated", 0):
            self._global_zone_hvac_mode = hvac_mode
            self.async_write_ha_state()
        _resultado_global(self.hass, "Koolnova Global Zone Control", que, result)

    async def async_set_temperature(self, **kwargs):
        """Set global target temperature for ALL zones."""
        temp = kwargs.get("temperature")
        if temp is None:
            return

        precision = self.precision
        temp = round(temp / precision) * precision
        
        if not (self.min_temp <= temp <= self.max_temp):
            _LOGGER.error("Temperature %s out of configured range (%s - %s)", temp, self.min_temp, self.max_temp)
            return

        _LOGGER.info("Setting global temperature to %s degrees for all zones", temp)
        try:
            result = await self.coordinator.async_update_all_sensors_temperature(temp)
        except Exception as err:
            _fallo(self.hass, "Koolnova Global Temperature", "Error setting global temperature", err)
        _resultado_global(self.hass, "Koolnova Global Temperature", f"Global temperature {temp}", result)

    async def async_turn_on(self):
        """Turn the project on: push AUTO to every zone, regardless of the configured
        (selectable) project/zone HVAC modes.

        The project's `mode`/`is_stop` fields are echoed back by the API but
        don't drive the hardware (confirmed live): the actual global on/off is
        per-zone status, same mechanism as `async_set_preset_mode` below.
        """
        _LOGGER.info("Turning project on: setting all zones to auto")
        await self._set_all_zones_status(HVACMode.AUTO, HVAC_TO_KOOLNOVA_ZONE_STATUS[HVACMode.AUTO], "Turning project on")

    async def async_turn_off(self):
        """Turn the project off: push OFF to every zone (see async_turn_on)."""
        _LOGGER.info("Turning project off: setting all zones to off")
        await self._set_all_zones_status(HVACMode.OFF, HVAC_TO_KOOLNOVA_ZONE_STATUS[HVACMode.OFF], "Turning project off")

class KoolnovaZoneEntity(ClimateEntity):
    """Individual room zone as a climate device."""

    # Relabels the zone's HVAC modes in the UI ("auto" shows as "On"): the
    # codes sent to the API are untouched (see entity_component translations).
    _attr_translation_key = "koolnova_zone"

    def __init__(self, coordinator, config_entry, sensor):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._sensor = sensor
        self._sensor_id = sensor["Room_id"]
        self._attr_name = f"Koolnova {sensor['Room_Name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_zone_{sensor['Room_id']}"
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_should_poll = False

    def _get_config_value(self, key, default):
        """Get configuration value from options or data."""
        return self.config_entry.options.get(key, self.config_entry.data.get(key, default))

    def _get_zone_hvac_modes(self):
        """Get configured zone HVAC modes."""
        mode_values = self._get_config_value(CONF_ZONE_HVAC_MODES, [mode.value for mode in DEFAULT_ZONE_HVAC_MODES])
        return [HVACMode(value) for value in mode_values]
        
    def _get_min_temp(self):
        """Get configured minimum temperature."""
        return self._get_config_value(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)

    def _get_max_temp(self):
        """Get configured maximum temperature."""
        return self._get_config_value(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)

    def _get_temp_precision(self):
        """Get configured temperature precision."""
        return self._get_config_value(CONF_TEMP_PRECISION, DEFAULT_TEMP_PRECISION)

    @property
    def hvac_modes(self):
        """Return configured HVAC modes for zones."""
        return self._get_zone_hvac_modes()

    @property
    def min_temp(self):
        """Return configured minimum temperature."""
        return self._get_min_temp()

    @property
    def max_temp(self):
        """Return configured maximum temperature."""
        return self._get_max_temp()

    @property
    def precision(self):
        """Return configured temperature precision."""
        return self._get_temp_precision()

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    def _update_sensor_data(self):
        """Update local sensor data from coordinator."""
        if not self.coordinator.data or not isinstance(self.coordinator.data.get("sensors"), list):
            return
        
        for sensor in self.coordinator.data.get("sensors", []):
            if sensor.get("Room_id") == self._sensor_id:
                self._sensor = sensor
                break

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        self._update_sensor_data()
        status = self._sensor.get("Room_status", "02")
        current_mode = KOOLNOVA_ZONE_STATUS_TO_HVAC.get(status, HVACMode.OFF)
        if current_mode not in self.hvac_modes:
            return HVACMode.OFF
        return current_mode

    @property
    def native_current_temperature(self):
        """Return current temperature."""
        self._update_sensor_data()
        return self._sensor.get("Room_actual_temp")

    @property
    def native_target_temperature(self):
        """Return target temperature."""
        self._update_sensor_data()
        return self._sensor.get("Room_setpoint_temp")

    @property
    def fan_mode(self):
        """Return current fan mode."""
        self._update_sensor_data()
        return KOOLNOVA_TO_FAN.get(self._sensor.get("Room_speed"))

    @property
    def fan_modes(self):
        """Return list of available fan modes."""
        return [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]

    @property
    def available(self):
        """Return if entity is available."""
        self._update_sensor_data()
        project_online = False
        if self.coordinator.data.get("projects"):
            project_online = self.coordinator.data["projects"][0].get("is_online", False)
        return self.coordinator.last_update_success and project_online

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        self._update_sensor_data()

        # Obtener system_last_sync del sensor (datos globales del controlador)
        system_last_sync = None
        topic_info = self._sensor.get("topic_info", {})
        if topic_info and topic_info.get("last_sync"):
            try:
                system_last_sync = datetime.fromisoformat(topic_info["last_sync"])
            except (ValueError, TypeError):
                system_last_sync = topic_info["last_sync"]

        return {
            "room_id": self._sensor.get("Room_id"),
            "room_status_raw": self._sensor.get("Room_status"),
            "room_speed_raw": self._sensor.get("Room_speed"),
            "topic_id": self._sensor.get("Topic_id", None),
            "last_updated": self._sensor.get("Room_update_at"),
            "system_last_sync": system_last_sync,  # last sync of the system
        }

    async def async_set_temperature(self, **kwargs):
        """Set target temperature."""
        temp = kwargs.get("temperature")
        if temp is None:
            return

        precision = self.precision
        temp = round(temp / precision) * precision
        
        if not (self.min_temp <= temp <= self.max_temp):
            _LOGGER.error("Temperature %s out of configured range (%s - %s)", temp, self.min_temp, self.max_temp)
            return

        _LOGGER.info("Setting temperature to %s degrees for %s", temp, self._attr_name)
        body = {"setpoint_temperature": temp}

        try:
            await self.coordinator.async_update_sensor_data(self._sensor_id, body)
            _LOGGER.info("Temperature successfully updated for %s", self._attr_name)
        except Exception as err:
            _fallo(self.hass, "Koolnova", f"Error updating zone temperature for {self._attr_name}", err)

    async def async_set_fan_mode(self, fan_mode):
        """Set fan mode."""
        if fan_mode not in self.fan_modes:
            _LOGGER.error("Unsupported fan mode: %s. Available: %s", fan_mode, self.fan_modes)
            return
        koolnova_speed = FAN_TO_KOOLNOVA.get(fan_mode)
        if not koolnova_speed:
            _LOGGER.error("Unsupported fan mode: %s. Available: %s", fan_mode, self.fan_modes)
            return

        _LOGGER.info("Setting fan mode to %s (speed: %s) for %s", fan_mode, koolnova_speed, self._attr_name)
        body = {"speed": koolnova_speed}

        try:
            await self.coordinator.async_update_sensor_data(self._sensor_id, body)
            _LOGGER.info("Fan mode successfully updated for %s", self._attr_name)
        except Exception as err:
            _fallo(self.hass, "Koolnova", f"Error updating zone fan mode for {self._attr_name}", err)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode for zones - only configured modes allowed."""
        if hvac_mode not in self.hvac_modes:
            _LOGGER.error("Unsupported HVAC mode for zone: %s. Allowed: %s", hvac_mode, self.hvac_modes)
            return

        status_code = HVAC_TO_KOOLNOVA_ZONE_STATUS.get(hvac_mode)
        if not status_code:
            _LOGGER.error("HVAC mode not mapped: %s", hvac_mode)
            return

        _LOGGER.info("Setting HVAC mode to %s (status: %s) for %s", hvac_mode, status_code, self._attr_name)
        body = {"status": status_code}

        try:
            await self.coordinator.async_update_sensor_data(self._sensor_id, body)
            _LOGGER.info("HVAC mode successfully updated for %s", self._attr_name)
        except Exception as err:
            _fallo(self.hass, "Koolnova", f"Error updating zone HVAC mode for {self._attr_name}", err)

    async def async_turn_on(self):
        """Turn the zone on (AUTO, or the first configured non-off mode)."""
        if HVACMode.AUTO in self.hvac_modes:
            await self.async_set_hvac_mode(HVACMode.AUTO)
        else:
            for mode in self.hvac_modes:
                if mode != HVACMode.OFF:
                    await self.async_set_hvac_mode(mode)
                    break

    async def async_turn_off(self):
        """Turn the zone off."""
        if HVACMode.OFF in self.hvac_modes:
            await self.async_set_hvac_mode(HVACMode.OFF)


class KoolnovaConnectivitySensor(SensorEntity):
    """Single sensor holding all connectivity information of the Koolnova system."""

    _attr_has_entity_name = True
    _attr_translation_key = "connectivity_status"
    _attr_icon = "mdi:router-wireless"
    _attr_should_poll = False

    def __init__(self, coordinator, config_entry):
        """Initialize the connectivity sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_connectivity_status"

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def state(self):
        """Online/Offline, based on the state of the system."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return "Desconocido"

        topic_info = sensors[0].get("topic_info", {})
        is_online = topic_info.get("is_online")

        return "Online" if is_online else "Offline"

    @property
    def extra_state_attributes(self):
        """All connectivity attributes.

        Attribute keys are snake_case identifiers, not display strings: Home
        Assistant localises them through `state_attributes` in the translation
        files. Per-room timestamps live in a single `rooms_last_update` mapping
        because a dynamically named attribute per room could not be translated.
        """
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return {}

        # System-wide information
        topic_info = sensors[0].get("topic_info", {})
        attrs = {
            "wifi_signal": topic_info.get("rssi"),
            "online": topic_info.get("is_online"),
        }

        # Last update of the system
        system_last_sync = topic_info.get("last_sync")
        if system_last_sync:
            attrs["last_update"] = self._as_datetime(system_last_sync)

        # Last update of each room, keyed by room name
        rooms_last_update = {}
        for sensor in sensors:
            room_name = sensor.get("Room_Name", f"room_{sensor.get('Room_id')}")
            room_last_sync = sensor.get("topic_info", {}).get("last_sync")

            if room_last_sync:
                rooms_last_update[room_name] = self._as_datetime(room_last_sync)

        attrs["rooms_last_update"] = rooms_last_update

        return attrs

    @staticmethod
    def _as_datetime(value):
        """Parse an API timestamp, falling back to the raw string."""
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value


class KoolnovaHubEntity(ClimateEntity):
    """Hub entity for legacy hub-based controllers.

    Exposes ON/OFF (as HVACMode AUTO/OFF) and the behavior mode
    (manual / auto / planning). Hub accounts are the older Koolnova
    controllers; newer zone-based systems have no hub.
    """

    _attr_translation_key = "koolnova_hub"
    _attr_should_poll = False
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.OFF]

    def __init__(self, coordinator, config_entry, hub):
        """Initialize the hub entity."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._hub = hub
        self._hub_id = hub["Hub_id"]

        self._attr_name = f"Koolnova Hub {self._hub_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_hub_{self._hub_id}"
        self._attr_supported_features = (
            ClimateEntityFeature.PRESET_MODE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    def _update_hub_data(self):
        """Update local hub data from coordinator."""
        for hub in self.coordinator.data.get("hubs", []):
            if hub.get("Hub_id") == self._hub_id:
                self._hub = hub
                break

    @property
    def hvac_mode(self):
        """Return current HVAC mode (AUTO = on, OFF = off)."""
        self._update_hub_data()
        return HVACMode.AUTO if self._hub.get("State") else HVACMode.OFF

    @property
    def preset_modes(self):
        """Return available hub behavior modes."""
        return ["manual", "auto", "planning"]

    @property
    def preset_mode(self):
        """Return current hub behavior mode."""
        self._update_hub_data()
        return self._hub.get("Mode")

    async def async_set_hvac_mode(self, hvac_mode):
        """Turn the hub on (AUTO) or off."""
        state = (hvac_mode == HVACMode.AUTO)
        try:
            result = await self.coordinator.hass.async_add_executor_job(
                self.coordinator.client.set_hub_state, self._hub_id, state
            )
            self._hub.update({"State": result.get("state"), "Mode": result.get("mode")})
            self.async_write_ha_state()
        except Exception as err:
            _fallo(self.hass, "Koolnova Hub", f"Error setting hub {self._hub_id} state", err)

    async def async_set_preset_mode(self, preset_mode):
        """Set the hub behavior mode (manual / auto / planning)."""
        try:
            result = await self.coordinator.hass.async_add_executor_job(
                self.coordinator.client.set_hub_mode, self._hub_id, preset_mode
            )
            self._hub.update({"State": result.get("state"), "Mode": result.get("mode")})
            self.async_write_ha_state()
        except Exception as err:
            _fallo(self.hass, "Koolnova Hub", f"Error setting hub {self._hub_id} mode", err)

    async def async_turn_on(self):
        """Turn the hub on."""
        await self.async_set_hvac_mode(HVACMode.AUTO)

    async def async_turn_off(self):
        """Turn the hub off."""
        await self.async_set_hvac_mode(HVACMode.OFF)
