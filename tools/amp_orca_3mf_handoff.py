#!/usr/bin/env python3
"""Generate an Orca 3MF handoff from an AMP plan packet and 3MF template.

This tool changes project representation only. It does not slice, emit G-code,
connect to a printer, or bypass printer-side validation.
"""

from __future__ import annotations

import argparse
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


class HandoffError(ValueError):
    """Raised when a template or AMP packet cannot produce a valid handoff."""


@dataclass(frozen=True)
class HandoffPlan:
    assignments: dict[str, int]
    nozzle_diameters: list[str]


def normalize_region_name(value: str) -> str:
    name = str(value).strip()
    return name[:-4] if name.lower().endswith(".stl") else name


def load_plan(packet_dir: Path) -> HandoffPlan:
    queue_path = packet_dir / "process_queue.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    queue = payload.get("process_queue", [])
    tool_classes = sorted(
        {str(item["recommended_tool_class"]) for item in queue}, key=float
    )
    tool_slots = {tool_class: index + 1 for index, tool_class in enumerate(tool_classes)}
    assignments = {
        normalize_region_name(str(item["region_name"])): tool_slots[
            str(item["recommended_tool_class"])
        ]
        for item in queue
    }
    return HandoffPlan(assignments=assignments, nozzle_diameters=tool_classes)


def patch_model_settings(data: bytes, assignments: dict[str, int]) -> bytes:
    root = ET.fromstring(data)
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
    payload = json.loads(data.decode("utf-8"))
    existing = payload.get("nozzle_diameter")
    if not isinstance(existing, list) or len(existing) < len(nozzles):
        available = len(existing) if isinstance(existing, list) else 0
        raise HandoffError(
            f"template has {available} tool slots; AMP plan requires {len(nozzles)}"
        )
    payload["nozzle_diameter"] = list(nozzles) + existing[len(nozzles) :]
    return (json.dumps(payload, indent="\t") + "\n").encode("utf-8")


def generate_handoff(
    template: Path, packet_dir: Path, output: Path
) -> dict[str, Any]:
    template = Path(template)
    packet_dir = Path(packet_dir)
    output = Path(output)
    if template.resolve() == output.resolve():
        raise HandoffError("template and output paths must be different")

    plan = load_plan(packet_dir)
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
                    data = source.read(info.filename)
                    if info.filename == MODEL_SETTINGS:
                        data = patched_model
                    elif info.filename == PROJECT_SETTINGS:
                        data = patched_project
                    destination.writestr(info, data)

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
