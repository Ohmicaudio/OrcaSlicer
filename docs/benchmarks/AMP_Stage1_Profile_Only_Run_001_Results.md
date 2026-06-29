# AMP Stage 1 Profile-Only Run 001 Results

## Run Metadata

- Date/time updated: 2026-06-29 16:55 -04:00
- Git branch: `u1-adaptive-nozzle-strategy`
- Benchmark type: profile-only slicing comparison
- Target slicer: Snapmaker Orca V2.3.4 official Windows portable release
- Executable used locally: `C:\Users\d\tools\Snapmaker_Orca\V2.3.4_portable\Snapmaker_Orca_Windows_V2.3.4_portable\snapmaker-orca.exe`
- Windows file version: `2.3.4.0`
- CLI log version string: `Current Snapmaker_Orca Version 01.10.01.50`
- Target baseline profile: `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`
- Experimental profile: `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`

This benchmark compares profile-only slicing behavior. It does not prove print strength. It does not prove surface quality. It does not prove dimensional accuracy. It does not prove physical mixed-nozzle behavior.

Any print-time differences are unavailable in this pass because the current metrics parser did not find Snapmaker print-time comments in the exported G-code. File size, movement counts, and parsed positive E totals are G-code inspection metrics only.

## Current Status

Run 001 now has a provisional Snapmaker Orca CLI slicing pass for seven STL models:

- six generated benchmark models;
- one downloaded public 3DBenchy STL.

The exact requested stock profile could not be loaded by the official Snapmaker Orca V2.3.4 CLI. The CLI repeatedly crashed while loading:

```text
resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json
```

The crash occurred before slicing and returned:

```text
-1073741819
```

A profile-isolation pass found that the official CLI slices successfully when the stock process is copied to an ignored temp file with only this key omitted:

```json
"wipe_tower_filament": "0"
```

No production profile was changed. The provisional stock G-code in `outputs/amp_run_001/gcode/` was generated with that ignored temp profile so that the rest of the benchmark pipeline could run. Treat these results as a provisional CLI-safe stock baseline, not a final exact-stock-profile result.

The experimental effective-width profile loaded and sliced successfully as-is.

## Commands Run

Download and inspect official Snapmaker Orca release metadata:

```powershell
$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/Snapmaker/OrcaSlicer/releases/latest' -Headers @{ 'User-Agent'='Codex-AMP-Benchmark' }
$release | Select-Object tag_name,name,published_at,html_url
$release.assets | Select-Object name,size,browser_download_url
```

Download and extract the official Windows portable asset:

```powershell
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile C:\Users\d\tools\Snapmaker_Orca\downloads\Snapmaker_Orca_Windows_V2.3.4_portable.zip
Expand-Archive -LiteralPath C:\Users\d\tools\Snapmaker_Orca\downloads\Snapmaker_Orca_Windows_V2.3.4_portable.zip -DestinationPath C:\Users\d\tools\Snapmaker_Orca\V2.3.4_portable -Force
```

Confirm executable metadata:

```powershell
(Get-Item 'C:\Users\d\tools\Snapmaker_Orca\V2.3.4_portable\Snapmaker_Orca_Windows_V2.3.4_portable\snapmaker-orca.exe').VersionInfo
```

Probe exact stock profile:

```powershell
& 'C:\Users\d\tools\Snapmaker_Orca\V2.3.4_portable\Snapmaker_Orca_Windows_V2.3.4_portable\snapmaker-orca.exe' `
  --debug 3 `
  --slice 0 `
  --outputdir outputs\amp_run_001\gcode\thin_wall_comb\stock_probe `
  --load-settings "resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json;resources\profiles\Snapmaker\process\0.20 Standard @Snapmaker U1 (0.4 nozzle).json" `
  --load-filaments "resources\profiles\Snapmaker\filament\Snapmaker PLA @U1.json" `
  outputs\amp_run_001\models\generated\thin_wall_comb.stl
```

Result:

```text
CLI crash while loading stock process profile, before G-code export.
Exit code: -1073741819
```

Run provisional profile-only slicing with official Snapmaker Orca CLI:

```powershell
python <local Run 001 slicing harness>
```

The harness used:

```text
--slice 0
--load-settings "<U1 0.4 machine>;<process profile>"
--load-filaments "<Snapmaker PLA @U1>"
```

Canonical G-code outputs:

```text
outputs/amp_run_001/gcode/<model>/stock.gcode
outputs/amp_run_001/gcode/<model>/experimental.gcode
```

Run metrics:

```powershell
python tools\amp_gcode_metrics.py outputs\amp_run_001\gcode
```

Result:

```text
wrote 14 row(s)
```

## Model List

