#!/usr/bin/env python3
"""Generate a disabled Fluidd/Klipper macro sandbox from an AMP plan packet.

The generated files are templates and dry-run artifacts only. They are not
intended to be installed on a printer without review and hardware validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HEADER = [
    "# AMP SANDBOX TEMPLATE ONLY",
    "# NOT READY TO PRINT",
    "# DO NOT INSTALL ON A PRINTER WITHOUT REVIEW",
    "# DOES NOT IMPLEMENT MIXED-NOZZLE SLICING",
    "# DOES NOT BYPASS SNAPMAKER TOUCHSCREEN VALIDATION",
]

GCODE_HEADER = [
    "; AMP SANDBOX DRY RUN ONLY",
    "; NOT READY TO PRINT",
    "; DO NOT INSTALL ON A PRINTER WITHOUT REVIEW",
    "; DOES NOT IMPLEMENT MIXED-NOZZLE SLICING",
    "; DOES NOT BYPASS SNAPMAKER TOUCHSCREEN VALIDATION",
]

TOOL_MACROS = {
    "0.2": "AMP_TOOL_0P2",
    "0.4": "AMP_TOOL_0P4",
    "0.6": "AMP_TOOL_0P6",
    "0.8": "AMP_TOOL_0P8",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [part.strip() for part in value.split(";") if part.strip()]
    return []


def load_packet(packet_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    schedule_path = packet_dir / "toolchange_schedule.json"
    assignments_path = packet_dir / "tool_assignments.json"
    if not schedule_path.exists():
        raise FileNotFoundError(f"missing {schedule_path}")
    if not assignments_path.exists():
        raise FileNotFoundError(f"missing {assignments_path}")
    schedule = read_json(schedule_path)
    assignments = read_json(assignments_path)
    if not isinstance(schedule.get("schedule"), list):
        raise ValueError("toolchange_schedule.json must contain a schedule array")
    if not isinstance(assignments.get("tool_assignments"), list):
        raise ValueError("tool_assignments.json must contain a tool_assignments array")
    return schedule, assignments


def assignment_by_region(assignments: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in assignments.get("tool_assignments", []):
        if isinstance(item, dict) and item.get("region_name"):
            result[str(item["region_name"])] = item
    return result


def build_tool_map(schedule: dict[str, Any], assignments: dict[str, Any]) -> list[dict[str, Any]]:
    assignment_map = assignment_by_region(assignments)
    tools: dict[str, dict[str, Any]] = {}
    for step in schedule.get("schedule", []):
        if not isinstance(step, dict):
            continue
        tool_class = str(step.get("tool_class", "unknown"))
        region_name = str(step.get("region_name", ""))
        assignment = assignment_map.get(region_name, {})
        entry = tools.setdefault(
            tool_class,
            {
                "tool_class": tool_class,
                "tool_macro": TOOL_MACROS.get(tool_class, f"AMP_TOOL_{tool_class.replace('.', 'P')}"),
                "nozzle_diameter": float(tool_class) if tool_class.replace(".", "", 1).isdigit() else None,
                "selected_process_profile": step.get("selected_process_profile", ""),
                "intended_regions": [],
                "fallback_tool": assignment.get("fallback_tool_class", ""),
                "risk_flags": [],
                "requires_hardware_validation": True,
            },
        )
        entry["intended_regions"].append(region_name)
        entry["risk_flags"].extend(flag for flag in as_list(step.get("risk_flags")) if flag not in entry["risk_flags"])
        for flag in as_list(assignment.get("risk_flags")):
            if flag not in entry["risk_flags"]:
                entry["risk_flags"].append(flag)
    return [tools[key] for key in sorted(tools, key=lambda item: float(item) if item.replace(".", "", 1).isdigit() else 99)]


def macro_block(name: str, description: str, message: str, params: list[str] | None = None) -> list[str]:
    params = params or []
    lines = [
        f"[gcode_macro {name}]",
        f"description: AMP sandbox placeholder - {description}",
    ]
    if params:
        for param in params:
            lines.append(f"variable_{param}: \"unset\"")
    lines.extend(
        [
            "gcode:",
            f"  # {message}",
            f"  RESPOND TYPE=command MSG=\"AMP sandbox: {message}\"",
            "",
        ]
    )
    return lines


def generate_tools_cfg(tool_map: list[dict[str, Any]]) -> list[str]:
    lines = HEADER + [
        "",
        "# This file declares AMP tool placeholders for dry-run review only.",
        "# No heaters, extruders, offsets, movement, or tool-selection commands are configured here.",
        "",
    ]
    for tool in tool_map:
        lines.extend(
            [
                f"# {tool['tool_macro']}",
                f"# tool_class: {tool['tool_class']}",
                f"# nozzle_diameter: {tool['nozzle_diameter']}",
                f"# selected_process_profile: {tool['selected_process_profile']}",
                f"# intended_regions: {', '.join(tool['intended_regions'])}",
                f"# fallback_tool: {tool['fallback_tool']}",
                "# offset_x: hardware_validation_required",
                "# offset_y: hardware_validation_required",
                "# offset_z: hardware_validation_required",
                "",
            ]
        )
    return lines


def generate_macros_cfg() -> list[str]:
    lines = HEADER + [
        "",
        "# These macros are dry-run placeholders. They intentionally avoid movement, heating, extrusion, and real tool selection.",
        "# Review and hardware validation are required before any executable macro can be created from this template.",
        "",
    ]
    macros = [
        ("AMP_DRY_RUN_SELECT_TOOL", "dry-run tool selection", "would select requested AMP tool class", ["tool_class"]),
        ("AMP_VALIDATE_TOOL_CLASS", "dry-run tool validation", "would validate requested tool class against hardware state", ["tool_class"]),
        ("AMP_APPLY_TOOL_OFFSET_PLACEHOLDER", "offset placeholder", "would apply reviewed per-tool offset placeholder", ["tool_class"]),
        ("AMP_SAVE_STATE_PLACEHOLDER", "state save placeholder", "would save printer state before toolchange"),
        ("AMP_RESTORE_STATE_PLACEHOLDER", "state restore placeholder", "would restore printer state after toolchange"),
        ("AMP_PARK_TOOL_PLACEHOLDER", "tool parking placeholder", "would park current tool using reviewed macro"),
        ("AMP_PICK_TOOL_PLACEHOLDER", "tool pick placeholder", "would pick requested tool using reviewed macro", ["tool_class"]),
        ("AMP_PURGE_WIPE_PLACEHOLDER", "purge/wipe placeholder", "would run reviewed purge or wipe macro"),
        ("AMP_PRINT_REGION_PLACEHOLDER", "region print placeholder", "would print region using slicer-generated toolpaths in a future integration", ["region_name"]),
    ]
    for spec in macros:
        lines.extend(macro_block(*spec))
    return lines


def generate_dry_run_schedule(schedule: dict[str, Any]) -> list[str]:
    lines = GCODE_HEADER + [
        "; Comments-only schedule with optional RESPOND dry-run lines.",
        "; No uncommented T commands.",
        "; No uncommented motion.",
        "; No uncommented extrusion.",
        "; No temperatures.",
        "",
    ]
    for step in schedule.get("schedule", []):
        if not isinstance(step, dict):
            continue
        lines.extend(
            [
                f"; STEP {step.get('step_index', '')}",
                f"; region={step.get('region_name', '')}",
                f"; planned_tool_class={step.get('tool_class', '')}",
                f"; selected_process_profile={step.get('selected_process_profile', '')}",
                f"; layer_height={step.get('selected_layer_height_mm', '')}",
                f"; line_width_class={step.get('selected_line_width_class', '')}",
                f"; risk_flags={'; '.join(as_list(step.get('risk_flags')))}",
                f"; requires_toolchange={str(step.get('requires_toolchange', '')).lower()}",
                f"; reason={step.get('reason', '')}",
                f"; fallback_if_rejected={step.get('fallback_if_rejected', '')}",
                f"; RESPOND TYPE=command MSG=\"AMP dry-run step {step.get('step_index', '')}: would use tool {step.get('tool_class', '')} for {step.get('region_name', '')}\"",
                "",
            ]
        )
    return lines


def generate_preflight_checklist() -> list[str]:
    return [
        "# AMP Fluidd/Klipper Sandbox Preflight Checklist",
        "",
        "This checklist is for a future developer-only dry-run path. The sandbox is not printable.",
        "",
        "- [ ] Confirm physical nozzle installed per tool.",
        "- [ ] Confirm tool offsets for every physical tool.",
        "- [ ] Confirm Z offsets for every physical tool.",
        "- [ ] Confirm purge/wipe behavior with non-printing dry-run first.",
        "- [ ] Confirm material/nozzle compatibility.",
        "- [ ] Avoid 0.2 mm nozzles with PETG-CF, PETG-GF, Wood, or TPU.",
        "- [ ] Confirm Fluidd path only.",
        "- [ ] Confirm touchscreen path remains blocked.",
        "- [ ] Confirm no production print is attempted from this sandbox.",
        "- [ ] Confirm emergency stop access.",
        "- [ ] Confirm first hardware test is air/dry-run or non-extruding.",
    ]


def generate_safety_report() -> list[str]:
    return [
        "# AMP Fluidd/Klipper Sandbox Safety Report",
        "",
        "## Status",
        "",
        "- Sandbox output only.",
        "- Macro templates are disabled/dry-run placeholders.",
        "- Dry-run schedule is comments-only plus commented RESPOND examples.",
        "- No production mixed-nozzle G-code is generated.",
        "- Snapmaker touchscreen path remains blocked.",
        "",
        "## Non-Claims",
        "",
        "- This does not implement mixed-nozzle slicing.",
        "- This does not flash or modify printer firmware.",
        "- This does not generate production T0/T1/T2/T3 commands.",
        "- This does not generate a single mixed-nozzle G-code print.",
        "- This does not validate physical mixed-nozzle behavior.",
        "- This does not bypass Snapmaker touchscreen nozzle validation.",
    ]


def generate(packet_dir: Path, out_dir: Path) -> dict[str, Any]:
    schedule, assignments = load_packet(packet_dir)
    tool_map = build_tool_map(schedule, assignments)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_text(out_dir / "amp_tools.cfg.template", generate_tools_cfg(tool_map))
    write_text(out_dir / "amp_macros.cfg.template", generate_macros_cfg())
    write_text(out_dir / "amp_dry_run_schedule.gcode.txt", generate_dry_run_schedule(schedule))
    write_text(out_dir / "amp_preflight_checklist.md", generate_preflight_checklist())
    write_text(out_dir / "amp_safety_report.md", generate_safety_report())
    write_json(out_dir / "amp_tool_map.json", {"schema_version": "0.1", "tool_map": tool_map})
    return {"out_dir": str(out_dir), "tool_count": len(tool_map), "step_count": len(schedule.get("schedule", []))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="AMP plan packet directory")
    parser.add_argument("--out", required=True, help="Sandbox output directory")
    args = parser.parse_args()
    result = generate(Path(args.packet), Path(args.out))
    print(f"wrote AMP Fluidd/Klipper sandbox to {result['out_dir']}")
    print(f"tool_count={result['tool_count']} step_count={result['step_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
