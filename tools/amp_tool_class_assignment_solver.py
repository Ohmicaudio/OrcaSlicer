#!/usr/bin/env python3
"""Offline AMP region-to-tool-class assignment solver."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


TOOL_CLASSES: Dict[str, Dict[str, str]] = {
    "0.2": {"layer": "0.06-0.10", "width": "0.22"},
    "0.4": {"layer": "0.12-0.20", "width": "0.42-0.45"},
    "0.6": {"layer": "0.24-0.36", "width": "0.62"},
    "0.8": {"layer": "0.32-0.56", "width": "0.82"},
}

TOUCHSCREEN_WARNING = (
    "Advisory only: physical mixed-nozzle execution remains blocked for U1 "
    "touchscreen workflows until Snapmaker provides a compatible per-tool "
    "metadata/logical mapping path."
)


@dataclass
class Region:
    region_name: str
    visibility: str = "internal"
    detail_criticality: str = "low"
    wall_or_bulk: str = "normal_wall"
    min_feature_size_mm: float = 1.0
    target_layer_height_mm: float = 0.20
    estimated_region_area_mm2: float = 0.0
    estimated_path_length_mm: float = 0.0
    toolchange_allowed: bool = True
    material_risk: str = "normal"
    confidence_hint: Optional[str] = None
    source_note: str = ""
    estimated_toolchange_cost_s: float = 60.0
    minimum_time_savings_required_s: float = 60.0
    minimum_region_area_for_toolchange_mm2: float = 200.0
    minimum_path_length_for_toolchange_mm: float = 500.0
    current_tool_class: Optional[str] = "0.4"
    single_nozzle_mode: bool = False


@dataclass
class Assignment:
    region_name: str
    recommended_tool_class: str
    recommended_layer_height_class: str
    recommended_line_width_class: str
    fallback_tool_class: str
    reason: str
    risk_flags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    cost_gate_passed: bool = True
    estimated_toolchange_cost_s: float = 0.0
    cost_gate_reason: str = ""
    fallback_reason: str = ""


def example_regions() -> List[Region]:
    return [
        Region(
            region_name="micro_detail_zone",
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.35,
            target_layer_height_mm=0.06,
            estimated_region_area_mm2=250.0,
            estimated_path_length_mm=900.0,
        ),
        Region(
            region_name="normal_visible_detail_zone",
            visibility="visible",
            detail_criticality="high",
            wall_or_bulk="normal_wall",
            min_feature_size_mm=0.75,
            target_layer_height_mm=0.16,
            estimated_region_area_mm2=900.0,
            estimated_path_length_mm=1500.0,
        ),
        Region(
            region_name="structural_shell_zone",
            visibility="internal",
            detail_criticality="low",
            wall_or_bulk="structural_shell",
            min_feature_size_mm=2.4,
            target_layer_height_mm=0.24,
            estimated_region_area_mm2=2400.0,
            estimated_path_length_mm=2300.0,
        ),
        Region(
            region_name="bulk_zone",
            visibility="hidden",
            detail_criticality="none",
            wall_or_bulk="bulk",
            min_feature_size_mm=5.0,
            target_layer_height_mm=0.40,
            estimated_region_area_mm2=6500.0,
            estimated_path_length_mm=5200.0,
        ),
        Region(
            region_name="abrasive_micro_detail_rejected",
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.35,
            target_layer_height_mm=0.06,
            estimated_region_area_mm2=160.0,
            estimated_path_length_mm=500.0,
            material_risk="abrasive",
        ),
        Region(
            region_name="no_toolchange_single_nozzle_fallback",
            visibility="hidden",
            detail_criticality="none",
            wall_or_bulk="bulk",
            min_feature_size_mm=6.0,
            target_layer_height_mm=0.40,
            estimated_region_area_mm2=7000.0,
            estimated_path_length_mm=6000.0,
            toolchange_allowed=False,
        ),
        Region(
            region_name="thin_wall_reject_large_tool",
            visibility="internal",
            detail_criticality="medium",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.55,
            target_layer_height_mm=0.12,
            estimated_region_area_mm2=350.0,
            estimated_path_length_mm=900.0,
        ),
        Region(
            region_name="low_confidence_fallback",
            visibility="internal",
            detail_criticality="medium",
            wall_or_bulk="structural_shell",
            min_feature_size_mm=1.8,
            target_layer_height_mm=0.24,
            estimated_region_area_mm2=1900.0,
            estimated_path_length_mm=1900.0,
            confidence_hint="low",
        ),
        Region(
            region_name="tiny_micro_detail_not_worth_toolchange",
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.35,
            target_layer_height_mm=0.06,
            estimated_region_area_mm2=45.0,
            estimated_path_length_mm=120.0,
            current_tool_class="0.4",
        ),
        Region(
            region_name="large_micro_detail_panel_worth_0p2",
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.40,
            target_layer_height_mm=0.06,
            estimated_region_area_mm2=1200.0,
            estimated_path_length_mm=2600.0,
            current_tool_class="0.4",
        ),
        Region(
            region_name="small_bulk_region_not_worth_0p8",
            visibility="hidden",
            detail_criticality="none",
            wall_or_bulk="bulk",
            min_feature_size_mm=4.0,
            target_layer_height_mm=0.40,
            estimated_region_area_mm2=180.0,
            estimated_path_length_mm=300.0,
            current_tool_class="0.4",
        ),
        Region(
            region_name="large_hidden_bulk_worth_0p8",
            visibility="hidden",
            detail_criticality="none",
            wall_or_bulk="bulk",
            min_feature_size_mm=6.0,
            target_layer_height_mm=0.40,
            estimated_region_area_mm2=8000.0,
            estimated_path_length_mm=7000.0,
            current_tool_class="0.4",
        ),
        Region(
            region_name="current_tool_0p4_no_toolchange_fallback",
            visibility="hidden",
            detail_criticality="none",
            wall_or_bulk="bulk",
            min_feature_size_mm=6.0,
            target_layer_height_mm=0.40,
            estimated_region_area_mm2=8000.0,
            estimated_path_length_mm=7000.0,
            toolchange_allowed=False,
            current_tool_class="0.4",
        ),
        Region(
            region_name="clog_risk_micro_detail_fallback_0p4",
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.40,
            target_layer_height_mm=0.06,
            estimated_region_area_mm2=1400.0,
            estimated_path_length_mm=2400.0,
            material_risk="clog_risk",
            current_tool_class="0.4",
        ),
    ]


def as_bool(value: object, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: object, default: float) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def normalize_generated_region(raw: Dict[str, object]) -> Region:
    name = str(raw.get("region_name", "unnamed_region"))
    intended = str(raw.get("intended_nozzle", "0.4"))
    if intended == "0.2":
        return Region(
            region_name=name,
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.35,
            target_layer_height_mm=0.06,
            estimated_region_area_mm2=250.0,
            estimated_path_length_mm=900.0,
            current_tool_class="0.4",
            source_note=str(raw.get("reason", "")),
        )
    if intended == "0.4":
        return Region(
            region_name=name,
            visibility="visible",
            detail_criticality="high",
            wall_or_bulk="normal_wall",
            min_feature_size_mm=0.65,
            target_layer_height_mm=0.16,
            estimated_region_area_mm2=900.0,
            estimated_path_length_mm=1500.0,
            current_tool_class="0.4",
            source_note=str(raw.get("reason", "")),
        )
    if intended == "0.6":
        return Region(
            region_name=name,
            visibility="internal",
            detail_criticality="low",
            wall_or_bulk="structural_shell",
            min_feature_size_mm=2.0,
            target_layer_height_mm=0.24,
            estimated_region_area_mm2=2400.0,
            estimated_path_length_mm=2300.0,
            current_tool_class="0.4",
            source_note=str(raw.get("reason", "")),
        )
    return Region(
        region_name=name,
        visibility="hidden",
        detail_criticality="none",
        wall_or_bulk="bulk",
        min_feature_size_mm=5.0,
        target_layer_height_mm=0.40,
        estimated_region_area_mm2=6500.0,
        estimated_path_length_mm=5200.0,
        current_tool_class="0.4",
        source_note=str(raw.get("reason", "")),
    )


def region_from_dict(raw: Dict[str, object]) -> Region:
    if "visibility" not in raw and "intended_nozzle" in raw:
        return normalize_generated_region(raw)
    return Region(
        region_name=str(raw.get("region_name", "unnamed_region")),
        visibility=str(raw.get("visibility", "internal")),
        detail_criticality=str(raw.get("detail_criticality", "low")),
        wall_or_bulk=str(raw.get("wall_or_bulk", "normal_wall")),
        min_feature_size_mm=as_float(raw.get("min_feature_size_mm"), 1.0),
        target_layer_height_mm=as_float(raw.get("target_layer_height_mm"), 0.20),
        estimated_region_area_mm2=as_float(raw.get("estimated_region_area_mm2"), 0.0),
        estimated_path_length_mm=as_float(raw.get("estimated_path_length_mm"), 0.0),
        toolchange_allowed=as_bool(raw.get("toolchange_allowed"), True),
        material_risk=str(raw.get("material_risk", "normal")),
        confidence_hint=str(raw["confidence_hint"]) if raw.get("confidence_hint") is not None else None,
        estimated_toolchange_cost_s=as_float(raw.get("estimated_toolchange_cost_s"), 60.0),
        minimum_time_savings_required_s=as_float(raw.get("minimum_time_savings_required_s"), 60.0),
        minimum_region_area_for_toolchange_mm2=as_float(raw.get("minimum_region_area_for_toolchange_mm2"), 200.0),
        minimum_path_length_for_toolchange_mm=as_float(raw.get("minimum_path_length_for_toolchange_mm"), 500.0),
        current_tool_class=str(raw["current_tool_class"]) if raw.get("current_tool_class") is not None else None,
        single_nozzle_mode=as_bool(raw.get("single_nozzle_mode"), False),
    )


def load_regions(path: Path) -> List[Region]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_regions = data.get("regions", data if isinstance(data, list) else [])
    if not isinstance(raw_regions, list):
        raise ValueError(f"{path} does not contain a regions array")
    return [region_from_dict(item) for item in raw_regions if isinstance(item, dict)]


def class_info(tool_class: str) -> Dict[str, str]:
    return TOOL_CLASSES.get(tool_class, {"layer": "stock", "width": "stock"})


def confidence_for(region: Region, tool_class: str, risks: List[str], base: float) -> float:
    if region.confidence_hint == "low":
        risks.append("low_confidence")
        return min(base, 0.45)
    if tool_class in {"reject", "single_nozzle_fallback"}:
        return min(base, 0.35)
    if risks:
        return min(base, 0.70)
    return base


def cost_gate(region: Region, tool_class: str, fallback_tool: str, risks: List[str]) -> tuple[str, bool, str, str]:
    current = region.current_tool_class
    if tool_class in {"reject", "single_nozzle_fallback"}:
        return tool_class, False, "No toolchange cost gate applies to reject/single-nozzle fallback.", ""
    if current is None:
        return tool_class, True, "No current tool class was provided; advisory assignment is allowed.", ""
    if tool_class == current:
        return tool_class, True, f"Recommended tool already matches current tool {current}; no toolchange is needed.", ""

    area_ok = region.estimated_region_area_mm2 >= region.minimum_region_area_for_toolchange_mm2
    path_ok = region.estimated_path_length_mm >= region.minimum_path_length_for_toolchange_mm
    if area_ok and path_ok:
        return (
            tool_class,
            True,
            (
                f"Toolchange from {current} to {tool_class} passes region-size gate "
                f"(area {region.estimated_region_area_mm2:.1f} >= {region.minimum_region_area_for_toolchange_mm2:.1f} mm^2, "
                f"path {region.estimated_path_length_mm:.1f} >= {region.minimum_path_length_for_toolchange_mm:.1f} mm). "
                f"Estimated toolchange cost is {region.estimated_toolchange_cost_s:.1f}s; "
                f"minimum required savings is {region.minimum_time_savings_required_s:.1f}s."
            ),
            "",
        )

    risks.append("cost_gate_failed")
    fallback = current or fallback_tool or "0.4"
    return (
        fallback,
        False,
        (
            f"Toolchange from {current} to {tool_class} failed region-size gate "
            f"(area {region.estimated_region_area_mm2:.1f}/{region.minimum_region_area_for_toolchange_mm2:.1f} mm^2, "
            f"path {region.estimated_path_length_mm:.1f}/{region.minimum_path_length_for_toolchange_mm:.1f} mm)."
        ),
        f"Falling back to {fallback} because the region is too small to justify the toolchange cost.",
    )


def finalize_assignment(
    region: Region,
    tool_class: str,
    fallback_tool: str,
    reason: str,
    risks: List[str],
    base_confidence: float,
) -> Assignment:
    final_tool, gate_passed, gate_reason, fallback_reason = cost_gate(region, tool_class, fallback_tool, risks)
    info = class_info(final_tool)
    if final_tool != tool_class:
        reason = f"{reason} {fallback_reason}".strip()
    confidence = confidence_for(region, final_tool, risks, base_confidence)
    return Assignment(
        region_name=region.region_name,
        recommended_tool_class=final_tool,
        recommended_layer_height_class=info["layer"],
        recommended_line_width_class=info["width"],
        fallback_tool_class=fallback_tool,
        reason=reason,
        risk_flags=risks,
        confidence=confidence,
        cost_gate_passed=gate_passed,
        estimated_toolchange_cost_s=region.estimated_toolchange_cost_s,
        cost_gate_reason=gate_reason,
        fallback_reason=fallback_reason,
    )


def assign(region: Region) -> Assignment:
    risks: List[str] = [TOUCHSCREEN_WARNING]
    reason_parts: List[str] = []

    if region.single_nozzle_mode or not region.toolchange_allowed:
        risks.append("toolchange_disabled")
        reason = "Tool changes are disabled, so AMP keeps advisory stock/single-tool behavior."
        confidence = confidence_for(region, "single_nozzle_fallback", risks, 0.70)
        return Assignment(
            region.region_name,
            "single_nozzle_fallback",
            "stock",
            "stock",
            region.current_tool_class or "0.4",
            reason,
            risks,
            confidence,
            False,
            region.estimated_toolchange_cost_s,
            "Single-nozzle mode or toolchange-disabled input bypasses multi-tool cost gating.",
            f"Falling back to {region.current_tool_class or '0.4'} stock/single-tool behavior.",
        )

    if region.confidence_hint == "low":
        reason = "Region confidence is low; fall back to the general visible/detail class."
        return finalize_assignment(region, "0.4", "0.4", reason, risks, 0.55)

    risk_material = region.material_risk in {"clog_risk", "flexible", "abrasive"}
    visible = region.visibility == "visible"
    detail = region.detail_criticality

    if detail == "micro" and visible:
        if not risk_material and region.min_feature_size_mm >= 0.35:
            risks.append("high_cost_detail_tool")
            risks.append("preview_required")
            reason_parts.append("Visible micro detail is plausible for the 0.2 fine/detail class.")
            return finalize_assignment(region, "0.2", "0.4", " ".join(reason_parts), risks, 0.72)
        if risk_material:
            risks.append(f"material_{region.material_risk}")
            reason_parts.append("0.2 is rejected for this material risk; use 0.4 as the safer visible-detail fallback.")
        else:
            risks.append("micro_feature_below_documented_sliceable_bound")
            reason_parts.append("Feature size is below the documented 0.35 mm 0.2-proxy sliceable lower bound; use 0.4 fallback unless validated.")
        return finalize_assignment(region, "0.4", "0.4", " ".join(reason_parts), risks, 0.65)

    if region.wall_or_bulk == "thin_wall":
        if region.min_feature_size_mm < 0.70:
            risks.append("reject_large_tool_for_thin_wall")
            return finalize_assignment(region, "0.4", "0.2", "Thin wall is too small for 0.6/0.8; use finer fallback.", risks, 0.62)
        return finalize_assignment(region, "0.4", "0.4", "Thin wall remains on the general class until validated.", risks, 0.70)

    if visible or detail in {"medium", "high"}:
        if region.wall_or_bulk == "structural_shell" and region.min_feature_size_mm >= 2.0 and detail in {"none", "low"}:
            return finalize_assignment(region, "0.6", "0.4", "Visible risk is low and shell geometry is thick enough for 0.6.", risks, 0.68)
        risks.append("avoid_large_visible_tool")
        return finalize_assignment(region, "0.4", "0.2", "Normal visible/detail geometry should use the 0.4 general class and avoid 0.8.", risks, 0.78)

    if region.wall_or_bulk == "structural_shell":
        if region.min_feature_size_mm < 1.8:
            risks.append("thin_structural_shell")
            return finalize_assignment(region, "0.4", "0.4", "Structural shell is too thin or too visible for 0.6.", risks, 0.62)
        return finalize_assignment(region, "0.6", "0.4", "Internal/low-detail structural shell is a 0.6 candidate.", risks, 0.82)

    if region.wall_or_bulk == "bulk" or region.visibility == "hidden":
        large_enough = region.estimated_region_area_mm2 >= 3000.0 or region.estimated_path_length_mm >= 3000.0
        if large_enough and region.min_feature_size_mm >= 3.0:
            risks.append("bulk_tool_cost_gate")
            return finalize_assignment(region, "0.8", "0.6", "Hidden/internal bulk is large enough for the 0.8 bulk class.", risks, 0.84)
        risks.append("medium_bulk")
        return finalize_assignment(region, "0.6", "0.4", "Bulk is not large enough for 0.8; use 0.6 medium bulk fallback.", risks, 0.72)

    risks.append("unmatched_rule")
    return finalize_assignment(region, "0.4", "0.4", "No stronger rule matched; use the general 0.4 fallback.", risks, 0.50)


def assignments_for(regions: Iterable[Region]) -> List[Assignment]:
    return [assign(region) for region in regions]


def assignment_row(assignment: Assignment) -> Dict[str, object]:
    return {
        "region_name": assignment.region_name,
        "recommended_tool_class": assignment.recommended_tool_class,
        "recommended_layer_height_class": assignment.recommended_layer_height_class,
        "recommended_line_width_class": assignment.recommended_line_width_class,
        "fallback_tool_class": assignment.fallback_tool_class,
        "cost_gate_passed": str(assignment.cost_gate_passed).lower(),
        "estimated_toolchange_cost_s": f"{assignment.estimated_toolchange_cost_s:.1f}",
        "cost_gate_reason": assignment.cost_gate_reason,
        "fallback_reason": assignment.fallback_reason,
        "reason": assignment.reason,
        "risk_flags": "; ".join(assignment.risk_flags),
        "confidence": f"{assignment.confidence:.2f}",
    }


def write_csv(assignments: List[Assignment], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [assignment_row(item) for item in assignments]
    fields = list(rows[0].keys()) if rows else list(assignment_row(Assignment("", "", "", "", "", "")).keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown(assignments: List[Assignment]) -> str:
    lines = [
        "| Region | Tool | Layer class | Width class | Fallback | Cost gate | Cost reason | Confidence | Risk flags | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for item in assignments:
        row = assignment_row(item)
        lines.append(
            f"| `{row['region_name']}` | `{row['recommended_tool_class']}` | "
            f"`{row['recommended_layer_height_class']}` | `{row['recommended_line_width_class']}` | "
            f"`{row['fallback_tool_class']}` | {row['cost_gate_passed']} | {row['cost_gate_reason']} | "
            f"{row['confidence']} | {row['risk_flags']} | {row['reason']} |"
        )
    return "\n".join(lines) + "\n"


def write_markdown(assignments: List[Assignment], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown(assignments), encoding="utf-8", newline="\n")


def write_json_examples(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"regions": [region.__dict__ for region in example_regions()]}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Region metadata JSON file")
    parser.add_argument("--examples", action="store_true", help="Use built-in example regions")
    parser.add_argument("--write-examples", help="Write built-in examples to a JSON file")
    parser.add_argument("--format", choices=("markdown", "csv", "json"), default="markdown")
    parser.add_argument("--out", help="Output path; stdout is used if omitted")
    args = parser.parse_args()

    if args.write_examples:
        write_json_examples(Path(args.write_examples))

    if args.examples:
        regions = example_regions()
    elif args.input:
        regions = load_regions(Path(args.input))
    else:
        parser.error("provide --examples or --input")

    result = assignments_for(regions)
    if args.out:
        out_path = Path(args.out)
        if args.format == "csv":
            write_csv(result, out_path)
        elif args.format == "json":
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps([assignment_row(item) for item in result], indent=2), encoding="utf-8", newline="\n")
        else:
            write_markdown(result, out_path)
    else:
        if args.format == "csv":
            rows = [assignment_row(item) for item in result]
            if rows:
                writer = csv.DictWriter(__import__("sys").stdout, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
        elif args.format == "json":
            print(json.dumps([assignment_row(item) for item in result], indent=2))
        else:
            print(markdown(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
