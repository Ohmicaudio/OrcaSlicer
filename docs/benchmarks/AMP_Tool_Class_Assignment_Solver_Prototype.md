# AMP Tool-Class Assignment Solver Prototype

## Purpose

This document records the first offline Adaptive Manufacturing Planner tool-class assignment solver.

The solver maps region metadata to an advisory U1 tool class:

```text
region metadata + tool matrix -> recommended tool class + fallback + reason
```

This is not slicer integration. It does not modify profiles, G-code generation, Flow, LayerRegion, PerimeterGenerator, Arachne, UI, PrintObject, Snapmaker validation, or CalibUtils.

## Tool Ladder Summary

The current U1 profile-backed tool ladder is:

| Tool class | Planning role | Layer-height class | Line-width class |
| --- | --- | --- | --- |
| 0.2 mm | Fine/micro visible detail | 0.06-0.10 mm | 0.22 mm |
| 0.4 mm | Safe/general visible detail fallback | 0.12-0.20 mm | 0.42-0.45 mm |
| 0.6 mm | Structural shell / medium bulk | 0.24-0.36 mm | 0.62 mm |
| 0.8 mm | Hidden/internal bulk | 0.32-0.56 mm | 0.82 mm |

## Input Metadata Schema

The solver accepts a JSON file with a top-level `regions` array. Each region may include:

| Field | Values / meaning |
| --- | --- |
| `region_name` | Stable region identifier. |
| `visibility` | `hidden`, `internal`, or `visible`. |
| `detail_criticality` | `none`, `low`, `medium`, `high`, or `micro`. |
| `wall_or_bulk` | `thin_wall`, `normal_wall`, `structural_shell`, or `bulk`. |
| `min_feature_size_mm` | Minimum feature-size estimate for the region. |
| `xy_min_feature_size_mm` | Minimum local XY feature size. Defaults to `min_feature_size_mm` when omitted. |
| `xy_nominal_feature_size_mm` | Typical/local nominal XY feature size. |
| `z_feature_height_mm` | Height of the local detail feature. |
| `vertical_extent_mm` | Total vertical persistence of the region/detail. |
| `vertical_extent_layers` | Approximate number of layers through which the region/detail persists. |
| `target_layer_height_mm` | Intended layer-height estimate. |
| `surface_slope_degrees` | Coarse surface orientation/slope estimate. |
| `local_z_candidate` | Advisory flag that future local-Z handling may be needed. |
| `z_resolution_criticality` | `none`, `low`, `medium`, `high`, or `micro`. |
| `line_type` | Slicer/path intent, such as `external_perimeter`, `top_surface`, `sparse_infill`, `support_interface`, `bridge`, or `color_detail_skin`. |
| `line_role_visibility` | Role-level visibility, such as `visible`, `hidden`, `internal`, `cosmetic`, `mating`, or `structural`. |
| `estimated_region_area_mm2` | Coarse area estimate for cost decisions. |
| `estimated_path_length_mm` | Coarse path-length estimate for cost decisions. |
| `toolchange_allowed` | Whether advisory multi-tool assignment is allowed for the region. |
| `material_risk` | `normal`, `clog_risk`, `flexible`, or `abrasive`. |
| `confidence_hint` | Optional hint such as `low`. |
| `estimated_toolchange_cost_s` | Optional estimated cost of switching to the recommended tool. |
| `minimum_time_savings_required_s` | Optional minimum savings target used when explaining a toolchange. |
| `minimum_region_area_for_toolchange_mm2` | Optional area threshold for toolchange-worthy regions. |
| `minimum_path_length_for_toolchange_mm` | Optional path-length threshold for toolchange-worthy regions. |
| `current_tool_class` | Optional current/default tool class, usually `0.4` for conservative fallback. |
| `single_nozzle_mode` | Optional flag that forces stock/single-tool fallback behavior. |

The solver also accepts the current generated fixture sidecar format from:

```text
outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture_regions.json
```

That sidecar is normalized into the richer schema before assignment.

## Rule Set

The current rule set is line-type and 3D-feature aware:

