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

    def test_hub_failure_raises(self):
        coord = coordinator()
        coord.hass.async_add_executor_job = AsyncMock(side_effect=RuntimeError("x"))
        hub = self.entidad(climate_mod.KoolnovaHubEntity, coord, {"Hub_id": "h1", "State": True})
        with self.assertRaises(HomeAssistantError):
            run(hub.async_set_preset_mode("auto"))


if __name__ == "__main__":
    unittest.main()
