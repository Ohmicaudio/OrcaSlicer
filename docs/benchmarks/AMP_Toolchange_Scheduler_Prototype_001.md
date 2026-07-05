# AMP Toolchange Scheduler Prototype 001

## Purpose

This report documents the first offline AMP toolchange scheduling prototype.

The scheduler takes region metadata and AMP continuous-resolution assignments, then produces an advisory execution schedule:

```text
layer / region / tool / profile / estimated cost / reason / fallback
```

This is the bridge between region assignment and a future toolchange/T-code emission plan. It does not implement mixed-nozzle slicing.

## Input Region Plan

Input metadata:

```text
docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json
```

Fixture regions:

| Region | Role | Visibility | Detail | Intended planning pressure |
| --- | --- | --- | --- | --- |
| `micro_detail_zone` | external perimeter | visible | micro | preserve fine XY/Z detail |
| `normal_visible_detail_zone` | top surface | visible | high | preserve normal cosmetic detail |
| `structural_shell_zone` | internal perimeter | internal | low | allow structural/internal tool class |
| `bulk_zone` | sparse infill | hidden | none | allow bulk tool class |

## Tool/Profile Queue

The scheduler uses the continuous resolution field prototype to select the U1 process/profile class for each region:

| Region | Tool | Process profile | Layer height | Line width class |
| --- | ---: | --- | ---: | ---: |
| `micro_detail_zone` | 0.2 | `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | 0.06 | 0.22 |
| `normal_visible_detail_zone` | 0.4 | `0.16 Optimal @Snapmaker U1 (0.4 nozzle).json` | 0.16 | 0.42 |
| `structural_shell_zone` | 0.6 | `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | 0.24 | 0.62 |
| `bulk_zone` | 0.8 | `0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | 0.40 | 0.82 |

The default/current tool for this run is 0.4. The estimated toolchange cost is 60 seconds per transition.

## Scheduling Modes

The prototype supports four modes:

- `minimize_toolchanges`
- `detail_first`
- `bulk_first`
- `layer_ordered`

The scheduler preserves layer/Z order when region metadata provides layer or vertical-order fields. The current fixture metadata does not provide layer IDs, so the non-layer modes can reorder the four regions to show scheduling behavior.

## Schedule Tables

### Summary

| Mode | Toolchanges | Estimated toolchange cost | Tool sequence |
| --- | ---: | ---: | --- |
| `minimize_toolchanges` | 3 | 180.0s | `0.4 -> 0.2 -> 0.6 -> 0.8` |
| `detail_first` | 4 | 240.0s | `0.2 -> 0.4 -> 0.6 -> 0.8` |
| `bulk_first` | 4 | 240.0s | `0.8 -> 0.6 -> 0.4 -> 0.2` |
| `layer_ordered` | 4 | 240.0s | `0.2 -> 0.4 -> 0.6 -> 0.8` |

### Minimize Toolchanges

| Step | Region | Tool | Change | Layer | Width | Reason |
| ---: | --- | ---: | --- | ---: | ---: | --- |
| 1 | `normal_visible_detail_zone` | 0.4 | false | 0.16 | 0.42 | starts with the current/default 0.4 tool group to avoid an immediate toolchange |
| 2 | `micro_detail_zone` | 0.2 | true | 0.06 | 0.22 | micro visible detail still requests the 0.2 class |
| 3 | `structural_shell_zone` | 0.6 | true | 0.24 | 0.62 | internal structural shell requests 0.6 |
| 4 | `bulk_zone` | 0.8 | true | 0.40 | 0.82 | hidden bulk requests 0.8 |

### Detail First

| Step | Region | Tool | Change | Layer | Width | Reason |
| ---: | --- | ---: | --- | ---: | ---: | --- |
| 1 | `micro_detail_zone` | 0.2 | true | 0.06 | 0.22 | quality-driven micro detail first |
| 2 | `normal_visible_detail_zone` | 0.4 | true | 0.16 | 0.42 | normal visible detail follows |
| 3 | `structural_shell_zone` | 0.6 | true | 0.24 | 0.62 | structural/internal region follows detail regions |
| 4 | `bulk_zone` | 0.8 | true | 0.40 | 0.82 | hidden bulk last |

### Bulk First

| Step | Region | Tool | Change | Layer | Width | Reason |
| ---: | --- | ---: | --- | ---: | ---: | --- |
| 1 | `bulk_zone` | 0.8 | true | 0.40 | 0.82 | throughput-driven hidden bulk first |
| 2 | `structural_shell_zone` | 0.6 | true | 0.24 | 0.62 | internal shell follows |
| 3 | `normal_visible_detail_zone` | 0.4 | true | 0.16 | 0.42 | visible detail later |
| 4 | `micro_detail_zone` | 0.2 | true | 0.06 | 0.22 | micro detail last |

### Layer Ordered

| Step | Region | Tool | Change | Layer | Width | Reason |
| ---: | --- | ---: | --- | ---: | ---: | --- |
| 1 | `micro_detail_zone` | 0.2 | true | 0.06 | 0.22 | preserves input/layer-style order |
| 2 | `normal_visible_detail_zone` | 0.4 | true | 0.16 | 0.42 | preserves input/layer-style order |
| 3 | `structural_shell_zone` | 0.6 | true | 0.24 | 0.62 | preserves input/layer-style order |
| 4 | `bulk_zone` | 0.8 | true | 0.40 | 0.82 | preserves input/layer-style order |

## Toolchange Count Per Mode

With a 0.4 default tool:

- `minimize_toolchanges` produces 3 toolchanges.
- `detail_first` produces 4 toolchanges.
- `bulk_first` produces 4 toolchanges.
- `layer_ordered` produces 4 toolchanges.

This is the first place AMP starts separating assignment from execution. The region assignment can remain the same while the execution order changes the estimated toolchange cost.

## Cost Sensitivity Notes

The current fixture has one region per tool class. With a 60 second toolchange cost, every extra transition matters.

`minimize_toolchanges` avoids the initial 0.4-to-0.2 transition by scheduling the 0.4 visible detail region first. That does not mean the 0.2 detail region is rejected. It means the scheduler can preserve the quality-driven 0.2 assignment while still reducing one avoidable transition.

For real parts with many regions, this same grouping layer becomes more important:

```text
region assignment says what each region wants
scheduling says when it is worth changing tools
```

## Fallback/Rejection Notes

The current fixture regions pass the simple area/path cost gates from the continuous-resolution planner.

Fallback remains part of each scheduled step:

- 0.2 detail can fall back to 0.4 if scheduling or hardware validation rejects it.
- 0.6 structural shell can fall back to 0.4 if the region is too small or physical validation rejects it.
- 0.8 hidden bulk can fall back to 0.6 if the region size, toolchange cost, or hardware constraints make 0.8 unjustified.

0.8 bulk must pass cost gates and may fall back when region size is insufficient.

## Relationship To Future T-Code Emission

The scheduler is the step before a future T-code emission plan:

```text
continuous resolution field
-> quantized U1 tool/profile class
-> toolchange-aware schedule
-> future emission plan
-> future G-code integration
```

The scheduler output is not itself G-code. It names the intended tool/profile sequence and records why each step exists.

Generated ignored outputs:

```text
outputs/amp_toolchange_scheduler/schedule_minimize_toolchanges.json
outputs/amp_toolchange_scheduler/schedule_detail_first.json
outputs/amp_toolchange_scheduler/schedule_bulk_first.json
outputs/amp_toolchange_scheduler/schedule_layer_ordered.json
outputs/amp_toolchange_scheduler/schedule_summary.md
outputs/amp_toolchange_scheduler/schedule_summary.csv
outputs/amp_toolchange_scheduler/pseudo_toolchange_schedule.gcode.txt
```

The pseudo schedule is comments-only and explicitly marked not printable.

## What This Proves

- AMP can now produce an offline toolchange-aware execution schedule from region metadata and process-profile assignments.
- Toolchange scheduling is separate from region assignment.
- Scheduling mode changes execution order and estimated toolchange count without changing the underlying region desires.
- 0.2 detail may be kept for quality even when it is not time-saving.
- 0.8 bulk must pass cost gates and may fall back when region size is insufficient.
- This is the step before any future T-code emission plan.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate production `T0`, `T1`, `T2`, or `T3` commands.

This does not generate a single mixed-nozzle G-code print.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future/hardware-dependent.

This does not prove print strength, surface quality, dimensional accuracy, or bonding.
