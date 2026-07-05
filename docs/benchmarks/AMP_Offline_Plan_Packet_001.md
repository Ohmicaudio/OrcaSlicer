# AMP Offline Plan Packet 001

## Purpose

This report documents the first unified offline AMP plan packet for the multi-tool resolution fixture.

The packet combines:

```text
continuous resolution field
-> tool-class assignment
-> cost gates
-> selected U1 process profiles
-> toolchange schedule
-> per-region G-code status
-> risk/fallback report
-> debug artifact JSON
```

This is offline/advisory tooling only. It does not modify slicer behavior, emit production T-code, or generate a single mixed-nozzle print job.

## Packet Contents

Generated packet directories:

```text
outputs/amp_plan_packet_001/
outputs/amp_plan_packet_001_detail_first/
```

Generated files:

| File | Purpose |
| --- | --- |
| `plan.json` | Packet metadata, source metadata, target platform, U1 start-path warnings, and non-claims. |
| `regions.json` | Source region metadata plus feature, line-type, visibility, and risk fields. |
| `resolution_field.json` | Continuous desired XY/Z values and quantized U1 tool/profile outputs. |
| `tool_assignments.json` | Cost-gated tool recommendations, fallback tools, confidence, and reasons. |
| `process_queue.json` | Concrete U1 process profile selection and fallback process profile. |
| `toolchange_schedule.json` | Toolchange-aware step order and estimated transition cost. |
| `per_region_gcode_status.json` | Per-region G-code presence, selected profile, file size, and metrics if available. |
| `risk_report.md` | Human-readable risk and fallback summary. |
| `debug_artifact.json` | Simplified offline AMP debug artifact with entries, observation summary, and warnings. |

The generated packet outputs are intentionally not committed.

## Input Fixture Regions

Input metadata:

```text
docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json
```

| Region | Line type | Visibility | Planning intent |
| --- | --- | --- | --- |
| `micro_detail_zone` | external perimeter | visible | fine XY/Z detail candidate |
| `normal_visible_detail_zone` | top surface | visible | normal cosmetic/detail candidate |
| `structural_shell_zone` | internal perimeter | internal | structural shell candidate |
| `bulk_zone` | sparse infill | hidden | bulk/infill candidate |

## Continuous Resolution Summary

| Region | Desired XY | Desired Z | Quantized tool | Layer | Width | Local-Z |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `micro_detail_zone` | 0.210 | 0.050 | 0.2 | 0.06 | 0.22 | true |
| `normal_visible_detail_zone` | 0.420 | 0.160 | 0.4 | 0.16 | 0.42 | false |
| `structural_shell_zone` | 0.620 | 0.240 | 0.6 | 0.24 | 0.62 | false |
| `bulk_zone` | 0.820 | 0.400 | 0.8 | 0.40 | 0.82 | false |

The packet preserves quantization error and risk flags in `resolution_field.json`.

## Tool Assignment Summary

| Region | Tool | Fallback | Confidence | Cost gate |
| --- | ---: | ---: | ---: | --- |
| `micro_detail_zone` | 0.2 | 0.4 | 0.70 | passed |
| `normal_visible_detail_zone` | 0.4 | 0.2 | 0.70 | passed |
| `structural_shell_zone` | 0.6 | 0.4 | 0.70 | passed |
| `bulk_zone` | 0.8 | 0.6 | 0.70 | passed |

The packet keeps tool assignment separate from scheduling. A region can request a tool for quality or bulk reasons without forcing that tool to be executed first.

## Process-Profile Queue Summary

