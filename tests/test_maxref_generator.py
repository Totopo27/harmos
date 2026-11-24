"""
Unit tests for Harmos Maxref Generator (core/compiler/maxref_generator.py).
Validates that generated .maxref.xml documents are well-formed XML and conform to Cycling '74 specifications.
"""
import os
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

from core.compiler.maxref_generator import (
    generate_maxref_xml,
    write_maxref_file,
    escape_xml,
    map_ir_attr_type_to_c74
)


class TestMaxrefGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_escape_xml(self):
        self.assertEqual(escape_xml("a < b & c > d"), "a &lt; b &amp; c &gt; d")
        self.assertEqual(escape_xml(None), "")
        self.assertEqual(escape_xml(42), "42")
        # Attributes are emitted single-quoted, so both quote kinds must be escaped.
        self.assertEqual(escape_xml("it's \"x\""), "it&apos;s &quot;x&quot;")
        ET.fromstring(f"<c74object name='{escape_xml(chr(39) + 'quoted' + chr(34))}'/>")

    def test_map_ir_attr_type_to_c74(self):
        self.assertEqual(map_ir_attr_type_to_c74("float"), "float64")
        self.assertEqual(map_ir_attr_type_to_c74("double"), "float64")
        self.assertEqual(map_ir_attr_type_to_c74("int"), "long")
        self.assertEqual(map_ir_attr_type_to_c74("integer"), "long")
        self.assertEqual(map_ir_attr_type_to_c74("symbol"), "symbol")
        self.assertEqual(map_ir_attr_type_to_c74("string"), "symbol")
        self.assertEqual(map_ir_attr_type_to_c74("list"), "list")
        self.assertEqual(map_ir_attr_type_to_c74("unknown"), "symbol")

    def test_generate_maxref_xml_well_formed(self):
        ir = {
            "object_name": "harmos.test_osc",
            "category": "dsp",
            "description": "Prueba de oscilador & síntesis <dsp>",
            "inlets": [
                {"id": 0, "type": "signal", "description": "Modulador de frecuencia"},
                {"id": 1, "type": "float", "description": "Frecuencia base en Hz"}
            ],
            "outlets": [
                {"id": 0, "type": "signal", "description": "Señal sintetizada"}
            ],
            "attributes": [
                {"name": "ratio", "type": "float", "default": 1.414, "description": "Ratio armónico"}
            ],
            "messages": [
                {"name": "reset", "description": "Reinicia la fase del oscilador"}
            ],
            "arguments": [
                {"name": "initial_freq", "type": "number", "optional": True, "description": "Frecuencia inicial"}
            ]
        }

        xml_str = generate_maxref_xml(ir, author="Harmos Team")

        # 1. Verificar que sea XML bien formado
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "c74object")
        self.assertEqual(root.attrib.get("name"), "harmos.test_osc")

        # 2. Comprobar digest y description
        digest = root.find("digest")
        self.assertIsNotNone(digest)
        self.assertIn("Prueba de oscilador", digest.text)

        # 3. Comprobar metadatos (autor y tags)
        metadata_authors = root.findall(".//metadata[@name='author']")
        self.assertEqual(len(metadata_authors), 1)
        self.assertEqual(metadata_authors[0].text, "Harmos Team")

        tags = [t.text for t in root.findall(".//metadata[@name='tag']")]
        self.assertIn("dsp", tags)

        # 4. Comprobar métodos generados
        methods = {m.attrib["name"]: m for m in root.findall(".//method")}
        self.assertIn("reset", methods)
        self.assertIn("signal", methods)
        self.assertIn("float", methods)

        # 5. Comprobar atributos generados
        attrs = {a.attrib["name"]: a for a in root.findall(".//attribute")}
        self.assertIn("ratio", attrs)
        self.assertEqual(attrs["ratio"].attrib.get("type"), "float64")
        self.assertEqual(attrs["ratio"].attrib.get("get"), "1")
        self.assertEqual(attrs["ratio"].attrib.get("set"), "1")

        # 6. Comprobar argumentos
        args = {a.attrib["name"]: a for a in root.findall(".//objarg")}
        self.assertIn("initial_freq", args)
        self.assertEqual(args["initial_freq"].attrib.get("optional"), "1")

        # 7. Comprobar seealso por defecto para DSP
        seealso = [s.attrib["name"] for s in root.findall(".//seealso")]
        self.assertIn("cycle~", seealso)

    def test_write_maxref_file_creates_file_and_directories(self):
        ir = {
            "object_name": "harmos.dummy",
            "category": "control",
            "inlets": [{"id": 0, "type": "anything", "description": "Input"}],
            "outlets": [{"id": 0, "type": "anything", "description": "Output"}]
        }

        nested_out = os.path.join(self.temp_dir, "nested", "docs", "harmos.dummy.maxref.xml")
        written_path = write_maxref_file(ir, nested_out)

        self.assertEqual(written_path, nested_out)
        self.assertTrue(os.path.isfile(nested_out))

        with open(nested_out, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<c74object name='harmos.dummy'", content)
        self.assertIn("<method name='bang'>", content)
        self.assertIn("<method name='anything'>", content)


if __name__ == "__main__":
    unittest.main()
