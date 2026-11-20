"""Service calls of the climate entities: a failure must reach the caller and must not leave the
global mode showing what was not applied; and the global control's on/off.

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
        p.coordinator.data["sensors"][0]["Room_status"] = "03"   # on: only the mode is sent
        with self.assertRaises(HomeAssistantError):
            run(p.async_set_hvac_mode(HVACMode.COOL))

    def test_hub_failure_raises(self):
        coord = coordinator()
        coord.hass.async_add_executor_job = AsyncMock(side_effect=RuntimeError("x"))
        hub = self.entidad(climate_mod.KoolnovaHubEntity, coord, {"Hub_id": "h1", "State": True})
        with self.assertRaises(HomeAssistantError):
            run(hub.async_set_preset_mode("auto"))


def control(*estados):
    """Coordinator with one zone per status ("02" off, "03" on) and the mocks the global control uses."""
    c = SimpleNamespace(
        data={"sensors": [{"Room_id": i, "Room_Name": f"Z{i}", "Room_status": st}
                          for i, st in enumerate(estados, 1)],
              "projects": [{"Topic_id": 7, "Mode": "1", "is_online": True, "eco": False, "is_stop": False}],
              "hubs": []},
        hass=MagicMock(), client=MagicMock())
    c.async_update_sensor_data = AsyncMock()
    c.async_update_project_data = AsyncMock()
    c.async_update_all_sensors_status = AsyncMock(return_value={"updated": len(estados), "failed": 0})
    return c


def apagar_todo(c):
    for s in c.data["sensors"]:
        s["Room_status"] = "02"


@unittest.skipUnless(HAVE_HA, "needs Home Assistant")
class GlobalOnOffTest(unittest.TestCase):
    """Global control on/off: Off only when every zone is off; Off remembers the zones that were
    on and turning back on restores only those."""

    def setUp(self):
        patch.object(climate_mod, "async_create").start()
        self.addCleanup(patch.stopall)

    def proyecto(self, c):
        e = climate_mod.KoolnovaProjectEntity(c, ENTRY, c.data["projects"][0])
        e.hass = MagicMock()
        e.async_write_ha_state = MagicMock()
        return e

    def zonas_encendidas(self, c):
        return [x.args for x in c.async_update_sensor_data.await_args_list]

    def test_off_is_selectable(self):
        self.assertEqual(self.proyecto(control("02")).hvac_modes, [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT])

    def test_off_listed_once_when_configured(self):
        c = control("02")
        p = self.proyecto(c)
        with patch.object(p, "_get_project_hvac_modes", return_value=[HVACMode.OFF, HVACMode.COOL]):
            self.assertEqual(p.hvac_modes, [HVACMode.OFF, HVACMode.COOL])

    def test_state_off_only_when_every_zone_is_off(self):
        c = control("02", "02", "02")
        p = self.proyecto(c)
        self.assertEqual(p.hvac_mode, HVACMode.OFF)
        c.data["sensors"][1]["Room_status"] = "03"   # one zone out of three on
        self.assertEqual(p.hvac_mode, HVACMode.COOL)

    def test_off_remembers_zones_and_turns_every_zone_off(self):
        c = control("03", "02", "03")
        p = self.proyecto(c)
        run(p.async_set_hvac_mode(HVACMode.OFF))
        self.assertEqual(p._rooms_to_restore, [1, 3])
        self.assertEqual(p.extra_state_attributes["rooms_to_restore"], [1, 3])
        c.async_update_all_sensors_status.assert_awaited_once_with("02")
        c.async_update_project_data.assert_not_called()

    def test_off_when_already_off_keeps_memory(self):
        c = control("02", "02")
        p = self.proyecto(c)
        p._rooms_to_restore = [2]
        run(p.async_turn_off())
        self.assertEqual(p._rooms_to_restore, [2])

    def test_mode_while_on_only_switches_mode(self):
        c = control("03", "02")
        run(self.proyecto(c).async_set_hvac_mode(HVACMode.HEAT))
        c.async_update_project_data.assert_awaited_once_with(7, {"mode": "4"})
        c.async_update_sensor_data.assert_not_called()
        c.async_update_all_sensors_status.assert_not_called()

    def test_mode_while_off_switches_mode_and_restores_zones(self):
        c = control("03", "02", "03")
        p = self.proyecto(c)
        run(p.async_turn_off())
        apagar_todo(c)
        run(p.async_set_hvac_mode(HVACMode.HEAT))
        c.async_update_project_data.assert_awaited_once_with(7, {"mode": "4"})
        self.assertEqual(self.zonas_encendidas(c), [(1, {"status": "03"}), (3, {"status": "03"})])

    def test_mode_while_off_with_nothing_remembered_changes_nothing(self):
        c = control("02", "02")
        with self.assertRaises(HomeAssistantError):
            run(self.proyecto(c).async_set_hvac_mode(HVACMode.HEAT))
        c.async_update_project_data.assert_not_called()
        c.async_update_sensor_data.assert_not_called()

    def test_turn_on_restores_only_remembered_zones(self):
        c = control("02", "03", "02")
        p = self.proyecto(c)
        run(p.async_turn_off())
        apagar_todo(c)
        run(p.async_turn_on())
        self.assertEqual(self.zonas_encendidas(c), [(2, {"status": "03"})])
        c.async_update_project_data.assert_not_called()

    def test_turn_on_skips_zones_that_no_longer_exist(self):
        c = control("02", "02")
        p = self.proyecto(c)
        p._rooms_to_restore = [2, 99]
        run(p.async_turn_on())
        self.assertEqual(self.zonas_encendidas(c), [(2, {"status": "03"})])

    def test_turn_on_with_nothing_remembered_raises(self):
        c = control("02", "02")
        with self.assertRaises(HomeAssistantError):
            run(self.proyecto(c).async_turn_on())
        c.async_update_sensor_data.assert_not_called()

    def test_turn_on_while_on_does_nothing(self):
        c = control("03", "02")
        p = self.proyecto(c)
        p._rooms_to_restore = [2]
        run(p.async_turn_on())
        c.async_update_sensor_data.assert_not_called()

    def test_turn_on_all_failed_raises(self):
        c = control("02")
        c.async_update_sensor_data = AsyncMock(side_effect=RuntimeError("HTTP 500"))
        p = self.proyecto(c)
        p._rooms_to_restore = [1]
        with self.assertRaises(HomeAssistantError):
            run(p.async_turn_on())

    def test_memory_restored_after_restart(self):
        c = control("02", "02")
        p = self.proyecto(c)
        p.hass = None
        last = SimpleNamespace(attributes={"rooms_to_restore": [2]})
        with patch.object(p, "async_get_last_state", AsyncMock(return_value=last)), \
             patch.object(climate_mod.ClimateEntity, "async_added_to_hass", AsyncMock()), \
             patch.object(p, "async_on_remove"):
            c.async_add_listener = MagicMock()
            run(p.async_added_to_hass())
        self.assertEqual(p._rooms_to_restore, [2])

    def test_zone_mode_preset_still_sets_every_zone(self):
        c = control("02", "02")
        run(self.proyecto(c).async_set_preset_mode("auto"))
        c.async_update_all_sensors_status.assert_awaited_once_with("03")


if __name__ == "__main__":
    unittest.main()
