# Dashboards

Example Lovelace layouts for this integration. None of this is required — build your own straight
from the entities in the [README](../README.md#entities). These are two starting points: one using
only core Home Assistant cards, one using [Mushroom](https://github.com/piitaya/lovelace-mushroom)
for a more compact look, plus a few extra patterns for less common setups.

Replace `<zone>` with your own room's slug — the part after `climate.koolnova_`, derived from that
room's `Room_Name` in the Koolnova app.

## Plain Home Assistant cards

No extra dependency: a `thermostat` card per zone (native temperature dial + HVAC mode buttons)
with its power switch as a `tile` underneath, in a 2-column grid; a `thermostat` card for the
global control; a `markdown` card reading the connectivity sensor's attributes (its `entity_id` follows your HA
language, so use yours).

```yaml
views:
  - title: Clima
    path: clima
    icon: mdi:air-conditioner
    cards:
      - type: thermostat
        entity: climate.koolnova_control_global
        name: Control Global

      - type: grid
        columns: 2
        square: false
        cards:
          - type: vertical-stack
            cards:
              - type: thermostat
                entity: climate.koolnova_<zone>
              - type: tile
                entity: switch.koolnova_<zone>_power
                name: Power
          # … repeat the vertical-stack above for each zone

      - type: markdown
        content: |
          ## 📶 Connectivity
          {% set sensor = 'sensor.koolnova_<project>_estado_de_conectividad' %}
          **Online:** {{ state_attr(sensor, 'online') }}

          **WiFi signal:** {{ state_attr(sensor, 'wifi_signal') }} dBm

          {% set lu = state_attr(sensor, 'last_update') %}
          **Last update:** {{ (lu | as_datetime | as_local).strftime('%H:%M:%S') if lu else '—' }}
```

## Mushroom cards

Needs [Mushroom](https://github.com/piitaya/lovelace-mushroom) from HACS. More compact: a
`mushroom-climate-card` per zone in a 2-column grid, `fill_container: true` so every card matches
the width of the global control card above it.

```yaml
views:
  - title: Clima
    path: clima
    icon: mdi:air-conditioner
    cards:
      - type: custom:mushroom-climate-card
        entity: climate.koolnova_control_global
        name: Control Global
        layout: vertical
        fill_container: true
        show_temperature_control: true
        hvac_modes: [cool, heat]

      - type: grid
        columns: 2
        square: false
        cards:
          - type: custom:mushroom-climate-card
            entity: climate.koolnova_<zone>
            name: <Zone>
            show_temperature_control: true
            fill_container: true
          # … repeat for each zone
```

`mushroom-climate-card` has no fan-speed control — checked against the current bundle, it doesn't
register a `climate-fan-modes` feature the way it does `climate-hvac-modes`. Use the core `tile`
card for fan speed instead (below).

## Other patterns

Not full dashboards, just things worth knowing when the default one-card-per-zone layout doesn't
match your install.

**Shared fan hardware.** Ducted systems often have one blower per floor or zone group feeding
several rooms, even though each room still gets its own Koolnova sensor and `climate` entity. Each
room's `fan_mode` is then cosmetically independent in Home Assistant but mechanically the same
physical fan — changing one room's speed changes it for the whole group, so eight identical fan
controls (one per room) is misleading rather than useful. A single control per group, using any one
zone entity from that group, avoids that. The core `tile` card's `climate-fan-modes` feature (note:
plural, unlike `climate-hvac-modes`) does this in one compact row:

```yaml
type: tile
entity: climate.koolnova_<one_zone_from_the_group>
name: Ground floor fan
hide_state: true
features_position: inline
features:
  - type: climate-fan-modes
    style: icons
```

`hide_state: true` drops the state text and `features_position: inline` puts the icon row next to
the title instead of below it, so the whole card stays one line tall.

**Conditional visibility.** Wrap any card in a `conditional` card to show or hide it based on
another entity's state — e.g. only show a fan control while the project is set to `cool`.

Condition on the `compressor_mode` attribute, **not** `state`: the project entity's `state` folds
in on/off (see [README](../README.md#entities) — it reports `off` when every zone is off,
regardless of whether the last selected mode was cool or heat), so a plain `state: cool` condition
also hides the card whenever the project happens to be off in cool mode. `compressor_mode` is the
raw cool/heat selection, unaffected by on/off:

```yaml
type: conditional
conditions:
  - entity: climate.koolnova_control_global
    attribute: compressor_mode
    state: cool
card:
  type: tile
  entity: climate.koolnova_<zone>
  # ...
```
