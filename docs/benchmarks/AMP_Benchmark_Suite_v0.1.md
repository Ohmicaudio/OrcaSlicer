# AMP Benchmark Suite v0.1

## Purpose

This benchmark suite defines a repeatable validation path for the Adaptive Manufacturing Planner project without changing slicer behavior.

The current benchmark pass compares stock Snapmaker Orca U1 output against experimental profile-only output. Future passes may compare stock output against a future AMP read-only debug artifact, and later against future AMP-influenced slicing output after explicit review.

This benchmark suite does not validate physical mixed-nozzle printing, strength, bonding, surface quality, or dimensional accuracy.

## Current Validation Levels

### Level 0: Stock Snapmaker Orca U1 Profile

- No AMP code involved.
- Uses an existing Snapmaker Orca U1 profile as the baseline.
- Establishes normal preview, path, time, and filament estimates.

### Level 1: Experimental Profile-Only Effective-Width Profile

- No slicer behavior changes.
- Uses existing role-specific line-width settings and Arachne.
- Produces experimental profile-only output for comparison against Level 0.
- Does not prove that Adaptive Manufacturing Planner logic exists or works.

### Level 2: Future AMP Read-Only Prototype

- Produces debug, region, and scoring artifacts only.
- No G-code or toolpath changes.
- Compares future AMP read-only debug artifact recommendations against stock and experimental profile-only output.
- Serves as a visibility and validation layer, not a manufacturing behavior change.

### Level 3: Future AMP Behavior-Changing Prototype

- Not part of the current benchmark pass.
- Requires prior equivalence tests and explicit review.
- May produce future AMP-influenced slicing output only after the read-only prototype is stable and disabled behavior is proven equivalent to stock behavior.

### Level 4: U1 Physical Mixed-Nozzle Validation

- Requires U1 hardware.
- Requires known nozzle/toolhead state, calibration behavior, tool-change behavior, and purge behavior.
- No strength, print-quality, or mixed-nozzle claims before real prints.

## Related Documents

This benchmark suite uses the profile-only baseline described in:

- `docs/U1_Profile_Only_Test_Plan.md`

The benchmark suite should also be read with:

- `docs/AdaptiveManufacturingPlanner_v0.2.md`
- `docs/AMP_ReadOnly_Prototype_Implementation_Plan.md`
- `docs/U1_Mixed_Nozzle_Risk_Register.md`

## Non-Goals

This benchmark suite must not:

- Modify C++ behavior.
- Modify profiles.
- Modify Snapmaker nozzle validation.
- Bypass nozzle mismatch checks.
- Claim that mixed physical nozzle behavior works without U1 hardware.
- Treat slicer preview or G-code inspection as a substitute for real mechanical validation.

## Benchmark Models

Use functional, inspectable parts rather than only decorative benchmark models.

Recommended model categories:

- Thin cosmetic detail part with small text, fine holes, or small exterior features.
- Box, bracket, or adapter with large internal wall and infill regions.
- Cosmetic top-surface part with broad visible top faces.
- Support-heavy part with overhangs and removable support regions.
- Ohmic Audio Labs validation part such as a speaker adapter, LED speaker ring, amplifier mount, trim component, or fabrication fixture.

Each model should be versioned or identified by filename, source, units, and expected use.

## Benchmark Matrix

Run each model through the following levels when available:

| Level | Output Type | Required Today | Behavior-Changing |
| --- | --- | --- | --- |
| Level 0 | Stock Snapmaker Orca U1 profile | Yes | No |
| Level 1 | Experimental profile-only output | Yes | No C++ changes |
| Level 2 | Future AMP read-only debug artifact | No | No |
| Level 3 | Future AMP-influenced slicing output | No | Yes |
| Level 4 | U1 physical mixed-nozzle validation | No | Hardware validation |

For the current pass, only Level 0 and Level 1 are expected.

## Current Profile-Only Procedure

For each model:

