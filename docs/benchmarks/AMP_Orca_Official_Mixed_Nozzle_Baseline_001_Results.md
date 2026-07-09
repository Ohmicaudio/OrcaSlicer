# AMP Orca Official Mixed Nozzle Baseline 001 Results

## Purpose

Run a first local baseline probe against the official OrcaSlicer mixed nozzle-size workflow and compare the result with AMP's offline planner direction.

This is baseline investigation only. It does not implement AMP mixed-nozzle slicing, does not validate physical mixed-nozzle behavior, does not prove touchscreen-compatible mixed-nozzle execution, and does not bypass Snapmaker validation.

## Official Orca Mixed-Nozzle Workflow Summary

Official OrcaSlicer documentation states that mixed nozzle sizes are supported since `v2.2.0-beta`:

<https://www.orcaslicer.com/wiki/guides/mixed_nozzle_sizes>

The documented workflow is manual/static:

- set nozzle diameter per extruder
- use nozzle-agnostic percentage-based line widths
- assign features/tools through Filament for Features or painting workflows
- calibrate each material/nozzle combination where needed

AMP should not claim that Orca lacks mixed-nozzle support. AMP's distinct value remains automated geometry-driven resolution planning, continuous-to-discrete tool quantization, cost gating, fallback reasoning, sidecar/debug contracts, and U1-safe execution gating.

## Inputs

Region bodies:

`outputs/amp_multitool_resolution_fixture/region_bodies/`

Intended AMP queue:

| Region body | Intended tool class |
| --- | --- |
| `micro_detail_zone.stl` | `0.2` |
| `normal_visible_detail_zone.stl` | `0.4` |
| `structural_shell_zone.stl` | `0.6` |
| `bulk_zone.stl` | `0.8` |

Scratch workspace:

`outputs/amp_orca_official_mixed_nozzle_baseline/`

The scratch workspace is ignored output and is not committed.

## Upstream Orca Baseline Result

Executable:

`C:\Users\d\tools\OrcaSlicer\V2.4.1_portable_full\orca-slicer.exe`

Official sample profiles inspected:

- `resources/profiles/Custom/machine/MyToolChanger.json`
- `resources/profiles/Custom/machine/MyToolChanger 0.4 nozzle.json`
- `resources/profiles/Custom/process/0.20mm Standard @MyToolChanger.json`
- `resources/profiles/Custom/filament/Generic PLA @MyToolChanger.json`

Finding:

The upstream portable install includes official `MyToolChanger` sample profiles. The machine-model profile advertises nozzle options `0.4;0.2;0.6;0.8`, while the instantiated `MyToolChanger 0.4 nozzle` profile uses a repeated `0.4` nozzle vector. A scratch copy was created under ignored outputs to represent the official documented manual edit: per-extruder nozzle diameters `0.2`, `0.4`, `0.6`, `0.8`, and `0.8` for the five-slot sample toolchanger profile.

Control result:

| Probe | Result |
| --- | --- |
| Upstream `MyToolChanger 0.4` single-object control | export succeeded |
| Output | `outputs/amp_orca_official_mixed_nozzle_baseline/upstream_orca/direct_bulk_official_0p4_scratch_process_g92_compat/plate_1.gcode` |

The control required adding `G92 E0` to scratch layer g-code because the CLI reported:

```text
Relative extruder addressing requires resetting the extruder position at each layer to prevent loss of floating point accuracy. Add "G92 E0" to layer_gcode.
```

Mixed scratch result:

| Probe | Result |
| --- | --- |
| Upstream direct single-object with scratch mixed-nozzle machine | exit `-17`, no G-code |
| Upstream four-region assemble-list with scratch mixed-nozzle machine | exit `-17`, no G-code |
| Shared layer-height retry at `0.08` mm | exit `-17`, no G-code |

The portable CLI path did not print a detailed error for the mixed scratch machine beyond:

```text
Slic3r::CLI::run found error, exit
```

Interpretation:

The installed upstream Orca baseline proves the shipped toolchanger control can export G-code through CLI, but this probe did not successfully reproduce the official mixed-nozzle workflow through CLI scratch settings. The official documented workflow may require GUI/project setup, project-preset registration, painting/Filament-for-Features assignment, or additional metadata not carried by this CLI probe.

## Upstream Orca GUI Mixed-Nozzle Result

Date:

`2026-07-09`

Executable:

`C:\Users\d\tools\OrcaSlicer\V2.4.1_portable_full\orca-slicer.exe`

Local GUI probe workspace:

