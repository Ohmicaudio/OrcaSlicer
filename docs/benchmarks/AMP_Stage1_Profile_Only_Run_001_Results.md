# AMP Stage 1 Profile-Only Run 001 Results

## Run Metadata

- Date/time updated: 2026-07-01 05:21 -04:00
- Git branch: `u1-adaptive-nozzle-strategy`
- Current branch head during run: `71faf4261`
- CLI fix included in branch: `afc59c6b8 fix: harden CLI assemble-list plate loading`
- Benchmark type: profile-only slicing comparison
- Target slicer: patched local Snapmaker Orca fork
- Executable used locally: `B:\ohmic\Snapmaker-OrcaSlicer\build\src\Release\snapmaker-orca-console.exe`
- Built DLL used locally: `B:\ohmic\Snapmaker-OrcaSlicer\build\src\Release\Snapmaker_Orca.dll`
- CLI log version string: `Current Snapmaker_Orca Version 01.10.01.50`
- Requested stock profile: `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`
- CLI-safe stock profile used for slicing: `outputs/amp_run_001/tmp_profiles/stock_cli_safe_0.20_standard_u1_0.4.process.json`
- Experimental profile: `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`
- Metrics output: `outputs/amp_run_001/reports/metrics.csv`
- Command ledger: `outputs/amp_run_001/reports/run_001_cli_commands.json`

This benchmark compares profile-only slicing behavior. Same-plate comparison is for visual inspection. Separate stock-only and experimental-only G-code exports are used for metrics.

Preview/G-code does not prove print strength. Preview/G-code does not prove surface quality. This does not validate physical mixed-nozzle behavior. Estimated print time is slicer/G-code-derived unless confirmed on real hardware.

## Patched CLI State

The AMP branch includes the Snapmaker CLI assemble-list fix:

```text
afc59c6b8 fix: harden CLI assemble-list plate loading
```

Focused controls with the patched CLI:

| Control | Result | Output |
| --- | --- | --- |
| Single-object assemble-list control | exit `0` | `outputs/amp_run_001/cli_controls/single_control.gcode` |
| Two-object same-plate assemble-list control | exit `0` | `outputs/amp_run_001/cli_controls/same_plate_control.gcode` |

The exact requested stock process profile still crashes in the CLI before slicing:

```text
resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json
exit code: -1073741819
```

The local CLI-safe stock profile used for this run is a copy of the requested stock profile with only this key omitted:

```json
"wipe_tower_filament": "0"
```

No production profile was changed.

## CLI Method

The run used the patched console wrapper and the patched `Snapmaker_Orca.dll` from the local fork build tree:

```powershell
B:\ohmic\Snapmaker-OrcaSlicer\build\src\Release\snapmaker-orca-console.exe
B:\ohmic\Snapmaker-OrcaSlicer\build\src\Release\Snapmaker_Orca.dll
```

Stock-only exports used:

```powershell
& B:\ohmic\Snapmaker-OrcaSlicer\build\src\Release\snapmaker-orca-console.exe `
  --debug 3 `
  --slice 0 `
  --outputdir <temporary output directory> `
  --load-settings "resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json;outputs\amp_run_001\tmp_profiles\stock_cli_safe_0.20_standard_u1_0.4.process.json" `
  --load-filaments "resources\profiles\Snapmaker\filament\Snapmaker PLA @U1.json" `
  outputs\amp_run_001\models\generated\<model>.stl
```

Experimental-only exports used:

```powershell
& B:\ohmic\Snapmaker-OrcaSlicer\build\src\Release\snapmaker-orca-console.exe `
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
| `speaker_adapter_ring.stl` | generated | Speaker adapter ring | generated | generated | blocked by same-plate CLI crash |
| `led_ring_face.stl` | generated | LED speaker ring face | generated | generated | blocked by same-plate CLI crash |
| `sloped_surface_torture.stl` | generated | Sloped surface torture | generated | generated | generated |

## Stock-Only vs Experimental-Only Metrics

These are G-code inspection metrics from separate stock-only and experimental-only exports. Same-plate comparison G-code is intentionally not mixed into this table.

