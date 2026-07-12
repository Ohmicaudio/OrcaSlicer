# AMP Streaming 3MF Observer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, read-only Python observer that inventories large Orca/Bambu-style 3MF projects without extracting or modifying them and without confusing material/color assignments with physical nozzle or AMP tool recommendations.

**Architecture:** A standalone standard-library CLI opens the 3MF as a ZIP, parses small project metadata in memory, and streams referenced object-model XML with `ElementTree.iterparse`. It joins explicit metadata into a stable observation dictionary, serializes JSON/Markdown deterministically, and writes requested reports atomically while leaving the source archive byte-identical.

**Tech Stack:** Python 3, `argparse`, `dataclasses`, `hashlib`, `json`, `tempfile`, `unittest`, `xml.etree.ElementTree`, `zipfile`.

---

## File Structure

- Create `tools/amp_observe_3mf.py`: observation types, metadata parsers, streaming geometry summarizer, deterministic serializers, atomic writers, and CLI.
- Create `tests/tools/test_amp_observe_3mf.py`: synthetic 3MF fixture builder plus contract, streaming, determinism, and failure tests.
- Create `docs/benchmarks/AMP_Floating_Island_3MF_Observation_001.md`: verified real-project result after implementation.
- Modify `.gitignore` only if generated observation reports are not already covered by `outputs/`; otherwise leave it unchanged.

### Task 1: Establish the observation contract and package validation

**Files:**
- Create: `tools/amp_observe_3mf.py`
- Create: `tests/tools/test_amp_observe_3mf.py`

- [ ] **Step 1: Write the failing package-contract tests**

Create the test fixture builder and first tests:

```python
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from tools.amp_observe_3mf import ObservationError, observe_3mf


MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
ROOT_MODEL = "3D/3dmodel.model"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_model_xml(vertices: list[tuple[float, float, float]], triangles: list[tuple[int, int, int]]) -> bytes:
    namespace = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}model", {"unit": "millimeter"})
    resources = ET.SubElement(root, f"{{{namespace}}}resources")
    obj = ET.SubElement(resources, f"{{{namespace}}}object", {"id": "1", "type": "model"})
    mesh = ET.SubElement(obj, f"{{{namespace}}}mesh")
    vertices_node = ET.SubElement(mesh, f"{{{namespace}}}vertices")
    for x, y, z in vertices:
        ET.SubElement(vertices_node, f"{{{namespace}}}vertex", {"x": str(x), "y": str(y), "z": str(z)})
    triangles_node = ET.SubElement(mesh, f"{{{namespace}}}triangles")
    for v1, v2, v3 in triangles:
        ET.SubElement(triangles_node, f"{{{namespace}}}triangle", {"v1": str(v1), "v2": str(v2), "v3": str(v3)})
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
    def test_observes_source_contract_without_assigning_a_nozzle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "synthetic.3mf"
            write_synthetic_3mf(source)
            before = sha256(source)

            report = observe_3mf(source)

            self.assertEqual(report["schema_version"], "0.1")
            self.assertEqual(report["source"]["sha256"], before)
            self.assertEqual(report["source"]["member_count"], 5)
            self.assertEqual(report["physical_tools"]["nozzle_diameters"], ["0.4", "0.4"])
            self.assertEqual(report["objects"][0]["material_assignment"], 2)
            self.assertIsNone(report["objects"][0]["physical_nozzle_assignment"])
            self.assertIsNone(report["objects"][0]["recommended_tool_class"])
            self.assertEqual(sha256(source), before)

    def test_rejects_missing_required_member(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "broken.3mf"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(ROOT_MODEL, b"<model/>")
            with self.assertRaisesRegex(ObservationError, "missing required member"):
                observe_3mf(source)
```

