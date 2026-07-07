#!/usr/bin/env python3
"""Validate a non-executable AMP U1 Fluidd execution review bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "README_NOT_INSTALLABLE.md",
    "amp_plan/plan.json",
    "amp_plan/regions.json",
    "amp_plan/resolution_field.json",
    "amp_plan/tool_assignments.json",
    "amp_plan/process_queue.json",
    "amp_plan/toolchange_schedule.json",
    "amp_plan/per_region_gcode_status.json",
    "amp_plan/debug_artifact.json",
    "amp_plan/risk_report.md",
    "amp_3mf_sidecar/amp_multitool_resolution_fixture.amp3mf.zip",
    "fluidd_klipper_sandbox/amp_tools.cfg.template",
    "fluidd_klipper_sandbox/amp_macros.cfg.template",
    "fluidd_klipper_sandbox/amp_dry_run_schedule.gcode.txt",
    "fluidd_klipper_sandbox/amp_preflight_checklist.md",
    "fluidd_klipper_sandbox/amp_safety_report.md",
    "fluidd_klipper_sandbox/amp_tool_map.json",
    "safety/AMP_Fluidd_Klipper_Hardware_Preflight_001.md",
    "safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Checklist.json",
    "safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Result.md",
    "metadata/bundle_manifest.json",
    "metadata/file_hashes.json",
    "metadata/validation_summary.json",
    "validators/amp_validate_plan_packet.py",
    "validators/amp_validate_3mf_plan_bundle.py",
    "validators/amp_validate_firmware_adapter_outputs.py",
    "validators/amp_validate_hardware_preflight.py",
]

FORBIDDEN_SCRIPT_SUFFIXES = {".bat", ".cmd", ".ps1", ".sh"}

LIVE_COMMAND_RE = re.compile(
    r"^\s*(?:T[0-9]+\b|G0\b|G1\b|M104\b|M109\b|M140\b|M190\b|"
    r"SET_GCODE_OFFSET\b|SAVE_GCODE_STATE\b|RESTORE_GCODE_STATE\b)",
    re.IGNORECASE,
)
EXTRUSION_RE = re.compile(r"^\s*G1\b.*\bE[-+0-9.]+", re.IGNORECASE)
PHYSICAL_CLAIM_RE = re.compile(
    r"(?:validates?|validated|proves?|confirmed)\s+physical\s+mixed[- ]nozzle",
    re.IGNORECASE,
)
TOUCHSCREEN_CLAIM_RE = re.compile(
    r"(?:touchscreen[- ]compatible|touchscreen_safe\s*[:=]\s*true)",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_checked: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_bundle(bundle: Path, root: Path) -> None:
    if not bundle.exists():
        raise FileNotFoundError(f"missing bundle: {bundle}")
    with zipfile.ZipFile(bundle, "r") as archive:
        for info in archive.infolist():
            target = (root / info.filename).resolve()
            if not target.is_relative_to(root.resolve()):
                raise ValueError(f"unsafe archive path: {info.filename}")
        archive.extractall(root)


def is_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#") or stripped.startswith(";")


def uncommented_command_hits(path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        if is_comment_or_blank(line):
            continue
        if LIVE_COMMAND_RE.search(line) or EXTRUSION_RE.search(line):
            hits.append((line_number, line))
    return hits


def validate_required_files(root: Path, result: ValidationResult) -> None:
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            result.error(f"missing required file: {rel}")


def validate_readme(root: Path, result: ValidationResult) -> None:
    text = read_text(root / "README_NOT_INSTALLABLE.md").upper()
    for phrase in [
        "NOT READY TO " + "PRINT",
        "DO NOT INSTALL ON A PRINTER",
        "DOES NOT IMPLEMENT MIXED-NOZZLE SLICING",
        "DOES NOT BYPASS SNAPMAKER TOUCHSCREEN VALIDATION",
        "HARDWARE PREFLIGHT STATUS: NOT_READY",
        "FOR REVIEW",
    ]:
        if phrase not in text:
            result.error(f"README_NOT_INSTALLABLE.md missing phrase: {phrase}")


def validate_manifest(root: Path, result: ValidationResult) -> None:
    manifest = read_json(root / "metadata/bundle_manifest.json")
    if manifest.get("hardware_preflight_status") != "not_ready":
        result.error("bundle_manifest hardware_preflight_status must be not_ready")
    safety = manifest.get("safety", {})
    if safety.get("do_not_install_on_printer") is not True:
        result.error("bundle_manifest must record do_not_install_on_printer=true")
    if safety.get("not_ready_to_print") is not True:
        result.error("bundle_manifest must record not_ready_to_print=true")
    if safety.get("touchscreen_mixed_nozzle_blocked") is not True:
        result.error("bundle_manifest must record touchscreen_mixed_nozzle_blocked=true")


def validate_preflight(root: Path, result: ValidationResult) -> None:
    text = read_text(root / "safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Result.md").lower()
    if "status=not_ready" not in text and "not_ready" not in text:
        result.error("preflight result must say not_ready")
    summary = read_json(root / "metadata/validation_summary.json")
    if summary.get("hardware_preflight_status") != "not_ready":
        result.error("validation_summary hardware_preflight_status must be not_ready")


def validate_hashes(root: Path, result: ValidationResult) -> None:
    hashes = read_json(root / "metadata/file_hashes.json")
    if not isinstance(hashes, dict):
        result.error("file_hashes.json must be an object")
        return
    for rel, expected in sorted(hashes.items()):
        path = root / rel
        if not path.exists():
            result.error(f"hash references missing file: {rel}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            result.error(f"hash mismatch for {rel}")


def validate_no_install_scripts(root: Path, result: ValidationResult) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        result.files_checked += 1
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in FORBIDDEN_SCRIPT_SUFFIXES:
            result.error(f"bundle contains executable install/script-like file: {rel}")


def validate_no_live_commands(root: Path, result: ValidationResult) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() not in {".txt", ".md", ".template", ".cfg"}:
            continue
        for line_number, line in uncommented_command_hits(path):
            result.error(f"{rel}:{line_number} contains uncommented live command: {line}")


def validate_no_unsafe_claims(root: Path, result: ValidationResult) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md", ".json", ".template"}:
            continue
        rel = path.relative_to(root).as_posix()
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            lowered = line.lower()
            is_safety_non_claim = (
                "does not" in lowered
                or "do not" in lowered
                or "no " in lowered
                or "blocked" in lowered
                or "false" in lowered
                or "non-claim" in lowered
            )
            if is_safety_non_claim:
                continue
            if PHYSICAL_CLAIM_RE.search(line):
                result.error(f"{rel}:{line_number} appears to claim physical mixed-nozzle validation")
            if TOUCHSCREEN_CLAIM_RE.search(line):
                result.error(f"{rel}:{line_number} appears to claim touchscreen compatibility")


def validate(bundle: Path) -> ValidationResult:
    result = ValidationResult()
    with tempfile.TemporaryDirectory(prefix="amp_u1_fluidd_bundle_validate_") as tmp:
        root = Path(tmp)
        extract_bundle(bundle, root)
        validate_required_files(root, result)
        if result.errors:
            return result
        validate_readme(root, result)
        validate_manifest(root, result)
        validate_preflight(root, result)
        validate_hashes(root, result)
        validate_no_install_scripts(root, result)
        validate_no_live_commands(root, result)
        validate_no_unsafe_claims(root, result)
        result.warn("hardware preflight remains not_ready")
        result.warn("bundle is research-only and non-installable")
    return result


def report_payload(bundle: Path, result: ValidationResult) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "bundle": str(bundle),
        "passed": result.passed,
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "files_checked": result.files_checked,
        "errors": result.errors,
        "warnings": result.warnings,
    }


def markdown_report(bundle: Path, result: ValidationResult) -> list[str]:
    lines = [
        "# AMP U1 Fluidd Execution Bundle Validation Report",
        "",
        f"- Bundle: `{bundle}`",
        f"- Passed: `{str(result.passed).lower()}`",
        f"- Errors: `{len(result.errors)}`",
        f"- Warnings: `{len(result.warnings)}`",
        f"- Files checked: `{result.files_checked}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend([f"- {error}" for error in result.errors] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {warning}" for warning in result.warnings] or ["- None"])
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not implement mixed-nozzle slicing.",
            "- This does not flash or modify firmware.",
            "- This does not recommend installing custom firmware.",
            "- This does not generate production T0/T1/T2/T3 commands.",
            "- This does not generate a printable mixed-nozzle file.",
            "- This does not validate physical mixed-nozzle behavior.",
            "- This does not bypass Snapmaker touchscreen nozzle validation.",
        ]
    )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, help="Bundle ZIP to validate")
    parser.add_argument("--out", required=True, help="JSON validation report path")
    parser.add_argument("--markdown", required=True, help="Markdown validation report path")
    args = parser.parse_args()

    bundle = Path(args.bundle)
    result = validate(bundle)
    write_json(Path(args.out), report_payload(bundle, result))
    write_text(Path(args.markdown), markdown_report(bundle, result))
    print(f"passed={str(result.passed).lower()} errors={len(result.errors)} warnings={len(result.warnings)}")
    print(f"wrote {args.out}")
    print(f"wrote {args.markdown}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
