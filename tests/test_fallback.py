"""The /devices/ fallback keeps what the project entity needs, TopicModes included.

Needs Home Assistant, so it is skipped where it isn't installed. Run it on its own, the same way
as tests/test_sensor.py (other modules stub `custom_components`).
"""

import unittest
from unittest.mock import MagicMock

try:
    from custom_components.koolnova.const import mode_code_for
    from custom_components.koolnova.coordinator import KoolnovaDataUpdateCoordinator
    from homeassistant.components.climate import HVACMode
    HAVE_HA = True
except ImportError:  # no Home Assistant in this environment
    HAVE_HA = False

TOPIC = {"id": 7, "name": "Main", "mode": "4",
         "configurations": [{"key": "TopicModes", "value": "01001001"}]}


def coordinator():
    c = KoolnovaDataUpdateCoordinator.__new__(KoolnovaDataUpdateCoordinator)
    c.client = MagicMock()
    c.client.get_devices.return_value = [
        {"sensor": {"id": 1, "name": "A", "status": "03", "topic_info": TOPIC}}]
    c._fetch_hubs = lambda: []
    c.data = {"projects": [{"Topic_id": 7, "Mode": "4", "Topic_modes": "01001001"}],
              "sensors": [], "hubs": []}
    return c


@unittest.skipUnless(HAVE_HA, "needs Home Assistant")
class FallbackTest(unittest.TestCase):
    def test_fallback_projects_carry_topic_modes(self):
        projects = coordinator()._fetch_data_fallback()["projects"]
        self.assertEqual(projects[0]["Topic_modes"], "01001001")

    def test_sensors_fallback_keeps_heat_on_radiant_floor(self):
        # Radiant-floor-only system: Heat must keep sending "4", not "2", after a fallback read
        c = coordinator()
        c.client.get_sensors.side_effect = RuntimeError("HTTP 500")
        project = c._fetch_sensors_only()["projects"][0]
        self.assertEqual(mode_code_for(HVACMode.HEAT, project["Topic_modes"]), "4")


if __name__ == "__main__":
    unittest.main()
