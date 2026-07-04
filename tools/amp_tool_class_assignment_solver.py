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
    xy_min_feature_size_mm: float = 1.0
    xy_nominal_feature_size_mm: float = 1.0
    z_feature_height_mm: float = 0.20
    vertical_extent_mm: float = 0.20
    vertical_extent_layers: int = 1
    target_layer_height_mm: float = 0.20
    surface_slope_degrees: float = 0.0
    local_z_candidate: bool = False
    z_resolution_criticality: str = "none"
    line_type: str = "internal_perimeter"
    line_role_visibility: str = "internal"
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
    line_type: str = ""
    line_role_visibility: str = ""
    risk_flags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    cost_gate_passed: bool = True
    estimated_toolchange_cost_s: float = 0.0
    cost_gate_reason: str = ""
    fallback_reason: str = ""


def example_regions() -> List[Region]:
    return [
        Region(
            region_name="shallow_logo_top_surface",
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="normal_wall",
            min_feature_size_mm=0.35,
            xy_min_feature_size_mm=0.35,
            xy_nominal_feature_size_mm=0.55,
            z_feature_height_mm=0.12,
            vertical_extent_mm=0.12,
            vertical_extent_layers=2,
            target_layer_height_mm=0.06,
            surface_slope_degrees=0.0,
            local_z_candidate=True,
            z_resolution_criticality="micro",
            line_type="top_surface",
            line_role_visibility="cosmetic",
            estimated_region_area_mm2=250.0,
            estimated_path_length_mm=900.0,
        ),
        Region(
            region_name="tall_visible_side_text",
            visibility="visible",
            detail_criticality="high",
            wall_or_bulk="thin_wall",
            min_feature_size_mm=0.50,
            xy_min_feature_size_mm=0.50,
            xy_nominal_feature_size_mm=0.80,
            z_feature_height_mm=6.0,
            vertical_extent_mm=6.0,
            vertical_extent_layers=30,
            target_layer_height_mm=0.12,
            surface_slope_degrees=90.0,
            z_resolution_criticality="medium",
            line_type="external_perimeter",
            line_role_visibility="cosmetic",
            estimated_region_area_mm2=900.0,
            estimated_path_length_mm=1500.0,
        ),
        Region(
            region_name="hidden_internal_perimeter",
            visibility="internal",
            detail_criticality="low",
            wall_or_bulk="structural_shell",
            min_feature_size_mm=2.4,
            xy_min_feature_size_mm=2.4,
            xy_nominal_feature_size_mm=4.0,
            z_feature_height_mm=10.0,
            vertical_extent_mm=10.0,
            vertical_extent_layers=42,
            target_layer_height_mm=0.24,
            line_type="internal_perimeter",
            line_role_visibility="structural",
            estimated_region_area_mm2=2400.0,
            estimated_path_length_mm=2300.0,
        ),
        Region(
            region_name="support_interface_should_stay_conservative",
            visibility="internal",
            detail_criticality="medium",
            wall_or_bulk="normal_wall",
            min_feature_size_mm=0.8,
            xy_min_feature_size_mm=0.8,
            xy_nominal_feature_size_mm=1.2,
            z_feature_height_mm=0.2,
            vertical_extent_mm=1.0,
            vertical_extent_layers=5,
            target_layer_height_mm=0.20,
            line_type="support_interface",
            line_role_visibility="mating",
            estimated_region_area_mm2=1200.0,
            estimated_path_length_mm=1600.0,
        ),
        Region(
            region_name="bridge_reject_large_tool",
            visibility="internal",
            detail_criticality="medium",
            wall_or_bulk="normal_wall",
            min_feature_size_mm=1.0,
            xy_min_feature_size_mm=1.0,
            xy_nominal_feature_size_mm=2.0,
            z_feature_height_mm=0.24,
            vertical_extent_mm=1.2,
            vertical_extent_layers=5,
            target_layer_height_mm=0.24,
            line_type="bridge",
            line_role_visibility="structural",
            estimated_region_area_mm2=1800.0,
            estimated_path_length_mm=2200.0,
        ),
        Region(
            region_name="painted_surface_color_skin",
            visibility="visible",
            detail_criticality="high",
            wall_or_bulk="normal_wall",
            min_feature_size_mm=0.6,
            xy_min_feature_size_mm=0.6,
            xy_nominal_feature_size_mm=1.0,
            z_feature_height_mm=0.2,
            vertical_extent_mm=0.8,
            vertical_extent_layers=4,
            target_layer_height_mm=0.12,
            line_type="color_detail_skin",
            line_role_visibility="cosmetic",
            estimated_region_area_mm2=1600.0,
            estimated_path_length_mm=2200.0,
        ),
        Region(
            region_name="local_z_micro_detail_candidate",
            visibility="visible",
            detail_criticality="micro",
            wall_or_bulk="normal_wall",
            min_feature_size_mm=0.35,
            xy_min_feature_size_mm=0.35,
            xy_nominal_feature_size_mm=0.50,
            z_feature_height_mm=0.08,
            vertical_extent_mm=0.08,
            vertical_extent_layers=1,
            target_layer_height_mm=0.06,
            local_z_candidate=True,
            z_resolution_criticality="micro",
            line_type="painted_surface",
            line_role_visibility="cosmetic",
            estimated_region_area_mm2=500.0,
            estimated_path_length_mm=1000.0,
        ),
        Region(
            region_name="bulk_region_worth_0p8",
            visibility="hidden",
            detail_criticality="none",
            wall_or_bulk="bulk",
            min_feature_size_mm=8.0,
            xy_min_feature_size_mm=8.0,
            xy_nominal_feature_size_mm=20.0,
            z_feature_height_mm=25.0,
            vertical_extent_mm=25.0,
            vertical_extent_layers=63,
            target_layer_height_mm=0.40,
            line_type="sparse_infill",
            line_role_visibility="hidden",
            estimated_region_area_mm2=8000.0,
            estimated_path_length_mm=7000.0,
        ),
        Region(
            region_name="bulk_region_too_small_for_0p8",
            visibility="hidden",
            detail_criticality="none",
            wall_or_bulk="bulk",
            min_feature_size_mm=4.0,
            xy_min_feature_size_mm=4.0,
            xy_nominal_feature_size_mm=8.0,
            z_feature_height_mm=4.0,
            vertical_extent_mm=4.0,
            vertical_extent_layers=10,
            target_layer_height_mm=0.40,
            estimated_region_area_mm2=180.0,
            estimated_path_length_mm=300.0,
            line_type="sparse_infill",
            line_role_visibility="hidden",
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


def as_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
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
            xy_min_feature_size_mm=0.35,
            xy_nominal_feature_size_mm=0.55,
            z_feature_height_mm=0.12,
            vertical_extent_mm=0.45,
            vertical_extent_layers=6,
            target_layer_height_mm=0.06,
            local_z_candidate=True,
            z_resolution_criticality="micro",
            line_type="external_perimeter",
            line_role_visibility="cosmetic",
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
            xy_min_feature_size_mm=0.65,
            xy_nominal_feature_size_mm=1.0,
            z_feature_height_mm=0.6,
            vertical_extent_mm=2.4,
            vertical_extent_layers=15,
            target_layer_height_mm=0.16,
            z_resolution_criticality="medium",
            line_type="top_surface",
            line_role_visibility="cosmetic",
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
            xy_min_feature_size_mm=2.0,
            xy_nominal_feature_size_mm=4.0,
            z_feature_height_mm=8.0,
            vertical_extent_mm=8.0,
            vertical_extent_layers=33,
            target_layer_height_mm=0.24,
            line_type="internal_perimeter",
            line_role_visibility="structural",
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
        xy_min_feature_size_mm=5.0,
        xy_nominal_feature_size_mm=12.0,
        z_feature_height_mm=12.0,
        vertical_extent_mm=12.0,
        vertical_extent_layers=30,
        target_layer_height_mm=0.40,
        line_type="sparse_infill",
        line_role_visibility="hidden",
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
        xy_min_feature_size_mm=as_float(raw.get("xy_min_feature_size_mm"), as_float(raw.get("min_feature_size_mm"), 1.0)),
        xy_nominal_feature_size_mm=as_float(raw.get("xy_nominal_feature_size_mm"), as_float(raw.get("min_feature_size_mm"), 1.0)),
        z_feature_height_mm=as_float(raw.get("z_feature_height_mm"), as_float(raw.get("target_layer_height_mm"), 0.20)),
        vertical_extent_mm=as_float(raw.get("vertical_extent_mm"), as_float(raw.get("target_layer_height_mm"), 0.20)),
        vertical_extent_layers=as_int(raw.get("vertical_extent_layers"), 1),
        target_layer_height_mm=as_float(raw.get("target_layer_height_mm"), 0.20),
        surface_slope_degrees=as_float(raw.get("surface_slope_degrees"), 0.0),
        local_z_candidate=as_bool(raw.get("local_z_candidate"), False),
        z_resolution_criticality=str(raw.get("z_resolution_criticality", "none")),
        line_type=str(raw.get("line_type", "internal_perimeter")),
        line_role_visibility=str(raw.get("line_role_visibility", raw.get("visibility", "internal"))),
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


def is_visible_or_cosmetic(region: Region) -> bool:
    return region.visibility == "visible" or region.line_role_visibility in {"visible", "cosmetic", "mating"}


def is_hidden_or_internal(region: Region) -> bool:
    return region.visibility in {"hidden", "internal"} and region.line_role_visibility in {"hidden", "internal", "structural"}


def add_z_risks(region: Region, risks: List[str]) -> None:
    if region.local_z_candidate:
        risks.append("local_z_candidate")
    if region.local_z_candidate and region.z_resolution_criticality in {"high", "micro"} and is_visible_or_cosmetic(region):
        risks.append("local_z_future_required")


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
        line_type=region.line_type,
        line_role_visibility=region.line_role_visibility,
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
    add_z_risks(region, risks)

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
            region.line_type,
            region.line_role_visibility,
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
    visible = is_visible_or_cosmetic(region)
    detail = region.detail_criticality
    line_type = region.line_type

    if line_type in {"bridge", "overhang"}:
        risks.append("bridge_or_overhang_sensitive")
        return finalize_assignment(region, "0.4", "0.4", "Bridge/overhang regions use conservative 0.4 fallback until validated.", risks, 0.60)

    if line_type == "support_interface":
        risks.append("support_interface_risk")
        return finalize_assignment(region, "0.4", "0.4", "Support interface is mating/quality-sensitive and stays conservative.", risks, 0.66)

    if line_type == "support":
        if is_hidden_or_internal(region) and region.estimated_region_area_mm2 >= 3000.0 and region.estimated_path_length_mm >= 3000.0:
            risks.append("support_large_tool_review")
            return finalize_assignment(region, "0.6", "0.4", "Non-interface support may use a larger tool only after review.", risks, 0.55)
        return finalize_assignment(region, "0.4", "0.4", "Support remains conservative unless enough non-interface support volume exists.", risks, 0.62)

    if line_type in {"painted_surface", "color_detail_skin"}:
        risks.append("future_surface_color_track")
        if detail in {"micro", "high"} and region.xy_min_feature_size_mm <= 0.45 and not risk_material:
            risks.append("high_cost_detail_tool")
            risks.append("preview_required")
            reason_parts.append("Painted/color-detail skin is visible cosmetic detail with fine XY/Z requirements.")
            return finalize_assignment(region, "0.2", "0.4", " ".join(reason_parts), risks, 0.68)
        risks.append("avoid_large_visible_tool")
        return finalize_assignment(region, "0.4", "0.2", "Painted/color-detail skin is visible/cosmetic and stays on a conservative visible-detail tool.", risks, 0.70)

    if line_type in {"top_surface", "bottom_surface"} and visible:
        if region.surface_slope_degrees > 10.0:
            risks.append("sloped_top_surface_visual_review")
        if detail in {"micro", "high"} and region.xy_min_feature_size_mm <= 0.40 and region.z_resolution_criticality in {"high", "micro"} and not risk_material:
            risks.append("high_cost_detail_tool")
            risks.append("preview_required")
            reason_parts.append("Visible top detail has fine XY/Z requirements; 0.2 is detail-driven, not speed-driven.")
            return finalize_assignment(region, "0.2", "0.4", " ".join(reason_parts), risks, 0.68)
        risks.append("avoid_large_visible_tool")
        return finalize_assignment(region, "0.4", "0.2", "Top/cosmetic surfaces stay on the conservative visible-detail class.", risks, 0.76)

    if line_type == "external_perimeter" and visible:
        if detail in {"micro", "high"} and not risk_material and region.xy_min_feature_size_mm >= 0.35 and region.z_feature_height_mm <= 0.20:
            risks.append("high_cost_detail_tool")
            risks.append("preview_required")
            reason_parts.append("Visible external perimeter detail is plausible for the 0.2 fine/detail class because XY and Z detail are both small.")
            return finalize_assignment(region, "0.2", "0.4", " ".join(reason_parts), risks, 0.72)
        if risk_material:
            risks.append(f"material_{region.material_risk}")
            reason_parts.append("0.2 is rejected for this material risk; use 0.4 as the safer visible-detail fallback.")
        else:
            risks.append("avoid_large_visible_tool")
            reason_parts.append("Visible external perimeter/detail geometry should use 0.4 unless fine XY/Z detail requires 0.2.")
        return finalize_assignment(region, "0.4", "0.4", " ".join(reason_parts), risks, 0.65)

    if detail == "micro" and visible:
        if not risk_material and region.xy_min_feature_size_mm >= 0.35 and region.z_resolution_criticality in {"high", "micro"}:
            risks.append("high_cost_detail_tool")
            risks.append("preview_required")
            reason_parts.append("Visible micro detail is plausible for the 0.2 fine/detail class when XY/Z metadata supports it.")
            return finalize_assignment(region, "0.2", "0.4", " ".join(reason_parts), risks, 0.70)
        risks.append("avoid_large_visible_tool")
        return finalize_assignment(region, "0.4", "0.4", "Visible detail lacks enough XY/Z evidence for 0.2; use 0.4 fallback.", risks, 0.65)

    if region.wall_or_bulk == "thin_wall":
        if region.min_feature_size_mm < 0.70:
            risks.append("reject_large_tool_for_thin_wall")
            return finalize_assignment(region, "0.4", "0.2", "Thin wall is too small for 0.6/0.8; use finer fallback.", risks, 0.62)
        return finalize_assignment(region, "0.4", "0.4", "Thin wall remains on the general class until validated.", risks, 0.70)

    if line_type == "internal_perimeter":
        if is_hidden_or_internal(region) and region.xy_min_feature_size_mm >= 1.8 and region.vertical_extent_layers >= 8:
            risks.append("internal_perimeter_width_review")
            return finalize_assignment(region, "0.6", "0.4", "Hidden/internal perimeter has enough XY size and vertical persistence for 0.6 review.", risks, 0.72)
        risks.append("thin_or_low_persistence_internal")
        return finalize_assignment(region, "0.4", "0.4", "Internal perimeter is too thin, visible, or vertically shallow for 0.6.", risks, 0.64)

    if line_type == "internal_solid_infill":
        if is_hidden_or_internal(region) and region.estimated_region_area_mm2 >= 3000.0 and region.estimated_path_length_mm >= 3000.0:
            risks.append("internal_solid_large_tool_review")
            return finalize_assignment(region, "0.6", "0.4", "Hidden/internal solid infill is a 0.6 review candidate.", risks, 0.68)
        return finalize_assignment(region, "0.4", "0.4", "Internal solid infill remains 0.4 until the region is large enough.", risks, 0.62)

    if line_type == "sparse_infill":
        if is_hidden_or_internal(region) and region.estimated_region_area_mm2 >= 3000.0 and region.estimated_path_length_mm >= 3000.0 and region.xy_min_feature_size_mm >= 3.0:
            risks.append("bulk_tool_cost_gate")
            return finalize_assignment(region, "0.8", "0.6", "Hidden sparse infill/bulk is large enough for the 0.8 bulk class if cost gates pass.", risks, 0.72)
        risks.append("medium_bulk")
        return finalize_assignment(region, "0.6", "0.4", "Sparse infill/bulk is not large enough for 0.8; use 0.6/0.4 fallback.", risks, 0.66)

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
        "line_type": assignment.line_type,
        "line_role_visibility": assignment.line_role_visibility,
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
        "| Region | Line type | Role | Tool | Layer class | Width class | Fallback | Cost gate | Cost reason | Confidence | Risk flags | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for item in assignments:
        row = assignment_row(item)
        lines.append(
            f"| `{row['region_name']}` | `{row['line_type']}` | `{row['line_role_visibility']}` | `{row['recommended_tool_class']}` | "
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
