from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from tools.amp_observe_3mf import ObservationError, observe_3mf


MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
ROOT_MODEL = "3D/3dmodel.model"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_model_xml(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
) -> bytes:
    namespace = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}model", {"unit": "millimeter"})
    resources = ET.SubElement(root, f"{{{namespace}}}resources")
    obj = ET.SubElement(resources, f"{{{namespace}}}object", {"id": "1", "type": "model"})
    mesh = ET.SubElement(obj, f"{{{namespace}}}mesh")
    vertices_node = ET.SubElement(mesh, f"{{{namespace}}}vertices")
    for x, y, z in vertices:
        ET.SubElement(
            vertices_node,
            f"{{{namespace}}}vertex",
            {"x": str(x), "y": str(y), "z": str(z)},
        )
    triangles_node = ET.SubElement(mesh, f"{{{namespace}}}triangles")
    for v1, v2, v3 in triangles:
        ET.SubElement(
            triangles_node,
            f"{{{namespace}}}triangle",
            {"v1": str(v1), "v2": str(v2), "v3": str(v3)},
        )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_synthetic_3mf(path: Path) -> None:
    root_model = b'''<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="millimeter">
  <metadata name="Title">Synthetic Project</metadata>
  <metadata name="Designer">AMP Tests</metadata>
  <metadata name="License">Test Fixture</metadata>
  <metadata name="Application">AMP Synthetic</metadata>
  <resources><object id="2" type="model"><components><component objectid="1" path="/3D/Objects/detail.model"/></components></object></resources>
  <build><item objectid="2"/></build>
</model>'''
    model_settings = b'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="Glass Detail.stl"/>
    <metadata key="extruder" value="2"/>
    <part id="1" subtype="normal_part"/>
  </object>
  <plate><metadata key="index" value="1"/><metadata key="name" value="Detail Plate"/><model_instance><metadata key="object_id" value="2"/></model_instance></plate>
</config>'''
    project_settings = {
        "nozzle_diameter": ["0.4", "0.4"],
        "filament_settings_id": ["Basic PLA", "Transparent PLA"],
        "filament_colour": ["#111111", "#EEEEFF"],
        "printer_settings_id": "Synthetic Printer",
        "print_settings_id": "0.20mm Synthetic",
        "layer_height": "0.2",
        "wall_generator": "classic",
    }
    detail = object_model_xml(
        [(0, 0, 0), (10, 0, 0), (0, 5, 2)],
        [(0, 1, 2)],
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", b"<Types/>")
        archive.writestr(ROOT_MODEL, root_model)
        archive.writestr(MODEL_SETTINGS, model_settings)
        archive.writestr(PROJECT_SETTINGS, json.dumps(project_settings))
        archive.writestr("3D/Objects/detail.model", detail)


class AmpObserve3mfContractTests(unittest.TestCase):
    def test_observes_source_contract_without_modifying_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            before = sha256(source)

            report = observe_3mf(source)

            self.assertEqual(report["schema_version"], "0.1")
            self.assertEqual(report["source"]["sha256"], before)
            self.assertEqual(report["source"]["member_count"], 5)
            self.assertEqual(sha256(source), before)

    def test_task_2_contract_observes_metadata_without_assigning_a_nozzle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)

            report = observe_3mf(source)

            self.assertEqual(
                report["physical_tools"]["nozzle_diameters"], ["0.4", "0.4"]
            )
            self.assertEqual(report["objects"][0]["material_assignment"], 2)
            self.assertIsNone(report["objects"][0]["physical_nozzle_assignment"])
            self.assertIsNone(report["objects"][0]["recommended_tool_class"])

    def test_rejects_missing_required_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "broken.3mf"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(ROOT_MODEL, b"<model/>")
            with self.assertRaisesRegex(ObservationError, "missing required member"):
                observe_3mf(source)

    def test_rejects_duplicate_required_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "duplicate.3mf"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(source, "w") as archive:
                    archive.writestr(ROOT_MODEL, b"<model/>")
                    archive.writestr(ROOT_MODEL, b"<model/>")
                    archive.writestr(MODEL_SETTINGS, b"<config/>")
                    archive.writestr(PROJECT_SETTINGS, b"{}")
            with self.assertRaisesRegex(ObservationError, "duplicate required member"):
                observe_3mf(source)
