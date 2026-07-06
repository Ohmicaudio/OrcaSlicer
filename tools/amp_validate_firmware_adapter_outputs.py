#!/usr/bin/env python3
"""Validate AMP firmware adapter pseudo and sandbox outputs.

The validator enforces that current AMP execution-adapter artifacts remain
offline/advisory and cannot accidentally become printable mixed-nozzle G-code.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LIVE_COMMAND_RE = re.compile(
    r"^\s*(?:"
    r"T[0-9]+\b|"
    r"G0\b|G1\b|"
    r"M104\b|M109\b|M140\b|M190\b|M106\b|M82\b|M83\b|"
    r"SET_GCODE_OFFSET\b|SAVE_GCODE_STATE\b|RESTORE_GCODE_STATE\b|"
    r"AMP_[A-Z0-9_]+\b|KTCC_[A-Z0-9_]+\b"
    r")",
    re.IGNORECASE,
)

EXTRUSION_RE = re.compile(r"^\s*G1\b.*\bE[-+0-9.]+", re.IGNORECASE)
REQUIRED_SANDBOX_HEADERS = [
    "AMP SANDBOX TEMPLATE ONLY",
    "NOT READY TO PRINT",
    "DO NOT INSTALL ON A PRINTER WITHOUT REVIEW",
]
REQUIRED_PER_REPORT_SAFETY_PHRASES = [
    "touchscreen",
    "physical",
    "validation",
    "production",
    "mixed-nozzle",
]

REQUIRED_GLOBAL_SAFETY_PHRASES = [
    "touchscreen",
    "blocked",
    "fluidd",
    "future",
    "does not bypass",
]


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    adapter_summary: list[dict[str, Any]] = field(default_factory=list)
    sandbox_summary: dict[str, Any] = field(default_factory=dict)
    safety_corpus: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def is_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith(";") or stripped.startswith("#")


def live_command_hits(path: Path, allow_respond: bool = True) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for index, line in enumerate(read_text(path).splitlines(), start=1):
        stripped = line.strip()
        if is_comment_or_blank(line):
            continue
        if allow_respond and stripped.upper().startswith("RESPOND "):
            continue
        if LIVE_COMMAND_RE.search(line) or EXTRUSION_RE.search(line):
            hits.append((index, line))
    return hits


def validate_non_printable_header(path: Path, result: ValidationResult) -> None:
    text = read_text(path)
    first_lines = "\n".join(text.splitlines()[:5]).lower()
    if "not printable" not in first_lines and "not ready to print" not in first_lines and "dry run only" not in first_lines:
        result.error(f"{path} missing clear non-printable warning near top")


def validate_pseudo_file(path: Path, result: ValidationResult, require_comments_only: bool = True) -> None:
    if not path.exists():
        result.error(f"missing pseudo file: {path}")
        return
    validate_non_printable_header(path, result)
    text = read_text(path)
    for line_number, line in enumerate(text.splitlines(), start=1):
        if require_comments_only and not is_comment_or_blank(line):
            result.error(f"{path}:{line_number} contains uncommented line: {line}")
    hits = live_command_hits(path)
    for line_number, line in hits:
        result.error(f"{path}:{line_number} contains live command: {line}")


def validate_safety_report(path: Path, result: ValidationResult) -> None:
    if not path.exists():
        result.error(f"missing safety report: {path}")
        return
    text = read_text(path)
    result.safety_corpus.append(text)
    text_lower = text.lower()
    for phrase in REQUIRED_PER_REPORT_SAFETY_PHRASES:
        if phrase.lower() not in text_lower:
            result.error(f"{path} missing safety phrase: {phrase}")


def validate_global_safety_corpus(result: ValidationResult) -> None:
    corpus = "\n".join(result.safety_corpus).lower()
    for phrase in REQUIRED_GLOBAL_SAFETY_PHRASES:
        if phrase not in corpus:
            result.error(f"safety report corpus missing global safety phrase: {phrase}")


def validate_adapter_plan(path: Path, adapter_id: str, result: ValidationResult) -> dict[str, Any]:
    if not path.exists():
        result.error(f"missing adapter plan: {path}")
        return {}
    payload = read_json(path)
    if payload.get("adapter_id") != adapter_id:
        result.error(f"{path} adapter_id mismatch: {payload.get('adapter_id')} != {adapter_id}")
    if payload.get("production_gcode") is not False:
        result.error(f"{path} must record production_gcode=false")
    if payload.get("comments_only") is not True:
        result.error(f"{path} must record comments_only=true")
    return payload


def adapter_status(adapter: dict[str, Any]) -> str:
    adapter_id = str(adapter.get("adapter_id", ""))
    if adapter_id == "snapmaker_touchscreen_blocked":
        return "blocked_advisory"
    if adapter_id == "snapmaker_fluidd_klipper_experimental":
        return "future_experimental"
    if adapter_id == "paxx12_u1_extended_firmware":
        return "research_only_future_experimental"
    if adapter_id in {"generic_klipper_macro", "klipper_ktcc_reference", "reprap_firmware_reference"}:
        return "reference_only"
    if adapter_id == "klipper_nozzlechange_extra":
        return "research_only"
    return "unknown"


def validate_manifest_consistency(manifest_path: Path, pseudo_root: Path, result: ValidationResult) -> None:
    manifest = read_json(manifest_path)
    adapters = manifest.get("adapters", [])
    if not isinstance(adapters, list):
        result.error("manifest adapters must be a list")
        return

    seen_nozzlechange = False
    for adapter in adapters:
        if not isinstance(adapter, dict):
            result.error("manifest adapter entry is not an object")
            continue
        adapter_id = str(adapter.get("adapter_id", ""))
        status = adapter_status(adapter)
        output_dir = pseudo_root / adapter_id
        emitted = output_dir.exists()
        if adapter_id == "klipper_nozzlechange_extra":
            seen_nozzlechange = True
            if emitted and status != "research_only":
                result.error("klipper_nozzlechange_extra must remain research-only unless source/command model is documented")
        elif not emitted:
            result.error(f"manifest adapter has no pseudo output: {adapter_id}")

        if adapter_id == "snapmaker_touchscreen_blocked":
            if adapter.get("supports_toolchange_commands") is not False or adapter.get("touchscreen_safe") is not False:
                result.error("snapmaker_touchscreen_blocked must be blocked/advisory only")
        if adapter_id == "snapmaker_fluidd_klipper_experimental":
            if adapter.get("requires_hardware_validation") is not True:
                result.error("snapmaker_fluidd_klipper_experimental must require hardware validation")
            if adapter.get("fluidd_only") is not True:
                result.error("snapmaker_fluidd_klipper_experimental must be marked fluidd_only")
        if adapter_id == "paxx12_u1_extended_firmware":
            if adapter.get("requires_hardware_validation") is not True:
                result.error("paxx12_u1_extended_firmware must require hardware validation")
            if adapter.get("fluidd_only") is not True:
                result.error("paxx12_u1_extended_firmware must be marked fluidd_only")
            if adapter.get("touchscreen_safe") is not False:
                result.error("paxx12_u1_extended_firmware must not be touchscreen safe")
            if adapter.get("supports_custom_klipper_includes") is not True:
                result.error("paxx12_u1_extended_firmware must record custom Klipper include support")
            if adapter.get("supports_print_hooks") is not True:
                result.error("paxx12_u1_extended_firmware must record print hook support")
        if adapter_id in {"generic_klipper_macro", "klipper_ktcc_reference", "reprap_firmware_reference"}:
            if adapter.get("requires_hardware_validation") is not True:
                result.error(f"{adapter_id} must require hardware validation")

        result.adapter_summary.append(
            {
                "adapter_id": adapter_id,
                "status": status,
                "pseudo_emitted": emitted,
                "touchscreen_safe": adapter.get("touchscreen_safe"),
                "fluidd_only": adapter.get("fluidd_only"),
                "requires_hardware_validation": adapter.get("requires_hardware_validation"),
            }
        )

    if not seen_nozzlechange:
        result.warn("klipper_nozzlechange_extra not in manifest; treated as research-only/not emitted")
        result.adapter_summary.append(
            {
                "adapter_id": "klipper_nozzlechange_extra",
                "status": "research_only_not_emitted",
                "pseudo_emitted": False,
                "touchscreen_safe": False,
                "fluidd_only": False,
                "requires_hardware_validation": True,
            }
        )


def validate_pseudo_outputs(pseudo_root: Path, result: ValidationResult) -> None:
    if not pseudo_root.exists():
        result.error(f"missing pseudo output root: {pseudo_root}")
        return
    for adapter_dir in sorted(path for path in pseudo_root.iterdir() if path.is_dir()):
        adapter_id = adapter_dir.name
        for expected in ["schedule.md", "pseudo.gcode.txt", "safety_report.md", "adapter_plan.json"]:
            if not (adapter_dir / expected).exists():
                result.error(f"{adapter_id} missing {expected}")
        validate_pseudo_file(adapter_dir / "pseudo.gcode.txt", result)
        validate_safety_report(adapter_dir / "safety_report.md", result)
        validate_adapter_plan(adapter_dir / "adapter_plan.json", adapter_id, result)


def validate_sandbox_headers(path: Path, result: ValidationResult) -> None:
    text = read_text(path)
    for header in REQUIRED_SANDBOX_HEADERS:
        if header not in text:
            result.error(f"{path} missing sandbox header: {header}")


def validate_tool_map(path: Path, result: ValidationResult) -> None:
    if not path.exists():
        result.error(f"missing tool map: {path}")
        return
    payload = read_json(path)
    entries = payload.get("tool_map", [])
    if not isinstance(entries, list):
        result.error("amp_tool_map.json tool_map must be a list")
        return
    by_class = {str(entry.get("tool_class")): entry for entry in entries if isinstance(entry, dict)}
    for tool_class in ["0.2", "0.4", "0.6", "0.8"]:
        if tool_class not in by_class:
            result.error(f"amp_tool_map.json missing tool class {tool_class}")
            continue
        entry = by_class[tool_class]
        if entry.get("requires_hardware_validation") is not True:
            result.error(f"tool class {tool_class} must require hardware validation")
        risk_text = " ".join(str(item) for item in entry.get("risk_flags", []))
        if "blocked" not in risk_text.lower() and "validation" not in risk_text.lower():
            result.error(f"tool class {tool_class} missing blocked/validation warning in risk flags")


def validate_sandbox(sandbox_root: Path, result: ValidationResult) -> None:
    if not sandbox_root.exists():
        result.error(f"missing sandbox root: {sandbox_root}")
        return

    expected = [
        "amp_tools.cfg.template",
        "amp_macros.cfg.template",
        "amp_dry_run_schedule.gcode.txt",
        "amp_preflight_checklist.md",
        "amp_safety_report.md",
        "amp_tool_map.json",
    ]
    for name in expected:
        if not (sandbox_root / name).exists():
            result.error(f"sandbox missing {name}")

    for cfg in ["amp_tools.cfg.template", "amp_macros.cfg.template"]:
        path = sandbox_root / cfg
        if path.exists():
            validate_sandbox_headers(path, result)
            for line_number, line in live_command_hits(path):
                result.error(f"{path}:{line_number} contains live command: {line}")

    validate_pseudo_file(sandbox_root / "amp_dry_run_schedule.gcode.txt", result)
    validate_safety_report(sandbox_root / "amp_safety_report.md", result)
    validate_tool_map(sandbox_root / "amp_tool_map.json", result)
    result.sandbox_summary = {"path": str(sandbox_root), "files_checked": expected}


def report_payload(result: ValidationResult) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "passed": result.passed,
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "errors": result.errors,
        "warnings": result.warnings,
        "adapter_summary": result.adapter_summary,
        "sandbox_summary": result.sandbox_summary,
    }


def markdown_report(result: ValidationResult) -> list[str]:
    lines = [
        "# AMP Firmware Adapter Output Validation Report",
        "",
        f"- Passed: `{str(result.passed).lower()}`",
        f"- Errors: `{len(result.errors)}`",
        f"- Warnings: `{len(result.warnings)}`",
        "",
        "## Adapter Summary",
        "",
        "| Adapter | Status | Pseudo emitted | Touchscreen safe | Fluidd only | Hardware validation |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in result.adapter_summary:
        lines.append(
            f"| `{item.get('adapter_id')}` | `{item.get('status')}` | {str(item.get('pseudo_emitted')).lower()} | "
            f"{str(item.get('touchscreen_safe')).lower()} | {str(item.get('fluidd_only')).lower()} | "
            f"{str(item.get('requires_hardware_validation')).lower()} |"
        )
    lines.extend(["", "## Errors", ""])
    lines.extend([f"- {error}" for error in result.errors] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {warning}" for warning in result.warnings] or ["- None"])
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not implement mixed-nozzle slicing.",
            "- This does not flash or modify printer firmware.",
            "- This does not generate production tool-selection commands.",
            "- This does not generate a single mixed-nozzle G-code print.",
            "- This does not validate physical mixed-nozzle behavior.",
            "- This does not bypass Snapmaker touchscreen nozzle validation.",
        ]
    )
    return lines


def validate(manifest: Path, pseudo_root: Path, sandbox_root: Path) -> ValidationResult:
    result = ValidationResult()
    validate_manifest_consistency(manifest, pseudo_root, result)
    validate_pseudo_outputs(pseudo_root, result)
    validate_sandbox(sandbox_root, result)
    validate_global_safety_corpus(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Adapter manifest JSON")
    parser.add_argument("--pseudo-root", required=True, help="Generated firmware adapter pseudo output root")
    parser.add_argument("--sandbox-root", required=True, help="Generated Fluidd/Klipper sandbox root")
    parser.add_argument("--out-json", required=True, help="JSON validation report path")
    parser.add_argument("--out-md", required=True, help="Markdown validation report path")
    args = parser.parse_args()

    result = validate(Path(args.manifest), Path(args.pseudo_root), Path(args.sandbox_root))
    write_json(Path(args.out_json), report_payload(result))
    write_text(Path(args.out_md), markdown_report(result))
    print(f"passed={str(result.passed).lower()} errors={len(result.errors)} warnings={len(result.warnings)}")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
