"""Tests for the Koolnova <-> Home Assistant code tables.

`const.py` imports from Home Assistant, which is not installed here, so a minimal stub
of `homeassistant.components.climate` is registered before importing it. The stub uses
Home Assistant's real string values, which is what the mappings ultimately produce.

These tables are easy to get subtly wrong — the project modes were read as 1 cool, 2 off,
4 heat, 6 auto for a long time, while Koolnova's web app defines 2 as heating and 4 as radiant
floor — and a wrong entry silently heats the house when asked to cool.
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
        """Codes as defined by Koolnova's web app (`app-topic-modes`)."""
        self.assertEqual(
            const.KOOLNOVA_TO_HVAC_MODE,
            {
                "0": "fan_only",  # ventilation
                "1": "cool",      # cooling (air)
                "2": "heat",      # heating (air)
                "3": "dry",       # dehumidification
                "4": "heat",      # radiant floor
                "5": "cool",      # floor cooling + cold air
                "6": "heat",      # radiant floor + hot air
            },
        )

    def test_candidates_cover_every_code_once(self):
        codes = [c for cands in const.HVAC_TO_KOOLNOVA_MODE_CANDIDATES.values() for c in cands]
        self.assertCountEqual(codes, const.KOOLNOVA_TO_HVAC_MODE.keys())

    def test_candidates_decode_to_their_mode(self):
        for mode, codes in const.HVAC_TO_KOOLNOVA_MODE_CANDIDATES.items():
            for code in codes:
                with self.subTest(mode=mode, code=code):
                    self.assertEqual(const.KOOLNOVA_TO_HVAC_MODE[code], mode)

    def test_air_codes_are_preferred(self):
        self.assertEqual(const.HVAC_TO_KOOLNOVA_MODE_CANDIDATES["heat"][0], "2")
        self.assertEqual(const.HVAC_TO_KOOLNOVA_MODE_CANDIDATES["cool"][0], "1")


class TopicModesTest(unittest.TestCase):
    """TopicModes: "0"/"1" per position, index N enables mode N."""

    def test_enabled_codes(self):
        self.assertEqual(const.enabled_mode_codes("11110001"), ["0", "1", "2", "3"])
        self.assertEqual(const.enabled_mode_codes("0110000"), ["1", "2"])
        self.assertEqual(const.enabled_mode_codes("0000101"), ["4", "6"])

    def test_positions_without_a_known_code_are_ignored(self):
        self.assertEqual(const.enabled_mode_codes("00000001"), [])
        self.assertEqual(const.enabled_mode_codes("01x1"), ["1", "3"])

    def test_unknown_falls_back_to_air_cool_and_heat(self):
        for value in (None, "", 11110001, ["1"]):
            with self.subTest(value=value):
                self.assertEqual(const.enabled_mode_codes(value), ["1", "2"])
                self.assertEqual(const.enabled_hvac_modes(value), ["heat", "cool"])

    def test_enabled_hvac_modes(self):
        self.assertEqual(const.enabled_hvac_modes("11110001"), ["heat", "cool", "dry", "fan_only"])
        self.assertEqual(const.enabled_hvac_modes("0110000"), ["heat", "cool"])
        self.assertEqual(const.enabled_hvac_modes("0000100"), ["heat"])  # radiant floor only
        self.assertEqual(const.enabled_hvac_modes("0000011"), ["heat", "cool"])  # floor + air
        self.assertEqual(const.enabled_hvac_modes("0000000"), [])

    def test_mode_code_for(self):
        self.assertEqual(const.mode_code_for("heat", "11110001"), "2")
        self.assertEqual(const.mode_code_for("cool", "11110001"), "1")
        self.assertEqual(const.mode_code_for("dry", "11110001"), "3")
        self.assertEqual(const.mode_code_for("fan_only", "11110001"), "0")

    def test_mode_code_for_picks_the_first_enabled_code(self):
        self.assertEqual(const.mode_code_for("heat", "0010101"), "2")  # air heat over floor
        self.assertEqual(const.mode_code_for("heat", "0000101"), "6")  # floor + air over floor only
        self.assertEqual(const.mode_code_for("heat", "0000100"), "4")  # floor only
        self.assertEqual(const.mode_code_for("cool", "0000011"), "5")

    def test_mode_code_for_disabled_or_unknown_mode(self):
        self.assertIsNone(const.mode_code_for("dry", "0110000"))
        self.assertIsNone(const.mode_code_for("off", "11111111"))
        self.assertIsNone(const.mode_code_for("auto", "11111111"))
        self.assertEqual(const.mode_code_for("heat", None), "2")
        self.assertIsNone(const.mode_code_for("dry", None))


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
        for mode in const.DEFAULT_PROJECT_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.AVAILABLE_PROJECT_HVAC_MODES)
        for mode in const.DEFAULT_ZONE_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.AVAILABLE_ZONE_HVAC_MODES)

    def test_default_project_modes_do_not_filter(self):
        self.assertEqual(const.DEFAULT_PROJECT_HVAC_MODES, const.AVAILABLE_PROJECT_HVAC_MODES)

    def test_every_available_mode_can_be_encoded(self):
        for mode in const.AVAILABLE_PROJECT_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.HVAC_TO_KOOLNOVA_MODE_CANDIDATES)
        for mode in const.AVAILABLE_ZONE_HVAC_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, const.HVAC_TO_KOOLNOVA_ZONE_STATUS)

    def test_default_precision_is_selectable(self):
        self.assertIn(const.DEFAULT_TEMP_PRECISION, const.AVAILABLE_TEMP_PRECISIONS)


class PlatformsTest(unittest.TestCase):
    def test_domain_and_platforms(self):
        self.assertEqual(const.DOMAIN, "koolnova")
        self.assertEqual(const.PLATFORMS, ["climate", "binary_sensor", "switch", "sensor"])


if __name__ == "__main__":
    unittest.main()
