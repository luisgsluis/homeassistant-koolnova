"""A project mode change is confirmed against what the system reports, not the PATCH answer.

Koolnova answers a mode PATCH with the requested mode at once, but the system applies it later or
not at all. After a change, the polls read the projects instead of the sensors (no extra request)
until the system reports the mode or MODE_CHANGE_TIMEOUT passes.

Needs Home Assistant, so it is skipped where it isn't installed. Run it on its own, the same way
as tests/test_sensor.py (other modules stub `custom_components`).
"""

import asyncio
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from custom_components.koolnova import climate as climate_mod
    from custom_components.koolnova import coordinator as coordinator_mod
    from custom_components.koolnova.const import MODE_CHANGE_TIMEOUT
    from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator
    from homeassistant.components.climate import HVACMode
    HAVE_HA = True
except ImportError:  # no Home Assistant in this environment
    HAVE_HA = False

ENTRY = SimpleNamespace(entry_id="e1", options={}, data={})
TOPIC = 7


def run(coro):
    return asyncio.run(coro)


def project(mode, topic_id=TOPIC):
    return {"Topic_id": topic_id, "Mode": mode, "is_online": True, "eco": False,
            "is_stop": False, "last_sync": "2026-01-01T00:00:00"}


def make_coordinator(cached_mode="1", system_mode="1"):
    """Coordinator with a cache, whose API reports `system_mode` for the project."""
    coord = KoolnovaDataUpdateCoordinator.__new__(KoolnovaDataUpdateCoordinator)
    coord.hass = MagicMock()
    coord.hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
    coord.client = MagicMock()
    coord.client.get_project.side_effect = lambda: [project(system_mode)]
    coord.client.get_sensors.return_value = [{"Room_id": 1, "Room_Name": "A", "topic_info": {}}]
    coord.client.update_project.side_effect = lambda topic_id, body: {"id": topic_id, **body}
    coord.config_entry = ENTRY
    coord.data = {"projects": [project(cached_mode)], "sensors": [{"Room_id": 1}], "hubs": []}
    coord._project_update_counter = 0
    coord._project_update_frequency = 10
    coord._pending_modes = {}
    coord.async_update_listeners = MagicMock()
    return coord


def fired_update_types(coord):
    return [c.args[1]["update_type"] for c in coord.hass.bus.async_fire.call_args_list]


