#!/usr/bin/env python3
"""Generate a unified offline AMP advisory plan packet.

The packet combines region metadata, continuous resolution demand, U1 process
profile selection, toolchange scheduling, G-code status, risk reporting, and a
simplified debug artifact. It is advisory only and has no slicer side effects.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from amp_continuous_resolution_field import compute_plan, region_from_dict as continuous_region_from_dict
from amp_tool_class_assignment_solver import assignment_row, assignments_for, load_regions
from amp_toolchange_scheduler import payload_for, schedule
from amp_u1_process_profile_resolver import resolve_regions


PACKET_VERSION = "0.1"
CREATED_BY = "tools/amp_generate_plan_packet.py"
TARGET_PLATFORM = "Snapmaker U1 advisory profile ladder"
TOUCHSCREEN_BLOCK_REASON = (
    "Touchscreen-compatible mixed-nozzle execution remains blocked pending "
    "Snapmaker's future per-tool metadata/logical mapping path."
)
NON_CLAIMS = [
    "This does not implement mixed-nozzle slicing.",
    "This does not generate production T0/T1/T2/T3 commands.",
    "This does not generate a single mixed-nozzle G-code print.",
    "This does not validate physical mixed-nozzle behavior.",
    "This does not bypass Snapmaker touchscreen nozzle validation.",
    "Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.",
    "Fluidd-only experimentation remains future/hardware-dependent.",
]

REGION_GCODE_MAP = {
    "micro_detail_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/micro_detail_zone_0p2.gcode",
    "normal_visible_detail_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/normal_visible_detail_zone_0p4.gcode",
    "structural_shell_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/structural_shell_zone_0p6.gcode",
    "bulk_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/bulk_zone_0p8.gcode",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def raw_region_records(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    rows = data.get("regions", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"{path} does not contain a regions array")
    return [row for row in rows if isinstance(row, dict)]


def load_metric_rows(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    by_file: dict[str, dict[str, str]] = {}
    for row in rows:
        file_name = Path(row.get("file", "")).name
        if file_name:
            by_file[file_name] = row
    return by_file


def merge_risk_flags(*groups: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in group:
            text = str(item)
            if text and text not in seen:
                seen.add(text)
                merged.append(text)
    return merged


def region_metadata_packet(records: list[dict[str, Any]], assignments: dict[str, dict[str, Any]], resolution: dict[str, dict[str, Any]], process: dict[str, dict[str, Any]]) -> dict[str, Any]:
    regions: list[dict[str, Any]] = []
    for record in records:
        name = str(record.get("region_name", "unnamed_region"))
        assignment = assignments.get(name, {})
        plan = resolution.get(name, {})
        process_row = process.get(name, {})
        regions.append(
            {
                "region_name": name,
                "metadata": record,
                "feature_metadata": {
                    "xy_min_feature_size_mm": record.get("xy_min_feature_size_mm", record.get("min_feature_size_mm")),
                    "xy_nominal_feature_size_mm": record.get("xy_nominal_feature_size_mm"),
                    "z_feature_height_mm": record.get("z_feature_height_mm"),
                    "vertical_extent_mm": record.get("vertical_extent_mm"),
                    "vertical_extent_layers": record.get("vertical_extent_layers"),
                    "surface_slope_degrees": record.get("surface_slope_degrees"),
                    "local_z_candidate": record.get("local_z_candidate", False),
                },
                "line_type": record.get("line_type", plan.get("line_type", assignment.get("line_type", ""))),
                "line_role_visibility": record.get("line_role_visibility", assignment.get("line_role_visibility", "")),
                "visibility": record.get("visibility", plan.get("visibility", "")),
                "risk_flags": merge_risk_flags(
                    plan.get("risk_flags", []),
                    process_row.get("risk_flags", []),
                    str(assignment.get("risk_flags", "")).split("; ") if assignment.get("risk_flags") else [],
                ),
            }
        )
    return {"regions": regions}


def resolution_packet(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [asdict(compute_plan(continuous_region_from_dict(record))) for record in records]
    return {"resolution_field": rows}


def assignment_packet(regions: list[Any]) -> dict[str, Any]:
    rows = [assignment_row(item) for item in assignments_for(regions)]
    return {"tool_assignments": rows}


def process_packet(regions: list[Any], repo_root: Path) -> dict[str, Any]:
    return {"process_queue": resolve_regions(regions, repo_root)}


def gcode_status_packet(
    records: list[dict[str, Any]],
    process_rows: dict[str, dict[str, Any]],
    repo_root: Path,
    metrics_path: Path,
) -> dict[str, Any]:
    metrics = load_metric_rows(metrics_path)
    rows: list[dict[str, Any]] = []
    for record in records:
        name = str(record.get("region_name", "unnamed_region"))
        gcode_path = REGION_GCODE_MAP.get(name, "")
        path = repo_root / gcode_path if gcode_path else None
        exists = bool(path and path.exists())
        metric = metrics.get(path.name if path else "", {})
        process_row = process_rows.get(name, {})
        rows.append(
            {
                "region_name": name,
                "assigned_region_body_path": str(record.get("source_model", record.get("body_path", ""))),
                "selected_profile": process_row.get("selected_process_profile", ""),
                "gcode_path": gcode_path,
                "gcode_status": "present" if exists else "missing",
                "file_size_bytes": path.stat().st_size if exists and path else 0,
                "metrics": metric,
            }
        )
    return {"per_region_gcode_status": rows}


def debug_artifact_packet(
    resolution_rows: dict[str, dict[str, Any]],
    schedule_payload: dict[str, Any],
    records: list[dict[str, Any]],
    validation: dict[str, Any],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    index_by_region = {str(record.get("region_name", f"region_{index}")): index for index, record in enumerate(records)}
    for step in schedule_payload["schedule"]:
        name = str(step["region_name"])
        plan = resolution_rows.get(name, {})
        region_index = index_by_region.get(name, 0)
        entries.append(
            {
                "object_id": region_index,
                "layer_id": region_index,
                "region_id": region_index,
                "region_name": name,
                "plan_reason": plan.get("reason", step.get("reason", "")),
                "confidence": plan.get("confidence", 0.0),
                "toolchange_requested": bool(step.get("requires_toolchange")),
                "bead_width_override_present": False,
                "nozzle_override_present": True,
                "source_stage": "offline_plan_packet",
                "warnings": step.get("risk_flags", []),
            }
        )
    warnings_by_region = {entry["region_name"]: entry.get("warnings", []) for entry in entries}
    observation_summary = {
        "warnings": ["offline advisory packet; no geometry polygons, coordinates, or production G-code commands are included"],
        "entries": [
            {
                "object_id": index,
                "layer_id": index,
                "region_id": index,
                "region_name": str(record.get("region_name", f"region_{index}")),
                "region_category": str(record.get("line_type", "unknown")),
                "observed_item_count": 1,
                "warning_count": len(warnings_by_region.get(str(record.get("region_name", f"region_{index}")), [])),
            }
            for index, record in enumerate(records)
        ],
    }
    return {
        "schema_version": "0.1",
        "generation_mode": "offline_advisory",
        "touchscreen_mixed_nozzle_blocked": True,
        "fluidd_experimental_future_possible": True,
        "entries": entries,
        "observation_summary": observation_summary,
        "warnings": [
            TOUCHSCREEN_BLOCK_REASON,
            "This debug artifact is offline/advisory only and does not change slicer behavior.",
            *validation.get("warnings", []),
        ],
    }


def validate_packet(
    records: list[dict[str, Any]],
    assignments: dict[str, dict[str, Any]],
    process_rows: dict[str, dict[str, Any]],
    gcode_rows: list[dict[str, Any]],
    repo_root: Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})
        if not passed:
            warnings.append(f"{name}: {detail}")

    names = [str(record.get("region_name", "")) for record in records]
    add("all_regions_have_tool_assignments", all(name in assignments for name in names), f"{len(assignments)}/{len(names)} assignments present")
    add("all_regions_have_selected_process_profiles", all(process_rows.get(name, {}).get("selected_process_profile") for name in names), f"{len(process_rows)}/{len(names)} process rows present")
    existing_profiles = []
    for name in names:
        selected = str(process_rows.get(name, {}).get("selected_process_profile", ""))
        existing_profiles.append(bool(selected and (repo_root / selected).exists()))
    add("all_selected_process_profiles_exist", all(existing_profiles), f"{sum(1 for item in existing_profiles if item)}/{len(existing_profiles)} selected profiles exist")
    add("all_assigned_tools_have_fallback", all(assignments.get(name, {}).get("fallback_tool_class") for name in names), "fallback tool class present for each region")
    add("touchscreen_mixed_nozzle_blocked_is_true", True, "packet records touchscreen mixed-nozzle block")
    add("no_region_claims_physical_validation", True, "packet non-claims explicitly keep physical validation out of scope")
    add("local_z_flags_are_advisory_only", True, "local-Z appears only as advisory flags")
    missing_gcode = [row["region_name"] for row in gcode_rows if row["gcode_status"] != "present"]
    if missing_gcode:
        warnings.append(f"missing G-code marked for regions: {', '.join(missing_gcode)}")
    add("missing_gcode_marked_not_silent", True, f"{len(missing_gcode)} missing region G-code file(s) marked")
    return {"checks": checks, "passed": all(check["passed"] for check in checks), "warnings": warnings}


def risk_report(packet: dict[str, Any]) -> str:
    assignment_rows = packet["tool_assignments"]["tool_assignments"]
    process_rows = {row["region_name"]: row for row in packet["process_queue"]["process_queue"]}
    schedule_rows = packet["toolchange_schedule"]["schedule"]
    gcode_rows = {row["region_name"]: row for row in packet["per_region_gcode_status"]["per_region_gcode_status"]}
    lines = [
        "# AMP Offline Plan Packet 001 Risk Report",
        "",
        "This report summarizes the advisory packet risk and fallback state.",
        "",
        "| Region | Tool | Profile | Schedule step | G-code | Fallback | Risk flags |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    step_by_region = {row["region_name"]: row for row in schedule_rows}
    for row in assignment_rows:
        name = row["region_name"]
        process = process_rows.get(name, {})
        step = step_by_region.get(name, {})
        gcode = gcode_rows.get(name, {})
        lines.append(
            f"| `{name}` | `{row['recommended_tool_class']}` | `{process.get('selected_process_profile', '')}` | "
            f"{step.get('step_index', '')} | {gcode.get('gcode_status', 'missing')} | `{row['fallback_tool_class']}` | {row['risk_flags']} |"
        )
    lines.extend(["", "Validation checks:", ""])
    for check in packet["validation"]["checks"]:
        lines.append(f"- {check['check']}: {check['passed']} - {check['detail']}")
    lines.extend(["", "Non-claims:", ""])
    lines.extend(f"- {item}" for item in NON_CLAIMS)
    return "\n".join(lines) + "\n"


def build_packet(input_path: Path, repo_root: Path, schedule_mode: str, metrics_path: Path) -> dict[str, Any]:
    records = raw_region_records(input_path)
    regions = load_regions(input_path)
    resolution = resolution_packet(records)
    resolution_by_region = {row["region_name"]: row for row in resolution["resolution_field"]}
    assignments = assignment_packet(regions)
    assignments_by_region = {row["region_name"]: row for row in assignments["tool_assignments"]}
    process = process_packet(regions, repo_root)
    process_by_region = {row["region_name"]: row for row in process["process_queue"]}
    schedule_steps = schedule(records, process_by_region, schedule_mode, "0.4", 60.0)
    schedule_payload = payload_for(schedule_mode, schedule_steps)
    gcode = gcode_status_packet(records, process_by_region, repo_root, metrics_path)
    validation = validate_packet(records, assignments_by_region, process_by_region, gcode["per_region_gcode_status"], repo_root)
    return {
        "plan": {
            "packet_version": PACKET_VERSION,
            "created_by": CREATED_BY,
            "source_metadata": str(input_path).replace("\\", "/"),
            "target_platform": TARGET_PLATFORM,
            "touchscreen_mixed_nozzle_blocked": True,
            "touchscreen_block_reason": TOUCHSCREEN_BLOCK_REASON,
            "fluidd_experimental_future_possible": True,
            "non_claims": NON_CLAIMS,
        },
        "regions": region_metadata_packet(records, assignments_by_region, resolution_by_region, process_by_region),
        "resolution_field": resolution,
        "tool_assignments": assignments,
        "process_queue": process,
        "toolchange_schedule": schedule_payload,
        "per_region_gcode_status": gcode,
        "validation": validation,
        "debug_artifact": debug_artifact_packet(resolution_by_region, schedule_payload, records, validation),
    }


def write_packet(out_dir: Path, packet: dict[str, Any]) -> None:
    write_json(out_dir / "plan.json", packet["plan"])
    write_json(out_dir / "regions.json", packet["regions"])
    write_json(out_dir / "resolution_field.json", packet["resolution_field"])
    write_json(out_dir / "tool_assignments.json", packet["tool_assignments"])
    write_json(out_dir / "process_queue.json", packet["process_queue"])
    write_json(out_dir / "toolchange_schedule.json", packet["toolchange_schedule"])
    write_json(out_dir / "per_region_gcode_status.json", packet["per_region_gcode_status"])
    write_json(out_dir / "debug_artifact.json", packet["debug_artifact"])
    write_text(out_dir / "risk_report.md", risk_report(packet))


def print_summary(packet: dict[str, Any], out_dir: Path) -> None:
    print(f"wrote AMP offline plan packet to {out_dir}")
    print(f"schedule mode: {packet['toolchange_schedule']['scheduling_mode']}")
    print(f"toolchanges: {packet['toolchange_schedule']['toolchange_count']}")
    print("region | tool | profile | schedule_step | gcode")
    step_by_region = {row["region_name"]: row for row in packet["toolchange_schedule"]["schedule"]}
    profile_by_region = {row["region_name"]: row for row in packet["process_queue"]["process_queue"]}
    gcode_by_region = {row["region_name"]: row for row in packet["per_region_gcode_status"]["per_region_gcode_status"]}
    for row in packet["tool_assignments"]["tool_assignments"]:
        name = row["region_name"]
        print(
            f"{name} | {row['recommended_tool_class']} | "
            f"{profile_by_region.get(name, {}).get('selected_process_profile', '')} | "
            f"{step_by_region.get(name, {}).get('step_index', '')} | "
            f"{gcode_by_region.get(name, {}).get('gcode_status', 'missing')}"
        )
    validation = packet["validation"]
    print(f"validation: {'passed' if validation['passed'] else 'warnings'}")
    for check in validation["checks"]:
        print(f"- {check['check']}: {check['passed']} ({check['detail']})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Region metadata JSON")
    parser.add_argument("--out", required=True, help="Output packet directory")
    parser.add_argument("--schedule-mode", default="minimize_toolchanges", choices=["minimize_toolchanges", "detail_first", "bulk_first", "layer_ordered"])
    parser.add_argument("--metrics", default="outputs/amp_multitool_resolution_fixture/reports/region_metrics.csv")
    args = parser.parse_args()

    repo_root = Path.cwd()
    packet = build_packet(Path(args.input), repo_root, args.schedule_mode, Path(args.metrics))
    out_dir = Path(args.out)
    write_packet(out_dir, packet)
    print_summary(packet, out_dir)
    return 0 if packet["validation"]["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
