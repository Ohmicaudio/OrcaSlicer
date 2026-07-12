from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from tools.amp_orca_3mf_handoff import generate_handoff


REGIONS = [
    ("micro_detail_zone", "0.2"),
    ("normal_visible_detail_zone", "0.4"),
    ("structural_shell_zone", "0.6"),
    ("bulk_zone", "0.8"),
]


def write_packet(path: Path) -> None:
    path.mkdir(parents=True)
    process_queue = {
        "process_queue": [
            {
                "region_name": name,
                "recommended_tool_class": nozzle,
                "recommended_nozzle_diameter": nozzle,
            }
            for name, nozzle in REGIONS
        ]
    }
    (path / "process_queue.json").write_text(
        json.dumps(process_queue), encoding="utf-8"
    )
    (path / "plan.json").write_text(
        json.dumps({"schema_version": "0.1", "status": "advisory"}),
        encoding="utf-8",
    )
    (path / "tool_assignments.json").write_text(
        json.dumps(
            {
                "assignments": [
                    {"region_name": name, "tool_class": nozzle}
                    for name, nozzle in REGIONS
                ]
            }
        ),
        encoding="utf-8",
    )
    (path / "preflight_status.json").write_text(
        json.dumps({"status": "not_ready", "ready": False}), encoding="utf-8"
    )


def model_settings_xml(regions: list[tuple[str, str]] = REGIONS) -> bytes:
    root = ET.Element("config")
    for index, (name, _) in enumerate(regions, start=1):
        obj = ET.SubElement(root, "object", {"id": str(index * 2)})
        ET.SubElement(obj, "metadata", {"key": "name", "value": f"{name}.stl"})
        ET.SubElement(obj, "metadata", {"key": "extruder", "value": "1"})
        ET.SubElement(obj, "part", {"id": str(index * 2 - 1), "subtype": "normal_part"})
    ET.SubElement(root, "plate")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_template(path: Path) -> None:
    project_settings = {"nozzle_diameter": ["0.4"] * 5, "untouched": "value"}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", b"<Types/>")
        archive.writestr("3D/3dmodel.model", b"<model/>")
        archive.writestr("3D/Objects/body.model", b"unchanged mesh")
        archive.writestr("Metadata/model_settings.config", model_settings_xml())
        archive.writestr(
            "Metadata/project_settings.config", json.dumps(project_settings).encode()
        )


def read_member(path: Path, name: str) -> bytes:
    with zipfile.ZipFile(path) as archive:
        return archive.read(name)


def read_object_extruders(path: Path) -> dict[str, str]:
    root = ET.fromstring(read_member(path, "Metadata/model_settings.config"))
    result: dict[str, str] = {}
    for obj in root.findall("object"):
        metadata = {
            item.attrib["key"]: item.attrib["value"]
            for item in obj.findall("metadata")
        }
        result[metadata["name"].removesuffix(".stl")] = metadata["extruder"]
    return result


def read_project_nozzles(path: Path) -> list[str]:
    return json.loads(
        read_member(path, "Metadata/project_settings.config").decode("utf-8")
    )["nozzle_diameter"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AmpOrca3mfHandoffTests(unittest.TestCase):
    def test_maps_regions_and_preserves_mesh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "template.3mf"
            packet = root / "packet"
            output = root / "handoff.3mf"
            write_template(template)
            write_packet(packet)

            result = generate_handoff(template, packet, output)

            self.assertEqual(result["region_count"], 4)
            self.assertEqual(
                result["nozzle_diameters"], ["0.2", "0.4", "0.6", "0.8"]
            )
            self.assertEqual(
                read_object_extruders(output),
                {
                    "micro_detail_zone": "1",
                    "normal_visible_detail_zone": "2",
                    "structural_shell_zone": "3",
                    "bulk_zone": "4",
                },
            )
            self.assertEqual(
                read_project_nozzles(output)[:4], ["0.2", "0.4", "0.6", "0.8"]
            )
            self.assertEqual(
                read_member(output, "3D/Objects/body.model"), b"unchanged mesh"
            )

    def test_embeds_packet_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "template.3mf"
            packet = root / "packet"
            output = root / "handoff.3mf"
            write_template(template)
            write_packet(packet)

            generate_handoff(template, packet, output)

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertTrue(
                    {
                        "Metadata/AMP/plan.json",
                        "Metadata/AMP/process_queue.json",
                        "Metadata/AMP/tool_assignments.json",
                        "Metadata/AMP/preflight_status.json",
                        "Metadata/AMP/handoff_manifest.json",
                    }.issubset(names)
                )
                manifest = json.loads(
                    archive.read("Metadata/AMP/handoff_manifest.json")
                )
            self.assertEqual(manifest["schema_version"], "0.1")
            self.assertEqual(manifest["source_template_sha256"], sha256(template))
            self.assertEqual(
                manifest["nozzle_diameters"], ["0.2", "0.4", "0.6", "0.8"]
            )
            self.assertEqual(manifest["hardware_preflight_status"], "not_ready")
            self.assertEqual(
                [item["region_name"] for item in manifest["region_assignments"]],
                sorted(name for name, _ in REGIONS),
            )

    def test_output_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "template.3mf"
            packet = root / "packet"
            first = root / "first.3mf"
            second = root / "second.3mf"
            write_template(template)
            write_packet(packet)

            generate_handoff(template, packet, first)
            generate_handoff(template, packet, second)

            self.assertEqual(sha256(first), sha256(second))


if __name__ == "__main__":
    unittest.main()
