# AMP Stage 1 Profile-Only Run 001 Results

## Run Metadata

- Date/time updated: 2026-07-01 11:01 -04:00
- Git branch used for local run: `u1-adaptive-nozzle-strategy-cli-benchmark`
- Current branch head during run: `a0f6db925`
- CLI fixes included in local benchmark branch:
  - `afc59c6b8 fix: harden CLI assemble-list plate loading`
  - `fd26642c9 fix: guard CLI FDM normalization without nozzle diameter`
  - `a0f6db925 fix: avoid GUI filament state in CLI extruder expansion`
- Benchmark type: profile-only slicing comparison
- Target slicer: patched local Snapmaker Orca fork
- Executable used locally: `B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe`
- Built DLL used locally: `B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\Snapmaker_Orca.dll`
- CLI log version string: `Current Snapmaker_Orca Version 01.10.01.50`
- Stock profile used for slicing: `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`
- Experimental profile: `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`
- Metrics output: `outputs/amp_run_001/reports/metrics.csv`
- Command ledger: `outputs/amp_run_001/reports/run_001_cli_commands.json`

This benchmark compares profile-only slicing behavior. Same-plate comparison is for visual inspection. Separate stock-only and experimental-only G-code exports are used for metrics.

Preview/G-code does not prove print strength. Preview/G-code does not prove surface quality. This does not validate physical mixed-nozzle behavior. Estimated print time is slicer/G-code-derived unless confirmed on real hardware.

## CLI Hardening Context

Run 001 used a local CLI-hardened Snapmaker Orca build. The exact stock U1 process profile no longer required a CLI-safe copy in that local branch.

The CLI hardening fixes are being contributed separately to Snapmaker Orca and tracked in `docs/dev/Snapmaker_CLI_Hardening_PR_Tracker.md`. These CLI fixes do not change AMP planner behavior.

## Patched CLI State

The local benchmark branch includes three Snapmaker CLI hardening fixes:

```text
afc59c6b8 fix: harden CLI assemble-list plate loading
fd26642c9 fix: guard CLI FDM normalization without nozzle diameter
a0f6db925 fix: avoid GUI filament state in CLI extruder expansion
```

Focused controls with the patched CLI:

| Control | Result | Output |
| --- | --- | --- |
| Single-object assemble-list control | exit `0` | `outputs/bdrive_smoke/single_exact_stock_console_fixed/plate_1.gcode` |
| Two-object same-plate assemble-list control | exit `0` | `outputs/bdrive_smoke/same_plate_exact_stock_console_fixed/plate_1.gcode` |

The exact requested stock process profile now slices successfully in the local benchmark branch:

```text
resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json
single-object assemble-list smoke: exit 0
two-object same-plate assemble-list smoke: exit 0
```

No production profile was changed.

## CLI Method

The run used the patched console wrapper and the patched `Snapmaker_Orca.dll` from the local fork build tree:

```powershell
B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe
B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\Snapmaker_Orca.dll
```

Stock-only exports used:

```powershell
& B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe `
  --debug 3 `
  --slice 0 `
  --outputdir <temporary output directory> `
  --load-settings "resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json;resources\profiles\Snapmaker\process\0.20 Standard @Snapmaker U1 (0.4 nozzle).json" `
  --load-filaments "resources\profiles\Snapmaker\filament\Snapmaker PLA @U1.json" `
  outputs\amp_run_001\models\generated\<model>.stl
```

Experimental-only exports used:

```powershell
& B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe `
  --debug 3 `
  --slice 0 `
  --outputdir <temporary output directory> `
  --load-settings "resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json;docs\experimental_profiles\u1_0.4_adaptive_effective_width.process.json" `
  --load-filaments "resources\profiles\Snapmaker\filament\Snapmaker PLA @U1.json" `
  outputs\amp_run_001\models\generated\<model>.stl
```

Same-plate visual comparison exports used `--load-assemble-list` with a generated assemble-list JSON containing two copies of the same STL. The first object used stock settings. The second object used object-level `print_params`:

