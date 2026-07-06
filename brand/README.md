# Brand assets

Koolnova integration logo/icon. A six-arm snowflake ("nova") with a cool→warm
diagonal gradient (cyan→blue→orange→red) symbolising climate control (cooling + heating).

- `icon.png` (256×256), `icon@2x.png` (512×512) — square mark, transparent background.
- `logo.png` / `logo@2x.png` — landscape mark + `koolnova` wordmark (dark slate, for light backgrounds).
- `dark_logo.png` / `dark_logo@2x.png` — white wordmark, for dark backgrounds.

These are published to [home-assistant/brands](https://github.com/home-assistant/brands)
under `custom_integrations/koolnova/`, which is where Home Assistant loads
integration icons from (the integration repo itself is not used for this).

Regenerate with `python generate.py` (needs Pillow).
