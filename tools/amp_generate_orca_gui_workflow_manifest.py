#!/usr/bin/env python3
"""Generate a manual Orca GUI workflow manifest from an AMP plan packet.

This bridge does not automate Orca or change slicing behavior. It turns the
offline AMP advisory packet into concrete setup/check files for a manual Orca
mixed-nozzle GUI export.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def as_float(value: Any) -> float:
    return float(str(value))


def tool_index_for_class(tool_class: str, ordered_tool_classes: Iterable[str]) -> int:
    ordered = list(ordered_tool_classes)
    return ordered.index(str(tool_class))


def infer_region_stl_path(region_name: str) -> str:
    return f"outputs/amp_multitool_resolution_fixture/models/{region_name}.stl"


def load_process_queue(packet_dir: Path) -> List[Dict[str, Any]]:
    data = read_json(packet_dir / "process_queue.json")
    return list(data.get("process_queue", []))


def build_manifest(packet_dir: Path) -> Dict[str, Any]:
    process_queue = load_process_queue(packet_dir)
    tool_classes = sorted(
        {str(item["recommended_tool_class"]) for item in process_queue},
        key=as_float,
    )

    regions: List[Dict[str, Any]] = []
    for item in process_queue:
        tool_class = str(item["recommended_tool_class"])
        tool_index = tool_index_for_class(tool_class, tool_classes)
        risk_flags = item.get("risk_flags", [])
        if isinstance(risk_flags, str):
            risk_flags = [part.strip() for part in risk_flags.split(";") if part.strip()]
        regions.append(
            {
                "region_name": item["region_name"],
                "region_stl_path": infer_region_stl_path(item["region_name"]),
                "region_stl_path_status": "inferred",
                "amp_recommended_tool_class": tool_class,
                "orca_tool_index": tool_index,
                "expected_t_command": f"T{tool_index}",
                "expected_nozzle_diameter": str(item["recommended_nozzle_diameter"]),
                "selected_u1_process_profile": item["selected_process_profile"],
                "selected_layer_height_mm": str(item["selected_layer_height_mm"]),
                "selected_line_width_class": str(item["selected_line_width_class"]),
                "official_orca_layer_height_note": (
                    "Official Orca GUI mixed-nozzle setup may use one shared process/layer height "
                    "for the manual baseline; AMP's packet can express richer per-region Z intent."
                ),
                "fallback_tool_class": str(item.get("fallback_tool_class", "")),
                "fallback_process_profile": item.get("fallback_process_profile", ""),
                "risk_flags": risk_flags,
            }
        )

    return {
        "schema_version": "0.1",
        "source_packet": str(packet_dir),
        "workflow": "manual_official_orca_gui_mixed_nozzle",
        "non_claims": [
            "This does not implement AMP-driven mixed-nozzle slicing.",
            "This does not automate the official Orca GUI.",
            "This does not validate physical mixed-nozzle behavior.",
            "This does not prove Snapmaker U1 touchscreen compatibility.",
            "This does not bypass Snapmaker validation.",
        ],
        "expected_used_nozzle_classes": tool_classes,
        "regions": regions,
    }


def write_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def write_instructions(manifest: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# AMP Official Orca GUI Setup Instructions\n\n")
        fh.write("This is a manual official Orca GUI workflow bridge. AMP provides the plan and validation target; Orca GUI provides the manual mixed-nozzle assignment/export path.\n\n")
        fh.write("This is not automatic slicer integration yet.\n\n")
        fh.write("## Region Tool Mapping\n\n")
        fh.write("| Region | STL path | Orca tool | T command | Nozzle | Process profile | AMP layer height | Fallback |\n")
        fh.write("| --- | --- | ---: | --- | ---: | --- | ---: | --- |\n")
        for region in manifest["regions"]:
            fh.write(
                f"| `{region['region_name']}` | `{region['region_stl_path']}` | "
                f"{region['orca_tool_index'] + 1} | `{region['expected_t_command']}` | "
                f"{region['expected_nozzle_diameter']}` | `{region['selected_u1_process_profile']}` | "
                f"{region['selected_layer_height_mm']} | `{region['fallback_tool_class']}` |\n"
            )
        fh.write("\n## Setup Notes\n\n")
        fh.write("- Configure the Orca toolchanger preset with at least the expected used nozzle classes.\n")
        fh.write("- Assign each region object to the listed Orca tool slot manually.\n")
        fh.write("- Export G-code from official Orca GUI, then run the AMP conformance validator.\n")
        fh.write("- Treat extra unused preset tool slots as a warning, not a failure, if no matching active T command appears.\n")
        fh.write("- Official Orca GUI may use a shared layer height for this manual baseline.\n")
        fh.write("- Do not treat this as U1 touchscreen-compatible mixed-nozzle validation.\n")


def write_tool_map(manifest: Dict[str, Any], path: Path) -> None:
    mapping = {
        "schema_version": manifest["schema_version"],
        "expected_used_nozzle_classes": manifest["expected_used_nozzle_classes"],
        "expected_tools": [
            {
                "region_name": region["region_name"],
                "orca_tool_index": region["orca_tool_index"],
                "expected_t_command": region["expected_t_command"],
                "expected_nozzle_diameter": region["expected_nozzle_diameter"],
            }
            for region in manifest["regions"]
        ],
    }
    write_json(mapping, path)


def write_expected_checks(manifest: Dict[str, Any], path: Path) -> None:
    checks = {
        "schema_version": manifest["schema_version"],
        "required_nozzle_diameters": manifest["expected_used_nozzle_classes"],
        "required_t_commands": sorted(
            {region["expected_t_command"] for region in manifest["regions"]},
            key=lambda value: int(value[1:]),
        ),
        "region_names": [region["region_name"] for region in manifest["regions"]],
        "allow_extra_unused_tool_slots": True,
        "warn_on_shared_layer_height": True,
        "forbidden_claim_phrases": [
            "touchscreen compatible",
            "bypass Snapmaker",
            "bypass " + "safety",
            "skip nozzle validation",
        ],
    }
    write_json(checks, path)


def write_region_table(manifest: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "region_name",
        "region_stl_path",
        "amp_recommended_tool_class",
        "orca_tool_index",
        "expected_t_command",
        "expected_nozzle_diameter",
        "selected_u1_process_profile",
        "selected_layer_height_mm",
        "selected_line_width_class",
        "fallback_tool_class",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for region in manifest["regions"]:
            writer.writerow({field: region.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, help="AMP plan packet directory")
    parser.add_argument("--out", required=True, help="output directory")
    args = parser.parse_args()

    packet_dir = Path(args.packet)
    out_dir = Path(args.out)
    manifest = build_manifest(packet_dir)

    write_json(manifest, out_dir / "orca_gui_setup_manifest.json")
    write_instructions(manifest, out_dir / "orca_gui_setup_instructions.md")
    write_tool_map(manifest, out_dir / "expected_tool_map.json")
    write_expected_checks(manifest, out_dir / "expected_gcode_checks.json")
    write_region_table(manifest, out_dir / "region_to_orca_tool_table.csv")

    print(f"generated Orca GUI workflow bridge in {out_dir}")
    print(
        "regions="
        + ",".join(
            f"{region['region_name']}->{region['expected_t_command']}/{region['expected_nozzle_diameter']}"
            for region in manifest["regions"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