1. Slice with the stock Snapmaker Orca U1 profile.
2. Slice with the experimental profile-only effective-width profile.
3. Record slicing success or failure.
4. Record estimated print time.
5. Record estimated filament usage.
6. Inspect previewed outer walls, inner walls, top surfaces, support, and infill.
7. Export G-code for inspection only.
8. Compare path count, apparent extrusion-width behavior, and role-specific changes where visible.
9. Record any preview degradation, missing thin features, apparent overfill, or toolpath-generation errors.

## Future Read-Only Prototype Procedure

When the future AMP read-only prototype exists, add these steps:

1. Enable the hidden read-only planner flag.
2. Generate the future AMP read-only debug artifact.
3. Confirm generated toolpaths and G-code remain unchanged.
4. Compare region classifications against visible geometry.
5. Compare scoring/recommendation reason codes against expected model features.
6. Record cases where the planner recommends stock fallback.

The future AMP read-only debug artifact may help identify candidate regions for later optimization, but it must not be consumed by toolpath generation in the read-only milestone.

## Future Behavior-Changing Procedure

Future AMP-influenced slicing output is out of scope for the current benchmark pass.

Before Level 3 begins:

- Disabled behavior must be proven equivalent to stock behavior.
- Read-only debug output must be stable.
- The behavior-changing path must receive explicit review.
- Safety constraints must be rechecked.
- A rollback/fallback path must be documented.

## What Preview And G-Code Inspection Can Validate

Slicer preview and G-code inspection can validate:

- Whether a model slices successfully.
- Whether path geometry differs between stock and experimental profile-only output.
- Whether role-specific line-width settings appear to affect expected regions.
- Whether visible outer walls, inner walls, top surfaces, supports, and infill look plausible.
- Whether G-code comments or metadata expose expected role/path differences.
- Whether future AMP read-only debug artifact classifications match visible regions.

## What Preview And G-Code Inspection Cannot Validate

Slicer preview and G-code inspection cannot validate:

- Real print strength.
- Surface quality.
- Dimensional accuracy.
- Layer bonding.
- Inter-bead bonding.
- Nozzle/toolhead reliability.
- Purge behavior.
- Tool-change overhead.
- Mixed physical nozzle success.
- Material-specific flow limits under real printer conditions.

Any claim about these properties requires physical U1 printing and measurement.

## Metrics

Record these metrics for each benchmark model:

- Model identifier.
- Profile or validation level.
- Slicing success or failure.
- Estimated print time.
- Estimated filament usage.
- Number of toolpath-generation warnings or errors.
- Visible preview issues.
- Notable G-code/path differences.
- For future AMP read-only debug artifacts: region count, classification labels, confidence scores, fallback reasons, and recommendation reason codes.
- For later U1 physical validation: measured print time, part mass, dimensional checks, surface inspection, bonding observations, and failure notes.

## Pass Criteria For Current Benchmark Pass

The current Level 0/Level 1 benchmark pass is acceptable if:

- Stock Snapmaker Orca U1 profile output slices successfully.
- Experimental profile-only output slices successfully.
- Profile-only differences are explainable through existing role-specific line-width settings and Arachne.
- No slicer behavior changes are required.
- No profile defaults are modified.
- No Snapmaker nozzle validation path is modified.
- The results avoid claims about real print strength, print quality, dimensional accuracy, bonding, or mixed physical nozzle behavior.

## Fail Criteria For Current Benchmark Pass

The current benchmark pass fails if:

- Experimental profile-only output causes slicing errors.
- Thin features disappear in preview without an acceptable explanation.
- Outer cosmetic walls visibly degrade in preview.
- Top surfaces become visibly coarse or sparse.
- Support paths become unstable.
- The benchmark writeup implies behavior-changing AMP output exists today.
- The benchmark writeup claims physical U1 mixed-nozzle behavior without real U1 validation.

## Reporting Template

Use one record per model and validation level:

```text
Model:
Source:
Units:
Validation level:
Profile/config:
Slicing result:
Estimated print time:
Estimated filament:
Preview observations:
G-code/path observations:
Future AMP read-only debug artifact observations:
Physical print observations:
Pass/fail:
Notes:
```

For current Level 0/Level 1 runs, leave future AMP read-only debug artifact observations and physical print observations empty or mark them as not available.
