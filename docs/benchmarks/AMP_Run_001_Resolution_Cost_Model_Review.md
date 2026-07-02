# AMP Run 001 Resolution Cost Model Review

## Purpose

This review applies the offline AMP resolution-allocation cost model to practical Stage 1 scenarios from Run 001.

The goal is to turn Run 001 evidence into a settings decision table:

- where AMP should preserve detail;
- where wider internal line widths are worth testing;
- where larger layer height may matter as much as line width;
- where risk is too high for a Stage 1 candidate.

This model is an offline estimator. It does not modify slicer behavior. It does not prove print quality. It does not prove strength. It does not validate U1 mixed-nozzle behavior. It informs candidate selection only.

## Inputs

This review used:

- `tools/amp_resolution_cost_model.py`
- `docs/benchmarks/AMP_Run_001_Findings.md`
- `docs/benchmarks/AMP_Stage1_Profile_Only_Run_001_Results.md`
- `docs/benchmarks/AMP_Resolution_Cost_Model_Prototype.md`
- `docs/U1_Profile_Only_Test_Plan.md`

The local estimator scenario JSON and generated CSV/Markdown outputs were written under:

```text
outputs/amp_resolution_cost_model/run_001_review/
```

Those files are generated local analysis artifacts and are not committed.

## Candidate Settings

| Candidate | Line width | Layer height | Intended use |
| --- | ---: | ---: | --- |
| Stock U1 0.4 baseline | 0.42 mm | 0.20 mm | Baseline detail-preserving profile behavior. |
| Conservative internal candidate | 0.52 mm | 0.20 mm | First serious internal-width candidate for hidden/internal regions. |
| Aggressive internal/infill candidate | 0.58 mm | 0.28 mm where detail risk is low | Higher-risk candidate combining wider paths with coarser Z. |
| Wide-nozzle proxy reference | 0.70 mm | 0.28 mm | Proxy-only reference from available 0.6 mm nozzle testing, not a U1 default or validated AMP target. |

The current Run 001 experimental profile already uses:

```text
outer_wall_line_width = 0.42
top_surface_line_width = 0.42
support_line_width = 0.42
inner_wall_line_width = 0.52
internal_solid_infill_line_width = 0.52
sparse_infill_line_width = 0.58
```

## Estimator Output

The table below is produced from geometry-like scenario inputs. It is not a replacement for slicer preview, G-code inspection, or physical testing.

| Scenario | Candidate | Stock paths | Candidate paths | Estimated time delta | Risk flag | Recommendation |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Visible logo/text region | preserve 0.42 / 0.20 | 3 | 3 | 0.0% | `detail_visibility` | `preserve_detail` |
| Visible logo/text region | aggressive 0.52 / 0.20 | 3 | 3 | 0.0% | `poor_residual_width,detail_visibility` | `reject_candidate` |
| Thin-wall detail region | preserve 0.42 / 0.20 | 2 | 2 | 0.0% | `detail_visibility` | `preserve_detail` |
| Thin-wall detail region | aggressive 0.52 / 0.20 | 2 | 2 | 0.0% | `detail_visibility` | `preserve_detail` |
| Hidden internal wall | conservative 0.52 / 0.20 | 7 | 5 | 28.6% | `none` | `widen_internal` |
| Hidden internal wall | aggressive 0.58 / 0.28 | 7 | 5 | 22.7% | `flow_limited` | `widen_internal` |
| Large infill/bulk region | conservative 0.52 / 0.20 | 20 | 16 | 20.0% | `none` | `widen_internal` |
| Large infill/bulk region | aggressive 0.58 / 0.28 | 20 | 14 | 24.2% | `flow_limited` | `widen_internal` |
| Speaker adapter ring wall | conservative 0.52 / 0.20 | 12 | 10 | 16.7% | `none` | `widen_internal` |
| Speaker adapter ring wall | aggressive 0.58 / 0.28 | 12 | 9 | 18.8% | `flow_limited` | `widen_internal` |
| LED ring face | preserve 0.42 / 0.20 | 5 | 5 | 0.0% | `detail_visibility,top_surface_conservative` | `preserve_detail` |
| LED ring face | aggressive 0.52 / 0.28 | 5 | 4 | 20.0% | `detail_visibility,top_surface_conservative` | `preserve_detail` |
| Sloped/top-detail region | preserve 0.42 / 0.20 | 6 | 6 | 0.0% | `poor_residual_width,detail_visibility,top_surface_conservative` | `reject_candidate` |
| Sloped/top-detail region | aggressive 0.52 / 0.28 | 6 | 5 | 16.7% | `poor_residual_width,detail_visibility,top_surface_conservative` | `reject_candidate` |
| Hidden bulk reference | proxy 0.70 / 0.28 | 20 | 12 | 40.0% | `none` | `widen_internal` |

