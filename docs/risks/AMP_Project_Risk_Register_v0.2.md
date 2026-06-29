# AMP Project Risk Register v0.2

**Document ID:** `docs/risks/AMP_Project_Risk_Register_v0.2.md`
**Project:** Project Atlas / Adaptive Manufacturing Planner (AMP)
**Status:** Under Review

## 1. Executive Summary And Core Guardrail

This document details the engineering risk register across all three planned development stages of the Adaptive Manufacturing Planner. Current architectural findings show that `PrintObject::make_perimeters()` distributes layer work through `tbb::parallel_for`, so AMP controls must prioritize thread safety, non-destructive observation, and upstream alignment.

### Mandatory Infrastructure Guardrail

No physical mixed-nozzle implementation for Stage 2 will execute until:

1. Physical Snapmaker U1 hardware access is secured for localized coordinate and kinematic testing.
2. The U1 hardware-side nozzle state and validation behavior is documented through Snapmaker guidance, public interfaces, or observed development logs.
3. Kinematic tool-change overhead and volumetric wipe-tower costs can be empirically modeled.
4. Stage 1 demonstrates stable disabled/no-op behavior and benchmark results across the agreed regression suite.

## 2. Risk Matrix Overview

| Risk ID | Category | Stage Affected | Severity | Likelihood | Core Mitigation |
| --- | --- | --- | --- | --- | --- |
| RSK-01 | Slicing correctness and concurrency | Stage 1, 2, 3 | Critical | High | Sidecar cache populated by a serial pre-pass. |
| RSK-02 | Arachne edge cases | Stage 1 | High | Medium | Constrain scaling to initial conservative bounds before broader testing. |
| RSK-03 | Flow and overfill boundaries | Stage 1, 2 | High | High | Validate transitions with volumetric cross-section checks. |
| RSK-04 | Thin-feature loss | Stage 1 | Medium | Medium | Apply hard minimum feature thresholds before region merging. |
| RSK-05 | Preview vs. real mismatch | Stage 1, 2 | High | Low | Use four explicit validation levels and normalized G-code parity where applicable. |
| RSK-06 | Tool-change overhead | Stage 2, 3 | Medium | High | Model travel, purge, wipe, and heating costs before assigning alternate tools. |
| RSK-07 | Purge and wipe behavior | Stage 2 | High | High | Treat purge/wipe behavior as a Stage 2 research blocker. |
| RSK-08 | Nozzle mismatch validation | Stage 2 | Critical | High | Preserve core hardware interlocks and Snapmaker validation paths. |
| RSK-09 | User misunderstanding | Stage 1, 2 | Medium | Medium | Hide experimental options under developer-only configuration visibility such as `comDevelop`. |
| RSK-10 | Upstream maintainability | Stage 1, 2, 3 | Medium | High | Keep planning/scoring/cache code isolated and core edits append-only. |
| RSK-11 | Benchmark validity | Stage 1, 2 | Medium | Medium | Pair synthetic stress models with functional automotive components. |
| RSK-12 | Lack of U1 hardware | Stage 2 | High | Critical | Keep physical mixed-nozzle behavior disabled and blocked until hardware validation. |
| RSK-13 | Project scope creep | Stage 1, 2, 3 | Medium | High | Keep milestones bounded and document current non-goals. |

## 3. Granular Risk Breakdown

### 3.1 Slicing Correctness And Concurrency (RSK-01)

**Risk description:** `PrintObject::make_perimeters()` uses `tbb::parallel_for` to process layer work. Writing directly to shared planner maps, debug buffers, or sidecar data from inside that parallel loop would introduce race conditions and non-repeatable output.

**Stages affected:** Stage 1, 2, 3

**Concurrency guardrails:**

- No shared mutable planner or debug writes are permitted inside the `PrintObject::make_perimeters()` parallel loop.
- No shared mutable planner or debug writes are permitted inside `LayerRegion::make_perimeters()`.
- The first AMP prototype must process geometric observations through a deterministic serial pre-pass, or use explicit thread-local accumulation with a deterministic merge pass.
- PrintObject-owned sidecar data or a PrintObject-scoped cache is the first safe owner for read-only planner observations.

**Validation method:** Run repeated regression slices on identical complex meshes and compare normalized G-code output. Add ThreadSanitizer coverage where toolchain support exists.

### 3.2 Arachne Edge Cases (RSK-02)

**Risk description:** Aggressive width targets can push Arachne into difficult center-line path distribution cases, including path intersections, unstable transitions, or missing thin-wall behavior.

**Stage affected:** Stage 1

**Mitigation:** Constrain scaling parameters to conservative verified profile baselines before exposing broader parametric ranges.

**Validation method:** Slice synthetic stress-test templates containing thin features, stepped width targets, narrow text, small holes, and sharp curvature transitions.

### 3.3 Flow And Overfill Boundaries (RSK-03)

**Risk description:** Transitions between stock-width outer regions and wider internal regions can create overfill, poor seam behavior, or weak bonding if only 2D offsets are considered.

**Stages affected:** Stage 1, 2

**Mitigation:** Evaluate transitions using volumetric cross-section checks and conservative fallback rules. Do not allow planner recommendations to bypass existing flow limits.

**Validation method:** Compare previewed path geometry, G-code role/width metadata where available, and later physical cross-sections once hardware validation begins.

### 3.4 Thin-Feature Loss (RSK-04)

**Risk description:** Region classification may misclassify small decorative or mating elements as broad internal regions, causing lost details or dimensional errors.

**Stage affected:** Stage 1

**Mitigation:** Apply hard minimum feature-size thresholds and low-confidence fallback. Features below safe baseline limits must use stock rendering.

**Validation method:** Use synthetic models with text, pins, slots, and holes spanning 0.1 mm to 2.0 mm.

