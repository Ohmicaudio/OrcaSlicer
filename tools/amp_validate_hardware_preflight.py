#!/usr/bin/env python3
"""Validate AMP Fluidd/Klipper hardware preflight checklist state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALID_STATUSES = {"pending", "passed", "failed", "not_applicable"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def filled_status_map(filled_path: Path | None) -> dict[str, dict[str, Any]]:
    if filled_path is None:
        return {}
    payload = read_json(filled_path)
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        raise ValueError("filled checklist must contain a checks array")
    result: dict[str, dict[str, Any]] = {}
    for check in checks:
        if not isinstance(check, dict) or "check_id" not in check:
            raise ValueError("filled checklist entries must contain check_id")
        result[str(check["check_id"])] = check
    return result


def validate(checklist_path: Path, filled_path: Path | None = None) -> dict[str, Any]:
    checklist = read_json(checklist_path)
    checks = checklist.get("checks", [])
    if not isinstance(checks, list):
        raise ValueError("checklist must contain a checks array")

    filled = filled_status_map(filled_path)
    pending: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    passed: list[dict[str, Any]] = []

    merged_checks: list[dict[str, Any]] = []
    for check in checks:
        if not isinstance(check, dict):
            invalid.append({"check_id": "unknown", "reason": "check entry is not an object"})
            continue
        check_id = str(check.get("check_id", "unknown"))
        required = bool(check.get("required", False))
        override = filled.get(check_id, {})
        status = str(override.get("status", check.get("status_default", "pending")))
        evidence = str(override.get("evidence", ""))

        merged = dict(check)
        merged["status"] = status
        merged["evidence"] = evidence
        merged_checks.append(merged)

        if status not in VALID_STATUSES:
            invalid.append({"check_id": check_id, "reason": f"invalid status: {status}"})
            continue
        if required and status == "pending":
            pending.append(merged)
        elif required and status == "failed":
            failed.append(merged)
        elif required and status == "not_applicable":
            invalid.append({"check_id": check_id, "reason": "required check cannot be not_applicable"})
        elif required and status == "passed":
            if not evidence:
                invalid.append({"check_id": check_id, "reason": "required passed check must include evidence"})
            else:
                passed.append(merged)

    not_ready_reasons = []
    if pending:
        not_ready_reasons.append("required checks are pending")
    if failed:
        not_ready_reasons.append("required checks failed")
    if invalid:
        not_ready_reasons.append("checklist has invalid entries")

    ready = not pending and not failed and not invalid
    return {
        "schema_version": "0.1",
        "ready": ready,
        "status": "ready" if ready else "not_ready",
        "check_count": len(merged_checks),
        "required_count": sum(1 for check in merged_checks if check.get("required")),
        "passed_required_count": len(passed),
        "pending_required_count": len(pending),
        "failed_required_count": len(failed),
        "invalid_count": len(invalid),
        "not_ready_reasons": not_ready_reasons,
        "pending": [{"check_id": item["check_id"], "description": item["description"]} for item in pending],
        "failed": [{"check_id": item["check_id"], "description": item["description"]} for item in failed],
        "invalid": invalid,
    }


def markdown_report(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# AMP Fluidd/Klipper Hardware Preflight Result",
        "",
        f"- Status: `{payload['status']}`",
        f"- Ready: `{str(payload['ready']).lower()}`",
        f"- Required checks: `{payload['required_count']}`",
        f"- Passed required checks: `{payload['passed_required_count']}`",
        f"- Pending required checks: `{payload['pending_required_count']}`",
        f"- Failed required checks: `{payload['failed_required_count']}`",
        f"- Invalid checks: `{payload['invalid_count']}`",
        "",
        "## Not Ready Reasons",
        "",
    ]
    lines.extend([f"- {reason}" for reason in payload["not_ready_reasons"]] or ["- None"])

    lines.extend(["", "## Pending Required Checks", ""])
    lines.extend([f"- `{item['check_id']}`: {item['description']}" for item in payload["pending"]] or ["- None"])

    lines.extend(["", "## Failed Required Checks", ""])
    lines.extend([f"- `{item['check_id']}`: {item['description']}" for item in payload["failed"]] or ["- None"])

    lines.extend(["", "## Invalid Checks", ""])
    lines.extend([f"- `{item['check_id']}`: {item['reason']}" for item in payload["invalid"]] or ["- None"])

    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not implement mixed-nozzle slicing.",
            "- This does not flash or modify firmware.",
            "- This does not generate production tool-selection commands.",
            "- This does not generate a printable mixed-nozzle file.",
            "- This does not validate physical mixed-nozzle behavior.",
            "- This does not bypass Snapmaker touchscreen nozzle validation.",
        ]
    )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checklist", required=True, help="Preflight checklist JSON")
    parser.add_argument("--filled-checklist", help="Optional filled checklist JSON")
    parser.add_argument("--out", required=True, help="JSON output path")
    parser.add_argument("--markdown", required=True, help="Markdown output path")
    args = parser.parse_args()

    payload = validate(Path(args.checklist), Path(args.filled_checklist) if args.filled_checklist else None)
    write_json(Path(args.out), payload)
    write_text(Path(args.markdown), markdown_report(payload))
    print(
        f"status={payload['status']} ready={str(payload['ready']).lower()} "
        f"pending_required={payload['pending_required_count']} failed_required={payload['failed_required_count']} "
        f"invalid={payload['invalid_count']}"
    )
    return 0 if payload["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
