# AMP Future Scope Roadmap

## Core Philosophy

Adaptive Manufacturing Planner is a resolution-allocation planning layer for FDM/FFF slicing.

Preferred shorthand:

```text
Spend resolution only where it earns its keep.
```

The goal is the smallest controlled repeatable detail in X/Y/Z where that detail is needed.

AMP is not speed-first. It is not U1-only. It is not mixed-nozzle-only. The planner should eventually decide where visible detail, top-surface quality, structural regions, support-critical areas, and hidden internal bulk need different manufacturing treatment.

## Hardware Tiers

### Tier 1: Single-Nozzle FDM/FFF

Tier 1 uses existing slicer mechanisms and does not require toolchanging hardware.

Potential capabilities:

- role-specific line width;
- adaptive bead width;
- adaptive layer height;
- visible-surface preservation;
- internal/bulk region planning;
- profile-only Arachne experiments.

This tier is useful immediately because it can test resolution allocation on ordinary printers before physical tool assignment exists.

### Tier 2: Multi-Material / IDEX / Support-Tool Systems

Tier 2 adds material, support, and color/surface assignment without assuming different physical nozzle diameters.

Potential capabilities:

- material assignment;
- support interface assignment;
- color/detail surface assignment;
- soluble or breakaway support planning;
- visible-surface color/detail planning.

This tier does not require a mixed-nozzle assumption.

### Tier 3: Toolchanger / Mixed-Nozzle Systems

Tier 3 adds physical tool/nozzle assignment.

Potential capabilities:

- small nozzle for visible detail;
- larger nozzle for hidden/internal/bulk regions;
- toolchange and purge cost modeling;
- hardware-specific validation;
- bonding, seam, and calibration risk handling.

This tier is hardware-specific and remains blocked from behavior claims until real validation exists.

## Current Completed State

- Public AMP branch exists: `u1-adaptive-nozzle-strategy`.
- Snapmaker Innovation Fund submission is recorded.
- Snapmaker forum and Reddit promotion started.
- Run 001 broad profile-only comparison completed.
- Run 001 visual review completed.
- Run 002 Stock vs Width-only vs Layer-height-only vs Combined comparison completed.
- Stage 1 heuristic candidates are documented.
- Proxy bead-width characterization package exists.
- Visual resolution enhancement track exists.
- Snapmaker CLI hardening PRs exist:
  - https://github.com/Snapmaker/OrcaSlicer/pull/560
  - https://github.com/Snapmaker/OrcaSlicer/pull/561
  - https://github.com/Snapmaker/OrcaSlicer/pull/562
- No production slicer path consumes AMP.
- No production profile defaults are changed.
- No G-code behavior change has been made for AMP.

## Stage 1 Roadmap: Software/Profile Resolution Allocation

### Run 001: Broad Profile-Only Comparison

Deliverable:

- Stock U1 0.4 profile vs experimental effective-width/Arachne profile across generated benchmark models.

Pass/fail criteria:

- Stock and experimental profiles slice.
- G-code metrics are recorded.
- Same-plate visual comparison is available where useful.
- No slicer behavior changes are required.

Decision supported:

- Whether role-specific width changes are worth isolating.

Blocked:

- Physical quality, strength, bonding, and mixed-nozzle claims.

Status:

- Completed.

### Run 002: Candidate Axis Split

Deliverable:

- Stock vs Width-only vs Layer-height-only vs Combined on focused model set.

Pass/fail criteria:

- Candidate effects are separated.
- Metrics include layer count, file size, M73 estimate, moves, and positive E.
- Results do not claim physical performance.

Decision supported:

- Width-only is the first conservative Stage 1 candidate.
- Layer height is a separate axis.
- Combined mode remains experimental.

Blocked:

- Behavior integration and production defaults.

Status:

- Completed.

### Run 003: Detail-Rich Real/Fixture Validation

Deliverable:

- A detail-rich product-style fixture or actual Ohmic part sliced as Stock vs Width-only.

Pass/fail criteria:

- The model includes visible/cosmetic detail and internal/bulk regions.
- Width-only preserves visible/detail regions in preview.
- Internal/bulk path burden decreases or changes explainably.
- No physical claims are made from preview alone.

Decision supported:

- Whether `0.52` internal width should carry forward as the first Stage 1 heuristic candidate.

Blocked:

- Any candidate that damages visible/detail regions.
- Any move to implementation without visual and physical review.

Status:

- In progress with `AMP_Detail_Rich_Width_Only_Validation_001`.

### Proxy Physical Measurements

Deliverable:

- Physical coupon or part measurements on available FDM hardware.

Pass/fail criteria:

