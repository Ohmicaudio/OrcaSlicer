#!/usr/bin/env python3
"""Pack an AMP 3MF-adjacent sidecar plan bundle.

The bundle is a portable authority package for offline AMP planning data. It is
not a native slicer 3MF writer and it does not generate executable G-code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AMP_PACKET_FILES = [
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

REGION_STL_FILES = [
    "micro_detail_zone.stl",
    "normal_visible_detail_zone.stl",
    "structural_shell_zone.stl",
    "bulk_zone.stl",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(args: list[str], fallback: str) -> str:
    try:
        result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    except Exception:
        return fallback
    value = result.stdout.strip()
    return value or fallback


def copy_required(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"missing required bundle input: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def region_names(packet_dir: Path) -> list[str]:
    regions = read_json(packet_dir / "regions.json").get("regions", [])
    names = [str(item.get("region_name")) for item in regions if isinstance(item, dict) and item.get("region_name")]
    if not names:
        raise ValueError("regions.json did not contain any region_name values")
    return sorted(names)


def adapter_target(manifest_path: Path) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    adapters = []
    wanted = {
        "snapmaker_touchscreen_blocked",
        "snapmaker_fluidd_klipper_experimental",
        "paxx12_u1_extended_firmware",
        "generic_klipper_macro",
        "klipper_ktcc_reference",
        "reprap_firmware_reference",
    }
    for adapter in manifest.get("adapters", []):
        if isinstance(adapter, dict) and adapter.get("adapter_id") in wanted:
            adapters.append(
                {
                    "adapter_id": adapter.get("adapter_id"),
                    "adapter_name": adapter.get("adapter_name"),
                    "target_controller": adapter.get("target_controller"),
                    "execution_status": adapter.get("execution_status", ""),
                    "command_style": adapter.get("command_style"),
                    "touchscreen_safe": adapter.get("touchscreen_safe"),
                    "fluidd_only": adapter.get("fluidd_only"),
                    "requires_hardware_validation": adapter.get("requires_hardware_validation"),
                    "source_url": adapter.get("source_url", ""),
                    "docs_url": adapter.get("docs_url", ""),
                    "safety_warnings": adapter.get("safety_warnings", []),
                }
            )
    return {
        "schema_version": "0.1",
        "source_of_truth": "amp_plan_packet",
        "executable_commands": False,
        "adapters": sorted(adapters, key=lambda item: str(item["adapter_id"])),
    }


def preflight_status(checklist_path: Path) -> dict[str, Any]:
    checklist = read_json(checklist_path)
    checks = checklist.get("checks", [])
    required = [item for item in checks if isinstance(item, dict) and item.get("required") is True]
    pending = [item for item in required if item.get("status_default", "pending") == "pending"]
    return {
        "schema_version": "0.1",
        "status": "not_ready",
        "ready": False,
        "required_count": len(required),
        "pending_required_count": len(pending),
        "touchscreen_mixed_nozzle_blocked": True,
        "fluidd_experimental_future_possible": True,
        "hardware_evidence_supplied": False,
    }


def manifest_payload(packet_dir: Path, region_dir: Path, adapter_manifest: Path, checklist: Path) -> dict[str, Any]:
    return {
        "bundle_version": "0.1",
        "created_by": "tools/amp_pack_3mf_plan_bundle.py",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_branch": git_value(["branch", "--show-current"], "unknown"),
        "source_commit": git_value(["rev-parse", "HEAD"], "unknown"),
        "target_platform": "FDM/FFF sidecar authority bundle",
        "target_machine": "Snapmaker U1 planning target",
        "source_paths": {
            "packet": str(packet_dir).replace("\\", "/"),
            "regions": str(region_dir).replace("\\", "/"),
            "adapter_manifest": str(adapter_manifest).replace("\\", "/"),
            "hardware_preflight_checklist": str(checklist).replace("\\", "/"),
        },
        "tool_ladder": ["0.2", "0.4", "0.6", "0.8"],
        "regions": region_names(packet_dir),
        "representation_status": {
            "sidecar_authority": True,
            "not_native_slicer_mixed_profile": True,
        },
        "safety_status": {
            "touchscreen_mixed_nozzle_blocked": True,
            "fluidd_experimental_future_possible": True,
            "hardware_preflight_status": "not_ready",
        },
        "non_claims": [
            "no mixed-nozzle slicing implementation",
            "no production T-code emission",
            "no physical validation",
            "no touchscreen bypass",
            "no custom firmware installation recommendation",
        ],
    }


def bundle_readme() -> str:
    return """# AMP 3MF Sidecar Plan Bundle

This archive is a 3MF-adjacent AMP sidecar authority bundle.

It packages offline AMP planning data, separated region bodies, adapter target
metadata, and preflight status so future GUI, CLI, or firmware-adapter tools can
review the same plan.

This is not a native slicer mixed-profile 3MF file. It does not implement
mixed-nozzle slicing, emit production T-code, validate physical mixed-nozzle
behavior, bypass Snapmaker touchscreen validation, or recommend installing
custom firmware.
"""


def collect_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel == "metadata/file_hashes.json":
            continue
        hashes[rel] = sha256_file(path)
    return hashes


def pack(packet_dir: Path, region_dir: Path, out_path: Path, adapter_manifest: Path, checklist: Path) -> dict[str, Any]:
    staging = out_path.parent / "_amp_3mf_plan_bundle_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    for name in AMP_PACKET_FILES:
        copy_required(packet_dir / name, staging / "amp" / name)
    for name in REGION_STL_FILES:
        copy_required(region_dir / name, staging / "models" / name)

    adapter_payload = adapter_target(adapter_manifest)
    write_json(staging / "amp" / "adapter_target.json", adapter_payload)
    write_json(staging / "amp" / "preflight_status.json", preflight_status(checklist))
    write_json(staging / "metadata" / "bundle_manifest.json", manifest_payload(packet_dir, region_dir, adapter_manifest, checklist))
    write_text(staging / "metadata" / "README.md", bundle_readme())
    write_json(staging / "metadata" / "file_hashes.json", collect_hashes(staging))
    write_json(out_path.parent / "adapter_target.json", adapter_payload)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(staging).as_posix())

    shutil.rmtree(staging)
    return {"bundle": str(out_path), "file_count": len(zipfile.ZipFile(out_path).namelist())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="AMP plan packet directory")
    parser.add_argument("--regions", required=True, help="Directory containing region STL bodies")
    parser.add_argument("--out", required=True, help="Output .amp3mf.zip path")
    parser.add_argument("--adapter-manifest", default="docs/benchmarks/AMP_Firmware_Adapter_Manifests.json")
    parser.add_argument("--preflight-checklist", default="docs/safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Checklist.json")
    args = parser.parse_args()

    result = pack(
        Path(args.packet),
        Path(args.regions),
        Path(args.out),
        Path(args.adapter_manifest),
        Path(args.preflight_checklist),
    )
    print(f"wrote {result['bundle']}")
    print(f"file_count={result['file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