| Model | Stock size | Experimental size | Size delta | Stock travel moves | Experimental travel moves | Travel delta | Stock positive E | Experimental positive E | E delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `thin_wall_comb` | 451015 | 414906 | -8.0% | 8810 | 7897 | -10.4% | 2494.658 | 2441.427 | -2.1% |
| `large_bracket_box` | 4064626 | 3137845 | -22.8% | 116507 | 86304 | -25.9% | 10712.675 | 10379.266 | -3.1% |
| `embossed_text_plate` | 419654 | 355137 | -15.4% | 9971 | 7933 | -20.4% | 756.248 | 775.374 | +2.5% |
| `speaker_adapter_ring` | 2219230 | 1830885 | -17.5% | 70204 | 57698 | -17.8% | 1996.022 | 1439.444 | -27.9% |
| `led_ring_face` | 587277 | 552028 | -6.0% | 16022 | 15308 | -4.5% | 1274.228 | 981.306 | -23.0% |
| `sloped_surface_torture` | 1715337 | 1250720 | -27.1% | 45577 | 30473 | -33.1% | 2519.849 | 2343.980 | -7.0% |

The metrics parser found no estimated print-time or filament-usage comments in the parsed Snapmaker G-code format. File size, movement counts, and parsed positive E totals are G-code inspection metrics only.

## Same-Plate Visual Comparison Status

Same-plate comparison is for visual inspection in a G-code viewer. It is not the source for stock-vs-experimental metrics.

| Model | Same-plate result | Output |
| --- | --- | --- |
| `thin_wall_comb` | generated | `outputs/amp_run_001/gcode/thin_wall_comb/same_plate_stock_vs_experimental.gcode` |
| `large_bracket_box` | generated | `outputs/amp_run_001/gcode/large_bracket_box/same_plate_stock_vs_experimental.gcode` |
| `embossed_text_plate` | generated | `outputs/amp_run_001/gcode/embossed_text_plate/same_plate_stock_vs_experimental.gcode` |
| `speaker_adapter_ring` | blocked by CLI access-violation exit `3221225477` / `0xC0000005` | not generated |
| `led_ring_face` | blocked by CLI access-violation exit `3221225477` / `0xC0000005` | not generated |
| `sloped_surface_torture` | generated | `outputs/amp_run_001/gcode/sloped_surface_torture/same_plate_stock_vs_experimental.gcode` |

The two same-plate failures happen after assemble-list loading begins and after the model bounding box is logged. Their separate stock-only and experimental-only slices both succeed, so this is recorded as a same-plate CLI automation blocker, not as a model/profile slicing failure.

## Upstream Orca CLI Probe

The earlier upstream Orca V2.4.1 same-plate result remains an upstream Orca CLI automation probe, not official Snapmaker Orca target validation.

That probe is useful evidence that the general Orca CLI assemble-list workflow can support same-plate comparison, but its metrics are not mixed into the official Snapmaker Run 001 table above.

## Observations

- The patched Snapmaker Orca CLI can slice all six generated Run 001 models as stock-only and experimental-only G-code.
- The patched Snapmaker Orca CLI can run the single-object assemble-list control.
- The patched Snapmaker Orca CLI can run the two-object same-plate assemble-list control.
- Four of six generated models produced real Snapmaker same-plate visual comparison G-code.
- Two larger/ring-like generated models still hit a same-plate CLI access violation.
- Experimental effective-width settings change generated G-code metrics across all six models.
- The largest file-size and travel-move reductions in this pass appear on `sloped_surface_torture` and `large_bracket_box`.
- `embossed_text_plate` shows lower file size and travel moves but higher parsed positive E, which should be inspected visually before drawing conclusions.

## Failures / Blockers

- Exact stock process profile still crashes in CLI before slicing when loaded as-is.
- Isolated stock-profile trigger remains `wipe_tower_filament`; this run used an ignored CLI-safe stock copy with only that key omitted.
- Same-plate visual comparison still crashes for `speaker_adapter_ring` and `led_ring_face`.
- The metrics parser still does not extract Snapmaker estimated print time or filament usage from the current G-code comments.
- Layer count remains unavailable from the current parser for these Snapmaker G-code files.

## What Can Be Concluded

- The patched Snapmaker Orca CLI is now usable for Run 001 profile-only benchmark automation.
- The profile-only stock-vs-experimental comparison can be generated for the six synthetic benchmark models.
- Same-plate visual comparison is now usable for a subset of generated models.
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
