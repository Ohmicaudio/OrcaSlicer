#!/usr/bin/env python3
"""Extract a U1 nozzle/layer/width capability matrix from Snapmaker profiles."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


NOZZLE_RE = re.compile(r"nozzle[_ )-]*(0\.[2468])|0\.[0-9]+\s+.*\((0\.[2468]) nozzle\)")
LAYER_RE = re.compile(r"(?:fdm_process_U1_)?(0\.\d+)")


@dataclass
class ToolFamily:
    nozzle: str
    layer_heights: Set[str] = field(default_factory=set)
    line_widths: Set[str] = field(default_factory=set)
    outer_widths: Set[str] = field(default_factory=set)
    inner_widths: Set[str] = field(default_factory=set)
    process_files: List[str] = field(default_factory=list)


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def first_string(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list) and value:
        return str(value[0])
    return str(value)


def normalize_float_string(value: object) -> Optional[str]:
    text = first_string(value)
    if not text:
        return None
    try:
        return f"{float(text):.2f}".rstrip("0").rstrip(".")
    except ValueError:
        return text


def nozzle_from_path(path: Path) -> Optional[str]:
    text = path.name
    if "U1" not in text:
        return None
    match = NOZZLE_RE.search(text)
    if match:
        return match.group(1) or match.group(2)
    if "fdm_process_U1_0." in text and "nozzle_" not in text:
        return "0.4"
    return None


def layer_from_path(path: Path) -> Optional[str]:
    match = LAYER_RE.search(path.stem)
    if not match:
        return None
    try:
        return f"{float(match.group(1)):.2f}".rstrip("0").rstrip(".")
    except ValueError:
        return match.group(1)


def suitability(nozzle: str) -> Dict[str, str]:
    return {
        "0.2": {
            "visible_detail": "high: micro/fine visible detail",
            "structural_shell": "limited: small shells and fine features",
            "bulk": "low: too slow for bulk except tiny parts",
            "notes": "Use for fine visible detail and small text; current U1 profiles begin at 0.06 mm layer height.",
        },
        "0.4": {
            "visible_detail": "high: general visible/detail",
            "structural_shell": "medium: normal shell work",
            "bulk": "medium: general-purpose fallback",
            "notes": "General U1 detail/shell default class.",
        },
        "0.6": {
            "visible_detail": "medium: coarse visible detail only",
            "structural_shell": "high: structural shell / medium bulk",
            "bulk": "high: useful for larger internal regions",
            "notes": "Good candidate for non-cosmetic shell and medium bulk regions.",
        },
        "0.8": {
            "visible_detail": "low: avoid fine visible detail",
            "structural_shell": "medium: large simple shells only",
            "bulk": "high: bulk / fast internal regions",
            "notes": "Bulk class; 0.56 mm is the largest observed U1 layer height in current profiles.",
        },
    }[nozzle]


def collect(process_dir: Path, machine_path: Path) -> List[Dict[str, str]]:
    machine = load_json(machine_path)
    declared_nozzles = first_string(machine.get("nozzle_diameter")) or ""
    declared = [item.strip() for item in declared_nozzles.split(";") if item.strip()]
    families = {nozzle: ToolFamily(nozzle=nozzle) for nozzle in declared}

    # Base/common 0.4 widths live in the inherited U1 profiles.
    base_04_widths: Dict[str, Optional[str]] = {}
    for base_name in ("fdm_process_U1.json", "fdm_process_U1_common.json"):
        path = process_dir / base_name
        if not path.exists():
            continue
        data = load_json(path)
        for key in ("line_width", "outer_wall_line_width", "inner_wall_line_width"):
            value = normalize_float_string(data.get(key))
            if value:
                base_04_widths[key] = value

    for path in sorted(process_dir.glob("*.json")):
        if "copy" in path.name or "_old" in path.name:
            continue
        nozzle = nozzle_from_path(path)
        if nozzle not in families:
            continue
        data = load_json(path)
        layer = normalize_float_string(data.get("layer_height")) or layer_from_path(path)
        if layer:
            families[nozzle].layer_heights.add(layer)
        for key, target in (
            ("line_width", families[nozzle].line_widths),
            ("outer_wall_line_width", families[nozzle].outer_widths),
            ("inner_wall_line_width", families[nozzle].inner_widths),
        ):
            value = normalize_float_string(data.get(key))
            if value:
                target.add(value)
        families[nozzle].process_files.append(path.name)

    if "0.4" in families:
        for value in base_04_widths.values():
            if value:
                families["0.4"].line_widths.add(value)
        if base_04_widths.get("outer_wall_line_width"):
            families["0.4"].outer_widths.add(base_04_widths["outer_wall_line_width"])
        if base_04_widths.get("inner_wall_line_width"):
            families["0.4"].inner_widths.add(base_04_widths["inner_wall_line_width"])

    rows: List[Dict[str, str]] = []
    for nozzle in sorted(families, key=float):
        family = families[nozzle]
        suitability_info = suitability(nozzle)
        rows.append({
            "nozzle_diameter": nozzle,
            "available_layer_heights": ";".join(sorted(family.layer_heights, key=float)),
            "observed_line_widths": ";".join(sorted(family.line_widths, key=float)),
            "observed_outer_widths": ";".join(sorted(family.outer_widths, key=float)),
            "observed_inner_widths": ";".join(sorted(family.inner_widths, key=float)),
            "visible_detail_suitability": suitability_info["visible_detail"],
            "structural_shell_suitability": suitability_info["structural_shell"],
            "bulk_suitability": suitability_info["bulk"],
            "notes": suitability_info["notes"],
            "process_file_count": str(len(family.process_files)),
        })
    return rows


def write_csv(rows: Iterable[Dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fields = [
        "nozzle_diameter",
        "available_layer_heights",
        "observed_line_widths",
        "observed_outer_widths",
        "observed_inner_widths",
        "visible_detail_suitability",
        "structural_shell_suitability",
        "bulk_suitability",
        "notes",
        "process_file_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--machine", default="resources/profiles/Snapmaker/machine/Snapmaker U1.json")
    parser.add_argument("--process-dir", default="resources/profiles/Snapmaker/process")
    parser.add_argument("--out", default="outputs/amp_tool_matrix/u1_tool_capability_matrix.csv")
    args = parser.parse_args()

    rows = collect(Path(args.process_dir), Path(args.machine))
    write_csv(rows, Path(args.out))
    print(f"wrote {args.out} with {len(rows)} tool class rows")
    for row in rows:
        print(
            f"{row['nozzle_diameter']} nozzle: layers {row['available_layer_heights']} "
            f"widths {row['observed_line_widths']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