```json
{
  "wall_generator": "arachne",
  "outer_wall_line_width": "0.42",
  "top_surface_line_width": "0.42",
  "support_line_width": "0.42",
  "inner_wall_line_width": "0.52",
  "internal_solid_infill_line_width": "0.52",
  "sparse_infill_line_width": "0.58"
}
```

The exact command ledger for this local run is stored in ignored output at:

```text
outputs/amp_run_001/reports/run_001_cli_commands.json
```

## Model List

| Model | Source | Category | Stock-only G-code | Experimental-only G-code | Same-plate visual comparison |
| --- | --- | --- | --- | --- | --- |
| `thin_wall_comb.stl` | generated | Thin-wall detail | generated | generated | generated |
| `large_bracket_box.stl` | generated | Large bracket / box | generated | generated | generated |
| `embossed_text_plate.stl` | generated | Embossed/debossed text surrogate | generated | generated | generated |
| `speaker_adapter_ring.stl` | generated | Speaker adapter ring | generated | generated | generated |
| `led_ring_face.stl` | generated | LED speaker ring face | generated | generated | generated |
| `sloped_surface_torture.stl` | generated | Sloped surface torture | generated | generated | generated |

## Stock-Only vs Experimental-Only Metrics

These are G-code inspection metrics from separate stock-only and experimental-only exports. Same-plate comparison G-code is intentionally not mixed into this table.

| Model | Stock size | Experimental size | Size delta | Stock travel moves | Experimental travel moves | Travel delta | Stock positive E | Experimental positive E | E delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `thin_wall_comb` | 453055 | 413706 | -8.7% | 8810 | 7897 | -10.4% | 2494.658 | 2441.427 | -2.1% |
| `large_bracket_box` | 4068626 | 3145045 | -22.7% | 116507 | 86304 | -25.9% | 10712.675 | 10379.266 | -3.1% |
| `embossed_text_plate` | 418982 | 355893 | -15.1% | 9971 | 7933 | -20.4% | 756.248 | 775.374 | +2.5% |
| `speaker_adapter_ring` | 2219130 | 1831985 | -17.4% | 70204 | 57698 | -17.8% | 1996.022 | 1439.444 | -27.9% |
| `led_ring_face` | 586917 | 552100 | -5.9% | 16022 | 15308 | -4.5% | 1274.228 | 981.306 | -23.0% |
| `sloped_surface_torture` | 1714217 | 1250860 | -27.0% | 45577 | 30473 | -33.1% | 2519.849 | 2343.980 | -7.0% |

The metrics parser found no estimated print-time or filament-usage comments in the parsed Snapmaker G-code format. File size, movement counts, and parsed positive E totals are G-code inspection metrics only.

## Same-Plate Visual Comparison Status

Same-plate comparison is for visual inspection in a G-code viewer. It is not the source for stock-vs-experimental metrics.

| Model | Same-plate result | Output |
| --- | --- | --- |
| `thin_wall_comb` | generated | `outputs/amp_run_001/gcode/thin_wall_comb/same_plate_stock_vs_experimental.gcode` |
| `large_bracket_box` | generated | `outputs/amp_run_001/gcode/large_bracket_box/same_plate_stock_vs_experimental.gcode` |
| `embossed_text_plate` | generated | `outputs/amp_run_001/gcode/embossed_text_plate/same_plate_stock_vs_experimental.gcode` |
| `speaker_adapter_ring` | generated | `outputs/amp_run_001/gcode/speaker_adapter_ring/same_plate_stock_vs_experimental.gcode` |
| `led_ring_face` | generated | `outputs/amp_run_001/gcode/led_ring_face/same_plate_stock_vs_experimental.gcode` |
| `sloped_surface_torture` | generated | `outputs/amp_run_001/gcode/sloped_surface_torture/same_plate_stock_vs_experimental.gcode` |

All six same-plate exports generated successfully in this local run. Same-plate G-code remains a visual inspection artifact, not the source for stock-vs-experimental metrics.