@unittest.skipUnless(HAVE_HA, "needs Home Assistant")
class PendingModeCoordinatorTest(unittest.TestCase):
    def setUp(self):
        self.notify = patch.object(coordinator_mod, "async_create").start()
        self.addCleanup(patch.stopall)

    def change_mode(self, coord, code):
        run(coord.async_update_project_data(TOPIC, {"mode": code}))

    def test_mode_patch_marks_the_mode_pending(self):
        coord = make_coordinator(cached_mode="1", system_mode="1")
        self.change_mode(coord, "2")
        self.assertEqual(coord.pending_mode(TOPIC), "2")
        self.assertEqual(coord.data["projects"][0]["Mode"], "2")  # the PATCH answer, as before

    def test_other_project_patches_mark_nothing(self):
        coord = make_coordinator()
        run(coord.async_update_project_data(TOPIC, {"eco": True}))
        self.assertIsNone(coord.pending_mode(TOPIC))

    def test_while_pending_polls_read_projects_instead_of_sensors(self):
        coord = make_coordinator(cached_mode="1", system_mode="1")
        self.change_mode(coord, "2")
        result = run(coord._async_update_data())
        coord.client.get_project.assert_called_once()
        coord.client.get_sensors.assert_not_called()
        self.assertEqual(result["sensors"], [{"Room_id": 1}])  # kept from the cache
        self.assertEqual(fired_update_types(coord), ["projects_only"])

    def test_while_pending_the_requested_mode_is_shown(self):
        coord = make_coordinator(cached_mode="1", system_mode="1")
        self.change_mode(coord, "2")
        result = run(coord._async_update_data())
        self.assertEqual(result["projects"][0]["Mode"], "2")
        self.assertEqual(coord.pending_mode(TOPIC), "2")
        self.notify.assert_not_called()

    def test_confirmed_mode_ends_the_wait(self):
        coord = make_coordinator(cached_mode="1", system_mode="2")
        self.change_mode(coord, "2")
        result = run(coord._async_update_data())
        self.assertEqual(result["projects"][0]["Mode"], "2")
        self.assertIsNone(coord.pending_mode(TOPIC))
        coord.data = result
        run(coord._async_update_data())  # back to the normal sensors-only polls
        coord.client.get_sensors.assert_called_once()
        self.notify.assert_not_called()

    def test_timeout_shows_the_real_mode_and_notifies(self):
        coord = make_coordinator(cached_mode="1", system_mode="1")
        self.change_mode(coord, "2")
        with patch.object(coordinator_mod.time, "monotonic",
                          return_value=time.monotonic() + MODE_CHANGE_TIMEOUT + 1):
            result = run(coord._async_update_data())
        self.assertEqual(result["projects"][0]["Mode"], "1")
        self.assertIsNone(coord.pending_mode(TOPIC))
        self.notify.assert_called_once()

    def test_reading_projects_resets_the_project_counter(self):
        coord = make_coordinator()
        coord._project_update_counter = 9
        self.change_mode(coord, "2")
        run(coord._async_update_data())
        self.assertEqual(coord._project_update_counter, 0)

    def test_failed_read_keeps_the_mode_pending_and_polls_as_usual(self):
        coord = make_coordinator()
        self.change_mode(coord, "2")
        coord.client.get_project.side_effect = RuntimeError("timeout")
        run(coord._async_update_data())
        coord.client.get_sensors.assert_called_once()
        self.assertEqual(coord.pending_mode(TOPIC), "2")
        self.assertEqual(fired_update_types(coord), ["sensors_only"])

    def test_failed_read_after_the_timeout_stops_waiting(self):
        coord = make_coordinator()
        self.change_mode(coord, "2")
        coord._pending_modes[TOPIC] = ("2", time.monotonic() - 1)
        coord.client.get_project.side_effect = RuntimeError("timeout")
        run(coord._async_update_data())
        self.assertIsNone(coord.pending_mode(TOPIC))

    def test_projects_endpoint_down_uses_the_devices_fallback(self):
        # /topics/ down, /devices/ up: a pending change must not leave the integration without data
        coord = make_coordinator()
        self.change_mode(coord, "2")
        coord.client.get_project.side_effect = RuntimeError("HTTP 404")
        coord.client.get_sensors.side_effect = RuntimeError("HTTP 404")
        coord.client.get_devices.return_value = [{"sensor": {
            "id": 1, "name": "A", "status": "03", "topic_info": {"id": TOPIC, "mode": "1"}}}]
        coord._fetch_hubs = lambda: []
        for _ in range(3):
            result = run(coord._async_update_data())
            self.assertEqual(result["sensors"][0]["Room_id"], 1)

    def test_only_the_changed_project_is_kept_on_the_request(self):
        coord = make_coordinator()
        coord.client.get_project.side_effect = lambda: [project("1"), project("1", topic_id=8)]
        coord.data["projects"].append(project("1", topic_id=8))
        self.change_mode(coord, "2")
        result = run(coord._async_update_data())
        self.assertEqual([p["Mode"] for p in result["projects"]], ["2", "1"])

    def test_no_pending_mode_keeps_sensors_only_polls(self):
        coord = make_coordinator()
        run(coord._async_update_data())
        coord.client.get_project.assert_not_called()
        coord.client.get_sensors.assert_called_once()
        self.assertEqual(fired_update_types(coord), ["sensors_only"])


@unittest.skipUnless(HAVE_HA, "needs Home Assistant")
class PendingModeAttributeTest(unittest.TestCase):
    def entity(self, coord):
        e = climate_mod.KoolnovaProjectEntity(coord, ENTRY, coord.data["projects"][0])
        e.hass = MagicMock()
        e.async_write_ha_state = MagicMock()
        return e

    def test_pending_mode_attribute(self):
        coord = make_coordinator(cached_mode="1")
        entity = self.entity(coord)
        self.assertIsNone(entity.extra_state_attributes["pending_mode"])
        coord.expect_project_mode(TOPIC, "4")
        self.assertEqual(entity.extra_state_attributes["pending_mode"], HVACMode.HEAT.value)

    def test_set_hvac_mode_marks_the_mode_pending(self):
        coord = make_coordinator(cached_mode="1")
        entity = self.entity(coord)
        run(entity.async_set_hvac_mode(HVACMode.HEAT))
        self.assertEqual(entity.extra_state_attributes["pending_mode"], HVACMode.HEAT.value)


if __name__ == "__main__":
    unittest.main()
