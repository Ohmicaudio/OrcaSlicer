#!/usr/bin/env python3
"""Check AMP offline debug artifact JSON against the C++ packet-compatible schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUPPORTED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "slicer_build_info",
    "generation_mode",
    "touchscreen_mixed_nozzle_blocked",
    "fluidd_experimental_future_possible",
    "warnings",
    "entries",
    "observation_summary",
}

SUPPORTED_ENTRY_FIELDS = {
    "object_id",
    "layer_id",
    "region_id",
    "region_name",
    "plan_reason",
    "confidence",
    "toolchange_requested",
    "bead_width_override_present",
    "nozzle_override_present",
    "source_stage",
    "recommended_tool_class",
    "fallback_tool_class",
    "selected_process_profile",
    "selected_layer_height_mm",
    "selected_line_width_class",
    "cost_gate_passed",
    "cost_gate_reason",
    "fallback_reason",
    "risk_flags",
    "local_z_future_required",
    "touchscreen_mixed_nozzle_blocked",
    "warnings",
}

PACKET_ENTRY_FIELDS = {
    "region_name",
    "recommended_tool_class",
    "fallback_tool_class",
    "selected_process_profile",
    "selected_layer_height_mm",
    "selected_line_width_class",
    "cost_gate_passed",
    "cost_gate_reason",
    "fallback_reason",
    "risk_flags",
    "local_z_future_required",
    "touchscreen_mixed_nozzle_blocked",
}


def check(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {"path": str(path), "passed": False, "errors": ["debug artifact root is not an object"], "warnings": []}

    unsupported_top = sorted(set(payload) - SUPPORTED_TOP_LEVEL_FIELDS)
    if unsupported_top:
        errors.append(f"unsupported top-level fields: {', '.join(unsupported_top)}")

    if payload.get("generation_mode") not in {"offline_advisory", "disabled", "enabled_noop", "enabled_readonly"}:
        errors.append(f"unsupported generation_mode: {payload.get('generation_mode')!r}")

    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        errors.append("entries is not an array")
        entries = []

    packet_field_hits: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry {index} is not an object")
            continue
        unsupported_entry = sorted(set(entry) - SUPPORTED_ENTRY_FIELDS)
        if unsupported_entry:
            errors.append(f"entry {index} has unsupported fields: {', '.join(unsupported_entry)}")
        packet_field_hits.update(set(entry) & PACKET_ENTRY_FIELDS)

    missing_packet_fields = sorted(PACKET_ENTRY_FIELDS - packet_field_hits)
    if missing_packet_fields:
        warnings.append(
            "debug artifact does not yet populate all packet-compatible fields: "
            + ", ".join(missing_packet_fields)
        )

    return {
        "path": str(path).replace("\\", "/"),
        "passed": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "entry_count": len(entries),
        "packet_fields_present": sorted(packet_field_hits),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="debug_artifact.json paths")
    args = parser.parse_args()

    results = [check(Path(path)) for path in args.paths]
    print(json.dumps({"results": results}, indent=2))
    return 0 if all(result["passed"] for result in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