### 3.5 Preview Vs. Real Print Mismatch (RSK-05)

**Risk description:** Preview and G-code inspection can reveal path differences but cannot prove real print strength, surface quality, dimensional accuracy, bonding, purge reliability, or mixed-nozzle success.

**Stages affected:** Stage 1, 2

**Mitigation strategy: four validation levels**

1. **Level 1: Disabled / no-op planner.** Generated output must remain equivalent to stock behavior, with any unavoidable metadata differences explicitly enumerated.
2. **Level 2: Profile-only experiment.** G-code changes are expected but must map directly to declared profile settings, existing role-specific line-width options, and Arachne behavior.
3. **Level 3: Read-only AMP prototype.** Slicer outputs must remain unchanged. AMP generates decoupled debug, region, and scoring artifacts only.
4. **Level 4: Future behavior-changing AMP.** Active G-code or toolpath changes require explicit review, regression coverage, and rollback/fallback behavior.

### 3.6 Tool-Change Overhead (RSK-06)

**Risk description:** Tool or nozzle changes can cost more time than they save if travel, purge, wipe, heating, or synchronization overhead is ignored.

**Stages affected:** Stage 2, 3

**Mitigation:** Add a future cost model that accounts for physical travel, purge volume, wipe behavior, and minimum useful region size. The planner must fall back to single-nozzle behavior when swap penalties outweigh expected gains.

**Validation method:** Compare slicer estimates, future planner cost estimates, and measured U1 print times after hardware access.

### 3.7 Purge And Wipe Tower Behavior (RSK-07)

**Risk description:** Mixed physical nozzle workflows may require different purge volumes, wipe behavior, or tower geometry. Incorrect assumptions can cause contamination, defects, or tower failure.

**Stage affected:** Stage 2

**Research blocker control:** Treat wipe and purge behavior as a Stage 2 research blocker. Do not write or execute mixed physical nozzle toolpath output until physical toolhead purge requirements, contamination thresholds, and wipe tower reliability are analyzed on U1 hardware.

### 3.8 Nozzle Mismatch Validation Interlocks (RSK-08)

**Risk description:** Altering or bypassing nozzle validation can create unsafe or invalid print jobs if slicer assumptions disagree with the printer's known toolhead/nozzle state.

**Stage affected:** Stage 2

**Mitigation:** Never modify or bypass machine-side safety mechanisms, firmware checks, or validation routines such as Snapmaker nozzle validation paths in `CalibUtils.cpp`. AMP must operate through declared slicer configuration, planner outputs, and validated toolpath-generation interfaces while preserving job metadata and validation behavior.

### 3.9 User Misunderstanding (RSK-09)

**Risk description:** Users may misread early AMP work as production-ready adaptive physical nozzle behavior.

**Stages affected:** Stage 1, 2

**Mitigation:** Keep experimental controls hidden from normal production profile UI layouts and use clear Adaptive Manufacturing Planner terminology. Separate bead-width planning, read-only diagnostics, and physical mixed-nozzle validation in all public docs.

**Validation method:** Verify experimental options remain developer-only and are not enabled by production profile defaults.

### 3.10 Upstream Maintainability (RSK-10)

**Risk description:** Deeply embedding AMP region logic into shared slicing hot paths would make upstream synchronization and maintainer review harder.

**Stages affected:** Stage 1, 2, 3

**Mitigation:** Isolate planning, scoring, and caching into discrete self-contained files such as `src/libslic3r/AdaptiveManufacturingPlanner.*`. Core files should receive minimal append-only configuration declarations until behavior-changing work is explicitly approved.

**Validation method:** Review each AMP commit boundary for touched files and run dry-run merge checks against upstream when practical.

### 3.11 Benchmark Validity (RSK-11)

**Risk description:** Simple cubes and decorative examples do not stress the geometry and manufacturing boundaries that matter for functional parts.

**Stages affected:** Stage 1, 2

**Mitigation:** Use a dual-layer benchmark method:

- **Synthetic benchmark models** to isolate thin features, small holes, curvature steps, internal widening, overfill boundaries, and support-heavy cases.
- **Functional automotive benchmark models** from Ohmic Audio Labs, such as speaker adapters, multi-layer rings, trim components, amplifier mounts, and fabrication fixtures.

**Validation method:** Keep benchmark results separated by validation level so profile-only output, future read-only artifacts, and future behavior-changing output are not conflated.

### 3.12 Lack Of Physical U1 Hardware Access (RSK-12)

**Risk description:** Physical mixed-nozzle toolhead transitions and coordinate/tool state assumptions cannot be validated without a U1.

**Stage affected:** Stage 2

**Mitigation:** Stage 2 behavior remains disabled by default, hidden from normal UI, and blocked behind explicit developer configuration until physical U1 validation is available. No strength, print-quality, dimensional, bonding, purge, or mixed-nozzle claims should be made before real U1 prints.

### 3.13 Project Scope Creep (RSK-13)

**Risk description:** Combining adaptive cooling, multi-material optimization, orientation changes, layer-height planning, and mixed-nozzle behavior too early would stall the core architecture.

**Stages affected:** Stage 1, 2, 3

**Mitigation:** Enforce strict milestones:

1. Documentation and architecture.
2. Hidden config flag.
3. Pure value-type stock fallback module.
4. Read-only debug output.
5. Geometry scoring.
6. Behavior-changing bead-width planning.
7. Arachne integration.
8. U1 physical mixed-nozzle validation after hardware access.

## 4. Current Recommendation

Proceed only to the pure value-type stock fallback module after the branch is clean and the read-only integration map is reconciled. Do not start planner algorithms, Arachne changes, or physical mixed-nozzle behavior until the relevant validation levels and guardrails are satisfied.
