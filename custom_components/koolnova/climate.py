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

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Koolnova climate entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    if coordinator.data.get("projects"):
        proj = coordinator.data["projects"][0]
        entities.append(KoolnovaProjectEntity(coordinator, entry, proj))

    # Agregar sensor de conectividad único
    entities.append(KoolnovaConnectivitySensor(coordinator, entry))

    for sensor in coordinator.data.get("sensors", []):
        entities.append(KoolnovaZoneEntity(coordinator, entry, sensor))

    async_add_entities(entities, update_before_add=False)

class KoolnovaProjectEntity(ClimateEntity):
    """Project entity with global control: temperature, project HVAC mode, zone fan speed, and zone HVAC mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "koolnova_project" # Clave para que HA busque traducciones específicas.

    def __init__(self, coordinator, config_entry, project):
        """Initialize the project entity."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._project = project

        self._attr_unique_id = f"{config_entry.entry_id}_project"
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | 
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.PRESET_MODE
        )
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
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
        # Devolvemos los valores ('off', 'auto') que se usarán como claves en los ficheros de traducción.
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
        """Return current project HVAC mode."""
        self._update_project_data()
        current_mode = KOOLNOVA_TO_HVAC_MODE.get(self._project["Mode"], HVACMode.OFF)
        if current_mode not in self.hvac_modes:
            return HVACMode.OFF
        return current_mode

    @property
    def target_temperature(self):
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
    def current_temperature(self):
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

        # Obtener datos de conectividad del sistema desde sensores (más actualizados)
        system_connectivity = {}
        if sensors:
            topic_info = sensors[0].get("topic_info", {})  # Cualquier sensor tiene los mismos datos globales
            system_connectivity = {
                "system_rssi": topic_info.get("rssi"),
                "online_status": topic_info.get("is_online"),  # Más actualizado que del proyecto
                "last_sync": topic_info.get("last_sync"),      # Más actualizado que del proyecto
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
            _LOGGER.error("Error updating project mode: %s", err)
            async_create(
                self.hass, f"Error updating project mode: {err}", title="Koolnova Project Mode"
            )

    async def async_set_fan_mode(self, fan_mode):
        """Set global fan mode for ALL zones."""
        if fan_mode not in self.fan_modes:
            _LOGGER.error("Unsupported fan mode: %s. Available: %s", fan_mode, self.fan_modes)
            return

        speed_code = FAN_TO_KOOLNOVA.get(fan_mode)
        if not speed_code:
            _LOGGER.error("Fan mode not mapped: %s", fan_mode)
            return

        self._global_fan_mode = fan_mode
        self.async_write_ha_state()
        
        _LOGGER.info("Setting global fan mode to %s (speed: %s) for all zones", fan_mode, speed_code)

        try:
            result = await self.coordinator.async_update_all_sensors_fan_speed(speed_code)
            if result.get("failed", 0) > 0:
                async_create(
                    self.hass,
                    f"Global fan mode update completed with some failures: "
                    f"{result.get('updated', 0)} successful, {result.get('failed', 0)} failed",
                    title="Koolnova Global Fan Control",
                )
            else:
                _LOGGER.info("Global fan mode successfully updated to %s for all %d zones", fan_mode, result.get("updated", 0))
        except Exception as err:
            _LOGGER.error("Error setting global fan mode: %s", err)
            async_create(self.hass, f"Error setting global fan mode: {err}", title="Koolnova Global Fan Control")

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

        self._global_zone_hvac_mode = hvac_mode
        self.async_write_ha_state()

        _LOGGER.info("Setting global zone HVAC mode to %s (status: %s) for all zones", hvac_mode, status_code)

        try:
            result = await self.coordinator.async_update_all_sensors_status(status_code)
            if result.get("failed", 0) > 0:
                async_create(
                    self.hass,
                    f"Global zone HVAC mode update completed with some failures: "
                    f"{result.get('updated', 0)} successful, {result.get('failed', 0)} failed",
                    title="Koolnova Global Zone Control",
                )
            else:
                _LOGGER.info("Global zone HVAC mode successfully updated to %s for all %d zones", preset_mode, result.get("updated", 0))
        except Exception as err:
            _LOGGER.error("Error setting global zone HVAC mode: %s", err)
            async_create(self.hass, f"Error setting global zone HVAC mode: {err}", title="Koolnova Global Zone Control")


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
            if result.get("failed", 0) > 0:
                async_create(
                    self.hass,
                    f"Global temperature update completed with some failures: "
                    f"{result.get('updated', 0)} successful, {result.get('failed', 0)} failed",
                    title="Koolnova Global Temperature",
                )
            else:
                _LOGGER.info("Global temperature successfully updated to %s degrees for all %d zones", temp, result.get("updated", 0))
        except Exception as err:
            _LOGGER.error("Error setting global temperature: %s", err)
            async_create(self.hass, f"Error setting global temperature: {err}", title="Koolnova Global Temperature")

class KoolnovaZoneEntity(ClimateEntity):
    """Individual room zone as a climate device."""

    def __init__(self, coordinator, config_entry, sensor):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._sensor = sensor
        self._sensor_id = sensor["Room_id"]
        self._attr_name = f"Koolnova {sensor['Room_Name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_zone_{sensor['Room_id']}"
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
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
    def current_temperature(self):
        """Return current temperature."""
        self._update_sensor_data()
        return self._sensor.get("Room_actual_temp")

    @property
    def target_temperature(self):
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
            "system_last_sync": system_last_sync,  # Última sync del sistema
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
            _LOGGER.error("Error updating zone temperature for %s: %s", self._attr_name, err)
            async_create(self.hass, f"Error updating zone temperature: {err}", title="Koolnova")

    async def async_set_fan_mode(self, fan_mode):
        """Set fan mode."""
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
            _LOGGER.error("Error updating zone fan mode for %s: %s", self._attr_name, err)
            async_create(self.hass, f"Error updating zone fan mode: {err}", title="Koolnova")

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
            _LOGGER.error("Error updating zone HVAC mode for %s: %s", self._attr_name, err)
            async_create(self.hass, f"Error updating zone HVAC mode: {err}", title="Koolnova")


class KoolnovaConnectivitySensor(SensorEntity):
    """Sensor único con toda la información de conectividad del sistema Koolnova."""

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
        """Estado: Online/Offline basado en el sistema."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return "Desconocido"

        topic_info = sensors[0].get("topic_info", {})
        is_online = topic_info.get("is_online")

        return "Online" if is_online else "Offline"

    @property
    def extra_state_attributes(self):
        """Todos los atributos de conectividad."""
        sensors = self.coordinator.data.get("sensors", [])
        if not sensors:
            return {}

        # Información del sistema (global)
        topic_info = sensors[0].get("topic_info", {})
        attrs = {
            "Señal WiFi": topic_info.get("rssi"),
            "Online": topic_info.get("is_online"),
        }

        # Última actualización del sistema
        system_last_sync = topic_info.get("last_sync")
        if system_last_sync:
            try:
                attrs["Última actualización"] = datetime.fromisoformat(system_last_sync)
            except (ValueError, TypeError):
                attrs["Última actualización"] = system_last_sync

        # Última actualización de cada habitación
        for sensor in sensors:
            room_name = sensor.get("Room_Name", f"habitacion_{sensor.get('Room_id')}")
            sensor_topic_info = sensor.get("topic_info", {})
            room_last_sync = sensor_topic_info.get("last_sync")

            if room_last_sync:
                try:
                    attrs[f"Última actualización {room_name}"] = datetime.fromisoformat(room_last_sync)
                except (ValueError, TypeError):
                    attrs[f"Última actualización {room_name}"] = room_last_sync

        return attrs