| Model | Source | Category | Stock G-code | Experimental G-code | Status |
| --- | --- | --- | --- | --- | --- |
| `thin_wall_comb.stl` | generated | Thin-wall detail | generated with CLI-safe stock baseline | generated | provisional results available |
| `large_bracket_box.stl` | generated | Large bracket / box | generated with CLI-safe stock baseline | generated | provisional results available |
| `embossed_text_plate.stl` | generated | Embossed/debossed text surrogate | generated with CLI-safe stock baseline | generated | provisional results available |
| `speaker_adapter_ring.stl` | generated | Speaker adapter ring | generated with CLI-safe stock baseline | generated | provisional results available |
| `led_ring_face.stl` | generated | LED speaker ring face | generated with CLI-safe stock baseline | generated | provisional results available |
| `sloped_surface_torture.stl` | generated | Sloped surface torture | generated with CLI-safe stock baseline | generated | provisional results available |
| `3DBenchy.stl` | downloaded public model | General slicer torture model | generated with CLI-safe stock baseline | generated | provisional results available |
| `Floating+Island.3mf` | user-provided local model | Multi-color / multi-region Bambu 3MF | not generated | not generated | future local candidate only |

`Floating+Island.3mf` was not used in this profile-only pass. It is a Bambu-origin multi-color 3MF with a large mesh payload and must not be treated as a U1-native project or as mixed physical nozzle validation.

## Stock vs Experimental Metrics

These are G-code inspection metrics from `outputs/amp_run_001/reports/metrics.csv`.

| Model | Stock size | Experimental size | Size delta | Stock travel moves | Experimental travel moves | Travel delta | Stock positive E | Experimental positive E | E delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `3DBenchy` | 4133668 | 3688820 | -10.8% | 104264 | 91478 | -12.3% | 3248.689 | 3141.970 | -3.3% |
| `embossed_text_plate` | 411551 | 350821 | -14.8% | 9819 | 7841 | -20.1% | 691.328 | 759.192 | +9.8% |
| `large_bracket_box` | 4063554 | 3137243 | -22.8% | 116510 | 86306 | -25.9% | 10706.668 | 10376.233 | -3.1% |
| `led_ring_face` | 586366 | 551443 | -6.0% | 16022 | 15308 | -4.5% | 1274.228 | 981.306 | -23.0% |
| `sloped_surface_torture` | 1713913 | 1250035 | -27.1% | 45583 | 30470 | -33.2% | 2528.247 | 2343.591 | -7.3% |
| `speaker_adapter_ring` | 2218373 | 1829852 | -17.5% | 70207 | 57686 | -17.8% | 1984.638 | 1435.723 | -27.7% |
| `thin_wall_comb` | 450346 | 413147 | -8.3% | 8810 | 7895 | -10.4% | 2494.658 | 2446.591 | -1.9% |

## Observations

- The official Snapmaker Orca V2.3.4 CLI can slice U1 0.4 models using U1 machine, process, and filament profiles.
- The target stock profile currently exposes a CLI crash when loaded with `wipe_tower_filament`.
- Removing only `wipe_tower_filament` in an ignored temp copy allowed a provisional stock baseline to be generated.
- The experimental effective-width profile loaded without modification and generated G-code.
- All generated STL benchmark models and 3DBenchy produced both provisional stock and experimental G-code.
- The metrics parser found 14 canonical G-code files.
- Snapmaker exported G-code did not include estimated print-time or filament-usage comments in the formats currently parsed by `tools/amp_gcode_metrics.py`.
- The metrics parser did not count layers from the current Snapmaker G-code comments, so layer count remains unavailable in this pass.

## Failures / Blockers

Primary exact-stock blocker:

- Official Snapmaker Orca V2.3.4 CLI crashes while loading the requested exact stock process profile before slicing.
- Isolated trigger: `wipe_tower_filament` in `0.20 Standard @Snapmaker U1 (0.4 nozzle).json`.
- Workaround used for provisional G-code: ignored temp stock process profile with only `wipe_tower_filament` omitted.

Open follow-up:

- Verify whether the Snapmaker Orca GUI can load and export the exact stock profile without the CLI crash.
- If GUI exact-stock export works, rerun Run 001 with exact `stock.gcode` files and replace the provisional metrics.
- Update `tools/amp_gcode_metrics.py` later if Snapmaker G-code exposes layer, time, or filament metadata under different comment formats.

## What Can Be Concluded

- The Run 001 benchmark workspace, generated models, model manifest, and G-code metrics tooling are usable with official Snapmaker Orca output.
- The experimental effective-width profile is importable by the official Snapmaker Orca V2.3.4 CLI.
- A provisional stock-vs-experimental G-code comparison exists for seven STL models.
- The provisional experimental outputs differ from the provisional stock baseline in file size, travel-move count, and parsed positive E totals.

## What Cannot Be Concluded

This run cannot claim:

- final exact-stock-profile parity, because the exact stock profile hit a CLI crash;
- print-time improvement;
- filament reduction;
- strength improvement;
- surface quality improvement;
- dimensional accuracy improvement;
- bonding improvement;
- mixed physical nozzle behavior;
- U1 toolhead, purge, wipe, calibration, or nozzle-state behavior.

Those claims require exact-stock slicing where applicable and, for physical outcomes, measured hardware validation.
