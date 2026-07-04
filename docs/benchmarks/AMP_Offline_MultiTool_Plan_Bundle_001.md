# AMP Offline Multi-Tool Plan Bundle 001

## Purpose

This document records the first complete offline Adaptive Manufacturing Planner output bundle for the multi-tool resolution fixture.

The bundle connects:

```text
fixture regions
-> cost-gated solver assignment
-> fallback and risk flags
-> slice queue
-> per-region G-code status
-> planner report artifacts
```

This is offline/advisory tooling only. It does not generate a single mixed-nozzle print job.

## Generated Bundle

Command:

```powershell
python tools/amp_generate_offline_plan_bundle.py --input docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json --out outputs/amp_offline_plan_bundle_001
```

Generated ignored artifacts:

| Artifact | Purpose |
| --- | --- |
| `outputs/amp_offline_plan_bundle_001/plan.json` | Cost-gated advisory planner output. |
| `outputs/amp_offline_plan_bundle_001/slice_queue.json` | Per-region intended slicer inputs and existing G-code status. |
| `outputs/amp_offline_plan_bundle_001/risk_report.md` | Human-readable risk/fallback summary. |
| `outputs/amp_offline_plan_bundle_001/assignment_table.csv` | Tabular assignment output. |
| `outputs/amp_offline_plan_bundle_001/README.md` | Bundle overview. |
| `outputs/amp_offline_plan_bundle_001/assignment_solver_output.md` | Direct markdown output from the solver. |

## Input Fixture Regions

Committed metadata:

```text
docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json
```

| Region | Line type | Role | Visibility | Detail | XY min | Z feature | Vertical extent | Area | Path |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `micro_detail_zone` | external_perimeter | cosmetic | visible | micro | 0.35 mm | 0.12 mm | 0.45 mm / 6 layers | 250.0 mm^2 | 900.0 mm |
| `normal_visible_detail_zone` | top_surface | cosmetic | visible | high | 0.75 mm | 0.60 mm | 2.40 mm / 15 layers | 900.0 mm^2 | 1500.0 mm |
| `structural_shell_zone` | internal_perimeter | structural | internal | low | 2.40 mm | 8.00 mm | 8.00 mm / 33 layers | 2400.0 mm^2 | 2300.0 mm |
| `bulk_zone` | sparse_infill | hidden | hidden | none | 5.00 mm | 12.00 mm | 12.00 mm / 30 layers | 6500.0 mm^2 | 5200.0 mm |

All four regions use:

```text
estimated_toolchange_cost_s = 60.0
minimum_time_savings_required_s = 60.0
minimum_region_area_for_toolchange_mm2 = 200.0
minimum_path_length_for_toolchange_mm = 500.0
current_tool_class = 0.4
```

## Tool Capability Ladder

| Tool class | Planner role | Layer-height class | Line-width class |
| --- | --- | --- | --- |
| 0.2 | Fine/micro visible detail | 0.06-0.10 | 0.22 |
| 0.4 | Safe/general visible detail fallback | 0.12-0.20 | 0.42-0.45 |
| 0.6 | Structural shell / medium bulk | 0.24-0.36 | 0.62 |
| 0.8 | Hidden/internal bulk | 0.32-0.56 | 0.82 |

## Cost-Gated Assignment Table

| Region | Line type | Tool | Layer class | Width class | Fallback | Cost gate | Confidence |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| `micro_detail_zone` | external_perimeter | 0.2 | 0.06-0.10 | 0.22 | 0.4 | pass | 0.70 |
| `normal_visible_detail_zone` | top_surface | 0.4 | 0.12-0.20 | 0.42-0.45 | 0.2 | pass | 0.70 |
| `structural_shell_zone` | internal_perimeter | 0.6 | 0.24-0.36 | 0.62 | 0.4 | pass | 0.70 |
| `bulk_zone` | sparse_infill | 0.8 | 0.32-0.56 | 0.82 | 0.6 | pass | 0.70 |

Current fixture mapping:

```text
micro_detail_zone          -> 0.2
normal_visible_detail_zone -> 0.4
structural_shell_zone      -> 0.6
bulk_zone                  -> 0.8
```

