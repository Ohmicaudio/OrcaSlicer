#!/usr/bin/env python3
"""Export a comments-only pseudo toolchange schedule from an AMP packet.

The output is intentionally non-printable. It never emits uncommented T-code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TOOL_TO_T = {"0.2": "T0", "0.4": "T1", "0.6": "T2", "0.8": "T3"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def risk_text(flags: Any) -> str:
    if isinstance(flags, list):
        return "; ".join(str(item) for item in flags)
    return str(flags or "")


def export(packet_dir: Path, out_path: Path) -> None:
    schedule_path = packet_dir / "toolchange_schedule.json"
    if not schedule_path.exists():
        raise FileNotFoundError(f"missing {schedule_path}")
    payload = read_json(schedule_path)
    steps = payload.get("schedule", [])
    if not isinstance(steps, list):
        raise ValueError("toolchange_schedule.json does not contain a schedule array")

    lines = [
        "; PSEUDO ONLY - NOT PRINTABLE",
        "; AMP offline advisory schedule",
        "; This does not implement mixed-nozzle slicing",
        "; Touchscreen-compatible mixed-nozzle execution remains blocked",
        f"; packet={str(packet_dir).replace(chr(92), '/')}",
        f"; scheduling_mode={payload.get('scheduling_mode', '')}",
        f"; toolchange_count={payload.get('toolchange_count', '')}",
        "",
    ]

    for step in steps:
        if not isinstance(step, dict):
            continue
        tool = str(step.get("tool_class", ""))
        pseudo_t = TOOL_TO_T.get(tool, "T?")
        lines.extend(
            [
                f"; STEP {step.get('step_index', '')}",
                f"; region={step.get('region_name', '')}",
                f"; intended_tool_class={tool}",
                f"; selected_process_profile={step.get('selected_process_profile', '')}",
                f"; selected_layer_height_mm={step.get('selected_layer_height_mm', '')}",
                f"; selected_line_width_class={step.get('selected_line_width_class', '')}",
                f"; requires_toolchange={str(step.get('requires_toolchange', '')).lower()}",
                f"; reason={step.get('reason', '')}",
                f"; risk_flags={risk_text(step.get('risk_flags', []))}",
                f"; WOULD_SELECT_TOOL {pseudo_t} for {tool}",
                "",
            ]
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="AMP packet directory")
    parser.add_argument("--out", required=True, help="Comments-only pseudo schedule path")
    args = parser.parse_args()
    export(Path(args.packet), Path(args.out))
    print(f"wrote comments-only pseudo schedule to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
