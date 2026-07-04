#!/usr/bin/env python3
"""Generate an offline AMP multi-tool planning bundle."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from amp_tool_class_assignment_solver import assignment_row, assignments_for, load_regions
from amp_u1_process_profile_resolver import resolve_regions


PROFILE_MAP: Dict[str, Dict[str, str]] = {
    "0.2": {
        "process_profile": "resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json",
        "filament_profile": "resources/profiles/Snapmaker/filament/Generic PLA @U1 0.2 nozzle.json",
        "gcode": "outputs/amp_multitool_resolution_fixture/region_gcode/micro_detail_zone_0p2.gcode",
    },
    "0.4": {
        "process_profile": "resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json",
        "filament_profile": "resources/profiles/Snapmaker/filament/Snapmaker PLA Translucent @U1 0.4 nozzle.json",
        "gcode": "outputs/amp_multitool_resolution_fixture/region_gcode/normal_visible_detail_zone_0p4.gcode",
    },
    "0.6": {
        "process_profile": "resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json",
        "filament_profile": "resources/profiles/Snapmaker/filament/Generic PLA @U1 0.6 nozzle.json",
        "gcode": "outputs/amp_multitool_resolution_fixture/region_gcode/structural_shell_zone_0p6.gcode",
    },
    "0.8": {
        "process_profile": "resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json",
        "filament_profile": "resources/profiles/Snapmaker/filament/Generic PLA @U1 0.8 nozzle.json",
        "gcode": "outputs/amp_multitool_resolution_fixture/region_gcode/bulk_zone_0p8.gcode",
    },
}

REGION_GCODE_MAP: Dict[str, str] = {
    "micro_detail_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/micro_detail_zone_0p2.gcode",
    "normal_visible_detail_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/normal_visible_detail_zone_0p4.gcode",
    "structural_shell_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/structural_shell_zone_0p6.gcode",
    "bulk_zone": "outputs/amp_multitool_resolution_fixture/region_gcode/bulk_zone_0p8.gcode",
}


def load_metrics(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    by_name: Dict[str, Dict[str, str]] = {}
    for row in rows:
        file_name = Path(row.get("file", "")).name
        if file_name:
            by_name[file_name] = row
    return by_name


def gcode_status(repo_root: Path, region_name: str, tool_class: str, metrics: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    relative = REGION_GCODE_MAP.get(region_name) or PROFILE_MAP.get(tool_class, {}).get("gcode", "")
    if not relative:
        return {"exists": False, "path": "", "size_bytes": 0, "metrics": {}}
    path = repo_root / relative
    exists = path.exists()
    metric = metrics.get(path.name, {})
    return {
        "exists": exists,
        "path": relative,
        "size_bytes": path.stat().st_size if exists else 0,
        "metrics": {
            "layers": metric.get("layer_count", ""),
            "extrusion_moves": metric.get("extrusion_moves", ""),
            "travel_moves": metric.get("travel_moves", ""),
            "total_positive_e": metric.get("total_positive_e", ""),
            "estimated_print_time": metric.get("estimated_print_time_comment", ""),
        } if metric else {},
    }


def plan_rows(repo_root: Path, input_path: Path, metrics_path: Path) -> List[Dict[str, object]]:
    regions = load_regions(input_path)
    assignments = assignments_for(regions)
    process_queue = resolve_regions(regions, repo_root)
    process_by_region = {str(item["region_name"]): item for item in process_queue}
    metrics = load_metrics(metrics_path)
    rows: List[Dict[str, object]] = []
    for assignment in assignments:
        row = assignment_row(assignment)
        tool_class = str(row["recommended_tool_class"])
        profile = PROFILE_MAP.get(tool_class, {})
        process_selection = process_by_region.get(str(row["region_name"]), {})
        rows.append({
            **row,
            "recommended_nozzle": tool_class if tool_class in PROFILE_MAP else "",
            "intended_process_profile": profile.get("process_profile", ""),
            "intended_filament_profile": profile.get("filament_profile", ""),
            "selected_u1_process_profile": process_selection.get("selected_process_profile", profile.get("process_profile", "")),
            "selected_layer_height_mm": process_selection.get("selected_layer_height_mm", ""),
            "selected_line_width_class": process_selection.get("selected_line_width_class", row.get("recommended_line_width_class", "")),
            "requested_layer_height_mm": process_selection.get("requested_layer_height_mm", ""),
            "process_selection_reason": process_selection.get("selection_reason", ""),
            "fallback_process_profile": process_selection.get("fallback_process_profile", ""),
            "local_z_future_required": process_selection.get("local_z_future_required", False),
            "touchscreen_mixed_nozzle_blocked": process_selection.get("touchscreen_mixed_nozzle_blocked", True),
            "gcode_status": gcode_status(repo_root, str(row["region_name"]), tool_class, metrics),
        })
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")


def write_assignment_csv(rows: Iterable[Dict[str, object]], path: Path) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "region_name",
        "recommended_tool_class",
        "recommended_nozzle",
        "recommended_layer_height_class",
        "recommended_line_width_class",
        "fallback_tool_class",
        "confidence",
        "cost_gate_passed",
        "estimated_toolchange_cost_s",
        "cost_gate_reason",
        "fallback_reason",
        "risk_flags",
        "reason",
        "intended_process_profile",
        "selected_u1_process_profile",
        "selected_layer_height_mm",
        "selected_line_width_class",
        "requested_layer_height_mm",
        "process_selection_reason",
        "fallback_process_profile",
        "local_z_future_required",
        "touchscreen_mixed_nozzle_blocked",
        "intended_filament_profile",
        "gcode_exists",
        "gcode_path",
        "gcode_size_bytes",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            status = row.get("gcode_status", {})
            if not isinstance(status, dict):
                status = {}
            writer.writerow({
                **{field: row.get(field, "") for field in fields},
                "gcode_exists": status.get("exists", False),
                "gcode_path": status.get("path", ""),
                "gcode_size_bytes": status.get("size_bytes", 0),
            })


def write_slice_queue(rows: List[Dict[str, object]], path: Path) -> None:
    queue = []
    for row in rows:
        queue.append({
            "region_name": row["region_name"],
            "tool_class": row["recommended_tool_class"],
            "process_profile": row.get("selected_u1_process_profile", row.get("intended_process_profile", "")),
            "selected_layer_height_mm": row.get("selected_layer_height_mm", ""),
            "selected_line_width_class": row.get("selected_line_width_class", ""),
            "requested_layer_height_mm": row.get("requested_layer_height_mm", ""),
            "fallback_process_profile": row.get("fallback_process_profile", ""),
            "local_z_future_required": row.get("local_z_future_required", False),
            "touchscreen_mixed_nozzle_blocked": row.get("touchscreen_mixed_nozzle_blocked", True),
            "filament_profile": row.get("intended_filament_profile", ""),
            "existing_gcode": row.get("gcode_status", {}),
        })
    write_json(path, {"slice_queue": queue})


def write_risk_report(rows: List[Dict[str, object]], path: Path) -> None:
    lines = [
        "# AMP Offline Plan Bundle 001 Risk Report",
        "",
        "This is an offline advisory report. It does not implement mixed-nozzle slicing.",
        "",
        "| Region | Tool | Cost gate | Confidence | Risk flags | Fallback | G-code |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        status = row.get("gcode_status", {})
        if not isinstance(status, dict):
            status = {}
        gcode_text = "present" if status.get("exists") else "missing"
        lines.append(
            f"| `{row['region_name']}` | `{row['recommended_tool_class']}` | {row['cost_gate_passed']} | "
            f"{row['confidence']} | {row['risk_flags']} | `{row['fallback_tool_class']}` | {gcode_text} |"
        )
    lines.extend([
        "",
        "Non-claims:",
        "",
        "- This does not implement mixed-nozzle slicing.",
        "- This does not validate physical mixed-nozzle behavior.",
        "- This does not bypass Snapmaker touchscreen nozzle validation.",
        "- Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_readme(rows: List[Dict[str, object]], path: Path) -> None:
    lines = [
        "# AMP Offline Plan Bundle 001",
        "",
        "Generated artifacts:",
        "",
        "- `plan.json`: cost-gated advisory planner output.",
        "- `slice_queue.json`: per-region intended slicer inputs and existing G-code status.",
        "- `risk_report.md`: human-readable risk/fallback summary.",
        "- `assignment_table.csv`: tabular assignment output.",
        "",
        "Region summary:",
        "",
        "| Region | Tool | G-code status |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        status = row.get("gcode_status", {})
        if not isinstance(status, dict):
            status = {}
        lines.append(f"| `{row['region_name']}` | `{row['recommended_tool_class']}` | {'present' if status.get('exists') else 'missing'} |")
    lines.extend([
        "",
        "This bundle is offline/advisory only and is not a single mixed-nozzle print job.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--metrics", default="outputs/amp_multitool_resolution_fixture/reports/region_metrics.csv")
    args = parser.parse_args()

    repo_root = Path.cwd()
    input_path = Path(args.input)
    out_dir = Path(args.out)
    rows = plan_rows(repo_root, input_path, Path(args.metrics))
    write_json(out_dir / "plan.json", {"regions": rows})
    write_slice_queue(rows, out_dir / "slice_queue.json")
    write_risk_report(rows, out_dir / "risk_report.md")
    write_assignment_csv(rows, out_dir / "assignment_table.csv")
    write_readme(rows, out_dir / "README.md")
    print(f"wrote offline plan bundle to {out_dir} with {len(rows)} region(s)")
    for row in rows:
        status = row.get("gcode_status", {})
        exists = status.get("exists") if isinstance(status, dict) else False
        print(f"{row['region_name']}: {row['recommended_tool_class']} gcode={'present' if exists else 'missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
