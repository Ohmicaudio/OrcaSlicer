#!/usr/bin/env python3
"""Validate an AMP 3MF-adjacent sidecar plan bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import amp_debug_artifact_contract_check
except ImportError:  # pragma: no cover - optional checker in older branches
    amp_debug_artifact_contract_check = None  # type: ignore[assignment]


REQUIRED_AMP_JSON = [
    "amp/plan.json",
    "amp/regions.json",
    "amp/resolution_field.json",
    "amp/tool_assignments.json",
    "amp/process_queue.json",
    "amp/toolchange_schedule.json",
    "amp/per_region_gcode_status.json",
    "amp/debug_artifact.json",
    "amp/adapter_target.json",
    "amp/preflight_status.json",
]

REQUIRED_FILES = [
    *REQUIRED_AMP_JSON,
    "amp/risk_report.md",
    "models/micro_detail_zone.stl",
    "models/normal_visible_detail_zone.stl",
    "models/structural_shell_zone.stl",
    "models/bulk_zone.stl",
    "metadata/bundle_manifest.json",
    "metadata/file_hashes.json",
    "metadata/README.md",
]

REGION_TO_STL = {
    "micro_detail_zone": "models/micro_detail_zone.stl",
    "normal_visible_detail_zone": "models/normal_visible_detail_zone.stl",
    "structural_shell_zone": "models/structural_shell_zone.stl",
    "bulk_zone": "models/bulk_zone.stl",
}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    region_count: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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
            target = root / info.filename
            if not target.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"unsafe archive path: {info.filename}")
        archive.extractall(root)


def region_names(regions_json: Path) -> list[str]:
    payload = read_json(regions_json)
    regions = payload.get("regions", [])
    return sorted(str(item.get("region_name")) for item in regions if isinstance(item, dict) and item.get("region_name"))


def names_from_entries(path: Path, key: str, array_name: str) -> set[str]:
    payload = read_json(path)
    entries = payload.get(array_name, [])
    return {str(item.get(key)) for item in entries if isinstance(item, dict) and item.get(key)}


def debug_region_names(path: Path) -> set[str]:
    payload = read_json(path)
    entries = payload.get("entries", [])
    return {str(item.get("region_name")) for item in entries if isinstance(item, dict) and item.get("region_name")}


def validate_required_files(root: Path, result: ValidationResult) -> None:
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            result.error(f"missing required file: {rel}")


def validate_hashes(root: Path, result: ValidationResult) -> None:
    path = root / "metadata/file_hashes.json"
    if not path.exists():
        return
    expected = read_json(path)
    if not isinstance(expected, dict):
        result.error("metadata/file_hashes.json must be an object")
        return
    for rel, digest in sorted(expected.items()):
        file_path = root / rel
        if not file_path.exists():
            result.error(f"hash entry references missing file: {rel}")
            continue
        actual = sha256_file(file_path)
        if actual != digest:
            result.error(f"hash mismatch for {rel}")


def validate_region_consistency(root: Path, result: ValidationResult) -> None:
    regions = region_names(root / "amp/regions.json")
    result.region_count = len(regions)
    assignment_regions = names_from_entries(root / "amp/tool_assignments.json", "region_name", "tool_assignments")
    queue_regions = names_from_entries(root / "amp/process_queue.json", "region_name", "process_queue")
    debug_regions = debug_region_names(root / "amp/debug_artifact.json")

    for region in regions:
        stl = REGION_TO_STL.get(region)
        if not stl or not (root / stl).exists():
            result.error(f"region has no matching STL body: {region}")
        if region not in assignment_regions:
            result.error(f"region has no tool assignment: {region}")
        if region not in queue_regions:
            result.error(f"region has no process queue entry: {region}")
        if region not in debug_regions:
            result.error(f"region has no debug artifact entry: {region}")


def validate_debug_artifact_contract(root: Path, result: ValidationResult) -> None:
    if amp_debug_artifact_contract_check is None:
        result.warn("debug artifact contract checker is not available")
        return
    contract = amp_debug_artifact_contract_check.check(root / "amp/debug_artifact.json")
    if not contract.get("passed"):
        for error in contract.get("errors", []):
            result.error(f"debug artifact contract failed: {error}")
    for warning in contract.get("warnings", []):
        result.warn(f"debug artifact contract warning: {warning}")


def validate_safety(root: Path, result: ValidationResult) -> None:
    manifest = read_json(root / "metadata/bundle_manifest.json")
    preflight = read_json(root / "amp/preflight_status.json")
    representation = manifest.get("representation_status", {})
    safety = manifest.get("safety_status", {})
    non_claims = " ".join(str(item).lower() for item in manifest.get("non_claims", []))

    if representation.get("sidecar_authority") is not True:
        result.error("bundle_manifest must mark sidecar_authority=true")
    if representation.get("not_native_slicer_mixed_profile") is not True:
        result.error("bundle must not claim native slicer mixed-profile support")
    if safety.get("touchscreen_mixed_nozzle_blocked") is not True:
        result.error("touchscreen_mixed_nozzle_blocked must be true")
    if safety.get("hardware_preflight_status") != "not_ready":
        result.error("hardware_preflight_status must remain not_ready unless evidence is supplied")
    if preflight.get("status") != "not_ready" or preflight.get("ready") is not False:
        result.error("preflight_status must be not_ready by default")

    for phrase in ["no mixed-nozzle slicing implementation", "no production t-code emission", "no physical validation", "no touchscreen bypass"]:
        if phrase not in non_claims:
            result.error(f"bundle_manifest missing non-claim: {phrase}")

    result.warn("bundle is a sidecar authority, not native slicer mixed-profile support")
    result.warn("hardware preflight remains not_ready")


def validate_no_executable_gcode(root: Path, result: ValidationResult) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.endswith(".gcode") or rel.endswith(".gcode.txt"):
            result.error(f"bundle contains executable-looking G-code artifact: {rel}")


def validate(bundle: Path) -> ValidationResult:
    result = ValidationResult()
    with tempfile.TemporaryDirectory(prefix="amp_3mf_bundle_validate_") as tmp:
        root = Path(tmp)
        extract_bundle(bundle, root)
        validate_required_files(root, result)
        if result.errors:
            return result
        validate_hashes(root, result)
        validate_region_consistency(root, result)
        validate_debug_artifact_contract(root, result)
        validate_safety(root, result)
        validate_no_executable_gcode(root, result)
    return result


def report_payload(bundle: Path, result: ValidationResult) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "bundle": str(bundle),
        "passed": result.passed,
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "region_count": result.region_count,
        "errors": result.errors,
        "warnings": result.warnings,
    }


def markdown_report(bundle: Path, result: ValidationResult) -> list[str]:
    lines = [
        "# AMP 3MF Sidecar Plan Bundle Validation Report",
        "",
        f"- Bundle: `{bundle}`",
        f"- Passed: `{str(result.passed).lower()}`",
        f"- Errors: `{len(result.errors)}`",
        f"- Warnings: `{len(result.warnings)}`",
        f"- Region count: `{result.region_count}`",
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
            "- This does not generate production tool-selection commands.",
            "- This does not generate a printable mixed-nozzle file.",
            "- This does not validate physical mixed-nozzle behavior.",
            "- This does not bypass Snapmaker touchscreen nozzle validation.",
        ]
    )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, help="AMP sidecar bundle zip")
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
