# U1 Profile-Only Test Plan

## Purpose

Validate the Stage 1 concept without modifying slicer behavior. This test plan compares stock U1 process profiles against an experimental profile that changes role-specific line widths and enables Arachne.

## Baseline

Baseline process:

- `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`

Inherited process:

- `resources/profiles/Snapmaker/process/fdm_process_U1_0.20.json`
- `resources/profiles/Snapmaker/process/fdm_process_U1_common.json`
- `resources/profiles/Snapmaker/process/fdm_process_U1.json`

Machine:

- `resources/profiles/Snapmaker/machine/Snapmaker U1.json`

## Experimental Profile

Documentation-only example:

- `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`

Experimental settings:

- `wall_generator`: `arachne`
- `outer_wall_line_width`: `0.42`
- `top_surface_line_width`: `0.42`
- `support_line_width`: `0.42`
- `inner_wall_line_width`: `0.52`
- `internal_solid_infill_line_width`: `0.52`
- `sparse_infill_line_width`: `0.58`

This profile is not registered in `resources/profiles/Snapmaker.json` and is not a production preset.

## Test Models

Use at least four models:

- Thin-wall detail model.
- Box or bracket with large infill regions.
- Cosmetic/top-surface detail model.
- Multi-region or modifier-volume model.

## Measurements

For each model:

- Slice with stock U1 0.4 profile.
- Slice with experimental profile.
- Record estimated print time.
- Record filament usage.
- Compare previewed outer walls, inner walls, top surfaces, and infill.
- Export G-code and inspect extrusion widths where visible in comments or path metadata.

## Expected Stage 1 Outcomes

Acceptable:

- Outer visible detail remains close to stock.
- Infill/internal path count decreases or estimated print time improves.
- Arachne handles internal widening without obvious overfill in preview.

Not acceptable:

- Exterior walls visibly degrade in preview.
- Thin walls disappear or overfill.
- Top surfaces become visibly coarse.
- Support paths become unstable.
- Toolpath generation errors occur.

## Hardware Validation Is Deferred

Do not claim print quality or strength improvements from profile-only tests. Hardware validation requires a U1 and calibrated nozzle/toolhead setup.

## Pass Criteria For Phase A

Phase A passes if:

- Stock and experimental profiles both slice successfully.
- The experimental profile produces explainable role-width differences.
- The profile-only experiment identifies whether Arachne is a good Stage 1 target.
- No slicer code behavior is modified.

