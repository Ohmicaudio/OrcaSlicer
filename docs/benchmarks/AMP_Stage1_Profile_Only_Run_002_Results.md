# AMP Stage 1 Profile-Only Run 002 Results

## Purpose

Run 002 compares four profile-only strategies on the focused Run 002 model set:

- Stock
- Width-only
- Layer-height-only
- Combined width plus layer height

This benchmark compares profile-only slicing behavior. It is intended to identify candidate settings for later visual and physical validation, not to prove final print performance.

## Slicer Build and CLI Path

- Date/time updated: 2026-07-02
- Repo branch used for documentation: `u1-adaptive-nozzle-strategy`
- Repo branch head during run: `6d2fd4091`
- Target slicer: local CLI-hardened Snapmaker Orca build
- Executable used locally: `B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe`
- CLI log/header version string: `Snapmaker Orca 2.3.5`
- Metrics output: `outputs/amp_run_002/reports/metrics.csv`
- Command ledger: `outputs/amp_run_002/reports/run_002_cli_commands.json`

The local CLI build includes the Snapmaker CLI hardening fixes used for Run 001. Those fixes are separate from AMP planner behavior and are tracked as standalone Snapmaker Orca PRs.

## CLI Method

Each model was sliced separately for each candidate. The general command form was:

```powershell
& B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe `
  --debug 3 `
  --slice 0 `
  --outputdir <temporary output directory> `
  --load-settings "resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json;<candidate process profile>" `
  --load-filaments "resources\profiles\Snapmaker\filament\Snapmaker PLA @U1.json" `
  outputs\amp_run_001\models\generated\<model>.stl
```

Temporary ignored candidate process profiles were generated under:

```text
outputs/amp_run_002/profiles/
```

No production profile was modified.

## Model List

| Model | Reason |
| --- | --- |
| `thin_wall_comb` | Detail/thin-wall guardrail. |
| `large_bracket_box` | Large internal/bulk candidate. |
| `speaker_adapter_ring` | Functional ring/wall candidate. |
| `led_ring_face` | Cosmetic/top-detail guardrail. |
| `sloped_surface_torture` | Layer-height and visible-slope caution case. |

All five models sliced successfully under all four variants.

## Variant Definitions

| Variant | Definition |
| --- | --- |
| Stock | Stock Snapmaker U1 0.4 process profile. |
| Width-only | Stock-derived temporary profile with Arachne, outer/top/support `0.42`, inner/internal solid `0.52`, sparse infill `0.58`, stock layer height. |
| Layer-height-only | Stock-derived temporary profile with explicit `layer_height = 0.28`, stock-like widths. |
| Combined | Stock-derived temporary profile with the width-only settings plus explicit `layer_height = 0.28`. |

An initial attempt to use the packaged `0.28 Extra Draft @Snapmaker U1 (0.4 nozzle)` profile directly did not change layer count in the local CLI path. Run 002 was rerun with stock-derived temporary profiles containing explicit overrides so that the layer-height candidates were reproducible from the command ledger.

## Metrics Table

Metrics are parsed from generated G-code. Estimated print time is the slicer-derived `M73 R` value from the G-code header/start sequence. Filament usage comments were not present in the parsed Snapmaker G-code.

| Model | Variant | Time | Time delta | Size delta | Layer delta | Extrusion delta | Travel delta | E delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `thin_wall_comb` | `width_only` | 66 min | +1.5% | -5.4% | +0 (+0.0%) | +2.2% | -9.0% | +0.9% |
| `thin_wall_comb` | `layer_height_only` | 61 min | -6.2% | -17.2% | -17 (-28.3%) | -5.9% | -13.8% | -14.5% |
| `thin_wall_comb` | `combined` | 61 min | -6.2% | -23.6% | -17 (-28.3%) | -4.9% | -23.3% | -13.8% |
| `large_bracket_box` | `width_only` | 402 min | +1.0% | -24.1% | +0 (+0.0%) | -12.2% | -26.7% | -8.9% |
| `large_bracket_box` | `layer_height_only` | 386 min | -3.0% | -23.9% | -57 (-28.5%) | -30.3% | -22.2% | -31.8% |
| `large_bracket_box` | `combined` | 398 min | +0.0% | -42.0% | -57 (-28.5%) | -27.7% | -44.5% | -22.2% |
| `speaker_adapter_ring` | `width_only` | 151 min | +0.0% | -14.6% | +0 (+0.0%) | -4.0% | -16.1% | -3.8% |
| `speaker_adapter_ring` | `layer_height_only` | 157 min | +4.0% | -16.9% | -14 (-28.0%) | -6.6% | -17.7% | -21.4% |
| `speaker_adapter_ring` | `combined` | 158 min | +4.6% | -34.3% | -14 (-28.0%) | +11.0% | -37.4% | -21.6% |
| `led_ring_face` | `width_only` | 58 min | +0.0% | -0.8% | +0 (+0.0%) | +9.1% | -0.6% | -3.8% |
| `led_ring_face` | `layer_height_only` | 64 min | +10.3% | -17.5% | -5 (-27.8%) | -0.6% | -18.4% | -26.0% |
| `led_ring_face` | `combined` | 64 min | +10.3% | -21.8% | -5 (-27.8%) | +0.7% | -23.6% | -26.7% |
| `sloped_surface_torture` | `width_only` | 152 min | -5.6% | -27.0% | +0 (+0.0%) | -3.7% | -33.3% | -8.9% |
| `sloped_surface_torture` | `layer_height_only` | 164 min | +1.9% | -15.0% | -20 (-28.6%) | -12.9% | -13.5% | -25.4% |
| `sloped_surface_torture` | `combined` | 166 min | +3.1% | -33.7% | -20 (-28.6%) | -9.3% | -37.9% | -17.1% |

