from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest import mock

from tools.amp_observe_3mf import ObservationError, observe_3mf


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

    def test_rejects_root_object_referencing_multiple_model_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "multiple-object-models.3mf"
            root_model = synthetic_root_model(
                component_references=[
                    ("/3D/Objects/detail.model", "1", None),
                    ("/3D/Objects/other.model", "2", None),
                ]
            )
            write_synthetic_3mf(source, root_model=root_model)

            with self.assertRaisesRegex(
                ObservationError, "object 2 references multiple model members"
            ):
                observe_3mf(source)

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
