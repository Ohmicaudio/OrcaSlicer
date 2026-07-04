# AMP Same-Plate Multi-Profile Process Queue Probe 001

## Purpose

This probe tests whether the offline AMP process-profile queue can be represented as a single Snapmaker Orca plate containing separated region bodies.

The goal is preview/proxy evidence only:

```text
offline AMP plan
-> separated region bodies
-> assemble-list proxy
-> Snapmaker Orca CLI G-code export
```

This is not true single-object mixed-nozzle slicing.

## Why This Is a Proxy

Snapmaker Orca's CLI assemble-list path supports per-object `print_params`. It does not load a separate full U1 process profile per object.

For this probe, the intended U1 process profile for each region is recorded as metadata, then approximated through object-level settings where the assemble-list path can express them:

- `layer_height`
- role-specific line-width settings
- `wall_generator`
- filament/extruder ID

The CLI still loads one base machine/process stack for the plate.

## Inputs

Region bodies:

```text
outputs/amp_multitool_resolution_fixture/region_bodies/micro_detail_zone.stl
outputs/amp_multitool_resolution_fixture/region_bodies/normal_visible_detail_zone.stl
outputs/amp_multitool_resolution_fixture/region_bodies/structural_shell_zone.stl
outputs/amp_multitool_resolution_fixture/region_bodies/bulk_zone.stl
```

Generator:

```text
tools/amp_generate_multitool_same_plate_probe.py
```

Generated ignored files:

```text
outputs/amp_same_plate_multitool_probe/assemble_list.json
outputs/amp_same_plate_multitool_probe/metadata.json
```

## Resolved Process-Profile Queue

