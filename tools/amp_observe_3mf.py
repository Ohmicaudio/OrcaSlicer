#!/usr/bin/env python3
"""Read-only streaming inventory for Orca/Bambu-style 3MF projects."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import shutil
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


@dataclass
class StagedReportOutput:
    destination: Path
    content: str
    temp_path: Path | None = None
    backup_path: Path | None = None
    existed: bool = False
    replaced: bool = False


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


def optional_plate_member_inventory(
    infos: list[zipfile.ZipInfo],
) -> tuple[list[str], list[str]]:
    plate_members = []
    for info in infos:
        segments = info.filename.split("/")
        if (
            len(segments) < 2
            or ascii_case_insensitive_key(segments[0]) != "metadata"
            or not ascii_case_insensitive_key(segments[-1]).startswith("plate_")
        ):
            continue
        plate_members.append(info.filename)
    plate_members.sort(key=lambda name: (ascii_case_insensitive_key(name), name))
    thumbnail_extensions = {"png", "jpg", "jpeg", "webp"}
    plate_thumbnail_members = [
        name
        for name in plate_members
        if "." in name.rsplit("/", 1)[-1]
        and ascii_case_insensitive_key(name.rsplit(".", 1)[-1])
        in thumbnail_extensions
    ]
    return plate_members, plate_thumbnail_members


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
        if references:
            result[object_id] = tuple(
                sorted(
                    references,
                    key=lambda reference: (
                        reference.canonical_key,
                        reference.object_id,
                        reference.transform or (),
                    ),
                )
            )
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


def merge_geometry_summaries(
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    bounds = [summary["bounds"] for summary in summaries if summary["bounds"]]
    minimum = (
        [min(item["min"][axis] for item in bounds) for axis in range(3)]
        if bounds
        else None
    )
    maximum = (
        [max(item["max"][axis] for item in bounds) for axis in range(3)]
        if bounds
        else None
    )
    return {
        "vertex_count": sum(summary["vertex_count"] for summary in summaries),
        "triangle_count": sum(
            summary["triangle_count"] for summary in summaries
        ),
        "bounds": (
            {"min": minimum, "max": maximum}
            if minimum is not None and maximum is not None
            else None
        ),
        "dimensions": (
            [high - low for low, high in zip(minimum, maximum)]
            if minimum is not None and maximum is not None
            else None
        ),
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
        object_assignment = None
        if "extruder" in metadata:
            parsed_assignment = parse_required_int(
                metadata["extruder"],
                f"object {object_id} extruder",
                minimum=0,
                domain="nonnegative",
            )
            object_assignment = (
                None if parsed_assignment == 0 else parsed_assignment
            )
        part_assignments: list[dict[str, Any]] = []
        seen_part_ids: set[int] = set()
        for part in (child for child in node if local_name(child.tag) == "part"):
            part_id = parse_required_int(
                part.attrib.get("id"),
                f"object {object_id} part id",
                minimum=1,
                domain="positive",
            )
            if part_id in seen_part_ids:
                raise ObservationError(
                    f"duplicate part id {part_id} in object {object_id}"
                )
            seen_part_ids.add(part_id)
            part_metadata = metadata_map(part)
            explicit_assignment = None
            if "extruder" in part_metadata:
                parsed_assignment = parse_required_int(
                    part_metadata["extruder"],
                    f"object {object_id} part {part_id} extruder",
                    minimum=0,
                    domain="nonnegative",
                )
                if parsed_assignment > 0:
                    explicit_assignment = parsed_assignment
            effective_assignment = explicit_assignment or object_assignment
            part_assignments.append(
                {
                    "part_id": part_id,
                    "explicit_material_assignment": explicit_assignment,
                    "effective_material_assignment": effective_assignment,
                    "resolved_material": material_by_slot.get(
                        effective_assignment
                    ),
                }
            )
        part_assignments.sort(key=lambda item: item["part_id"])
        effective_slots = sorted(
            {
                item["effective_material_assignment"]
                for item in part_assignments
                if item["effective_material_assignment"] is not None
            }
        )
        has_unresolved_part_assignments = any(
            item["effective_material_assignment"] is None
            for item in part_assignments
        )
        assignment = object_assignment
        if part_assignments:
            assignment = (
                effective_slots[0]
                if len(effective_slots) == 1
                and not has_unresolved_part_assignments
                else None
            )
        name = metadata.get("name", f"object_{object_id}")
        tokens = sorted(set(re.findall(r"[a-z0-9]+", Path(name).stem.lower())))
        object_warnings = []
        if has_unresolved_part_assignments and effective_slots:
            object_warnings.append(
                "known effective part material assignments: "
                + ", ".join(str(slot) for slot in effective_slots)
                + "; unresolved part assignments are present"
            )
        elif len(effective_slots) > 1:
            object_warnings.append(
                "mixed effective part material assignments: "
                + ", ".join(str(slot) for slot in effective_slots)
            )
        unresolved_slots = (
            [slot for slot in effective_slots if slot not in material_by_slot]
            if part_assignments
            else (
                [assignment]
                if assignment is not None and assignment not in material_by_slot
                else []
            )
        )
        for slot in unresolved_slots:
            object_warnings.append(
                (
                    f"effective part material assignment {slot}"
                    if part_assignments
                    else f"material assignment {slot}"
                )
                + " does not resolve to a configured slot"
            )
        objects.append(
            {
                "object_id": object_id,
                "name": name,
                "plate_id": None,
                "plate_name": None,
                "plate_ids": [],
                "plate_names": [],
                "instances": [],
                "source_model_member": None,
                "source_model_members": [],
                "part_count": len(part_assignments),
                "part_assignments": part_assignments,
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
    explicit_instance_plates: dict[tuple[int, int], int] = {}
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
        plate_name = (
            metadata["plater_name"]
            if "plater_name" in metadata
            else metadata.get("name")
        )
        instances: list[dict[str, Any]] = []
        seen_instance_identities: set[tuple[int, int | None]] = set()
        for instance_node in (
            item for item in node.iter() if local_name(item.tag) == "model_instance"
        ):
            instance_metadata = metadata_map(instance_node)
            object_id_value = next(
                (
                    child.attrib.get("value")
                    for child in instance_node
                    if local_name(child.tag) == "metadata"
                    and child.attrib.get("key") == "object_id"
                ),
                None,
            )
            object_id = parse_required_int(
                object_id_value,
                f"plate {plate_id} object id",
                minimum=1,
                domain="positive",
            )
            instance_id = None
            if "instance_id" in instance_metadata:
                instance_id_value = next(
                    (
                        child.attrib.get("value")
                        for child in instance_node
                        if local_name(child.tag) == "metadata"
                        and child.attrib.get("key") == "instance_id"
                    ),
                    None,
                )
                instance_id = parse_required_int(
                    instance_id_value,
                    f"plate {plate_id} instance id",
                    minimum=0,
                    domain="nonnegative",
                )
            identity = (object_id, instance_id)
            if identity in seen_instance_identities:
                raise ObservationError(
                    "duplicate instance identity on plate "
                    f"{plate_id}: object {object_id}, instance "
                    f"{instance_id if instance_id is not None else 'null'}"
                )
            seen_instance_identities.add(identity)
            if instance_id is not None:
                explicit_identity = (object_id, instance_id)
                previous_plate_id = explicit_instance_plates.get(
                    explicit_identity
                )
                if previous_plate_id is not None:
                    first_plate_id, second_plate_id = sorted(
                        (previous_plate_id, plate_id)
                    )
                    raise ObservationError(
                        "duplicate explicit instance identity across plates: "
                        f"object {object_id}, instance {instance_id} on plates "
                        f"{first_plate_id} and {second_plate_id}"
                    )
                explicit_instance_plates[explicit_identity] = plate_id
            instances.append(
                {"object_id": object_id, "instance_id": instance_id}
            )
        instances.sort(
            key=lambda item: (
                item["object_id"],
                item["instance_id"] is None,
                item["instance_id"] if item["instance_id"] is not None else 0,
            )
        )
        plates.append(
            {
                "plate_id": plate_id,
                "name": plate_name,
                "object_ids": sorted(
                    {instance["object_id"] for instance in instances}
                ),
                "instances": instances,
            }
        )
    object_by_id = {item["object_id"]: item for item in objects}
    plates.sort(key=lambda item: (item["plate_id"], item["name"] or ""))
    for plate in plates:
        for instance in plate["instances"]:
            object_id = instance["object_id"]
            if object_id not in object_by_id:
                raise ObservationError(
                    f"plate {plate['plate_id']} references unknown object id: {object_id}"
                )
            object_by_id[object_id]["instances"].append(
                {
                    "plate_id": plate["plate_id"],
                    "plate_name": plate["name"],
                    "instance_id": instance["instance_id"],
                }
            )
    for item in objects:
        item["instances"].sort(
            key=lambda instance: (
                instance["plate_id"],
                instance["instance_id"] is None,
                (
                    instance["instance_id"]
                    if instance["instance_id"] is not None
                    else 0
                ),
                instance["plate_name"] or "",
            )
        )
        item["plate_ids"] = sorted(
            {instance["plate_id"] for instance in item["instances"]}
        )
        item["plate_names"] = sorted(
            {
                instance["plate_name"]
                for instance in item["instances"]
                if instance["plate_name"] is not None
            }
        )
        if len(item["plate_ids"]) == 1:
            item["plate_id"] = item["plate_ids"][0]
            item["plate_name"] = item["instances"][0]["plate_name"]
        elif len(item["plate_ids"]) > 1:
            item["warnings"].append(
                "object appears on multiple plates: "
                + ", ".join(str(plate_id) for plate_id in item["plate_ids"])
            )
    return (
        sorted(objects, key=lambda item: (item["object_id"], item["name"])),
        plates,
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
            plate_members, plate_thumbnail_members = (
                optional_plate_member_inventory(infos)
            )
            for item in objects:
                references = root_object_references.get(item["object_id"])
                if references is None:
                    continue
                references_by_member: dict[
                    str, list[ObjectModelReference]
                ] = {}
                for reference in references:
                    references_by_member.setdefault(
                        reference.canonical_key, []
                    ).append(reference)
                geometry_summaries = []
                for canonical_key in sorted(references_by_member):
                    member_references = tuple(
                        references_by_member[canonical_key]
                    )
                    referenced_name = member_references[0].member_name
                    entries = member_lookup.get(canonical_key, [])
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
                    item["source_model_members"].append(member_info.filename)
                    with archive.open(member_info, "r") as handle:
                        geometry_summaries.append(
                            stream_geometry(
                                handle,
                                member_info.filename,
                                member_references,
                            )
                        )
                if len(item["source_model_members"]) == 1:
                    item["source_model_member"] = item[
                        "source_model_members"
                    ][0]
                item["geometry"] = merge_geometry_summaries(
                    geometry_summaries
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
                    "plate_members": plate_members,
                    "plate_thumbnail_members": plate_thumbnail_members,
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


def invalid_report(context: str, message: str) -> None:
    raise ObservationError(f"invalid observation report; {context} {message}")


def require_mapping(
    value: Any, context: str, required: set[str]
) -> dict[str, Any]:
    if not isinstance(value, dict):
        invalid_report(context, "must be an object")
    missing = sorted(required - set(value))
    if missing:
        invalid_report(context, "missing: " + ", ".join(missing))
    return value


def require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        invalid_report(context, "must be a list")
    return value


def require_string(value: Any, context: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str):
        expected = "a string or null" if nullable else "a string"
        invalid_report(context, f"must be {expected}")


def require_integer(value: Any, context: str, *, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        invalid_report(context, "must be an integer")
    if value < minimum:
        invalid_report(context, f"must be at least {minimum}")


def require_string_list(value: Any, context: str) -> list[Any]:
    items = require_list(value, context)
    for index, item in enumerate(items):
        require_string(item, f"{context}[{index}]")
    return items


def validate_utf8_strings(value: Any, context: str) -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            invalid_report(context, "contains a lone surrogate")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                invalid_report(context, "contains a non-string key")
            validate_utf8_strings(key, f"{context} key")
            validate_utf8_strings(item, f"{context}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_utf8_strings(item, f"{context}[{index}]")


def validate_material(value: Any, context: str) -> None:
    material = require_mapping(value, context, {"slot", "profile", "color"})
    require_integer(material["slot"], f"{context}.slot", minimum=1)
    require_string(material["profile"], f"{context}.profile", nullable=True)
    require_string(material["color"], f"{context}.color", nullable=True)


def validate_part_assignment(value: Any, context: str) -> None:
    assignment = require_mapping(
        value,
        context,
        {
            "part_id",
            "explicit_material_assignment",
            "effective_material_assignment",
            "resolved_material",
        },
    )
    require_integer(assignment["part_id"], f"{context}.part_id", minimum=1)
    for field in (
        "explicit_material_assignment",
        "effective_material_assignment",
    ):
        if assignment[field] is not None:
            require_integer(assignment[field], f"{context}.{field}", minimum=1)
    if assignment["resolved_material"] is not None:
        validate_material(
            assignment["resolved_material"], f"{context}.resolved_material"
        )


def validate_number_vector(value: Any, context: str) -> None:
    items = require_list(value, context)
    if len(items) != 3:
        invalid_report(context, "must contain three numbers")
    for index, item in enumerate(items):
        try:
            finite = math.isfinite(item)
        except (OverflowError, TypeError):
            finite = False
        if (
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not finite
        ):
            invalid_report(f"{context}[{index}]", "must be a finite number")


def validate_geometry(value: Any, context: str) -> None:
    geometry = require_mapping(
        value,
        context,
        {"vertex_count", "triangle_count", "bounds", "dimensions", "streamed"},
    )
    require_integer(geometry["vertex_count"], f"{context}.vertex_count")
    require_integer(geometry["triangle_count"], f"{context}.triangle_count")
    bounds = geometry["bounds"]
    if bounds is not None:
        bounds = require_mapping(bounds, f"{context}.bounds", {"min", "max"})
        validate_number_vector(bounds["min"], f"{context}.bounds.min")
        validate_number_vector(bounds["max"], f"{context}.bounds.max")
    dimensions = geometry["dimensions"]
    if dimensions is not None:
        validate_number_vector(dimensions, f"{context}.dimensions")
    if not isinstance(geometry["streamed"], bool):
        invalid_report(f"{context}.streamed", "must be a boolean")


def validate_warning_list(value: Any, context: str) -> None:
    require_string_list(value, context)


def validate_report(report: dict[str, Any]) -> None:
    validate_utf8_strings(report, "report")
    report = require_mapping(
        report,
        "report",
        {
            "schema_version",
            "source",
            "project",
            "physical_tools",
            "materials",
            "plates",
            "objects",
            "warnings",
        },
    )
    require_string(report["schema_version"], "schema_version")

    source = require_mapping(
        report["source"],
        "source",
        {
            "file_name",
            "sha256",
            "compressed_size",
            "member_count",
            "uncompressed_member_bytes",
            "required_members",
            "plate_members",
            "plate_thumbnail_members",
        },
    )
    require_string(source["file_name"], "source.file_name")
    require_string(source["sha256"], "source.sha256")
    for field in ("compressed_size", "member_count", "uncompressed_member_bytes"):
        require_integer(source[field], f"source.{field}")
    require_string_list(source["required_members"], "source.required_members")
    require_string_list(source["plate_members"], "source.plate_members")
    require_string_list(
        source["plate_thumbnail_members"], "source.plate_thumbnail_members"
    )

    project = require_mapping(
        report["project"],
        "project",
        {
            "title",
            "designer",
            "license",
            "source_application",
            "printer_preset",
            "process_preset",
            "layer_height",
            "wall_generator",
        },
    )
    for key, value in project.items():
        require_string(value, f"project.{key}", nullable=True)

    physical_tools = require_mapping(
        report["physical_tools"],
        "physical_tools",
        {"nozzle_diameters", "source_member"},
    )
    nozzles = require_list(
        physical_tools["nozzle_diameters"], "physical_tools.nozzle_diameters"
    )
    for index, nozzle in enumerate(nozzles):
        require_string(
            nozzle,
            f"physical_tools.nozzle_diameters[{index}]",
            nullable=True,
        )
    require_string(physical_tools["source_member"], "physical_tools.source_member")

    materials = require_list(report["materials"], "materials")
    for index, material in enumerate(materials):
        validate_material(material, f"materials[{index}]")

    plates = require_list(report["plates"], "plates")
    for index, value in enumerate(plates):
        context = f"plates[{index}]"
        plate = require_mapping(
            value, context, {"plate_id", "name", "object_ids", "instances"}
        )
        require_integer(plate["plate_id"], f"{context}.plate_id", minimum=1)
        require_string(plate["name"], f"{context}.name", nullable=True)
        object_ids = require_list(plate["object_ids"], f"{context}.object_ids")
        for object_index, object_id in enumerate(object_ids):
            require_integer(
                object_id,
                f"{context}.object_ids[{object_index}]",
                minimum=1,
            )
        instances = require_list(plate["instances"], f"{context}.instances")
        for instance_index, value in enumerate(instances):
            instance_context = f"{context}.instances[{instance_index}]"
            instance = require_mapping(
                value, instance_context, {"object_id", "instance_id"}
            )
            require_integer(
                instance["object_id"],
                f"{instance_context}.object_id",
                minimum=1,
            )
            if instance["instance_id"] is not None:
                require_integer(
                    instance["instance_id"],
                    f"{instance_context}.instance_id",
                )

    objects = require_list(report["objects"], "objects")
    object_fields = {
        "object_id",
        "name",
        "plate_id",
        "plate_name",
        "plate_ids",
        "plate_names",
        "instances",
        "source_model_member",
        "source_model_members",
        "part_count",
        "part_assignments",
        "material_assignment",
        "resolved_material",
        "physical_nozzle_assignment",
        "recommended_tool_class",
        "semantic_name_tokens",
        "geometry",
        "warnings",
    }
    for index, value in enumerate(objects):
        context = f"objects[{index}]"
        item = require_mapping(value, context, object_fields)
        require_integer(item["object_id"], f"{context}.object_id", minimum=1)
        require_string(item["name"], f"{context}.name")
        if item["plate_id"] is not None:
            require_integer(item["plate_id"], f"{context}.plate_id", minimum=1)
        require_string(item["plate_name"], f"{context}.plate_name", nullable=True)
        plate_ids = require_list(item["plate_ids"], f"{context}.plate_ids")
        for plate_index, plate_id in enumerate(plate_ids):
            require_integer(
                plate_id, f"{context}.plate_ids[{plate_index}]", minimum=1
            )
        require_string_list(item["plate_names"], f"{context}.plate_names")
        instances = require_list(item["instances"], f"{context}.instances")
        for instance_index, value in enumerate(instances):
            instance_context = f"{context}.instances[{instance_index}]"
            instance = require_mapping(
                value,
                instance_context,
                {"plate_id", "plate_name", "instance_id"},
            )
            require_integer(
                instance["plate_id"],
                f"{instance_context}.plate_id",
                minimum=1,
            )
            require_string(
                instance["plate_name"],
                f"{instance_context}.plate_name",
                nullable=True,
            )
            if instance["instance_id"] is not None:
                require_integer(
                    instance["instance_id"],
                    f"{instance_context}.instance_id",
                )
        require_string(
            item["source_model_member"],
            f"{context}.source_model_member",
            nullable=True,
        )
        require_string_list(
            item["source_model_members"], f"{context}.source_model_members"
        )
        require_integer(item["part_count"], f"{context}.part_count")
        part_assignments = require_list(
            item["part_assignments"], f"{context}.part_assignments"
        )
        for part_index, assignment in enumerate(part_assignments):
            validate_part_assignment(
                assignment, f"{context}.part_assignments[{part_index}]"
            )
        if item["material_assignment"] is not None:
            require_integer(
                item["material_assignment"],
                f"{context}.material_assignment",
                minimum=1,
            )
        if item["resolved_material"] is not None:
            validate_material(item["resolved_material"], f"{context}.resolved_material")
        for field in (
            "physical_nozzle_assignment",
            "recommended_tool_class",
        ):
            if item[field] is not None:
                invalid_report(f"{context}.{field}", "must be null")
        require_string_list(
            item["semantic_name_tokens"], f"{context}.semantic_name_tokens"
        )
        if item["geometry"] is not None:
            validate_geometry(item["geometry"], f"{context}.geometry")
        validate_warning_list(item["warnings"], f"{context}.warnings")

    validate_warning_list(report["warnings"], "warnings")


def serialize_json(report: dict[str, Any]) -> str:
    validate_report(report)
    try:
        return (
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        )
    except (TypeError, ValueError) as exc:
        raise ObservationError(f"invalid observation report: {exc}") from exc


def markdown_text(value: Any) -> str:
    escaped = html.escape(str(value), quote=True)
    return (
        escaped
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "<br>")
        .replace("|", "&#124;")
        .replace("`", "&#96;")
    )


def serialize_markdown(report: dict[str, Any]) -> str:
    validate_report(report)
    source = report["source"]
    nozzle_diameters = report["physical_tools"]["nozzle_diameters"]
    nozzle_vector = ",".join(
        "" if diameter is None else markdown_text(diameter)
        for diameter in nozzle_diameters
    )
    lines = [
        "# AMP 3MF Observation",
        "",
        f"- Source: `{markdown_text(source['file_name'])}`",
        f"- SHA-256: `{markdown_text(source['sha256'])}`",
        f"- ZIP members: {source['member_count']}",
        f"- Plates: {len(report['plates'])}",
        f"- Objects: {len(report['objects'])}",
        f"- Configured nozzle vector: `{nozzle_vector}`",
        "",
        "## Objects",
        "",
        "| ID | Name | Plate | Material slot | Vertices | Triangles |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in report["objects"]:
        geometry = item["geometry"] or {}
        lines.append(
            f"| {item['object_id']} | {markdown_text(item['name'])} | "
            f"{item['plate_id'] or ''} | {item['material_assignment'] or ''} | "
            f"{geometry.get('vertex_count', '')} | "
            f"{geometry.get('triangle_count', '')} |"
        )
    lines.extend(
        [
            "",
            "Material/color assignments are not physical nozzle assignments or "
            "AMP recommendations.",
            "",
        ]
    )
    return "\n".join(lines)


def cleanup_report_artifacts(outputs: list[StagedReportOutput]) -> list[str]:
    errors = []
    for output in outputs:
        for kind, artifact in (
            ("temporary file", output.temp_path),
            ("backup", output.backup_path),
        ):
            if artifact is None:
                continue
            try:
                artifact.unlink(missing_ok=True)
            except (OSError, UnicodeError) as exc:
                errors.append(
                    f"{output.destination} {kind} cleanup failed: {exc}"
                )
    return errors


def stage_report_output(output: StagedReportOutput) -> None:
    destination = output.destination
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            output.temp_path = Path(handle.name)
            handle.write(output.content)
    except (OSError, UnicodeError) as exc:
        raise ObservationError(
            f"failed to stage report destination {destination}: {exc}"
        ) from exc


def backup_report_output(output: StagedReportOutput) -> None:
    destination = output.destination
    output.existed = os.path.lexists(destination)
    if not output.existed:
        return
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".bak",
            delete=False,
        ) as handle:
            output.backup_path = Path(handle.name)
        shutil.copy2(destination, output.backup_path)
    except (OSError, UnicodeError) as exc:
        raise ObservationError(
            f"failed to back up report destination {destination}: {exc}"
        ) from exc


def commit_report_outputs(outputs: list[StagedReportOutput]) -> None:
    try:
        for output in outputs:
            stage_report_output(output)
        for output in outputs:
            backup_report_output(output)
    except ObservationError as exc:
        cleanup_errors = cleanup_report_artifacts(outputs)
        if cleanup_errors:
            raise ObservationError(
                f"{exc}; pre-commit cleanup errors: "
                + "; ".join(cleanup_errors)
            ) from exc
        raise

    current: StagedReportOutput | None = None
    try:
        for current in outputs:
            if current.temp_path is None:
                raise ObservationError(
                    f"missing staged report for {current.destination}"
                )
            os.replace(current.temp_path, current.destination)
            current.temp_path = None
            current.replaced = True
    except (OSError, UnicodeError, ObservationError) as exc:
        rollback_errors = []
        for output in reversed(outputs):
            if not output.replaced:
                continue
            try:
                if output.existed:
                    if output.backup_path is None:
                        raise OSError("missing rollback backup")
                    os.replace(output.backup_path, output.destination)
                    output.backup_path = None
                else:
                    output.destination.unlink(missing_ok=True)
            except (OSError, UnicodeError) as rollback_exc:
                rollback_errors.append(
                    f"{output.destination}: {rollback_exc}"
                )
        cleanup_errors = cleanup_report_artifacts(outputs)
        details = rollback_errors + cleanup_errors
        suffix = f"; rollback cleanup errors: {'; '.join(details)}" if details else ""
        destination = current.destination if current is not None else "unknown"
        raise ObservationError(
            f"failed to replace report destination {destination}: {exc}{suffix}"
        ) from exc

    cleanup_errors = cleanup_report_artifacts(outputs)
    if cleanup_errors:
        raise ObservationError(
            "failed to clean report output artifacts: "
            + "; ".join(cleanup_errors)
        )


def atomic_write(path: Path, content: str) -> Path:
    path = Path(path)
    commit_report_outputs([StagedReportOutput(path, content)])
    return path


def normalized_output_path(path: Path) -> str:
    try:
        absolute = os.path.abspath(os.path.normpath(os.fspath(path)))
        return os.path.normcase(os.path.realpath(absolute))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ObservationError(
            f"cannot normalize report path {path}: {exc}"
        ) from exc


def filesystem_is_case_insensitive(path: Path) -> bool:
    if os.path.normcase("A") == os.path.normcase("a"):
        return True
    current = Path(os.path.abspath(os.path.normpath(os.fspath(path))))
    while not os.path.lexists(current) and current.parent != current:
        current = current.parent
    for existing in (current, *current.parents):
        name = existing.name
        for index, character in enumerate(name):
            if not character.isalpha():
                continue
            swapped = character.swapcase()
            if swapped == character:
                continue
            alternate = existing.with_name(
                name[:index] + swapped + name[index + 1 :]
            )
            try:
                if os.path.samefile(existing, alternate):
                    return True
            except FileNotFoundError:
                pass
            except (OSError, UnicodeError, ValueError) as exc:
                raise ObservationError(
                    f"cannot determine report path case sensitivity for "
                    f"{path}: {exc}"
                ) from exc
            break
    return False


def paths_alias(first: Path, second: Path) -> bool:
    first_normalized = normalized_output_path(first)
    second_normalized = normalized_output_path(second)
    if first_normalized == second_normalized:
        return True
    if (
        first_normalized.casefold() == second_normalized.casefold()
        and (
            filesystem_is_case_insensitive(first)
            or filesystem_is_case_insensitive(second)
        )
    ):
        return True
    try:
        return os.path.samefile(first, second)
    except FileNotFoundError:
        return False
    except (OSError, UnicodeError, ValueError) as exc:
        raise ObservationError(
            f"cannot compare report paths {first} and {second}: {exc}"
        ) from exc


def validate_report_paths(
    source_path: Path,
    json_path: Path | None,
    markdown_path: Path | None,
) -> None:
    source_path = Path(source_path)
    if json_path is not None and paths_alias(source_path, Path(json_path)):
        raise ObservationError(
            f"JSON destination aliases source: {json_path}"
        )
    if markdown_path is not None and paths_alias(
        source_path, Path(markdown_path)
    ):
        raise ObservationError(
            f"Markdown destination aliases source: {markdown_path}"
        )
    if (
        json_path is not None
        and markdown_path is not None
        and paths_alias(Path(json_path), Path(markdown_path))
    ):
        raise ObservationError(
            "JSON and Markdown destinations alias: "
            f"{json_path} and {markdown_path}"
        )


def write_reports(
    report: dict[str, Any],
    *,
    source_path: Path,
    json_path: Path | None,
    markdown_path: Path | None,
) -> None:
    validate_report_paths(source_path, json_path, markdown_path)
    json_content = serialize_json(report) if json_path is not None else None
    markdown_content = (
        serialize_markdown(report) if markdown_path is not None else None
    )
    outputs = []
    if json_path is not None and json_content is not None:
        outputs.append(StagedReportOutput(Path(json_path), json_content))
    if markdown_path is not None and markdown_content is not None:
        outputs.append(StagedReportOutput(Path(markdown_path), markdown_content))
    commit_report_outputs(outputs)


def silence_stdout() -> None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    except (OSError, UnicodeError):
        pass


def write_json_stdout(report: dict[str, Any]) -> None:
    content = serialize_json(report)
    try:
        sys.stdout.write(content)
        sys.stdout.flush()
    except BrokenPipeError:
        raise
    except (OSError, UnicodeError) as exc:
        silence_stdout()
        raise ObservationError(
            f"failed to write observation JSON to stdout: {exc}"
        ) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--3mf", required=True, type=Path, dest="source")
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args(argv)
    try:
        validate_report_paths(args.source, args.out_json, args.out_md)
        report = observe_3mf(args.source)
        if args.out_json is None and args.out_md is None:
            write_json_stdout(report)
        else:
            write_reports(
                report,
                source_path=args.source,
                json_path=args.out_json,
                markdown_path=args.out_md,
            )
    except BrokenPipeError:
        silence_stdout()
        return 1
    except ObservationError as exc:
        print(f"AMP 3MF observation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