## Initial Same-Plate Visual Review

An initial local preview-image review was performed from the same-plate G-code files. The review generated role-colored path preview sheets for sampled layers and stored them locally under:

```text
outputs/amp_run_001/visual_review/
```

Those preview sheets are local review artifacts and are not committed.

Visual review is preview-only. Preview does not prove surface quality. Preview does not prove strength. Preview does not validate mixed physical nozzle behavior.

| Model | Layers inspected | Initial review status | Notes |
| --- | --- | --- | --- |
| `thin_wall_comb` | 1 / 31 / 60 | acceptable for viewer confirmation | Thin comb features remain visible in sampled layers. |
| `large_bracket_box` | 1 / 101 / 200 | acceptable for viewer confirmation | Exterior loops remain visible; internal/sparse paths differ as expected. |
| `embossed_text_plate` | 1 / 11 / 21 | caution | Text surrogate paths remain present, but the parsed positive E increase still needs viewer confirmation. |
| `speaker_adapter_ring` | 1 / 26 / 50 | acceptable for viewer confirmation | Inner and outer ring loops remain visible in sampled layers. |
| `led_ring_face` | 1 / 10 / 18 | caution for cosmetic review | Ring body and small top/detail marks remain visible in sampled layers. |
| `sloped_surface_torture` | 1 / 36 / 70 | caution for slope review | Stepped/sloped features remain visible, but topmost sampled layer was not useful for cosmetic slope judgment. |

No obvious missing exterior loop or vanished feature was visible in the sampled preview sheets. Snapmaker Orca or Prusa G-code Viewer confirmation is still recommended before changing Run 002 settings.

## Upstream Orca CLI Probe

The earlier upstream Orca V2.4.1 same-plate result remains an upstream Orca CLI automation probe, not official Snapmaker Orca target validation.

That probe is useful evidence that the general Orca CLI assemble-list workflow can support same-plate comparison, but its metrics are not mixed into the official Snapmaker Run 001 table above.

## Observations

- The patched Snapmaker Orca CLI can slice all six generated Run 001 models as stock-only and experimental-only G-code.
- The patched Snapmaker Orca CLI can run the single-object assemble-list control.
- The patched Snapmaker Orca CLI can run the two-object same-plate assemble-list control.
- All six generated models produced real Snapmaker same-plate visual comparison G-code.
- Experimental effective-width settings change generated G-code metrics across all six models.
- The largest file-size and travel-move reductions in this pass appear on `sloped_surface_torture` and `large_bracket_box`.
- `embossed_text_plate` shows lower file size and travel moves but higher parsed positive E, which should be inspected visually before drawing conclusions.

## Failures / Blockers

- The exact stock U1 process profile requires the local normalize_fdm CLI guard fix until Snapmaker PR #561 or equivalent is merged upstream.
- Full same-plate coverage requires the local CLI extruder-expansion guard until the corresponding fix is merged upstream.
- The metrics parser still does not extract Snapmaker estimated print time or filament usage from the current G-code comments.
- Layer count remains unavailable from the current parser for these Snapmaker G-code files.

## What Can Be Concluded

- The patched Snapmaker Orca CLI is now usable for Run 001 profile-only benchmark automation.
- The profile-only stock-vs-experimental comparison can be generated for the six synthetic benchmark models.
- Same-plate visual comparison is now usable for all six generated models in the local CLI-hardened benchmark branch.
- The experimental effective-width/Arachne setup produces measurable G-code differences in file size, travel moves, and parsed positive E totals.

## What Cannot Be Concluded

This run cannot claim:

- print-time improvement;
- filament reduction;
- print strength improvement;
- surface quality improvement;
- dimensional accuracy improvement;
- bonding improvement;
- physical mixed-nozzle behavior;
- U1 toolhead, purge, wipe, calibration, or nozzle-state behavior.

Those claims require real hardware validation. Physical mixed-nozzle behavior remains a separate Stage 2 question.
