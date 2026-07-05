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

FORBIDDEN_CLAIM_FRAGMENTS = {
    "mixed-nozzle" " works",
    "bypass" " safety",
    "factory" "-tested",
    "production t0",
    "production t1",
    "production t2",
    "production t3",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def entries_by_region(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return {}
    return {
        str(entry.get("region_name")): entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("region_name") is not None
    }


def add_golden_errors(payload: dict[str, Any], golden: dict[str, Any], errors: list[str]) -> None:
    golden_mode = golden.get("generation_mode")
    if golden_mode is not None and payload.get("generation_mode") != golden_mode:
        errors.append(
            f"generation_mode {payload.get('generation_mode')!r} does not match golden {golden_mode!r}"
        )

    golden_regions = entries_by_region(golden)
    payload_regions = entries_by_region(payload)
    if set(payload_regions) != set(golden_regions):
        errors.append(
            "region_name set does not match golden: "
            f"expected {sorted(golden_regions)}, got {sorted(payload_regions)}"
        )

    for region_name, golden_entry in sorted(golden_regions.items()):
        payload_entry = payload_regions.get(region_name)
        if payload_entry is None:
            continue
        missing_fields = sorted(set(golden_entry) - set(payload_entry))
        if missing_fields:
            errors.append(f"{region_name} missing golden fields: {', '.join(missing_fields)}")
        if payload_entry.get("touchscreen_mixed_nozzle_blocked") is not True:
            errors.append(f"{region_name} does not explicitly keep touchscreen mixed-nozzle blocked")

    serialized = json.dumps(payload, sort_keys=True).lower()
    found_claims = sorted(fragment for fragment in FORBIDDEN_CLAIM_FRAGMENTS if fragment in serialized)
    if found_claims:
        errors.append(f"forbidden production claim fragments found: {', '.join(found_claims)}")


def check(path: Path, golden: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = load_json(path)
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

    if golden is not None and isinstance(payload, dict):
        add_golden_errors(payload, golden, errors)

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
    parser.add_argument("--golden", help="optional golden debug artifact contract fixture")
    args = parser.parse_args()

    golden = load_json(Path(args.golden)) if args.golden else None
    results = [check(Path(path), golden=golden) for path in args.paths]
    print(json.dumps({"results": results}, indent=2))
    return 0 if all(result["passed"] for result in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
