#!/usr/bin/env python3
"""Resolve AMP tool-class assignments to concrete Snapmaker U1 process profiles.

This is offline/advisory tooling. It does not generate mixed-nozzle G-code and
does not modify slicer behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from amp_tool_class_assignment_solver import Assignment, Region, assignments_for, load_regions


PROCESS_ROOT = Path("resources/profiles/Snapmaker/process")
TOUCHSCREEN_BLOCKED = (
    "Touchscreen-compatible mixed-nozzle execution remains blocked pending "
    "Snapmaker's future per-tool metadata/logical mapping path."
)


@dataclass(frozen=True)
class ProcessProfile:
    nozzle: str
    layer_height: float
    file_name: str

    @property
    def path(self) -> str:
        return str(PROCESS_ROOT / self.file_name).replace("\\", "/")


PROFILE_CATALOG: Dict[str, List[ProcessProfile]] = {
    "0.2": [
        ProcessProfile("0.2", 0.06, "0.06 Standard @Snapmaker U1 (0.2 nozzle).json"),
        ProcessProfile("0.2", 0.08, "0.08 Standard @Snapmaker U1 (0.2 nozzle).json"),
        ProcessProfile("0.2", 0.10, "0.10 Standard @Snapmaker U1 (0.2 nozzle).json"),
        ProcessProfile("0.2", 0.12, "0.12 Standard @Snapmaker U1 (0.2 nozzle).json"),
        ProcessProfile("0.2", 0.14, "0.14 Standard @Snapmaker U1 (0.2 nozzle).json"),
    ],
    "0.4": [
        ProcessProfile("0.4", 0.08, "0.08 High Quality @Snapmaker U1 (0.4 nozzle).json"),
        ProcessProfile("0.4", 0.12, "0.12 Fine @Snapmaker U1 (0.4 nozzle).json"),
        ProcessProfile("0.4", 0.16, "0.16 Optimal @Snapmaker U1 (0.4 nozzle).json"),
        ProcessProfile("0.4", 0.20, "0.20 Standard @Snapmaker U1 (0.4 nozzle).json"),
        ProcessProfile("0.4", 0.24, "0.24 Draft @Snapmaker U1 (0.4 nozzle).json"),
        ProcessProfile("0.4", 0.28, "0.28 Extra Draft @Snapmaker U1 (0.4 nozzle).json"),
    ],
    "0.6": [
        ProcessProfile("0.6", 0.18, "0.18 Standard @Snapmaker U1 (0.6 nozzle).json"),
        ProcessProfile("0.6", 0.24, "0.24 Standard @Snapmaker U1 (0.6 nozzle).json"),
        ProcessProfile("0.6", 0.30, "0.30 Standard @Snapmaker U1 (0.6 nozzle).json"),
        ProcessProfile("0.6", 0.36, "0.36 Standard @Snapmaker U1 (0.6 nozzle).json"),
        ProcessProfile("0.6", 0.42, "0.42 Standard @Snapmaker U1 (0.6 nozzle).json"),
    ],
    "0.8": [
        ProcessProfile("0.8", 0.24, "0.24 Standard @Snapmaker U1 (0.8 nozzle).json"),
        ProcessProfile("0.8", 0.32, "0.32 Standard @Snapmaker U1 (0.8 nozzle).json"),
        ProcessProfile("0.8", 0.40, "0.40 Standard @Snapmaker U1 (0.8 nozzle).json"),
        ProcessProfile("0.8", 0.48, "0.48 Standard @Snapmaker U1 (0.8 nozzle).json"),
        ProcessProfile("0.8", 0.56, "0.56 Standard @Snapmaker U1 (0.8 nozzle).json"),
    ],
}

FALLBACK_LAYER_TARGETS = {
    "0.2": 0.08,
    "0.4": 0.20,
    "0.6": 0.24,
    "0.8": 0.32,
}


def is_visible_or_sensitive(region: Region) -> bool:
    return region.visibility == "visible" or region.line_role_visibility in {"visible", "cosmetic", "mating"}


def is_forbidden_for_08(region: Region) -> bool:
    return region.line_type in {"top_surface", "painted_surface", "color_detail_skin", "support_interface", "bridge", "overhang"} or is_visible_or_sensitive(region)


def nearest_safer_profile(tool_class: str, requested: float) -> tuple[ProcessProfile, str]:
    profiles = sorted(PROFILE_CATALOG[tool_class], key=lambda item: item.layer_height)
    lower_or_equal = [item for item in profiles if item.layer_height <= requested + 1e-9]
    if lower_or_equal:
        selected = lower_or_equal[-1]
        if abs(selected.layer_height - requested) < 1e-9:
            return selected, f"Selected exact supported {selected.layer_height:.2f} mm U1 process profile."
        return selected, (
            f"Requested {requested:.2f} mm is unavailable for {tool_class}; "
            f"selected nearest safer/lower {selected.layer_height:.2f} mm profile."
        )
    selected = profiles[0]
    return selected, (
        f"Requested {requested:.2f} mm is below available {tool_class} profiles; "
        f"selected finest available {selected.layer_height:.2f} mm profile."
    )


def requested_layer_height(region: Region, assignment: Assignment) -> tuple[float, List[str]]:
    tool = assignment.recommended_tool_class
    reasons: List[str] = []
    target = region.target_layer_height_mm

    if tool == "0.2":
        if region.z_resolution_criticality in {"high", "micro"} or region.local_z_candidate:
            target = min(target, 0.08)
            reasons.append("0.2 high/micro Z detail uses 0.06-0.08 mm class.")
        elif region.detail_criticality in {"micro", "high"}:
            target = min(max(target, 0.10), 0.12)
            reasons.append("0.2 normal fine detail uses 0.10-0.12 mm class.")
        else:
            target = min(max(target, 0.14), 0.14)
            reasons.append("0.2 low Z criticality may use 0.14 mm class.")
    elif tool == "0.4":
        if region.line_type in {"top_surface", "painted_surface", "color_detail_skin"} or region.line_role_visibility == "cosmetic":
            target = min(max(target, 0.12), 0.20)
            reasons.append("0.4 visible/top/cosmetic region stays within 0.12-0.20 mm.")
        elif region.detail_criticality in {"none", "low"} and not is_visible_or_sensitive(region):
            target = min(max(target, 0.20), 0.28)
            reasons.append("0.4 low-risk shell may use 0.20-0.28 mm.")
        else:
            target = 0.20
            reasons.append("0.4 defaults to 0.20 mm.")
    elif tool == "0.6":
        if is_visible_or_sensitive(region) or region.surface_slope_degrees > 10.0:
            target = min(target, 0.24)
            reasons.append("0.6 visible/sloped risk uses conservative 0.24 mm and requires review.")
        elif region.z_resolution_criticality in {"none", "low"} and target >= 0.36:
            target = min(target, 0.42)
            reasons.append("0.6 hidden low-Z-risk shell may use 0.36-0.42 mm.")
        else:
            target = 0.24 if target <= 0.24 else 0.30
            reasons.append("0.6 structural shell defaults to 0.24 or 0.30 mm.")
    elif tool == "0.8":
        if is_forbidden_for_08(region):
            target = 0.24
            reasons.append("0.8 is forbidden for this sensitive line type; resolver records conservative fallback risk.")
        elif region.z_resolution_criticality in {"none", "low"} and target >= 0.48:
            target = min(target, 0.56)
            reasons.append("0.8 hidden low-Z-risk bulk may use 0.48-0.56 mm.")
        else:
            target = 0.32 if target <= 0.32 else 0.40
            reasons.append("0.8 bulk defaults to 0.32 or 0.40 mm.")
    else:
        target = 0.20
        reasons.append("Unknown or fallback tool uses conservative stock target.")
    return target, reasons


def fallback_profile(tool_class: str) -> ProcessProfile:
    fallback_tool = tool_class if tool_class in PROFILE_CATALOG else "0.4"
    profile, _ = nearest_safer_profile(fallback_tool, FALLBACK_LAYER_TARGETS[fallback_tool])
    return profile


def resolve_region(region: Region, assignment: Assignment, repo_root: Path) -> Dict[str, object]:
    tool = assignment.recommended_tool_class
    risk_flags = list(assignment.risk_flags)
    if tool not in PROFILE_CATALOG:
        tool = "0.4"
        risk_flags.append("process_resolver_unknown_tool_fallback")

    if tool == "0.8" and is_forbidden_for_08(region):
        risk_flags.append("resolver_rejects_0p8_sensitive_line_type")
        tool = "0.4"

    requested, reason_parts = requested_layer_height(region, assignment)
    selected, nearest_reason = nearest_safer_profile(tool, requested)
    selected_path = repo_root / selected.path
    if not selected_path.exists():
        risk_flags.append("selected_process_profile_missing")

    fallback_tool = assignment.fallback_tool_class if assignment.fallback_tool_class in PROFILE_CATALOG else "0.4"
    fallback = fallback_profile(fallback_tool)
    local_z_required = "local_z_future_required" in risk_flags or (
        region.local_z_candidate and region.z_resolution_criticality in {"high", "micro"}
    )
    if local_z_required and "local_z_future_required" not in risk_flags:
        risk_flags.append("local_z_future_required")

    return {
        "region_name": region.region_name,
        "line_type": region.line_type,
        "line_role_visibility": region.line_role_visibility,
        "recommended_tool_class": assignment.recommended_tool_class,
        "recommended_nozzle_diameter": selected.nozzle,
        "selected_process_profile": selected.path,
        "selected_layer_height_mm": f"{selected.layer_height:.2f}".rstrip("0").rstrip("."),
        "selected_line_width_class": assignment.recommended_line_width_class,
        "requested_layer_height_mm": f"{requested:.2f}".rstrip("0").rstrip("."),
        "selection_reason": " ".join(reason_parts + [nearest_reason]),
        "fallback_process_profile": fallback.path,
        "fallback_tool_class": assignment.fallback_tool_class,
        "risk_flags": risk_flags,
        "local_z_future_required": local_z_required,
        "touchscreen_mixed_nozzle_blocked": True,
        "touchscreen_block_reason": TOUCHSCREEN_BLOCKED,
    }


def resolve_regions(regions: Iterable[Region], repo_root: Optional[Path] = None) -> List[Dict[str, object]]:
    root = repo_root or Path.cwd()
    assignments = assignments_for(regions)
    return [resolve_region(region, assignment, root) for region, assignment in zip(regions, assignments)]


def write_json(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"process_queue": rows}, indent=2), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "region_name",
        "line_type",
        "line_role_visibility",
        "recommended_tool_class",
        "recommended_nozzle_diameter",
        "selected_process_profile",
        "selected_layer_height_mm",
        "selected_line_width_class",
        "requested_layer_height_mm",
        "selection_reason",
        "fallback_process_profile",
        "fallback_tool_class",
        "local_z_future_required",
        "touchscreen_mixed_nozzle_blocked",
        "risk_flags",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **{field: row.get(field, "") for field in fields},
                "risk_flags": "; ".join(str(item) for item in row.get("risk_flags", [])),
            })


def write_markdown(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AMP U1 Process Profile Queue",
        "",
        "| Region | Tool | Process profile | Layer | Width class | Local-Z | Fallback |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['region_name']}` | {row['recommended_nozzle_diameter']} | "
            f"`{row['selected_process_profile']}` | {row['selected_layer_height_mm']} | "
            f"{row['selected_line_width_class']} | {row['local_z_future_required']} | "
            f"`{row['fallback_process_profile']}` |"
        )
    lines.extend([
        "",
        "This queue is offline/advisory only and is not a single mixed-nozzle print job.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--csv")
    parser.add_argument("--markdown")
    args = parser.parse_args()

    rows = resolve_regions(load_regions(Path(args.input)), Path.cwd())
    out_path = Path(args.out)
    write_json(out_path, rows)
    csv_path = Path(args.csv) if args.csv else out_path.with_suffix(".csv")
    md_path = Path(args.markdown) if args.markdown else out_path.with_suffix(".md")
    write_csv(csv_path, rows)
    write_markdown(md_path, rows)
    print(f"wrote {len(rows)} process queue row(s) to {out_path}")
    for row in rows:
        print(f"{row['region_name']}: {row['recommended_nozzle_diameter']} -> {row['selected_process_profile']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
