#!/usr/bin/env python3
"""Generate an Orca 3MF handoff from an AMP plan packet and 3MF template.

This tool changes project representation only. It does not slice, emit G-code,
connect to a printer, or bypass printer-side validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
AMP_METADATA_PREFIX = "Metadata/AMP/"
PACKET_SIDECAR_FILES = (
    "plan.json",
    "regions.json",
    "resolution_field.json",
    "tool_assignments.json",
    "process_queue.json",
    "toolchange_schedule.json",
    "per_region_gcode_status.json",
    "debug_artifact.json",
    "preflight_status.json",
    "risk_report.md",
)


class HandoffError(ValueError):
    """Raised when a template or AMP packet cannot produce a valid handoff."""


@dataclass(frozen=True)
class HandoffPlan:
    assignments: dict[str, int]
    nozzle_diameters: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_region_name(value: str) -> str:
    name = str(value).strip()
    return name[:-4] if name.lower().endswith(".stl") else name


def load_plan(packet_dir: Path) -> HandoffPlan:
    queue_path = packet_dir / "process_queue.json"
    if not queue_path.is_file():
        raise HandoffError(f"missing AMP packet file: {queue_path}")
    try:
        payload = json.loads(queue_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HandoffError(f"invalid process_queue.json: {exc}") from exc
    queue = payload.get("process_queue", [])
    if not isinstance(queue, list) or not queue:
        raise HandoffError("process_queue.json contains no process_queue entries")
    try:
        tool_classes = sorted(
            {str(item["recommended_tool_class"]) for item in queue}, key=float
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HandoffError(f"invalid process_queue.json tool class: {exc}") from exc
    tool_slots = {tool_class: index + 1 for index, tool_class in enumerate(tool_classes)}
    assignments: dict[str, int] = {}
    for item in queue:
        try:
            region_name = normalize_region_name(str(item["region_name"]))
            tool_class = str(item["recommended_tool_class"])
        except (KeyError, TypeError) as exc:
            raise HandoffError(f"invalid process_queue.json entry: {exc}") from exc
        if not region_name:
            raise HandoffError("process_queue.json contains an empty region_name")
        if region_name in assignments:
            raise HandoffError(f"duplicate planned region: {region_name}")
        assignments[region_name] = tool_slots[tool_class]
    return HandoffPlan(assignments=assignments, nozzle_diameters=tool_classes)


def patch_model_settings(data: bytes, assignments: dict[str, int]) -> bytes:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise HandoffError(f"invalid {MODEL_SETTINGS}: {exc}") from exc
    matched: set[str] = set()
    for obj in root.findall("object"):
        metadata = {
            item.attrib.get("key"): item
            for item in obj.findall("metadata")
            if item.attrib.get("key")
        }
        name_item = metadata.get("name")
        if name_item is None:
            continue
        region_name = normalize_region_name(name_item.attrib.get("value", ""))
        if region_name not in assignments:
            continue
        if region_name in matched:
            raise HandoffError(f"duplicate template region: {region_name}")
        extruder_item = metadata.get("extruder")
        if extruder_item is None:
            extruder_item = ET.SubElement(obj, "metadata", {"key": "extruder"})
        extruder_item.set("value", str(assignments[region_name]))
        matched.add(region_name)

    missing = sorted(set(assignments) - matched)
    if missing:
        raise HandoffError("missing planned region(s) in template: " + ", ".join(missing))

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def patch_project_settings(data: bytes, nozzles: list[str]) -> bytes:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HandoffError(f"invalid {PROJECT_SETTINGS}: {exc}") from exc
    existing = payload.get("nozzle_diameter")
    if not isinstance(existing, list) or len(existing) < len(nozzles):
        available = len(existing) if isinstance(existing, list) else 0
        raise HandoffError(
            f"template has {available} tool slots; AMP plan requires {len(nozzles)}"
        )
    payload["nozzle_diameter"] = list(nozzles) + existing[len(nozzles) :]
    return (json.dumps(payload, indent="\t") + "\n").encode("utf-8")


def packet_members(packet_dir: Path) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    for name in PACKET_SIDECAR_FILES:
        path = packet_dir / name
        if path.is_file():
            members[f"{AMP_METADATA_PREFIX}{name}"] = path.read_bytes()
    return members


def handoff_manifest(
    template: Path, packet_dir: Path, plan: HandoffPlan
) -> dict[str, Any]:
    preflight_path = packet_dir / "preflight_status.json"
    preflight_status = "not_ready"
    if preflight_path.is_file():
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        preflight_status = str(preflight.get("status", "not_ready"))
    nozzle_by_slot = {
        index + 1: nozzle for index, nozzle in enumerate(plan.nozzle_diameters)
    }
    return {
        "schema_version": "0.1",
        "generator": "tools/amp_orca_3mf_handoff.py",
        "source_template_sha256": sha256_file(template),
        "nozzle_diameters": plan.nozzle_diameters,
        "region_assignments": [
            {
                "region_name": region_name,
                "orca_extruder": slot,
                "expected_t_command": f"T{slot - 1}",
                "nozzle_diameter": nozzle_by_slot[slot],
            }
            for region_name, slot in sorted(plan.assignments.items())
        ],
        "hardware_preflight_status": preflight_status,
        "non_claims": [
            "no physical mixed-nozzle validation",
            "no touchscreen-compatible mixed-nozzle claim",
            "no Snapmaker validation bypass",
            "no printer execution",
        ],
    }


def deterministic_zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    return info


def generate_handoff(
    template: Path, packet_dir: Path, output: Path
) -> dict[str, Any]:
    template = Path(template)
    packet_dir = Path(packet_dir)
    output = Path(output)
    if template.resolve() == output.resolve():
        raise HandoffError("template and output paths must be different")

    plan = load_plan(packet_dir)
    embedded_members = packet_members(packet_dir)
    embedded_members[f"{AMP_METADATA_PREFIX}source_template.sha256"] = (
        sha256_file(template) + "\n"
    ).encode("ascii")
    embedded_members[f"{AMP_METADATA_PREFIX}handoff_manifest.json"] = (
        json.dumps(
            handoff_manifest(template, packet_dir, plan), indent=2, sort_keys=True
        )
        + "\n"
    ).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with zipfile.ZipFile(template, "r") as source:
            names = set(source.namelist())
            missing_members = sorted({MODEL_SETTINGS, PROJECT_SETTINGS} - names)
            if missing_members:
                raise HandoffError(
                    "template is missing required member(s): "
                    + ", ".join(missing_members)
                )
            patched_model = patch_model_settings(
                source.read(MODEL_SETTINGS), plan.assignments
            )
            patched_project = patch_project_settings(
                source.read(PROJECT_SETTINGS), plan.nozzle_diameters
            )

            with tempfile.NamedTemporaryFile(
                dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)

            with zipfile.ZipFile(temp_path, "w") as destination:
                for info in sorted(source.infolist(), key=lambda item: item.filename):
                    if info.filename.startswith(AMP_METADATA_PREFIX):
                        continue
                    data = source.read(info.filename)
                    if info.filename == MODEL_SETTINGS:
                        data = patched_model
                    elif info.filename == PROJECT_SETTINGS:
                        data = patched_project
                    destination.writestr(info, data)
                for name, data in sorted(embedded_members.items()):
                    destination.writestr(deterministic_zip_info(name), data)

        with zipfile.ZipFile(temp_path, "r") as generated:
            generated.testzip()
        os.replace(temp_path, output)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return {
        "output": str(output),
        "region_count": len(plan.assignments),
        "nozzle_diameters": plan.nozzle_diameters,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    result = generate_handoff(args.template, args.packet, args.out)
    print(f"wrote {result['output']}")
    print(f"region_count={result['region_count']}")
    print("nozzle_diameters=" + ",".join(result["nozzle_diameters"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
