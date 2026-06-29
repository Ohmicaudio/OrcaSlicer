# AMP Stage 1 Profile-Only Benchmark Run 001

## Purpose

This document defines the first public Stage 1 profile-only benchmark package for Adaptive Manufacturing Planner (AMP).

The run compares stock Snapmaker Orca U1 profile output against an experimental effective-width profile. It does not modify slicer behavior, production profiles, G-code generation, Snapmaker nozzle validation, or any production slicing path.

This is a profile-only benchmark. It can show whether existing role-specific line-width settings and Arachne produce explainable preview/G-code differences. It cannot prove print-time improvement, strength improvement, print quality improvement, dimensional accuracy, bonding, or mixed physical nozzle behavior without measured hardware results.

## Related Documents

- `docs/U1_Profile_Only_Test_Plan.md`
- `docs/benchmarks/AMP_Benchmark_Suite_v0.1.md`
- `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`
- `docs/benchmarks/models_needed.md`

## Baseline Profile

Use the stock Snapmaker U1 0.4 mm process profile:

- `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`

Inherited process files:

- `resources/profiles/Snapmaker/process/fdm_process_U1_0.20.json`
- `resources/profiles/Snapmaker/process/fdm_process_U1_common.json`
- `resources/profiles/Snapmaker/process/fdm_process_U1.json`

Machine profile:

- `resources/profiles/Snapmaker/machine/Snapmaker U1.json`

## Experimental Profile

Use the documentation-only experimental effective-width profile:

- `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`

This profile is not registered as a production preset and does not change stock Snapmaker profiles.

Experimental settings:

- `wall_generator`: `arachne`
- `line_width`: `0.45`
- `outer_wall_line_width`: `0.42`
- `top_surface_line_width`: `0.42`
- `support_line_width`: `0.42`
- `inner_wall_line_width`: `0.52`
- `internal_solid_infill_line_width`: `0.52`
- `sparse_infill_line_width`: `0.58`

## Models Needed

Run 001 needs community-sourced or locally-created models that exercise different geometry roles.

Minimum set:

- Thin-wall detail model.
- Large bracket or box.
- Cosmetic top-surface detail model.
- Embossed or debossed text model.
- Speaker adapter ring.
- LED speaker ring face.
- Curved badge.
- Sloped surface torture test.
- Multi-region modifier model.

Record each model with filename, source URL or author, license if known, units, scale, and intended feature being tested.

## Procedure

For each model:

1. Slice with the stock Snapmaker U1 0.4 mm profile.
2. Slice with the experimental effective-width profile.
3. Record whether slicing completed successfully.
4. Record estimated print time from the slicer.
5. Record estimated filament usage from the slicer.
6. Inspect previewed outer walls, inner walls, top surfaces, support, and infill.
7. Export G-code for inspection only.
8. Inspect role/path differences where visible in preview, comments, or metadata.
9. Record warnings, errors, missing features, apparent overfill, or preview degradation.

Do not infer physical strength, print quality, bonding, or dimensional accuracy from preview alone.

## Exact Measurements To Collect

For each model and each profile:

- Model identifier.
- Model source.
- Units and scale.
- Profile used.
- Slicing success or failure.
- Slicer warnings or errors.
- Estimated print time.
- Estimated filament usage.
- Previewed outer-wall condition.
- Previewed inner-wall condition.
- Previewed top-surface condition.
- Previewed infill condition.
- Previewed support condition, if support is enabled.
- G-code file size.
- G-code comments or metadata that indicate role/path differences, if available.
- Qualitative notes on visible path count or path spacing changes.

For comparison:

- Slicer-estimated print-time delta between stock and experimental profile-only output.
- Estimated filament-usage delta between stock and experimental profile-only output.
- Whether differences are explainable by role-specific line widths and Arachne.

Do not claim print-time improvement until hardware timing is measured. For Run 001, report only slicer-estimated print-time deltas.

## Pass Criteria

Run 001 passes for a model if:

- Stock Snapmaker Orca U1 profile output slices successfully.
- Experimental effective-width profile output slices successfully.
- Differences are explainable as profile-only effects from existing role-specific line-width settings and Arachne.
- Visible outer walls remain close to stock in preview.
- Thin-wall detail does not disappear in preview.
- Top surfaces do not become visibly coarse or sparse in preview.
- Support paths do not become visibly unstable in preview.
- No production profile defaults are modified.
- No C++ slicer behavior is modified.
- No Snapmaker nozzle validation path is modified.

## Fail Criteria

Run 001 fails for a model if:

- Stock output fails unexpectedly.
- Experimental profile-only output fails to slice.
- Thin features disappear in preview.
- Cosmetic outer walls visibly degrade in preview.
- Top surfaces become visibly coarse, sparse, or unstable.
- Support paths become visibly unstable.
- The writeup implies AMP behavior-changing output exists today.
- The writeup claims physical U1 mixed-nozzle behavior without real U1 validation.
- The writeup claims strength, print quality, bonding, or dimensional improvement from preview/G-code inspection alone.

## What Preview And G-Code Can Validate

Preview and G-code inspection can validate:

- Whether each model slices successfully.
- Whether the experimental effective-width profile changes visible path layout.
- Whether outer walls, top surfaces, inner walls, support, and infill remain plausible in preview.
- Whether role-specific line-width settings appear to affect the expected regions.
- Whether the experimental profile produces explainable path-count or spacing differences.
- Whether G-code comments or metadata expose expected role/path differences.

## What Cannot Be Claimed Without Hardware

Do not claim:

- Real print-time improvement.
- Strength improvement.
- Print quality improvement.
- Dimensional accuracy improvement.
- Layer bonding improvement.
- Inter-bead bonding improvement.
- Surface finish improvement.
- U1 toolhead reliability.
- Purge or wipe behavior.
- Mixed physical nozzle success.
- Material-specific flow safety.

All physical claims require U1 hardware, calibrated toolheads, measured prints, and documented test conditions.

## Reporting Template

Use one record per model:

```text
Model:
Source:
License:
Units/scale:
Feature category:

Baseline profile:
Baseline slicing result:
Baseline estimated print time:
Baseline estimated filament:
Baseline warnings/errors:
Baseline preview observations:
Baseline G-code/path observations:

Experimental profile:
Experimental slicing result:
Experimental estimated print time:
Experimental estimated filament:
Experimental warnings/errors:
Experimental preview observations:
Experimental G-code/path observations:

Estimated print-time delta:
Estimated filament delta:
Explainable profile-only differences:
Preview regressions:
Pass/fail:
Notes:
Physical print observations: Not available in profile-only benchmark.
```

## Run 001 Status

Status: ready for model selection and slicing.

This benchmark package does not include measured results yet.
