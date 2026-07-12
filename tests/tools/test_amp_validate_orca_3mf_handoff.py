from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Callable

from tools.amp_orca_3mf_handoff import generate_handoff
from tools.amp_validate_orca_3mf_handoff import validate_handoff
from tests.tools.test_amp_generate_orca_3mf_handoff import (
    write_packet,
    write_template,
)


def rewrite_member(path: Path, name: str, transform: Callable[[bytes], bytes]) -> None:
    replacement = path.with_suffix(".replacement")
    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
        replacement, "w"
    ) as destination:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == name:
                data = transform(data)
            destination.writestr(info, data)
    replacement.replace(path)


class AmpOrca3mfHandoffValidatorTests(unittest.TestCase):
    def build_handoff(self, root: Path) -> tuple[Path, Path]:
        template = root / "template.3mf"
        packet = root / "packet"
        output = root / "handoff.3mf"
        write_template(template)
        write_packet(packet)
        generate_handoff(template, packet, output)
        return output, packet

    def test_accepts_generated_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, packet = self.build_handoff(Path(temp_dir))

            report = validate_handoff(output, packet)

            self.assertTrue(report["valid"])
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["nozzle_diameters"][:4], ["0.2", "0.4", "0.6", "0.8"])

    def test_rejects_corrupted_object_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, packet = self.build_handoff(Path(temp_dir))

            def corrupt(data: bytes) -> bytes:
                root = ET.fromstring(data)
                first = root.find("object")
                assert first is not None
                extruder = next(
                    item
                    for item in first.findall("metadata")
                    if item.attrib.get("key") == "extruder"
                )
                extruder.set("value", "4")
                return ET.tostring(root, encoding="utf-8", xml_declaration=True)

            rewrite_member(output, "Metadata/model_settings.config", corrupt)

            report = validate_handoff(output, packet)

            self.assertFalse(report["valid"])
            self.assertTrue(any("extruder" in error for error in report["errors"]))

    def test_rejects_corrupted_nozzle_vector(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, packet = self.build_handoff(Path(temp_dir))

            def corrupt(data: bytes) -> bytes:
                payload = json.loads(data)
                payload["nozzle_diameter"][2] = "0.4"
                return json.dumps(payload).encode()

            rewrite_member(output, "Metadata/project_settings.config", corrupt)

            report = validate_handoff(output, packet)

            self.assertFalse(report["valid"])
            self.assertTrue(any("nozzle" in error for error in report["errors"]))

    def test_rejects_missing_embedded_packet_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, packet = self.build_handoff(Path(temp_dir))
            replacement = output.with_suffix(".replacement")
            with zipfile.ZipFile(output, "r") as source, zipfile.ZipFile(
                replacement, "w"
            ) as destination:
                for info in source.infolist():
                    if info.filename == "Metadata/AMP/process_queue.json":
                        continue
                    destination.writestr(info, source.read(info.filename))
            replacement.replace(output)

            report = validate_handoff(output, packet)

            self.assertFalse(report["valid"])
            self.assertTrue(
                any("process_queue.json" in error for error in report["errors"])
            )

    def test_rejects_corrupted_manifest_template_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, packet = self.build_handoff(Path(temp_dir))

            def corrupt(data: bytes) -> bytes:
                payload = json.loads(data)
                payload["source_template_sha256"] = "0" * 64
                return json.dumps(payload).encode()

            rewrite_member(output, "Metadata/AMP/handoff_manifest.json", corrupt)

            report = validate_handoff(output, packet)

            self.assertFalse(report["valid"])
            self.assertTrue(any("template hash" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
