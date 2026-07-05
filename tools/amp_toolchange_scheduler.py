#!/usr/bin/env python3
"""Offline AMP toolchange scheduling prototype.

This tool turns already-advisory AMP region resolution plans into a
toolchange-aware execution schedule. It does not emit production G-code,
toolchange commands, or slicer behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from amp_continuous_resolution_field import compute_plan, load_regions, region_from_dict


TOOL_ORDER = ("0.2", "0.4", "0.6", "0.8")
TOOL_INDEX = {tool: index for index, tool in enumerate(TOOL_ORDER)}
DETAIL_TO_BULK_ORDER = {"0.2": 0, "0.4": 1, "0.6": 2, "0.8": 3}
BULK_TO_DETAIL_ORDER = {"0.8": 0, "0.6": 1, "0.4": 2, "0.2": 3}

TOUCHSCREEN_REASON = (
    "U1 touchscreen-started mixed-nozzle execution remains blocked because "
    "current validation treats the first nozzle_diameter as authoritative."
)


@dataclass
class ScheduleStep:
    step_index: int
    region_name: str
    line_type: str
    visibility: str
    tool_class: str
    selected_process_profile: str
    selected_layer_height_mm: float
    selected_line_width_class: float
    requires_toolchange: bool
    previous_tool_class: str
    estimated_toolchange_cost_s: float
    reason: str
    risk_flags: list[str]
    fallback_if_rejected: str


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_process_queue(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    data = read_json(path)
    if isinstance(data, dict):
        if "slice_queue" in data:
            rows = data["slice_queue"]
        elif "resolution_plan" in data:
            rows = data["resolution_plan"]
        elif "regions" in data:
            rows = data["regions"]
        else:
            rows = []
    else:
        rows = data
    if not isinstance(rows, list):
        raise ValueError(f"{path} does not contain a queue array")
    by_region: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("region_name"):
            by_region[str(row["region_name"])] = row
    return by_region


def float_or(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def int_or(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_region_records(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    rows = data.get("regions", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"{path} does not contain a regions array")
    return [row for row in rows if isinstance(row, dict)]


def layer_key(record: dict[str, Any], original_index: int) -> tuple[int, float, int]:
    layer = record.get("layer_id", record.get("layer_index"))
    z = record.get("z_mm", record.get("z_height_mm"))
    return (int_or(layer, 0), float_or(z, 0.0), original_index)


def has_layer_order(records: Iterable[dict[str, Any]]) -> bool:
    for record in records:
        if any(key in record for key in ("layer_id", "layer_index", "z_mm", "z_height_mm")):
            return True
    return False


def schedule_priority(record: dict[str, Any], plan: dict[str, Any], mode: str, original_index: int, default_tool: str) -> tuple[Any, ...]:
    tool = str(plan.get("quantized_tool_class", "0.4"))
    line_type = str(record.get("line_type", ""))
    visibility = str(record.get("visibility", ""))
    detail = float_or(plan.get("desired_detail_score"), 0.0)
    bulk = float_or(plan.get("desired_bulk_score"), 0.0)
    layer = layer_key(record, original_index)

    if mode == "layer_ordered":
        return (*layer, TOOL_INDEX.get(tool, 99), original_index)
    if mode == "detail_first":
        quality_rank = 0 if visibility == "visible" or detail >= 0.65 else 1
        return (quality_rank, DETAIL_TO_BULK_ORDER.get(tool, 99), -detail, *layer, original_index)
    if mode == "bulk_first":
        bulk_rank = 0 if line_type == "sparse_infill" or bulk >= 0.50 else 1
        return (bulk_rank, BULK_TO_DETAIL_ORDER.get(tool, 99), -bulk, *layer, original_index)
    if mode == "minimize_toolchanges":
        current_rank = 0 if tool == default_tool else 1
        return (current_rank, TOOL_INDEX.get(tool, 99), *layer, original_index)
    raise ValueError(f"unsupported scheduling mode: {mode}")


def mode_reason(mode: str, tool: str, record: dict[str, Any], plan: dict[str, Any]) -> str:
    base = str(plan.get("reason", plan.get("continuous_reason", "advisory region assignment")))
    if mode == "detail_first" and tool in {"0.2", "0.4"}:
        return f"quality-driven detail-first step; {base}"
    if mode == "bulk_first" and tool in {"0.6", "0.8"}:
        return f"throughput-driven bulk-first step; {base}"
    if mode == "minimize_toolchanges":
        return f"grouped to reduce tool transitions; {base}"
    if mode == "layer_ordered":
        return f"layer/order-preserving step; {base}"
    return base


def fallback_text(plan: dict[str, Any], current_tool: str) -> str:
    flags = [str(flag) for flag in plan.get("risk_flags", [])]
    fallback = str(plan.get("fallback_tool_class", current_tool))
    if "toolchange_cost_gate_failed" in flags:
        return f"use fallback tool {fallback}; region did not pass toolchange cost gate"
    if any("touchscreen" in flag.lower() for flag in flags):
        return f"use single-authoritative-nozzle workflow or fallback tool {fallback} for touchscreen-started jobs"
    return f"fallback tool {fallback} if scheduling or hardware validation rejects this step"


def plan_records(region_records: list[dict[str, Any]], process_queue: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, record in enumerate(region_records):
        region = region_from_dict(record)
        plan = asdict(compute_plan(region))
        queued = process_queue.get(region.region_name, {})
        if queued:
            if queued.get("selected_process_profile") or queued.get("process_profile"):
                plan["selected_process_profile"] = queued.get("selected_process_profile", queued.get("process_profile"))
            if queued.get("selected_layer_height_mm"):
                plan["quantized_layer_height"] = float_or(queued.get("selected_layer_height_mm"), plan["quantized_layer_height"])
            if queued.get("selected_line_width_class"):
                plan["quantized_line_width_class"] = float_or(queued.get("selected_line_width_class"), plan["quantized_line_width_class"])
        rows.append({"original_index": index, "record": record, "plan": plan})
    return rows


def ordered_records(rows: list[dict[str, Any]], mode: str, default_tool: str) -> list[dict[str, Any]]:
    if mode != "layer_ordered" and has_layer_order([row["record"] for row in rows]):
        grouped: dict[tuple[int, float], list[dict[str, Any]]] = {}
        for row in rows:
            record = row["record"]
            key = layer_key(record, int(row["original_index"]))[:2]
            grouped.setdefault(key, []).append(row)
        ordered: list[dict[str, Any]] = []
        for key in sorted(grouped):
            ordered.extend(sorted(grouped[key], key=lambda row: schedule_priority(row["record"], row["plan"], mode, int(row["original_index"]), default_tool)))
        return ordered
    return sorted(rows, key=lambda row: schedule_priority(row["record"], row["plan"], mode, int(row["original_index"]), default_tool))


def schedule(
    region_records: list[dict[str, Any]],
    process_queue: dict[str, dict[str, Any]],
    mode: str,
    default_tool: str,
    toolchange_cost_s: float,
) -> list[ScheduleStep]:
    planned = ordered_records(plan_records(region_records, process_queue), mode, default_tool)
    previous_tool = default_tool
    steps: list[ScheduleStep] = []
    for index, row in enumerate(planned, start=1):
        record = row["record"]
        plan = row["plan"]
        tool = str(plan.get("quantized_tool_class", default_tool))
        requires_toolchange = tool != previous_tool
        cost = toolchange_cost_s if requires_toolchange else 0.0
        risk_flags = [str(flag) for flag in plan.get("risk_flags", [])]
        if mode == "detail_first" and tool in {"0.2", "0.4"}:
            risk_flags.append("quality_driven")
        if mode == "bulk_first" and tool in {"0.6", "0.8"}:
            risk_flags.append("throughput_driven")
        if mode == "minimize_toolchanges":
            risk_flags.append("same_tool_grouping")
        steps.append(
            ScheduleStep(
                step_index=index,
                region_name=str(plan.get("region_name", record.get("region_name", "unnamed_region"))),
                line_type=str(plan.get("line_type", record.get("line_type", ""))),
                visibility=str(plan.get("visibility", record.get("visibility", ""))),
                tool_class=tool,
                selected_process_profile=str(plan.get("selected_process_profile", "")),
                selected_layer_height_mm=float_or(plan.get("quantized_layer_height"), 0.0),
                selected_line_width_class=float_or(plan.get("quantized_line_width_class"), 0.0),
                requires_toolchange=requires_toolchange,
                previous_tool_class=previous_tool,
                estimated_toolchange_cost_s=cost,
                reason=mode_reason(mode, tool, record, plan),
                risk_flags=risk_flags,
                fallback_if_rejected=fallback_text(plan, default_tool),
            )
        )
        previous_tool = tool
    return steps


def toolchange_count(steps: list[ScheduleStep]) -> int:
    return sum(1 for step in steps if step.requires_toolchange)


def total_toolchange_cost(steps: list[ScheduleStep]) -> float:
    return round(sum(step.estimated_toolchange_cost_s for step in steps), 3)


def payload_for(mode: str, steps: list[ScheduleStep]) -> dict[str, Any]:
    return {
        "scheduling_mode": mode,
        "touchscreen_mixed_nozzle_blocked": True,
        "touchscreen_block_reason": TOUCHSCREEN_REASON,
        "fluidd_experimental_future_possible": True,
        "fluidd_note": "Future Fluidd-only mixed-nozzle experimentation remains hardware-dependent and developer-only.",
        "toolchange_count": toolchange_count(steps),
        "estimated_toolchange_cost_s": total_toolchange_cost(steps),
        "schedule": [asdict(step) for step in steps],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8", newline="\n")


def write_summary_csv(path: Path, schedules: dict[str, list[ScheduleStep]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "mode",
        "step_index",
        "region_name",
        "tool_class",
        "requires_toolchange",
        "previous_tool_class",
        "estimated_toolchange_cost_s",
        "selected_layer_height_mm",
        "selected_line_width_class",
        "selected_process_profile",
        "risk_flags",
        "fallback_if_rejected",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for mode, steps in schedules.items():
            for step in steps:
                row = asdict(step)
                row["mode"] = mode
                row["risk_flags"] = "; ".join(step.risk_flags)
                writer.writerow({field: row.get(field, "") for field in fields})


def write_summary_markdown(path: Path, schedules: dict[str, list[ScheduleStep]]) -> None:
    lines = [
        "# AMP Toolchange Scheduler Output Summary",
        "",
        "This is offline/advisory output only. It does not emit production T-code or mixed-nozzle G-code.",
        "",
        "| Mode | Toolchanges | Estimated toolchange cost | Tool sequence |",
        "| --- | ---: | ---: | --- |",
    ]
    for mode, steps in schedules.items():
        sequence = " -> ".join(step.tool_class for step in steps)
        lines.append(f"| `{mode}` | {toolchange_count(steps)} | {total_toolchange_cost(steps):.1f}s | `{sequence}` |")
    for mode, steps in schedules.items():
        lines.extend(["", f"## {mode}", "", "| Step | Region | Tool | Change | Layer | Width | Reason |", "| ---: | --- | --- | --- | ---: | ---: | --- |"])
        for step in steps:
            lines.append(
                f"| {step.step_index} | `{step.region_name}` | `{step.tool_class}` | "
                f"{step.requires_toolchange} | {step.selected_layer_height_mm:.2f} | "
                f"{step.selected_line_width_class:.2f} | {step.reason} |"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_pseudo_gcode(path: Path, mode: str, steps: list[ScheduleStep]) -> None:
    lines = [
        "; PSEUDO ONLY - NOT PRINTABLE",
        "; AMP offline advisory toolchange schedule",
        f"; scheduling_mode={mode}",
        "; This file intentionally contains comments only.",
    ]
    for step in steps:
        tool_number = TOOL_INDEX.get(step.tool_class, -1)
        lines.extend(
            [
                f"; STEP {step.step_index} region={step.region_name} tool={step.tool_class} process={step.selected_process_profile}",
                f"; WOULD_SELECT_TOOL T{tool_number}",
                f"; requires_toolchange={str(step.requires_toolchange).lower()} cost_s={step.estimated_toolchange_cost_s:.1f}",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Region metadata JSON")
    parser.add_argument("--process-queue", help="Optional existing process queue or resolution plan JSON")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--toolchange-cost-s", type=float, default=60.0)
    parser.add_argument("--default-tool-class", default="0.4")
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["minimize_toolchanges", "detail_first", "bulk_first", "layer_ordered"],
        choices=["minimize_toolchanges", "detail_first", "bulk_first", "layer_ordered"],
    )
    parser.add_argument("--pseudo-gcode", help="Optional comments-only pseudo schedule path")
    args = parser.parse_args()

    records = load_region_records(Path(args.input))
    queue = load_process_queue(Path(args.process_queue)) if args.process_queue else {}
    out_dir = Path(args.out_dir)
    schedules: dict[str, list[ScheduleStep]] = {}
    for mode in args.modes:
        steps = schedule(records, queue, mode, args.default_tool_class, args.toolchange_cost_s)
        schedules[mode] = steps
        write_json(out_dir / f"schedule_{mode}.json", payload_for(mode, steps))
    write_summary_markdown(out_dir / "schedule_summary.md", schedules)
    write_summary_csv(out_dir / "schedule_summary.csv", schedules)
    if args.pseudo_gcode:
        write_pseudo_gcode(Path(args.pseudo_gcode), "minimize_toolchanges", schedules["minimize_toolchanges"])

    for mode, steps in schedules.items():
        sequence = " -> ".join(step.tool_class for step in steps)
        print(f"{mode}: {toolchange_count(steps)} toolchange(s), {total_toolchange_cost(steps):.1f}s, sequence {sequence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
