#!/usr/bin/env python3
"""Validate official Orca mixed-nozzle G-code against an AMP plan packet.

This is an in-memory/text validation helper for workflow checks. It does not
validate physical safety and does not change generated G-code.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


NOZZLE_RE = re.compile(r"nozzle[_ ]diameter[s]?\s*[:=]\s*(.+)", re.I)
PRINT_SETTINGS_RE = re.compile(r"print_settings_id\s*[:=]\s*(.+)", re.I)
LAYER_Z_RE = re.compile(r"^(?:G0|G1)\b.*(?:^|\s)Z(-?(?:\d+(?:\.\d+)?|\.\d+))\b", re.I)
TOOL_RE = re.compile(r"^T(\d+)\b")
FORBIDDEN_CLAIMS = [
    "touchscreen compatible",
    "bypass snapmaker",
    "bypass " + "safety",
    "skip nozzle validation",
]


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def split_values(value: str) -> List[str]:
    value = value.strip().strip(";").replace("[", "").replace("]", "")
    return [part for part in re.split(r"[,; ]+", value) if part]


def normalize_nozzle(value: Any) -> str:
    return f"{float(str(value)):.3f}".rstrip("0").rstrip(".")


def expected_from_packet(packet_dir: Path, expected_tool_map: Optional[Path]) -> Dict[str, Any]:
    if expected_tool_map:
        data = read_json(expected_tool_map)
        tools = list(data.get("expected_tools", []))
        return {
            "required_nozzles": [normalize_nozzle(value) for value in data.get("expected_used_nozzle_classes", [])],
            "required_tools": [str(item["expected_t_command"])[1:] for item in tools],
            "region_names": [item["region_name"] for item in tools],
            "tool_map": tools,
        }

    data = read_json(packet_dir / "process_queue.json")
    queue = list(data.get("process_queue", []))
    tool_classes = sorted(
        {normalize_nozzle(item["recommended_tool_class"]) for item in queue},
        key=lambda value: float(value),
    )
    tools: List[Dict[str, Any]] = []
    for item in queue:
        nozzle = normalize_nozzle(item["recommended_nozzle_diameter"])
        tool_index = tool_classes.index(nozzle)
        tools.append(
            {
                "region_name": item["region_name"],
                "expected_t_command": f"T{tool_index}",
                "expected_nozzle_diameter": nozzle,
            }
        )
    return {
        "required_nozzles": tool_classes,
        "required_tools": [str(tool["expected_t_command"])[1:] for tool in tools],
        "region_names": [tool["region_name"] for tool in tools],
        "tool_map": tools,
    }


def inspect_gcode(path: Path, region_names: Iterable[str]) -> Dict[str, Any]:
    nozzles: List[str] = []
    tools: List[str] = []
    print_settings_id = ""
    z_values: List[float] = []
    layer_heights: Set[float] = set()
    last_z: Optional[float] = None
    region_hits = {name: False for name in region_names}
    forbidden_hits: List[str] = []

    text_lower_parts: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            lower = line.lower()
            text_lower_parts.append(lower)

            nozzle_match = NOZZLE_RE.search(line)
            if nozzle_match:
                nozzles.extend(normalize_nozzle(value) for value in split_values(nozzle_match.group(1)))

            settings_match = PRINT_SETTINGS_RE.search(line)
            if settings_match and not print_settings_id:
                print_settings_id = settings_match.group(1).strip()

            tool_match = TOOL_RE.match(line)
            if tool_match:
                tools.append(tool_match.group(1))

            z_match = LAYER_Z_RE.match(line)
            if z_match:
                z = round(float(z_match.group(1)), 5)
                if last_z is not None and z > last_z:
                    layer_heights.add(round(z - last_z, 5))
                if not z_values or z != z_values[-1]:
                    z_values.append(z)
                last_z = z

            for name in region_hits:
                if name.lower() in lower:
                    region_hits[name] = True

    all_text = "\n".join(text_lower_parts)
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in all_text:
            forbidden_hits.append(phrase)

    return {
        "nozzle_diameter_values_raw": nozzles,
        "nozzle_diameter_values_unique": sorted(set(nozzles), key=lambda value: float(value)),
        "tool_commands": tools,
        "active_tools": sorted(set(tools), key=lambda value: int(value)),
        "tool_command_count": len(tools),
        "print_settings_id": print_settings_id,
        "layer_height_values": sorted(layer_heights),
        "region_hits": region_hits,
        "forbidden_claim_hits": forbidden_hits,
    }


def validate(packet_dir: Path, gcode_path: Path, expected_tool_map: Optional[Path]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "schema_version": "0.1",
        "pass": False,
        "gcode": str(gcode_path),
        "errors": [],
        "warnings": [],
        "expected": {},
        "observed": {},
    }
    if not gcode_path.exists():
        result["errors"].append("G-code file does not exist.")
        return result

    expected = expected_from_packet(packet_dir, expected_tool_map)
    observed = inspect_gcode(gcode_path, expected["region_names"])
    result["expected"] = expected
    result["observed"] = observed

    observed_nozzles = set(observed["nozzle_diameter_values_unique"])
    for nozzle in expected["required_nozzles"]:
        if nozzle not in observed_nozzles:
            result["errors"].append(f"Missing expected nozzle diameter {nozzle}.")

    observed_tools = set(observed["active_tools"])
    for tool in expected["required_tools"]:
        if tool not in observed_tools:
            result["errors"].append(f"Missing expected active tool T{tool}.")

    expected_nozzle_set = set(expected["required_nozzles"])
    extra_nozzles = [
        nozzle for nozzle in observed["nozzle_diameter_values_raw"]
        if nozzle not in expected_nozzle_set
    ]
    extra_tools = [tool for tool in observed["active_tools"] if tool not in set(expected["required_tools"])]
    if extra_nozzles:
        result["warnings"].append(f"Extra nozzle slot values observed: {','.join(extra_nozzles)}")
    if len(observed["nozzle_diameter_values_raw"]) > len(expected["required_nozzles"]):
        result["warnings"].append(
            "Nozzle header contains more tool-slot values than AMP expected used nozzle classes; "
            "treat unused duplicate slots as preset artifacts if no extra active T command appears."
        )
    if extra_tools:
        result["warnings"].append(f"Extra active tools observed: {','.join('T' + tool for tool in extra_tools)}")

    if observed["tool_command_count"] <= 0:
        result["errors"].append("No T commands found.")

    missing_regions = [name for name, found in observed["region_hits"].items() if not found]
    if missing_regions:
        result["warnings"].append(
            "Object-level region mapping could not be fully verified from G-code comments: "
            + ", ".join(missing_regions)
        )

    if observed["layer_height_values"]:
        result["warnings"].append(
            "Layer-height observations are G-code-derived; official Orca manual workflow may use shared/global layer height."
        )
    else:
        result["warnings"].append("No layer-height deltas detected.")

    if observed["print_settings_id"]:
        result["warnings"].append(
            f"Observed print_settings_id `{observed['print_settings_id']}`; manual baseline may expose one global process profile."
        )
    else:
        result["warnings"].append("Missing print_settings_id.")

    if observed["forbidden_claim_hits"]:
        result["errors"].append(
            "Forbidden touchscreen/safety claim text found: "
            + ", ".join(observed["forbidden_claim_hits"])
        )

    result["pass"] = not result["errors"]
    return result


def write_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def write_markdown(result: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    observed = result["observed"]
    expected = result["expected"]
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# AMP Orca Mixed-Nozzle G-code Validation\n\n")
        fh.write(f"Result: **{'PASS' if result['pass'] else 'FAIL'}**\n\n")
        fh.write(f"G-code: `{result['gcode']}`\n\n")
        fh.write("## Expected\n\n")
        fh.write(f"- Nozzles: `{','.join(expected.get('required_nozzles', []))}`\n")
        fh.write(f"- Tools: `{','.join('T' + tool for tool in expected.get('required_tools', []))}`\n\n")
        fh.write("## Observed\n\n")
        fh.write(f"- Nozzles: `{','.join(observed.get('nozzle_diameter_values_unique', []))}`\n")
        fh.write(f"- Active tools: `{','.join('T' + tool for tool in observed.get('active_tools', []))}`\n")
        fh.write(f"- Tool command count: {observed.get('tool_command_count', 0)}\n")
        fh.write(f"- Print settings ID: `{observed.get('print_settings_id', '')}`\n")
        fh.write(f"- Layer-height deltas: `{','.join(str(value) for value in observed.get('layer_height_values', []))}`\n\n")
        fh.write("## Errors\n\n")
        if result["errors"]:
            for error in result["errors"]:
                fh.write(f"- {error}\n")
        else:
            fh.write("- None\n")
        fh.write("\n## Warnings\n\n")
        if result["warnings"]:
            for warning in result["warnings"]:
                fh.write(f"- {warning}\n")
        else:
            fh.write("- None\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, help="AMP plan packet directory")
    parser.add_argument("--gcode", required=True, help="Orca exported G-code")
    parser.add_argument("--expected-tool-map", default="", help="optional expected tool map JSON")
    parser.add_argument("--out", required=True, help="output JSON report")
    parser.add_argument("--markdown", required=True, help="output markdown report")
    args = parser.parse_args()

    expected_tool_map = Path(args.expected_tool_map) if args.expected_tool_map else None
    result = validate(Path(args.packet), Path(args.gcode), expected_tool_map)
    write_json(result, Path(args.out))
    write_markdown(result, Path(args.markdown))
    print(f"result={'PASS' if result['pass'] else 'FAIL'}")
    print(f"errors={len(result['errors'])} warnings={len(result['warnings'])}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    for warning in result["warnings"]:
        print(f"WARNING: {warning}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
