"""Tests for the Koolnova <-> Home Assistant code tables.

`const.py` imports from Home Assistant, which is not installed here, so a minimal stub
of `homeassistant.components.climate` is registered before importing it. The stub uses
Home Assistant's real string values, which is what the mappings ultimately produce.

These tables are easy to get subtly wrong — the project modes 4 and 6 were documented
swapped for a long time — and a wrong entry silently heats the house when asked to cool.
"""

import importlib.util
import sys
import types
import unittest
from enum import StrEnum
from pathlib import Path


def _install_home_assistant_stub():
    """Register a stand-in for the parts of Home Assistant that const.py imports."""
    if "homeassistant.components.climate" in sys.modules:
        return

    class HVACMode(StrEnum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        HEAT_COOL = "heat_cool"
        AUTO = "auto"
        DRY = "dry"
        FAN_ONLY = "fan_only"

    climate = types.ModuleType("homeassistant.components.climate")
    climate.HVACMode = HVACMode
    climate.FAN_LOW = "low"
    climate.FAN_MEDIUM = "medium"
    climate.FAN_HIGH = "high"
    climate.FAN_AUTO = "auto"

    homeassistant = types.ModuleType("homeassistant")
    components = types.ModuleType("homeassistant.components")
    components.climate = climate
    homeassistant.components = components

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.climate"] = climate


def _load_const():
    _install_home_assistant_stub()
    path = Path(__file__).resolve().parent.parent / "custom_components" / "koolnova" / "const.py"
    spec = importlib.util.spec_from_file_location("koolnova_const", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


const = _load_const()


class ProjectModeTest(unittest.TestCase):
    def test_project_mode_codes(self):
        self.assertEqual(
            const.KOOLNOVA_TO_HVAC_MODE,
            {"1": "cool", "2": "off", "4": "heat", "6": "auto"},
        )

    def test_project_mode_inverse_round_trips(self):
        for code, mode in const.KOOLNOVA_TO_HVAC_MODE.items():
            with self.subTest(code=code):
                self.assertEqual(const.HVAC_TO_KOOLNOVA_MODE[mode], code)


class ZoneStatusTest(unittest.TestCase):
    def test_zone_status_codes(self):
        self.assertEqual(
            const.KOOLNOVA_ZONE_STATUS_TO_HVAC,
            {"00": "cool", "01": "heat", "02": "off", "03": "auto"},
        )

    def test_zone_status_inverse_round_trips(self):
        for code, mode in const.KOOLNOVA_ZONE_STATUS_TO_HVAC.items():
            with self.subTest(code=code):
                self.assertEqual(const.HVAC_TO_KOOLNOVA_ZONE_STATUS[mode], code)

    def test_zone_and_project_encodings_stay_distinct(self):
        """Zone codes are zero-padded pairs, project codes are single digits."""
        self.assertTrue(all(len(code) == 2 for code in const.KOOLNOVA_ZONE_STATUS_TO_HVAC))
        self.assertTrue(all(len(code) == 1 for code in const.KOOLNOVA_TO_HVAC_MODE))


class FanSpeedTest(unittest.TestCase):
    def test_fan_speed_codes(self):
        self.assertEqual(
            const.KOOLNOVA_TO_FAN,
            {"1": "low", "2": "medium", "3": "high", "4": "auto"},
        )

    def test_fan_inverse_round_trips(self):
        for code, speed in const.KOOLNOVA_TO_FAN.items():
            with self.subTest(code=code):
                self.assertEqual(const.FAN_TO_KOOLNOVA[speed], code)


class LimitsTest(unittest.TestCase):
    def test_polling_never_goes_below_the_koolnova_ban_threshold(self):
        """Koolnova bans IPs polled more often than once every 30 s."""
        self.assertGreaterEqual(const.MIN_UPDATE_INTERVAL, 30)
        self.assertGreaterEqual(const.DEFAULT_UPDATE_INTERVAL, const.MIN_UPDATE_INTERVAL)

    def test_interval_bounds_are_ordered(self):
        self.assertLess(const.MIN_UPDATE_INTERVAL, const.MAX_UPDATE_INTERVAL)
        self.assertLessEqual(const.DEFAULT_UPDATE_INTERVAL, const.MAX_UPDATE_INTERVAL)

    def test_project_update_frequency_bounds_are_ordered(self):
        self.assertLessEqual(const.MIN_PROJECT_UPDATE_FREQUENCY, const.DEFAULT_PROJECT_UPDATE_FREQUENCY)
        self.assertLessEqual(const.DEFAULT_PROJECT_UPDATE_FREQUENCY, const.MAX_PROJECT_UPDATE_FREQUENCY)

    def test_temperature_defaults_sit_inside_the_configurable_range(self):
        self.assertLess(const.DEFAULT_MIN_TEMP, const.DEFAULT_MAX_TEMP)
        self.assertGreaterEqual(const.DEFAULT_MIN_TEMP, const.MIN_CONFIGURABLE_TEMP)
        self.assertLessEqual(const.DEFAULT_MAX_TEMP, const.MAX_CONFIGURABLE_TEMP)

    def test_default_modes_are_offered_by_the_config_flow(self):
        for mode in const.DEFAULT_PROJECT_HVAC_MODES + const.DEFAULT_ZONE_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.AVAILABLE_HVAC_MODES)

    def test_every_available_mode_can_be_encoded(self):
        for mode in const.AVAILABLE_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.HVAC_TO_KOOLNOVA_MODE)
                self.assertIn(mode, const.HVAC_TO_KOOLNOVA_ZONE_STATUS)

    def test_default_precision_is_selectable(self):
        self.assertIn(const.DEFAULT_TEMP_PRECISION, const.AVAILABLE_TEMP_PRECISIONS)


class PlatformsTest(unittest.TestCase):
    def test_domain_and_platforms(self):
        self.assertEqual(const.DOMAIN, "koolnova")
        self.assertEqual(const.PLATFORMS, ["climate", "binary_sensor", "switch", "sensor"])


if __name__ == "__main__":
    unittest.main()
