#!/usr/bin/env python3
"""Collect lightweight G-code metrics for AMP benchmark reports."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional


TIME_RE = re.compile(r"(?:estimated printing time|estimated print time|print time|total time)\s*[:=]\s*(.+)", re.I)
FILAMENT_RE = re.compile(r"(?:filament used|total filament|filament length)\s*[:=]\s*(.+)", re.I)
TYPE_RE = re.compile(r"^\s*;\s*(?:TYPE|FEATURE|role)\s*[:=]\s*(.+)\s*$", re.I)
TOTAL_LAYER_RE = re.compile(r"^\s*;\s*total layer number\s*:\s*(\d+)\s*$", re.I)
M73_TIME_RE = re.compile(r"^\s*M73\b.*(?:^|\s)R(\d+)\b")


def parse_e_value(line: str) -> Optional[float]:
    match = re.search(r"(?:^|\s)E(-?\d+(?:\.\d+)?)", line)
    return float(match.group(1)) if match else None


def metric_row(path: Path) -> Dict[str, object]:
    row: Dict[str, object] = {
        "file": str(path),
        "file_size_bytes": path.stat().st_size if path.exists() else 0,
        "layer_count": 0,
        "tool_count": 0,
        "toolchange_count": 0,
        "extrusion_moves": 0,
        "travel_moves": 0,
        "total_positive_e": 0.0,
        "estimated_print_time_comment": "",
        "estimated_filament_comment": "",
        "type_comment_counts": "",
        "warnings": "",
    }
    if not path.exists():
        row["warnings"] = "missing file"
        return row

    last_e: Optional[float] = None
    tools = set()
    type_counts: Dict[str, int] = {}
    warnings: List[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            total_layer_match = TOTAL_LAYER_RE.match(stripped)
            if total_layer_match:
                row["layer_count"] = int(total_layer_match.group(1))
            if stripped.startswith(";LAYER:") or stripped.startswith("; layer "):
                row["layer_count"] = int(row["layer_count"]) + 1
            if re.match(r"^T\d+\b", stripped):
                tools.add(stripped.split()[0])
                row["toolchange_count"] = int(row["toolchange_count"]) + 1
            type_match = TYPE_RE.match(stripped)
            if type_match:
                key = type_match.group(1).strip()
                type_counts[key] = type_counts.get(key, 0) + 1
            time_match = TIME_RE.search(stripped)
            if time_match and not row["estimated_print_time_comment"]:
                row["estimated_print_time_comment"] = time_match.group(1).strip()
            m73_match = M73_TIME_RE.match(stripped)
            if m73_match and not row["estimated_print_time_comment"]:
                row["estimated_print_time_comment"] = f"{m73_match.group(1)} min (M73 R)"
            filament_match = FILAMENT_RE.search(stripped)
            if filament_match and not row["estimated_filament_comment"]:
                row["estimated_filament_comment"] = filament_match.group(1).strip()
            if stripped.startswith(("G0", "G1")):
                e_value = parse_e_value(stripped)
                has_xy = bool(re.search(r"(?:^|\s)[XY]-?\d", stripped))
                if e_value is not None:
                    if last_e is not None and e_value > last_e:
                        row["total_positive_e"] = float(row["total_positive_e"]) + (e_value - last_e)
                        row["extrusion_moves"] = int(row["extrusion_moves"]) + 1
                    last_e = e_value
                elif has_xy:
                    row["travel_moves"] = int(row["travel_moves"]) + 1

    row["tool_count"] = len(tools)
    row["type_comment_counts"] = "; ".join(f"{k}={v}" for k, v in sorted(type_counts.items()))
    if not row["estimated_print_time_comment"]:
        warnings.append("missing estimated print time comment")
    if not row["estimated_filament_comment"]:
        warnings.append("missing filament usage comment")
    if not row["type_comment_counts"]:
        warnings.append("missing role/type comments")
    row["warnings"] = "; ".join(warnings)
    row["total_positive_e"] = f"{float(row['total_positive_e']):.3f}"
    return row


def collect(paths: Iterable[Path]) -> List[Dict[str, object]]:
    return [metric_row(path) for path in paths]


def is_temp_gcode(path: Path) -> bool:
    return any(parent.name.endswith("_tmp") for parent in path.parents)


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "file",
        "file_size_bytes",
        "layer_count",
        "tool_count",
        "toolchange_count",
        "extrusion_moves",
        "travel_moves",
        "total_positive_e",
        "estimated_print_time_comment",
        "estimated_filament_comment",
        "type_comment_counts",
        "warnings",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_summary(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# AMP G-code Metrics Summary\n\n")
        if not rows:
            fh.write("No G-code files were found.\n")
            return
        fh.write("| File | Size bytes | Layers | Tools | Toolchanges | Extrusion moves | Travel moves | Total positive E | Warnings |\n")
        fh.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for row in rows:
            fh.write(
                f"| `{row['file']}` | {row['file_size_bytes']} | {row['layer_count']} | {row['tool_count']} | "
                f"{row['toolchange_count']} | {row['extrusion_moves']} | {row['travel_moves']} | "
                f"{row['total_positive_e']} | {row['warnings']} |\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="G-code files or directories to scan")
    parser.add_argument("--csv", default="outputs/amp_run_001/reports/metrics.csv")
    parser.add_argument("--summary", default="outputs/amp_run_001/reports/summary.md")
    args = parser.parse_args()

    files: List[Path] = []
    for item in args.paths:
        path = Path(item)
        if path.is_dir():
            files.extend(file for file in sorted(path.rglob("*.gcode")) if not is_temp_gcode(file))
        else:
            files.append(path)

    rows = collect(files)
    write_csv(rows, Path(args.csv))
    write_summary(rows, Path(args.summary))
    print(f"wrote {len(rows)} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
