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

## Example Assignment Table

Generated command:

```powershell
python tools/amp_tool_class_assignment_solver.py --input docs/benchmarks/AMP_Tool_Class_Assignment_Examples.json --format markdown --out outputs/amp_tool_assignment/examples.md
```

| Region | Tool | Layer class | Width class | Fallback | Confidence | Risk flags | Reason |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| `micro_detail_zone` | `0.2` | `0.06-0.10` | `0.22` | `0.4` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; preview_required | Visible micro detail is plausible for the 0.2 fine/detail class. |
| `normal_visible_detail_zone` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.2` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; avoid_large_visible_tool | Normal visible/detail geometry should use the 0.4 general class and avoid 0.8. |
| `structural_shell_zone` | `0.6` | `0.24-0.36` | `0.62` | `0.4` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path. | Internal/low-detail structural shell is a 0.6 candidate. |
| `bulk_zone` | `0.8` | `0.32-0.56` | `0.82` | `0.6` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path. | Hidden/internal bulk is large enough for the 0.8 bulk class. |
| `abrasive_micro_detail_rejected` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.4` | 0.65 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; material_abrasive | 0.2 is rejected for this material risk; use 0.4 as the safer visible-detail fallback. |
| `no_toolchange_single_nozzle_fallback` | `single_nozzle_fallback` | `stock` | `stock` | `0.4` | 0.35 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; toolchange_disabled | Tool changes are disabled, so AMP keeps advisory stock/single-tool behavior. |
| `thin_wall_reject_large_tool` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.2` | 0.62 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; reject_large_tool_for_thin_wall | Thin wall is too small for 0.6/0.8; use finer fallback. |
| `low_confidence_fallback` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.4` | 0.45 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; low_confidence | Region confidence is low; fall back to the general visible/detail class. |

## Multi-Tool Fixture Assignment Results

Generated command:

```powershell
python tools/amp_tool_class_assignment_solver.py --input outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture_regions.json --format markdown --out outputs/amp_tool_assignment/multitool_fixture_assignments.md
```

| Region | Tool | Layer class | Width class | Fallback | Confidence | Risk flags | Reason |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| `micro_detail_zone` | `0.2` | `0.06-0.10` | `0.22` | `0.4` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; preview_required | Visible micro detail is plausible for the 0.2 fine/detail class. |
| `normal_visible_detail_zone` | `0.4` | `0.12-0.20` | `0.42-0.45` | `0.2` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path.; avoid_large_visible_tool | Normal visible/detail geometry should use the 0.4 general class and avoid 0.8. |
| `structural_shell_zone` | `0.6` | `0.24-0.36` | `0.62` | `0.4` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path. | Internal/low-detail structural shell is a 0.6 candidate. |
| `bulk_zone` | `0.8` | `0.32-0.56` | `0.82` | `0.6` | 0.70 | Advisory only: physical mixed-nozzle execution remains blocked for U1 touchscreen workflows until Snapmaker provides a compatible per-tool metadata/logical mapping path. | Hidden/internal bulk is large enough for the 0.8 bulk class. |

## Fallback Behavior

The current fallback hierarchy is conservative:

- 0.2 micro/detail assignments fall back to 0.4 if material or feature risk is high.
- 0.4 remains the safe/general visible-detail fallback.
- 0.6 structural assignments fall back to 0.4 for thin or visible/mating regions.
- 0.8 bulk assignments fall back to 0.6 for medium bulk and 0.4 when tool changes are not allowed.
- `single_nozzle_fallback` preserves stock/single-tool behavior when tool changes are disabled.

## Risk Flags

Current risk flags include:

- `preview_required`
- `material_abrasive`
- `toolchange_disabled`
- `reject_large_tool_for_thin_wall`
- `low_confidence`
- `avoid_large_visible_tool`
- U1 touchscreen mixed-nozzle advisory warning

## What This Proves

- AMP can now produce an offline region-to-tool-class assignment.
- 0.2 is the fine/micro detail class.
- 0.4 is the safe/general visible detail fallback.
- 0.6 is the structural shell class.
- 0.8 is the bulk class.
- The generated multi-tool fixture maps to the intended 0.2 / 0.4 / 0.6 / 0.8 ladder.
- The solver emits fallback tools, reasons, risk flags, and confidence values.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or real toolchange reliability.

Tool assignment remains advisory/offline only.

Touchscreen-compatible mixed-nozzle behavior remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.
