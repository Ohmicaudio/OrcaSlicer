# AMP Stage 1 Profile-Only Benchmark Run 002

## Purpose

Run 002 moves AMP Stage 1 from Run 001's broad stock-versus-effective-width comparison into a focused settings comparison.

The goal is to evaluate whether useful path/time differences are driven more by:

- role-specific line width;
- layer height;
- or the combination of internal width plus coarser Z resolution.

Run 002 remains profile-only unless physical prints are explicitly performed and documented. Visible, top, and detail-critical regions remain conservative.

## Inputs

Run 002 should use:

- `docs/benchmarks/AMP_Run_001_Findings.md`
- `docs/benchmarks/AMP_Stage1_Profile_Only_Run_001_Results.md`
- `docs/benchmarks/AMP_Run_001_Resolution_Cost_Model_Review.md`
- `docs/benchmarks/AMP_Resolution_Cost_Model_Prototype.md`
- `tools/amp_resolution_cost_model.py`
- `docs/U1_Profile_Only_Test_Plan.md`

## Model Set

Use a smaller focused model set from Run 001:

| Model | Reason |
| --- | --- |
| `thin_wall_comb` | Detail/thin-wall guardrail. |
| `large_bracket_box` | Large hidden/internal/bulk region candidate. |
| `speaker_adapter_ring` | Functional ring/wall candidate with strong Run 001 metric movement. |
| `led_ring_face` | Cosmetic/top-detail guardrail. |
| `sloped_surface_torture` | Layer-height and visible-slope risk check. |

Do not add more models to Run 002 unless one of these fails to slice or cannot answer the settings question.

## Comparison Matrix

Each model should be sliced under four candidates:

| Candidate | Purpose |
| --- | --- |
| A. Stock | Baseline stock U1 0.4 profile. |
| B. Width-only | Isolate role-specific internal width changes. |
| C. Layer-height-only | Isolate Z-resolution and layer-count effects. |
| D. Combined | Test whether internal width plus coarser layer height compounds savings without obvious preview regression. |

## Candidate A: Stock

Use the stock Snapmaker U1 0.4 mm process profile:

```text
resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json
```

Expected baseline:

- stock line-width behavior;
- stock `0.20 mm` layer height;
- stock visible/detail treatment.

## Candidate B: Width-Only

Intent:

- isolate the effect of role-specific width changes;
- keep layer height stock-like.

Settings:

```text
wall_generator = arachne
outer_wall_line_width = 0.42
top_surface_line_width = 0.42
support_line_width = 0.42
inner_wall_line_width = 0.52
internal_solid_infill_line_width = 0.52
sparse_infill_line_width = 0.58
layer_height = 0.20
```

Expected candidate behavior:

- visible/detail regions should stay close to stock in preview;
- internal walls and sparse/internal regions may show fewer/wider paths;
- this is the first serious Stage 1 software-only candidate.

## Candidate C: Layer-Height-Only

Intent:

- isolate layer-height effects;
- keep line widths stock-like.

Settings:

```text
outer_wall_line_width = stock-like / 0.42 where explicit
top_surface_line_width = stock-like / 0.42 where explicit
support_line_width = stock-like / 0.42 where explicit
inner_wall_line_width = stock-like
internal_solid_infill_line_width = stock-like
sparse_infill_line_width = stock-like
layer_height = 0.28 where appropriate
```

Guardrail:

- preserve fine or adaptive layer heights where visual/top/detail risk exists;
- do not treat coarse layer height as acceptable on visible slopes or cosmetic top regions without visual review.

## Candidate D: Combined

Intent:

- test combined motion/resolution savings;
- apply width and layer-height changes only where low-detail assumptions are reasonable.

Settings:

```text
wall_generator = arachne
outer_wall_line_width = 0.42
top_surface_line_width = 0.42
support_line_width = 0.42
inner_wall_line_width = 0.52
internal_solid_infill_line_width = 0.52
sparse_infill_line_width = 0.58
layer_height = 0.28 for non-detail regions
```

