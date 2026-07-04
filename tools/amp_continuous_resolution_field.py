#!/usr/bin/env python3
"""Offline AMP continuous resolution field prototype.

This tool computes a continuous resolution demand for each region, then
quantizes that demand into the available Snapmaker U1 process/profile ladder.

It is advisory only. It does not emit G-code, tool changes, or slicer behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


TOUCHSCREEN_WARNING = (
    "Advisory only: physical mixed-nozzle execution remains blocked for U1 "
    "touchscreen workflows until Snapmaker provides a compatible per-tool "
    "metadata/logical mapping path."
)


@dataclass(frozen=True)
class ToolProfile:
    tool_class: str
    nozzle_diameter_mm: float
    line_width_mm: float
    layer_heights_mm: tuple[float, ...]
    process_profiles: dict[float, str]
    fallback_tool_class: str


U1_LADDER: dict[str, ToolProfile] = {
    "0.2": ToolProfile(
        "0.2",
        0.2,
        0.22,
        (0.06, 0.08, 0.10, 0.12, 0.14),
        {
            0.06: "resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json",
            0.08: "resources/profiles/Snapmaker/process/0.08 Standard @Snapmaker U1 (0.2 nozzle).json",
            0.10: "resources/profiles/Snapmaker/process/0.10 Standard @Snapmaker U1 (0.2 nozzle).json",
            0.12: "resources/profiles/Snapmaker/process/0.12 Standard @Snapmaker U1 (0.2 nozzle).json",
            0.14: "resources/profiles/Snapmaker/process/0.14 Standard @Snapmaker U1 (0.2 nozzle).json",
        },
        "0.4",
    ),
    "0.4": ToolProfile(
        "0.4",
        0.4,
        0.42,
        (0.08, 0.12, 0.16, 0.20, 0.24, 0.28),
        {
            0.08: "resources/profiles/Snapmaker/process/0.08 High Quality @Snapmaker U1 (0.4 nozzle).json",
            0.12: "resources/profiles/Snapmaker/process/0.12 Fine @Snapmaker U1 (0.4 nozzle).json",
            0.16: "resources/profiles/Snapmaker/process/0.16 Optimal @Snapmaker U1 (0.4 nozzle).json",
            0.20: "resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json",
            0.24: "resources/profiles/Snapmaker/process/0.24 Draft @Snapmaker U1 (0.4 nozzle).json",
            0.28: "resources/profiles/Snapmaker/process/0.28 Extra Draft @Snapmaker U1 (0.4 nozzle).json",
        },
        "0.2",
    ),
    "0.6": ToolProfile(
        "0.6",
        0.6,
        0.62,
        (0.18, 0.24, 0.30, 0.36, 0.42),
        {
            0.18: "resources/profiles/Snapmaker/process/0.18 Standard @Snapmaker U1 (0.6 nozzle).json",
            0.24: "resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json",
            0.30: "resources/profiles/Snapmaker/process/0.30 Standard @Snapmaker U1 (0.6 nozzle).json",
            0.36: "resources/profiles/Snapmaker/process/0.36 Standard @Snapmaker U1 (0.6 nozzle).json",
            0.42: "resources/profiles/Snapmaker/process/0.42 Standard @Snapmaker U1 (0.6 nozzle).json",
        },
        "0.4",
    ),
    "0.8": ToolProfile(
        "0.8",
        0.8,
        0.82,
        (0.24, 0.32, 0.40, 0.48, 0.56),
        {
            0.24: "resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.8 nozzle).json",
            0.32: "resources/profiles/Snapmaker/process/0.32 Standard @Snapmaker U1 (0.8 nozzle).json",
            0.40: "resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json",
            0.48: "resources/profiles/Snapmaker/process/0.48 Standard @Snapmaker U1 (0.8 nozzle).json",
            0.56: "resources/profiles/Snapmaker/process/0.56 Standard @Snapmaker U1 (0.8 nozzle).json",
        },
        "0.6",
    ),
}


@dataclass
class Region:
    region_name: str
    line_type: str = "internal_perimeter"
    visibility: str = "internal"
    line_role_visibility: str = "internal"
    detail_criticality: str = "low"
    z_resolution_criticality: str = "low"
    xy_min_feature_size_mm: float = 1.0
    xy_nominal_feature_size_mm: float = 1.0
    z_feature_height_mm: float = 0.2
    vertical_extent_mm: float = 1.0
    vertical_extent_layers: int = 1
    surface_slope_degrees: float = 0.0
    wall_or_bulk: str = "normal_wall"
    estimated_region_area_mm2: float = 0.0
    estimated_path_length_mm: float = 0.0
    material_risk: str = "normal"
    toolchange_allowed: bool = True
    current_tool_class: str = "0.4"
    target_layer_height_mm: float = 0.20
    local_z_candidate: bool = False
    estimated_toolchange_cost_s: float = 60.0
    minimum_region_area_for_toolchange_mm2: float = 200.0
    minimum_path_length_for_toolchange_mm: float = 500.0


@dataclass
class ResolutionPlan:
    region_name: str
    line_type: str
    visibility: str
    line_role_visibility: str
    desired_xy_width_mm: float
    desired_z_height_mm: float
    desired_nozzle_class_mm: float
    desired_detail_score: float
    desired_bulk_score: float
    desired_visibility_score: float
    local_z_candidate: bool
    continuous_reason: str
    reason: str
    quantized_tool_class: str
    quantized_nozzle: float
    quantized_layer_height: float
    quantized_line_width_class: float
    selected_process_profile: str
    fallback_tool_class: str
    quantization_error_xy: float
    quantization_error_z: float
    risk_flags: list[str]
    confidence: float


def as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def region_from_dict(raw: dict[str, Any]) -> Region:
    return Region(
        region_name=str(raw.get("region_name", "unnamed_region")),
        line_type=str(raw.get("line_type", "internal_perimeter")),
        visibility=str(raw.get("visibility", raw.get("line_role_visibility", "internal"))),
        line_role_visibility=str(raw.get("line_role_visibility", raw.get("visibility", "internal"))),
        detail_criticality=str(raw.get("detail_criticality", "low")),
        z_resolution_criticality=str(raw.get("z_resolution_criticality", "low")),
        xy_min_feature_size_mm=as_float(raw.get("xy_min_feature_size_mm", raw.get("min_feature_size_mm")), 1.0),
        xy_nominal_feature_size_mm=as_float(raw.get("xy_nominal_feature_size_mm", raw.get("min_feature_size_mm")), 1.0),
        z_feature_height_mm=as_float(raw.get("z_feature_height_mm"), 0.2),
        vertical_extent_mm=as_float(raw.get("vertical_extent_mm"), 1.0),
        vertical_extent_layers=as_int(raw.get("vertical_extent_layers"), 1),
        surface_slope_degrees=as_float(raw.get("surface_slope_degrees"), 0.0),
        wall_or_bulk=str(raw.get("wall_or_bulk", "normal_wall")),
        estimated_region_area_mm2=as_float(raw.get("estimated_region_area_mm2"), 0.0),
        estimated_path_length_mm=as_float(raw.get("estimated_path_length_mm"), 0.0),
        material_risk=str(raw.get("material_risk", "normal")),
        toolchange_allowed=as_bool(raw.get("toolchange_allowed"), True),
        current_tool_class=str(raw.get("current_tool_class", "0.4")),
        target_layer_height_mm=as_float(raw.get("target_layer_height_mm"), 0.20),
        local_z_candidate=as_bool(raw.get("local_z_candidate"), False),
        estimated_toolchange_cost_s=as_float(raw.get("estimated_toolchange_cost_s"), 60.0),
        minimum_region_area_for_toolchange_mm2=as_float(raw.get("minimum_region_area_for_toolchange_mm2"), 200.0),
        minimum_path_length_for_toolchange_mm=as_float(raw.get("minimum_path_length_for_toolchange_mm"), 500.0),
    )


def load_regions(path: Path) -> list[Region]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_regions = data["regions"] if isinstance(data, dict) and "regions" in data else data
    if not isinstance(raw_regions, list):
        raise ValueError(f"{path} does not contain a regions array")
    return [region_from_dict(item) for item in raw_regions]


def score_detail(region: Region) -> float:
    base = {"micro": 1.0, "high": 0.78, "medium": 0.50, "low": 0.22, "none": 0.0}.get(region.detail_criticality, 0.25)
    if region.xy_min_feature_size_mm <= 0.45:
        base = max(base, 0.92)
    if region.z_resolution_criticality in {"micro", "high"}:
        base = max(base, 0.85)
    return min(base, 1.0)


def score_visibility(region: Region) -> float:
    if region.visibility == "visible" or region.line_role_visibility in {"cosmetic", "visible", "mating"}:
        return 1.0
    if region.line_role_visibility == "structural":
        return 0.35
    if region.visibility == "hidden" or region.line_role_visibility == "hidden":
        return 0.05
    return 0.25


def score_bulk(region: Region) -> float:
    score = 0.0
    if region.wall_or_bulk in {"bulk", "structural_shell"}:
        score += 0.35
    if region.line_type in {"sparse_infill", "internal_solid_infill"}:
        score += 0.35
    if region.estimated_region_area_mm2 >= 3000.0:
        score += 0.15
    if region.estimated_path_length_mm >= 3000.0:
        score += 0.15
    return min(score, 1.0)


def desired_z_height(region: Region, detail_score: float, visibility_score: float, bulk_score: float) -> tuple[float, str]:
    if region.local_z_candidate or region.z_resolution_criticality == "micro":
        target = min(region.target_layer_height_mm, 0.05)
        return target, "micro/local-Z candidate asks for finer Z than the base layer plan"
    if region.z_resolution_criticality == "high" or detail_score >= 0.80:
        return min(region.target_layer_height_mm, 0.08), "high detail/visibility asks for fine Z"
    if region.z_resolution_criticality == "medium" or visibility_score >= 0.80:
        return min(max(region.target_layer_height_mm, 0.12), 0.16), "visible or medium-Z detail asks for conservative Z"
    if bulk_score >= 0.75 and region.line_type == "sparse_infill":
        return min(max(region.target_layer_height_mm, 0.40), 0.50), "hidden bulk can use coarse Z before quantization"
    if bulk_score >= 0.50:
        return min(max(region.target_layer_height_mm, 0.24), 0.36), "internal structural/bulk region can use medium-coarse Z"
    return min(max(region.target_layer_height_mm, 0.16), 0.24), "general region uses stock-ish Z demand"


def desired_xy_width(region: Region, detail_score: float, visibility_score: float, bulk_score: float) -> tuple[float, str]:
    if region.line_type in {"bridge", "support_interface"}:
        return 0.42, "bridge/support-interface stays conservative"
    if detail_score >= 0.90 and visibility_score >= 0.80:
        return max(0.18, min(0.22, region.xy_min_feature_size_mm * 0.60)), "visible micro detail asks for sub-0.25 XY width"
    if detail_score >= 0.65 and visibility_score >= 0.80:
        return max(0.32, min(0.42, region.xy_min_feature_size_mm * 0.62)), "normal visible detail asks for 0.4-class XY width"
    if region.line_type == "internal_perimeter" or region.wall_or_bulk == "structural_shell":
        return 0.62 if region.xy_min_feature_size_mm >= 1.8 else 0.42, "structural/internal wall demand is based on available wall thickness"
    if region.line_type == "sparse_infill" or region.wall_or_bulk == "bulk":
        return 0.82 if bulk_score >= 0.75 and region.xy_min_feature_size_mm >= 3.0 else 0.62, "hidden bulk demand grows with region size and feature allowance"
    return 0.42, "default XY demand stays on the 0.4 visible/detail class"


def nearest_layer(tool_class: str, desired_z: float) -> float:
    heights = U1_LADDER[tool_class].layer_heights_mm
    return min(heights, key=lambda item: (abs(item - desired_z), item))


def initial_tool_from_demand(region: Region, desired_xy: float, desired_z: float, detail_score: float, visibility_score: float, bulk_score: float) -> str:
    if region.line_type in {"bridge", "support_interface"}:
        return "0.4"
    if visibility_score >= 0.80:
        return "0.2" if detail_score >= 0.90 or desired_z <= 0.08 or desired_xy <= 0.25 else "0.4"
    if region.line_type == "internal_perimeter" or region.wall_or_bulk == "structural_shell":
        return "0.6" if desired_xy >= 0.52 and region.vertical_extent_layers >= 8 else "0.4"
    if region.line_type == "sparse_infill" or region.wall_or_bulk == "bulk":
        return "0.8" if desired_xy >= 0.70 and bulk_score >= 0.75 else "0.6"
    return min(U1_LADDER, key=lambda key: abs(U1_LADDER[key].line_width_mm - desired_xy))


def apply_cost_gate(region: Region, tool_class: str, risk_flags: list[str]) -> str:
    if not region.toolchange_allowed:
        risk_flags.append("toolchange_disabled")
        return region.current_tool_class
    if tool_class == region.current_tool_class:
        return tool_class
    area_ok = region.estimated_region_area_mm2 >= region.minimum_region_area_for_toolchange_mm2
    path_ok = region.estimated_path_length_mm >= region.minimum_path_length_for_toolchange_mm
    if area_ok and path_ok:
        risk_flags.append("toolchange_cost_gate_passed")
        return tool_class
    risk_flags.append("toolchange_cost_gate_failed")
    return region.current_tool_class


def risk_flags_for(region: Region, tool_class: str, desired_z: float) -> list[str]:
    flags = [TOUCHSCREEN_WARNING]
    if region.local_z_candidate or desired_z < 0.06:
        flags.append("local_z_candidate")
        flags.append("local_z_future_required")
    if region.line_type in {"top_surface", "painted_surface", "color_detail_skin"} or region.surface_slope_degrees > 10.0:
        flags.append("visual_review_required")
    if region.line_type in {"bridge", "support_interface"}:
        flags.append("large_tool_restricted")
    if tool_class == "0.8" and (region.visibility == "visible" or region.line_role_visibility in {"cosmetic", "mating"}):
        flags.append("reject_0p8_visible_or_mating")
    if tool_class == "0.2" and region.material_risk in {"clog_risk", "abrasive", "flexible"}:
        flags.append(f"material_risk_{region.material_risk}")
    return flags


def confidence(detail_score: float, bulk_score: float, risk_flags: list[str]) -> float:
    score = 0.55 + 0.20 * max(detail_score, bulk_score)
    if "toolchange_cost_gate_failed" in risk_flags:
        score -= 0.15
    if "local_z_future_required" in risk_flags or "visual_review_required" in risk_flags:
        score -= 0.05
    return max(0.20, min(0.85, score))


def compute_plan(region: Region) -> ResolutionPlan:
    detail = score_detail(region)
    visibility = score_visibility(region)
    bulk = score_bulk(region)
    desired_xy, xy_reason = desired_xy_width(region, detail, visibility, bulk)
    desired_z, z_reason = desired_z_height(region, detail, visibility, bulk)
    desired_nozzle = min((0.2, 0.4, 0.6, 0.8), key=lambda item: abs(item - desired_xy))

    initial_tool = initial_tool_from_demand(region, desired_xy, desired_z, detail, visibility, bulk)
    risk_flags = risk_flags_for(region, initial_tool, desired_z)
    final_tool = apply_cost_gate(region, initial_tool, risk_flags)
    if "reject_0p8_visible_or_mating" in risk_flags and final_tool == "0.8":
        final_tool = "0.4"
    if "material_risk_clog_risk" in risk_flags and final_tool == "0.2":
        final_tool = "0.4"

    profile = U1_LADDER[final_tool]
    layer_height = nearest_layer(final_tool, desired_z)
    reason = f"{xy_reason}; {z_reason}"
    return ResolutionPlan(
        region_name=region.region_name,
        line_type=region.line_type,
        visibility=region.visibility,
        line_role_visibility=region.line_role_visibility,
        desired_xy_width_mm=round(desired_xy, 4),
        desired_z_height_mm=round(desired_z, 4),
        desired_nozzle_class_mm=desired_nozzle,
        desired_detail_score=round(detail, 3),
        desired_bulk_score=round(bulk, 3),
        desired_visibility_score=round(visibility, 3),
        local_z_candidate=("local_z_future_required" in risk_flags),
        continuous_reason=reason,
        reason=reason,
        quantized_tool_class=final_tool,
        quantized_nozzle=profile.nozzle_diameter_mm,
        quantized_layer_height=layer_height,
        quantized_line_width_class=profile.line_width_mm,
        selected_process_profile=profile.process_profiles[layer_height],
        fallback_tool_class=profile.fallback_tool_class,
        quantization_error_xy=round(abs(profile.line_width_mm - desired_xy), 4),
        quantization_error_z=round(abs(layer_height - desired_z), 4),
        risk_flags=risk_flags,
        confidence=round(confidence(detail, bulk, risk_flags), 3),
    )


def example_regions() -> list[Region]:
    return [
        Region("micro_text_face", "external_perimeter", "visible", "cosmetic", "micro", "micro", 0.32, 0.50, 0.10, 0.40, 5, 0.0, "thin_wall", 320.0, 800.0, "normal", True, "0.4", 0.06, True),
        Region("normal_cosmetic_wall", "external_perimeter", "visible", "cosmetic", "high", "medium", 0.70, 1.20, 0.60, 3.0, 18, 8.0, "normal_wall", 1000.0, 1600.0, "normal", True, "0.4", 0.16),
        Region("hidden_internal_wall", "internal_perimeter", "internal", "structural", "low", "low", 2.2, 3.5, 6.0, 8.0, 32, 90.0, "structural_shell", 2400.0, 2400.0, "normal", True, "0.4", 0.24),
        Region("structural_boss", "internal_perimeter", "internal", "structural", "low", "medium", 2.8, 5.0, 8.0, 10.0, 40, 90.0, "structural_shell", 1800.0, 1900.0, "normal", True, "0.4", 0.24),
        Region("bulk_infill_mass", "sparse_infill", "hidden", "hidden", "none", "none", 6.0, 15.0, 16.0, 16.0, 40, 0.0, "bulk", 7000.0, 6000.0, "normal", True, "0.4", 0.40),
        Region("sloped_top_logo", "top_surface", "visible", "cosmetic", "high", "high", 0.55, 0.85, 0.18, 0.80, 6, 22.0, "normal_wall", 900.0, 1200.0, "normal", True, "0.4", 0.12),
        Region("painted_surface_skin", "painted_surface", "visible", "cosmetic", "high", "medium", 0.60, 1.0, 0.20, 0.80, 4, 5.0, "normal_wall", 1600.0, 2200.0, "normal", True, "0.4", 0.12),
        Region("support_interface", "support_interface", "internal", "mating", "medium", "medium", 0.80, 1.20, 0.20, 1.0, 5, 0.0, "normal_wall", 1200.0, 1600.0, "normal", True, "0.4", 0.20),
        Region("bridge_region", "bridge", "internal", "structural", "medium", "medium", 1.0, 2.0, 0.24, 1.2, 5, 0.0, "normal_wall", 1800.0, 2200.0, "normal", True, "0.4", 0.24),
        Region("local_z_micro_mark", "painted_surface", "visible", "cosmetic", "micro", "micro", 0.35, 0.50, 0.08, 0.08, 1, 0.0, "normal_wall", 500.0, 1000.0, "normal", True, "0.4", 0.06, True),
    ]


def plans_for(regions: Iterable[Region]) -> list[ResolutionPlan]:
    return [compute_plan(region) for region in regions]


def write_json(path: Path, plans: list[ResolutionPlan]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"resolution_plan": [asdict(plan) for plan in plans]}, indent=2), encoding="utf-8", newline="\n")


def write_csv(path: Path, plans: list[ResolutionPlan]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(plan) for plan in plans]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            row["risk_flags"] = "; ".join(row["risk_flags"])
            writer.writerow(row)


def write_markdown(path: Path, plans: list[ResolutionPlan]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| Region | Desired XY | Desired Z | Tool | Layer | Width | XY error | Z error | Local-Z | Confidence | Reason |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for plan in plans:
        lines.append(
            f"| `{plan.region_name}` | {plan.desired_xy_width_mm:.3f} | {plan.desired_z_height_mm:.3f} | "
            f"{plan.quantized_tool_class} | {plan.quantized_layer_height:.2f} | {plan.quantized_line_width_class:.2f} | "
            f"{plan.quantization_error_xy:.3f} | {plan.quantization_error_z:.3f} | {plan.local_z_candidate} | "
            f"{plan.confidence:.2f} | {plan.continuous_reason} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_examples(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"regions": [asdict(region) for region in example_regions()]}, indent=2), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Region metadata JSON file")
    parser.add_argument("--examples", action="store_true", help="Use built-in example regions")
    parser.add_argument("--write-examples", help="Write example region metadata JSON")
    parser.add_argument("--out", required=True, help="JSON output path")
    parser.add_argument("--csv", help="Optional CSV output path")
    parser.add_argument("--markdown", help="Optional markdown output path")
    args = parser.parse_args()

    if args.write_examples:
        write_examples(Path(args.write_examples))

    if args.examples:
        regions = example_regions()
    elif args.input:
        regions = load_regions(Path(args.input))
    else:
        parser.error("provide --input or --examples")

    plans = plans_for(regions)
    write_json(Path(args.out), plans)
    if args.csv:
        write_csv(Path(args.csv), plans)
    if args.markdown:
        write_markdown(Path(args.markdown), plans)

    print(f"wrote {len(plans)} resolution plan row(s) to {args.out}")
    for plan in plans:
        print(
            f"{plan.region_name}: desired XY {plan.desired_xy_width_mm:.3f}, "
            f"desired Z {plan.desired_z_height_mm:.3f} -> "
            f"{plan.quantized_tool_class} / {plan.quantized_layer_height:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
