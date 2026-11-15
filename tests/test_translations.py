"""Tests for the translation files and the attribute keys they describe.

Attribute keys are technical identifiers; the display text belongs in the translation
files. Until v1.4.0 the connectivity attributes were literally named "Señal WiFi" and
"Última actualización", which hard-coded Spanish into every dashboard that read them.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTEGRATION = ROOT / "custom_components" / "koolnova"
TRANSLATIONS = sorted((INTEGRATION / "translations").glob("*.json"))
STRINGS = INTEGRATION / "strings.json"

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")

# Attributes the connectivity entity exposes, in the order sensor.py builds them.
CONNECTIVITY_ATTRIBUTES = {"wifi_signal", "online", "last_update", "rooms_last_update"}


def _load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _attribute_keys(document):
    """Yield (file-relative path, key) for every declared state attribute."""
    for domain, entities in document.get("entity", {}).items():
        for entity, block in entities.items():
            for key in block.get("state_attributes", {}):
                yield f"entity.{domain}.{entity}", key


class TranslationFilesTest(unittest.TestCase):
    def test_translation_files_are_present(self):
        names = {path.name for path in TRANSLATIONS}
        self.assertIn("en.json", names)
        self.assertIn("es.json", names)

    def test_every_translation_is_valid_json(self):
        for path in [STRINGS, *TRANSLATIONS]:
            with self.subTest(file=path.name):
                _load(path)

    def test_translations_share_the_structure_of_strings_json(self):
        """A key present in strings.json must exist in every translation."""
        def keys(node, prefix=""):
            found = set()
            for key, value in node.items():
                path = f"{prefix}.{key}" if prefix else key
                found.add(path)
                if isinstance(value, dict):
                    found |= keys(value, path)
            return found

        expected = keys(_load(STRINGS))
        for path in TRANSLATIONS:
            with self.subTest(file=path.name):
                self.assertEqual(expected - keys(_load(path)), set())

    def test_zone_state_translations_live_under_entity_climate(self):
        """Zone modes are relabelled via `entity.climate.koolnova_zone.state`.

        The frontend resolves entity-state overrides as
        `component.<platform>.entity.<domain>.<translation_key>.state.<state>`
        (the `entity` category). Under `entity_component` they are silently
        ignored and the thermostat card keeps showing "Auto".
        """
        for path in [STRINGS, *TRANSLATIONS]:
            with self.subTest(file=path.name):
                states = _load(path)["entity"]["climate"]["koolnova_zone"]["state"]
                self.assertEqual(set(states), {"auto", "off"})


class AttributeKeyTest(unittest.TestCase):
    def test_declared_attribute_keys_are_snake_case(self):
        """No spaces, no accents, no capitals: those are display strings, not keys."""
        for path in [STRINGS, *TRANSLATIONS]:
            for where, key in _attribute_keys(_load(path)):
                with self.subTest(file=path.name, attribute=f"{where}.{key}"):
                    self.assertRegex(key, SNAKE_CASE)

    def test_connectivity_attributes_are_declared_in_every_file(self):
        for path in [STRINGS, *TRANSLATIONS]:
            document = _load(path)
            declared = set(
                document["entity"]["sensor"]["connectivity_status"]["state_attributes"]
            )
            with self.subTest(file=path.name):
                self.assertEqual(declared, CONNECTIVITY_ATTRIBUTES)

    def test_the_entity_is_declared_only_under_the_sensor_domain(self):
        """It is a SensorEntity added by the sensor platform; before v3 it was registered under climate."""
        for path in [STRINGS, *TRANSLATIONS]:
            entity = _load(path)["entity"]
            with self.subTest(file=path.name):
                self.assertIn("connectivity_status", entity["sensor"])
                self.assertNotIn("connectivity_status", entity["climate"])

    def test_the_class_lives_in_the_sensor_platform(self):
        sensor = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        climate = (INTEGRATION / "climate.py").read_text(encoding="utf-8")
        self.assertIn("class KoolnovaConnectivitySensor(SensorEntity)", sensor)
        self.assertNotIn("KoolnovaConnectivitySensor", climate)


class ConnectivitySourceTest(unittest.TestCase):
    """Guard the attribute keys at their source, since sensor.py needs HA to import."""

    def test_sensor_py_emits_only_snake_case_attribute_keys(self):
        source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        block = source.split("def extra_state_attributes", 1)[-1]

        for key in CONNECTIVITY_ATTRIBUTES:
            with self.subTest(attribute=key):
                self.assertIn(f'"{key}"', block)

    def test_no_accented_attribute_keys_remain(self):
        source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        for literal in ('"Señal WiFi"', '"Última actualización"'):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, source)


if __name__ == "__main__":
    unittest.main()
