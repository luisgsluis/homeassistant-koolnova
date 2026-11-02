"""Sensor entities for Koolnova: per-zone relative humidity."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a humidity sensor for every zone that reports one.

    Zones without a humidity probe return `humidity: null`, so they get no entity.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        KoolnovaZoneHumiditySensor(coordinator, entry, sensor)
        for sensor in coordinator.data.get("sensors", [])
        if sensor.get("Room_humidity") is not None
    ]
    async_add_entities(entities, update_before_add=False)


class KoolnovaZoneHumiditySensor(SensorEntity):
    """Relative humidity reported by a single zone's thermostat."""

    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry, sensor):
        """Initialize the zone humidity sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._sensor = sensor
        self._sensor_id = sensor["Room_id"]

        self._attr_name = f"Koolnova {sensor['Room_Name']} Humidity"
        self._attr_unique_id = f"{config_entry.entry_id}_zone_{sensor['Room_id']}_humidity"

    async def async_added_to_hass(self):
        """Connect to coordinator."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    def _update_sensor_data(self):
        """Refresh local sensor data from the coordinator."""
        for sensor in self.coordinator.data.get("sensors", []):
            if sensor.get("Room_id") == self._sensor_id:
                self._sensor = sensor
                break

    @property
    def available(self):
        """Available while the coordinator is healthy and the zone reports a value."""
        self._update_sensor_data()
        return (
            self.coordinator.last_update_success
            and self._sensor.get("Room_humidity") is not None
        )

    @property
    def native_value(self):
        """Return the zone's relative humidity in percent."""
        self._update_sensor_data()
        return self._sensor.get("Room_humidity")
