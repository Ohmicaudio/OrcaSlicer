#!/usr/bin/env python3
"""Inspect G-code for mixed-nozzle / multi-tool evidence.

This is a lightweight text inspector for AMP and external fork probes. It does
not validate print safety or physical behavior.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


NOZZLE_RE = re.compile(r"nozzle[_ ]diameter[s]?\s*[:=]\s*(.+)", re.I)
PRINT_SETTINGS_RE = re.compile(r"print_settings_id\s*[:=]\s*(.+)", re.I)
LAYER_Z_RE = re.compile(r"^(?:G0|G1)\b.*(?:^|\s)Z(-?(?:\d+(?:\.\d+)?|\.\d+))\b", re.I)
TOOL_RE = re.compile(r"^T(\d+)\b")
EXTRUDER_COMMENT_RE = re.compile(r"\b(?:extruder|tool)\s*[:=]\s*(\d+)", re.I)
E_RE = re.compile(r"(?:^|\s)E(-?(?:\d+(?:\.\d+)?|\.\d+))")


def parse_e_value(line: str) -> Optional[float]:
    match = E_RE.search(line)
    return float(match.group(1)) if match else None


def split_values(value: str) -> List[str]:
    value = value.strip().strip(";")
    value = value.replace("[", "").replace("]", "")
    parts = re.split(r"[,; ]+", value)
    return [part for part in (p.strip() for p in parts) if part]


def inspect_file(path: Path) -> Dict[str, object]:
    row: Dict[str, object] = {
        "file": str(path),
        "nozzle_diameter_values": "",
        "nozzle_diameter_count": 0,
        "print_settings_id": "",
        "tool_commands": 0,
        "active_tools": "",
        "layer_height_values": "",
        "layer_height_count": 0,
        "extrusion_moves": 0,
        "per_tool_extrusion_moves": "",
        "wipe_tower_comment_hits": 0,
        "purge_comment_hits": 0,
        "support_comment_hits": 0,
        "line_width_comment_hits": 0,
        "possible_mixed_nozzle_evidence": "no",
        "warnings": "",
    }
    if not path.exists():
        row["warnings"] = "missing file"
        return row

    nozzle_values: List[str] = []
    tools: Set[str] = set()
    z_values: List[float] = []
    layer_heights: Set[float] = set()
    current_tool = "unknown"
    per_tool_extrusions: Dict[str, int] = {}
    warnings: List[str] = []
    last_z: Optional[float] = None
    last_e: Optional[float] = None
    relative_extrusion = False

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            lower = line.lower()

            nozzle_match = NOZZLE_RE.search(line)
            if nozzle_match:
                nozzle_values.extend(split_values(nozzle_match.group(1)))

            settings_match = PRINT_SETTINGS_RE.search(line)
            if settings_match and not row["print_settings_id"]:
                row["print_settings_id"] = settings_match.group(1).strip()

            tool_match = TOOL_RE.match(line)
            if tool_match:
                current_tool = tool_match.group(1)
                tools.add(current_tool)
                row["tool_commands"] = int(row["tool_commands"]) + 1

            extruder_comment = EXTRUDER_COMMENT_RE.search(line)
            if extruder_comment:
                current_tool = extruder_comment.group(1)
                tools.add(current_tool)

            if re.match(r"^M83\b", line):
                relative_extrusion = True
            elif re.match(r"^M82\b", line):
                relative_extrusion = False
            elif re.match(r"^G92\b", line):
                e_value = parse_e_value(line)
                if e_value is not None:
                    last_e = e_value

            z_match = LAYER_Z_RE.match(line)
            if z_match:
                z = round(float(z_match.group(1)), 5)
                if last_z is not None and z > last_z:
                    layer_heights.add(round(z - last_z, 5))
                if not z_values or z != z_values[-1]:
                    z_values.append(z)
                last_z = z

            if line.startswith(("G0", "G1")):
                e_value = parse_e_value(line)
                if e_value is not None:
                    positive_e = e_value if relative_extrusion else (e_value - last_e if last_e is not None else 0.0)
                    if positive_e > 0:
                        row["extrusion_moves"] = int(row["extrusion_moves"]) + 1
                        per_tool_extrusions[current_tool] = per_tool_extrusions.get(current_tool, 0) + 1
                    if not relative_extrusion:
                        last_e = e_value

            if "wipe tower" in lower or "wipe_tower" in lower:
                row["wipe_tower_comment_hits"] = int(row["wipe_tower_comment_hits"]) + 1
            if "purge" in lower or "flush" in lower:
                row["purge_comment_hits"] = int(row["purge_comment_hits"]) + 1
            if "support" in lower or "interface" in lower or "raft" in lower:
                row["support_comment_hits"] = int(row["support_comment_hits"]) + 1
            if "line width" in lower or "line_width" in lower or "extrusion width" in lower:
                row["line_width_comment_hits"] = int(row["line_width_comment_hits"]) + 1

    unique_nozzle_values = sorted(set(nozzle_values))
    unique_layer_heights = sorted(layer_heights)
    row["nozzle_diameter_values"] = ",".join(unique_nozzle_values)
    row["nozzle_diameter_count"] = len(unique_nozzle_values)
    row["active_tools"] = ",".join(sorted(tools, key=lambda x: (x == "unknown", int(x) if x.isdigit() else 9999, x)))
    row["layer_height_values"] = ",".join(f"{value:.5g}" for value in unique_layer_heights)
    row["layer_height_count"] = len(unique_layer_heights)
    row["per_tool_extrusion_moves"] = "; ".join(f"{tool}={count}" for tool, count in sorted(per_tool_extrusions.items()))

    extrusion_tools = {
        tool
        for tool, count in per_tool_extrusions.items()
        if tool != "unknown" and count > 0
    }
    evidence = len(unique_nozzle_values) > 1 or len(extrusion_tools) > 1
    row["possible_mixed_nozzle_evidence"] = "yes" if evidence else "no"
    if len(unique_nozzle_values) <= 1:
        warnings.append("one or zero nozzle_diameter values found")
    if len(tools) <= 1:
        warnings.append("one or zero active tools found")
    if int(row["tool_commands"]) == 0:
        warnings.append("no explicit T commands found")
    elif len(extrusion_tools) <= 1:
        warnings.append("tool commands found, but extrusion was assigned to one or zero tools")
    if not row["print_settings_id"]:
        warnings.append("missing print_settings_id")
    row["warnings"] = "; ".join(warnings)
    return row


def collect_files(paths: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.gcode")))
        else:
            files.append(path)
    return files


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else [
        "file",
        "nozzle_diameter_values",
        "tool_commands",
        "active_tools",
        "warnings",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Mixed-Nozzle G-code Inspection Summary\n\n")
        if not rows:
            fh.write("No G-code files were inspected.\n")
            return
        fh.write("| File | Nozzle diameters | Tools | T commands | Layer heights | Evidence | Warnings |\n")
        fh.write("| --- | --- | --- | ---: | --- | --- | --- |\n")
        for row in rows:
            fh.write(
                f"| `{row['file']}` | `{row['nozzle_diameter_values']}` | `{row['active_tools']}` | "
                f"{row['tool_commands']} | `{row['layer_height_values']}` | "
                f"{row['possible_mixed_nozzle_evidence']} | {row['warnings']} |\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="G-code files or directories to inspect")
    parser.add_argument("--out", default="", help="optional output directory for CSV and markdown summary")
    args = parser.parse_args()

    rows = [inspect_file(path) for path in collect_files(args.paths)]
    for row in rows:
        print(
            f"{row['file']}: nozzles={row['nozzle_diameter_values'] or '-'} "
            f"tools={row['active_tools'] or '-'} t_commands={row['tool_commands']} "
            f"evidence={row['possible_mixed_nozzle_evidence']} warnings={row['warnings']}"
        )

    if args.out:
        out = Path(args.out)
        write_csv(rows, out / "mixed_nozzle_gcode_inspection.csv")
        write_summary(rows, out / "mixed_nozzle_gcode_inspection.md")
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