- [ ] **Step 2: Run the focused tests and verify the import fails**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'tools.amp_observe_3mf'`.

- [ ] **Step 3: Add the minimal observation types, hashing, and ZIP validation**

Create `tools/amp_observe_3mf.py` with this initial public boundary:

```python
#!/usr/bin/env python3
"""Read-only streaming inventory for Orca/Bambu-style 3MF projects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO


ROOT_MODEL = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
REQUIRED_MEMBERS = {ROOT_MODEL, MODEL_SETTINGS, PROJECT_SETTINGS}
SCHEMA_VERSION = "0.1"


class ObservationError(ValueError):
    """Raised when a 3MF cannot produce a trustworthy observation report."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def observe_3mf(source: Path) -> dict[str, Any]:
    source = Path(source)
    try:
        with zipfile.ZipFile(source, "r") as archive:
            infos = archive.infolist()
            names = {item.filename for item in infos}
            missing = sorted(REQUIRED_MEMBERS - names)
            if missing:
                raise ObservationError("missing required member(s): " + ", ".join(missing))
            return {
                "schema_version": SCHEMA_VERSION,
                "source": {
                    "file_name": source.name,
                    "sha256": sha256_file(source),
                    "compressed_size": source.stat().st_size,
                    "member_count": len(infos),
                    "uncompressed_member_bytes": sum(item.file_size for item in infos),
                    "required_members": sorted(REQUIRED_MEMBERS),
                },
                "project": {},
                "physical_tools": {"nozzle_diameters": [], "source_member": PROJECT_SETTINGS},
                "materials": [],
                "plates": [],
                "objects": [],
                "warnings": [],
            }
    except (OSError, zipfile.BadZipFile) as exc:
        raise ObservationError(f"unreadable 3MF archive: {exc}") from exc
