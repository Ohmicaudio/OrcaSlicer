# AMP Real-Part Width-Only Validation 001

## Purpose

This validation pass tests the first conservative Stage 1 heuristic candidate on one real or realistic detail-bearing functional part:

```text
Stock
vs.
Width-only internal widening
```

The goal is to ask one practical question:

```text
Does width-only internal widening preserve visible/detail surfaces while reducing or simplifying internal path burden on a real-ish, product-style part?
```

This is the next evidence step after Run 002. It is intentionally narrower than another synthetic benchmark matrix.

Basic or plain generated geometry is no longer a decision-making target for AMP. Basic synthetic models are useful for smoke testing CLI slicing, export, metrics scripts, and crash fixes. They are not sufficient for deciding whether AMP preserves resolution where it matters.

The validation target must include both:

```text
visible/cosmetic detail to protect
internal/bulk geometry where wider paths might help
```

If a model has only bulk, it cannot test detail preservation. If it has only detail and no bulk, it cannot test resolution reallocation.

## Scope

This pass is limited to Stage 1 profile-only validation unless physical prints are explicitly performed and recorded.

Allowed:

- stock-vs-width-only slicing comparison;
- visual preview review;
- G-code metrics comparison;
- optional physical print notes if the part is printed.

Not allowed in this pass:

- layer-height changes;
- combined width plus layer-height changes;
- geometry scoring implementation;
- Arachne, Flow, LayerRegion, PerimeterGenerator, G-code generation, UI, PrintObject, Snapmaker validation, or CalibUtils.cpp changes;
- physical mixed-nozzle behavior.

## Candidate Strategy

The width-only candidate preserves visible/detail/top settings and widens only internal/bulk roles.

Candidate values:

```text
outer wall: stock / 0.42 mm
top surface: stock / 0.42 mm
support: stock / 0.42 mm
internal wall: 0.52 mm
internal solid: 0.52 mm
sparse infill: 0.58 mm, only if the part is bulk/internal enough
layer height: stock
```

This is based on the Run 002 decision that width-only is the cleanest first Stage 1 candidate for internal/bulk regions, while layer-height and combined modes need more visual and physical evidence.

## Model Target Requirements

Use detail-bearing geometry with actual AMP decision value.

The selected model must include most of:

- outer cosmetic face;
- raised or recessed text/logo surrogate;
- small grooves or pinstripes;
- mounting holes;
- counterbores or bosses;
- curved or chamfered surface;
- thin decorative detail;
- thicker hidden backside or internal bulk.

Preferred target:

```text
actual Ohmic speaker ring / LED ring / badge / trim part with visible detail
```

Fallback target:

```text
AMP detail-ring validation fixture
```

The fallback fixture must not be a plain ring. It should be intentionally designed to contain detail to preserve and bulk to optimize.

## Model Candidates

Use one of these real or realistic functional parts:

| Candidate | Why it is useful |
| --- | --- |
| Actual Ohmic speaker ring with logo/text/detail | Best mix of cosmetic face, holes, ring walls, backside bulk, and visible detail. |
| LED speaker ring face | Cosmetic front surface, openings, small features, visible/detail guardrail. |
| Amp bracket with holes, bosses, and top markings | Functional shape with fit features, exterior walls, top detail, and bulk regions. |
| Trim/logo badge | Detail/cosmetic guardrail with text, logo, face quality, and edge quality. |
| AMP detail-ring validation fixture | Fallback only; must include text/logo surrogate, grooves, holes, bosses/counterbores, chamfers, and backside bulk. |

Preferred first pick:

```text
detail-rich speaker ring or LED ring face
```

Reason:

- Run 002 showed width-only as the best conservative candidate for `speaker_adapter_ring`.
- A detail-rich ring is functional enough to make fit and hole quality meaningful.
- A cosmetic/detail face plus backside or internal bulk can test whether AMP's preserve-vs-widen split makes practical sense.
- A plain/basic ring is not enough because it does not test visible detail preservation.

## Chosen Part Record

Fill this section when the part is selected.

| Field | Value |
| --- | --- |
| Model name | TBD |
| Source path | TBD |
| Why this part is useful | TBD |
| Visible/detail features present | TBD |
| Internal/bulk regions present | TBD |
| Reason this is not just a smoke-test model | TBD |
| Material, if printed | TBD |
| Printer, if printed | TBD |
| Nozzle, if printed | TBD |
| Slicer/build used | TBD |

## Visible And Detail Surfaces

Record:

