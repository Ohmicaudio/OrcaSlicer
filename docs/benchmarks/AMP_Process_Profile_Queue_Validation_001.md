# AMP Process Profile Queue Validation 001

## Purpose

This report validates the first AMP U1 process-profile slice queue against real Snapmaker Orca CLI slicing.

The queue under test was generated from:

```text
region metadata
-> 3D / line-type-aware tool-class assignment
-> cost gating
-> concrete Snapmaker U1 process profile selection
-> offline slice queue
```

This is offline/advisory benchmarking only. It validates that each assigned region body can be sliced separately with the exact U1 process profile selected by the AMP resolver.

## Commands

Resolver command:

```powershell
python tools\amp_u1_process_profile_resolver.py --input docs\benchmarks\AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json --out outputs\amp_process_profile_resolver\multitool_fixture_process_queue.json
```

Offline bundle command:

```powershell
python tools\amp_generate_offline_plan_bundle.py --input docs\benchmarks\AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json --out outputs\amp_offline_plan_bundle_001
```

Metrics command:

```powershell
python tools\amp_gcode_metrics.py outputs\amp_process_profile_queue_validation\gcode --csv outputs\amp_process_profile_queue_validation\reports\metrics.csv --summary outputs\amp_process_profile_queue_validation\reports\summary.md
```

CLI executable used for slicing:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\snapmaker-orca-console.exe
```

The slice commands used the same pattern for each region:

```powershell
snapmaker-orca-console.exe --debug 1 --slice 0 --outputdir <case-output-dir> --load-settings <U1-machine-profile> --load-settings <selected-process-profile> --load-filaments <selected-filament-profile> <region-body-stl>
```

The full per-region commands are recorded in the ignored output file:

```text
outputs/amp_process_profile_queue_validation/gcode/slice_results.json
```

## Region-to-Profile Queue

| Region | Region body | Tool class | Selected U1 process profile | Layer height | Width class | Filament profile |
| --- | --- | ---: | --- | ---: | --- | --- |
| `micro_detail_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/micro_detail_zone.stl` | 0.2 | `resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | 0.06 | 0.22 | `resources/profiles/Snapmaker/filament/Generic PLA @U1 0.2 nozzle.json` |
| `normal_visible_detail_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/normal_visible_detail_zone.stl` | 0.4 | `resources/profiles/Snapmaker/process/0.16 Optimal @Snapmaker U1 (0.4 nozzle).json` | 0.16 | 0.42-0.45 | `resources/profiles/Snapmaker/filament/Snapmaker PLA Translucent @U1 0.4 nozzle.json` |
| `structural_shell_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/structural_shell_zone.stl` | 0.6 | `resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | 0.24 | 0.62 | `resources/profiles/Snapmaker/filament/Generic PLA @U1 0.6 nozzle.json` |
| `bulk_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/bulk_zone.stl` | 0.8 | `resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | 0.40 | 0.82 | `resources/profiles/Snapmaker/filament/Generic PLA @U1 0.8 nozzle.json` |

## Slice Pass/Fail Table

| Region | Output G-code | Exit code | Exported | CLI warnings/errors |
| --- | --- | ---: | --- | --- |
| `micro_detail_zone` | `outputs/amp_process_profile_queue_validation/gcode/micro_detail_zone_0p2_0p06.gcode` | 0 | yes | Non-fatal stdout warning: `PartPlate::calc_exclude_triangles:Unable to create exclude triangles` |
| `normal_visible_detail_zone` | `outputs/amp_process_profile_queue_validation/gcode/normal_visible_detail_zone_0p4_0p16.gcode` | 0 | yes | Non-fatal stdout warning: `PartPlate::calc_exclude_triangles:Unable to create exclude triangles` |
| `structural_shell_zone` | `outputs/amp_process_profile_queue_validation/gcode/structural_shell_zone_0p6_0p24.gcode` | 0 | yes | Non-fatal stdout warning: `PartPlate::calc_exclude_triangles:Unable to create exclude triangles` |
| `bulk_zone` | `outputs/amp_process_profile_queue_validation/gcode/bulk_zone_0p8_0p40.gcode` | 0 | yes | Non-fatal stdout warning: `PartPlate::calc_exclude_triangles:Unable to create exclude triangles` |

All four selected region/profile pairs produced G-code.

## Metrics

| Region | G-code size | Layers | Tools | Toolchanges | Extrusion moves | Travel moves | Total positive E | Estimated time | Metrics warning |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `micro_detail_zone` | 370,953 | 28 | 1 | 2 | 8,782 | 921 | 540.786 | 20 min (M73 R) | missing filament usage comment |
| `normal_visible_detail_zone` | 232,339 | 20 | 1 | 2 | 5,036 | 684 | 1,040.969 | 10 min (M73 R) | missing filament usage comment |
| `structural_shell_zone` | 255,782 | 16 | 1 | 2 | 6,253 | 503 | 1,647.293 | 32 min (M73 R) | missing filament usage comment |
| `bulk_zone` | 99,195 | 17 | 1 | 2 | 1,710 | 111 | 2,398.836 | 46 min (M73 R) | missing filament usage comment |

Estimated print time is slicer/G-code-derived and is not a physical print measurement.

## Local-Z Flags

| Region | Local-Z future required | Meaning |
| --- | --- | --- |
| `micro_detail_zone` | true | The resolver selected the 0.06 mm 0.2 process profile and preserved the `local_z_future_required` flag. This recognizes shallow/fine Z detail, but local-Z behavior is not implemented. |
| `normal_visible_detail_zone` | false | Uses a single selected global 0.16 mm process profile in this validation. |
| `structural_shell_zone` | false | Uses a single selected global 0.24 mm process profile in this validation. |
| `bulk_zone` | false | Uses a single selected global 0.40 mm process profile in this validation. |

## Fallback Profiles

| Region | Selected tool | Fallback tool | Fallback process profile |
| --- | ---: | ---: | --- |
| `micro_detail_zone` | 0.2 | 0.4 | `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json` |
| `normal_visible_detail_zone` | 0.4 | 0.2 | `resources/profiles/Snapmaker/process/0.08 Standard @Snapmaker U1 (0.2 nozzle).json` |
| `structural_shell_zone` | 0.6 | 0.4 | `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json` |
| `bulk_zone` | 0.8 | 0.6 | `resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json` |

Fallbacks are advisory. They were not used by this validation run.

## Observed Warnings

The Snapmaker Orca CLI emitted this non-fatal stdout warning for each region:

```text
Slic3r::GUI::PartPlate::calc_exclude_triangles:Unable to create exclude triangles
```

Each case still exited 0 and exported G-code.

The metrics tool reported `missing filament usage comment` for all four outputs. This affects the metrics report's filament usage field only; G-code files were still produced.

## What This Proves

- AMP can map fixture regions to concrete Snapmaker U1 process profiles.
- Each selected U1 process profile was tested against its assigned region body.
- The offline process-profile queue is slicer-readable as separate per-region inputs.
- The selected 0.2, 0.4, 0.6, and 0.8 U1 profile families can each export G-code for the assigned fixture region.
- Local-Z requirements can be carried through the advisory queue as flags.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate a single mixed-nozzle G-code file.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.

This does not implement local-Z.

This does not prove print strength, surface quality, dimensional accuracy, or bonding.

## Next Required Step

The next useful step is to convert the offline queue into a deterministic debug-artifact style bundle that can be inspected without touching production slicing. A later integration step can then compare the advisory bundle against real slicer objects, still before any toolpath or G-code behavior changes.
