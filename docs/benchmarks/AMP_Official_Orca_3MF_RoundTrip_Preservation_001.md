# AMP Official Orca 3MF RoundTrip Preservation 001

## Purpose

Determine whether the official Orca GUI project/3MF path preserves the repaired four-object mixed-nozzle setup after save and reopen.

This is representation validation only. It does not implement AMP mixed-nozzle slicing.

## Known Successful GUI Mixed-Nozzle G-code Baseline

Known successful G-code:

```text
C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\gcode\official_orca_mixed_probe_0p12_fixed_models.gcode
```

Known GUI assignment:

| Region | GUI tool slot | G-code tool | Nozzle |
| --- | ---: | --- | ---: |
| `micro_detail_zone` | 1 | `T0` | `0.2` |
| `normal_visible_detail_zone` | 2 | `T1` | `0.4` |
| `structural_shell_zone` | 3 | `T2` | `0.6` |
| `bulk_zone` | 4 | `T3` | `0.8` |

Known G-code evidence:

```text
nozzle_diameter = 0.2,0.4,0.6,0.8,0.8
active tools = T0,T1,T2,T3
```

The fifth `0.8` is an unused extra preset/tool slot.

## Original 3MF Inspection

Original 3MF:

```text
C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\orca_official_mixed_nozzle_original.3mf
```

Creation method:

- Official Orca GUI loaded the repaired four-object mixed-nozzle probe.
- The project was saved with Orca's `Save Project as` shortcut.
- The saved project was reopened through Orca's `Open Project` dialog.

Package summary:

| Field | Result |
| --- | --- |
| File size | 49,699 bytes |
| SHA-256 | `5bf496e71255f45cd47943a6f0a4d5318123b3cc37721f0217bdd121ed7e19c7` |
| ZIP entries | 18 |
| Nozzle vector | `0.2,0.4,0.6,0.8,0.8` |
| Print settings ID | `0.12mm Mixed Probe @AMP Mixed ToolChanger` |
| Printer settings ID | `AMP Mixed ToolChanger 0.2-0.4-0.6-0.8` |
| Printer model | `Generic ToolChanger Printer` |

Object/tool metadata from `Metadata/model_settings.config`:

| Object | Stored extruder |
| --- | ---: |
| `micro_detail_zone.stl` | 1 |
| `normal_visible_detail_zone.stl` | 2 |
| `structural_shell_zone.stl` | 3 |
| `bulk_zone.stl` | 4 |

The package also contains distinct object model entries:

```text
3D/Objects/micro_detail_zone.stl_1.model
3D/Objects/normal_visible_detail_zone.stl_2.model
3D/Objects/structural_shell_zone.stl_3.model
3D/Objects/bulk_zone.stl_4.model
```

## Roundtrip 3MF Inspection

Roundtrip 3MF:

```text
C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\orca_official_mixed_nozzle_roundtrip.3mf
```

Method note:

Orca successfully reopened the original 3MF. The reopened current project was saved with `Ctrl+S`. Because the Windows Save As dialog repeatedly focused the Search field while trying to create a second filename through automation, the reopened/resaved package was copied to the roundtrip filename for package inspection. The copied roundtrip artifact is byte-identical to the reopened/resaved project file.

Package summary:

| Field | Result |
| --- | --- |
| File size | 49,699 bytes |
| SHA-256 | `5bf496e71255f45cd47943a6f0a4d5318123b3cc37721f0217bdd121ed7e19c7` |
| ZIP entries | 18 |
| Nozzle vector | `0.2,0.4,0.6,0.8,0.8` |
| Print settings ID | `0.12mm Mixed Probe @AMP Mixed ToolChanger` |
| Printer settings ID | `AMP Mixed ToolChanger 0.2-0.4-0.6-0.8` |
| Printer model | `Generic ToolChanger Printer` |
| Byte-identical to original | yes |

Object/tool metadata from `Metadata/model_settings.config`:

| Object | Stored extruder |
| --- | ---: |
| `micro_detail_zone.stl` | 1 |
| `normal_visible_detail_zone.stl` | 2 |
| `structural_shell_zone.stl` | 3 |
| `bulk_zone.stl` | 4 |

## Roundtrip G-code Inspection

No separate roundtrip G-code export was created in this pass.

The successful original G-code export remains the current G-code baseline. The 3MF package inspection verifies that the project representation preserves the object/tool/nozzle metadata needed to reproduce that manual GUI workflow.

## Object/Tool Assignment Preservation Result

Result: preserved.

Official Orca 3MF preserves the four distinct region objects and their manual tool assignments:

```text
micro_detail_zone.stl -> extruder 1 -> T0 intent
normal_visible_detail_zone.stl -> extruder 2 -> T1 intent
structural_shell_zone.stl -> extruder 3 -> T2 intent
bulk_zone.stl -> extruder 4 -> T3 intent
```

## Nozzle/Profile Preservation Result

Result: partially preserved.

The project-level nozzle vector is preserved:

```text
0.2,0.4,0.6,0.8,0.8
```

The mixed probe process/printer IDs are preserved:

```text
0.12mm Mixed Probe @AMP Mixed ToolChanger
AMP Mixed ToolChanger 0.2-0.4-0.6-0.8
```

However, this remains a shared/global process profile in this probe. It does not preserve AMP's richer per-region U1 process/layer-height plan:

```text
0.06 / 0.16 / 0.24 / 0.40
```

## Comparison To CLI Assemble-List Collapse

The CLI assemble-list path previously collapsed or failed to express the full mixed-process workflow reliably.

The official Orca GUI 3MF path is stronger for representation:

| Capability | CLI assemble-list | Official Orca 3MF |
| --- | --- | --- |
| Four region objects | yes, but fragile | yes |
| Object-to-tool assignment | weak/limited | preserved as `extruder` metadata |
| Nozzle vector | not reliable in scratch CLI path | preserved globally |
| Manual mixed-nozzle G-code path | not proven through scratch CLI | proven through GUI export |
| Per-region AMP layer plan | not represented | not represented in this probe |

## Comparison To AMP Sidecar Plan Bundle

Official Orca 3MF is now a viable manual execution/review bridge for:

- object identity
- object-to-tool assignment
- project-level nozzle vector
- printer/process IDs
- later GUI export validation

AMP sidecar remains authoritative for:

- region confidence
- fallback tools
- cost-gate reasons
- per-region intended U1 process profiles
- per-region layer-height intent
- safety and execution warnings
- touchscreen mixed-nozzle block status

## Decision

Decision: use a hybrid official Orca 3MF plus AMP sidecar authority path.

Official Orca 3MF preserves objects/tool slots and the global nozzle vector well enough to serve as AMP's first manual execution bridge.

It does not yet prove full per-region process/nozzle/layer-height execution. AMP should therefore keep its sidecar packet as the authority for planner intent and use the official Orca 3MF/project file as the manual GUI setup and export vehicle.

Recommended bridge path:

```text
AMP plan packet
-> official Orca 3MF with region objects and tool assignments
-> AMP sidecar authority for process/layer/fallback/safety intent
-> official Orca GUI export
-> AMP G-code conformance validator
```

## Required Non-Claims

This does not implement AMP mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not prove Snapmaker U1 touchscreen compatibility.

This does not bypass Snapmaker validation.

This does not recommend printing the file.
