#!/usr/bin/env python3
"""Offline AMP resolution-allocation cost model prototype.

This tool estimates resolution and motion-cost tradeoffs from simple
geometry-like inputs. It does not inspect slicer geometry, write G-code, or
modify slicer behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


RECOMMEND_PRESERVE_DETAIL = "preserve_detail"
RECOMMEND_WIDEN_INTERNAL = "widen_internal"
RECOMMEND_INCREASE_LAYER_HEIGHT = "increase_layer_height"
RECOMMEND_CANDIDATE_OK = "candidate_ok"
RECOMMEND_REJECT_CANDIDATE = "reject_candidate"


@dataclass(frozen=True)
class RegionScenario:
    region_name: str
    visible_surface: bool
    top_surface: bool
    detail_critical: bool
    approximate_region_area_mm2: float
    approximate_path_length_mm: float
    wall_thickness_mm: float
    stock_line_width_mm: float
    candidate_line_width_mm: float
    stock_layer_height_mm: float
    candidate_layer_height_mm: float
    max_volumetric_flow_mm3_s: float
    nominal_speed_mm_s: float
    acceleration_penalty_factor: float = 1.0
    min_time_savings_fraction: float = 0.05


@dataclass(frozen=True)
class RegionEstimate:
    scenario: RegionScenario
    stock_path_count: int
    candidate_path_count: int
    stock_extrusion_volume_mm3: float
    candidate_extrusion_volume_mm3: float
    stock_effective_speed_mm_s: float
    candidate_effective_speed_mm_s: float
    stock_time_s: float
    candidate_time_s: float
    time_delta_s: float
    time_delta_fraction: float
    stock_flow_mm3_s: float
    candidate_flow_mm3_s: float
    resolution_risk_flag: str
    recommendation: str
    notes: str


def bool_from_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def scenario_from_dict(data: dict) -> RegionScenario:
    return RegionScenario(
        region_name=str(data["region_name"]),
        visible_surface=bool_from_value(data["visible_surface"]),
        top_surface=bool_from_value(data["top_surface"]),
        detail_critical=bool_from_value(data["detail_critical"]),
        approximate_region_area_mm2=float(data["approximate_region_area_mm2"]),
        approximate_path_length_mm=float(data["approximate_path_length_mm"]),
        wall_thickness_mm=float(data["wall_thickness_mm"]),
        stock_line_width_mm=float(data["stock_line_width_mm"]),
        candidate_line_width_mm=float(data["candidate_line_width_mm"]),
        stock_layer_height_mm=float(data["stock_layer_height_mm"]),
        candidate_layer_height_mm=float(data["candidate_layer_height_mm"]),
        max_volumetric_flow_mm3_s=float(data["max_volumetric_flow_mm3_s"]),
        nominal_speed_mm_s=float(data["nominal_speed_mm_s"]),
        acceleration_penalty_factor=float(data.get("acceleration_penalty_factor", 1.0)),
        min_time_savings_fraction=float(data.get("min_time_savings_fraction", 0.05)),
    )


def load_scenarios(path: Path) -> List[RegionScenario]:
    with path.open("r", encoding="utf-8-sig") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict):
        payload = payload.get("regions", [payload])
    if not isinstance(payload, list):
        raise ValueError("input JSON must be a region object, a list, or {'regions': [...]}")
    return [scenario_from_dict(item) for item in payload]


def positive_int_ceil(value: float) -> int:
    return max(1, int(math.ceil(value)))


def path_count(wall_thickness_mm: float, line_width_mm: float) -> int:
    if wall_thickness_mm <= 0 or line_width_mm <= 0:
        return 1
    return positive_int_ceil(wall_thickness_mm / line_width_mm)


def effective_speed(line_width_mm: float, layer_height_mm: float, nominal_speed_mm_s: float, max_flow_mm3_s: float) -> float:
    requested_flow = line_width_mm * layer_height_mm * nominal_speed_mm_s
    if requested_flow <= max_flow_mm3_s:
        return nominal_speed_mm_s
    return max_flow_mm3_s / max(line_width_mm * layer_height_mm, 1e-9)


def poor_residual_width(wall_thickness_mm: float, line_width_mm: float, count: int) -> bool:
    if count <= 1:
        return False
    residual = wall_thickness_mm - math.floor(wall_thickness_mm / line_width_mm) * line_width_mm
    return 0 < residual < line_width_mm * 0.35


def estimate_region(scenario: RegionScenario) -> RegionEstimate:
    stock_count = path_count(scenario.wall_thickness_mm, scenario.stock_line_width_mm)
    candidate_count = path_count(scenario.wall_thickness_mm, scenario.candidate_line_width_mm)

    stock_volume = scenario.approximate_path_length_mm * scenario.stock_line_width_mm * scenario.stock_layer_height_mm * stock_count
    candidate_volume = scenario.approximate_path_length_mm * scenario.candidate_line_width_mm * scenario.candidate_layer_height_mm * candidate_count

    stock_speed = effective_speed(
        scenario.stock_line_width_mm,
        scenario.stock_layer_height_mm,
        scenario.nominal_speed_mm_s,
        scenario.max_volumetric_flow_mm3_s,
    )
    candidate_speed = effective_speed(
        scenario.candidate_line_width_mm,
        scenario.candidate_layer_height_mm,
        scenario.nominal_speed_mm_s,
        scenario.max_volumetric_flow_mm3_s,
    )

    stock_time = scenario.approximate_path_length_mm * stock_count / max(stock_speed, 1e-9)
    candidate_time = scenario.approximate_path_length_mm * candidate_count / max(candidate_speed, 1e-9)
    stock_time *= max(scenario.acceleration_penalty_factor, 0.01)
    candidate_time *= max(scenario.acceleration_penalty_factor, 0.01)

    stock_flow = scenario.stock_line_width_mm * scenario.stock_layer_height_mm * scenario.nominal_speed_mm_s
    candidate_flow = scenario.candidate_line_width_mm * scenario.candidate_layer_height_mm * scenario.nominal_speed_mm_s
    time_delta = stock_time - candidate_time
    time_delta_fraction = time_delta / stock_time if stock_time > 0 else 0.0

    notes: List[str] = []
    risks: List[str] = []
    recommendation = RECOMMEND_CANDIDATE_OK

    if scenario.candidate_line_width_mm > scenario.wall_thickness_mm:
        risks.append("candidate_width_exceeds_wall")
        notes.append("candidate line width is wider than wall thickness")
        recommendation = RECOMMEND_REJECT_CANDIDATE

    if poor_residual_width(scenario.wall_thickness_mm, scenario.candidate_line_width_mm, candidate_count):
        risks.append("poor_residual_width")
        notes.append("candidate width leaves a narrow residual wall segment")
        if recommendation != RECOMMEND_REJECT_CANDIDATE:
            recommendation = RECOMMEND_REJECT_CANDIDATE

    if candidate_flow > scenario.max_volumetric_flow_mm3_s:
        risks.append("flow_limited")
        notes.append("candidate exceeds max volumetric flow at nominal speed and would need speed limiting")
        if recommendation != RECOMMEND_REJECT_CANDIDATE:
            recommendation = RECOMMEND_CANDIDATE_OK

    if scenario.visible_surface or scenario.detail_critical:
        risks.append("detail_visibility")
        notes.append("visible or detail-critical region should preserve conservative settings")
        if recommendation != RECOMMEND_REJECT_CANDIDATE:
            recommendation = RECOMMEND_PRESERVE_DETAIL

    if scenario.top_surface:
        risks.append("top_surface_conservative")
        notes.append("top-surface regions should be conservative until validated")
        if recommendation not in {RECOMMEND_REJECT_CANDIDATE, RECOMMEND_PRESERVE_DETAIL}:
            recommendation = RECOMMEND_PRESERVE_DETAIL

    if recommendation == RECOMMEND_CANDIDATE_OK:
        if time_delta_fraction < scenario.min_time_savings_fraction:
            risks.append("low_savings")
            notes.append("estimated time savings are below the configured threshold")
            recommendation = RECOMMEND_PRESERVE_DETAIL
        elif scenario.candidate_layer_height_mm > scenario.stock_layer_height_mm and scenario.candidate_line_width_mm == scenario.stock_line_width_mm:
            recommendation = RECOMMEND_INCREASE_LAYER_HEIGHT
        elif scenario.candidate_line_width_mm > scenario.stock_line_width_mm and not scenario.visible_surface:
            recommendation = RECOMMEND_WIDEN_INTERNAL

    risk_flag = ",".join(risks) if risks else "none"
    return RegionEstimate(
        scenario=scenario,
        stock_path_count=stock_count,
        candidate_path_count=candidate_count,
        stock_extrusion_volume_mm3=stock_volume,
        candidate_extrusion_volume_mm3=candidate_volume,
        stock_effective_speed_mm_s=stock_speed,
        candidate_effective_speed_mm_s=candidate_speed,
        stock_time_s=stock_time,
        candidate_time_s=candidate_time,
        time_delta_s=time_delta,
        time_delta_fraction=time_delta_fraction,
        stock_flow_mm3_s=stock_flow,
        candidate_flow_mm3_s=candidate_flow,
        resolution_risk_flag=risk_flag,
        recommendation=recommendation,
        notes="; ".join(notes) if notes else "candidate accepted by offline estimate",
    )


def example_scenarios() -> List[RegionScenario]:
    common = {
        "stock_line_width_mm": 0.42,
        "candidate_line_width_mm": 0.58,
        "stock_layer_height_mm": 0.20,
        "candidate_layer_height_mm": 0.20,
        "max_volumetric_flow_mm3_s": 12.0,
        "nominal_speed_mm_s": 80.0,
    }
    return [
        RegionScenario(
            region_name="visible logo/text region",
            visible_surface=True,
            top_surface=False,
            detail_critical=True,
            approximate_region_area_mm2=120.0,
            approximate_path_length_mm=240.0,
            wall_thickness_mm=1.2,
            **common,
        ),
        RegionScenario(
            region_name="hidden internal wall region",
            visible_surface=False,
            top_surface=False,
            detail_critical=False,
            approximate_region_area_mm2=800.0,
            approximate_path_length_mm=900.0,
            wall_thickness_mm=2.4,
            **common,
        ),
        RegionScenario(
            region_name="large infill/bulk region",
            visible_surface=False,
            top_surface=False,
            detail_critical=False,
            approximate_region_area_mm2=3500.0,
            approximate_path_length_mm=4200.0,
            wall_thickness_mm=8.0,
            stock_line_width_mm=0.42,
            candidate_line_width_mm=0.62,
            stock_layer_height_mm=0.20,
            candidate_layer_height_mm=0.28,
            max_volumetric_flow_mm3_s=12.0,
            nominal_speed_mm_s=80.0,
        ),
        RegionScenario(
            region_name="thick speaker ring wall",
            visible_surface=False,
            top_surface=False,
            detail_critical=False,
            approximate_region_area_mm2=1800.0,
            approximate_path_length_mm=2200.0,
            wall_thickness_mm=5.0,
            **common,
        ),
        RegionScenario(
            region_name="thin wall detail region",
            visible_surface=True,
            top_surface=False,
            detail_critical=True,
            approximate_region_area_mm2=90.0,
            approximate_path_length_mm=180.0,
            wall_thickness_mm=0.8,
            **common,
        ),
        RegionScenario(
            region_name="top cosmetic surface",
            visible_surface=True,
            top_surface=True,
            detail_critical=False,
            approximate_region_area_mm2=900.0,
            approximate_path_length_mm=1100.0,
            wall_thickness_mm=2.0,
            **common,
        ),
    ]


def estimate_all(scenarios: Iterable[RegionScenario]) -> List[RegionEstimate]:
    return [estimate_region(scenario) for scenario in scenarios]


def rows(estimates: Iterable[RegionEstimate]) -> List[dict]:
    output: List[dict] = []
    for estimate in estimates:
        scenario = estimate.scenario
        output.append(
            {
                "region_name": scenario.region_name,
                "visible_surface": scenario.visible_surface,
                "top_surface": scenario.top_surface,
                "detail_critical": scenario.detail_critical,
                "wall_thickness_mm": f"{scenario.wall_thickness_mm:.3f}",
                "stock_line_width_mm": f"{scenario.stock_line_width_mm:.3f}",
                "candidate_line_width_mm": f"{scenario.candidate_line_width_mm:.3f}",
                "stock_layer_height_mm": f"{scenario.stock_layer_height_mm:.3f}",
                "candidate_layer_height_mm": f"{scenario.candidate_layer_height_mm:.3f}",
                "stock_path_count": estimate.stock_path_count,
                "candidate_path_count": estimate.candidate_path_count,
                "stock_volume_mm3": f"{estimate.stock_extrusion_volume_mm3:.3f}",
                "candidate_volume_mm3": f"{estimate.candidate_extrusion_volume_mm3:.3f}",
                "stock_time_s": f"{estimate.stock_time_s:.3f}",
                "candidate_time_s": f"{estimate.candidate_time_s:.3f}",
                "time_delta_s": f"{estimate.time_delta_s:.3f}",
                "time_delta_percent": f"{estimate.time_delta_fraction * 100.0:.1f}",
                "stock_flow_mm3_s": f"{estimate.stock_flow_mm3_s:.3f}",
                "candidate_flow_mm3_s": f"{estimate.candidate_flow_mm3_s:.3f}",
                "resolution_risk_flag": estimate.resolution_risk_flag,
                "recommendation": estimate.recommendation,
                "notes": estimate.notes,
            }
        )
    return output


def write_csv(rows_: List[dict], path: Optional[Path]) -> None:
    fields = list(rows_[0].keys()) if rows_ else []
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = path.open("w", encoding="utf-8", newline="")
        close = True
    else:
        fh = sys.stdout
        close = False
    try:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows_:
            writer.writerow(row)
    finally:
        if close:
            fh.close()


def markdown_table(rows_: List[dict]) -> str:
    if not rows_:
        return "No scenarios.\n"
    fields = [
        "region_name",
        "stock_path_count",
        "candidate_path_count",
        "stock_time_s",
        "candidate_time_s",
        "time_delta_percent",
        "candidate_flow_mm3_s",
        "resolution_risk_flag",
        "recommendation",
    ]
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join("---" for _ in fields) + " |"
    lines = [header, sep]
    for row in rows_:
        lines.append("| " + " | ".join(str(row[field]) for field in fields) + " |")
    return "\n".join(lines) + "\n"


def write_markdown(rows_: List[dict], path: Optional[Path]) -> None:
    content = markdown_table(rows_)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    else:
        print(content, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON region scenario file")
    parser.add_argument("--examples", action="store_true", help="run built-in example scenarios")
    parser.add_argument("--format", choices=("markdown", "csv"), default="markdown")
    parser.add_argument("--out", type=Path, help="output path; stdout if omitted")
    args = parser.parse_args()

    if args.input:
        scenarios = load_scenarios(args.input)
    else:
        scenarios = example_scenarios()

    if not args.examples and not args.input:
        print("No input supplied; using built-in example scenarios. Pass --examples to make this explicit.", file=sys.stderr)

    result_rows = rows(estimate_all(scenarios))
    if args.format == "csv":
        write_csv(result_rows, args.out)
    else:
        write_markdown(result_rows, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