## Stock vs Width-Only Observations

Width-only produced clear file-size and travel-move reductions on internal/bulk-heavy geometry.

- `large_bracket_box`: file size -24.1%, travel -26.7%, extrusion moves -12.2%, but M73 time +1.0%.
- `speaker_adapter_ring`: file size -14.6%, travel -16.1%, M73 time unchanged.
- `sloped_surface_torture`: file size -27.0%, travel -33.3%, M73 time -5.6%.

Width-only is less attractive on detail/cosmetic guardrails:

- `thin_wall_comb`: travel reduced, but extrusion moves and positive E increased slightly.
- `led_ring_face`: nearly neutral file/time behavior, with extrusion moves increasing.

## Stock vs Layer-Height-Only Observations

Layer-height-only reduced layer count by roughly 28% on every selected model, confirming that the explicit temporary `layer_height = 0.28` profiles were active.

The M73 time estimate did not consistently improve:

- `thin_wall_comb`: M73 time -6.2%.
- `large_bracket_box`: M73 time -3.0%.
- `speaker_adapter_ring`: M73 time +4.0%.
- `led_ring_face`: M73 time +10.3%.
- `sloped_surface_torture`: M73 time +1.9%.

This means layer-height reduction alone should not be treated as a universal speed win in this profile path. It remains useful as a candidate lever, but it needs visual and physical checks before it is trusted on cosmetic or sloped regions.

## Stock vs Combined Observations

Combined produced the largest G-code size and travel-move reductions in several models:

- `large_bracket_box`: file size -42.0%, travel -44.5%.
- `speaker_adapter_ring`: file size -34.3%, travel -37.4%.
- `sloped_surface_torture`: file size -33.7%, travel -37.9%.
- `thin_wall_comb`: file size -23.6%, travel -23.3%.

However, the M73 time estimate was not consistently improved:

- `large_bracket_box`: unchanged versus stock.
- `thin_wall_comb`: -6.2%.
- `speaker_adapter_ring`: +4.6%.
- `led_ring_face`: +10.3%.
- `sloped_surface_torture`: +3.1%.

Combined is therefore a strong candidate for path-complexity reduction, but not automatically the best candidate for slicer-estimated print time in this run.

## Candidate Decisions

| Model | Best conservative candidate | Most aggressive candidate worth keeping | Reject / caution |
| --- | --- | --- | --- |
| `thin_wall_comb` | Layer-height-only, only after visual thin-feature review. | Combined as a caution candidate. | Width-only is not compelling because extrusion moves and positive E increased. |
| `large_bracket_box` | Layer-height-only for M73 time estimate. | Combined for file/travel/path reduction. | Width-only and combined need physical checks because M73 time does not improve. |
| `speaker_adapter_ring` | Width-only. | Combined only as an aggressive geometry/path candidate. | Layer-height-only and combined need fit, hole, wall, and bonding checks; M73 time increased. |
| `led_ring_face` | Stock / preserve detail. | Width-only only if visual review confirms cosmetic features remain intact. | Layer-height-only and combined are caution/reject candidates for this cosmetic face because M73 time increased and visible detail risk is high. |
| `sloped_surface_torture` | Width-only. | Combined only as a path-count candidate. | Layer-height-only and combined are caution candidates for visible slope stepping; M73 time increased. |

## What Needs Visual Review

Visual review should be performed in Snapmaker Orca preview first, then optionally in Prusa G-code Viewer:

- `thin_wall_comb`: confirm thin features do not disappear, overfill, or merge.
- `large_bracket_box`: confirm exterior loops remain stock-like and reductions are internal/bulk.
- `speaker_adapter_ring`: confirm holes, ring walls, and mounting features remain plausible.
- `led_ring_face`: confirm cosmetic face, LED openings, and small marks remain stock-like.
- `sloped_surface_torture`: confirm `0.28` layer candidates do not introduce unacceptable visible stepping in preview.

## What Needs Physical Validation

Physical validation is required before claiming:

- print-time improvement;
- print strength;
- surface quality;
- dimensional accuracy;
- bonding quality;
- hole fit;
- thin-wall reliability;
- visible-slope acceptability.

The best next physical proxy checks are functional rings/brackets and small visible-detail coupons, not mixed physical nozzle prints.

## Conclusions

- Width-only mostly helps internal/bulk-heavy models and is strongest on `large_bracket_box`, `speaker_adapter_ring`, and `sloped_surface_torture`.
- Layer-height-only reduces layer count as intended, but M73 time estimates do not consistently improve.
- Combined settings produce the largest file-size and travel reductions, but M73 time estimates can stay flat or increase.
- Visible/detail-heavy models should preserve conservative settings until visual review and physical prints say otherwise.
- `0.52` remains the first serious internal-width candidate.
- `0.58` remains an aggressive sparse/internal candidate requiring visual and physical checks.
- Run 002 supports a first AMP heuristic direction: preserve visible/detail regions, consider width-only for internal/bulk regions, and treat coarse layer height as model/region-specific rather than globally safe.

## Required Non-Claims

Run 002 remains profile-only.

Preview/G-code does not prove print strength.

Preview/G-code does not prove surface quality.

Run 002 does not validate physical mixed-nozzle behavior.

Estimated print time is slicer/G-code-derived unless confirmed on hardware.

Bambu/proxy data does not validate U1 behavior.

