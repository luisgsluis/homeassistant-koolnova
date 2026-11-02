"""Tests for the zone humidity/CO2 sensors and the coordinator cache.

These need Home Assistant itself, so they are skipped where it isn't installed (the CI job
only has the standard library + requests). Run them inside the HA container:

    docker cp tests homeassistant:/tmp/kt && docker cp custom_components homeassistant:/tmp/kc
    docker exec -w /tmp homeassistant sh -c 'mkdir -p kr && cp -r kt kr/tests && cp -r kc kr/custom_components && cd kr && python -m unittest tests.test_sensor -v'
(run it on its own: other test modules stub `custom_components` in sys.modules, which makes this one skip under `discover`)
"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

try:
    from custom_components.koolnova import sensor as sensor_mod
    from custom_components.koolnova.const import DOMAIN
    from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator
    from homeassistant.components.sensor import SensorDeviceClass
    HAVE_HA = True
except ImportError:  # no Home Assistant in this environment
    HAVE_HA = False

ENTRY_ID = "entry1"


def zone(room_id, name, humidity=None, co2=None):
    return {"Room_id": room_id, "Room_Name": name, "Room_humidity": humidity, "Room_co2": co2}


class FakeCoordinator:
    """The bits of the coordinator the sensor platform touches."""

    def __init__(self, sensors):
        self.data = {"sensors": sensors}
        self.last_update_success = True
        self.listeners = []

    def async_add_listener(self, cb, context=None):
        self.listeners.append(cb)
        return lambda: self.listeners.remove(cb)

    def refresh(self):
        for cb in list(self.listeners):
            cb()


@unittest.skipUnless(HAVE_HA, "needs Home Assistant")
class SensorPlatformTest(unittest.TestCase):
    def setUp(self):
        self.added = []
        self.unloads = []
        self.entry = SimpleNamespace(entry_id=ENTRY_ID, async_on_unload=self.unloads.append)

    def setup(self, sensors):
        self.coord = FakeCoordinator(sensors)
        hass = SimpleNamespace(data={DOMAIN: {ENTRY_ID: self.coord}})
        asyncio.run(sensor_mod.async_setup_entry(hass, self.entry, lambda ents, **kw: self.added.extend(ents)))

    def uids(self):
        return sorted(e.unique_id for e in self.added)

    def test_only_zones_with_a_value_get_entities(self):
        self.setup([zone(1, "A", humidity=50.0), zone(2, "B"), zone(3, "C", humidity=40.0, co2=600)])
        self.assertEqual(
            self.uids(),
            [f"{ENTRY_ID}_zone_1_humidity", f"{ENTRY_ID}_zone_3_co2", f"{ENTRY_ID}_zone_3_humidity"],
        )

    def test_unique_id_and_name_of_humidity_keep_the_2_1_0_format(self):
        self.setup([zone(7, "Salon", humidity=50.0)])
        e = self.added[0]
        self.assertEqual(e.unique_id, f"{ENTRY_ID}_zone_7_humidity")
        self.assertEqual(e.name, "Koolnova Salon Humidity")

    def test_device_classes_units_and_values(self):
        self.setup([zone(1, "A", humidity=51.5, co2=700)])
        by = {e.unique_id.rsplit("_", 1)[1]: e for e in self.added}
        self.assertEqual(by["humidity"].device_class, SensorDeviceClass.HUMIDITY)
        self.assertEqual(by["humidity"].native_unit_of_measurement, "%")
        self.assertEqual(by["humidity"].native_value, 51.5)
        self.assertEqual(by["co2"].device_class, SensorDeviceClass.CO2)
        self.assertEqual(by["co2"].native_unit_of_measurement, "ppm")
        self.assertEqual(by["co2"].native_value, 700)

    def test_no_data_yet_creates_nothing_and_does_not_crash(self):
        self.setup([])
        self.coord.data = None
        self.coord.refresh()
        self.assertEqual(self.added, [])

    def test_a_zone_that_starts_reporting_later_gets_its_entity(self):
        self.setup([zone(1, "A"), zone(2, "B", humidity=45.0)])
        self.assertEqual(self.uids(), [f"{ENTRY_ID}_zone_2_humidity"])
        self.coord.data["sensors"][0]["Room_humidity"] = 48.0
        self.coord.data["sensors"][0]["Room_co2"] = 500
        self.coord.refresh()
        self.assertEqual(
            self.uids(),
            [f"{ENTRY_ID}_zone_1_co2", f"{ENTRY_ID}_zone_1_humidity", f"{ENTRY_ID}_zone_2_humidity"],
        )

    def test_entities_are_not_added_twice(self):
        self.setup([zone(1, "A", humidity=50.0)])
        for _ in range(3):
            self.coord.refresh()
        self.assertEqual(len(self.added), 1)

    def test_a_new_zone_appearing_later_is_picked_up(self):
        self.setup([zone(1, "A", humidity=50.0)])
        self.coord.data["sensors"].append(zone(9, "New", humidity=30.0))
        self.coord.refresh()
        self.assertIn(f"{ENTRY_ID}_zone_9_humidity", self.uids())

    def test_the_listener_is_registered_for_removal_on_unload(self):
        self.setup([zone(1, "A")])
        self.assertEqual(len(self.coord.listeners), 1)
        self.assertEqual(len(self.unloads), 1)
        self.unloads[0]()
        self.assertEqual(self.coord.listeners, [])

    def test_entity_becomes_unavailable_when_the_value_goes_null_and_back(self):
        self.setup([zone(1, "A", humidity=50.0)])
        e = self.added[0]
        self.assertTrue(e.available)
        self.coord.data["sensors"][0]["Room_humidity"] = None
        self.assertFalse(e.available)
        self.assertIsNone(e.native_value)
        self.coord.data["sensors"][0]["Room_humidity"] = 52.0
        self.assertTrue(e.available)
        self.assertEqual(e.native_value, 52.0)

    def test_entity_unavailable_when_the_coordinator_failed(self):
        self.setup([zone(1, "A", humidity=50.0)])
        self.coord.last_update_success = False
        self.assertFalse(self.added[0].available)

    def test_entity_follows_its_own_zone_by_id(self):
        self.setup([zone(1, "A", humidity=50.0), zone(2, "B", humidity=60.0)])
        e2 = next(e for e in self.added if e.unique_id.endswith("zone_2_humidity"))
        self.coord.data["sensors"].reverse()
        self.assertEqual(e2.native_value, 60.0)


@unittest.skipUnless(HAVE_HA, "needs Home Assistant")
class CoordinatorCacheTest(unittest.TestCase):
    def make(self, **extra):
        coord = KoolnovaDataUpdateCoordinator.__new__(KoolnovaDataUpdateCoordinator)
        row = {"Room_id": 1, "Room_humidity": 50.0, "Room_co2": 600}
        row.update(extra)
        coord.data = {"sensors": [row]}
        return coord

    def put(self, coord, **fields):
        body = {"id": 1, "name": "A", "status": "03", "speed": "2", "temperature": 22.0,
                "setpoint_temperature": 22.0, "updated_at": "x", "topic_info": {"id": 5}}
        body.update(fields)
        self.assertTrue(coord._update_sensor_in_cache(1, body))
        return coord.data["sensors"][0]

    def test_put_without_humidity_or_co2_keeps_the_cached_values(self):
        row = self.put(self.make())
        self.assertEqual(row["Room_humidity"], 50.0)
        self.assertEqual(row["Room_co2"], 600)

    def test_put_with_humidity_and_co2_overwrites_them(self):
        row = self.put(self.make(), humidity=55.0, co2=650)
        self.assertEqual(row["Room_humidity"], 55.0)
        self.assertEqual(row["Room_co2"], 650)

    def test_put_for_unknown_sensor_changes_nothing(self):
        coord = self.make()
        self.assertFalse(coord._update_sensor_in_cache(99, {"id": 99}))


if __name__ == "__main__":
    unittest.main()