| Region/line type | Rule |
| --- | --- |
| External perimeter / visible cosmetic | Use 0.2 only for micro/high detail when XY and Z feature data justify it. Use 0.4 for normal visible detail. Reject 0.8. Avoid 0.6 unless it is structural and not cosmetic. |
| Top or bottom surface | Preserve conservative tool class unless Z/detail risk is low. Do not assign 0.8 to top cosmetic surfaces. Sloped top surfaces receive visual-review flags. |
| Internal perimeter | Treat 0.6 as a review candidate only when the region is hidden/internal, thick enough, and vertically persistent. Fall back to 0.4 for thin or shallow regions. |
| Sparse infill / hidden bulk | Treat 0.8 as a candidate only if hidden/bulk line type, feature size, area/path, and toolchange gates pass. |
| Bridge / overhang | Use conservative fallback and add `bridge_or_overhang_sensitive`. |
| Support interface | Keep conservative and add `support_interface_risk`. Non-interface support may be reviewed separately. |
| Painted surface / color detail skin | Treat as visible/cosmetic, preserve fine/detail behavior, and add `future_surface_color_track`. This is only a future surface-color planning marker, not an implemented color system. |
| Local-Z candidate | Add `local_z_candidate`; visible high/micro Z detail also gets `local_z_future_required`. No local-Z behavior is implemented. |
| Toolchange disabled | Return `single_nozzle_fallback`. |
| Low confidence | Fall back to 0.4/general. |

All mixed-tool recommendations carry the U1 touchscreen advisory warning.

## Cost-Gating Update

The solver now separates candidate selection from cost gating:

```text
region classification -> candidate tool class -> cost gate -> final recommendation
```

Additional cost-gating rules:

1. If `toolchange_allowed` is false or `single_nozzle_mode` is true, return `single_nozzle_fallback`.
2. If the candidate tool matches `current_tool_class`, pass the cost gate because no toolchange is needed.
3. If the candidate tool differs from `current_tool_class`, require both region area and path length to meet the configured thresholds.
4. If the region fails the threshold gate, fall back to `current_tool_class` or the safer general fallback.
5. 0.2 recommendations require visible high/micro detail, normal material risk, and a documented sliceable feature-size lower bound.
6. 0.8 recommendations remain hidden/internal/bulk only and must pass the region-size gate.

New output fields:

| Field | Meaning |
| --- | --- |
| `cost_gate_passed` | Whether the assignment passed the toolchange/region-size gate. |
| `estimated_toolchange_cost_s` | Toolchange cost used for explanation. |
| `cost_gate_reason` | Explanation of the gate pass/fail. |
| `fallback_reason` | Explanation when the solver falls back. |

The corrected 0.2 diagnostic matters here: 0.2 is viable for fine/micro regions, but it is expensive. The solver therefore treats 0.2 as a high-cost detail tool that must be justified by visible detail and sufficient region size.

## Example Assignment Table

Generated command:

```powershell
python tools/amp_tool_class_assignment_solver.py --input docs/benchmarks/AMP_Tool_Class_Assignment_Examples.json --format markdown --out outputs/amp_tool_assignment/examples_3d_line_type_assignments.md
```

| Region | Line type | Role | Tool | Fallback | Cost gate | Confidence | Key result |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| `shallow_logo_top_surface` | `top_surface` | `cosmetic` | `0.2` | `0.4` | pass | 0.68 | Visible top detail has fine XY/Z requirements and is detail-driven, not speed-driven. |
| `tall_visible_side_text` | `external_perimeter` | `cosmetic` | `0.4` | `0.4` | pass | 0.65 | Tall visible side detail stays on 0.4 because it is not shallow micro-Z detail. |
| `hidden_internal_perimeter` | `internal_perimeter` | `structural` | `0.6` | `0.4` | pass | 0.70 | Hidden/internal perimeter has enough XY size and vertical persistence for 0.6 review. |
| `support_interface_should_stay_conservative` | `support_interface` | `mating` | `0.4` | `0.4` | pass | 0.66 | Support interface remains conservative. |
| `bridge_reject_large_tool` | `bridge` | `structural` | `0.4` | `0.4` | pass | 0.60 | Bridge/overhang regions reject large-tool assignment by default. |
| `painted_surface_color_skin` | `color_detail_skin` | `cosmetic` | `0.4` | `0.2` | pass | 0.70 | Painted/color skin is visible/cosmetic and goes to the future surface-color track. |
| `local_z_micro_detail_candidate` | `painted_surface` | `cosmetic` | `0.2` | `0.4` | pass | 0.68 | Local-Z future requirement is flagged for shallow visible micro detail. |
| `bulk_region_worth_0p8` | `sparse_infill` | `hidden` | `0.8` | `0.6` | pass | 0.70 | Hidden sparse infill/bulk can use 0.8 only when cost gates pass. |
| `bulk_region_too_small_for_0p8` | `sparse_infill` | `hidden` | `0.4` | `0.4` | fail | 0.66 | Small sparse infill falls back because it cannot justify the toolchange. |

