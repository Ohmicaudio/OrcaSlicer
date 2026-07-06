# AMP 3MF Sidecar Plan Bundle 001

## Purpose

This report documents the first AMP 3MF-adjacent sidecar plan bundle.

The goal is to create a portable representation artifact that carries AMP's offline multi-tool plan without claiming that Snapmaker Orca already supports native mixed-profile or mixed-nozzle execution.

## Why This Bundle Exists

AMP currently has a representation gap:

- CLI assemble-list can collapse multi-profile intent.
- 3MF can preserve object identity, metadata, and tool/material assignment better than assemble-list.
- Native per-object process/nozzle execution is still unproven.
- AMP needs a sidecar authority package until slicer-native representation can carry full process/nozzle intent.

The bundle is that authority package.

## Relationship To 3MF Representation Diagnostic

Related diagnostic:

```text
docs/benchmarks/AMP_3MF_MultiProfile_Representation_Diagnostic_001.md
```

That diagnostic found that 3MF is promising for object identity and metadata, but it did not prove native per-object process/nozzle execution.

This bundle responds by keeping the authoritative AMP plan in sidecar JSON while carrying separated region bodies alongside it.

## Bundle Contents

Generated ignored bundle:

```text
outputs/amp_3mf_plan_bundle/amp_multitool_resolution_fixture.amp3mf.zip
```

Bundle file count:

```text
18
```

Top-level layout:

```text
amp/
metadata/
models/
```

AMP sidecar contents:

```text
amp/adapter_target.json
amp/debug_artifact.json
amp/per_region_gcode_status.json
amp/plan.json
amp/preflight_status.json
amp/process_queue.json
amp/regions.json
amp/resolution_field.json
amp/risk_report.md
amp/tool_assignments.json
amp/toolchange_schedule.json
```

Model contents:

```text
models/micro_detail_zone.stl
models/normal_visible_detail_zone.stl
models/structural_shell_zone.stl
models/bulk_zone.stl
```

Metadata contents:

```text
metadata/bundle_manifest.json
metadata/file_hashes.json
metadata/README.md
```

## Manifest Fields

The bundle manifest records:

- `bundle_version`
- `created_by`
- `source_branch`
- `source_commit`
- `target_platform`
- `target_machine`
- `tool_ladder`
- `regions`
- `representation_status`
- `safety_status`
- `non_claims`

Key status values:

```json
{
  "representation_status": {
    "not_native_slicer_mixed_profile": true,
    "sidecar_authority": true
  },
  "safety_status": {
    "fluidd_experimental_future_possible": true,
    "hardware_preflight_status": "not_ready",
    "touchscreen_mixed_nozzle_blocked": true
  }
}
```

## Region Body Mapping

The validator confirms every AMP region has a matching STL body:

| Region | STL body |
| --- | --- |
| `micro_detail_zone` | `models/micro_detail_zone.stl` |
| `normal_visible_detail_zone` | `models/normal_visible_detail_zone.stl` |
| `structural_shell_zone` | `models/structural_shell_zone.stl` |
| `bulk_zone` | `models/bulk_zone.stl` |

## Tool/Profile Queue Mapping

The bundle includes:

- `amp/tool_assignments.json`
- `amp/process_queue.json`
- `amp/toolchange_schedule.json`
- `amp/per_region_gcode_status.json`

The validator checks that every region has:

- a tool assignment
- a process queue entry
- a debug artifact entry
- a matching STL body

## Debug Artifact Mapping

The bundle includes:

```text
amp/debug_artifact.json
```

This preserves region names, recommended tool classes, selected process profiles, confidence values, risk flags, fallback tool classes, and blocked touchscreen status.

## Adapter Target Metadata

Generated sidecar metadata:

```text
outputs/amp_3mf_plan_bundle/adapter_target.json
amp/adapter_target.json
```

It summarizes:

- `snapmaker_touchscreen_blocked`
- `snapmaker_fluidd_klipper_experimental`
- `paxx12_u1_extended_firmware`
- `generic_klipper_macro`
- `klipper_ktcc_reference`
- `reprap_firmware_reference`

The metadata contains no executable commands.

## Validation Result

Command:

```powershell
python tools\amp_validate_3mf_plan_bundle.py --bundle outputs\amp_3mf_plan_bundle\amp_multitool_resolution_fixture.amp3mf.zip --out outputs\amp_3mf_plan_bundle\validation_report.json --markdown outputs\amp_3mf_plan_bundle\validation_report.md
```

Result:

```text
passed=true
errors=0
warnings=2
region_count=4
```

Warnings:

```text
bundle is a sidecar authority, not native slicer mixed-profile support
hardware preflight remains not_ready
```

Both warnings are intentional.

## What This Proves

- AMP can package a complete offline multi-tool plan into a portable sidecar bundle.
- The bundle preserves region identity, tool assignment, process profile selection, schedule, risk flags, and debug artifact data.
- The bundle includes all four separated region bodies.
- The bundle includes adapter target metadata.
- The bundle includes preflight status.
- Bundle hashes can be validated.

## What This Does Not Prove

- This does not implement mixed-nozzle slicing.
- This does not generate production `T0`, `T1`, `T2`, or `T3` commands.
- This does not create a verified mixed-nozzle print.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
- This does not recommend installing custom firmware.

## Next Bridge

The next representation bridge is:

```text
AMP sidecar bundle
-> GUI/manual 3MF project review
-> 3MF save/reopen round trip
-> object/tool-slot metadata inspection
-> exported G-code diagnostic only
```

Until native 3MF/project representation proves it can carry full process/nozzle intent, the sidecar bundle remains the current authority path.

Hardware preflight remains `not_ready`.
