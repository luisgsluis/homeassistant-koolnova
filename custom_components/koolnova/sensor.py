"""Sensor entities for Koolnova: per-zone relative humidity and CO2."""

import logging
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZoneMeasurement:
    """One per-zone reading exposed as a sensor."""

    key: str  # suffix of the unique ID and of the entity ID
    label: str  # suffix of the entity name
    data_key: str  # key in the coordinator's sensor dicts
    device_class: SensorDeviceClass
    unit: str


# Plain string: HA's CONCENTRATION_PARTS_PER_MILLION constant is deprecated and its
# replacement (UnitOfRatio) is not available in every HA release this integration supports.
PPM = "ppm"

ZONE_MEASUREMENTS = (
    ZoneMeasurement("humidity", "Humidity", "Room_humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
    ZoneMeasurement("co2", "CO2", "Room_co2", SensorDeviceClass.CO2, PPM),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Create a sensor for every zone that reports a value, now or later.

    Zones without a probe return `null`, so they get no entity at startup. Because a
    zone can start reporting afterwards (probe added, firmware update, API change), the
    coordinator is checked on every refresh and the missing entities are added then.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known = set()

    def _add_new_entities():
        new = []
        for sensor in (coordinator.data or {}).get("sensors", []):
            for measurement in ZONE_MEASUREMENTS:
                uid = f"{entry.entry_id}_zone_{sensor['Room_id']}_{measurement.key}"
                if uid in known or sensor.get(measurement.data_key) is None:
                    continue
                known.add(uid)
                new.append(KoolnovaZoneSensor(coordinator, entry, sensor, measurement))
        if new:
            _LOGGER.debug("Adding %d Koolnova zone sensor(s)", len(new))
            async_add_entities(new, update_before_add=False)

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


class KoolnovaZoneSensor(SensorEntity):
    """A reading (humidity or CO2) reported by a single zone's thermostat."""

    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry, sensor, measurement):
        """Initialize the zone sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._sensor = sensor
        self._sensor_id = sensor["Room_id"]
        self._measurement = measurement

        self._attr_device_class = measurement.device_class
        self._attr_native_unit_of_measurement = measurement.unit
        self._attr_name = f"Koolnova {sensor['Room_Name']} {measurement.label}"
        self._attr_unique_id = f"{config_entry.entry_id}_zone_{sensor['Room_id']}_{measurement.key}"

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
            and self._sensor.get(self._measurement.data_key) is not None
        )

    @property
    def native_value(self):
        """Return the zone's reading."""
        self._update_sensor_data()
        return self._sensor.get(self._measurement.data_key)