- Measurements record actual material, printer, nozzle, line width, visible artifacts, and dimensional notes.
- Proxy results are not described as U1 mixed-nozzle validation.

Decision supported:

- Whether candidate line widths are physically plausible enough to keep testing.

Blocked:

- U1-specific conclusions.

Status:

- Package exists; first observations are early/proxy only.

### First Conservative Heuristic Candidate

Deliverable:

- Preserve visible/detail regions.
- Consider `0.52` internal wall/internal solid where confidence is high.
- Treat `0.58` sparse infill as aggressive.
- Keep `0.28` layer height separate.

Pass/fail criteria:

- Candidate survives Run 003 visual review and at least one physical/proxy check.

Decision supported:

- Whether read-only planner recommendations should start with width-only internal/bulk logic.

Blocked:

- Behavior-changing slicing.

Status:

- Documented, not implemented.

### Future Read-Only Observation

Deliverable:

- Serial deterministic observation data feeding sidecar/debug artifacts.

Pass/fail criteria:

- No production output changes.
- No writes inside parallel perimeter loops.
- Debug output remains developer-only and deterministic.

Decision supported:

- Whether the planner can classify regions safely before influencing slicing.

Blocked:

- Geometry scoring and G-code changes.

Status:

- Designed at value-type/debug level only.

### Future Planner Recommendation Output

Deliverable:

- Read-only recommendation output such as `preserve_detail`, `widen_internal`, or `reject_candidate`.

Pass/fail criteria:

- Recommendations are inspectable.
- Stock slicing remains equivalent when behavior is disabled.

Decision supported:

- Whether AMP recommendations match preview and physical evidence.

Blocked:

- Any direct Arachne/Flow/G-code consumption.

Status:

- Future work.

## Stage 2 Roadmap: Physical Mixed-Nozzle Validation

Snapmaker support constraints currently shape Stage 2:

- Touchscreen-started prints use the first G-code `nozzle_diameter` value as the single authoritative validation value for used toolheads.
- The printer stores nozzle size per physical toolhead.
- Load/unload behavior adapts to configured toolhead nozzle size.
- Printing follows G-code strictly after the job starts.
- Snapmaker plans future mixed nozzle-size support.
- Fluidd-only validation may be possible later because the touchscreen nozzle-size verification path is not used.
- Touchscreen-compatible mixed-nozzle support is blocked pending Snapmaker's future metadata and logical/physical tool mapping support.

Stage 2A:

- Fluidd-only experimental validation, developer-only, after U1 hardware access.

Stage 2B:

- Touchscreen-compatible mixed-nozzle validation, blocked until Snapmaker provides or documents compatible metadata/tool mapping.

Non-negotiable constraints:

- Do not bypass Snapmaker validation.
- Do not claim mixed physical nozzle support from Stage 1 profile-only evidence.
- Do not use 0.2 mm nozzles with PETG-CF, PETG-GF, Wood, or TPU in future U1 validation.

## Surface Color / Visual Resolution Roadmap

The same visibility/detail classification can support a future visual-resolution track:

- outer-skin color planning;
- FullSpectrum-style visible-surface use cases;
- visible logo/text/badge/trim regions;
- future local-Z painted surface planning;
- separation of visual resolution from mechanical resolution.

This track should remain explicit about limits:

- no claims of pigment-style color mixing;
- no claims of calibrated color matching;
- no surface-color G-code behavior until a separate validation path exists;
- no confusion between optical blending and physical pigment mixing.

## Actual Next 5 Technical Decisions

1. Whether `0.52` internal wall/internal solid is the first Stage 1 candidate.
   - Current leaning: yes, pending detail-rich validation and physical/proxy review.
2. Whether `0.58` sparse infill remains aggressive.
   - Current leaning: yes; keep as review-required rather than default.
3. Whether `0.28` layer height should remain separate from width planning.
   - Current leaning: yes; Run 002 showed layer count reductions but inconsistent M73 estimates.
4. Whether combined width plus coarse layer height remains blocked.
   - Current leaning: yes; combined is powerful but too coupled and too risky for visible/detail regions.
5. What Run 003 must prove.
   - It must show that width-only preserves visible/detail regions while reducing or simplifying internal/bulk path burden on a detail-rich model.

## Explicit Non-Goals

- No Arachne integration yet.
- No Flow integration yet.
- No LayerRegion integration yet.
- No G-code behavior change yet.
- No physical mixed-nozzle output yet.
- No touchscreen mixed-nozzle support yet.
- No safety bypass.
- No production profile defaults.
- No claim of print strength improvement.
- No claim of surface-quality improvement.
- No claim of U1 mixed physical nozzle behavior.
