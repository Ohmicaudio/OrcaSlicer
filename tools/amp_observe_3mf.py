#!/usr/bin/env python3
"""Read-only streaming inventory for Orca/Bambu-style 3MF projects."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO


ROOT_MODEL = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
REQUIRED_MEMBERS = {ROOT_MODEL, MODEL_SETTINGS, PROJECT_SETTINGS}
SCHEMA_VERSION = "0.1"
CORE_NAMESPACE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PRODUCTION_NAMESPACE = (
    "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
)
CORE_OBJECT = f"{{{CORE_NAMESPACE}}}object"
CORE_COMPONENT = f"{{{CORE_NAMESPACE}}}component"
CORE_MESH = f"{{{CORE_NAMESPACE}}}mesh"
CORE_VERTICES = f"{{{CORE_NAMESPACE}}}vertices"
CORE_VERTEX = f"{{{CORE_NAMESPACE}}}vertex"
CORE_TRIANGLES = f"{{{CORE_NAMESPACE}}}triangles"
CORE_TRIANGLE = f"{{{CORE_NAMESPACE}}}triangle"
PRODUCTION_PATH = f"{{{PRODUCTION_NAMESPACE}}}path"
ASCII_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
ASCII_PCHAR = ASCII_UNRESERVED | frozenset("!$&'()*+,;=:@")
ASCII_ORDINAL_LOWER = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"
)


class ObservationError(ValueError):
    """Raised when a 3MF cannot produce a trustworthy observation report."""


@dataclass(frozen=True)
class ObjectModelReference:
    member_name: str
    canonical_key: str
    object_id: int
    transform: tuple[float, ...] | None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_member_counts(
    infos: list[zipfile.ZipInfo], required_members: set[str]
) -> None:
    counts = Counter(item.filename for item in infos)
    missing = sorted(name for name in required_members if counts[name] == 0)
    if missing:
        raise ObservationError("missing required member(s): " + ", ".join(missing))
    duplicates = sorted(name for name in required_members if counts[name] > 1)
    if duplicates:
        raise ObservationError(
            "duplicate required member(s): " + ", ".join(duplicates)
        )


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


def parse_required_int(
    value: str | None, context: str, *, minimum: int, domain: str
) -> int:
    if value is None:
        raise ObservationError(f"missing {context}")
    try:
        parsed = int(value.strip())
    except ValueError as exc:
        raise ObservationError(f"invalid {context}: {value!r}") from exc
    if parsed < minimum:
        raise ObservationError(f"{context} must be {domain}: {parsed}")
    return parsed


def read_list_setting(
    payload: dict[str, Any], key: str, warnings: list[str]
) -> list[Any]:
    values = payload.get(key, [])
    if not isinstance(values, list):
        warnings.append(f"project {key} is not a list")
        return []
    return values


def json_value_kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "list"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def validate_nullable_string_entries(
    values: list[Any], key: str, warnings: list[str]
) -> list[str | None]:
    validated: list[str | None] = []
    for slot, value in enumerate(values, start=1):
        if value is None or isinstance(value, str):
            validated.append(value)
            continue
        warnings.append(
            f"project {key} slot {slot} must be a string or null; "
            f"got {json_value_kind(value)}"
        )
        validated.append(None)
    return validated


def validate_nozzle_entries(
    values: list[Any], warnings: list[str]
) -> list[str | None]:
    validated: list[str | None] = []
    for slot, value in enumerate(values, start=1):
        is_numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        reason = None
        if not isinstance(value, str) and not is_numeric:
            reason = json_value_kind(value)
        else:
            candidate = value.strip() if isinstance(value, str) else str(value)
            try:
                diameter = Decimal(candidate)
            except InvalidOperation:
                reason = "nonnumeric string"
            else:
                if not diameter.is_finite():
                    reason = "non-finite value"
                elif diameter <= 0:
                    reason = "nonpositive value"
        if reason is None:
            validated.append(str(value))
            continue
        warnings.append(
            f"project nozzle_diameter slot {slot} must be a positive finite "
            f"numeric diameter; got {reason}"
        )
        validated.append(None)
    return validated


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


def parse_finite_float(value: str | None, context: str) -> float:
    if value is None:
        raise ObservationError(f"missing {context}")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ObservationError(f"invalid {context}: {value!r}") from exc
    if not math.isfinite(parsed):
        raise ObservationError(f"non-finite {context}: {value!r}")
    return parsed


def parse_component_transform(
    value: str | None, context: str
) -> tuple[float, ...] | None:
    if value is None:
        return None
    parts = value.split()
    if len(parts) != 12:
        raise ObservationError(
            f"invalid {context}: expected 12 values, got {len(parts)}"
        )
    return tuple(
        parse_finite_float(part, f"{context} value {index}")
        for index, part in enumerate(parts, start=1)
    )


def ascii_case_insensitive_key(value: str) -> str:
    return value.translate(ASCII_ORDINAL_LOWER)


def is_normalized_uri_path_segment(value: str) -> bool:
    if not value or set(value) == {"."} or value.endswith("."):
        return False
    index = 0
    while index < len(value):
        character = value[index]
        if character != "%":
            if character not in ASCII_PCHAR:
                return False
            index += 1
            continue
        if index + 2 >= len(value) or not re.fullmatch(
            r"[0-9A-Fa-f]{2}", value[index + 1 : index + 3]
        ):
            return False
        decoded = chr(int(value[index + 1 : index + 3], 16))
        if decoded in ASCII_UNRESERVED or decoded in "/\\":
            return False
        index += 3
    return True


def canonical_object_model_name(
    value: str, context: str, *, reference: bool
) -> tuple[str, str]:
    invalid = (
        not value
        or "\\" in value
        or "?" in value
        or "#" in value
        or (reference and (not value.startswith("/") or value.startswith("//")))
        or (not reference and value.startswith("/"))
    )
    member_name = value[1:] if reference and value.startswith("/") else value
    segments = member_name.split("/")
    invalid = invalid or any(
        not is_normalized_uri_path_segment(segment) for segment in segments
    )
    invalid = invalid or len(segments) < 3
    if not invalid:
        invalid = (
            ascii_case_insensitive_key(segments[0]) != "3d"
            or ascii_case_insensitive_key(segments[1]) != "objects"
        )
    if invalid:
        raise ObservationError(f"invalid {context}: {value!r}")
    return member_name, ascii_case_insensitive_key(member_name)


def looks_like_object_model_member(name: str) -> bool:
    segments = [
        segment
        for segment in re.split(r"[/\\]+", name.lstrip("/"))
        if segment
    ]
    return (
        len(segments) >= 2
        and ascii_case_insensitive_key(segments[0]) == "3d"
        and ascii_case_insensitive_key(segments[1]) == "objects"
    )


def object_model_member_lookup(
    infos: list[zipfile.ZipInfo],
) -> dict[str, list[zipfile.ZipInfo]]:
    result: dict[str, list[zipfile.ZipInfo]] = {}
    for info in infos:
        if not looks_like_object_model_member(info.filename):
            continue
        _, canonical_key = canonical_object_model_name(
            info.filename, "object-model ZIP member name", reference=False
        )
        result.setdefault(canonical_key, []).append(info)
    return result


def parse_root_object_references(
    data: bytes,
) -> dict[int, tuple[ObjectModelReference, ...]]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ObservationError(f"invalid {ROOT_MODEL}: {exc}") from exc
    result: dict[int, tuple[ObjectModelReference, ...]] = {}
    seen_ids: set[int] = set()
    for obj in root.iter():
        if obj.tag != CORE_OBJECT:
            continue
        object_id = parse_required_int(
            obj.attrib.get("id"),
            "root object id",
            minimum=1,
            domain="positive",
        )
        if object_id in seen_ids:
            raise ObservationError(f"duplicate root object id: {object_id}")
        seen_ids.add(object_id)
        references: list[ObjectModelReference] = []
        for component in obj.iter():
            if component.tag != CORE_COMPONENT:
                continue
            qualified_path = component.attrib.get(PRODUCTION_PATH)
            fallback_path = component.attrib.get("path")
            if (
                qualified_path is not None
                and fallback_path is not None
                and qualified_path != fallback_path
            ):
                raise ObservationError(
                    "conflicting qualified and unqualified paths for "
                    f"object {object_id}"
                )
            raw_path = (
                qualified_path if qualified_path is not None else fallback_path
            )
            if raw_path is None:
                continue
            member_name, canonical_key = canonical_object_model_name(
                raw_path,
                f"referenced object-model path for object {object_id}",
                reference=True,
            )
            referenced_object_id = parse_required_int(
                component.attrib.get("objectid"),
                f"root object {object_id} component objectid",
                minimum=1,
                domain="positive",
            )
            transform = parse_component_transform(
                component.attrib.get("transform"),
                f"root object {object_id} component transform",
            )
            references.append(
                ObjectModelReference(
                    member_name=member_name,
                    canonical_key=canonical_key,
                    object_id=referenced_object_id,
                    transform=transform,
                )
            )
        canonical_keys = {reference.canonical_key for reference in references}
        if len(canonical_keys) > 1:
            raise ObservationError(
                f"object {object_id} references multiple model members"
            )
        if references:
            result[object_id] = tuple(references)
    return result


def transform_vertex(
    values: tuple[float, float, float],
    reference: ObjectModelReference,
    member_name: str,
) -> list[float]:
    if reference.transform is None:
        return list(values)
    x, y, z = values
    matrix = reference.transform
    transformed = [
        x * matrix[0] + y * matrix[3] + z * matrix[6] + matrix[9],
        x * matrix[1] + y * matrix[4] + z * matrix[7] + matrix[10],
        x * matrix[2] + y * matrix[5] + z * matrix[8] + matrix[11],
    ]
    if not all(math.isfinite(value) for value in transformed):
        raise ObservationError(
            "non-finite transformed coordinate for object-model member "
            f"{member_name} object {reference.object_id}"
        )
    return transformed


def stream_geometry(
    handle: BinaryIO,
    member_name: str,
    references: tuple[ObjectModelReference, ...],
) -> dict[str, Any]:
    vertex_count = 0
    triangle_count = 0
    minimum = [float("inf"), float("inf"), float("inf")]
    maximum = [float("-inf"), float("-inf"), float("-inf")]
    references_by_object: dict[int, list[ObjectModelReference]] = {}
    for reference in references:
        references_by_object.setdefault(reference.object_id, []).append(reference)
    element_stack: list[ET.Element] = []
    object_ids_by_element: dict[int, int] = {}
    mesh_vertex_counts: dict[int, int] = {}
    seen_object_ids: set[int] = set()
    found_object_ids: set[int] = set()
    try:
        for event, element in ET.iterparse(handle, events=("start", "end")):
            if event == "start":
                element_stack.append(element)
                if element.tag == CORE_OBJECT:
                    object_id = parse_required_int(
                        element.attrib.get("id"),
                        f"object-model member {member_name} object id",
                        minimum=1,
                        domain="positive",
                    )
                    if object_id in seen_object_ids:
                        raise ObservationError(
                            f"duplicate object id {object_id} in object-model "
                            f"member {member_name}"
                        )
                    seen_object_ids.add(object_id)
                    object_ids_by_element[id(element)] = object_id
                    if object_id in references_by_object:
                        found_object_ids.add(object_id)
                elif element.tag == CORE_MESH:
                    mesh_vertex_counts[id(element)] = 0
                continue

            is_vertex = (
                element.tag == CORE_VERTEX
                and len(element_stack) >= 4
                and element_stack[-2].tag == CORE_VERTICES
                and element_stack[-3].tag == CORE_MESH
                and element_stack[-4].tag == CORE_OBJECT
            )
            is_triangle = (
                element.tag == CORE_TRIANGLE
                and len(element_stack) >= 4
                and element_stack[-2].tag == CORE_TRIANGLES
                and element_stack[-3].tag == CORE_MESH
                and element_stack[-4].tag == CORE_OBJECT
            )
            if is_vertex or is_triangle:
                object_id = object_ids_by_element[id(element_stack[-4])]
                object_references = references_by_object.get(object_id, [])
                mesh_id = id(element_stack[-3])
                if is_vertex:
                    mesh_vertex_counts[mesh_id] += 1
                    if object_references:
                        coordinates = tuple(
                            parse_finite_float(
                                element.attrib.get(axis),
                                f"object-model member {member_name} object "
                                f"{object_id} vertex {axis} coordinate",
                            )
                            for axis in ("x", "y", "z")
                        )
                        for reference in object_references:
                            values = transform_vertex(
                                coordinates, reference, member_name
                            )
                            minimum = [
                                min(current, value)
                                for current, value in zip(minimum, values)
                            ]
                            maximum = [
                                max(current, value)
                                for current, value in zip(maximum, values)
                            ]
                        vertex_count += len(object_references)
                elif object_references:
                    mesh_vertex_count = mesh_vertex_counts[mesh_id]
                    for attribute in ("v1", "v2", "v3"):
                        context = (
                            f"object-model member {member_name} object {object_id} "
                            f"mesh triangle {attribute} index"
                        )
                        vertex_index = parse_required_int(
                            element.attrib.get(attribute),
                            context,
                            minimum=0,
                            domain="nonnegative",
                        )
                        if vertex_index >= mesh_vertex_count:
                            raise ObservationError(
                                f"{context} {vertex_index} out of range for "
                                f"{mesh_vertex_count} vertices"
                            )
                    triangle_count += len(object_references)

            if element.tag == CORE_OBJECT:
                object_ids_by_element.pop(id(element), None)
            elif element.tag == CORE_MESH:
                mesh_vertex_counts.pop(id(element), None)
            element_stack.pop()
            if element_stack:
                element_stack[-1].remove(element)
            element.clear()
    except ET.ParseError as exc:
        raise ObservationError(
            f"invalid object-model member {member_name}: {exc}"
        ) from exc
    missing_object_ids = sorted(set(references_by_object) - found_object_ids)
    if missing_object_ids:
        missing = ", ".join(str(object_id) for object_id in missing_object_ids)
        label = "id" if len(missing_object_ids) == 1 else "ids"
        raise ObservationError(
            f"missing referenced object {label} {missing} in object-model "
            f"member {member_name}"
        )
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


def parse_project_settings(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    nozzles = read_list_setting(payload, "nozzle_diameter", warnings)
    if not nozzles and isinstance(payload.get("nozzle_diameter", []), list):
        warnings.append("project nozzle_diameter is empty")
    profiles = read_list_setting(payload, "filament_settings_id", warnings)
    colors = read_list_setting(payload, "filament_colour", warnings)
    if len(profiles) != len(colors):
        warnings.append(
            "project material profile/color length mismatch: "
            f"{len(profiles)} profiles, {len(colors)} colors"
        )
    nozzle_diameters = validate_nozzle_entries(nozzles, warnings)
    profiles = validate_nullable_string_entries(
        profiles, "filament_settings_id", warnings
    )
    colors = validate_nullable_string_entries(colors, "filament_colour", warnings)
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
        "nozzle_diameters": nozzle_diameters,
        "source_member": PROJECT_SETTINGS,
    }
    return project, physical_tools, materials, warnings


def parse_model_settings(
    data: bytes, materials: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
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
        object_id = parse_required_int(
            node.attrib.get("id"), "object id", minimum=1, domain="positive"
        )
        if object_id in seen_ids:
            raise ObservationError(f"duplicate object id: {object_id}")
        seen_ids.add(object_id)
        metadata = metadata_map(node)
        assignment = None
        if "extruder" in metadata:
            parsed_assignment = parse_required_int(
                metadata["extruder"],
                f"object {object_id} extruder",
                minimum=0,
                domain="nonnegative",
            )
            assignment = None if parsed_assignment == 0 else parsed_assignment
        name = metadata.get("name", f"object_{object_id}")
        tokens = sorted(set(re.findall(r"[a-z0-9]+", Path(name).stem.lower())))
        object_warnings = []
        if assignment is not None and assignment not in material_by_slot:
            object_warnings.append(
                f"material assignment {assignment} does not resolve to a configured slot"
            )
        objects.append(
            {
                "object_id": object_id,
                "name": name,
                "plate_id": None,
                "plate_name": None,
                "source_model_member": None,
                "part_count": sum(
                    1 for child in node if local_name(child.tag) == "part"
                ),
                "material_assignment": assignment,
                "resolved_material": material_by_slot.get(assignment),
                "physical_nozzle_assignment": None,
                "recommended_tool_class": None,
                "semantic_name_tokens": tokens,
                "geometry": None,
                "warnings": object_warnings,
            }
        )
    plates: list[dict[str, Any]] = []
    seen_plate_ids: set[int] = set()
    for node in (child for child in root if local_name(child.tag) == "plate"):
        metadata = metadata_map(node)
        plate_id_value = (
            metadata["plater_id"]
            if "plater_id" in metadata
            else metadata.get("index")
        )
        plate_id = parse_required_int(
            plate_id_value, "plate id", minimum=1, domain="positive"
        )
        if plate_id in seen_plate_ids:
            raise ObservationError(f"duplicate plate id: {plate_id}")
        seen_plate_ids.add(plate_id)
        object_ids = sorted(
            parse_required_int(
                item.attrib.get("value"),
                f"plate {plate_id} object id",
                minimum=1,
                domain="positive",
            )
            for item in node.iter()
            if local_name(item.tag) == "metadata"
            and item.attrib.get("key") == "object_id"
        )
        plate_name = (
            metadata["plater_name"]
            if "plater_name" in metadata
            else metadata.get("name")
        )
        plates.append(
            {
                "plate_id": plate_id,
                "name": plate_name,
                "object_ids": object_ids,
            }
        )
    object_by_id = {item["object_id"]: item for item in objects}
    plate_by_object: dict[int, dict[str, Any]] = {}
    for plate in plates:
        for object_id in plate["object_ids"]:
            if object_id not in object_by_id:
                raise ObservationError(
                    f"plate {plate['plate_id']} references unknown object id: {object_id}"
                )
            previous = plate_by_object.get(object_id)
            if previous is not None and previous["plate_id"] != plate["plate_id"]:
                plate_ids = sorted((previous["plate_id"], plate["plate_id"]))
                raise ObservationError(
                    f"ambiguous plate membership for object id {object_id}: "
                    f"{plate_ids[0]}, {plate_ids[1]}"
                )
            plate_by_object[object_id] = plate
    for item in objects:
        plate = plate_by_object.get(item["object_id"])
        if plate:
            item["plate_id"] = plate["plate_id"]
            item["plate_name"] = plate["name"]
    return (
        sorted(objects, key=lambda item: (item["object_id"], item["name"])),
        sorted(plates, key=lambda item: (item["plate_id"], item["name"] or "")),
        [],
    )


def observe_3mf(source: Path) -> dict[str, Any]:
    source = Path(source)
    try:
        with zipfile.ZipFile(source, "r") as archive:
            infos = archive.infolist()
            validate_member_counts(infos, REQUIRED_MEMBERS)
            root_data = archive.read(ROOT_MODEL)
            root_project, root_warnings = parse_root_metadata(root_data)
            root_object_references = parse_root_object_references(root_data)
            settings_project, physical_tools, materials, project_warnings = (
                parse_project_settings(read_json_member(archive, PROJECT_SETTINGS))
            )
            project = {**root_project, **settings_project}
            objects, plates, model_warnings = parse_model_settings(
                archive.read(MODEL_SETTINGS), materials
            )
            member_lookup = object_model_member_lookup(infos)
            for item in objects:
                references = root_object_references.get(item["object_id"])
                if references is None:
                    continue
                referenced_name = references[0].member_name
                entries = member_lookup.get(references[0].canonical_key, [])
                if not entries:
                    raise ObservationError(
                        "missing referenced object-model member: "
                        f"{referenced_name}"
                    )
                if len(entries) > 1:
                    entry_names = {entry.filename for entry in entries}
                    if len(entry_names) == 1:
                        raise ObservationError(
                            "duplicate referenced object-model member: "
                            f"{referenced_name}"
                        )
                    raise ObservationError(
                        "ambiguous canonical object-model member: "
                        + ", ".join(sorted(entry_names))
                    )
                member_info = entries[0]
                item["source_model_member"] = member_info.filename
                with archive.open(member_info, "r") as handle:
                    item["geometry"] = stream_geometry(
                        handle, member_info.filename, references
                    )
            warnings = sorted(root_warnings + project_warnings + model_warnings)
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
                "project": project,
                "physical_tools": physical_tools,
                "materials": materials,
                "plates": plates,
                "objects": objects,
                "warnings": warnings,
            }
    except (OSError, zipfile.BadZipFile) as exc:
        raise ObservationError(f"unreadable 3MF archive: {exc}") from exc
