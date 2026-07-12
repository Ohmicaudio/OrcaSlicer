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


def synthetic_model_settings() -> bytes:
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="Glass Detail.stl"/>
    <metadata key="extruder" value=" 2 "/>
    <part id="1" subtype="normal_part"/>
  </object>
  <plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="Detail Plate"/><model_instance><metadata key="object_id" value="2"/></model_instance></plate>
</config>'''


def synthetic_project_settings() -> dict[str, object]:
    return {
        "nozzle_diameter": ["0.4", "0.4"],
        "filament_settings_id": ["Basic PLA", "Transparent PLA"],
        "filament_colour": ["#111111", "#EEEEFF"],
        "printer_settings_id": "Synthetic Printer",
        "print_settings_id": "0.20mm Synthetic",
        "layer_height": "0.2",
        "wall_generator": "classic",
    }


def write_synthetic_3mf(
    path: Path,
    *,
    model_settings: bytes | None = None,
    project_settings: dict[str, object] | None = None,
) -> None:
    root_model = b'''<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="millimeter">
  <metadata name="Title">Synthetic Project</metadata>
  <metadata name="Designer">AMP Tests</metadata>
  <metadata name="License">Test Fixture</metadata>
  <metadata name="Application">AMP Synthetic</metadata>
  <resources><object id="2" type="model"><components><component objectid="1" path="/3D/Objects/detail.model"/></components></object></resources>
  <build><item objectid="2"/></build>
