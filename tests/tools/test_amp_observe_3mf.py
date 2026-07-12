from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest import mock

from tools.amp_observe_3mf import (
    ObservationError,
    main,
    observe_3mf,
    serialize_json,
    serialize_markdown,
    validate_report,
    write_reports,
)


MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
ROOT_MODEL = "3D/3dmodel.model"
CORE_NAMESPACE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PRODUCTION_NAMESPACE = (
    "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
)
EXTENSION_NAMESPACE = "urn:amp:observer-test-extension"

Coordinate = float | int | str
Vertex = tuple[Coordinate, Coordinate, Coordinate]
Triangle = tuple[int, int, int]
Mesh = tuple[list[Vertex], list[Triangle]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_model_xml(
    vertices: list[Vertex],
    triangles: list[Triangle],
) -> bytes:
    return object_model_objects_xml([(1, [(vertices, triangles)])])


def object_model_objects_xml(
    objects: list[tuple[int, list[Mesh]]], *, extension_noise: bool = False
) -> bytes:
    ET.register_namespace("", CORE_NAMESPACE)
    ET.register_namespace("e", EXTENSION_NAMESPACE)
    root = ET.Element(f"{{{CORE_NAMESPACE}}}model", {"unit": "millimeter"})
    resources = ET.SubElement(root, f"{{{CORE_NAMESPACE}}}resources")
    for object_id, meshes in objects:
        obj = ET.SubElement(
            resources,
            f"{{{CORE_NAMESPACE}}}object",
            {"id": str(object_id), "type": "model"},
        )
        for vertices, triangles in meshes:
            mesh = ET.SubElement(obj, f"{{{CORE_NAMESPACE}}}mesh")
            vertices_node = ET.SubElement(mesh, f"{{{CORE_NAMESPACE}}}vertices")
            for x, y, z in vertices:
                ET.SubElement(
                    vertices_node,
                    f"{{{CORE_NAMESPACE}}}vertex",
                    {"x": str(x), "y": str(y), "z": str(z)},
                )
            triangles_node = ET.SubElement(mesh, f"{{{CORE_NAMESPACE}}}triangles")
            for v1, v2, v3 in triangles:
                ET.SubElement(
                    triangles_node,
                    f"{{{CORE_NAMESPACE}}}triangle",
                    {"v1": str(v1), "v2": str(v2), "v3": str(v3)},
                )
        if extension_noise:
            ET.SubElement(
                obj,
                f"{{{EXTENSION_NAMESPACE}}}vertex",
                {"x": "-100", "y": "-100", "z": "-100"},
            )
            ET.SubElement(obj, f"{{{EXTENSION_NAMESPACE}}}triangle")
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


def synthetic_root_model(
    *,
    object_id: str = "2",
    component_path: str = "/3D/Objects/detail.model",
    referenced_object_id: str = "1",
    transform: str | None = None,
    qualified_path: bool = True,
    unqualified_component_path: str | None = None,
    component_references: list[tuple[str, str, str | None]] | None = None,
) -> bytes:
    ET.register_namespace("", CORE_NAMESPACE)
    ET.register_namespace("p", PRODUCTION_NAMESPACE)
    root = ET.Element(f"{{{CORE_NAMESPACE}}}model", {"unit": "millimeter"})
    for name, value in (
        ("Title", "Synthetic Project"),
        ("Designer", "AMP Tests"),
        ("License", "Test Fixture"),
        ("Application", "AMP Synthetic"),
    ):
        node = ET.SubElement(root, f"{{{CORE_NAMESPACE}}}metadata", {"name": name})
        node.text = value
    resources = ET.SubElement(root, f"{{{CORE_NAMESPACE}}}resources")
    outer_object = ET.SubElement(
        resources,
        f"{{{CORE_NAMESPACE}}}object",
        {"id": object_id, "type": "model"},
    )
    components = ET.SubElement(outer_object, f"{{{CORE_NAMESPACE}}}components")
    references = component_references or [
        (component_path, referenced_object_id, transform)
    ]
    for index, (path, target_object_id, component_transform) in enumerate(references):
        attributes = {"objectid": target_object_id}
        if qualified_path:
            attributes[f"{{{PRODUCTION_NAMESPACE}}}path"] = path
        else:
            attributes["path"] = path
        if index == 0 and unqualified_component_path is not None:
            attributes["path"] = unqualified_component_path
        if component_transform is not None:
            attributes["transform"] = component_transform
        ET.SubElement(components, f"{{{CORE_NAMESPACE}}}component", attributes)
    build = ET.SubElement(root, f"{{{CORE_NAMESPACE}}}build")
    ET.SubElement(build, f"{{{CORE_NAMESPACE}}}item", {"objectid": object_id})
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_synthetic_3mf(
    path: Path,
    *,
    model_settings: bytes | None = None,
    project_settings: dict[str, object] | None = None,
    root_model: bytes | None = None,
    object_model_data: bytes | None = None,
    object_model_members: list[tuple[str, bytes]] | None = None,
    optional_members: list[tuple[str, bytes]] | None = None,
) -> None:
    if model_settings is None:
        model_settings = synthetic_model_settings()
    if project_settings is None:
        project_settings = synthetic_project_settings()
    if root_model is None:
        root_model = synthetic_root_model()
    if object_model_data is None:
        object_model_data = object_model_xml(
            [(0, 0, 0), (10, 0, 0), (0, 5, 2)],
            [(0, 1, 2)],
        )
    if object_model_members is None:
        object_model_members = [("3D/Objects/detail.model", object_model_data)]
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", b"<Types/>")
        archive.writestr(ROOT_MODEL, root_model)
        archive.writestr(MODEL_SETTINGS, model_settings)
        archive.writestr(PROJECT_SETTINGS, json.dumps(project_settings))
        for member_name, payload in object_model_members:
            archive.writestr(member_name, payload)
        for member_name, payload in optional_members or []:
            archive.writestr(member_name, payload)


class AmpObserve3mfContractTests(unittest.TestCase):
    def test_serialization_is_deterministic_and_contains_no_absolute_path(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            report = observe_3mf(source)

            first = serialize_json(report)
            second = serialize_json(report)

            self.assertEqual(first, second)
            self.assertTrue(first.endswith("\n"))
            self.assertNotIn(str(source.parent), first)
            self.assertIn('"physical_nozzle_assignment": null', first)

    def test_json_serialization_rejects_non_finite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            report = observe_3mf(source)
            report["project"]["invalid_number"] = float("nan")

            with self.assertRaises(ObservationError):
                serialize_json(report)

    def test_validate_report_rejects_malformed_nested_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            valid = observe_3mf(source)
            cases = [
                (
                    "source type",
                    lambda report: report.__setitem__("source", []),
                    "source",
                ),
                (
                    "source field",
                    lambda report: report["source"].pop("file_name"),
                    "source",
                ),
                (
                    "source field type",
                    lambda report: report["source"].__setitem__(
                        "member_count", "five"
                    ),
                    "source.member_count",
                ),
                (
                    "project type",
                    lambda report: report.__setitem__("project", []),
                    "project",
                ),
                (
                    "project field",
                    lambda report: report["project"].pop("title"),
                    "project",
                ),
                (
                    "project field type",
                    lambda report: report["project"].__setitem__("title", 7),
                    "project.title",
                ),
                (
                    "physical tools field",
                    lambda report: report["physical_tools"].pop(
                        "nozzle_diameters"
                    ),
                    "physical_tools",
                ),
                (
                    "nozzle entry type",
                    lambda report: report["physical_tools"].__setitem__(
                        "nozzle_diameters", [0.4]
                    ),
                    "physical_tools.nozzle_diameters[0]",
                ),
                (
                    "materials type",
                    lambda report: report.__setitem__("materials", {}),
                    "materials",
                ),
                (
                    "material field",
                    lambda report: report["materials"][0].pop("slot"),
                    "materials[0]",
                ),
                (
                    "material field type",
                    lambda report: report["materials"][0].__setitem__(
                        "profile", []
                    ),
                    "materials[0].profile",
                ),
                (
                    "plate field",
                    lambda report: report["plates"][0].pop("object_ids"),
                    "plates[0]",
                ),
                (
                    "plate field type",
                    lambda report: report["plates"][0].__setitem__(
                        "object_ids", "2"
                    ),
                    "plates[0].object_ids",
                ),
                (
                    "object field",
                    lambda report: report["objects"][0].pop("name"),
                    "objects[0]",
                ),
                (
                    "object field type",
                    lambda report: report["objects"][0].__setitem__(
                        "semantic_name_tokens", "glass"
                    ),
                    "objects[0].semantic_name_tokens",
                ),
                (
                    "geometry field",
                    lambda report: report["objects"][0]["geometry"].pop(
                        "bounds"
                    ),
                    "objects[0].geometry",
                ),
                (
                    "geometry field type",
                    lambda report: report["objects"][0]["geometry"].__setitem__(
                        "dimensions", [1.0, 2.0]
                    ),
                    "objects[0].geometry.dimensions",
                ),
                (
                    "geometry enormous integer",
                    lambda report: report["objects"][0]["geometry"].__setitem__(
                        "dimensions", [10**1000, 2, 3]
                    ),
                    "objects[0].geometry.dimensions[0]",
                ),
                (
                    "report warning type",
                    lambda report: report.__setitem__("warnings", [7]),
                    "warnings[0]",
                ),
                (
                    "object warning type",
                    lambda report: report["objects"][0].__setitem__(
                        "warnings", "warning"
                    ),
                    "objects[0].warnings",
                ),
            ]

            for label, mutate, context in cases:
                report = copy.deepcopy(valid)
                mutate(report)
                with self.subTest(label=label), self.assertRaisesRegex(
                    ObservationError, context.replace("[", r"\[")
                ):
                    validate_report(report)

    def test_serializers_reject_non_null_observer_authority_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            valid = observe_3mf(source)
            cases = [
                ("physical_nozzle_assignment", 1),
                ("recommended_tool_class", "fine"),
            ]
            for field, value in cases:
                for serializer in (serialize_json, serialize_markdown):
                    report = copy.deepcopy(valid)
                    report["objects"][0][field] = value
                    with self.subTest(
                        field=field, serializer=serializer.__name__
                    ), self.assertRaisesRegex(
                        ObservationError,
                        rf"objects\[0\]\.{field} must be null",
                    ):
                        serializer(report)

    def test_write_reports_rejects_authority_mutation_before_replacement(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            markdown_path = root / "report.md"
            write_synthetic_3mf(source)
            valid = observe_3mf(source)
            for field, value in (
                ("physical_nozzle_assignment", 1),
                ("recommended_tool_class", "standard"),
            ):
                report = copy.deepcopy(valid)
                report["objects"][0][field] = value
                json_path.write_text("old json\n", encoding="utf-8")
                markdown_path.write_text("old markdown\n", encoding="utf-8")

                with self.subTest(field=field), self.assertRaisesRegex(
                    ObservationError,
                    rf"objects\[0\]\.{field} must be null",
                ):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=markdown_path,
                    )

                self.assertEqual(json_path.read_text(encoding="utf-8"), "old json\n")
                self.assertEqual(
                    markdown_path.read_text(encoding="utf-8"), "old markdown\n"
                )
                self.assertFalse(list(root.glob(".*.tmp")))
                self.assertFalse(list(root.glob(".*.bak")))

    def test_validate_report_rejects_lone_surrogates_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            valid = observe_3mf(source)
            cases = [
                (
                    "source.file_name",
                    lambda report: report["source"].__setitem__(
                        "file_name", "bad\ud800name"
                    ),
                ),
                (
                    "project.title",
                    lambda report: report["project"].__setitem__(
                        "title", "bad\udfffproject"
                    ),
                ),
                (
                    "objects[0].name",
                    lambda report: report["objects"][0].__setitem__(
                        "name", "bad\ud800object"
                    ),
                ),
                (
                    "warnings[0]",
                    lambda report: report.__setitem__(
                        "warnings", ["bad\udfffwarning"]
                    ),
                ),
            ]

            for context, mutate in cases:
                report = copy.deepcopy(valid)
                mutate(report)
                with self.subTest(context=context):
                    with self.assertRaisesRegex(
                        ObservationError, "lone surrogate"
                    ) as raised:
                        serialize_json(report)
                    self.assertIn(context, str(raised.exception))

            serialize_json(valid).encode("utf-8")

    def test_markdown_escapes_table_text_and_preserves_nozzle_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            report = observe_3mf(source)
            report["source"]["file_name"] = "source\nname.3mf"
            report["objects"][0]["name"] = "Glass|Detail\r\nSecond line.stl"
            report["physical_tools"]["nozzle_diameters"] = ["0.4", None, "0.8"]

            markdown = serialize_markdown(report)

            self.assertIn("Source: `source<br>name.3mf`", markdown)
            self.assertIn("Configured nozzle vector: `0.4,,0.8`", markdown)
            self.assertIn("Glass&#124;Detail<br>Second line.stl", markdown)
            self.assertEqual(markdown, serialize_markdown(report))
            self.assertTrue(markdown.endswith("\n"))

    def test_markdown_html_escapes_all_untrusted_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            report = observe_3mf(source)
            report["source"]["file_name"] = "<source&name>\rfile.3mf"
            report["objects"][0]["name"] = (
                "<b>A&B</b>\\|tick`\rline\nnext\r\nlast"
            )

            markdown = serialize_markdown(report)

            self.assertIn(
                "Source: `&lt;source&amp;name&gt;<br>file.3mf`", markdown
            )
            self.assertIn(
                "&lt;b&gt;A&amp;B&lt;/b&gt;\\&#124;tick&#96;"
                "<br>line<br>next<br>last",
                markdown,
            )
            self.assertNotIn("<source", markdown)
            self.assertNotIn("<b>", markdown)

    def test_writes_json_and_markdown_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            markdown_path = root / "report.md"
            write_synthetic_3mf(source)
            report = observe_3mf(source)

            write_reports(
                report,
                source_path=source,
                json_path=json_path,
                markdown_path=markdown_path,
            )

            self.assertEqual(
                json_path.read_text(encoding="utf-8"), serialize_json(report)
            )
            self.assertEqual(
                markdown_path.read_text(encoding="utf-8"),
                serialize_markdown(report),
            )
            self.assertFalse(list(root.glob(".*.tmp")))
            self.assertFalse(list(root.glob(".*.bak")))

    def test_failure_does_not_replace_existing_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            json_path.write_text("existing\n", encoding="utf-8")

            with self.assertRaises(ObservationError):
                write_reports(
                    {"not": "a report"},
                    source_path=source,
                    json_path=json_path,
                    markdown_path=None,
                )

            self.assertEqual(
                json_path.read_text(encoding="utf-8"), "existing\n"
            )

    def test_failed_replace_cleans_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            json_path.write_text("existing\n", encoding="utf-8")
            write_synthetic_3mf(source)
            report = observe_3mf(source)

            with mock.patch(
                "tools.amp_observe_3mf.os.replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaisesRegex(
                    ObservationError, "report.json.*replace failed"
                ):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=None,
                    )

            self.assertEqual(
                json_path.read_text(encoding="utf-8"), "existing\n"
            )
            self.assertFalse(list(root.glob(".*.tmp")))
            self.assertFalse(list(root.glob(".*.bak")))

    def test_second_replace_failure_restores_both_existing_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            markdown_path = root / "report.md"
            write_synthetic_3mf(source)
            json_path.write_text("old json\n", encoding="utf-8")
            markdown_path.write_text("old markdown\n", encoding="utf-8")
            report = observe_3mf(source)
            real_replace = os.replace
            replace_count = 0

            def fail_second_replace(src: Path, destination: Path) -> None:
                nonlocal replace_count
                replace_count += 1
                if replace_count == 2:
                    raise OSError("second replace failed")
                real_replace(src, destination)

            with mock.patch(
                "tools.amp_observe_3mf.os.replace",
                side_effect=fail_second_replace,
            ):
                with self.assertRaisesRegex(
                    ObservationError, "report.md.*second replace failed"
                ):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=markdown_path,
                    )

            self.assertEqual(
                json_path.read_text(encoding="utf-8"), "old json\n"
            )
            self.assertEqual(
                markdown_path.read_text(encoding="utf-8"), "old markdown\n"
            )
            self.assertFalse(list(root.glob(".*.tmp")))
            self.assertFalse(list(root.glob(".*.bak")))

    def test_second_replace_failure_removes_new_first_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            markdown_path = root / "report.md"
            write_synthetic_3mf(source)
            markdown_path.write_text("old markdown\n", encoding="utf-8")
            report = observe_3mf(source)
            real_replace = os.replace
            replace_count = 0

            def fail_second_replace(src: Path, destination: Path) -> None:
                nonlocal replace_count
                replace_count += 1
                if replace_count == 2:
                    raise OSError("second replace failed")
                real_replace(src, destination)

            with mock.patch(
                "tools.amp_observe_3mf.os.replace",
                side_effect=fail_second_replace,
            ):
                with self.assertRaises(ObservationError):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=markdown_path,
                    )

            self.assertFalse(json_path.exists())
            self.assertEqual(
                markdown_path.read_text(encoding="utf-8"), "old markdown\n"
            )
            self.assertFalse(list(root.glob(".*.tmp")))
            self.assertFalse(list(root.glob(".*.bak")))

    def test_write_reports_rejects_normalized_source_aliases_before_staging(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            write_synthetic_3mf(source)
            report = observe_3mf(source)
            aliases = [source, root / "unused" / ".." / source.name]
            case_alias = source.with_name(source.name.upper())
            if os.path.normcase(str(case_alias)) == os.path.normcase(str(source)):
                aliases.append(case_alias)

            for alias in aliases:
                with self.subTest(alias=alias), mock.patch(
                    "tools.amp_observe_3mf.tempfile.NamedTemporaryFile"
                ) as named_temp:
                    with self.assertRaisesRegex(
                        ObservationError, "JSON destination aliases source"
                    ):
                        write_reports(
                            report,
                            source_path=source,
                            json_path=alias,
                            markdown_path=None,
                        )
                    named_temp.assert_not_called()

            self.assertTrue(zipfile.is_zipfile(source))

    def test_write_reports_rejects_source_symlink_and_hardlink_aliases(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            hardlink = root / "hardlink.json"
            symlink = root / "symlink.json"
            write_synthetic_3mf(source)
            report = observe_3mf(source)
            os.link(source, hardlink)
            aliases = [hardlink]
            try:
                os.symlink(source, symlink)
            except OSError:
                pass
            else:
                aliases.append(symlink)

            for alias in aliases:
                with self.subTest(alias=alias), self.assertRaisesRegex(
                    ObservationError, "JSON destination aliases source"
                ):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=alias,
                        markdown_path=None,
                    )

            self.assertTrue(zipfile.is_zipfile(source))

    def test_write_reports_rejects_aliasing_output_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            markdown_alias = root / "unused" / ".." / json_path.name
            write_synthetic_3mf(source)
            report = observe_3mf(source)

            with self.assertRaisesRegex(
                ObservationError, "JSON and Markdown destinations alias"
            ):
                write_reports(
                    report,
                    source_path=source,
                    json_path=json_path,
                    markdown_path=markdown_alias,
                )

            self.assertFalse(json_path.exists())

    def test_write_reports_rejects_hardlinked_output_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            markdown_path = root / "report.md"
            write_synthetic_3mf(source)
            json_path.write_text("existing\n", encoding="utf-8")
            os.link(json_path, markdown_path)
            report = observe_3mf(source)

            with self.assertRaisesRegex(
                ObservationError, "JSON and Markdown destinations alias"
            ):
                write_reports(
                    report,
                    source_path=source,
                    json_path=json_path,
                    markdown_path=markdown_path,
                )

            self.assertEqual(json_path.read_text(encoding="utf-8"), "existing\n")
            self.assertEqual(
                markdown_path.read_text(encoding="utf-8"), "existing\n"
            )

    def test_write_reports_rejects_case_aliases_on_case_insensitive_filesystem(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            markdown_path = root / "REPORT.JSON"
            write_synthetic_3mf(source)
            report = observe_3mf(source)

            with mock.patch(
                "tools.amp_observe_3mf.os.path.normcase",
                side_effect=lambda value: value,
            ), mock.patch(
                "tools.amp_observe_3mf.filesystem_is_case_insensitive",
                return_value=True,
                create=True,
            ):
                with self.assertRaisesRegex(
                    ObservationError, "JSON and Markdown destinations alias"
                ):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=markdown_path,
                    )

            self.assertFalse(json_path.exists())

    def test_cli_rejects_collisions_before_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            write_synthetic_3mf(source)
            cases = [
                ["--3mf", str(source), "--out-json", str(source)],
                [
                    "--3mf",
                    str(source),
                    "--out-json",
                    str(root / "report.json"),
                    "--out-md",
                    str(root / "report.json"),
                ],
            ]

            for argv in cases:
                stderr = io.StringIO()
                with self.subTest(argv=argv), mock.patch(
                    "tools.amp_observe_3mf.observe_3mf"
                ) as observe, mock.patch("sys.stderr", stderr):
                    exit_code = main(argv)

                    self.assertEqual(exit_code, 2)
                    observe.assert_not_called()
                    self.assertIn("alias", stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())

            self.assertTrue(zipfile.is_zipfile(source))

    def test_cli_defaults_to_json_stdout_without_writing_a_report(self) -> None:
        class TrackingStdout(io.StringIO):
            flushed = False

            def flush(self) -> None:
                self.flushed = True
                super().flush()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            write_synthetic_3mf(source)
            before = sorted(item.name for item in root.iterdir())
            stdout = TrackingStdout()

            with mock.patch("sys.stdout", stdout):
                exit_code = main(["--3mf", str(source)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(stdout.getvalue())["schema_version"], "0.1"
            )
            self.assertTrue(stdout.flushed)
            self.assertEqual(sorted(item.name for item in root.iterdir()), before)

    def test_cli_reports_observation_errors_without_a_traceback(self) -> None:
        stderr = io.StringIO()

        with mock.patch("sys.stderr", stderr):
            exit_code = main(["--3mf", "missing.3mf"])

        self.assertEqual(exit_code, 2)
        self.assertIn("AMP 3MF observation failed:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_cli_wraps_output_oserror_with_destination_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            write_synthetic_3mf(source)
            stderr = io.StringIO()

            with mock.patch(
                "tools.amp_observe_3mf.tempfile.NamedTemporaryFile",
                side_effect=OSError("disk full"),
            ), mock.patch("sys.stderr", stderr):
                exit_code = main(
                    [
                        "--3mf",
                        str(source),
                        "--out-json",
                        str(json_path),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn(str(json_path), stderr.getvalue())
            self.assertIn("disk full", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertFalse(json_path.exists())

    def test_write_reports_wraps_unicode_output_error_with_destination(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            write_synthetic_3mf(source)
            report = observe_3mf(source)

            with mock.patch(
                "tools.amp_observe_3mf.tempfile.NamedTemporaryFile",
                side_effect=UnicodeError("encoding failed"),
            ):
                with self.assertRaisesRegex(
                    ObservationError, "report.json.*encoding failed"
                ):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=None,
                    )

            self.assertFalse(json_path.exists())

    def test_cli_treats_broken_stdout_pipe_without_an_error_report(self) -> None:
        class BrokenPipeStdout(io.StringIO):
            def write(self, value: str) -> int:
                raise BrokenPipeError("closed pipe")

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            stdout = BrokenPipeStdout()
            stderr = io.StringIO()

            with mock.patch("sys.stdout", stdout), mock.patch(
                "sys.stderr", stderr
            ):
                exit_code = main(["--3mf", str(source)])
                replacement = sys.stdout

            self.assertEqual(exit_code, 1)
            self.assertEqual(stderr.getvalue(), "")
            self.assertIsNot(replacement, stdout)
            replacement.flush()
            replacement.close()

    def test_cli_treats_flush_time_broken_pipe_without_an_error_report(
        self,
    ) -> None:
        class FlushBrokenPipeStdout(io.StringIO):
            def flush(self) -> None:
                raise BrokenPipeError("closed during flush")

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            stdout = FlushBrokenPipeStdout()
            stderr = io.StringIO()

            with mock.patch("sys.stdout", stdout), mock.patch(
                "sys.stderr", stderr
            ):
                exit_code = main(["--3mf", str(source)])
                replacement = sys.stdout

            self.assertEqual(exit_code, 1)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(json.loads(stdout.getvalue())["schema_version"], "0.1")
            replacement.close()

    def test_cli_wraps_immediate_stdout_oserror(self) -> None:
        class FailingStdout(io.StringIO):
            def write(self, value: str) -> int:
                raise OSError("stdout unavailable")

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            stdout = FailingStdout()
            stderr = io.StringIO()

            with mock.patch("sys.stdout", stdout), mock.patch(
                "sys.stderr", stderr
            ):
                exit_code = main(["--3mf", str(source)])
                replacement = sys.stdout

            self.assertEqual(exit_code, 2)
            self.assertIn("stdout", stderr.getvalue())
            self.assertIn("stdout unavailable", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertIsNot(replacement, stdout)
            replacement.flush()
            replacement.close()

    def test_cli_wraps_stdout_unicode_encode_error(self) -> None:
        class IncompatibleEncodingStdout(io.StringIO):
            def write(self, value: str) -> int:
                raise UnicodeEncodeError(
                    "ascii", "\N{LATIN SMALL LETTER E WITH ACUTE}", 0, 1, "ordinal"
                )

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            stdout = IncompatibleEncodingStdout()
            stderr = io.StringIO()

            with mock.patch("sys.stdout", stdout), mock.patch(
                "sys.stderr", stderr
            ):
                exit_code = main(["--3mf", str(source)])
                replacement = sys.stdout

            self.assertEqual(exit_code, 2)
            self.assertIn("stdout", stderr.getvalue())
            self.assertIn("can't encode", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertIsNot(replacement, stdout)
            replacement.flush()
            replacement.close()

    def test_write_reports_wraps_unicode_cleanup_error_with_destination(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            write_synthetic_3mf(source)
            json_path.write_text("existing\n", encoding="utf-8")
            report = observe_3mf(source)
            real_unlink = Path.unlink

            def fail_backup_cleanup(
                path: Path, *, missing_ok: bool = False
            ) -> None:
                if path.suffix == ".bak":
                    raise UnicodeError("cleanup encoding failed")
                real_unlink(path, missing_ok=missing_ok)

            with mock.patch.object(Path, "unlink", fail_backup_cleanup):
                with self.assertRaisesRegex(
                    ObservationError, "report.json.*cleanup encoding failed"
                ):
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=None,
                    )

    def test_precommit_failure_discloses_temp_cleanup_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            write_synthetic_3mf(source)
            json_path.write_text("existing\n", encoding="utf-8")
            report = observe_3mf(source)
            real_unlink = Path.unlink

            def fail_temp_cleanup(
                path: Path, *, missing_ok: bool = False
            ) -> None:
                if path.suffix == ".tmp":
                    raise OSError("temp unlink failed")
                real_unlink(path, missing_ok=missing_ok)

            with mock.patch(
                "tools.amp_observe_3mf.shutil.copy2",
                side_effect=OSError("backup copy failed"),
            ), mock.patch.object(Path, "unlink", fail_temp_cleanup):
                with self.assertRaises(ObservationError) as raised:
                    write_reports(
                        report,
                        source_path=source,
                        json_path=json_path,
                        markdown_path=None,
                    )

            leftovers = list(root.glob(".*.tmp"))
            for leftover in leftovers:
                leftover.unlink()

            message = str(raised.exception)
            self.assertEqual(
                json_path.read_text(encoding="utf-8"), "existing\n"
            )
            self.assertEqual(len(leftovers), 1)
            self.assertFalse(list(root.glob(".*.bak")))
            self.assertIn(str(json_path), message)
            self.assertIn("backup copy failed", message)
            self.assertIn("pre-commit cleanup errors", message)
            self.assertIn("temp unlink failed", message)

    def test_write_reports_wraps_path_preflight_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "synthetic.3mf"
            json_path = root / "report.json"
            write_synthetic_3mf(source)
            report = observe_3mf(source)
            cases = [
                (
                    "realpath",
                    mock.patch(
                        "tools.amp_observe_3mf.os.path.realpath",
                        side_effect=OSError("normalization failed"),
                    ),
                ),
                (
                    "samefile",
                    mock.patch(
                        "tools.amp_observe_3mf.os.path.samefile",
                        side_effect=UnicodeError("comparison failed"),
                    ),
                ),
            ]

            for label, patched_operation in cases:
                with self.subTest(label=label), patched_operation:
                    with self.assertRaisesRegex(
                        ObservationError,
                        "report path.*(normalization|comparison) failed",
                    ):
                        write_reports(
                            report,
                            source_path=source,
                            json_path=json_path,
                            markdown_path=None,
                        )

    def test_observes_source_contract_without_modifying_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            before = sha256(source)

            report = observe_3mf(source)

            self.assertEqual(report["schema_version"], "0.1")
            self.assertEqual(report["source"]["sha256"], before)
            self.assertEqual(report["source"]["member_count"], 5)
            self.assertEqual(report["source"]["plate_members"], [])
            self.assertEqual(report["source"]["plate_thumbnail_members"], [])
            self.assertEqual(sha256(source), before)

    def test_inventories_optional_plate_members_in_canonical_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "optional-plate-members.3mf"
            write_synthetic_3mf(
                source,
                optional_members=[
                    ("Metadata/plate_2.txt", b"metadata only"),
                    ("metadata/PLATE_10.WEBP", b"image"),
                    ("Metadata/nested/plate_1.JpEg", b"image"),
                    ("Metadata/not_plate_3.png", b"excluded"),
                    ("Other/plate_4.png", b"excluded"),
                ],
            )

            observed = observe_3mf(source)["source"]

            self.assertEqual(
                observed["plate_members"],
                [
                    "Metadata/nested/plate_1.JpEg",
                    "metadata/PLATE_10.WEBP",
                    "Metadata/plate_2.txt",
                ],
            )
            self.assertEqual(
                observed["plate_thumbnail_members"],
                [
                    "Metadata/nested/plate_1.JpEg",
                    "metadata/PLATE_10.WEBP",
                ],
            )

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
            self.assertEqual(
                report["objects"][0]["source_model_member"],
                "3D/Objects/detail.model",
            )
            geometry = report["objects"][0]["geometry"]
            self.assertEqual(geometry["vertex_count"], 3)
            self.assertEqual(geometry["triangle_count"], 1)
            self.assertEqual(geometry["bounds"]["min"], [0.0, 0.0, 0.0])
            self.assertEqual(geometry["bounds"]["max"], [10.0, 5.0, 2.0])
            self.assertEqual(geometry["dimensions"], [10.0, 5.0, 2.0])
            self.assertTrue(geometry["streamed"])
            self.assertEqual(report["warnings"], [])

    def test_accepts_unqualified_component_path_as_compatibility_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "unqualified-path.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(qualified_path=False),
            )

            report = observe_3mf(source)

            self.assertEqual(report["objects"][0]["geometry"]["vertex_count"], 3)

    def test_rejects_conflicting_qualified_and_unqualified_component_paths(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "conflicting-paths.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(
                    unqualified_component_path="/3D/Objects/other.model"
                ),
            )

            with self.assertRaisesRegex(
                ObservationError,
                "conflicting qualified and unqualified paths for object 2",
            ):
                observe_3mf(source)

    def test_never_reads_referenced_object_model_member_into_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "streaming-read-spy.3mf"
            write_synthetic_3mf(source)
            original_read = zipfile.ZipFile.read
            read_members: list[str] = []

            def tracking_read(
                archive: zipfile.ZipFile,
                name: str | zipfile.ZipInfo,
                pwd: bytes | None = None,
            ) -> bytes:
                member_name = (
                    name.filename if isinstance(name, zipfile.ZipInfo) else name
                )
                read_members.append(member_name)
                return original_read(archive, name, pwd)

            with mock.patch.object(zipfile.ZipFile, "read", new=tracking_read):
                report = observe_3mf(source)

            self.assertEqual(report["objects"][0]["geometry"]["vertex_count"], 3)
            self.assertNotIn("3D/Objects/detail.model", read_members)
            self.assertIn(ROOT_MODEL, read_members)

    def test_streaming_parser_unlinks_high_cardinality_children(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "high-cardinality.3mf"
            vertex_count = 5000
            detail = object_model_xml(
                [(index, index % 11, index % 7) for index in range(vertex_count)],
                [],
            )
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(qualified_path=False),
                object_model_data=detail,
            )
            real_iterparse = ET.iterparse
            retained_element_counts: list[int] = []
            requested_events: list[tuple[str, ...]] = []

            def tracking_iterparse(handle: object, events: tuple[str, ...]):
                requested_events.append(events)
                iterator = real_iterparse(handle, events=events)
                for event, element in iterator:
                    yield event, element
                retained_element_counts.append(sum(1 for _ in iterator.root.iter()))

            with mock.patch(
                "tools.amp_observe_3mf.ET.iterparse", new=tracking_iterparse
            ):
                report = observe_3mf(source)

            self.assertEqual(report["objects"][0]["geometry"]["vertex_count"], 5000)
            self.assertEqual(requested_events, [("start", "end")])
            self.assertEqual(retained_element_counts, [1])

    def test_rejects_invalid_vertex_coordinates_contextually(self) -> None:
        valid_detail = object_model_xml([(1, 2, 3)], [])
        cases = [
            ("nan", b'x="1"', b'x="NaN"'),
            ("positive infinity", b'x="1"', b'x="Infinity"'),
            ("negative infinity", b'x="1"', b'x="-Infinity"'),
            ("overflow", b'x="1"', b'x="1e309"'),
            ("nonnumeric", b'x="1"', b'x="not-a-number"'),
            ("missing", b' x="1"', b""),
        ]
        for label, original, replacement in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / f"invalid-coordinate-{label}.3mf"
                write_synthetic_3mf(
                    source,
                    root_model=synthetic_root_model(qualified_path=False),
                    object_model_data=valid_detail.replace(
                        original, replacement, 1
                    ),
                )

                with self.assertRaisesRegex(
                    ObservationError,
                    r"object-model member 3D/Objects/detail\.model "
                    r"object 1 vertex x coordinate",
                ):
                    observe_3mf(source)

    def test_applies_component_transform_to_geometry_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "transformed.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(
                    transform="2 0 0 0 3 0 0 0 4 7 11 13"
                ),
            )

            geometry = observe_3mf(source)["objects"][0]["geometry"]

            self.assertEqual(geometry["bounds"]["min"], [7.0, 11.0, 13.0])
            self.assertEqual(geometry["bounds"]["max"], [27.0, 26.0, 21.0])
            self.assertEqual(geometry["dimensions"], [20.0, 15.0, 8.0])

    def test_rejects_invalid_component_transforms_contextually(self) -> None:
        cases = [
            ("wrong count", "1 0 0 0 1 0 0 0 1 0 0"),
            ("nonnumeric", "1 0 0 0 1 0 0 0 1 0 no 0"),
            ("nan", "1 0 0 0 1 0 0 0 1 0 NaN 0"),
            ("positive infinity", "1 0 0 0 1 0 0 0 1 0 Infinity 0"),
            ("negative infinity", "1 0 0 0 1 0 0 0 1 0 -Infinity 0"),
            ("overflow", "1 0 0 0 1 0 0 0 1 0 1e309 0"),
        ]
        for label, transform in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / f"invalid-transform-{label}.3mf"
                write_synthetic_3mf(
                    source,
                    root_model=synthetic_root_model(transform=transform),
                )

                with self.assertRaisesRegex(
                    ObservationError, "object 2 component transform"
                ):
                    observe_3mf(source)

    def test_rejects_non_finite_transformed_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "overflowing-transform-result.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(
                    transform="1e308 0 0 0 1 0 0 0 1 0 0 0"
                ),
            )

            with self.assertRaisesRegex(
                ObservationError, "non-finite transformed coordinate"
            ):
                observe_3mf(source)

    def test_counts_only_referenced_core_object_mesh_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "object-identity.3mf"
            detail = object_model_objects_xml(
                [
                    (1, [([(0, 0, 0), (2, 0, 0), (0, 3, 1)], [(0, 1, 2)])]),
                    (
                        99,
                        [
                            (
                                [(-50, -50, -50), (50, 0, 0), (0, 50, 0)],
                                [(0, 1, 2), (2, 1, 0)],
                            )
                        ],
                    ),
                ],
                extension_noise=True,
            )
            write_synthetic_3mf(source, object_model_data=detail)

            geometry = observe_3mf(source)["objects"][0]["geometry"]

            self.assertEqual(geometry["vertex_count"], 3)
            self.assertEqual(geometry["triangle_count"], 1)
            self.assertEqual(geometry["bounds"]["min"], [0.0, 0.0, 0.0])
            self.assertEqual(geometry["bounds"]["max"], [2.0, 3.0, 1.0])

    def test_aggregates_multiple_meshes_and_components_from_one_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "component-aggregation.3mf"
            detail = object_model_objects_xml(
                [
                    (
                        1,
                        [
                            ([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)]),
                            ([(0, 0, 1)], []),
                        ],
                    ),
                    (
                        2,
                        [
                            (
                                [(10, 0, 0), (11, 0, 0), (10, 1, 0)],
                                [(0, 1, 2)],
                            )
                        ],
                    ),
                ]
            )
            root_model = synthetic_root_model(
                component_references=[
                    ("/3D/Objects/detail.model", "1", None),
                    (
                        "/3D/Objects/detail.model",
                        "2",
                        "1 0 0 0 1 0 0 0 1 0 0 2",
                    ),
                ]
            )
            write_synthetic_3mf(
                source, root_model=root_model, object_model_data=detail
            )

            geometry = observe_3mf(source)["objects"][0]["geometry"]

            self.assertEqual(geometry["vertex_count"], 7)
            self.assertEqual(geometry["triangle_count"], 2)
            self.assertEqual(geometry["bounds"]["min"], [0.0, 0.0, 0.0])
            self.assertEqual(geometry["bounds"]["max"], [11.0, 1.0, 2.0])

    def test_rejects_invalid_triangle_indices_contextually(self) -> None:
        valid_detail = object_model_xml(
            [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)]
        )
        cases = [
            ("missing", b' v1="0"', b"", "v1"),
            ("nonnumeric", b'v2="1"', b'v2="bad"', "v2"),
            ("negative", b'v3="2"', b'v3="-1"', "v3"),
            ("out of range", b'v1="0"', b'v1="3"', "v1"),
        ]
        for label, original, replacement, attribute in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / f"invalid-triangle-{label}.3mf"
                write_synthetic_3mf(
                    source,
                    object_model_data=valid_detail.replace(
                        original, replacement, 1
                    ),
                )

                with self.assertRaisesRegex(
                    ObservationError,
                    rf"object-model member 3D/Objects/detail\.model object 1 "
                    rf"mesh triangle {attribute} index",
                ):
                    observe_3mf(source)

    def test_rejects_triangle_index_outside_its_current_mesh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "per-mesh-triangle-index.3mf"
            detail = object_model_objects_xml(
                [
                    (
                        1,
                        [
                            ([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)]),
                            ([(2, 2, 2)], [(0, 0, 1)]),
                        ],
                    )
                ]
            )
            write_synthetic_3mf(source, object_model_data=detail)

            with self.assertRaisesRegex(
                ObservationError,
                "mesh triangle v3 index 1 out of range for 1 vertices",
            ):
                observe_3mf(source)

    def test_validates_each_mesh_against_its_own_vertex_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "valid-multiple-mesh-topology.3mf"
            detail = object_model_objects_xml(
                [
                    (
                        1,
                        [
                            ([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)]),
                            ([(2, 2, 2)], [(0, 0, 0)]),
                        ],
                    )
                ]
            )
            write_synthetic_3mf(source, object_model_data=detail)

            geometry = observe_3mf(source)["objects"][0]["geometry"]

            self.assertEqual(geometry["vertex_count"], 4)
            self.assertEqual(geometry["triangle_count"], 2)

    def test_rejects_missing_referenced_object_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "missing-object-identity.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(referenced_object_id="7"),
            )

            with self.assertRaisesRegex(
                ObservationError,
                "missing referenced object id 7 in object-model member",
            ):
                observe_3mf(source)

    def test_rejects_malformed_referenced_object_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "malformed-object-identity.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(referenced_object_id="bad"),
            )

            with self.assertRaisesRegex(
                ObservationError, "invalid root object 2 component objectid: 'bad'"
            ):
                observe_3mf(source)

    def test_rejects_noncanonical_referenced_object_model_paths(self) -> None:
        invalid_paths = [
            "",
            "3D/Objects/detail.model",
            "/3D/Objects/./detail.model",
            "/3D/Objects/../detail.model",
            "/3D\\Objects\\detail.model",
            "/3D//Objects/detail.model",
            "/3D/Objects/detail.model#fragment",
            "/3D/Objects/detail.model?query=1",
            "/3D/Objects/%2E/detail.model",
            "/3D/Objects/%2e%2e/detail.model",
            "/3D/Objects/d%65tail.model",
            "/3D/Objects/detail%2Fmodel",
            "/3D/Objects/detail%ZZ.model",
            "/3D/Objects/.../detail.model",
            "/3D/Objects/name./detail.model",
            "/3D/Objects/raw space.model",
            "/3D/Objects/caf\u00e9.model",
            "/3D/Objects/unsupported[character].model",
            "/3D/Objects/",
            "/Metadata/detail.model",
        ]
        for index, component_path in enumerate(invalid_paths):
            with self.subTest(
                path=component_path
            ), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / f"invalid-reference-{index}.3mf"
                write_synthetic_3mf(
                    source,
                    root_model=synthetic_root_model(component_path=component_path),
                )

                with self.assertRaisesRegex(
                    ObservationError,
                    "invalid referenced object-model path for object 2",
                ):
                    observe_3mf(source)

    def test_accepts_normalized_ascii_uri_object_member_names(self) -> None:
        valid_names = [
            "simple.model",
            "A-Z_a-z.0~!$&'()*+,;=:@.model",
            "detail%20part.model",
            "nested/part-name.model",
        ]
        detail = object_model_xml([(0, 0, 0)], [])
        for index, name in enumerate(valid_names):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / f"valid-part-name-{index}.3mf"
                member_name = f"3D/Objects/{name}"
                write_synthetic_3mf(
                    source,
                    root_model=synthetic_root_model(
                        component_path=f"/{member_name}"
                    ),
                    object_model_members=[(member_name, detail)],
                )

                report = observe_3mf(source)

                self.assertEqual(
                    report["objects"][0]["source_model_member"], member_name
                )

    def test_accepts_canonical_percent_encoded_object_member_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "percent-encoded-part-name.3mf"
            detail = object_model_xml([(0, 0, 0)], [])
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(
                    component_path="/3D/Objects/detail%20part.model"
                ),
                object_model_members=[
                    ("3D/Objects/detail%20part.model", detail)
                ],
            )

            report = observe_3mf(source)

            self.assertEqual(
                report["objects"][0]["source_model_member"],
                "3D/Objects/detail%20part.model",
            )

    def test_resolves_object_members_with_opc_case_insensitive_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "case-insensitive-part-name.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(
                    component_path="/3d/objects/DETAIL.model"
                ),
            )

            report = observe_3mf(source)

            self.assertEqual(
                report["objects"][0]["source_model_member"],
                "3D/Objects/detail.model",
            )

    def test_rejects_ascii_case_equivalent_duplicate_object_model_members(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "canonical-duplicate.3mf"
            detail = object_model_xml([(0, 0, 0)], [])
            write_synthetic_3mf(
                source,
                object_model_members=[
                    ("3D/Objects/detail.model", detail),
                    ("3d/objects/DETAIL.model", detail),
                ],
            )

            with self.assertRaisesRegex(
                ObservationError, "ambiguous canonical object-model member"
            ):
                observe_3mf(source)

    def test_rejects_noncanonical_object_model_zip_member_names(self) -> None:
        invalid_member_names = [
            "3D/Objects/../Objects/detail.model",
            "3D/Objects/control\x01.model",
        ]
        detail = object_model_xml([(0, 0, 0)], [])
        for index, member_name in enumerate(invalid_member_names):
            with self.subTest(
                name=member_name
            ), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / f"invalid-central-name-{index}.3mf"
                write_synthetic_3mf(
                    source,
                    object_model_members=[(member_name, detail)],
                )

                with self.assertRaisesRegex(
                    ObservationError, "invalid object-model ZIP member name"
                ):
                    observe_3mf(source)

    def test_rejects_missing_referenced_object_model_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "missing-object-model.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(
                    component_path="/3D/Objects/missing.model"
                ),
            )

            with self.assertRaisesRegex(
                ObservationError, "missing referenced object-model member"
            ):
                observe_3mf(source)

    def test_rejects_duplicate_referenced_object_model_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "duplicate-object-model.3mf"
            write_synthetic_3mf(source)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(source, "a") as archive:
                    archive.writestr(
                        "3D/Objects/detail.model",
                        object_model_xml([(1, 1, 1)], []),
                    )

            with self.assertRaisesRegex(
                ObservationError, "duplicate referenced object-model member"
            ):
                observe_3mf(source)

    def test_rejects_malformed_root_object_id_contextually(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "malformed-root-object-id.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(object_id="not-an-id"),
            )

            with self.assertRaisesRegex(
                ObservationError, "invalid root object id: 'not-an-id'"
            ):
                observe_3mf(source)

    def test_rejects_empty_referenced_object_model_path_contextually(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "empty-object-model-path.3mf"
            write_synthetic_3mf(
                source,
                root_model=synthetic_root_model(component_path="/"),
            )

            with self.assertRaisesRegex(
                ObservationError,
                "invalid referenced object-model path for object 2: '/'",
            ):
                observe_3mf(source)

    def test_aggregates_components_across_model_members_in_canonical_order(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "multiple-object-models.3mf"
            root_model = synthetic_root_model(
                component_references=[
                    (
                        "/3D/Objects/zeta.model",
                        "4",
                        "1 0 0 0 1 0 0 0 1 20 0 0",
                    ),
                    ("/3D/Objects/alpha.model", "2", None),
                ]
            )
            alpha = object_model_objects_xml(
                [(2, [([(0, 0, 0), (2, 0, 0), (0, 3, 0)], [(0, 1, 2)])])]
            )
            zeta = object_model_objects_xml(
                [(4, [([(0, 0, 0), (1, 0, 0), (0, 1, 5)], [(0, 1, 2)])])]
            )
            opened_members: list[str] = []
            real_open = zipfile.ZipFile.open

            def tracking_open(
                archive: zipfile.ZipFile,
                name: str | zipfile.ZipInfo,
                mode: str = "r",
                pwd: bytes | None = None,
                *,
                force_zip64: bool = False,
            ) -> object:
                member_name = (
                    name.filename if isinstance(name, zipfile.ZipInfo) else name
                )
                if member_name.startswith("3D/Objects/"):
                    opened_members.append(member_name)
                return real_open(
                    archive, name, mode, pwd, force_zip64=force_zip64
                )

            write_synthetic_3mf(
                source,
                root_model=root_model,
                object_model_members=[
                    ("3D/Objects/zeta.model", zeta),
                    ("3D/Objects/alpha.model", alpha),
                ],
            )

            with mock.patch.object(zipfile.ZipFile, "open", new=tracking_open):
                observed = observe_3mf(source)["objects"][0]

            self.assertEqual(
                observed["source_model_members"],
                ["3D/Objects/alpha.model", "3D/Objects/zeta.model"],
            )
            self.assertIsNone(observed["source_model_member"])
            self.assertEqual(
                opened_members,
                ["3D/Objects/alpha.model", "3D/Objects/zeta.model"],
            )
            self.assertEqual(observed["geometry"]["vertex_count"], 6)
            self.assertEqual(observed["geometry"]["triangle_count"], 2)
            self.assertEqual(observed["geometry"]["bounds"]["min"], [0.0, 0.0, 0.0])
            self.assertEqual(observed["geometry"]["bounds"]["max"], [21.0, 3.0, 5.0])

    def test_counts_each_shared_mesh_component_transform_occurrence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "shared-mesh-occurrences.3mf"
            root_model = synthetic_root_model(
                component_references=[
                    ("/3D/Objects/detail.model", "1", None),
                    (
                        "/3D/Objects/detail.model",
                        "1",
                        "1 0 0 0 1 0 0 0 1 50 0 0",
                    ),
                ]
            )
            write_synthetic_3mf(source, root_model=root_model)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(
                observed["source_model_members"], ["3D/Objects/detail.model"]
            )
            self.assertEqual(
                observed["source_model_member"], "3D/Objects/detail.model"
            )
            self.assertEqual(observed["geometry"]["vertex_count"], 6)
            self.assertEqual(observed["geometry"]["triangle_count"], 2)
            self.assertEqual(observed["geometry"]["bounds"]["min"], [0.0, 0.0, 0.0])
            self.assertEqual(observed["geometry"]["bounds"]["max"], [60.0, 5.0, 2.0])

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

    def test_rejects_out_of_range_metadata_integer_domains(self) -> None:
        base = synthetic_model_settings()
        cases = [
            (
                "zero object id",
                base.replace(b'<object id="2">', b'<object id="0">'),
                r"object id must be positive: 0",
            ),
            (
                "negative object id",
                base.replace(b'<object id="2">', b'<object id="-2">'),
                r"object id must be positive: -2",
            ),
            (
                "zero plate id",
                base.replace(
                    b'key="plater_id" value="1"',
                    b'key="plater_id" value="0"',
                ),
                r"plate id must be positive: 0",
            ),
            (
                "negative plate id",
                base.replace(
                    b'key="plater_id" value="1"',
                    b'key="plater_id" value="-1"',
                ),
                r"plate id must be positive: -1",
            ),
            (
                "zero referenced object id",
                base.replace(
                    b'key="object_id" value="2"',
                    b'key="object_id" value="0"',
                ),
                r"plate 1 object id must be positive: 0",
            ),
            (
                "negative referenced object id",
                base.replace(
                    b'key="object_id" value="2"',
                    b'key="object_id" value="-2"',
                ),
                r"plate 1 object id must be positive: -2",
            ),
            (
                "negative extruder",
                base.replace(
                    b'key="extruder" value=" 2 "',
                    b'key="extruder" value="-1"',
                ),
                r"object 2 extruder must be nonnegative: -1",
            ),
        ]
        for label, model_settings, message in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / "out-of-range.3mf"
                write_synthetic_3mf(source, model_settings=model_settings)

                with self.assertRaisesRegex(ObservationError, message):
                    observe_3mf(source)

    def test_treats_zero_extruder_as_inherited_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "inherited-extruder.3mf"
            model_settings = synthetic_model_settings().replace(
                b'key="extruder" value=" 2 "', b'key="extruder" value="0"'
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            report = observe_3mf(source)

            self.assertIsNone(report["objects"][0]["material_assignment"])
            self.assertIsNone(report["objects"][0]["resolved_material"])
            self.assertEqual(report["objects"][0]["warnings"], [])

    def test_part_assignments_inherit_object_slot_and_sort_by_part_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "inherited-part-extruders.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<part id="1" subtype="normal_part"/>',
                b'''<part id="9" subtype="normal_part"/>
    <part id="3" subtype="normal_part"><metadata key="extruder" value="0"/></part>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(
                observed["part_assignments"],
                [
                    {
                        "part_id": 3,
                        "explicit_material_assignment": None,
                        "effective_material_assignment": 2,
                        "resolved_material": observed["resolved_material"],
                    },
                    {
                        "part_id": 9,
                        "explicit_material_assignment": None,
                        "effective_material_assignment": 2,
                        "resolved_material": observed["resolved_material"],
                    },
                ],
            )
            self.assertEqual(observed["material_assignment"], 2)

    def test_part_override_replaces_object_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "part-override.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<part id="1" subtype="normal_part"/>',
                b'''<part id="1" subtype="normal_part">
      <metadata key="extruder" value="1"/>
    </part>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(observed["material_assignment"], 1)
            self.assertEqual(observed["resolved_material"]["slot"], 1)
            self.assertEqual(
                observed["part_assignments"][0]["explicit_material_assignment"], 1
            )
            self.assertEqual(
                observed["part_assignments"][0]["effective_material_assignment"],
                1,
            )

    def test_mixed_effective_part_slots_clear_object_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "mixed-parts.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<part id="1" subtype="normal_part"/>',
                b'''<part id="8" subtype="normal_part"/>
    <part id="2" subtype="normal_part"><metadata key="extruder" value="1"/></part>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(
                [
                    part["effective_material_assignment"]
                    for part in observed["part_assignments"]
                ],
                [1, 2],
            )
            self.assertIsNone(observed["material_assignment"])
            self.assertIsNone(observed["resolved_material"])
            self.assertEqual(
                observed["warnings"],
                ["mixed effective part material assignments: 1, 2"],
            )

    def test_known_and_unresolved_parts_clear_object_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "known-and-unresolved-parts.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<metadata key="extruder" value=" 2 "/>',
                b'<metadata key="extruder" value="0"/>',
            ).replace(
                b'<part id="1" subtype="normal_part"/>',
                b'''<part id="2" subtype="normal_part"/>
    <part id="1" subtype="normal_part"><metadata key="extruder" value="1"/></part>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(
                [
                    part["effective_material_assignment"]
                    for part in observed["part_assignments"]
                ],
                [1, None],
            )
            self.assertIsNone(observed["material_assignment"])
            self.assertIsNone(observed["resolved_material"])
            self.assertEqual(
                observed["warnings"],
                [
                    "known effective part material assignments: 1; unresolved part assignments are present"
                ],
            )

    def test_all_unresolved_parts_keep_null_summary_without_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "all-unresolved-parts.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<metadata key="extruder" value=" 2 "/>',
                b'<metadata key="extruder" value="0"/>',
            ).replace(
                b'<part id="1" subtype="normal_part"/>',
                b'''<part id="2" subtype="normal_part"/>
    <part id="1" subtype="normal_part"><metadata key="extruder" value="0"/></part>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(
                [
                    part["effective_material_assignment"]
                    for part in observed["part_assignments"]
                ],
                [None, None],
            )
            self.assertIsNone(observed["material_assignment"])
            self.assertIsNone(observed["resolved_material"])
            self.assertEqual(observed["warnings"], [])

    def test_object_assignment_is_preserved_when_object_has_no_parts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "no-parts.3mf"
            model_settings = synthetic_model_settings().replace(
                b'    <part id="1" subtype="normal_part"/>\n', b""
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(observed["part_count"], 0)
            self.assertEqual(observed["part_assignments"], [])
            self.assertEqual(observed["material_assignment"], 2)
            self.assertEqual(observed["resolved_material"]["slot"], 2)

    def test_rejects_malformed_part_identity_and_extruder(self) -> None:
        base = synthetic_model_settings()
        cases = [
            (
                "missing part id",
                base.replace(b'<part id="1"', b"<part"),
                "missing object 2 part id",
            ),
            (
                "nonpositive part id",
                base.replace(b'<part id="1"', b'<part id="0"'),
                "object 2 part id must be positive: 0",
            ),
            (
                "malformed part extruder",
                base.replace(
                    b'<part id="1" subtype="normal_part"/>',
                    b'<part id="1"><metadata key="extruder" value="bad"/></part>',
                ),
                "invalid object 2 part 1 extruder: 'bad'",
            ),
            (
                "negative part extruder",
                base.replace(
                    b'<part id="1" subtype="normal_part"/>',
                    b'<part id="1"><metadata key="extruder" value="-1"/></part>',
                ),
                "object 2 part 1 extruder must be nonnegative: -1",
            ),
        ]
        for label, model_settings, message in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / "malformed-part.3mf"
                write_synthetic_3mf(source, model_settings=model_settings)

                with self.assertRaisesRegex(ObservationError, message):
                    observe_3mf(source)

    def test_rejects_duplicate_part_identity_within_an_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "duplicate-part.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<part id="1" subtype="normal_part"/>',
                b'<part id="1"/><part id="1"/>',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(
                ObservationError, "duplicate part id 1 in object 2"
            ):
                observe_3mf(source)

    def test_warns_for_unresolved_effective_part_slots_in_slot_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "unresolved-part-slots.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<part id="1" subtype="normal_part"/>',
                b'''<part id="2"><metadata key="extruder" value="4"/></part>
    <part id="1"><metadata key="extruder" value="3"/></part>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(
                observed["warnings"],
                [
                    "mixed effective part material assignments: 3, 4",
                    "effective part material assignment 3 does not resolve to a configured slot",
                    "effective part material assignment 4 does not resolve to a configured slot",
                ],
            )
            self.assertTrue(
                all(
                    part["resolved_material"] is None
                    for part in observed["part_assignments"]
                )
            )

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

    def test_observes_multi_plate_and_multi_instance_membership(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "multi-plate-membership.3mf"
            model_settings = synthetic_model_settings().replace(
                b'''<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="Detail Plate"/><model_instance><metadata key="object_id" value="2"/></model_instance></plate>''',
                b'''<plate>
    <metadata key="plater_id" value="2"/>
    <metadata key="plater_name" value="Zulu Plate"/>
    <model_instance><metadata key="instance_id" value="1"/><metadata key="object_id" value="2"/></model_instance>
  </plate>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="Alpha Plate"/>
    <model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="2"/></model_instance>
    <model_instance><metadata key="instance_id" value="0"/><metadata key="object_id" value="2"/></model_instance>
  </plate>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            report = observe_3mf(source)
            observed = report["objects"][0]

            self.assertEqual(
                report["plates"],
                [
                    {
                        "plate_id": 1,
                        "name": "Alpha Plate",
                        "object_ids": [2],
                        "instances": [
                            {"object_id": 2, "instance_id": 0},
                            {"object_id": 2, "instance_id": 2},
                        ],
                    },
                    {
                        "plate_id": 2,
                        "name": "Zulu Plate",
                        "object_ids": [2],
                        "instances": [{"object_id": 2, "instance_id": 1}],
                    },
                ],
            )
            self.assertEqual(observed["plate_ids"], [1, 2])
            self.assertEqual(observed["plate_names"], ["Alpha Plate", "Zulu Plate"])
            self.assertIsNone(observed["plate_id"])
            self.assertIsNone(observed["plate_name"])
            self.assertEqual(
                observed["instances"],
                [
                    {
                        "plate_id": 1,
                        "plate_name": "Alpha Plate",
                        "instance_id": 0,
                    },
                    {
                        "plate_id": 1,
                        "plate_name": "Alpha Plate",
                        "instance_id": 2,
                    },
                    {
                        "plate_id": 2,
                        "plate_name": "Zulu Plate",
                        "instance_id": 1,
                    },
                ],
            )
            self.assertEqual(
                observed["warnings"],
                ["object appears on multiple plates: 1, 2"],
            )

    def test_rejects_duplicate_instance_identity_within_a_plate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "duplicate-instance.3mf"
            duplicate = b'''<model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="0"/></model_instance>'''
            model_settings = synthetic_model_settings().replace(
                b'<model_instance><metadata key="object_id" value="2"/></model_instance>',
                duplicate + duplicate,
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(
                ObservationError,
                "duplicate instance identity on plate 1: object 2, instance 0",
            ):
                observe_3mf(source)

    def test_rejects_explicit_instance_identity_repeated_across_plates(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "cross-plate-duplicate-instance.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<model_instance><metadata key="object_id" value="2"/></model_instance>',
                b'''<model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="0"/></model_instance>''',
            ).replace(
                b"</config>",
                b'''<plate><metadata key="plater_id" value="2"/><metadata key="plater_name" value="Other"/><model_instance><metadata key="instance_id" value="0"/><metadata key="object_id" value="2"/></model_instance></plate></config>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            with self.assertRaisesRegex(
                ObservationError,
                "duplicate explicit instance identity across plates: object 2, instance 0 on plates 1 and 2",
            ):
                observe_3mf(source)

    def test_allows_cross_plate_object_with_distinct_explicit_instance_ids(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "cross-plate-distinct-instances.3mf"
            model_settings = synthetic_model_settings().replace(
                b'<model_instance><metadata key="object_id" value="2"/></model_instance>',
                b'''<model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="0"/></model_instance>''',
            ).replace(
                b"</config>",
                b'''<plate><metadata key="plater_id" value="2"/><metadata key="plater_name" value="Other"/><model_instance><metadata key="instance_id" value="1"/><metadata key="object_id" value="2"/></model_instance></plate></config>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(observed["plate_ids"], [1, 2])
            self.assertEqual(
                [instance["instance_id"] for instance in observed["instances"]],
                [0, 1],
            )

    def test_allows_cross_plate_instances_without_explicit_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "cross-plate-implicit-instances.3mf"
            model_settings = synthetic_model_settings().replace(
                b"</config>",
                b'''<plate><metadata key="plater_id" value="2"/><metadata key="plater_name" value="Other"/><model_instance><metadata key="object_id" value="2"/></model_instance></plate></config>''',
            )
            write_synthetic_3mf(source, model_settings=model_settings)

            observed = observe_3mf(source)["objects"][0]

            self.assertEqual(observed["plate_ids"], [1, 2])
            self.assertEqual(
                [instance["instance_id"] for instance in observed["instances"]],
                [None, None],
            )

    def test_rejects_malformed_and_negative_instance_ids(self) -> None:
        base = synthetic_model_settings().replace(
            b'<metadata key="object_id" value="2"/>',
            b'<metadata key="object_id" value="2"/><metadata key="instance_id" value="VALUE"/>',
        )
        cases = [
            ("malformed", base.replace(b"VALUE", b"bad"), "invalid plate 1 instance id: 'bad'"),
            (
                "negative",
                base.replace(b"VALUE", b"-1"),
                "plate 1 instance id must be nonnegative: -1",
            ),
        ]
        for label, model_settings, message in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / "invalid-instance.3mf"
                write_synthetic_3mf(source, model_settings=model_settings)

                with self.assertRaisesRegex(ObservationError, message):
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

    def test_warns_and_clears_invalid_material_vector_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invalid-material-entries.3mf"
            project_settings = synthetic_project_settings()
            project_settings["filament_settings_id"] = [
                "Basic PLA",
                {"name": "Nested"},
                ["Nested"],
                7,
                True,
                None,
            ]
            project_settings["filament_colour"] = [
                "#111111",
                {"rgb": "#222222"},
                ["#333333"],
                4.5,
                False,
                None,
            ]
            write_synthetic_3mf(source, project_settings=project_settings)

            report = observe_3mf(source)

            self.assertEqual(
                report["materials"],
                [
                    {"slot": 1, "profile": "Basic PLA", "color": "#111111"},
                    {"slot": 2, "profile": None, "color": None},
                    {"slot": 3, "profile": None, "color": None},
                    {"slot": 4, "profile": None, "color": None},
                    {"slot": 5, "profile": None, "color": None},
                    {"slot": 6, "profile": None, "color": None},
                ],
            )
            self.assertEqual(
                report["warnings"],
                [
                    "project filament_colour slot 2 must be a string or null; got object",
                    "project filament_colour slot 3 must be a string or null; got list",
                    "project filament_colour slot 4 must be a string or null; got number",
                    "project filament_colour slot 5 must be a string or null; got boolean",
                    "project filament_settings_id slot 2 must be a string or null; got object",
                    "project filament_settings_id slot 3 must be a string or null; got list",
                    "project filament_settings_id slot 4 must be a string or null; got number",
                    "project filament_settings_id slot 5 must be a string or null; got boolean",
                ],
            )

    def test_warns_and_preserves_invalid_nozzle_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invalid-nozzle-entries.3mf"
            project_settings = synthetic_project_settings()
            project_settings["nozzle_diameter"] = [
                "0.4",
                0.6,
                1,
                None,
                {"diameter": 0.8},
                [1.0],
                True,
            ]
            write_synthetic_3mf(source, project_settings=project_settings)

            report = observe_3mf(source)

            self.assertEqual(
                report["physical_tools"]["nozzle_diameters"],
                ["0.4", "0.6", "1", None, None, None, None],
            )
            self.assertEqual(
                report["warnings"],
                [
                    "project nozzle_diameter slot 4 must be a positive finite numeric diameter; got null",
                    "project nozzle_diameter slot 5 must be a positive finite numeric diameter; got object",
                    "project nozzle_diameter slot 6 must be a positive finite numeric diameter; got list",
                    "project nozzle_diameter slot 7 must be a positive finite numeric diameter; got boolean",
                ],
            )

    def test_preserves_valid_nozzle_after_invalid_middle_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invalid-middle-nozzle.3mf"
            project_settings = synthetic_project_settings()
            project_settings["nozzle_diameter"] = ["0.4", None, "0.8"]
            write_synthetic_3mf(source, project_settings=project_settings)

            report = observe_3mf(source)

            self.assertEqual(
                report["physical_tools"]["nozzle_diameters"],
                ["0.4", None, "0.8"],
            )
            self.assertEqual(
                report["warnings"],
                [
                    "project nozzle_diameter slot 2 must be a positive finite numeric diameter; got null"
                ],
            )

    def test_warns_and_preserves_invalid_nozzle_numeric_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invalid-nozzle-domains.3mf"
            project_settings = synthetic_project_settings()
            project_settings["nozzle_diameter"] = [
                "not-a-number",
                "0",
                -0.2,
                "NaN",
                float("inf"),
                0.6,
            ]
            write_synthetic_3mf(source, project_settings=project_settings)

            report = observe_3mf(source)

            self.assertEqual(
                report["physical_tools"]["nozzle_diameters"],
                [None, None, None, None, None, "0.6"],
            )
            self.assertEqual(
                report["warnings"],
                [
                    "project nozzle_diameter slot 1 must be a positive finite numeric diameter; got nonnumeric string",
                    "project nozzle_diameter slot 2 must be a positive finite numeric diameter; got nonpositive value",
                    "project nozzle_diameter slot 3 must be a positive finite numeric diameter; got nonpositive value",
                    "project nozzle_diameter slot 4 must be a positive finite numeric diameter; got non-finite value",
                    "project nozzle_diameter slot 5 must be a positive finite numeric diameter; got non-finite value",
                ],
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
                [
                    "effective part material assignment 3 does not resolve to a configured slot"
                ],
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