## Fallback Table

| Region | Fallback | Reason |
| --- | --- | --- |
| `micro_detail_zone` | 0.4 | Use the general visible-detail tool if the 0.2 high-cost detail tool fails preview, material, or cost validation. |
| `normal_visible_detail_zone` | 0.2 | 0.4 is already the visible-detail recommendation; 0.2 remains an escalation path for detail failure, not the default. |
| `structural_shell_zone` | 0.4 | Use 0.4 if shell geometry becomes thin, visible, or tolerance-sensitive. |
| `bulk_zone` | 0.6 | Use 0.6 if the bulk region is too small or too close to visible/mating detail for 0.8. |

## Risk Flags

| Region | Risk flags |
| --- | --- |
| `micro_detail_zone` | U1 touchscreen advisory, `local_z_candidate`, `local_z_future_required`, `high_cost_detail_tool`, `preview_required` |
| `normal_visible_detail_zone` | U1 touchscreen advisory, `sloped_top_surface_visual_review`, `avoid_large_visible_tool` |
| `structural_shell_zone` | U1 touchscreen advisory, `internal_perimeter_width_review` |
| `bulk_zone` | U1 touchscreen advisory, `bulk_tool_cost_gate` |

The U1 touchscreen advisory means physical mixed-nozzle execution remains blocked for touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.

## Per-Region Slice Status

The bundle checked existing local per-region G-code outputs:

| Region | Tool | G-code path | Status | Size |
| --- | --- | --- | --- | ---: |
| `micro_detail_zone` | 0.2 | `outputs/amp_multitool_resolution_fixture/region_gcode/micro_detail_zone_0p2.gcode` | present | 372,294 bytes |
| `normal_visible_detail_zone` | 0.4 | `outputs/amp_multitool_resolution_fixture/region_gcode/normal_visible_detail_zone_0p4.gcode` | present | 209,503 bytes |
| `structural_shell_zone` | 0.6 | `outputs/amp_multitool_resolution_fixture/region_gcode/structural_shell_zone_0p6.gcode` | present | 255,782 bytes |
| `bulk_zone` | 0.8 | `outputs/amp_multitool_resolution_fixture/region_gcode/bulk_zone_0p8.gcode` | present | 97,702 bytes |

Metrics were pulled from:

```text
outputs/amp_multitool_resolution_fixture/reports/region_metrics.csv
```

| Region | Layers | Extrusion moves | Travel moves | Positive E | Estimate |
| --- | ---: | ---: | ---: | ---: | --- |
| `micro_detail_zone` | 28 | 8,790 | 924 | 540.789 | 20 min |
| `normal_visible_detail_zone` | 16 | 4,323 | 667 | 994.508 | 9 min |
| `structural_shell_zone` | 16 | 6,253 | 503 | 1,647.293 | 32 min |
| `bulk_zone` | 17 | 1,686 | 105 | 2,398.589 | 46 min |

These are slicer/G-code-derived values only.

## What This Proves

- AMP can now produce an offline cost-gated tool-class plan for the fixture.
- The plan includes fallbacks and cost-gate reasoning.
- The plan includes risk flags and confidence values.
- The plan records intended process and filament profiles.
- Per-region proxy G-code exists locally for each assigned tool class.
- The planner output now exists as a bundle that a future sidecar/debug-artifact bridge could consume.
- The fixture metadata now includes 3D feature fields and line/path role fields.
- The assignment is no longer based only on 2D area/path labels; it also includes XY feature size, Z feature height, vertical persistence, surface role, and line type.
- Local-Z need can be flagged as future work without implementing local-Z behavior.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not implement a single-object mixed-nozzle toolpath.

This does not implement local-Z.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or toolchange reliability.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.

## Next Implementation Step

The next safe implementation step is a planner-to-sidecar/debug-artifact mapping prototype:

```text
offline plan bundle with 3D/line-type metadata
-> AdaptiveManufacturingSidecar-compatible data
-> debug artifact JSON
```

That would connect the Python planner output to the behavior-neutral C++ AMP value types without wiring anything into production slicing.
