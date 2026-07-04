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
| `target_layer_height_mm` | Intended layer-height estimate. |
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

The first rule set is intentionally simple:

1. Micro/high visible detail uses 0.2 only when the feature size is plausible and material risk is normal.
2. 0.2 is rejected for clog-risk, flexible, or abrasive material contexts, with 0.4 as the fallback.
3. Normal visible detail prefers 0.4 and avoids 0.8.
4. Structural shell regions prefer 0.6 when detail/visibility risk is low.
5. Hidden/internal bulk prefers 0.8 only when the region is large enough and tool changes are allowed.
6. Thin walls reject large tools and fall back finer.
7. Toolchange-disabled regions return `single_nozzle_fallback`.
8. Low-confidence regions fall back to 0.4/general.
9. All mixed-tool recommendations carry the U1 touchscreen warning.

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
python tools/amp_tool_class_assignment_solver.py --input docs/benchmarks/AMP_Tool_Class_Assignment_Examples.json --format markdown --out outputs/amp_tool_assignment/examples_cost_gated.md
```

| Region | Tool | Layer class | Width class | Fallback | Cost gate | Confidence | Key result |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| `micro_detail_zone` | `0.2` | `0.06-0.10` | `0.22` | `0.4` | pass | 0.70 | Visible micro region is large enough to justify the 0.2 detail tool. |
| `normal_visible_detail_zone` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.2` | pass | 0.70 | Current/default 0.4 tool is already the visible-detail recommendation. |
| `structural_shell_zone` | `0.6` | `0.24-0.36` | `0.62` | `0.4` | pass | 0.70 | Structural shell is large enough to justify 0.6. |
| `bulk_zone` | `0.8` | `0.32-0.56` | `0.82` | `0.6` | pass | 0.70 | Hidden bulk is large enough to justify 0.8. |
| `abrasive_micro_detail_rejected` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.4` | pass | 0.65 | 0.2 is rejected due to material risk. |
| `no_toolchange_single_nozzle_fallback` | `single_nozzle_fallback` | `stock` | `stock` | `0.4` | fail | 0.35 | Tool changes are disabled. |
| `thin_wall_reject_large_tool` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.2` | pass | 0.62 | Large tools are rejected for thin wall geometry. |
| `low_confidence_fallback` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.4` | pass | 0.45 | Low confidence falls back to 0.4/general. |
| `tiny_micro_detail_not_worth_toolchange` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.4` | fail | 0.70 | 0.2 would be appropriate by detail type, but the region is too small to justify a toolchange. |
| `large_micro_detail_panel_worth_0p2` | `0.2` | `0.06-0.10` | `0.22` | `0.4` | pass | 0.70 | Large visible micro panel keeps the 0.2 recommendation. |
| `small_bulk_region_not_worth_0p8` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.4` | fail | 0.70 | Bulk intent is too small to justify leaving the current/default 0.4 tool. |
| `large_hidden_bulk_worth_0p8` | `0.8` | `0.32-0.56` | `0.82` | `0.6` | pass | 0.70 | Large hidden bulk keeps the 0.8 recommendation. |
| `current_tool_0p4_no_toolchange_fallback` | `single_nozzle_fallback` | `stock` | `stock` | `0.4` | fail | 0.35 | Tool changes are disabled. |
| `clog_risk_micro_detail_fallback_0p4` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.4` | pass | 0.65 | 0.2 is rejected for clog-risk material. |

## Multi-Tool Fixture Assignment Results

Generated command:

```powershell
python tools/amp_tool_class_assignment_solver.py --input outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture_regions.json --format markdown --out outputs/amp_tool_assignment/multitool_fixture_assignments_cost_gated.md
```

| Region | Tool | Layer class | Width class | Fallback | Cost gate | Confidence | Interpretation |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| `micro_detail_zone` | `0.2` | `0.06-0.10` | `0.22` | `0.4` | pass | 0.70 | 0.2 remains viable because the fixture-side printable micro proxy meets the documented 0.35 mm lower bound and size gate. |
| `normal_visible_detail_zone` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.2` | pass | 0.70 | 0.4 remains the visible-detail default. |
| `structural_shell_zone` | `0.6` | `0.24-0.36` | `0.62` | `0.4` | pass | 0.70 | 0.6 remains the structural shell class. |
| `bulk_zone` | `0.8` | `0.32-0.56` | `0.82` | `0.6` | pass | 0.70 | 0.8 remains bulk-only and passes the size/toolchange gate. |

## Effect On 0.2 / 0.8 Recommendations

The cost gate changes the solver from a static role mapper into an advisory planner:

- 0.2 remains viable for fine/micro regions, but it is marked as a high-cost detail tool and must pass feature-size, visibility, material, and region-size checks.
- 0.4 remains the safe visible-detail fallback when 0.2 is too risky, too costly, or material-limited.
- 0.6 remains the structural shell class and medium-bulk fallback.
- 0.8 remains hidden/internal/bulk only and must pass the region-size/toolchange gate.

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
- U1 touchscreen mixed-nozzle advisory warning

## What This Proves

- AMP can now produce an offline region-to-tool-class assignment.
- 0.2 is the fine/micro detail class.
- 0.4 is the safe/general visible detail fallback.
- 0.6 is the structural shell class.
- 0.8 is the bulk class.
- The generated multi-tool fixture maps to the intended 0.2 / 0.4 / 0.6 / 0.8 ladder.
- The solver emits fallback tools, reasons, risk flags, confidence values, and cost-gate explanations.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or real toolchange reliability.

Tool assignment remains advisory/offline only.

Touchscreen-compatible mixed-nozzle behavior remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.