## Multi-Tool Fixture Assignment Results

Generated command:

```powershell
python tools/amp_tool_class_assignment_solver.py --input docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json --format markdown --out outputs/amp_tool_assignment/fixture_3d_line_type_assignments.md
```

| Region | Line type | Role | Tool | Layer class | Width class | Fallback | Cost gate | Confidence | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| `micro_detail_zone` | `external_perimeter` | `cosmetic` | `0.2` | `0.06-0.10` | `0.22` | `0.4` | pass | 0.70 | 0.2 remains viable because the region is visible/cosmetic external detail with small XY and Z feature metadata. |
| `normal_visible_detail_zone` | `top_surface` | `cosmetic` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.2` | pass | 0.70 | 0.4 remains the top/cosmetic visible-detail class; sloped/top-surface visual review is flagged. |
| `structural_shell_zone` | `internal_perimeter` | `structural` | `0.6` | `0.24-0.36` | `0.62` | `0.4` | pass | 0.70 | 0.6 remains a structural/internal perimeter review candidate because the region is thick and vertically persistent. |
| `bulk_zone` | `sparse_infill` | `hidden` | `0.8` | `0.32-0.56` | `0.82` | `0.6` | pass | 0.70 | 0.8 remains hidden sparse-infill/bulk only and passes the size/toolchange gate. |

## Effect On 0.2 / 0.8 Recommendations

The cost gate changes the solver from a static role mapper into an advisory planner:

- 0.2 remains viable for fine/micro regions, but it is marked as a high-cost detail tool and must pass XY feature-size, Z feature-height, visibility, material, and region-size checks.
- 0.4 remains the safe visible-detail fallback when 0.2 is too risky, too costly, or material-limited.
- 0.6 remains the structural shell class and medium-bulk fallback.
- 0.8 remains hidden/internal/bulk only and must pass line-type, region-size, and toolchange gates.

The 3D metadata update adds an important correction: tool selection cannot be decided from 2D area/path alone. Line type, surface role, Z feature height, and vertical persistence are now part of the advisory decision.

The corrected 0.2 diagnostic showed the micro body produced many real extrusion moves after fixing the metrics parser. That supports keeping 0.2 in the ladder, but only with cost gating and preview-required risk flags.

## Fallback Behavior

The current fallback hierarchy is conservative:

- 0.2 micro/detail assignments fall back to 0.4 if material or feature risk is high.
- 0.2 micro/detail assignments also fall back to 0.4 if the region is too small to justify switching tools.
- 0.4 remains the safe/general visible-detail fallback.
- 0.6 structural assignments fall back to 0.4 for thin or visible/mating regions.
- 0.8 bulk assignments fall back to 0.6 for medium bulk and to the current/general tool when the cost gate fails.
- `single_nozzle_fallback` preserves stock/single-tool behavior when tool changes are disabled.

## Risk Flags

Current risk flags include:

- `preview_required`
- `material_abrasive`
- `toolchange_disabled`
- `reject_large_tool_for_thin_wall`
- `low_confidence`
- `avoid_large_visible_tool`
- `high_cost_detail_tool`
- `bulk_tool_cost_gate`
- `cost_gate_failed`
- `local_z_candidate`
- `local_z_future_required`
- `sloped_top_surface_visual_review`
- `bridge_or_overhang_sensitive`
- `support_interface_risk`
- `future_surface_color_track`
- `internal_perimeter_width_review`
- U1 touchscreen mixed-nozzle advisory warning

## What This Proves

- AMP can now produce an offline region-to-tool-class assignment.
- 0.2 is the fine/micro detail class.
- 0.4 is the safe/general visible detail fallback.
- 0.6 is the structural shell class.
- 0.8 is the bulk class.
- The generated multi-tool fixture maps to the intended 0.2 / 0.4 / 0.6 / 0.8 ladder.
- The solver emits fallback tools, reasons, risk flags, confidence values, and cost-gate explanations.
- The solver now carries 3D feature metadata and line/path type through the advisory output.
- Local-Z need is flagged as future work; no local-Z behavior is implemented.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or real toolchange reliability.

Tool assignment remains advisory/offline only.

Touchscreen-compatible mixed-nozzle behavior remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.
