# AMP Official Orca GUI Mixed-Nozzle Vs AMP Plan 001

## Purpose

Compare the repaired official Orca GUI mixed-nozzle G-code baseline against AMP's offline advisory plan packet.

This report connects two separate facts:

- Official upstream Orca GUI can produce a manual/static mixed-nozzle G-code representation.
- AMP can produce an automatic offline plan packet with region, tool, profile, fallback, cost, and warning metadata.

This does not implement AMP mixed-nozzle slicing.

## Official Orca GUI Setup

Executable:

`C:\Users\d\tools\OrcaSlicer\V2.4.1_portable_full\orca-slicer.exe`

Exported G-code:

`C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\gcode\official_orca_mixed_probe_0p12_fixed_models.gcode`

Local preview screenshot:

`C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\rerun_exported_fixed_models_preview.png`

Local probe setup:

- Printer preset: `AMP Mixed ToolChanger 0.2-0.4-0.6-0.8`
- Process preset: `0.12mm Mixed Probe @AMP Mixed ToolChanger`
- Filament preset: `Generic PETG @AMP Mixed ToolChanger`
- Line widths: percentage-based `120%`
- Prime tower: disabled for this representation probe
- Four STL region bodies loaded as separate objects

Object/tool assignment:

| Region object | Orca tool slot | G-code tool command |
| --- | ---: | --- |
| `micro_detail_zone.stl` | 1 | `T0` |
| `normal_visible_detail_zone.stl` | 2 | `T1` |
| `structural_shell_zone.stl` | 3 | `T2` |
| `bulk_zone.stl` | 4 | `T3` |

## Repaired Model Note

The first GUI export succeeded, but Orca warned that `normal_visible_detail_zone.stl` had floating regions. That warning was caused by the generated fixture, not by the Orca mixed-nozzle workflow.

The fixture generator was repaired so the normal visible-detail region uses a supported flat detail pad and slightly embedded raised features. The four repaired/current STL files were checked before rerunning:

| STL | Unsupported above-base components |
| --- | ---: |
| `micro_detail_zone.stl` | 0 |
| `normal_visible_detail_zone.stl` | 0 |
| `structural_shell_zone.stl` | 0 |
| `bulk_zone.stl` | 0 |

The repaired-model GUI rerun sliced and exported without the visible floating-region warning.

## G-code Inspection Results

Inspector command:

```text
python tools\amp_inspect_mixed_nozzle_gcode.py "C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\gcode\official_orca_mixed_probe_0p12_fixed_models.gcode" --out outputs\amp_orca_official_mixed_nozzle_baseline\repaired_gui_probe_reports
```

Inspector summary:

| Field | Result |
| --- | --- |
| Nozzle diameter values | `0.2,0.4,0.6,0.8` |
| Active tools | `0,1,2,3` |
| T commands | 80 |
| Extrusion moves | 25,228 |
| Per-tool extrusion moves | `0=4875; 1=6623; 2=10389; 3=3341` |
| Mixed-nozzle evidence | yes |
| Inspector warnings | none |

Header evidence:

```text
; nozzle_diameter = 0.2,0.4,0.6,0.8,0.8
; print_settings_id = 0.12mm Mixed Probe @AMP Mixed ToolChanger
; printer_settings_id = AMP Mixed ToolChanger 0.2-0.4-0.6-0.8
```

Preview summary:

| Field | Result |
| --- | ---: |
| Estimated total time | `36m18s` |
| Total filament | `15.61g` |
| Preview tool changes | 78 |
| Filament change times | 0 |

## Nozzle Header Analysis

The header contains five nozzle diameter values:

```text
0.2,0.4,0.6,0.8,0.8
```

The probe used Orca's Generic ToolChanger sample infrastructure, which has five tool slots. AMP assigned only four objects/tools. The fifth value is an unused fifth sample-toolchanger slot, duplicated as `0.8` in the local probe preset.

For the AMP comparison, the active nozzle classes are the first four assigned slots:

```text
T0 -> 0.2
T1 -> 0.4
T2 -> 0.6
T3 -> 0.8
```

The fifth header value should not be interpreted as a fifth AMP region or as proof of five active tools.

## Tool Command Analysis

Tool-command counts in the repaired export:

| Tool command | Count | Assigned region |
| --- | ---: | --- |
| `T0` | 16 | `micro_detail_zone` |
| `T1` | 28 | `normal_visible_detail_zone` |
| `T2` | 18 | `structural_shell_zone` |
| `T3` | 18 | `bulk_zone` |

All four assigned tools appear in output and all four tools have extrusion moves.

The active tool order alternates heavily by layer/object because this is a normal Orca by-layer multi-tool output, not AMP's offline scheduled execution order. The raw G-code includes 80 `T` commands; compressed adjacent duplicate removal gives 79 transitions.

The file also includes object markers such as:

