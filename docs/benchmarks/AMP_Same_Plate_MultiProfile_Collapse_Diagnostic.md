# AMP Same-Plate Multi-Profile Collapse Diagnostic

## Purpose

This diagnostic explains why the AMP same-plate multi-profile process queue probe exported G-code that collapsed to one active tool/profile behavior instead of preserving the four intended U1 process/tool classes.

This is diagnostic only. It does not implement mixed-nozzle slicing.

## Intended Process Queue

The offline AMP process-profile resolver selected this queue:

| Region | Intended tool class | Intended U1 process profile | Intended layer height | Intended width class |
| --- | ---: | --- | ---: | ---: |
| `micro_detail_zone` | 0.2 | `0.06 Standard @Snapmaker U1 (0.2 nozzle)` | 0.06 | 0.22 |
| `normal_visible_detail_zone` | 0.4 | `0.16 Optimal @Snapmaker U1 (0.4 nozzle)` | 0.16 | 0.42-0.45 |
| `structural_shell_zone` | 0.6 | `0.24 Standard @Snapmaker U1 (0.6 nozzle)` | 0.24 | 0.62 |
| `bulk_zone` | 0.8 | `0.40 Standard @Snapmaker U1 (0.8 nozzle)` | 0.40 | 0.82 |

The per-region validation showed that each selected process profile can slice its assigned region body when exported separately.

## Assemble-List Analysis

The generated assemble-list is:

```text
outputs/amp_same_plate_multitool_probe/assemble_list.json
```

It contains four object entries:

| Object | STL path | Filament ID | Object-level `print_params` |
| --- | --- | ---: | --- |
| `micro_detail_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/micro_detail_zone.stl` | 1 | `layer_height=0.06`, line widths `0.22`, `wall_generator=arachne` |
| `normal_visible_detail_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/normal_visible_detail_zone.stl` | 2 | `layer_height=0.16`, line widths `0.42`, `wall_generator=arachne` |
| `structural_shell_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/structural_shell_zone.stl` | 3 | `layer_height=0.24`, line widths `0.62`, `wall_generator=arachne` |
| `bulk_zone` | `outputs/amp_multitool_resolution_fixture/region_bodies/bulk_zone.stl` | 4 | `layer_height=0.40`, line widths `0.82`, `wall_generator=arachne` |

The companion metadata file records the intended process profiles:

```text
outputs/amp_same_plate_multitool_probe/metadata.json
```

That metadata includes the intended U1 process profile, nozzle class, layer height, filament ID, position, and object-level proxy settings for each region.

The Snapmaker Orca assemble-list parser accepts:

- `path`;
- `count`;
- `filaments`;
- `assemble_index`;
- `pos_x`, `pos_y`, `pos_z`;
- object-level `print_params`;
- height-range params;
- plate-level params.

The assemble-list schema does not provide a field for loading a full independent process profile per object. The generator therefore did not omit a supported per-object process-profile field; that field is not available in this CLI path.

## G-code Analysis

Same-plate output:

```text
outputs/amp_same_plate_multitool_probe/gcode/amp_same_plate_multitool_probe.gcode
```

