# Apple Home (HomeKit Bridge)

Notes for exposing this integration to Apple Home through Home Assistant's
[HomeKit Bridge](https://www.home-assistant.io/integrations/homekit/). Nothing here is specific to
how the integration talks to Koolnova; it is about how the HomeKit Bridge maps Koolnova's `climate`
entities.

Replace `<zone>` with your own room's slug — the part after `climate.koolnova_`.

## Tapping the thermostat tile shows "Fan on" and does nothing

**Symptom.** In Apple Home, tapping a Koolnova zone's tile doesn't turn the zone on or off. The
tile briefly shows "Fan on" and nothing changes.

**Why.** The HomeKit Bridge adds a linked Fan service to every `climate` entity that supports
`FAN_MODE`, and every Koolnova zone and project entity does (low / medium / high / auto). Apple
Home routes a tap on the tile to that fan's on/off switch, not to the thermostat. Koolnova fan
modes have no "off", so Home Assistant rejects the write and resets the fan to active: the tile
shows "Fan on" and the zone is untouched.

**Workaround.** Hide `FAN_MODE` from the entity with
[`customize`](https://www.home-assistant.io/docs/configuration/customizing-devices/), so the
HomeKit Bridge no longer adds the fan. `FAN_MODE` is worth 8 in `supported_features`:

1. In **Developer tools → States**, open each Koolnova `climate` entity you expose to HomeKit and
   read its `supported_features` attribute.
2. Subtract 8 and set the result in `customize.yaml`. On 3.0.1, zones report 393 (→ 385) and the
   project entity reports 409 (→ 401). The value can change between integration versions, so
   check yours instead of copying these numbers.

   ```yaml
   # configuration.yaml
   homeassistant:
     customize: !include customize.yaml
   ```

   ```yaml
   # customize.yaml
   climate.koolnova_<zone>:
     supported_features: 385
   climate.koolnova_<another_zone>:
     supported_features: 385
   climate.koolnova_<project>:
     supported_features: 401
   ```

3. Reload the core configuration (**Developer tools → YAML → Location & customizations**) or
   restart Home Assistant, then reload the HomeKit Bridge (**Settings → Devices & services →
   HomeKit Bridge → ⋮ → Reload**).

After that, a tap on the tile turns the zone on and off.

Side effects:

- `customize` changes the state attribute everywhere, so the fan-speed control also disappears
  from the entity's more-info dialog and from cards that read `supported_features`.
- `climate.set_fan_mode` still works from scripts and automations; only the advertised feature
  changes.
- If a later version of the integration changes the supported features, redo step 1.

The same workaround is discussed in the community thread
[Remove fan mode from HomeKit climate](https://community.home-assistant.io/t/remove-fan-mode-from-homekit-climate/439848).

## Keeping fan speed in Apple Home

With `FAN_MODE` hidden, Apple Home has no fan speed control. To get one back without breaking the
tile tap, expose a separate [template fan](https://www.home-assistant.io/integrations/template/)
that calls `climate.set_fan_mode`. It shows up as its own accessory, so the thermostat tile keeps
toggling the room.

```yaml
# configuration.yaml
template:
  - fan:
      - name: Koolnova fan
        unique_id: koolnova_fan_speed
        state: "on"
        speed_count: 3
        percentage: >
          {% set mode = state_attr('climate.koolnova_<zone>', 'fan_mode') %}
          {{ {'low': 33, 'medium': 66, 'high': 100}.get(mode, 0) }}
        preset_modes:
          - auto
        preset_mode: >
          {{ 'auto' if state_attr('climate.koolnova_<zone>', 'fan_mode') == 'auto' else none }}
        set_percentage:
          - condition: template
            value_template: "{{ percentage > 0 }}"
          - action: climate.set_fan_mode
            target:
              entity_id: climate.koolnova_<zone>
            data:
              fan_mode: >
                {{ 'low' if percentage <= 33 else 'medium' if percentage <= 66 else 'high' }}
        set_preset_mode:
          - action: climate.set_fan_mode
            target:
              entity_id: climate.koolnova_<zone>
            data:
              fan_mode: "{{ preset_mode }}"
        # Koolnova fans have no off: on/off does nothing and the fan stays "on".
        turn_on: []
        turn_off: []
```

Add the new `fan` entity to the HomeKit Bridge's included entities. To set the speed on every
zone at once, point the two `entity_id` targets at the project entity (`climate.koolnova_<project>`)
and keep reading `fan_mode` from a zone: the project entity's `fan_mode` only reflects the last
value set through it.

On at least one installation, setting the fan speed on one zone applies it to every zone (see also
"Shared fan hardware" in [DASHBOARDS.md](DASHBOARDS.md#other-patterns)). If yours behaves the same,
a single fan entity is enough. This depends on how the system is installed, so check yours before
relying on it.

## Zone modes

By default zones offer Off and Auto, which Home Assistant labels **On/Off** (see the
[README](../README.md#features)). The HomeKit Bridge maps the underlying modes, so Apple Home shows
them as **Off** and **Auto**. Auto here only means "on": a Koolnova zone has a single setpoint and
the integration does not support a heating/cooling temperature range. Heat or cool is chosen on
the project entity.