Guardrail:

- visible/top/detail regions remain conservative;
- if the CLI/profile path cannot express region-local layer-height behavior yet, document the limitation and run the closest reproducible profile-only approximation.

## Optional Proxy Wide-Line Reference

`0.70 mm` may be used only as a proxy observation from available 0.6 mm nozzle testing.

It must be clearly labeled:

```text
proxy wide-line reference only
not a U1 default
not a U1 0.4 mm profile target
not validated AMP behavior
not mixed-nozzle validation
```

Do not include `0.70 mm` in the official U1 0.4 profile comparison unless it is separated as exploratory/proxy-only.

## Measurements

For each model and candidate, record:

- slicing success/failure;
- slicer warnings/errors;
- estimated print time if available;
- filament usage if available;
- G-code file size;
- parsed positive E;
- travel moves;
- extrusion moves;
- layer count if available;
- role/path comment counts if available;
- visual preview notes;
- resolution risk flag;
- candidate recommendation.

For deltas, compare all candidates against Stock:

```text
Stock
vs.
Width-only
vs.
Layer-height-only
vs.
Combined
```

Separate stock-only/candidate-only G-code exports should be used for metrics. Same-plate outputs may be generated for visual comparison, but they should not be mixed into metric tables unless clearly labeled.

## Visual Review Requirements

Required checks:

| Model | Required visual check |
| --- | --- |
| `thin_wall_comb` | Thin features remain visible and do not overfill or disappear. |
| `large_bracket_box` | Savings occur in internal/bulk areas, not by degrading exterior loops. |
| `speaker_adapter_ring` | Inner/outer ring loops, holes, and mounting features remain plausible. |
| `led_ring_face` | Cosmetic face, LED openings, and small detail marks remain stock-like. |
| `sloped_surface_torture` | Coarse layer height does not create unacceptable visible stepping in preview. |

Use Snapmaker Orca preview first. Use Prusa G-code Viewer or another viewer as a secondary check where useful.

## Decision Outputs

For each model, Run 002 should report:

- best conservative candidate;
- most aggressive candidate worth keeping;
- rejected candidate, if any;
- what requires physical validation;
- whether Run 003 should focus on width, layer height, or combined settings.

Expected high-level decisions:

- `thin_wall_comb`: likely preserve detail or reject aggressive candidates.
- `large_bracket_box`: likely strongest internal/bulk candidate.
- `speaker_adapter_ring`: likely width-first candidate with physical fit validation needed.
- `led_ring_face`: likely preserve visible/top detail.
- `sloped_surface_torture`: likely layer-height caution case.

## Pass Criteria

Run 002 passes if:

- all selected models slice under Stock and at least two candidate profiles;
- metric deltas are separated by candidate type;
- visual/top/detail guardrails are explicitly reviewed;
- candidate recommendations are documented without claiming physical performance;
- no production profiles are modified;
- no slicer behavior is modified.

## Fail Criteria

Run 002 fails or needs revision if:

- candidate settings cannot be reproduced from documented CLI/profile inputs;
- visible/top/detail features disappear in preview;
- line-width and layer-height effects cannot be separated;
- results imply physical performance without hardware evidence;
- generated artifacts are mixed into committed docs without clear summary and filtering.

## Required Non-Claims

Run 002 remains profile-only unless physical prints are performed and recorded.

Preview/G-code does not prove print strength.

Preview/G-code does not prove surface quality.

Run 002 does not validate physical mixed-nozzle behavior.

Bambu/proxy tests do not validate U1 behavior.

Estimated print time is slicer/G-code-derived unless measured on real hardware.

## Next Step

After this plan is committed, run Run 002 with the local hardened Snapmaker Orca CLI and generate metrics for:

```text
Stock
Width-only
Layer-height-only
Combined
```

Public updates should wait until Run 002 has results.

