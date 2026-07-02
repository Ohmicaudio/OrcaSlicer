# AMP Resolution Cost Model Prototype

## Purpose

This document describes the first offline Adaptive Manufacturing Planner resolution-allocation estimator.

The goal is to estimate when a region should preserve conservative detail settings versus when it may be a candidate for wider line width, larger layer height, or other lower-resolution manufacturing settings.

This is an offline estimator. It does not modify slicer behavior. It does not inspect real slicer geometry. It does not emit G-code. It does not prove physical print quality.

## Framing

AMP is about motion and resolution allocation:

- XY: line width, wall count, path spacing, and perimeter treatment.
- Z: layer height, adaptive layer height, and local detail zones.
- Visibility: outside/cosmetic surfaces versus hidden/internal structure.
- Cost: motion time, path count, flow demand, and later toolchange overhead.

The physical coupon work remains useful as a sanity check and boundary-finding method, but the planner engine should primarily reason from visibility, geometry, wall thickness, layer height, motion cost, and flow limits.

## Tool

Prototype:

```text
tools/amp_resolution_cost_model.py
```

The tool can run built-in examples or read a JSON input file.

## Inputs

Each region scenario includes:

- `region_name`
- `visible_surface`
- `top_surface`
- `detail_critical`
- `approximate_region_area_mm2`
- `approximate_path_length_mm`
- `wall_thickness_mm`
- `stock_line_width_mm`
- `candidate_line_width_mm`
- `stock_layer_height_mm`
- `candidate_layer_height_mm`
- `max_volumetric_flow_mm3_s`
- `nominal_speed_mm_s`
- `acceleration_penalty_factor`, optional

## Computed Values

For each region, the prototype estimates:

- stock path count
- candidate path count
- stock extrusion volume
- candidate extrusion volume
- stock time
- candidate time
- time delta
- stock volumetric flow
- candidate volumetric flow
- resolution risk flag
- recommendation

Recommendations:

- `preserve_detail`
- `widen_internal`
- `increase_layer_height`
- `candidate_ok`
- `reject_candidate`

## Decision Rules

The prototype uses intentionally conservative rules:

- Visible surfaces bias toward `preserve_detail`.
- Detail-critical regions bias toward `preserve_detail`.
- Top surfaces are conservative until validated.
- Hidden/internal regions may consider wider line widths.
- Candidates are rejected if the requested line width exceeds the wall thickness.
- Candidates are rejected if line width leaves a poor residual wall segment.
- Candidates that exceed max volumetric flow are flagged and speed-limited in the estimate.
- Candidates with small estimated time savings preserve stock settings.

This model is a planning estimate, not proof of print strength, surface quality, bonding, dimensional accuracy, or U1 behavior.

## Built-In Scenarios

The built-in examples cover:

1. visible logo/text region
2. hidden internal wall region
3. large infill/bulk region
4. thick speaker ring wall
5. thin wall detail region
6. top cosmetic surface

Run:

```powershell
python tools\amp_resolution_cost_model.py --examples --format markdown
```

Example output columns:

```text
region_name
stock_path_count
candidate_path_count
stock_time_s
candidate_time_s
time_delta_percent
candidate_flow_mm3_s
resolution_risk_flag
recommendation
```

CSV output:

```powershell
python tools\amp_resolution_cost_model.py --examples --format csv --out outputs\amp_resolution_cost_model\examples.csv
```

## JSON Input Example

```json
[
  {
    "region_name": "hidden bracket web",
    "visible_surface": false,
    "top_surface": false,
    "detail_critical": false,
    "approximate_region_area_mm2": 1200,
    "approximate_path_length_mm": 1800,
    "wall_thickness_mm": 3.2,
    "stock_line_width_mm": 0.42,
    "candidate_line_width_mm": 0.58,
    "stock_layer_height_mm": 0.20,
    "candidate_layer_height_mm": 0.20,
    "max_volumetric_flow_mm3_s": 12.0,
    "nominal_speed_mm_s": 80.0
  }
]
```

Run:

```powershell
python tools\amp_resolution_cost_model.py --input path\to\regions.json --format markdown
```

## Validation Strategy

This prototype should be validated in layers:

- Compare estimator output against known slicer profile settings.
- Compare estimated directionality against generated G-code path counts and time estimates.
- Use physical proxy coupons only as bounds and sanity checks.
- Keep U1-specific mixed physical nozzle validation separate until U1 hardware behavior is available and documented.

Preview and G-code can validate path and motion differences. They cannot validate real print strength, surface quality, dimensional accuracy, bonding, or physical mixed-nozzle behavior.

## Platform Relevance

This applies to single-nozzle printers as well as future toolchanger and mixed-nozzle platforms.

For single-nozzle printers, the same model can reason about:

- adaptive layer height
- outer versus inner line width
- top-surface protection
- bulk infill width
- internal wall path count

For toolchanger systems later, the same math can inform where small-nozzle/fine-layer paths are worth their cost and where larger-nozzle/high-flow paths may be acceptable.

Snapmaker U1 remains the first submitted validation platform for this branch, but the estimator itself is not U1-only.

## Non-Goals

- No slicer integration.
- No C++ implementation.
- No profile changes.
- No G-code generation changes.
- No Flow, LayerRegion, PerimeterGenerator, Arachne, UI, PrintObject, Snapmaker validation, or CalibUtils.cpp changes.
- No claim of physical print quality.
- No claim of physical mixed-nozzle support.

