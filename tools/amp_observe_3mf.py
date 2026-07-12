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
from collections import Counter
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


def validate_nozzle_entries(values: list[Any], warnings: list[str]) -> list[str]:
    validated: list[str] = []
    for slot, value in enumerate(values, start=1):
        is_numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        if isinstance(value, str) or is_numeric:
            validated.append(str(value))
            continue
        warnings.append(
            f"project nozzle_diameter slot {slot} must be a string or numeric scalar; "
            f"got {json_value_kind(value)}"
        )
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
            settings_project, physical_tools, materials, project_warnings = (
                parse_project_settings(read_json_member(archive, PROJECT_SETTINGS))
            )
            project = {**root_project, **settings_project}
            objects, plates, model_warnings = parse_model_settings(
                archive.read(MODEL_SETTINGS), materials
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