The `0.70` row is a proxy wide-line reference only. It is not a U1 default, not a current AMP target, and not validated mixed-nozzle behavior.

## Decision Table

| Run 001 category | Decision | Reason | Visual check required | Physical validation required |
| --- | --- | --- | --- | --- |
| Visible logo/text region | Preserve stock detail settings. | Visibility and detail-critical flags dominate; widening has no useful estimated time benefit. | Text edges, stroke fill, top/bottom edge cleanup. | Surface readability and edge quality on real prints. |
| Thin-wall detail region | Preserve detail; do not widen by default. | Thin/detail regions offer little or no path-count benefit and are sensitive to residual wall behavior. | Thin feature survival, gap/overfill, missing strokes. | Dimensional survival of thin walls and small features. |
| Hidden internal wall region | Test 0.52 first. | Conservative internal width gives a useful path-count reduction with no model risk flag in the estimator. | Confirm exterior walls remain stock-like and reduction is internal. | Wall bonding, dimensional effect, and overfill on hidden/internal structures. |
| Large infill/bulk region | Strong Stage 1 candidate. | Both 0.52 and 0.58/coarse-Z candidates estimate useful time reduction; aggressive row is flow-limited. | Confirm no cosmetic surface roles are accidentally widened. | Flow stability, infill bonding, and any heat/drag artifacts. |
| Speaker adapter ring wall | Test 0.52 first; keep 0.58 as follow-up. | Ring walls show useful estimated path-count reduction and matched Run 001's large parsed positive-E reduction. | Inner/outer ring loops, mounting features, hole/edge quality. | Ring dimensions, fit, wall bonding, and deformation. |
| LED ring face | Preserve visible/top detail settings. | Even when the model estimates time reduction, visibility and top-surface risk override it. | Cosmetic face, LED hole edges, raised/engraved marks. | Surface appearance and small feature readability. |
| Sloped surface/top-detail region | Reject wider/coarser Stage 1 candidate until further review. | Top/slope/detail risk dominates; layer-height changes may visibly affect surface quality. | Sloped surface stepping, topmost layer quality, contour artifacts. | Real surface finish and layer-stepping comparison. |

## Required Conclusions

- Wider settings should not be used for visible logo/text/top-detail regions in Stage 1.
- Hidden/internal/bulk regions are the best Stage 1 candidates.
- Layer height is as important as line width for time reduction.
- `0.52 mm` is the first serious internal-width candidate.
- `0.58 mm` is an aggressive candidate requiring visual and physical checks.
- `0.70 mm` is a proxy measured wide-line reference, not a U1 default or validated AMP target.

## Run 002 Implications

Run 002 should split the experiment by mechanism instead of only changing line width:

| Run | Purpose | Candidate comparison |
| --- | --- | --- |
| Run 002A | Layer-height-first test | Stock versus coarse/adaptive layer height with conservative line widths. |
| Run 002B | Internal-width-first test | Stock versus 0.52 internal-width candidate with stock-like visible surfaces. |
| Run 002C | Combined test | Stock versus internal width plus coarse/adaptive layer height only in low-visibility regions. |

Recommended Run 002 models:

- `thin_wall_comb`
- `speaker_adapter_ring`
- `led_ring_face`
- `large_bracket_box`
- `sloped_surface_torture`

The comparison should become:

```text
Stock
vs.
Width-only candidate
vs.
Layer-height-only candidate
vs.
Combined candidate
```

## Non-Claims

This review cannot claim:

- print quality improvement;
- strength improvement;
- dimensional accuracy improvement;
- bonding improvement;
- U1 mixed-nozzle behavior;
- physical mixed-nozzle behavior;
- touchscreen or Fluidd mixed-nozzle readiness.

The model informs candidate selection only. Any behavior-changing AMP work remains blocked behind explicit design, tests, visual review, and hardware validation.