```text
EXCLUDE_OBJECT_DEFINE NAME=micro_detail_zone.stl_id_0_copy_0
EXCLUDE_OBJECT_DEFINE NAME=normal_visible_detail_zone.stl_id_1_copy_0
EXCLUDE_OBJECT_DEFINE NAME=structural_shell_zone.stl_id_2_copy_0
EXCLUDE_OBJECT_DEFINE NAME=bulk_zone.stl_id_3_copy_0
```

These comments are useful for validation, but they do not carry AMP confidence, fallback, cost, or safety-gating metadata.

## AMP Plan Packet Comparison

AMP packet input:

`outputs/amp_plan_packet_001/`

Relevant files:

- `process_queue.json`
- `tool_assignments.json`
- `toolchange_schedule.json`
- `debug_artifact.json`

Mapping:

| AMP region | AMP recommended tool class | AMP selected process profile | Official Orca assigned tool | Official Orca nozzle class | G-code T evidence | Match status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `micro_detail_zone` | `0.2` | `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | tool slot 1 | `0.2` | `T0`, 4,875 extrusion moves | match for XY/tool class | Orca uses shared `0.12` layer height, not AMP's future/local `0.06` request. |
| `normal_visible_detail_zone` | `0.4` | `0.16 Optimal @Snapmaker U1 (0.4 nozzle).json` | tool slot 2 | `0.4` | `T1`, 6,623 extrusion moves | match for XY/tool class | Orca uses shared `0.12` layer height, lower than AMP's selected `0.16` U1 process profile. |
| `structural_shell_zone` | `0.6` | `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | tool slot 3 | `0.6` | `T2`, 10,389 extrusion moves | match for XY/tool class | Orca uses shared `0.12` layer height, not AMP's selected `0.24` U1 process profile. |
| `bulk_zone` | `0.8` | `0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | tool slot 4 | `0.8` | `T3`, 3,341 extrusion moves | match for XY/tool class | Orca uses shared `0.12` layer height, not AMP's selected `0.40` U1 process profile. |

Result:

Official Orca preserves AMP's intended region-to-tool/nozzle mapping for this four-object representation probe. It does not preserve AMP's per-region process-profile or layer-height plan.

## Shared Layer-Height Observation

The Orca GUI probe used a shared process profile:

```text
0.12mm Mixed Probe @AMP Mixed ToolChanger
```

The G-code contains Z moves consistent with shared `0.12` stepping across the mixed-tool plate. Width comments vary by tool/nozzle class because the process used percentage-based widths:

| Tool/nozzle class | Representative WIDTH comments |
| --- | --- |
| `0.2` | approximately `0.24` |
| `0.4` | approximately `0.48` |
| `0.6` | approximately `0.72` |
| `0.8` | approximately `0.96` |

This confirms the useful manual/static baseline: one shared process/layer-height path, multiple nozzle widths by tool.

It also confirms the gap for AMP's full multi-resolution target. AMP's packet includes distinct selected U1 process profiles and desired layer heights (`0.06`, `0.16`, `0.24`, `0.40`), but official Orca's manual GUI baseline does not express those per-region Z choices in this probe.

## 3MF Status

The requested 3MF files were not present:

```text
C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\orca_official_mixed_nozzle_original.3mf
C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\orca_official_mixed_nozzle_roundtrip.3mf
```

G-code baseline exists.

3MF save/reopen preservation remains pending.

## What This Proves

Official upstream Orca GUI can produce mixed-nozzle G-code for the repaired four-region probe.

The exported G-code preserves multiple nozzle diameter values and emits real `T0`, `T1`, `T2`, and `T3` commands.

Official Orca GUI is now AMP's primary manual/static mixed-nozzle baseline.

AMP should not claim Orca lacks mixed-nozzle support.

AMP's distinct role is automatic region/tool/profile planning, cost gating, fallback reasoning, sidecar/debug contracts, and execution/preflight gating.

The official Orca GUI output includes enough object names, nozzle headers, tool commands, and width comments for a validator to compare basic region/tool mapping against AMP's packet.

## What This Does Not Prove

This does not implement AMP mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not prove Snapmaker U1 touchscreen compatibility.

This does not bypass Snapmaker validation.

This does not replace official Orca's manual workflow.

This does not prove independent per-tool or per-region layer height.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or safe printer execution.

## Next Bridge

The next bridge is not another proof that mixed-nozzle G-code can exist. The next bridge is:

```text
AMP plan packet
-> official Orca manual workflow guide / project manifest
-> G-code validator that checks Orca output against the AMP packet
-> later 3MF save/reopen preservation test
```

The sidecar remains the authority for AMP-specific data that G-code does not carry:

- confidence
- fallback tools
- cost-gate reasons
- local-Z advisory status
- touchscreen mixed-nozzle block status
- U1 execution/preflight warnings

Until Snapmaker U1 hardware validation and metadata support exist, this remains a representation and planning bridge, not a production mixed-nozzle execution path.
