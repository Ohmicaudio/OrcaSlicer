#!/usr/bin/env python3
"""Validate an AMP-generated Orca 3MF handoff package."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any


MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
MANIFEST = "Metadata/AMP/handoff_manifest.json"
SOURCE_TEMPLATE_HASH = "Metadata/AMP/source_template.sha256"
REQUIRED_EMBEDDED = {
    "Metadata/AMP/plan.json",
    "Metadata/AMP/process_queue.json",
    "Metadata/AMP/tool_assignments.json",
    MANIFEST,
    SOURCE_TEMPLATE_HASH,
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def normalize_region_name(value: str) -> str:
    name = str(value).strip()
    return name[:-4] if name.lower().endswith(".stl") else name


def expected_plan(packet_dir: Path) -> tuple[dict[str, int], list[str]]:
    payload = json.loads((packet_dir / "process_queue.json").read_text(encoding="utf-8"))
    queue = payload["process_queue"]
    nozzles = sorted(
        {str(item["recommended_tool_class"]) for item in queue}, key=float
    )
    slots = {nozzle: index + 1 for index, nozzle in enumerate(nozzles)}
    assignments = {
        normalize_region_name(item["region_name"]): slots[
            str(item["recommended_tool_class"])
        ]
        for item in queue
    }
    return assignments, nozzles


def parse_assignments(data: bytes) -> dict[str, str]:
    root = ET.fromstring(data)
    assignments: dict[str, str] = {}
    for obj in root.findall("object"):
        metadata = {
            item.attrib.get("key"): item.attrib.get("value", "")
            for item in obj.findall("metadata")
        }
        if "name" in metadata and "extruder" in metadata:
            assignments[normalize_region_name(metadata["name"])] = metadata["extruder"]
    return assignments


def validate_handoff(archive_path: Path, packet_dir: Path) -> dict[str, Any]:
    archive_path = Path(archive_path)
    packet_dir = Path(packet_dir)
    errors: list[str] = []
    warnings: list[str] = []
    observed_assignments: dict[str, str] = {}
    observed_nozzles: list[str] = []

    try:
        expected_assignments, expected_nozzles = expected_plan(packet_dir)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid AMP process_queue.json: {exc}")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "region_assignments": observed_assignments,
            "nozzle_diameters": observed_nozzles,
        }

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = set(archive.namelist())
            required = REQUIRED_EMBEDDED | {MODEL_SETTINGS, PROJECT_SETTINGS}
            for missing in sorted(required - names):
                errors.append(f"missing required 3MF member: {missing}")

            if MODEL_SETTINGS in names:
                try:
                    observed_assignments = parse_assignments(
                        archive.read(MODEL_SETTINGS)
                    )
                except ET.ParseError as exc:
                    errors.append(f"invalid {MODEL_SETTINGS}: {exc}")

            if PROJECT_SETTINGS in names:
                try:
                    project = json.loads(archive.read(PROJECT_SETTINGS))
                    nozzles = project.get("nozzle_diameter", [])
                    if isinstance(nozzles, list):
                        observed_nozzles = [str(value) for value in nozzles]
                    else:
                        errors.append("project nozzle_diameter is not a list")
                except (UnicodeError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid {PROJECT_SETTINGS}: {exc}")

            for region_name, expected_slot in sorted(expected_assignments.items()):
                observed_slot = observed_assignments.get(region_name)
                if observed_slot != str(expected_slot):
                    errors.append(
                        f"region {region_name} extruder mismatch: "
                        f"expected {expected_slot}, observed {observed_slot or 'missing'}"
                    )

            if observed_nozzles[: len(expected_nozzles)] != expected_nozzles:
                errors.append(
                    "project nozzle vector mismatch: expected leading "
                    + ",".join(expected_nozzles)
                    + "; observed "
                    + ",".join(observed_nozzles)
                )
            if len(observed_nozzles) > len(expected_nozzles):
                warnings.append("template retains additional unused tool slots")

            if "Metadata/AMP/process_queue.json" in names:
                source_queue = (packet_dir / "process_queue.json").read_bytes()
                if archive.read("Metadata/AMP/process_queue.json") != source_queue:
                    errors.append("embedded process_queue.json differs from source packet")

            if MANIFEST in names:
                try:
                    manifest = json.loads(archive.read(MANIFEST))
                    if manifest.get("nozzle_diameters") != expected_nozzles:
                        errors.append("handoff manifest nozzle vector differs from plan")
                    manifest_mapping = {
                        str(item.get("region_name")): int(item.get("orca_extruder"))
                        for item in manifest.get("region_assignments", [])
                    }
                    if manifest_mapping != expected_assignments:
                        errors.append("handoff manifest region mapping differs from plan")
                    manifest_hash = str(manifest.get("source_template_sha256", ""))
                    if SOURCE_TEMPLATE_HASH in names:
                        embedded_hash = archive.read(SOURCE_TEMPLATE_HASH).decode("ascii").strip()
                        if manifest_hash != embedded_hash:
                            errors.append("handoff manifest template hash mismatch")
                        if not SHA256_RE.fullmatch(embedded_hash) or embedded_hash == "0" * 64:
                            errors.append("embedded source template hash is invalid")
                except (UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid {MANIFEST}: {exc}")
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"invalid 3MF archive: {exc}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "region_assignments": observed_assignments,
        "nozzle_diameters": observed_nozzles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--3mf", required=True, type=Path, dest="archive_path")
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = validate_handoff(args.archive_path, args.packet)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print("PASS" if report["valid"] else "FAIL")
    print(f"errors={len(report['errors'])} warnings={len(report['warnings'])}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
