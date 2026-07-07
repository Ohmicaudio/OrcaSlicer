#!/usr/bin/env python3
"""Pack a non-executable AMP U1 Fluidd execution review bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


BUNDLE_NAME = "amp_u1_fluidd_execution_bundle_001"

PLAN_FILES = [
    "plan.json",
    "regions.json",
    "resolution_field.json",
    "tool_assignments.json",
    "process_queue.json",
    "toolchange_schedule.json",
    "per_region_gcode_status.json",
    "debug_artifact.json",
    "risk_report.md",
]

SANDBOX_FILES = [
    "amp_tools.cfg.template",
    "amp_macros.cfg.template",
    "amp_dry_run_schedule.gcode.txt",
    "amp_preflight_checklist.md",
    "amp_safety_report.md",
    "amp_tool_map.json",
]

SAFETY_DOCS = [
    "docs/safety/AMP_Fluidd_Klipper_Hardware_Preflight_001.md",
    "docs/safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Checklist.json",
    "docs/safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Result.md",
]

VALIDATOR_TOOLS = [
    "tools/amp_validate_plan_packet.py",
    "tools/amp_validate_3mf_plan_bundle.py",
    "tools/amp_validate_firmware_adapter_outputs.py",
    "tools/amp_validate_hardware_preflight.py",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"missing required input: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree_files(src_root: Path, dst_root: Path) -> None:
    if not src_root.exists():
        raise FileNotFoundError(f"missing required input directory: {src_root}")
    for src in sorted(path for path in src_root.rglob("*") if path.is_file()):
        copy_file(src, dst_root / src.relative_to(src_root))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hashes_for(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel == "metadata/file_hashes.json":
            continue
        hashes[rel] = sha256_file(path)
    return hashes


def zip_directory(root: Path, out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(root).as_posix())


def not_installable_readme() -> str:
    lines = [
        "# AMP U1 Fluidd Execution Bundle 001",
        "",
        "NOT READY TO " + "PRINT.",
        "",
        "DO NOT INSTALL ON A PRINTER.",
        "",
        "DOES NOT IMPLEMENT MIXED-NOZZLE SLICING.",
        "",
        "DOES NOT BYPASS SNAPMAKER TOUCHSCREEN VALIDATION.",
        "",
        "HARDWARE PREFLIGHT STATUS: NOT_READY.",
        "",
        "This bundle is for review and future dry-run planning only. It packages offline",
        "AMP advisory artifacts, disabled Fluidd/Klipper sandbox templates, adapter",
        "metadata, and safety/preflight records into one portable archive.",
        "",
        "The bundle is intentionally non-installable and non-printable as-is.",
        "",
        "It does not flash firmware.",
        "It does not modify firmware.",
        "It does not create install scripts.",
        "It does not emit production tool selection commands.",
        "It does not validate physical mixed-nozzle behavior.",
    ]
    return "\n".join(lines) + "\n"


def validation_summary(packet: Path, sidecar_bundle: Path, sandbox: Path, adapter_pseudo: Path) -> dict[str, Any]:
    packet_report = packet / "validation_report.json"
    sidecar_report = sidecar_bundle.parent / "validation_report.json"
    adapter_report = Path("outputs/amp_firmware_adapter_validation/paxx12_adapter_validation_report.json")
    return {
        "schema_version": "0.1",
        "bundle_status": "review_only_not_installable_not_printable",
        "hardware_preflight_status": "not_ready",
        "packet_validation_report_present": packet_report.exists(),
        "sidecar_validation_report_present": sidecar_report.exists(),
        "adapter_validation_report_present": adapter_report.exists(),
        "packet_validation": read_json(packet_report) if packet_report.exists() else None,
        "sidecar_validation": read_json(sidecar_report) if sidecar_report.exists() else None,
        "adapter_validation": read_json(adapter_report) if adapter_report.exists() else None,
        "inputs": {
            "packet": str(packet).replace("\\", "/"),
            "sidecar_bundle": str(sidecar_bundle).replace("\\", "/"),
            "sandbox": str(sandbox).replace("\\", "/"),
            "adapter_pseudo": str(adapter_pseudo).replace("\\", "/"),
        },
        "non_claims": [
            "does not implement mixed-nozzle slicing",
            "does not flash or modify firmware",
            "does not recommend installing custom firmware",
            "does not generate production T0/T1/T2/T3 commands",
            "does not generate a printable mixed-nozzle file",
            "does not validate physical mixed-nozzle behavior",
            "does not bypass Snapmaker touchscreen nozzle validation",
        ],
    }


def bundle_manifest(packet: Path, sidecar_bundle: Path, sandbox: Path, adapter_pseudo: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "bundle_id": BUNDLE_NAME,
        "status": "review_only_not_installable_not_printable",
        "hardware_preflight_status": "not_ready",
        "source_of_truth": "offline AMP plan packet",
        "inputs": {
            "packet": str(packet).replace("\\", "/"),
            "sidecar_bundle": str(sidecar_bundle).replace("\\", "/"),
            "sandbox": str(sandbox).replace("\\", "/"),
            "adapter_pseudo": str(adapter_pseudo).replace("\\", "/"),
        },
        "contains": {
            "amp_plan": True,
            "amp_3mf_sidecar": True,
            "fluidd_klipper_sandbox": True,
            "adapter_pseudo": True,
            "safety_preflight": True,
            "validators": True,
        },
        "safety": {
            "not_ready_to_print": True,
            "do_not_install_on_printer": True,
            "touchscreen_mixed_nozzle_blocked": True,
            "requires_hardware_validation": True,
        },
        "non_claims": [
            "no mixed-nozzle slicing implementation",
            "no firmware flashing or modification",
            "no production T-code emission",
            "no physical validation",
            "no touchscreen bypass",
        ],
    }


def build_bundle(packet: Path, sidecar_bundle: Path, sandbox: Path, adapter_pseudo: Path, out_zip: Path) -> Path:
    staging = out_zip.parent / "_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    write_text(staging / "README_NOT_INSTALLABLE.md", not_installable_readme())

    for name in PLAN_FILES:
        copy_file(packet / name, staging / "amp_plan" / name)
    copy_file(sidecar_bundle, staging / "amp_3mf_sidecar" / sidecar_bundle.name)
    for name in SANDBOX_FILES:
        copy_file(sandbox / name, staging / "fluidd_klipper_sandbox" / name)
    copy_tree_files(adapter_pseudo, staging / "adapter_pseudo")
    for rel in SAFETY_DOCS:
        src = Path(rel)
        copy_file(src, staging / "safety" / src.name)
    for rel in VALIDATOR_TOOLS:
        src = Path(rel)
        copy_file(src, staging / "validators" / src.name)

    write_json(staging / "metadata/bundle_manifest.json", bundle_manifest(packet, sidecar_bundle, sandbox, adapter_pseudo))
    write_json(staging / "metadata/validation_summary.json", validation_summary(packet, sidecar_bundle, sandbox, adapter_pseudo))
    write_json(staging / "metadata/file_hashes.json", hashes_for(staging))

    zip_directory(staging, out_zip)
    return out_zip


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="AMP plan packet directory")
    parser.add_argument("--sidecar-bundle", required=True, help="AMP 3MF sidecar bundle ZIP")
    parser.add_argument("--sandbox", required=True, help="Fluidd/Klipper sandbox directory")
    parser.add_argument("--adapter-pseudo", required=True, help="Firmware adapter pseudo output directory")
    parser.add_argument("--out", required=True, help="Output bundle ZIP")
    args = parser.parse_args()

    out = build_bundle(
        packet=Path(args.packet),
        sidecar_bundle=Path(args.sidecar_bundle),
        sandbox=Path(args.sandbox),
        adapter_pseudo=Path(args.adapter_pseudo),
        out_zip=Path(args.out),
    )
    print(f"bundle={out}")
    print("status=not_installable_not_printable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
