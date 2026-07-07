# AMP U1 Fluidd Execution Bundle 001

## Purpose

This document records the first complete AMP U1 Fluidd execution bundle.

The bundle packages the current offline AMP planning artifacts into one
portable archive for review and future dry-run planning. It is intentionally
non-installable and non-printable.

Generated ignored output:

```text
outputs/amp_u1_fluidd_execution_bundle_001/amp_u1_fluidd_execution_bundle_001.zip
```

## Why This Bundle Exists

AMP now has several separate review artifacts:

- offline AMP plan packet
- 3MF-adjacent sidecar plan bundle
- debug artifact
- Fluidd/Klipper sandbox templates
- firmware adapter pseudo output
- paxx12 U1 Extended Firmware source audit
- hardware preflight checklist and result

The execution bundle ties those pieces together so the eventual hardware
question is concrete:

```text
What exact packet, metadata, sandbox templates, adapter notes, and preflight
gates would travel together when hardware validation becomes possible?
```

## Bundle Contents

Top-level bundle layout:

```text
README_NOT_INSTALLABLE.md
amp_plan/
amp_3mf_sidecar/
fluidd_klipper_sandbox/
adapter_pseudo/
safety/
validators/
metadata/
```

The bundle `README_NOT_INSTALLABLE.md` states:

- a print-readiness warning
- DO NOT INSTALL ON A PRINTER
- DOES NOT IMPLEMENT MIXED-NOZZLE SLICING
- DOES NOT BYPASS SNAPMAKER TOUCHSCREEN VALIDATION
- HARDWARE PREFLIGHT STATUS: NOT_READY
- FOR REVIEW / FUTURE DRY-RUN PLANNING ONLY

## AMP Plan Packet Included

The bundle includes these offline AMP plan packet files:

```text
amp_plan/plan.json
amp_plan/regions.json
amp_plan/resolution_field.json
amp_plan/tool_assignments.json
amp_plan/process_queue.json
amp_plan/toolchange_schedule.json
amp_plan/per_region_gcode_status.json
amp_plan/debug_artifact.json
amp_plan/risk_report.md
```

These files remain advisory. They do not make slicer output change.

## 3MF Sidecar Bundle Included

The bundle includes:

```text
amp_3mf_sidecar/amp_multitool_resolution_fixture.amp3mf.zip
```

This keeps the sidecar representation connected to the same execution review
packet. It remains a sidecar representation and does not become native slicer
mixed-profile behavior.

## Fluidd/Klipper Sandbox Included

The bundle includes disabled sandbox files:

```text
fluidd_klipper_sandbox/amp_tools.cfg.template
fluidd_klipper_sandbox/amp_macros.cfg.template
fluidd_klipper_sandbox/amp_dry_run_schedule.gcode.txt
fluidd_klipper_sandbox/amp_preflight_checklist.md
fluidd_klipper_sandbox/amp_safety_report.md
fluidd_klipper_sandbox/amp_tool_map.json
```

These files are templates and review artifacts only. They are not install
scripts, printer configuration, or printable G-code.

## paxx12 Adapter Status

The bundle includes adapter pseudo output for the current research targets,
including:

```text
adapter_pseudo/paxx12_u1_extended_firmware/
```

The paxx12 adapter remains:

```text
research_only_future_experimental
fluidd_only: true
touchscreen_safe: false
requires_hardware_validation: true
```

The paxx12 source audit identified plausible future paths under
`extended/klipper/`, but no file in this bundle is intended to be copied to a
printer.

## Preflight Status

The bundled preflight files are:

```text
safety/AMP_Fluidd_Klipper_Hardware_Preflight_001.md
safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Checklist.json
safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Result.md
```

Preflight status:

```text
status=not_ready
ready=false
pending_required=28
failed_required=0
invalid=0
```

This is the intended state. No hardware evidence has been supplied.

## Validators Included

The bundle includes copies of the read-only validators used to check the
individual packet and safety artifacts:

```text
validators/amp_validate_plan_packet.py
validators/amp_validate_3mf_plan_bundle.py
validators/amp_validate_firmware_adapter_outputs.py
validators/amp_validate_hardware_preflight.py
```

These are included for review/reproducibility. They are not firmware files,
printer macros, install scripts, or G-code.

## Validation Result

Commands:

```powershell
python tools/amp_pack_u1_fluidd_execution_bundle.py --packet outputs/amp_plan_packet_001 --sidecar-bundle outputs/amp_3mf_plan_bundle/amp_multitool_resolution_fixture.amp3mf.zip --sandbox outputs/amp_fluidd_klipper_sandbox --adapter-pseudo outputs/amp_firmware_adapter_pseudo --out outputs/amp_u1_fluidd_execution_bundle_001/amp_u1_fluidd_execution_bundle_001.zip

python tools/amp_validate_u1_fluidd_execution_bundle.py --bundle outputs/amp_u1_fluidd_execution_bundle_001/amp_u1_fluidd_execution_bundle_001.zip --out outputs/amp_u1_fluidd_execution_bundle_001/validation_report.json --markdown outputs/amp_u1_fluidd_execution_bundle_001/validation_report.md
```

Result:

```text
passed=true
errors=0
warnings=2
files_checked=51
```

Warnings:

```text
hardware preflight remains not_ready
bundle is research-only and non-installable
```

## What This Proves

- AMP can package its offline advisory plan, sidecar representation, and
  Fluidd/Klipper sandbox into one reviewable bundle.
- The bundle validates as non-installable and non-printable.
- The bundle contains hashes for deterministic file integrity checks.
- The paxx12/Fluidd path is represented as a future experimental adapter target.
- Hardware preflight remains `not_ready`.

## What This Does Not Prove

- This does not implement mixed-nozzle slicing.
- This does not flash or modify firmware.
- This does not recommend installing custom firmware.
- This does not generate production `T0` / `T1` / `T2` / `T3` commands.
- This does not generate a printable mixed-nozzle file.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.

## Next Safe Step

The next safe milestone is a public milestone summary for:

```text
AMP Milestone 002:
Offline planner + sidecar representation + Fluidd/Klipper execution bundle
```

No hardware dry-run should be attempted until the preflight checklist has real
U1 evidence and the status changes from `not_ready`.