`C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\`

Local exported G-code:

`C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\gcode\official_orca_mixed_probe_0p12.gcode`

Local preview screenshot:

`C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\orca_exported_sliced_preview.png`

Setup:

- registered a local upstream Orca custom toolchanger printer preset for the probe
- configured tool nozzle diameters as `0.2`, `0.4`, `0.6`, `0.8`, plus one unused fifth sample-toolchanger slot
- registered a local `0.12mm Mixed Probe @AMP Mixed ToolChanger` process preset
- used percentage-based line widths to avoid the shared-process absolute-width failure
- disabled the prime tower for this representation probe
- imported four region-body STL files as separate objects
- assigned object/tool slots:
  - `micro_detail_zone.stl` -> tool slot `1` / emitted `T0`
  - `normal_visible_detail_zone.stl` -> tool slot `2` / emitted `T1`
  - `structural_shell_zone.stl` -> tool slot `3` / emitted `T2`
  - `bulk_zone.stl` -> tool slot `4` / emitted `T3`

Result:

| Probe | Result |
| --- | --- |
| Official Orca GUI four-object mixed-tool plate | export succeeded |
| Process | `0.12mm Mixed Probe @AMP Mixed ToolChanger` |
| Printer | `AMP Mixed ToolChanger 0.2-0.4-0.6-0.8` |
| Estimated total time | `36m13s` |
| Total filament | `15.38g` |
| Tool changes reported by preview | `77` |
| Filament change times reported by preview | `0` |

G-code evidence:

```text
; nozzle_diameter = 0.2,0.4,0.6,0.8,0.8
; print_settings_id = 0.12mm Mixed Probe @AMP Mixed ToolChanger
; printer_settings_id = AMP Mixed ToolChanger 0.2-0.4-0.6-0.8
```

Tool-command counts in the exported G-code:

| Tool command | Count |
| --- | ---: |
| `T0` | 16 |
| `T1` | 27 |
| `T2` | 18 |
| `T3` | 18 |

Preview caveat:

The GUI reported a floating-region/support warning for `normal_visible_detail_zone.stl`. The warning did not block slicing or export, but it means this particular model remains a representation/probe artifact, not a print-ready physical validation model.

Interpretation:

The official upstream Orca GUI workflow can preserve multiple nozzle diameters in exported G-code and can emit real multi-tool `T0`/`T1`/`T2`/`T3` commands from separate object/tool assignments. This corrects the earlier CLI-only result: the CLI scratch-profile failure is not evidence that official Orca mixed-nozzle output is unavailable. It is evidence that the CLI scratch-profile path was incomplete for the official GUI workflow.

This remains an upstream Orca GUI representation baseline. It does not validate Snapmaker U1 execution, physical mixed-nozzle printing, or touchscreen-compatible mixed-nozzle behavior.

## Snapmaker Orca Baseline Result

Executable:

`B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe`

Control result:

| Probe | Result |
| --- | --- |
| Snapmaker U1 `0.4` single-object control | export succeeded |
| Output | `outputs/amp_orca_official_mixed_nozzle_baseline/snapmaker_orca/snapmaker_control_u1_0p4_bulk/plate_1.gcode` |

Mixed scratch result:

| Probe | Result |
| --- | --- |
| Snapmaker direct single-object with upstream-style scratch mixed machine | exit `-17`, no G-code |
| Snapmaker four-region assemble-list with upstream-style scratch mixed machine | exit `-17`, no G-code |

Interpretation:

Snapmaker Orca CLI remains able to export normal U1 single-nozzle G-code, but this probe did not show that Snapmaker Orca V2.3.4 can consume the official upstream-style mixed toolchanger scratch profile through CLI. This is consistent with prior Snapmaker-specific constraints: U1 touchscreen-compatible mixed physical nozzle execution remains blocked, and Fluidd-only experimentation remains future and hardware-dependent.

## G-code Findings

Inspector command:

```text
python tools/amp_inspect_mixed_nozzle_gcode.py outputs/amp_orca_official_mixed_nozzle_baseline --out outputs/amp_orca_official_mixed_nozzle_baseline/reports
```

Exported G-code found:

| Output | Nozzle values | Tool commands | Mixed-nozzle evidence |
| --- | --- | --- | --- |
| Upstream `MyToolChanger 0.4` control | `0.4` | `0` | no |
| Upstream official GUI mixed-tool probe | `0.2,0.4,0.6,0.8,0.8` | `T0`, `T1`, `T2`, `T3` | yes, representation baseline |
| Snapmaker U1 `0.4` control | `0.4` | `2` startup/tool-prep commands | no |

The Snapmaker control includes tool commands in start/tool-prep code, but extrusion moves were assigned to one tool only. The inspector was tightened so tool-prep `T` commands alone are not counted as mixed-nozzle evidence.

Real mixed-nozzle G-code observed:

Yes, through the upstream Orca GUI/project workflow.

The earlier CLI scratch-profile probe did not produce mixed-nozzle output. The later upstream Orca GUI probe did produce G-code containing multiple nozzle diameter values and real `T0`/`T1`/`T2`/`T3` tool commands.

## 3MF / Project Findings

No 3MF/project save-reopen persistence result was produced in this pass.

Reason:

The GUI probe focused on object/tool assignment, slicing, and G-code export. It did not yet save and reopen a 3MF/project file to validate persistence.

Future baseline work should use GUI/project setup explicitly and then inspect saved 3MF/project contents and exported G-code.

## Shared Layer-Height Limitation

OrcaSlicer discussion #10175 identifies shared layer height as an active limitation for multi-nozzle, toolchanger, and IDEX workflows:

<https://github.com/OrcaSlicer/OrcaSlicer/discussions/10175>

This probe attempted a shared `0.20` mm layer-height process and a lower shared `0.08` mm retry for a mixed `0.2` / `0.4` / `0.6` / `0.8` scratch machine. Both mixed attempts failed before G-code export through CLI.

Result:

- Independent per-tool layer height was not observed.
- Shared layer-height behavior remains a key baseline limitation to test through GUI/project setup.
- This reinforces AMP's long-view target: plan XY width and Z height together rather than treating mixed nozzle size alone as full multi-resolution planning.

## Comparison To LixNix

| Capability | Official Orca baseline probe | LixNix runtime probe |
| --- | --- | --- |
| Documented mixed-nozzle support | yes, official wiki | external fork/prior art |
| CLI control export | yes, single-nozzle toolchanger control | yes |
| CLI mixed-nozzle G-code observed | no | not proven; no observed `T0`/`T1`/`T2`/`T3` tool-change output in tested paths |
| GUI mixed-nozzle G-code observed | yes | not tested |
| Mixed width/layer behavior observed | no mixed output in this probe | yes, under scratch mixed-extruder configs |
| Per-extruder layer height | not observed | source-level implementation appears present |
| GUI/project workflow tested | no | no |
| Physical validation | no | no |

LixNix remains useful deeper experimental prior art, especially for per-extruder layer-height and slicer-internal behavior. Official Orca remains the primary manual/static mixed-nozzle baseline.

## Comparison To AMP

| Capability | Upstream Orca official workflow | Snapmaker Orca V2.3.4 | LixNix branch | AMP current offline planner |
| --- | --- | --- | --- | --- |
| Per-extruder nozzle diameter | documented; GUI mixed-tool probe exported `0.2,0.4,0.6,0.8,0.8` | not exported through this CLI probe | source-level support | tool matrix and packet metadata |
| Percentage-based line width support | documented and present in official profiles | not proven for mixed U1 output | source-level behavior observed indirectly | planned/recommended in packets |
| Filament for Features assignment | documented; not exercised in CLI | not exercised | manual/per-feature infrastructure likely | automated region assignment offline |
| Object/painting route | object/tool assignment exercised in GUI | not exercised | likely relies on manual assignment | region bodies and packet mapping |
| Per-tool layer height | known gap / feature request | not observed | source-level implementation appears present | planned through local-Z/resolution demand |
| 3MF save/reopen preservation | not tested | not tested | not tested | sidecar bundle exists |
| G-code multiple nozzle representation | observed in upstream GUI probe | not observed | not proven | no production G-code output |
| T command emission | observed as `T0`/`T1`/`T2`/`T3` in upstream GUI probe | startup/tool-prep only in control | not proven in tested paths | no production G-code output |
| Automated geometry-driven assignment | no | no | not identified | yes, offline |
| Cost gating | no | no | not identified | yes, offline |
| Fallback/confidence reasoning | no | no | not identified | yes |
| Sidecar/debug artifact | no | no | no | yes |
| Hardware preflight gate | no U1-specific gate | Snapmaker validation exists but mixed path blocked | no U1-specific gate | adapter/preflight design exists |

## Decision

Official Orca mixed nozzle-size support exists and is now the primary manual/static baseline. AMP should not claim Orca lacks mixed-nozzle support.

The initial CLI probe did not produce real mixed-nozzle G-code from the official workflow, but the follow-up GUI probe did. Together they prove:

- upstream Orca's toolchanger control can export G-code through CLI after satisfying the `G92 E0` layer-gcode requirement
- upstream Orca's GUI workflow can export a four-object mixed-tool G-code representation containing `0.2`, `0.4`, `0.6`, and `0.8` nozzle values and `T0`/`T1`/`T2`/`T3` commands
- Snapmaker Orca can export normal U1 `0.4` control G-code
- the CLI scratch mixed-machine representation used here is insufficient or incomplete
- no physical or touchscreen-compatible mixed-nozzle behavior is validated

Next recommended action:

Save/reopen the official Orca GUI mixed-tool project as 3MF and inspect whether tool/nozzle assignments persist. Treat CLI scratch-profile failure as a representation limitation, not proof that the official GUI workflow does not work.

## Required Non-Claims

This result does not:

- implement AMP mixed-nozzle slicing
- validate physical mixed-nozzle behavior
- prove touchscreen-compatible mixed-nozzle execution
- bypass Snapmaker validation
- replace official Orca manual workflow
- prove independent per-tool layer height
- prove print strength, surface quality, bonding, or dimensional accuracy