</model>'''
    if model_settings is None:
        model_settings = synthetic_model_settings()
    if project_settings is None:
        project_settings = synthetic_project_settings()
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
            self.assertEqual(report["project"]["printer_preset"], "Synthetic Printer")
            self.assertEqual(report["project"]["process_preset"], "0.20mm Synthetic")
            self.assertEqual(report["project"]["layer_height"], "0.2")
            self.assertEqual(report["project"]["title"], "Synthetic Project")
            self.assertEqual(report["project"]["designer"], "AMP Tests")
            self.assertEqual(report["project"]["license"], "Test Fixture")
            self.assertEqual(report["project"]["source_application"], "AMP Synthetic")
            self.assertEqual(report["materials"][1]["slot"], 2)
            self.assertEqual(report["materials"][1]["profile"], "Transparent PLA")
            self.assertEqual(report["materials"][1]["color"], "#EEEEFF")
            self.assertEqual(report["plates"][0]["plate_id"], 1)
            self.assertEqual(report["plates"][0]["object_ids"], [2])
            self.assertEqual(report["objects"][0]["object_id"], 2)
            self.assertEqual(report["objects"][0]["name"], "Glass Detail.stl")
            self.assertEqual(report["objects"][0]["plate_id"], 1)
            self.assertEqual(report["objects"][0]["plate_name"], "Detail Plate")
            self.assertEqual(report["objects"][0]["material_assignment"], 2)
            self.assertEqual(report["objects"][0]["resolved_material"]["slot"], 2)
            self.assertIsNone(report["objects"][0]["physical_nozzle_assignment"])
            self.assertIsNone(report["objects"][0]["recommended_tool_class"])
            self.assertEqual(
                report["objects"][0]["semantic_name_tokens"], ["detail", "glass"]
            )
            self.assertEqual(report["warnings"], [])

    def test_rejects_duplicate_object_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "duplicate-object.3mf"
            model_settings = synthetic_model_settings().replace(
                b"</config>",
                b'<object id="2"><metadata key="name" value="Duplicate"/></object></config>',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(ObservationError, "duplicate object id: 2"):
                observe_3mf(source)

    def test_accepts_legacy_plate_metadata_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "legacy-plate-keys.3mf"
            model_settings = synthetic_model_settings().replace(
                b'key="plater_id"', b'key="index"'
            ).replace(b'key="plater_name"', b'key="name"')
            write_synthetic_3mf(source, model_settings=model_settings)

            report = observe_3mf(source)

            self.assertEqual(report["plates"][0]["plate_id"], 1)
            self.assertEqual(report["plates"][0]["name"], "Detail Plate")
            self.assertEqual(report["objects"][0]["plate_name"], "Detail Plate")

    def test_rejects_missing_and_malformed_metadata_ids(self) -> None:
        base = synthetic_model_settings()
        cases = [
            (
                "missing object id",
                base.replace(b'<object id="2">', b"<object>"),
                r"missing object id",
            ),
            (
                "malformed object id",
                base.replace(b'<object id="2">', b'<object id="two">'),
                r"invalid object id: 'two'",
            ),
            (
                "missing plate id",
                base.replace(b'<metadata key="plater_id" value="1"/>', b""),
                r"missing plate id",
            ),
            (
                "malformed plate id",
                base.replace(
                    b'<metadata key="plater_id" value="1"/>',
                    b'<metadata key="plater_id" value="one"/>',
                ),
                r"invalid plate id: 'one'",
            ),
            (
                "missing instance object id",
                base.replace(
                    b'<metadata key="object_id" value="2"/>',
                    b'<metadata key="object_id"/>',
                ),
                r"missing plate 1 object id",
            ),
            (
                "malformed instance object id",
                base.replace(
                    b'<metadata key="object_id" value="2"/>',
                    b'<metadata key="object_id" value="two"/>',
                ),
                r"invalid plate 1 object id: 'two'",
            ),
        ]
        for label, model_settings, message in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / "invalid-id.3mf"
                write_synthetic_3mf(source, model_settings=model_settings)

                with self.assertRaisesRegex(ObservationError, message):
                    observe_3mf(source)

    def test_rejects_duplicate_plate_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "duplicate-plate.3mf"
            second_plate = b'''<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="Duplicate"/></plate>'''
            model_settings = synthetic_model_settings().replace(
                b"</config>", second_plate + b"</config>"
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(ObservationError, "duplicate plate id: 1"):
                observe_3mf(source)

    def test_rejects_dangling_plate_object_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "dangling-object.3mf"
            model_settings = synthetic_model_settings().replace(
                b'key="object_id" value="2"', b'key="object_id" value="99"'
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(
                ObservationError, "plate 1 references unknown object id: 99"
            ):
                observe_3mf(source)

    def test_rejects_ambiguous_plate_membership(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "ambiguous-membership.3mf"
            second_plate = b'''<plate><metadata key="plater_id" value="2"/><metadata key="plater_name" value="Other"/><model_instance><metadata key="object_id" value="2"/></model_instance></plate>'''
            model_settings = synthetic_model_settings().replace(
                b"</config>", second_plate + b"</config>"
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(
                ObservationError, "ambiguous plate membership for object id 2: 1, 2"
            ):
                observe_3mf(source)

    def test_rejects_malformed_explicit_extruder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invalid-extruder.3mf"
            model_settings = synthetic_model_settings().replace(
                b'key="extruder" value=" 2 "', b'key="extruder" value="two"'
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(
                ObservationError, "invalid object 2 extruder: 'two'"
            ):
                observe_3mf(source)

    def test_warns_for_non_list_project_vectors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invalid-vectors.3mf"
            project_settings = synthetic_project_settings()
            project_settings.update(
                {
                    "nozzle_diameter": "0.4",
                    "filament_settings_id": "Basic PLA",
                    "filament_colour": "#111111",
                }
            )
            write_synthetic_3mf(source, project_settings=project_settings)

            report = observe_3mf(source)

            self.assertEqual(report["materials"], [])
            self.assertEqual(report["physical_tools"]["nozzle_diameters"], [])
            self.assertEqual(
                report["warnings"],
                [
                    "project filament_colour is not a list",
                    "project filament_settings_id is not a list",
                    "project nozzle_diameter is not a list",
                ],
            )

    def test_warns_for_material_vector_length_mismatch_without_inventing_values(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "mismatched-materials.3mf"
            project_settings = synthetic_project_settings()
            project_settings["filament_settings_id"] = ["Basic PLA"]
            write_synthetic_3mf(source, project_settings=project_settings)

            report = observe_3mf(source)

            self.assertEqual(
                report["materials"],
                [
                    {"slot": 1, "profile": "Basic PLA", "color": "#111111"},
                    {"slot": 2, "profile": None, "color": "#EEEEFF"},
                ],
            )
            self.assertEqual(
                report["warnings"],
                ["project material profile/color length mismatch: 1 profiles, 2 colors"],
            )

    def test_returns_metadata_in_deterministic_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "unsorted.3mf"
            model_settings = b'''<config>
  <object id="10"><metadata key="name" value="Ten.stl"/><metadata key="extruder" value="2"/></object>
  <object id="2"><metadata key="name" value="Two.stl"/></object>
  <object id="5"><metadata key="name" value="Five.stl"/><metadata key="extruder" value="1"/></object>
  <plate><metadata key="plater_id" value="3"/><metadata key="plater_name" value="Later"/><model_instance><metadata key="object_id" value="10"/></model_instance><model_instance><metadata key="object_id" value="5"/></model_instance></plate>
  <plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="First"/><model_instance><metadata key="object_id" value="2"/></model_instance></plate>
</config>'''
            write_synthetic_3mf(source, model_settings=model_settings)

            report = observe_3mf(source)

            self.assertEqual(
                [item["object_id"] for item in report["objects"]], [2, 5, 10]
            )
            self.assertEqual(
                [item["material_assignment"] for item in report["objects"]],
                [None, 1, 2],
            )
            self.assertEqual(
                [item["plate_id"] for item in report["objects"]], [1, 3, 3]
            )
            self.assertEqual(
                [item["plate_id"] for item in report["plates"]], [1, 3]
            )
            self.assertEqual(report["plates"][1]["object_ids"], [5, 10])

    def test_warns_for_unresolved_material_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "unresolved-material.3mf"
            model_settings = synthetic_model_settings().replace(
                b'key="extruder" value=" 2 "', b'key="extruder" value="3"'
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            report = observe_3mf(source)

            self.assertIsNone(report["objects"][0]["resolved_material"])
            self.assertEqual(
                report["objects"][0]["warnings"],
                ["material assignment 3 does not resolve to a configured slot"],
            )

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