- exterior walls;
- front/cosmetic face;
- top surfaces;
- text, logo, marks, or trim features;
- grooves, pinstripes, or other small cosmetic details;
- holes and mounting features;
- counterbores, bosses, or fit-critical reliefs;
- curved or chamfered cosmetic surfaces;
- fit-critical faces.

These areas should remain comparable to stock in preview before any physical print is trusted.

## Internal And Bulk Regions

Record:

- internal walls;
- internal solid regions;
- sparse infill regions;
- thick ring or bracket body sections;
- areas hidden after assembly or not cosmetically important.

These areas are the only intended target for the width-only candidate.

## Slicing Variants

### A. Stock

Use the stock Snapmaker U1 0.4 profile or the equivalent printer/profile appropriate for the physical proxy printer if this is not being sliced for U1 preview.

Record:

- G-code path;
- estimated time if available;
- file size;
- layer count;
- extrusion moves;
- travel moves;
- positive E total;
- warnings/errors.

### B. Width-Only Conservative

Use the width-only candidate:

```text
wall_generator: arachne
outer_wall_line_width: 0.42
top_surface_line_width: 0.42
support_line_width: 0.42
inner_wall_line_width: 0.52
internal_solid_infill_line_width: 0.52
sparse_infill_line_width: 0.58, if appropriate for the part
layer_height: stock
```

Record the same metrics as stock.

## Metrics Table Template

| Metric | Stock | Width-only | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Estimated time | TBD | TBD | TBD | Slicer/G-code-derived unless printed. |
| Actual print time, if printed | TBD | TBD | TBD | Optional physical result. |
| G-code file size | TBD | TBD | TBD | Profile-only metric. |
| Layer count | TBD | TBD | TBD | Should remain stock-like for width-only. |
| Extrusion moves | TBD | TBD | TBD | Inspect if increased. |
| Travel moves | TBD | TBD | TBD | Useful path-burden signal. |
| Positive E total | TBD | TBD | TBD | G-code parser metric only. |
| Filament use, if available | TBD | TBD | TBD | Slicer/G-code-derived unless weighed. |

## Visual Preview Checklist

Review stock and width-only in Snapmaker Orca preview first.

Check:

- exterior/visible detail remains comparable;
- no missing visible loops;
- no obvious top-surface degradation;
- holes remain plausible;
- fit-critical faces remain plausible;
- internal path burden decreases or remains explainably different;
- sparse infill changes do not affect visible/cosmetic surfaces;
- no obvious overfill, merged thin features, or removed features.

Use Prusa G-code Viewer or another viewer as a secondary check if useful.

## Physical Print Notes

If printed, record:

- printer;
- nozzle;
- material;
- layer height;
- slicer/profile;
- actual print time;
- visible outer wall quality;
- hole quality;
- top surface;
- fitment;
- material use or part weight, if measured;
- photos status;
- any failure or artifact.

Physical notes should be written as observations, not broad claims.

## Pass Criteria

This pass is favorable if:

- the selected target contains both visible/detail features and internal/bulk regions;
- exterior/visible detail remains comparable in preview;
- no visible loops are missing;
- no obvious top-surface degradation appears in preview;
- holes and fit-critical features remain plausible;
- internal path burden decreases or remains explainably different;
- any physical print, if performed, does not reveal obvious visible/detail regression;
- no unsupported claims are made.

## Fail Or Caution Criteria

Mark the candidate as fail or caution if:

- the selected model is too plain to answer the AMP preserve-vs-widen question;
- visible loops disappear;
- top/cosmetic surfaces become visibly worse in preview;
- holes or fit features appear compromised;
- extrusion moves or positive E increase without a clear explanation;
- sparse infill changes affect visible/cosmetic regions;
- physical print shows obvious fit, surface, or feature problems;
- results are used to imply strength, surface quality, or mixed-nozzle behavior without evidence.

## Required Non-Claims

This does not prove strength.

This does not prove final surface quality.

This does not prove dimensional accuracy.

This does not validate physical mixed-nozzle behavior.

This is still Stage 1 profile-only validation unless physically printed and recorded.

Preview/G-code metrics are planning evidence only.

## Next Step After This Pass

If stock-vs-width-only looks favorable on one real part, repeat on one second real part with a different risk profile:

```text
functional ring/bracket
then cosmetic face/badge
```

Do not move to geometry scoring, Flow integration, Arachne integration, LayerRegion consumption, G-code behavior changes, or mixed-nozzle output from this pass alone.
