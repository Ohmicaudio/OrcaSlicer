# AMP Stage 1 Heuristic Candidates

## Purpose

This document translates Run 001 and Run 002 profile-only evidence into candidate rules for future Adaptive Manufacturing Planner behavior.

These rules are not implemented. They are not production defaults. They are a cautious decision record for what AMP should test next before any planner logic is allowed to influence slicing output.

## Current Evidence Summary

Run 001 showed that the experimental effective-width/Arachne profile changes generated G-code metrics across the synthetic model set. It reduced file size and travel-move count across all six generated models, but some detail/cosmetic cases still required viewer confirmation.

Run 002 split that first experiment into separate candidate strategies:

- Width-only is the cleanest candidate for internal/bulk regions.
- Layer-height-only reduces layer count but does not always improve Snapmaker's `M73` time estimate.
- Combined width plus coarse layer height can produce strong path and file-size reductions, but it needs visual and physical validation before it is trusted.
- Visible/detail-heavy regions remain conservative until there is stronger evidence.

The current evidence is still profile-only slicer evidence. It is useful for selecting candidate rules, not for claiming final print performance.

## Conservative Heuristic Candidate

### Rule A: Preserve Visible And Detail Regions

Future AMP behavior should preserve conservative settings for:

- outer walls;
- visible exterior surfaces;
- top surfaces;
- text, logos, badges, trim faces, and other detail regions;
- thin-wall or detail-risk regions;
- sloped or top cosmetic surfaces unless visual review approves a coarser setting.

Initial candidate width:

```text
visible/detail width: stock / 0.42 mm
```

Rationale:

- Run 001 kept thin and visible features as caution cases.
- Run 002 showed that detail/cosmetic guardrails such as `thin_wall_comb` and `led_ring_face` do not justify aggressive global changes from metrics alone.
- Top and sloped surfaces carry high visual risk, especially when layer height changes are involved.

### Rule B: Widen Internal And Bulk Regions

Future AMP behavior may consider wider internal/bulk settings when the region is hidden, structurally non-critical in the current pass, and high confidence.

Initial candidate widths:

```text
internal wall: 0.52 mm
internal solid: 0.52 mm
sparse infill: 0.58 mm
```

Rationale:

- Run 002 width-only was the cleanest candidate for internal/bulk-heavy models.
- `large_bracket_box`, `speaker_adapter_ring`, and `sloped_surface_torture` showed substantial file-size and travel-move reductions with width-only settings.
- Width-only avoids mixing two optimization axes at once, making it the safest first Stage 1 planning candidate.

Constraints:

- Apply only to hidden/internal/bulk regions.
- Do not apply when thin features may disappear or merge.
- Do not apply when the planner cannot distinguish visible/detail regions from internal/bulk regions.
- Do not use the candidate if path-count changes remove required features in preview.

### Rule C: Treat Layer Height Separately From Width

Layer height should remain a separate optimization axis.

Initial candidate:

```text
layer height: 0.28 mm for non-detail regions only
```

Rationale:

- Run 002 layer-height-only reduced layer count by about 28% on the selected models.
- The Snapmaker `M73` time estimate did not consistently improve.
- Coarser layer height has stronger visible-surface risk than internal line-width changes.

Constraints:

- Do not assume coarser layer height always improves estimated time.
- Use coarse layer height only where Z resolution is not visually important.
- Preserve fine/adaptive Z treatment for visible slopes, top surfaces, text, logos, and cosmetic features.
- Treat slicer-estimated time as a candidate-selection signal, not physical print-time proof.

### Rule D: Keep Combined Mode Experimental

Combined width plus coarse layer height may be useful for large, simple, internal geometry, but it should remain blocked from implementation until visual and physical evidence is stronger.

Rationale:

- Run 002 combined settings often produced the largest file-size and travel-move reductions.
- The same combined settings did not consistently improve Snapmaker `M73` time estimates.
- Combined changes make it harder to identify whether regressions come from XY width, Z height, or their interaction.

Constraints:

- Do not use combined mode as a first implementation target.
- Require visual review before keeping any combined candidate.
- Require proxy physical characterization before claiming process value.
- Keep combined mode out of visible/detail-heavy regions.

## Reject And Caution Cases

Reject or mark a candidate as caution when it affects:

- thin walls;
- small text;
- logos;
- visible top surfaces;
- sloped cosmetic regions;
- detail marks, badges, trim, and other cosmetic faces;
- any region where path-count changes remove features;
- any region where Snapmaker `M73` time estimate gets worse despite reduced path/file metrics;
- any region where preview shows overfill, missing loops, merged features, or unsupported-looking paths.

Run 002 caution examples:

- `led_ring_face`: preserve visible/detail settings; layer-height and combined candidates increased M73 time estimate.
- `sloped_surface_torture`: width-only is promising, but layer-height and combined remain visible-slope caution cases.
- `thin_wall_comb`: aggressive settings require visual review because thin-feature survival is the point of the model.

## Required Future Data Before Implementation

Before implementing these heuristics in planner code, AMP needs:

- Run 002 visual review in Snapmaker Orca preview.
- Secondary viewer review where useful.
- Proxy bead-width physical results on available FDM hardware.
- At least one real functional part test.
- More model variety, including community-submitted geometry.
- Clear pass/fail examples where candidate settings preserve or damage detail.
- U1 validation later for any mixed physical nozzle behavior.

The first implementation after this evidence should still be read-only/debug oriented unless a separate implementation gate explicitly approves behavior changes.

## Candidate Config Values

| Region or axis | Candidate value | Status |
| --- | ---: | --- |
| Visible/detail width | stock / `0.42 mm` | Preserve. |
| Outer wall width | stock / `0.42 mm` | Preserve. |
| Top surface width | stock / `0.42 mm` | Preserve. |
| Internal wall width | `0.52 mm` | First serious Stage 1 candidate. |
| Internal solid width | `0.52 mm` | First serious Stage 1 candidate. |
| Sparse infill width | `0.58 mm` | Aggressive candidate requiring review. |
| Non-detail layer height | `0.28 mm` | Separate candidate axis, not global default. |
| Wide-line proxy | `0.70 mm` | Exploratory/proxy only. Not a U1 0.4 target. |

The `0.70 mm` wide-line proxy comes from available 0.6 mm nozzle proxy testing context. It is not a U1 0.4 mm target, not a production default, and not mixed-nozzle validation.

## Future Planner Interpretation

A future AMP planner should be able to assign a candidate recommendation such as:

```text
preserve_detail
widen_internal
increase_layer_height
candidate_ok
reject_candidate
```

For Stage 1, the first useful behavior candidate is likely:

```text
preserve_detail for visible/top/thin/detail regions
widen_internal for hidden/internal/bulk regions when confidence is high
```

Layer-height and combined recommendations should remain separate until the planner has stronger geometry classification, preview review, and proxy physical evidence.

## Non-Claims

These are candidate heuristics only.

They are not implemented.

They are not production defaults.

They do not prove print strength.

They do not prove surface quality.

They do not prove dimensional accuracy.

They do not validate physical mixed-nozzle behavior.

They do not modify slicer behavior, profiles, G-code generation, Arachne, Flow, LayerRegion, PerimeterGenerator, UI, PrintObject, Snapmaker validation, or CalibUtils.cpp.

