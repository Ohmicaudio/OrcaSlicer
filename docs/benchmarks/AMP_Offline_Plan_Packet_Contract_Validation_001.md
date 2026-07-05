# AMP Offline Plan Packet Contract Validation 001

## Purpose

This report documents the first mechanical validation pass for the AMP offline plan packet.

The goal is to make the packet a stable future sidecar/debug-artifact target:

```text
offline planner output
-> packet contract validation
-> comments-only pseudo toolchange export
-> future C++ debug artifact compatibility test
```

This is offline/advisory tooling only.

## Packet Files Validated

The validator checks that each packet directory contains:

```text
plan.json
regions.json
resolution_field.json
tool_assignments.json
process_queue.json
toolchange_schedule.json
per_region_gcode_status.json
risk_report.md
debug_artifact.json
```

Validated packet directories:

```text
outputs/amp_plan_packet_001/
outputs/amp_plan_packet_001_detail_first/
```

## Contract Rules

Plan-level rules:

- `packet_version` exists.
- `created_by` exists.
- `target_platform` exists.
- `touchscreen_mixed_nozzle_blocked` is true.
- `fluidd_experimental_future_possible` exists.
- `non_claims` exists.

Per-region consistency rules:

- every region has a resolution-field entry
- every region has a tool assignment
- every region has a process-queue entry
- every region has a schedule entry or explicit unscheduled reason
- every region has G-code status marked `present`, `missing`, or `unknown`
- every assigned tool has a fallback
- every process selection has a fallback process profile
- risk flags are represented

Safety rules:

- no packet may claim physical mixed-nozzle validation
- no packet may claim production mixed-nozzle G-code
- local-Z flags remain advisory only
- 0.2 with clog-risk material fails validation
- 0.8 on top/cosmetic/painted/support-interface/bridge line types fails validation

## Validation Results: Minimize Toolchanges Packet

Command:

```powershell
python tools\amp_validate_plan_packet.py --packet outputs\amp_plan_packet_001 --out outputs\amp_plan_packet_001\validation_report.json --markdown outputs\amp_plan_packet_001\validation_report.md
```

Result:

```text
passed: True
errors: 0
warnings: 0
regions: 4
```

Schedule summary:

| Mode | Toolchanges | Sequence |
| --- | ---: | --- |
| `minimize_toolchanges` | 3 | `0.4 -> 0.2 -> 0.6 -> 0.8` |

## Validation Results: Detail First Packet

Command:

```powershell
python tools\amp_validate_plan_packet.py --packet outputs\amp_plan_packet_001_detail_first --out outputs\amp_plan_packet_001_detail_first\validation_report.json --markdown outputs\amp_plan_packet_001_detail_first\validation_report.md
```

Result:

```text
passed: True
errors: 0
warnings: 0
regions: 4
```

Schedule summary:

| Mode | Toolchanges | Sequence |
| --- | ---: | --- |
| `detail_first` | 4 | `0.2 -> 0.4 -> 0.6 -> 0.8` |

## Pseudo Toolchange Export Status

Command:

```powershell
python tools\amp_export_pseudo_toolchange_schedule.py --packet outputs\amp_plan_packet_001 --out outputs\amp_plan_packet_001\pseudo_toolchange_schedule.gcode.txt
```

Generated ignored output:

```text
outputs/amp_plan_packet_001/pseudo_toolchange_schedule.gcode.txt
```

The pseudo export is comments-only and non-printable. It begins with:

```text
; PSEUDO ONLY - NOT PRINTABLE
; AMP offline advisory schedule
; This does not implement mixed-nozzle slicing
; Touchscreen-compatible mixed-nozzle execution remains blocked
```

Tool selections are represented only as comments:

```text
; WOULD_SELECT_TOOL T0 for 0.2
; WOULD_SELECT_TOOL T1 for 0.4
; WOULD_SELECT_TOOL T2 for 0.6
; WOULD_SELECT_TOOL T3 for 0.8
```

The exporter does not emit uncommented `T0`, `T1`, `T2`, or `T3` commands.

## Errors And Warnings

Both current packet modes validated with:

```text
errors: 0
warnings: 0
```

The validator is expected to fail or warn future packets that request unsafe combinations, including:

- 0.2 with clog-risk material
- 0.8 for top/cosmetic/painted/support-interface/bridge line types
- missing process profiles
- missing region schedule entries
- missing fallback tools or fallback process profiles
- unsafe claims about production mixed-nozzle output or physical validation

## What This Proves

- AMP now has a complete offline plan packet and a validator for that packet.
- The validator checks assignment/profile/schedule/G-code-status consistency.
- The pseudo toolchange export is comments-only and non-printable.
- The packet is suitable as a future sidecar/debug-artifact target.
- Validation can distinguish packet-contract issues from slicer behavior.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate production `T0`, `T1`, `T2`, or `T3` commands.

This does not generate a single mixed-nozzle G-code print.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future/hardware-dependent.

This does not prove print strength, surface quality, dimensional accuracy, or bonding.

## Next Integration Target

The next safe target is:

```text
offline plan packet
-> C++ AMP debug artifact compatibility test
```

That should remain read-only and should not wire AMP into production slicing, G-code generation, Snapmaker validation, or toolchange emission.