| Region | Intended tool class | Intended U1 process profile | Intended layer height | Object-level proxy width |
| --- | ---: | --- | ---: | ---: |
| `micro_detail_zone` | 0.2 | `resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | 0.06 | 0.22 |
| `normal_visible_detail_zone` | 0.4 | `resources/profiles/Snapmaker/process/0.16 Optimal @Snapmaker U1 (0.4 nozzle).json` | 0.16 | 0.42 |
| `structural_shell_zone` | 0.6 | `resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | 0.24 | 0.62 |
| `bulk_zone` | 0.8 | `resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | 0.40 | 0.82 |

## Assemble-List Method

Command:

```powershell
python tools\amp_generate_multitool_same_plate_probe.py
```

The generated assemble-list places the four region bodies on one plate with explicit spacing. Each object includes:

- STL path;
- filament ID;
- X/Y/Z position;
- object-level `print_params`;
- intended process profile recorded in `metadata.json`.

The generated `print_params` are intentionally limited to settings the CLI parser accepts as string key/value pairs. Full process-profile loading remains outside the assemble-list format.

## Slice Result

Successful slice command used:

```powershell
B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe --debug 1 --slice 0 --outputdir B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_same_plate_multitool_probe\gcode\same_plate_multitool_probe_attempt_002 --load-settings B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json --load-settings B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\process\0.20 Standard @Snapmaker U1 (0.4 nozzle).json --load-filaments B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\filament\Generic PLA @U1 0.2 nozzle.json --load-filaments B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\filament\Snapmaker PLA Translucent @U1 0.4 nozzle.json --load-filaments B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\filament\Generic PLA @U1 0.6 nozzle.json --load-filaments B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\filament\Generic PLA @U1 0.8 nozzle.json --load-assemble-list B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_same_plate_multitool_probe\assemble_list.json
```

| Attempt | Executable | Result |
| --- | --- | --- |
| `same_plate_multitool_probe_attempt_002` | `B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe` | exit `0`, G-code exported |

Output:

```text
outputs/amp_same_plate_multitool_probe/gcode/amp_same_plate_multitool_probe.gcode
```

The generated G-code is previewable, but it does not faithfully represent all four intended tool/profile classes.

## G-code/Header Observations

Header excerpt:

```text
; total layer number: 20
; external perimeters extrusion width = 0.42mm
; perimeters extrusion width = 0.42mm
; infill extrusion width = 0.42mm
; solid infill extrusion width = 0.42mm
; top infill extrusion width = 0.42mm
```

Observed object comments:

```text
; printing object normal_visible_detail_zone_1 id:0 copy 0
; stop printing object normal_visible_detail_zone_1 id:0 copy 0
```

The G-code did not show separate object comments for all four region bodies.

An explicit `assemble_index` variant also exported G-code, but still collapsed to a single observed object comment:

```text
; printing object assemble_2 id:0 copy 0
; stop printing object assemble_2 id:0 copy 0
```

## Toolchange/Nozzle Observations

The output uses only one active tool command:

```text
T1
```

Tool command count:

| Tool command | Count |
| --- | ---: |
| `T0` | 0 |
| `T1` | 3 |
| `T2` | 0 |
| `T3` | 0 |
| `T4` | 0 |

The G-code does include U1 startup routines that reference multiple extruder indices for preheat/feed/flow calibration, but the actual tool command stream did not represent the intended 0.2 / 0.4 / 0.6 / 0.8 process queue as separate active tools.

The header did not expose a four-nozzle `nozzle_diameter` representation for this same-plate proxy.

## Metrics Summary

Metrics command:

```powershell
python tools\amp_gcode_metrics.py outputs\amp_same_plate_multitool_probe\gcode\amp_same_plate_multitool_probe.gcode --csv outputs\amp_same_plate_multitool_probe\reports\metrics.csv --summary outputs\amp_same_plate_multitool_probe\reports\summary.md
```

| File | Size bytes | Layers | Tools | Toolchanges | Extrusion moves | Travel moves | Total positive E | Estimated time | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `amp_same_plate_multitool_probe.gcode` | 236,622 | 20 | 1 | 3 | 4,839 | 792 | 915.452 | 14 min (M73 R) | missing filament usage comment |

The metrics tool counts one tool in the output. The `toolchanges` count reflects repeated `T1` commands, not transitions across the intended 0.2 / 0.4 / 0.6 / 0.8 queue.

## Failed or Limited Attempts

| Attempt | Result | Classification |
| --- | --- | --- |
| `four_intended_filament_profiles` with the `cli-0p2-fix` executable | exit `-1073741819`, no G-code | local executable did not include a working assemble-list path |
| Known-good thin-wall assemble-list control with the `cli-0p2-fix` executable | exit `-1073741819`, no G-code | confirms that executable is not valid for assemble-list validation |
| Old `Snapmaker-OrcaSlicer-cli-fix` worktree executable | exit `-1073741819`, no G-code | local old build not usable for this validation |
| Multiple filament paths after a single `--load-filaments` option | exit `-2`, no G-code | CLI treats extra paths as model inputs when used with `--load-assemble-list` |
| Successful assemble-list build with explicit `assemble_index` values | exit `0`, G-code exported | still collapsed to one observed active object/tool behavior |

## What This Proves

- AMP can generate a same-plate assemble-list proxy from the resolved process-profile queue.
- The generated assemble-list can be accepted by a local hardened Snapmaker Orca CLI build.
- A previewable G-code file can be exported from the separated-region same-plate proxy.
- The probe is useful for identifying current CLI/profile representation limits before touching slicer internals.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate a faithful single mixed-nozzle G-code file.

This does not prove that all four intended U1 process profiles were applied on one plate.

This does not merge the separated region bodies back into one object.

This does not validate physical mixed-nozzle behavior.

This does not prove touchscreen compatibility.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.

## Conclusion

The same-plate proxy can be generated and sliced, but the current CLI assemble-list route does not faithfully carry the AMP four-region process queue into G-code.

The observed output collapses to one active tool/profile behavior. That makes this useful as a capability probe, not as validation of multi-tool AMP slicing.

## Next Step

The next safer step is planner bundle to debug artifact JSON export. That preserves the complete AMP queue, reasons, fallbacks, and local-Z flags without relying on assemble-list behavior to impersonate a real mixed-nozzle slicer path.

A later slicer integration step should only proceed after the debug artifact path can represent the queue deterministically and after Snapmaker's U1 per-tool metadata/logical mapping path is better understood.
