# AMP Stage 1 Profile-Only Run 001 Results

## Run Metadata

- Date/time prepared: 2026-06-29 16:01:39 -04:00
- Git branch: `u1-adaptive-nozzle-strategy`
- Source commit at preparation time: `51f9527`
- Benchmark type: profile-only slicing comparison
- Baseline profile: `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`
- Experimental profile: `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`

This benchmark compares profile-only slicing behavior. It does not prove print strength. It does not prove surface quality. It does not prove physical mixed-nozzle behavior.

Any print-time differences are slicer estimates or G-code-derived estimates only unless real U1 hardware is used.

## Current Status

Run 001 model preparation and benchmark tooling were completed locally.

The actual stock-vs-experimental slicing pass is blocked because no local Snapmaker Orca or OrcaSlicer executable was found in the repository or installed application search paths during this run.

The only local slicer-like executable discovered was:

```text
C:\Program Files\AnycubicSlicerNext\AnycubicSlicerNext.exe
```

It reports:

```text
AnycubicSlicerNext-1.4.1.2:
Usage: AnycubicSlicerNext [ OPTIONS ] [ file.3mf/file.stl ... ]
```

That executable was not used for Run 001 because this benchmark requires Snapmaker Orca / OrcaSlicer behavior with the Snapmaker U1 stock profile and the AMP experimental effective-width profile.

## Commands Run

Create output workspace:

```powershell
New-Item -ItemType Directory -Force -Path outputs\amp_run_001\models\generated,outputs\amp_run_001\models\downloaded,outputs\amp_run_001\gcode,outputs\amp_run_001\reports
```

Generate synthetic models:

```powershell
python tools\amp_generate_benchmark_models.py
```

Download public 3DBenchy model:

```powershell
$url='https://raw.githubusercontent.com/CreativeTools/3DBenchy/master/Single-part/3DBenchy.stl'
$out='outputs/amp_run_001/models/downloaded/3DBenchy.stl'
Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
```

Inspect local executable options:

```powershell
& 'C:\Program Files\AnycubicSlicerNext\AnycubicSlicerNext.exe' --help
```

Search for local Snapmaker/Orca slicer executables:

```powershell
Get-ChildItem -Path . -Recurse -File -Include *.exe
Get-Command OrcaSlicer,orca-slicer,Snapmaker_Orca,Snapmaker-Orca,prusa-slicer -ErrorAction SilentlyContinue
Get-ChildItem -Path C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work -Recurse -File -Include '*Orca*.exe','*Slicer*.exe','*Snapmaker*.exe'
```

Run G-code metrics tooling against the empty G-code output directory:

```powershell
python tools\amp_gcode_metrics.py outputs\amp_run_001\gcode
```

Result:

```text
wrote 0 row(s)
```

## Model List

| Model | Source | Category | Stock G-code | Experimental G-code | Status |
| --- | --- | --- | --- | --- | --- |
| `thin_wall_comb.stl` | generated | Thin-wall detail | not generated | not generated | slicing blocked |
| `large_bracket_box.stl` | generated | Large bracket / box | not generated | not generated | slicing blocked |
| `embossed_text_plate.stl` | generated | Embossed/debossed text surrogate | not generated | not generated | slicing blocked |
| `speaker_adapter_ring.stl` | generated | Speaker adapter ring | not generated | not generated | slicing blocked |
| `led_ring_face.stl` | generated | LED speaker ring face | not generated | not generated | slicing blocked |
| `sloped_surface_torture.stl` | generated | Sloped surface torture | not generated | not generated | slicing blocked |
| `3DBenchy.stl` | downloaded public model | General slicer torture model | not generated | not generated | slicing blocked |

## Stock vs Experimental Metrics

No stock or experimental G-code was generated during this run because the required slicer executable was not available.

| Model | Stock estimated time | Experimental estimated time | Stock filament | Experimental filament | Stock G-code size | Experimental G-code size | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `thin_wall_comb.stl` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | blocked: no Snapmaker Orca/OrcaSlicer executable |
| `large_bracket_box.stl` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | blocked: no Snapmaker Orca/OrcaSlicer executable |
| `embossed_text_plate.stl` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | blocked: no Snapmaker Orca/OrcaSlicer executable |
| `speaker_adapter_ring.stl` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | blocked: no Snapmaker Orca/OrcaSlicer executable |
| `led_ring_face.stl` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | blocked: no Snapmaker Orca/OrcaSlicer executable |
| `sloped_surface_torture.stl` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | blocked: no Snapmaker Orca/OrcaSlicer executable |
| `3DBenchy.stl` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | blocked: no Snapmaker Orca/OrcaSlicer executable |

## Observations

- Synthetic benchmark STL generation works without external Python dependencies.
- 3DBenchy was downloaded into the ignored output workspace and recorded in the model manifest.
- G-code metrics tooling works on the benchmark output directory and produces empty CSV/summary outputs when no G-code files are present.
- The local repository does not contain a built Snapmaker Orca/OrcaSlicer executable.
- No local `OrcaSlicer`, `orca-slicer`, `Snapmaker_Orca`, `Snapmaker-Orca`, or `prusa-slicer` command was found on `PATH`.
- AnycubicSlicerNext exposes similar command-line concepts such as `--load-settings`, `--outputdir`, and `--slice`, but it is not the target executable for this U1 profile-only benchmark.

## Failures / Blockers

Primary blocker:

- No local Snapmaker Orca or OrcaSlicer executable was available to perform the stock-vs-experimental U1 slicing pass.

Secondary blocker:

- The repository's previous local build notes indicate full Windows configure/test execution remains blocked by missing dependency packages, beginning with Boost `1.83.0`. This task did not modify project source or bypass dependency checks.

## Manual GUI Slicing Checklist

If a Snapmaker Orca GUI build is available before CLI slicing is available:

1. Open each model from `outputs/amp_run_001/models/generated/` and `outputs/amp_run_001/models/downloaded/`.
2. Select the stock Snapmaker U1 0.4 mm process profile.
3. Slice and export G-code to `outputs/amp_run_001/gcode/<model_name>/stock.gcode`.
4. Load or recreate the experimental effective-width profile from `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`.
5. Slice and export G-code to `outputs/amp_run_001/gcode/<model_name>/experimental.gcode`.
6. Run:

```powershell
python tools\amp_gcode_metrics.py outputs\amp_run_001\gcode
```

7. Update this results document with the stock-vs-experimental metrics.

## What Can Be Concluded

- The Run 001 benchmark workspace, synthetic models, model manifest, and G-code metrics tooling are ready.
- The committed tooling is docs/scripts only and does not modify slicer behavior, production profiles, G-code generation, Snapmaker validation, or AMP production integration.
- No stock-vs-experimental slicing conclusions can be drawn yet because no target slicer executable was available.

## What Cannot Be Concluded

This run cannot claim:

- print-time improvement;
- filament reduction;
- strength improvement;
- surface quality improvement;
- dimensional accuracy improvement;
- bonding improvement;
- mixed physical nozzle behavior;
- U1 toolhead, purge, wipe, calibration, or nozzle-state behavior.

Those claims require successful slicing and, for physical outcomes, measured hardware validation.
