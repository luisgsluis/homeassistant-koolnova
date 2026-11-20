"""Service calls of the climate entities: a failure must reach the caller and must not leave the
global mode showing what was not applied.

Needs Home Assistant, so it is skipped where it isn't installed. Run it inside the HA container
the same way as tests/test_sensor.py (on its own: other modules stub `custom_components`).
"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from custom_components.koolnova import climate as climate_mod
    from homeassistant.components.climate import FAN_HIGH, HVACMode
    from homeassistant.exceptions import HomeAssistantError
    HAVE_HA = True
except ImportError:  # no Home Assistant in this environment
    HAVE_HA = False

ENTRY = SimpleNamespace(entry_id="e1", options={}, data={})


def coordinator(**metodos):
    c = SimpleNamespace(data={"sensors": [{"Room_id": 1, "Room_Name": "Salón"}], "projects": [], "hubs": []},
                        hass=MagicMock(), client=MagicMock())
    for k, v in metodos.items():
        setattr(c, k, v)
    return c


def run(coro):
    return asyncio.run(coro)


@unittest.skipUnless(HAVE_HA, "needs Home Assistant")
class ClimateServiceTest(unittest.TestCase):
    def setUp(self):
        self.notif = patch.object(climate_mod, "async_create").start()
        self.addCleanup(patch.stopall)

    def entidad(self, cls, coord, *args):
        e = cls(coord, ENTRY, *args)
        e.hass = MagicMock()
        e.async_write_ha_state = MagicMock()
        return e

    def proyecto(self, **metodos):
        return self.entidad(climate_mod.KoolnovaProjectEntity, coordinator(**metodos), {"Topic_id": 7})

    def test_zone_failure_raises(self):
        coord = coordinator(async_update_sensor_data=AsyncMock(side_effect=RuntimeError("HTTP 500")))
        zona = self.entidad(climate_mod.KoolnovaZoneEntity, coord, {"Room_id": 1, "Room_Name": "Salón"})
        with self.assertRaises(HomeAssistantError):
            run(zona.async_set_temperature(temperature=22))
        self.notif.assert_called_once()

    def test_zone_unknown_fan_mode_is_not_sent(self):
        coord = coordinator(async_update_sensor_data=AsyncMock())
        zona = self.entidad(climate_mod.KoolnovaZoneEntity, coord, {"Room_id": 1, "Room_Name": "Salón"})
        run(zona.async_set_fan_mode("turbo"))
        coord.async_update_sensor_data.assert_not_called()

    def test_global_fan_all_failed_raises_and_keeps_mode(self):
        p = self.proyecto(async_update_all_sensors_fan_speed=AsyncMock(return_value={"updated": 0, "failed": 3}))
        antes = p.fan_mode
        with self.assertRaises(HomeAssistantError):
            run(p.async_set_fan_mode(FAN_HIGH))
        self.assertEqual(p.fan_mode, antes)

    def test_global_fan_exception_keeps_mode(self):
        p = self.proyecto(async_update_all_sensors_fan_speed=AsyncMock(side_effect=RuntimeError("timeout")))
        antes = p.fan_mode
        with self.assertRaises(HomeAssistantError):
            run(p.async_set_fan_mode(FAN_HIGH))
        self.assertEqual(p.fan_mode, antes)
        p.async_write_ha_state.assert_not_called()

    def test_global_partial_applies_and_notifies(self):
        p = self.proyecto(async_update_all_sensors_fan_speed=AsyncMock(return_value={"updated": 2, "failed": 1}))
        run(p.async_set_fan_mode(FAN_HIGH))
        self.assertEqual(p.fan_mode, FAN_HIGH)
        self.notif.assert_called_once()

    def test_turn_off_all_failed_raises_and_keeps_mode(self):
        p = self.proyecto(async_update_all_sensors_status=AsyncMock(return_value={"updated": 0, "failed": 2}))
        with self.assertRaises(HomeAssistantError):
            run(p.async_turn_off())
        self.assertEqual(p._global_zone_hvac_mode, HVACMode.AUTO)

    def test_turn_off_ok(self):
        p = self.proyecto(async_update_all_sensors_status=AsyncMock(return_value={"updated": 2, "failed": 0}))
        run(p.async_turn_off())
        self.assertEqual(p._global_zone_hvac_mode, HVACMode.OFF)
        self.notif.assert_not_called()

    def test_global_temperature_failure_raises(self):
        p = self.proyecto(async_update_all_sensors_temperature=AsyncMock(side_effect=RuntimeError("x")))
        with self.assertRaises(HomeAssistantError):
            run(p.async_set_temperature(temperature=22))

    def test_project_mode_failure_raises(self):
        p = self.proyecto(async_update_project_data=AsyncMock(side_effect=RuntimeError("x")))
        with self.assertRaises(HomeAssistantError):
            run(p.async_set_hvac_mode(p.hvac_modes[0]))

    def proyecto_modos(self, topic_modes, mode="2", options=None, **metodos):
        coord = coordinator(**metodos)
        coord.data["projects"] = [{"Topic_id": 7, "Mode": mode, "Topic_modes": topic_modes,
                                   "is_online": True, "eco": False, "is_stop": False}]
        entry = SimpleNamespace(entry_id="e1", options=options or {}, data={})
        e = climate_mod.KoolnovaProjectEntity(coord, entry, {"Topic_id": 7})
        e.hass = MagicMock()
        e.async_write_ha_state = MagicMock()
        return e

    def test_project_modes_come_from_topic_modes(self):
        self.assertEqual(self.proyecto_modos("11110001").hvac_modes,
                         [HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY])
        self.assertEqual(self.proyecto_modos("0110000").hvac_modes, [HVACMode.HEAT, HVACMode.COOL])
        self.assertEqual(self.proyecto_modos(None).hvac_modes, [HVACMode.HEAT, HVACMode.COOL])

    def test_project_modes_option_narrows_down(self):
        p = self.proyecto_modos("11110001", options={"project_hvac_modes": ["cool", "heat"]})
        self.assertEqual(p.hvac_modes, [HVACMode.HEAT, HVACMode.COOL])

    def test_project_modes_option_never_adds_a_disabled_mode(self):
        p = self.proyecto_modos("0110000", options={"project_hvac_modes": ["cool", "dry"]})
        self.assertEqual(p.hvac_modes, [HVACMode.COOL])

    def test_project_modes_option_with_nothing_left_offers_every_enabled_mode(self):
        p = self.proyecto_modos("0110000", options={"project_hvac_modes": ["off", "auto"]})
        self.assertEqual(p.hvac_modes, [HVACMode.HEAT, HVACMode.COOL])

    def test_project_mode_reads_heating_as_heat(self):
        coord_on = {"Room_id": 1, "Room_Name": "Salón", "Room_status": "03"}
        for code, expected in (("2", HVACMode.HEAT), ("1", HVACMode.COOL), ("4", HVACMode.HEAT),
                               ("6", HVACMode.HEAT), ("5", HVACMode.COOL), ("3", HVACMode.DRY),
                               ("0", HVACMode.FAN_ONLY)):
            with self.subTest(code=code):
                p = self.proyecto_modos("11111111", mode=code)
                p.coordinator.data["sensors"] = [dict(coord_on)]
                self.assertEqual(p.hvac_mode, expected)
                self.assertEqual(p.extra_state_attributes["compressor_mode"], expected.value)
                self.assertEqual(p.extra_state_attributes["project_mode_code"], code)

    def test_set_project_mode_sends_the_first_enabled_code(self):
        for topic_modes, mode, code in (("11110001", HVACMode.HEAT, "2"), ("11110001", HVACMode.COOL, "1"),
                                        ("11110001", HVACMode.DRY, "3"), ("11110001", HVACMode.FAN_ONLY, "0"),
                                        ("0000101", HVACMode.HEAT, "6"), ("0000100", HVACMode.HEAT, "4"),
                                        ("0000010", HVACMode.COOL, "5")):
            with self.subTest(topic_modes=topic_modes, mode=mode):
                p = self.proyecto_modos(topic_modes, async_update_project_data=AsyncMock())
                run(p.async_set_hvac_mode(mode))
                p.coordinator.async_update_project_data.assert_awaited_once_with(7, {"mode": code})

    def test_set_project_mode_not_enabled_is_not_sent(self):
        p = self.proyecto_modos("0110000", async_update_project_data=AsyncMock())
        run(p.async_set_hvac_mode(HVACMode.DRY))
        p.coordinator.async_update_project_data.assert_not_called()

    def test_hub_failure_raises(self):
        coord = coordinator()
        coord.hass.async_add_executor_job = AsyncMock(side_effect=RuntimeError("x"))
        hub = self.entidad(climate_mod.KoolnovaHubEntity, coord, {"Hub_id": "h1", "State": True})
        with self.assertRaises(HomeAssistantError):
            run(hub.async_set_preset_mode("auto"))


if __name__ == "__main__":
    unittest.main()