| Region | Selected profile | Layer | Width class | Fallback profile |
| --- | --- | ---: | --- | --- |
| `micro_detail_zone` | `resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | 0.06 | 0.22 | `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json` |
| `normal_visible_detail_zone` | `resources/profiles/Snapmaker/process/0.16 Optimal @Snapmaker U1 (0.4 nozzle).json` | 0.16 | 0.42-0.45 | `resources/profiles/Snapmaker/process/0.08 Standard @Snapmaker U1 (0.2 nozzle).json` |
| `structural_shell_zone` | `resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | 0.24 | 0.62 | `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json` |
| `bulk_zone` | `resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | 0.40 | 0.82 | `resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json` |

Validation confirmed that all four selected process profiles exist locally.

## Toolchange Schedule Summary

Two packet modes were generated.

| Packet | Schedule mode | Toolchanges | Tool sequence |
| --- | --- | ---: | --- |
| `outputs/amp_plan_packet_001/` | `minimize_toolchanges` | 3 | `0.4 -> 0.2 -> 0.6 -> 0.8` |
| `outputs/amp_plan_packet_001_detail_first/` | `detail_first` | 4 | `0.2 -> 0.4 -> 0.6 -> 0.8` |

`minimize_toolchanges` starts with the current/default 0.4 region and avoids one immediate transition. `detail_first` schedules the 0.2 micro-detail region first for quality-driven review.

## Per-Region G-Code Status

| Region | Assigned G-code | Status |
| --- | --- | --- |
| `micro_detail_zone` | `outputs/amp_multitool_resolution_fixture/region_gcode/micro_detail_zone_0p2.gcode` | present |
| `normal_visible_detail_zone` | `outputs/amp_multitool_resolution_fixture/region_gcode/normal_visible_detail_zone_0p4.gcode` | present |
| `structural_shell_zone` | `outputs/amp_multitool_resolution_fixture/region_gcode/structural_shell_zone_0p6.gcode` | present |
| `bulk_zone` | `outputs/amp_multitool_resolution_fixture/region_gcode/bulk_zone_0p8.gcode` | present |

Missing G-code paths are marked explicitly instead of failing silently. In this run, no region G-code files were missing.

## Debug Artifact JSON Status

`debug_artifact.json` uses:

```text
schema_version: 0.1
generation_mode: offline_advisory
```

It includes:

- one entry per scheduled region
- toolchange-requested status
- confidence
- plan reason
- recommended tool class
- fallback tool class
- selected U1 process profile
- selected layer height
- selected line-width class
- cost-gate result and reason
- fallback reason
- risk flags
- local-Z advisory status
- touchscreen mixed-nozzle block status
- warnings/risk flags
- observation summary entries

It does not include geometry polygons, coordinates, G-code snippets, Arachne state, Flow mutation data, or physical nozzle commands.

After the packet-compatibility update, `debug_artifact.json` is fully populated for the C++ packet-compatible field set. The debug artifact contract check passes for both generated packet modes with:

```text
errors: 0
warnings: 0
```

## Validation Checks

The generator validates:

- all regions have tool assignments
- all regions have selected process profiles
- all selected process profiles exist
- all assigned tools have fallback
- `touchscreen_mixed_nozzle_blocked` is true
- no region claims physical validation
- local-Z flags are advisory only
- missing G-code is marked instead of silently ignored

Both generated packet modes passed these checks.

## What This Proves

- AMP can now generate a complete offline advisory plan packet.
- The packet connects continuous resolution, tool assignment, profile selection, scheduling, and debug output.
- The packet is suitable as a future slicer-side sidecar/debug artifact target.
- Toolchange scheduling can be compared without changing region assignment.
- Per-region G-code status can be represented alongside planning decisions.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate production `T0`, `T1`, `T2`, or `T3` commands.

This does not generate a single mixed-nozzle G-code print.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future/hardware-dependent.

This does not prove print strength, surface quality, dimensional accuracy, or bonding.

## Next Implementation Step

The next safe implementation step is to make the packet schema stricter and testable:

```text
offline packet schema
-> deterministic packet validation tests
-> C++ sidecar/debug artifact compatibility review
-> read-only slicer-side import/export experiment later
```

That keeps the project on the sidecar/debug path before any production slicer integration or T-code emission.
