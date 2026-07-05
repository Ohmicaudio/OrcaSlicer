#!/usr/bin/env python3
"""Validate an AMP offline advisory plan packet.

The validator checks packet shape, cross-file region consistency, safety
guardrails, and common invalid tool/line-type combinations. It does not inspect
or modify slicer behavior.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "plan.json",
    "regions.json",
    "resolution_field.json",
    "tool_assignments.json",
    "process_queue.json",
    "toolchange_schedule.json",
    "per_region_gcode_status.json",
    "risk_report.md",
    "debug_artifact.json",
]

REQUIRED_PLAN_FIELDS = [
    "packet_version",
    "created_by",
    "target_platform",
    "touchscreen_mixed_nozzle_blocked",
    "fluidd_experimental_future_possible",
    "non_claims",
]

SAFE_GCODE_STATUS = {"present", "missing", "unknown"}
SENSITIVE_08_LINE_TYPES = {"top_surface", "painted_surface", "color_detail_skin", "support_interface", "bridge", "overhang"}
PHYSICAL_VALIDATION_CLAIMS = [
    "physical mixed-nozzle validated",
    "validated physical mixed-nozzle",
    "production mixed-nozzle g-code",
    "production mixed nozzle g-code",
    "mixed-nozzle slicing implemented",
    "mixed nozzle slicing implemented",
]


@dataclass
class Finding:
    level: str
    code: str
    message: str


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add(findings: list[Finding], level: str, code: str, message: str) -> None:
    findings.append(Finding(level, code, message))


def rows_by_region(payload: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    rows = payload.get(key, [])
    if not isinstance(rows, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("region_name"):
            result[str(row["region_name"])] = row
    return result


def risk_flags_from(row: dict[str, Any]) -> list[str]:
    flags = row.get("risk_flags", [])
    if isinstance(flags, list):
        return [str(item) for item in flags]
    if isinstance(flags, str):
        return [item.strip() for item in flags.split(";") if item.strip()]
    return []


def text_contains_claim(packet_dir: Path) -> list[str]:
    matches: list[str] = []
    for name in REQUIRED_FILES:
        path = packet_dir / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in PHYSICAL_VALIDATION_CLAIMS:
            if phrase in text:
                matches.append(f"{name}: {phrase}")
    return matches


def validate(packet_dir: Path) -> dict[str, Any]:
    findings: list[Finding] = []
    payloads: dict[str, Any] = {}

    for name in REQUIRED_FILES:
        path = packet_dir / name
        if not path.exists():
            add(findings, "error", "missing_required_file", f"missing {name}")
            continue
        if path.suffix == ".json":
            try:
                payloads[name] = read_json(path)
            except json.JSONDecodeError as exc:
                add(findings, "error", "invalid_json", f"{name}: {exc}")

    plan = payloads.get("plan.json", {})
    if isinstance(plan, dict):
        for field in REQUIRED_PLAN_FIELDS:
            if field not in plan:
                add(findings, "error", "missing_plan_field", f"plan.json missing {field}")
        if plan.get("touchscreen_mixed_nozzle_blocked") is not True:
            add(findings, "error", "touchscreen_block_not_true", "touchscreen_mixed_nozzle_blocked must be true")
        if not isinstance(plan.get("non_claims"), list) or not plan.get("non_claims"):
            add(findings, "error", "missing_non_claims", "plan.json must include non_claims list")
    elif "plan.json" in payloads:
        add(findings, "error", "invalid_plan_payload", "plan.json must contain an object")

    regions = rows_by_region(payloads.get("regions.json", {}), "regions")
    resolution = rows_by_region(payloads.get("resolution_field.json", {}), "resolution_field")
    assignments = rows_by_region(payloads.get("tool_assignments.json", {}), "tool_assignments")
    process = rows_by_region(payloads.get("process_queue.json", {}), "process_queue")
    gcode = rows_by_region(payloads.get("per_region_gcode_status.json", {}), "per_region_gcode_status")
    schedule_rows = rows_by_region({"schedule": payloads.get("toolchange_schedule.json", {}).get("schedule", [])}, "schedule")
    debug_entries = rows_by_region({"entries": payloads.get("debug_artifact.json", {}).get("entries", [])}, "entries")

    for name, region in regions.items():
        if name not in resolution:
            add(findings, "error", "missing_resolution_entry", f"{name} has no resolution field entry")
        if name not in assignments:
            add(findings, "error", "missing_tool_assignment", f"{name} has no tool assignment")
        if name not in process:
            add(findings, "error", "missing_process_queue_entry", f"{name} has no process queue entry")
        if name not in schedule_rows:
            unscheduled = region.get("unscheduled_reason") or assignments.get(name, {}).get("unscheduled_reason")
            if not unscheduled:
                add(findings, "error", "missing_schedule_entry", f"{name} has no schedule entry or unscheduled reason")
        if name not in gcode:
            add(findings, "error", "missing_gcode_status", f"{name} has no G-code status row")
        else:
            status = str(gcode[name].get("gcode_status", ""))
            if status not in SAFE_GCODE_STATUS:
                add(findings, "error", "invalid_gcode_status", f"{name} G-code status is {status!r}")
        assignment = assignments.get(name, {})
        process_row = process.get(name, {})
        if not assignment.get("fallback_tool_class"):
            add(findings, "error", "missing_fallback_tool", f"{name} has no fallback tool class")
        if not process_row.get("fallback_process_profile"):
            add(findings, "error", "missing_fallback_profile", f"{name} has no fallback process profile")
        if not risk_flags_from(region) and not risk_flags_from(assignment) and not risk_flags_from(process_row):
            add(findings, "warning", "missing_risk_flags", f"{name} has no risk flags list")

        metadata = region.get("metadata", {}) if isinstance(region.get("metadata"), dict) else {}
        tool = str(assignment.get("recommended_tool_class", process_row.get("recommended_tool_class", "")))
        material = str(metadata.get("material_risk", "")).lower()
        line_type = str(region.get("line_type", metadata.get("line_type", "")))
        role = str(region.get("line_role_visibility", metadata.get("line_role_visibility", "")))
        visibility = str(region.get("visibility", metadata.get("visibility", "")))

        if tool == "0.2" and material in {"clog_risk", "abrasive", "flexible"}:
            add(findings, "error", "unsafe_0p2_material", f"{name} requests 0.2 with material risk {material}")
        if tool == "0.8" and (line_type in SENSITIVE_08_LINE_TYPES or role in {"cosmetic", "mating"} or visibility == "visible"):
            add(findings, "error", "unsafe_0p8_sensitive_line_type", f"{name} requests 0.8 for sensitive line type/visibility")

    for name, entry in debug_entries.items():
        if name not in regions:
            add(findings, "warning", "debug_entry_without_region", f"debug artifact entry {name} has no matching region")
        if entry.get("source_stage") not in {"offline_plan_packet", "stock_fallback", "no_op_planner", "future_observation"}:
            add(findings, "warning", "unknown_debug_source_stage", f"{name} has source_stage {entry.get('source_stage')!r}")

    for claim in text_contains_claim(packet_dir):
        add(findings, "error", "unsafe_claim", claim)

    debug = payloads.get("debug_artifact.json", {})
    if isinstance(debug, dict):
        if debug.get("generation_mode") != "offline_advisory":
            add(findings, "warning", "unexpected_debug_generation_mode", "debug artifact generation_mode should be offline_advisory")
        if debug.get("touchscreen_mixed_nozzle_blocked") is not True:
            add(findings, "error", "debug_touchscreen_block_not_true", "debug artifact must preserve touchscreen block")

    error_count = sum(1 for finding in findings if finding.level == "error")
    warning_count = sum(1 for finding in findings if finding.level == "warning")
    return {
        "packet": str(packet_dir).replace("\\", "/"),
        "passed": error_count == 0,
        "error_count": error_count,
        "warning_count": warning_count,
        "region_count": len(regions),
        "findings": [asdict(finding) for finding in findings],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")


def markdown_for(result: dict[str, Any]) -> str:
    lines = [
        "# AMP Plan Packet Validation Report",
        "",
        f"Packet: `{result['packet']}`",
        "",
        f"Passed: `{result['passed']}`",
        f"Errors: `{result['error_count']}`",
        f"Warnings: `{result['warning_count']}`",
        f"Regions: `{result['region_count']}`",
        "",
        "| Level | Code | Message |",
        "| --- | --- | --- |",
    ]
    findings = result.get("findings", [])
    if findings:
        for finding in findings:
            lines.append(f"| {finding['level']} | `{finding['code']}` | {finding['message']} |")
    else:
        lines.append("| info | `no_findings` | No validation findings. |")
    lines.extend(
        [
            "",
            "This validator is offline/advisory only. It does not implement mixed-nozzle slicing or production T-code emission.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="AMP packet directory")
    parser.add_argument("--out", required=True, help="JSON validation report path")
    parser.add_argument("--markdown", required=True, help="Markdown validation report path")
    args = parser.parse_args()

    result = validate(Path(args.packet))
    write_json(Path(args.out), result)
    Path(args.markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(args.markdown).write_text(markdown_for(result), encoding="utf-8", newline="\n")
    print(f"packet: {result['packet']}")
    print(f"passed: {result['passed']}")
    print(f"errors: {result['error_count']}")
    print(f"warnings: {result['warning_count']}")
    for finding in result["findings"]:
        print(f"{finding['level']}: {finding['code']}: {finding['message']}")
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
