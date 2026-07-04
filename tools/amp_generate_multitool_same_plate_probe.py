#!/usr/bin/env python3
"""Generate an AMP same-plate multi-profile probe assemble list.

The output is an ignored CLI assemble-list JSON plus a metadata file. It is a
proxy for preview/analysis only: Snapmaker Orca's assemble-list path supports
per-object print_params, but it does not load a separate full process profile
per object.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "outputs" / "amp_same_plate_multitool_probe"
REGION_BODY_DIR = REPO_ROOT / "outputs" / "amp_multitool_resolution_fixture" / "region_bodies"


REGIONS: list[dict[str, Any]] = [
    {
        "region_name": "micro_detail_zone",
        "stl": "micro_detail_zone.stl",
        "intended_tool_class": "0.2",
        "intended_nozzle": "0.2",
        "intended_layer_height": "0.06",
        "intended_line_width": "0.22",
        "intended_process_profile": "resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json",
        "filament_id": 1,
        "position": [-75.0, 45.0, 0.0],
    },
    {
        "region_name": "normal_visible_detail_zone",
        "stl": "normal_visible_detail_zone.stl",
        "intended_tool_class": "0.4",
        "intended_nozzle": "0.4",
        "intended_layer_height": "0.16",
        "intended_line_width": "0.42",
        "intended_process_profile": "resources/profiles/Snapmaker/process/0.16 Optimal @Snapmaker U1 (0.4 nozzle).json",
        "filament_id": 2,
        "position": [35.0, 45.0, 0.0],
    },
    {
        "region_name": "structural_shell_zone",
        "stl": "structural_shell_zone.stl",
        "intended_tool_class": "0.6",
        "intended_nozzle": "0.6",
        "intended_layer_height": "0.24",
        "intended_line_width": "0.62",
        "intended_process_profile": "resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json",
        "filament_id": 3,
        "position": [-70.0, -55.0, 0.0],
    },
    {
        "region_name": "bulk_zone",
        "stl": "bulk_zone.stl",
        "intended_tool_class": "0.8",
        "intended_nozzle": "0.8",
        "intended_layer_height": "0.40",
        "intended_line_width": "0.82",
        "intended_process_profile": "resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json",
        "filament_id": 4,
        "position": [50.0, -55.0, 0.0],
    },
]


def object_print_params(region: dict[str, Any]) -> dict[str, str]:
    """Return the closest per-object process proxy supported by assemble-list."""
    width = region["intended_line_width"]
    return {
        "wall_generator": "arachne",
        "layer_height": region["intended_layer_height"],
        "outer_wall_line_width": width,
        "inner_wall_line_width": width,
        "top_surface_line_width": width,
        "internal_solid_infill_line_width": width,
        "sparse_infill_line_width": width,
        "support_line_width": width,
    }


def build_probe(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    objects: list[dict[str, Any]] = []
    metadata_regions: list[dict[str, Any]] = []
    missing: list[str] = []

    for region in REGIONS:
        stl_path = REGION_BODY_DIR / region["stl"]
        if not stl_path.exists():
            missing.append(str(stl_path))

        params = object_print_params(region)
        pos_x, pos_y, pos_z = region["position"]
        objects.append(
            {
                "path": str(stl_path),
                "count": 1,
                "filaments": [region["filament_id"]],
                "pos_x": [pos_x],
                "pos_y": [pos_y],
                "pos_z": [pos_z],
                "print_params": params,
            }
        )

        metadata_regions.append(
            {
                "object_name": region["region_name"],
                "stl_path": str(stl_path),
                "intended_tool_class": region["intended_tool_class"],
                "intended_nozzle": region["intended_nozzle"],
                "intended_process_profile": region["intended_process_profile"],
                "intended_layer_height": region["intended_layer_height"],
                "filament_id": region["filament_id"],
                "position": region["position"],
                "object_print_params": params,
            }
        )

    if missing:
        missing_text = "\n".join(missing)
        raise FileNotFoundError(f"Missing region body STL(s):\n{missing_text}")

    assemble = {
        "plates": [
            {
                "plate_name": "AMP same-plate multi-profile process queue probe",
                "need_arrange": False,
                "objects": objects,
            }
        ]
    }
    metadata = {
        "purpose": "Preview/proxy same-plate representation of the offline AMP process-profile queue.",
        "limitations": [
            "Snapmaker Orca assemble-list supports per-object print_params, not independent full process-profile loading per object.",
            "The intended process profiles are recorded as metadata and approximated with per-object layer/line-width settings.",
            "This is not mixed-nozzle slicing and is not physical mixed-nozzle validation.",
        ],
        "regions": metadata_regions,
    }

    assemble_path = out_dir / "assemble_list.json"
    metadata_path = out_dir / "metadata.json"
    assemble_path.write_text(json.dumps(assemble, indent=2) + "\n", encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return assemble_path, metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for ignored assemble-list and metadata files.",
    )
    args = parser.parse_args()

    assemble_path, metadata_path = build_probe(args.out_dir)
    print(f"wrote {assemble_path}")
    print(f"wrote {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
