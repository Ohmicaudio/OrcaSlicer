#!/usr/bin/env python3
"""Emit adapter-specific comments-only pseudo execution plans from an AMP packet.

The generated pseudo G-code is intentionally not printable. It is an advisory
developer artifact for comparing firmware/controller execution models.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def load_adapter(manifest_path: Path, adapter_id: str) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    adapters = manifest.get("adapters", [])
    if not isinstance(adapters, list):
        raise ValueError("adapter manifest must contain an adapters array")

    for adapter in adapters:
        if isinstance(adapter, dict) and adapter.get("adapter_id") == adapter_id:
            return adapter
    raise ValueError(f"adapter_id not found in manifest: {adapter_id}")


def load_packet(packet_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    schedule_path = packet_dir / "toolchange_schedule.json"
    if not schedule_path.exists():
        raise FileNotFoundError(f"missing {schedule_path}")

    plan_path = packet_dir / "plan.json"
    plan = read_json(plan_path) if plan_path.exists() else {}
    schedule = read_json(schedule_path)
    if not isinstance(schedule.get("schedule", []), list):
        raise ValueError("toolchange_schedule.json does not contain a schedule array")
    return plan, schedule


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def pseudo_command_lines(adapter: dict[str, Any], step: dict[str, Any]) -> list[str]:
    tool_class = str(step.get("tool_class", "unknown"))
    tool_map = adapter.get("tool_map", {})
    tool = tool_map.get(tool_class, {})
    tool_id = str(tool.get("tool_id", f"T?_{tool_class}"))
    macro_name = str(tool.get("macro_name", f"AMP_PICK_TOOL_{tool_class.replace('.', 'P')}"))
    rrf_tpre = str(tool.get("rrf_tpre", f"tpre{tool_id.replace('T', '')}.g"))
    offset = tool.get("offset", {})

    style = adapter.get("command_style", "comments_only")
    lines = [f"; WOULD_SELECT_TOOL {tool_id} for nozzle_class={tool_class}"]

    if style in {"klipper_macro", "snapmaker_fluidd_klipper"}:
        lines.extend(
            [
                f"; WOULD_RUN_KLIPPER_MACRO {macro_name} NOZZLE={tool_class} REGION=\"{step.get('region_name', '')}\"",
                f"; WOULD_SAVE_STATE {adapter.get('state_save_command', 'SAVE_GCODE_STATE NAME=amp_toolchange')}",
                f"; WOULD_APPLY_OFFSET X={offset.get('x', 'unknown')} Y={offset.get('y', 'unknown')} Z={offset.get('z', 'unknown')}",
                f"; WOULD_PURGE_OR_WIPE {adapter.get('purge_wipe_macro', 'AMP_PURGE_OR_WIPE')}",
                f"; WOULD_RESTORE_STATE {adapter.get('state_restore_command', 'RESTORE_GCODE_STATE NAME=amp_toolchange')}",
            ]
        )
    elif style == "klipper_ktcc":
        lines.extend(
            [
                f"; WOULD_RUN_KTCC_TOOL {tool_id} NOZZLE={tool_class}",
                f"; WOULD_USE_KTCC_TOOL_OBJECT {tool.get('ktcc_tool_name', tool_id)}",
                f"; WOULD_PARK_TOOL {adapter.get('parking_model', 'ktcc_tool_parking')}",
                f"; WOULD_SET_TOOL_HEATER_STATE {adapter.get('heater_model', 'active_standby_off')}",
                f"; WOULD_PURGE_OR_WIPE {adapter.get('purge_wipe_macro', 'KTCC_TOOLCHANGE_PURGE')}",
            ]
        )
    elif style == "reprap_firmware":
        tool_number = tool_id.replace("T", "")
        lines.extend(
            [
                f"; WOULD_RUN_RRF_TFREE tfree{tool_number}.g",
                f"; WOULD_RUN_RRF_TPRE {rrf_tpre}",
                f"; WOULD_RUN_RRF_TPOST tpost{tool_number}.g",
                f"; WOULD_APPLY_RRF_G10_OFFSET X={offset.get('x', 'unknown')} Y={offset.get('y', 'unknown')} Z={offset.get('z', 'unknown')}",
            ]
        )
    elif style == "blocked":
        lines.extend(
            [
                "; BLOCKED_ADAPTER touchscreen-started mixed-nozzle execution is advisory only",
                f"; WOULD_FALL_BACK_TO {step.get('fallback_if_rejected', 'single-authoritative-nozzle workflow')}",
            ]
        )
    else:
        lines.append(f"; WOULD_USE_ADAPTER_STYLE {style}")

    return lines


def emit(packet_dir: Path, manifest_path: Path, adapter_id: str, out_root: Path) -> dict[str, Any]:
    adapter = load_adapter(manifest_path, adapter_id)
    plan, schedule = load_packet(packet_dir)
    out_dir = out_root / adapter_id
    steps = schedule.get("schedule", [])

    safety_warnings = as_list(adapter.get("safety_warnings"))
    if adapter.get("touchscreen_safe") is False:
        safety_warnings.append("Adapter is not touchscreen-safe for mixed physical nozzle execution.")
    if adapter.get("requires_hardware_validation") is True:
        safety_warnings.append("Hardware validation is required before any executable emission can be considered.")

    adapter_plan = {
        "schema_version": "0.1",
        "adapter_id": adapter_id,
        "adapter_name": adapter.get("adapter_name", ""),
        "target_controller": adapter.get("target_controller", ""),
        "packet_dir": str(packet_dir).replace("\\", "/"),
        "packet_version": plan.get("packet_version", ""),
        "comments_only": True,
        "production_gcode": False,
        "schedule": steps,
        "safety_warnings": safety_warnings,
    }

    schedule_lines = [
        f"# AMP Firmware Adapter Pseudo Schedule: {adapter_id}",
        "",
        "This is a comments-only advisory execution plan. It is not printable G-code.",
        "",
        f"- Adapter: `{adapter.get('adapter_name', adapter_id)}`",
        f"- Target controller: `{adapter.get('target_controller', '')}`",
        f"- Command style: `{adapter.get('command_style', '')}`",
        f"- Touchscreen safe: `{str(adapter.get('touchscreen_safe', False)).lower()}`",
        f"- Fluidd only: `{str(adapter.get('fluidd_only', False)).lower()}`",
        f"- Requires hardware validation: `{str(adapter.get('requires_hardware_validation', True)).lower()}`",
        f"- Toolchange count: `{schedule.get('toolchange_count', '')}`",
        "",
        "## Steps",
        "",
    ]
    for step in steps:
        schedule_lines.extend(
            [
                f"### Step {step.get('step_index', '')}: {step.get('region_name', '')}",
                "",
                f"- Tool class: `{step.get('tool_class', '')}`",
                f"- Process profile: `{step.get('selected_process_profile', '')}`",
                f"- Layer height: `{step.get('selected_layer_height_mm', '')}`",
                f"- Line width class: `{step.get('selected_line_width_class', '')}`",
                f"- Requires toolchange: `{str(step.get('requires_toolchange', '')).lower()}`",
                f"- Reason: {step.get('reason', '')}",
                "",
            ]
        )

    pseudo_lines = [
        "; PSEUDO ONLY - NOT PRINTABLE",
        "; AMP firmware/controller adapter advisory output",
        "; This does not implement mixed-nozzle slicing",
        "; This does not generate production T0/T1/T2/T3 commands",
        "; This does not validate physical mixed-nozzle behavior",
        f"; adapter_id={adapter_id}",
        f"; target_controller={adapter.get('target_controller', '')}",
        f"; packet={str(packet_dir).replace(chr(92), '/')}",
        "",
    ]
    for warning in safety_warnings:
        pseudo_lines.append(f"; SAFETY_WARNING {warning}")
    pseudo_lines.append("")

    for step in steps:
        pseudo_lines.extend(
            [
                f"; STEP {step.get('step_index', '')}",
                f"; region={step.get('region_name', '')}",
                f"; line_type={step.get('line_type', '')}",
                f"; visibility={step.get('visibility', '')}",
                f"; intended_tool_class={step.get('tool_class', '')}",
                f"; selected_process_profile={step.get('selected_process_profile', '')}",
                f"; selected_layer_height_mm={step.get('selected_layer_height_mm', '')}",
                f"; selected_line_width_class={step.get('selected_line_width_class', '')}",
                f"; requires_toolchange={str(step.get('requires_toolchange', '')).lower()}",
                f"; reason={step.get('reason', '')}",
            ]
        )
        pseudo_lines.extend(pseudo_command_lines(adapter, step))
        pseudo_lines.append("")

    safety_lines = [
        f"# AMP Firmware Adapter Safety Report: {adapter_id}",
        "",
        "## Status",
        "",
        f"- Comments-only output: `{str(adapter_plan['comments_only']).lower()}`",
        f"- Production G-code: `{str(adapter_plan['production_gcode']).lower()}`",
        f"- Touchscreen safe: `{str(adapter.get('touchscreen_safe', False)).lower()}`",
        f"- Fluidd only: `{str(adapter.get('fluidd_only', False)).lower()}`",
        f"- Requires hardware validation: `{str(adapter.get('requires_hardware_validation', True)).lower()}`",
        "",
        "## Warnings",
        "",
    ]
    safety_lines.extend([f"- {warning}" for warning in safety_warnings] or ["- No adapter-specific warnings recorded."])
    safety_lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not implement mixed-nozzle slicing.",
            "- This does not flash or modify printer firmware.",
            "- This does not generate production tool-selection commands.",
            "- This does not generate a single mixed-nozzle G-code print.",
            "- This does not validate physical mixed-nozzle behavior.",
            "- This does not alter Snapmaker touchscreen nozzle validation.",
        ]
    )

    write_json(out_dir / "adapter_plan.json", adapter_plan)
    write_text(out_dir / "schedule.md", schedule_lines)
    write_text(out_dir / "pseudo.gcode.txt", pseudo_lines)
    write_text(out_dir / "safety_report.md", safety_lines)
    return adapter_plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="AMP plan packet directory")
    parser.add_argument("--manifests", required=True, help="Adapter manifest JSON")
    parser.add_argument("--adapter-id", required=True, help="Adapter id to emit")
    parser.add_argument("--out", required=True, help="Output root directory")
    args = parser.parse_args()

    plan = emit(Path(args.packet), Path(args.manifests), args.adapter_id, Path(args.out))
    print(f"wrote comments-only pseudo output for {plan['adapter_id']} to {Path(args.out) / args.adapter_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
