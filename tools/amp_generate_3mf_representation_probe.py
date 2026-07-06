#!/usr/bin/env python3
"""Generate an AMP 3MF representation probe manifest.

This tool does not write a 3MF project. It creates a structured manifest and
manual probe instructions for testing whether Snapmaker Orca can preserve AMP's
four-region process/tool intent through a richer project representation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REGION_ORDER = [
    "micro_detail_zone",
    "normal_visible_detail_zone",
    "structural_shell_zone",
    "bulk_zone",
]


PROCESS_QUEUE = {
    "micro_detail_zone": {
        "tool_class": "0.2",
        "intended_nozzle_diameter": 0.2,
        "intended_process_profile": "0.06 Standard @Snapmaker U1 (0.2 nozzle)",
        "selected_process_profile": "resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json",
        "intended_layer_height": 0.06,
        "intended_line_width_class": 0.22,
        "assigned_tool_slot": 1,
    },
    "normal_visible_detail_zone": {
        "tool_class": "0.4",
        "intended_nozzle_diameter": 0.4,
        "intended_process_profile": "0.16 Optimal @Snapmaker U1 (0.4 nozzle)",
        "selected_process_profile": "resources/profiles/Snapmaker/process/0.16 Optimal @Snapmaker U1 (0.4 nozzle).json",
        "intended_layer_height": 0.16,
        "intended_line_width_class": 0.42,
        "assigned_tool_slot": 2,
    },
    "structural_shell_zone": {
        "tool_class": "0.6",
        "intended_nozzle_diameter": 0.6,
        "intended_process_profile": "0.24 Standard @Snapmaker U1 (0.6 nozzle)",
        "selected_process_profile": "resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json",
        "intended_layer_height": 0.24,
        "intended_line_width_class": 0.62,
        "assigned_tool_slot": 3,
    },
    "bulk_zone": {
        "tool_class": "0.8",
        "intended_nozzle_diameter": 0.8,
        "intended_process_profile": "0.40 Standard @Snapmaker U1 (0.8 nozzle)",
        "selected_process_profile": "resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json",
        "intended_layer_height": 0.40,
        "intended_line_width_class": 0.82,
        "assigned_tool_slot": 4,
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def load_region_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    if isinstance(payload, dict):
        return payload
    return {}


def build_manifest(region_bodies: Path, region_metadata_path: Path) -> dict[str, Any]:
    metadata = load_region_metadata(region_metadata_path)
    metadata_regions = metadata.get("regions", []) if isinstance(metadata, dict) else []
    metadata_by_name = {
        str(region.get("region_name") or region.get("name")): region
        for region in metadata_regions
        if isinstance(region, dict)
    }

    regions: list[dict[str, Any]] = []
    for region_name in REGION_ORDER:
        queue = PROCESS_QUEUE[region_name]
        body_path = region_bodies / f"{region_name}.stl"
        regions.append(
            {
                "region_name": region_name,
                "region_body_path": str(body_path).replace("\\", "/"),
                "region_body_exists": body_path.exists(),
                "object_identity": region_name,
                "intended_tool_class": queue["tool_class"],
                "intended_nozzle_diameter": queue["intended_nozzle_diameter"],
                "intended_process_profile": queue["intended_process_profile"],
                "selected_process_profile": queue["selected_process_profile"],
                "intended_layer_height": queue["intended_layer_height"],
                "intended_line_width_class": queue["intended_line_width_class"],
                "assigned_filament_tool_slot": queue["assigned_tool_slot"],
                "source_metadata": metadata_by_name.get(region_name, {}),
            }
        )

    return {
        "schema_version": "0.1",
        "purpose": "AMP 3MF representation probe manifest. This is not a generated 3MF project.",
        "direct_3mf_generation": False,
        "direct_3mf_generation_reason": "Snapmaker/BBL 3MF writing requires exact model/project archives; this probe keeps representation intent explicit until a GUI or slicer-supported round trip is performed.",
        "region_bodies_dir": str(region_bodies).replace("\\", "/"),
        "region_metadata": str(region_metadata_path).replace("\\", "/"),
        "regions": regions,
        "non_claims": [
            "This does not implement mixed-nozzle slicing.",
            "This does not generate production T0/T1/T2/T3 commands.",
            "This does not generate a verified mixed-nozzle print.",
            "This does not validate physical mixed-nozzle behavior.",
            "This does not bypass Snapmaker touchscreen nozzle validation."
        ],
    }


def build_instructions(manifest_path: Path) -> list[str]:
    return [
        "# AMP 3MF Representation Probe Instructions",
        "",
        "This probe does not create a 3MF automatically. It defines the four-region AMP representation intent for a manual Snapmaker Orca GUI or future supported 3MF round-trip test.",
        "",
        f"Manifest: `{manifest_path.as_posix()}`",
        "",
        "## Manual Probe Steps",
        "",
        "1. Open Snapmaker Orca.",
        "2. Import each region body STL as a separate object:",
        "   - `micro_detail_zone.stl`",
        "   - `normal_visible_detail_zone.stl`",
        "   - `structural_shell_zone.stl`",
        "   - `bulk_zone.stl`",
        "3. Assign visible object names matching the region names.",
        "4. Attempt to assign distinct filament/tool slots matching the manifest.",
        "5. Attempt object-level settings only where the GUI supports them.",
        "6. Save as a project 3MF.",
        "7. Reopen the 3MF.",
        "8. Inspect whether object identities, extruder/tool slots, and any object-level settings survived.",
        "9. Export or slice only for representation diagnostics; do not treat output as mixed-nozzle validation.",
        "",
        "## Expected Probe Questions",
        "",
        "- Do all four objects remain distinct?",
        "- Do assigned extruder/tool slots survive save/load?",
        "- Are object-level line-width/layer-height settings available and preserved?",
        "- Is `nozzle_diameter` still project/global?",
        "- Does G-code export collapse to one process/nozzle class?",
        "",
        "## Non-Claims",
        "",
        "- This does not implement mixed-nozzle slicing.",
        "- This does not generate production tool-selection commands.",
        "- This does not generate a verified mixed-nozzle print.",
        "- This does not validate physical mixed-nozzle behavior.",
        "- This does not bypass Snapmaker touchscreen nozzle validation.",
    ]


def generate(region_bodies: Path, region_metadata: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(region_bodies, region_metadata)
    manifest_path = out_dir / "amp_3mf_representation_probe_manifest.json"
    instructions_path = out_dir / "amp_3mf_representation_probe_instructions.md"
    write_json(manifest_path, manifest)
    write_text(instructions_path, build_instructions(manifest_path))
    return {
        "manifest": str(manifest_path),
        "instructions": str(instructions_path),
        "region_count": len(manifest["regions"]),
        "all_bodies_exist": all(region["region_body_exists"] for region in manifest["regions"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region-bodies", default="outputs/amp_multitool_resolution_fixture/region_bodies")
    parser.add_argument("--region-metadata", default="docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json")
    parser.add_argument("--out", default="outputs/amp_3mf_representation_probe")
    args = parser.parse_args()

    result = generate(Path(args.region_bodies), Path(args.region_metadata), Path(args.out))
    print(f"wrote manifest={result['manifest']}")
    print(f"wrote instructions={result['instructions']}")
    print(f"region_count={result['region_count']} all_bodies_exist={str(result['all_bodies_exist']).lower()}")
    return 0 if result["all_bodies_exist"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