```

- [ ] **Step 4: Run the focused tests and confirm only the incomplete parser assertion fails**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: missing-member test passes; contract test fails because `objects` and nozzle metadata are not populated.

- [ ] **Step 5: Commit the contract foundation**

```powershell
git add tools/amp_observe_3mf.py tests/tools/test_amp_observe_3mf.py
git commit -m "test: define AMP 3MF observation contract"
```

### Task 2: Parse project, material, plate, and object metadata

**Files:**
- Modify: `tools/amp_observe_3mf.py`
- Modify: `tests/tools/test_amp_observe_3mf.py`

- [ ] **Step 1: Add failing metadata-join assertions**

Extend the contract test with:

```python
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
self.assertEqual(report["objects"][0]["resolved_material"]["slot"], 2)
self.assertEqual(report["objects"][0]["semantic_name_tokens"], ["detail", "glass"])
self.assertEqual(report["warnings"], [])
```

Add a duplicate-ID failure test by replacing `</config>` in `model_settings` with a second `<object id="2">...</object></config>` and asserting `ObservationError` contains `duplicate object id: 2`.

- [ ] **Step 2: Run the focused tests and verify metadata assertions fail**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: failures show missing project/material/plate/object values.

- [ ] **Step 3: Implement explicit metadata parsers and deterministic joins**

Add these focused helpers to `tools/amp_observe_3mf.py`:

```python
def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_json_member(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        payload = json.loads(archive.read(name).decode("utf-8"))
    except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
        raise ObservationError(f"invalid {name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ObservationError(f"invalid {name}: expected JSON object")
    return payload


def metadata_map(node: ET.Element) -> dict[str, str]:
    return {
        child.attrib["key"]: child.attrib.get("value", "")
        for child in node
        if local_name(child.tag) == "metadata" and "key" in child.attrib
    }


def parse_root_metadata(data: bytes) -> tuple[dict[str, Any], list[str]]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ObservationError(f"invalid {ROOT_MODEL}: {exc}") from exc
    values = {
        child.attrib.get("name", "").strip().lower(): (child.text or "").strip()
        for child in root
        if local_name(child.tag) == "metadata"
    }
    project = {
        "title": values.get("title") or None,
        "designer": values.get("designer") or None,
        "license": values.get("license") or None,
        "source_application": values.get("application") or None,
    }
    warnings = [
        f"project metadata is missing optional field: {key}"
        for key, value in project.items()
        if value is None
    ]
    return project, warnings


def parse_project_settings(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    nozzles = payload.get("nozzle_diameter", [])
    if not isinstance(nozzles, list):
        warnings.append("project nozzle_diameter is not a list")
        nozzles = []
    elif not nozzles:
        warnings.append("project nozzle_diameter is empty")
    profiles = payload.get("filament_settings_id", [])
    colors = payload.get("filament_colour", [])
    profiles = profiles if isinstance(profiles, list) else []
    colors = colors if isinstance(colors, list) else []
    count = max(len(profiles), len(colors))
    materials = [
        {
            "slot": index + 1,
            "profile": profiles[index] if index < len(profiles) else None,
            "color": colors[index] if index < len(colors) else None,
        }
        for index in range(count)
    ]
    project = {
        "printer_preset": payload.get("printer_settings_id"),
        "process_preset": payload.get("print_settings_id"),
        "layer_height": payload.get("layer_height"),
        "wall_generator": payload.get("wall_generator"),
    }
    physical_tools = {
        "nozzle_diameters": [str(value) for value in nozzles],
        "source_member": PROJECT_SETTINGS,
    }
    return project, physical_tools, materials, warnings


def parse_model_settings(data: bytes, materials: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ObservationError(f"invalid {MODEL_SETTINGS}: {exc}") from exc
    material_by_slot = {item["slot"]: item for item in materials}
    objects: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for node in root:
        if local_name(node.tag) != "object":
            continue
        object_id = int(node.attrib["id"])
        if object_id in seen_ids:
            raise ObservationError(f"duplicate object id: {object_id}")
        seen_ids.add(object_id)
        metadata = metadata_map(node)
        assignment = int(metadata["extruder"]) if metadata.get("extruder", "").isdigit() else None
        name = metadata.get("name", f"object_{object_id}")
        tokens = sorted(set(re.findall(r"[a-z0-9]+", Path(name).stem.lower())))
        object_warnings = []
        if assignment is not None and assignment not in material_by_slot:
            object_warnings.append(
                f"material assignment {assignment} does not resolve to a configured slot"
            )
        objects.append({
            "object_id": object_id,
            "name": name,
            "plate_id": None,
            "plate_name": None,
            "source_model_member": None,
            "part_count": sum(1 for child in node if local_name(child.tag) == "part"),
            "material_assignment": assignment,
            "resolved_material": material_by_slot.get(assignment),
            "physical_nozzle_assignment": None,
            "recommended_tool_class": None,
            "semantic_name_tokens": tokens,
            "geometry": None,
            "warnings": object_warnings,
        })
    plates: list[dict[str, Any]] = []
    for index, node in enumerate((child for child in root if local_name(child.tag) == "plate"), start=1):
        metadata = metadata_map(node)
        plate_id = int(metadata.get("index", index))
        object_ids = sorted(
            int(item.attrib["value"])
            for instance in node.iter()
            for item in instance
            if local_name(item.tag) == "metadata" and item.attrib.get("key") == "object_id"
        )
        plates.append({"plate_id": plate_id, "name": metadata.get("name"), "object_ids": object_ids})
    plate_by_object = {
        object_id: plate
        for plate in plates
        for object_id in plate["object_ids"]
    }
    for item in objects:
        plate = plate_by_object.get(item["object_id"])
        if plate:
            item["plate_id"] = plate["plate_id"]
            item["plate_name"] = plate["name"]
    return sorted(objects, key=lambda item: (item["object_id"], item["name"])), sorted(plates, key=lambda item: (item["plate_id"], item["name"] or "")), []
```

Wire these helpers into `observe_3mf()` before returning its report. Merge root metadata and project settings without guessed defaults:

```python
root_data = archive.read(ROOT_MODEL)
root_project, root_warnings = parse_root_metadata(root_data)
settings_project, physical_tools, materials, project_warnings = parse_project_settings(
    read_json_member(archive, PROJECT_SETTINGS)
)
project = {**root_project, **settings_project}
objects, plates, model_warnings = parse_model_settings(
    archive.read(MODEL_SETTINGS), materials
)
warnings = sorted(root_warnings + project_warnings + model_warnings)
```

- [ ] **Step 4: Run the focused tests and verify metadata joins pass**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: metadata tests pass; geometry assertions have not been added yet.

- [ ] **Step 5: Commit the metadata observer**

```powershell
git add tools/amp_observe_3mf.py tests/tools/test_amp_observe_3mf.py
git commit -m "tools: observe 3MF project metadata"
```

### Task 3: Stream object-model geometry summaries

**Files:**
- Modify: `tools/amp_observe_3mf.py`
- Modify: `tests/tools/test_amp_observe_3mf.py`

- [ ] **Step 1: Add failing geometry and streaming-path tests**

Add assertions to the synthetic contract test:

```python
geometry = report["objects"][0]["geometry"]
self.assertEqual(geometry["vertex_count"], 3)
self.assertEqual(geometry["triangle_count"], 1)
self.assertEqual(geometry["bounds"]["min"], [0.0, 0.0, 0.0])
self.assertEqual(geometry["bounds"]["max"], [10.0, 5.0, 2.0])
self.assertEqual(geometry["dimensions"], [10.0, 5.0, 2.0])
self.assertTrue(geometry["streamed"])
```

Add a missing-object-member test by changing the root component path to `/3D/Objects/missing.model` and asserting the error contains `missing referenced object-model member`.

- [ ] **Step 2: Run the focused tests and verify geometry is absent**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: geometry assertions fail because the object member is not resolved or streamed.

- [ ] **Step 3: Implement root-model reference mapping and streaming summaries**

Add:

```python
def parse_root_object_paths(data: bytes) -> dict[int, str]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ObservationError(f"invalid {ROOT_MODEL}: {exc}") from exc
    result: dict[int, str] = {}
    for obj in root.iter():
        if local_name(obj.tag) != "object" or "id" not in obj.attrib:
            continue
        object_id = int(obj.attrib["id"])
        paths = {
            component.attrib["path"].lstrip("/")
            for component in obj.iter()
            if local_name(component.tag) == "component" and component.attrib.get("path")
        }
        if len(paths) == 1:
            result[object_id] = next(iter(paths))
        elif len(paths) > 1:
            raise ObservationError(f"object {object_id} references multiple model members")
    return result


def stream_geometry(handle: BinaryIO, member_name: str) -> dict[str, Any]:
    vertex_count = 0
    triangle_count = 0
    minimum = [float("inf"), float("inf"), float("inf")]
    maximum = [float("-inf"), float("-inf"), float("-inf")]
    try:
        for _, element in ET.iterparse(handle, events=("end",)):
            name = local_name(element.tag)
            if name == "vertex":
                values = [float(element.attrib[key]) for key in ("x", "y", "z")]
                vertex_count += 1
                minimum = [min(current, value) for current, value in zip(minimum, values)]
                maximum = [max(current, value) for current, value in zip(maximum, values)]
            elif name == "triangle":
                triangle_count += 1
            element.clear()
    except (ET.ParseError, KeyError, ValueError) as exc:
        raise ObservationError(f"invalid object-model member {member_name}: {exc}") from exc
    if vertex_count == 0:
        bounds = None
        dimensions = None
    else:
        bounds = {"min": minimum, "max": maximum}
        dimensions = [high - low for low, high in zip(minimum, maximum)]
    return {
        "vertex_count": vertex_count,
        "triangle_count": triangle_count,
        "bounds": bounds,
        "dimensions": dimensions,
        "streamed": True,
    }
```

In `observe_3mf()`, parse `ROOT_MODEL`, assign each object's `source_model_member`, validate membership against `archive.namelist()`, and call:

```python
with archive.open(member_name, "r") as handle:
    item["geometry"] = stream_geometry(handle, member_name)
```

Do not use `archive.read(member_name)` for object-model members.

- [ ] **Step 4: Run the focused tests and verify streaming geometry passes**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: all geometry, missing-member, and earlier tests pass.

- [ ] **Step 5: Commit streaming geometry observation**

```powershell
git add tools/amp_observe_3mf.py tests/tools/test_amp_observe_3mf.py
git commit -m "tools: stream 3MF geometry summaries"
```

### Task 4: Add deterministic JSON/Markdown output and atomic CLI writing

**Files:**
- Modify: `tools/amp_observe_3mf.py`
- Modify: `tests/tools/test_amp_observe_3mf.py`

- [ ] **Step 1: Add failing determinism, escaping, CLI, and atomic-output tests**

Import `serialize_json`, `serialize_markdown`, and `write_reports` in the test module. Add:

```python
def test_serialization_is_deterministic_and_contains_no_absolute_path(self) -> None:
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

def test_writes_json_and_markdown_atomically(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "synthetic.3mf"
        json_path = root / "report.json"
        markdown_path = root / "report.md"
        write_synthetic_3mf(source)
        report = observe_3mf(source)
        write_reports(report, json_path=json_path, markdown_path=markdown_path)
        self.assertEqual(json_path.read_text(encoding="utf-8"), serialize_json(report))
        self.assertEqual(markdown_path.read_text(encoding="utf-8"), serialize_markdown(report))
        self.assertFalse(list(root.glob(".*.tmp")))

def test_failure_does_not_replace_existing_report(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        json_path = root / "report.json"
        json_path.write_text("existing\n", encoding="utf-8")
        with self.assertRaises(ObservationError):
            write_reports({"not": "a report"}, json_path=json_path, markdown_path=None)
        self.assertEqual(json_path.read_text(encoding="utf-8"), "existing\n")
```

- [ ] **Step 2: Run the focused tests and verify serializer imports fail**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: import error for the three missing output functions.

- [ ] **Step 3: Implement stable serializers, atomic writing, and CLI**

Add:

```python
def validate_report(report: dict[str, Any]) -> None:
    required = {"schema_version", "source", "project", "physical_tools", "materials", "plates", "objects", "warnings"}
    missing = sorted(required - set(report))
    if missing:
        raise ObservationError("invalid observation report; missing: " + ", ".join(missing))


def serialize_json(report: dict[str, Any]) -> str:
    validate_report(report)
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def serialize_markdown(report: dict[str, Any]) -> str:
    validate_report(report)
    source = report["source"]
    lines = [
        "# AMP 3MF Observation",
        "",
        f"- Source: `{source['file_name']}`",
        f"- SHA-256: `{source['sha256']}`",
        f"- ZIP members: {source['member_count']}",
        f"- Plates: {len(report['plates'])}",
        f"- Objects: {len(report['objects'])}",
        f"- Configured nozzle vector: `{','.join(report['physical_tools']['nozzle_diameters'])}`",
        "",
        "## Objects",
        "",
        "| ID | Name | Plate | Material slot | Vertices | Triangles |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in report["objects"]:
        geometry = item["geometry"] or {}
        escaped_name = item["name"].replace("|", "\\|")
        lines.append(
            f"| {item['object_id']} | {escaped_name} | "
            f"{item['plate_id'] or ''} | {item['material_assignment'] or ''} | "
            f"{geometry.get('vertex_count', '')} | {geometry.get('triangle_count', '')} |"
        )
    lines.extend(["", "Material/color assignments are not physical nozzle assignments or AMP recommendations.", ""])
    return "\n".join(lines)


def atomic_write(path: Path, content: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return path


def write_reports(report: dict[str, Any], *, json_path: Path | None, markdown_path: Path | None) -> None:
    json_content = serialize_json(report) if json_path is not None else None
    markdown_content = serialize_markdown(report) if markdown_path is not None else None
    if json_path is not None and json_content is not None:
        atomic_write(json_path, json_content)
    if markdown_path is not None and markdown_content is not None:
        atomic_write(markdown_path, markdown_content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--3mf", required=True, type=Path, dest="source")
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args(argv)
    try:
        report = observe_3mf(args.source)
        if args.out_json is None and args.out_md is None:
            sys.stdout.write(serialize_json(report))
        else:
            write_reports(report, json_path=args.out_json, markdown_path=args.out_md)
    except ObservationError as exc:
        print(f"AMP 3MF observation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests and a synthetic CLI smoke test**

Run:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
python tools\amp_observe_3mf.py --help
```

Expected: all tests pass; help lists `--3mf`, `--out-json`, and `--out-md`.

- [ ] **Step 5: Commit deterministic report output**

```powershell
git add tools/amp_observe_3mf.py tests/tools/test_amp_observe_3mf.py
git commit -m "tools: serialize deterministic 3MF observations"
```

### Task 5: Verify Floating Island and publish the observation report

**Files:**
- Create: `docs/benchmarks/AMP_Floating_Island_3MF_Observation_001.md`
- Modify: `tools/amp_observe_3mf.py` only for verified format compatibility defects
- Modify: `tests/tools/test_amp_observe_3mf.py` whenever the observer is corrected

- [ ] **Step 1: Run the real observer twice into ignored B-drive outputs**

Run:

```powershell
$source = 'C:\Users\d\Downloads\Floating+Island.3mf'
$out = 'B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_floating_island_observation'
New-Item -ItemType Directory -Force -Path $out | Out-Null
python tools\amp_observe_3mf.py --3mf $source --out-json "$out\observation-1.json" --out-md "$out\observation-1.md"
python tools\amp_observe_3mf.py --3mf $source --out-json "$out\observation-2.json" --out-md "$out\observation-2.md"
```

Expected: both commands exit `0`; no expanded 3MF directory is created.

- [ ] **Step 2: Verify the real-project contract and deterministic hashes**

Run:

```powershell
$out = 'B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_floating_island_observation'
$first = Get-FileHash "$out\observation-1.json" -Algorithm SHA256
$second = Get-FileHash "$out\observation-2.json" -Algorithm SHA256
if ($first.Hash -ne $second.Hash) { throw 'observation JSON is not deterministic' }
@'
import json
from pathlib import Path
p = json.loads(Path(r"B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_floating_island_observation\observation-1.json").read_text(encoding="utf-8"))
assert p["source"]["sha256"] == "8399e4ff4e428969d092844ddac6c6fd8c063b062fcbfedc7c02f3099d600e17"
assert p["source"]["member_count"] == 78
assert len(p["plates"]) == 8
assert len(p["objects"]) == 27
assert p["physical_tools"]["nozzle_diameters"] == ["0.4", "0.4"]
assert {item["material_assignment"] for item in p["objects"]} == {1, 2, 3, 4, 5, 6}
assert all(item["physical_nozzle_assignment"] is None for item in p["objects"])
assert all(item["recommended_tool_class"] is None for item in p["objects"])
print("Floating Island observation contract: PASS")
'@ | python -
```

Expected: matching report hashes and `Floating Island observation contract: PASS`.

- [ ] **Step 3: Correct only observed compatibility defects with a failing regression test first**

If the real package differs from the synthetic namespace/path/plate shape, first add the smallest synthetic reproduction to `tests/tools/test_amp_observe_3mf.py`, run it to observe failure, then update the parser. Do not special-case `Floating+Island.3mf`, its hash, its object names, or its Bambu application version.

Run after each correction:

```powershell
python -m unittest tests.tools.test_amp_observe_3mf -v
```

Expected: the new regression test and all previous tests pass.

- [ ] **Step 4: Create the committed integration report**

Create `docs/benchmarks/AMP_Floating_Island_3MF_Observation_001.md` with these sections and measured values from `observation-1.json`:

```markdown
# AMP Floating Island 3MF Observation 001

## Purpose

Verify the read-only streaming AMP 3MF observer on a detailed multi-plate, multi-material project without redistributing or modifying the source model.

## Source And Method

Record source SHA-256, compressed size, declared uncompressed member bytes, observer command, output report SHA-256, and confirmation that no archive extraction occurred.

## Observation Result

Record plate, object, material-slot, nozzle-vector, vertex, triangle, warning, and deterministic-repeat totals.

## Assignment Separation

Confirm material assignments 1 through 6 remain material/color metadata, while physical nozzle assignment and recommended AMP tool class remain null for every object.

## Limits

- This is read-only representation observation.
- No geometry scoring or manufacturing-region split was performed.
- No nozzle or tool class was recommended.
- No 3MF was modified.
- No G-code was generated.
- No physical U1 or mixed-nozzle behavior was validated.
- The source model is not committed or redistributed.
```

- [ ] **Step 5: Run complete verification and scope scans**

Run:

```powershell
python -m unittest discover -s tests\tools -p "test_amp*.py" -v
rg -n "amp_observe_3mf|physical_nozzle_assignment|recommended_tool_class" tools\amp_observe_3mf.py tests\tools\test_amp_observe_3mf.py docs\benchmarks\AMP_Floating_Island_3MF_Observation_001.md
rg -n "extractall|\.extract\(" tools\amp_observe_3mf.py
rg -n "zero-risk|Zero Risk|mathematically optimized|already partition|already partitions|partitions meshes|mixed-nozzle works|bypass safety|reverse-engineered|100% deterministic|factory-tested|85%--125%|85%-125%|true CMYK|accurate color reproduction|working CMYK|working FullSpectrum|ready to print" README.md docs tools
git diff --check
git status --short
```

Expected:

- all focused AMP tool tests pass;
- observer references remain limited to the new tool, test, and report;
- no `extract()` or `extractall()` call exists in the observer;
- overclaim scan has no newly introduced hits;
- no generated 3MF, JSON, Markdown, mesh, G-code, binary, or source model is staged.

- [ ] **Step 6: Commit the verified observer milestone**

```powershell
git add tools/amp_observe_3mf.py tests/tools/test_amp_observe_3mf.py docs/benchmarks/AMP_Floating_Island_3MF_Observation_001.md
git diff --cached --check
git diff --cached --name-only
git commit -m "tools: add streaming AMP 3MF observer"
git push public u1-adaptive-nozzle-strategy
```

Expected staged files are exactly the observer, its focused tests, and the integration report. Existing unrelated untracked CLI logs and scratch files remain untouched.
