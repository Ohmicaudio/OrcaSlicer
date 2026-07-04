#!/usr/bin/env python3
"""Compare AMP candidate tool slices against 0.4 baselines.

This helper consumes output from amp_gcode_metrics.py plus sweep metadata and
emits an offline/advisory cost-sensitivity table. It has no slicer integration
and does not inspect or write G-code.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


TOOLCHANGE_COSTS = (0, 5, 15, 30, 60)


def time_minutes(comment: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*min", comment or "")
    return int(match.group(1)) if match else None


def percent_delta(candidate: float, baseline: float) -> str:
    if baseline == 0:
        return ""
    return f"{((candidate - baseline) / baseline) * 100.0:.1f}"


def read_metrics(path: Path) -> Dict[str, Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_model: Dict[str, Dict[str, str]] = {}
    for row in rows:
        stem = Path(row["file"]).stem
        for suffix in ("_0p4_baseline", "_0p6_candidate", "_0p8_candidate"):
            if stem.endswith(suffix):
                by_model[stem[: -len(suffix)] + suffix] = row
                break
    return by_model


def read_metadata(path: Path) -> List[Dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    models = data.get("models", [])
    if not isinstance(models, list):
        raise ValueError(f"{path} does not contain a models array")
    return [item for item in models if isinstance(item, dict)]


def decision_for(region_type: str, candidate_tool: str, pre_savings_s: Optional[int], deltas: Dict[str, float]) -> str:
    if pre_savings_s is None:
        return "candidate_needs_visual_review"
    if pre_savings_s >= 60:
        return "candidate_wins"
    if candidate_tool == "0.8" and pre_savings_s < 0:
        return "fallback_0p4"
    if candidate_tool == "0.6" and pre_savings_s < 0:
        if deltas["extrusion_moves_pct"] < -25.0 or deltas["travel_moves_pct"] < -25.0:
            return "candidate_needs_visual_review"
        return "fallback_0p4"
    if region_type == "structural_shell":
        return "structural_or_quality_reason_only"
    return "candidate_needs_visual_review"


def build_rows(metrics_path: Path, metadata_path: Path) -> List[Dict[str, object]]:
    metrics = read_metrics(metrics_path)
    metadata = read_metadata(metadata_path)
    rows: List[Dict[str, object]] = []
    for item in metadata:
        model = str(item["model_name"])
        candidate_tool = str(item["intended_candidate_tool"])
        candidate_suffix = "_0p6_candidate" if candidate_tool == "0.6" else "_0p8_candidate"
        baseline = metrics.get(f"{model}_0p4_baseline")
        candidate = metrics.get(f"{model}{candidate_suffix}")
        if baseline is None or candidate is None:
            rows.append(
                {
                    "model_name": model,
                    "region_type": item.get("region_type", ""),
                    "size_class": item.get("size_class", ""),
                    "candidate_tool": candidate_tool,
                    "status": "missing_metrics",
                    "decision": "candidate_needs_visual_review",
                }
            )
            continue

        baseline_time = time_minutes(baseline.get("estimated_print_time_comment", ""))
        candidate_time = time_minutes(candidate.get("estimated_print_time_comment", ""))
        if baseline_time is None or candidate_time is None:
            pre_savings_s: Optional[int] = None
            m73_delta_min: Optional[int] = None
        else:
            m73_delta_min = candidate_time - baseline_time
            pre_savings_s = -m73_delta_min * 60

        deltas = {
            "file_size_pct": float(percent_delta(float(candidate["file_size_bytes"]), float(baseline["file_size_bytes"])) or 0.0),
            "extrusion_moves_pct": float(percent_delta(float(candidate["extrusion_moves"]), float(baseline["extrusion_moves"])) or 0.0),
            "travel_moves_pct": float(percent_delta(float(candidate["travel_moves"]), float(baseline["travel_moves"])) or 0.0),
            "positive_e_pct": float(percent_delta(float(candidate["total_positive_e"]), float(baseline["total_positive_e"])) or 0.0),
            "layer_count_pct": float(percent_delta(float(candidate["layer_count"]), float(baseline["layer_count"])) or 0.0),
        }
        row: Dict[str, object] = {
            "model_name": model,
            "region_type": item.get("region_type", ""),
            "size_class": item.get("size_class", ""),
            "candidate_tool": candidate_tool,
            "approximate_area_mm2": item.get("approximate_area_mm2", ""),
            "approximate_volume_mm3": item.get("approximate_volume_mm3", ""),
            "approximate_path_length_mm": item.get("approximate_path_length_mm", ""),
            "baseline_time": baseline.get("estimated_print_time_comment", ""),
            "candidate_time": candidate.get("estimated_print_time_comment", ""),
            "m73_delta_min": "" if m73_delta_min is None else m73_delta_min,
            "pre_toolchange_savings_s": "" if pre_savings_s is None else pre_savings_s,
            "file_size_delta_pct": f"{deltas['file_size_pct']:.1f}",
            "extrusion_moves_delta_pct": f"{deltas['extrusion_moves_pct']:.1f}",
            "travel_moves_delta_pct": f"{deltas['travel_moves_pct']:.1f}",
            "positive_e_delta_pct": f"{deltas['positive_e_pct']:.1f}",
            "layer_count_delta_pct": f"{deltas['layer_count_pct']:.1f}",
            "decision": decision_for(str(item.get("region_type", "")), candidate_tool, pre_savings_s, deltas),
            "status": "ok",
        }
        for cost in TOOLCHANGE_COSTS:
            row[f"net_savings_after_{cost}s_toolchange_s"] = "" if pre_savings_s is None else pre_savings_s - cost
        rows.append(row)
    return rows


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# AMP Multi-Tool Cost Sensitivity\n\n")
        fh.write("| Model | Candidate | Baseline time | Candidate time | Pre-toolchange savings | Net @60s | File size delta | Move delta | Travel delta | Positive E delta | Decision |\n")
        fh.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for row in rows:
            fh.write(
                f"| `{row.get('model_name', '')}` | {row.get('candidate_tool', '')} | "
                f"{row.get('baseline_time', '')} | {row.get('candidate_time', '')} | "
                f"{row.get('pre_toolchange_savings_s', '')} s | {row.get('net_savings_after_60s_toolchange_s', '')} s | "
                f"{row.get('file_size_delta_pct', '')}% | {row.get('extrusion_moves_delta_pct', '')}% | "
                f"{row.get('travel_moves_delta_pct', '')}% | {row.get('positive_e_delta_pct', '')}% | "
                f"{row.get('decision', '')} |\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()
    rows = build_rows(Path(args.metrics), Path(args.metadata))
    write_csv(rows, Path(args.out_csv))
    write_markdown(rows, Path(args.out_md))
    print(f"wrote {len(rows)} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