The slice command exited `0` and exported G-code using:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe
```

Important header observations:

```text
; external perimeters extrusion width = 0.42mm
; perimeters extrusion width = 0.42mm
; infill extrusion width = 0.42mm
; solid infill extrusion width = 0.42mm
; top infill extrusion width = 0.42mm
; nozzle_diameter = 0.4,0.4,0.4,0.4
; print_settings_id = 0.20 Standard @Snapmaker U1 (0.4 nozzle)
; printer_settings_id = Snapmaker U1 (0.4 nozzle)
```

The loaded filament profile names were preserved:

```text
; filament_settings_id = "Generic PLA @U1 0.2 nozzle";"Snapmaker PLA Translucent @U1 0.4 nozzle";"Generic PLA @U1 0.6 nozzle";"Generic PLA @U1 0.8 nozzle"
```

But filament-profile names are not the same as nozzle/process-profile execution. The exported G-code still reports U1 0.4 printer/process behavior.

Tool command observations:

| Tool command | Count |
| --- | ---: |
| `T0` | 0 |
| `T1` | 3 |
| `T2` | 0 |
| `T3` | 0 |
| `T4` | 0 |

Object comments in the output only showed one object behavior:

```text
; printing object normal_visible_detail_zone_1 id:0 copy 0
; stop printing object normal_visible_detail_zone_1 id:0 copy 0
```

An explicit `assemble_index` variant also exported G-code, but still collapsed to one observed object comment:

```text
; printing object assemble_2 id:0 copy 0
; stop printing object assemble_2 id:0 copy 0
```

The same-plate metrics were:

| File | Size bytes | Layers | Tools | Toolchanges | Extrusion moves | Travel moves | Total positive E | Estimated time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `amp_same_plate_multitool_probe.gcode` | 236,622 | 20 | 1 | 3 | 4,839 | 792 | 915.452 | 14 min (M73 R) |

The metrics tool counted one active tool. The repeated toolchange count reflects repeated `T1` commands, not transitions across the intended 0.2 / 0.4 / 0.6 / 0.8 process queue.

## Comparison To Separate Per-Region G-code

Separate per-region exports retain their intended profile identity.

| Export | Header width class | `nozzle_diameter` | `print_settings_id` | Active tool |
| --- | --- | --- | --- | --- |
| same-plate proxy | 0.42 mm | `0.4,0.4,0.4,0.4` | `0.20 Standard @Snapmaker U1 (0.4 nozzle)` | `T1` |
| `micro_detail_zone_0p2_0p06.gcode` | 0.22 mm | `0.2,0.2,0.2,0.2` | `0.06 Standard @Snapmaker U1 (0.2 nozzle)` | `T0` |
| `normal_visible_detail_zone_0p4_0p16.gcode` | 0.42 / 0.45 mm | `0.4,0.4,0.4,0.4` | `0.16 Optimal @Snapmaker U1 (0.4 nozzle)` | `T0` |
| `structural_shell_zone_0p6_0p24.gcode` | 0.62 mm | `0.6,0.6,0.6,0.6` | `0.24 Standard @Snapmaker U1 (0.6 nozzle)` | `T0` |
| `bulk_zone_0p8_0p40.gcode` | 0.82 mm | `0.8,0.8,0.8,0.8` | `0.40 Standard @Snapmaker U1 (0.8 nozzle)` | `T0` |

The separate exports prove the selected U1 process profiles are slicer-readable. The same-plate export proves that the current assemble-list route does not carry those full process identities into one combined job.

## Collapse Cause

The collapse is best classified as a representation/merge limitation, not an assignment failure.

Observed causes:

- The assemble-list schema can carry object-level `print_params`, but not a full independent process profile per object.
- The CLI loads one global machine/process stack for the plate.
- The output G-code reports the global U1 0.4 process profile and global U1 0.4 nozzle list.
- Repeated `--load-filaments` can preserve multiple filament profile names, but does not establish four nozzle/process classes.
- The emitted tool stream uses one active tool command (`T1`).
- Object comments collapse to one observed object behavior.

The generator is not the clear cause. It encoded the intended process queue in metadata and encoded the closest supported object-level proxy settings into `print_params`.

The missing capability is a slicer-facing representation that can preserve complete per-object process/nozzle classes in one job.

## What This Means For AMP

The offline planner chain remains valid:

```text
region metadata
-> tool-class assignment
-> cost gating
-> concrete U1 process profile selection
-> per-region slice queue
```

The current same-plate assemble-list proxy is not sufficient as a carrier for a real multi-profile or mixed-nozzle plan.

For now:

- per-region separate G-code remains the safe slicer-readability proxy;
- the same-plate proxy is useful as a capability probe only;
- AMP should preserve its full process queue in debug artifacts rather than relying on assemble-list G-code as proof;
- true single-object mixed-nozzle slicing requires later slicer integration or a richer project representation.

## Possible Next Paths

1. Keep per-region separate G-code as the current safe proxy.

2. Add planner-bundle to debug-artifact JSON export so the full queue, reasons, fallbacks, and local-Z flags can be reviewed deterministically without depending on G-code representation.

3. Investigate 3MF project representation:

   ```text
   Can a 3MF plate preserve multiple objects with distinct process profiles/nozzle classes in a way Snapmaker Orca keeps on reload/slice?
   ```

4. Treat single-object mixed-nozzle slicing as future slicer integration work, not a CLI assemble-list workaround.

5. Keep Fluidd-only experimentation future and hardware-dependent.

6. Keep the touchscreen-compatible path blocked pending Snapmaker per-tool metadata and logical/physical toolhead mapping support.

## Non-Claims

This does not implement mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

This diagnosis only explains why same-plate proxy output does not preserve four tool classes.

This does not prove that Snapmaker Orca cannot ever support this; it only documents the limitation of the current CLI assemble-list proxy path tested here.
