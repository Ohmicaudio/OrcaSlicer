# Adaptive Manufacturing Planner (AMP) — Technical Appendix

**For:** Snapmaker U1 Innovation Fund reviewers and Snapmaker Orca maintainers
**Companion to:** `Snapmaker_One_Page_Project_Summary_Final.md`, `Snapmaker_Form_Answers_Final.md`
**Status:** Design and validation stage. No behavior-changing slicer code is shipped or implied.
**Public branch:** <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy>

This appendix gives maintainers the technical detail needed to evaluate AMP without reading the full design set. It is written against the actual Snapmaker Orca codebase, not against an abstract design.

---

## 1. Scope of what exists vs. what is proposed

To be unambiguous: AMP today is documentation and a code-grounded plan. It does **not** perform geometry partitioning and does **not** generate behavior-changing G-code. AMP **is being developed toward geometry-aware region classification and manufacturing planning** through the staged plan below; that capability is not a current behavior.

The earliest code milestone is intentionally inert: a hidden flag and a no-op scaffold that nothing in the production path consumes.

## 2. Where AMP fits in the Snapmaker Orca pipeline

Relevant existing flow (verified in this tree):

- `Print::process()` schedules object work.
- `PrintObject::make_perimeters()` runs perimeter generation; it dispatches layer work through `tbb::parallel_for`, then calls `Layer::make_perimeters()` per layer.
- `LayerRegion::make_perimeters(...)` builds flows and constructs `PerimeterGenerator`, choosing Arachne or classic generation.
- `PerimeterGenerator::process_arachne()` constructs `Arachne::WallToolPaths(...)`.
- `Arachne::WallToolPaths` consumes `bead_width_0` (outer) and `bead_width_x` (inner) plus transition/minimum-width parameters.
- Nozzle diameter is read during flow construction (`LayerRegion::flow(...)`, `Flow::new_from_config_width(...)`) and in `Arachne::make_paths_params(...)`.

**AMP's read-only observation point** is a serial pass owned by `PrintObject`, after slicing has produced layer/region surfaces and *outside* the parallel perimeter loop. Stage 1 *consumption* (mapping planned outer/inner widths to `bead_width_0` / `bead_width_x`) is a later, behavior-changing milestone and is not part of the read-only prototype.

## 3. Concurrency finding (drives the architecture)

`PrintObject::make_perimeters()` processes layers with `tbb::parallel_for`, and `LayerRegion::make_perimeters()` runs inside that loop. Writing planner observations or debug buffers from inside that loop would create data races and non-repeatable output.

Consequences baked into the design (risk register RSK-01):

- No shared mutable planner/debug writes inside the `PrintObject::make_perimeters()` parallel loop or inside `LayerRegion::make_perimeters()`.
- The read-only prototype observes geometry through a **deterministic serial pre-pass** (or explicit thread-local accumulation with a deterministic merge).
- A **`PrintObject`-owned sidecar** is the first safe owner of read-only observations.
- Validation: repeated regression slices of identical meshes compared as normalized G-code, plus ThreadSanitizer where the toolchain supports it.

This is why AMP is hosted at `PrintObject` scope as a sidecar rather than wired into `LayerRegion::make_perimeters()`.

## 4. Architecture and ownership

- **Hidden flag:** `adaptive_manufacturing_enable` (`coBool`, default `false`), developer-visible only. With the flag off, the planner is not constructed and there is no allocation, I/O, or timing change.
- **Value-type outputs only.** The planner owns derived analysis/recommendation data keyed by existing object/layer/region identifiers. Existing slicer objects keep ownership of mesh, layer, region, surface, flow, toolpath, and G-code data. Any future behavior-changing stage consumes copied/value-type recommendations — the planner never mutates generation classes.
- **Self-contained files** (proposed), with no includes into hot generation headers:
  - `src/libslic3r/AdaptiveManufacturingPlan.hpp` / `.cpp` — value types and stock-fallback helpers.
  - `src/libslic3r/AdaptiveManufacturingPlanner.hpp` / `.cpp` — read-only `analyze_read_only(...)` API.
  - `tests/libslic3r/test_adaptive_manufacturing_planner.cpp` — unit tests.
- **Append-only edits to shared files** (`PrintConfig.hpp/.cpp`): the flag is appended, options are not reordered, and enum reflection is not perturbed, so profile serialization stays stable and the diff stays small.

## 5. Staged plan and risk-weighted rationale

| Stage | What | Software/Hardware | Why the risk level |
| --- | --- | --- | --- |
| Stage 1 | Adaptive bead widths | Software-only | **Lower-risk software-only validation path**: reuses existing line-width/Arachne mechanisms (`bead_width_0`/`bead_width_x` inputs) rather than introducing new toolpath logic; no behavior change while disabled; no strength or print-quality claims from preview alone. |
| Stage 2 | Adaptive physical nozzle selection | U1 hardware-backed | **Blocked until U1 hardware access**; no safety bypasses; mixed-nozzle behavior stays disabled and hidden, with no mixed-nozzle claims before physical validation on a real U1. |
| Stage 3 | Manufacturing optimization | Software + measured costs | Longer-term; future cost-aware planning and optimization that depends on validated Stage 1/2 cost models. |

## 6. Validation levels (no conflation of diagnostics and behavior)

The benchmark suite separates output strictly by level so a read-only diagnostic is never mistaken for a behavior change:

- **Level 0 — Stock U1 profile.** No AMP code; baseline preview/time/filament estimates.
- **Level 1 — Experimental profile-only effective-width profile.** No slicer code changes; uses existing line-width settings + Arachne. Demonstrates the *concept* via profiles only; does not prove AMP logic exists.
- **Level 2 — Read-only AMP prototype (future).** Emits debug/region/scoring artifacts only; generated toolpaths and G-code are unchanged.
- **Level 3 — Behavior-changing AMP (future).** Requires prior equivalence proof, explicit review, regression coverage, and a documented rollback path.
- **Level 4 — U1 physical mixed-nozzle validation.** Requires hardware; no strength/quality/mixed-nozzle claims before real prints.

The current pass targets **Level 0 and Level 1 only**. Benchmark models are functional and inspectable (thin-detail parts, brackets/adapters with large infill, broad top-surface parts, support-heavy parts, and Ohmic Audio Labs functional parts), not just decorative cubes.

What preview/G-code inspection **can** show: slicing success, path-geometry differences, whether role-specific width settings affect expected regions. What it **cannot** show: real strength, surface quality, dimensional accuracy, bonding, nozzle/toolhead reliability, purge behavior, or mixed-nozzle success — all of which require physical U1 printing.

## 7. Safety constraints (hard, not polish)

- **No bypass of nozzle-mismatch checks, firmware safety behavior, or Snapmaker device-validation paths** (e.g. `src/slic3r/Utils/CalibUtils.cpp`). AMP cooperates with these checks and never short-circuits or duplicates them.
- No physical mixed-nozzle toolpath output (no tool-change G-code, purge/wipe sequences, or per-region extruder switches) until U1 validation.
- No shipped/registered profile defaults that imply mixed nozzles are validated; the experimental width profile stays unregistered and docs-only.
- No planner output flows into `Flow`, `PerimeterGenerator`, Arachne, infill, support, tool assignment, or the G-code writer in the read-only milestone.
- Deterministic, locale-independent debug output with no filesystem paths; regions emitted in stable `(layer_id, region_id)` order.

## 8. Selected risks (full register in `docs/risks/AMP_Project_Risk_Register_v0.2.md`)

- **RSK-01 (Critical) — Slicing correctness/concurrency:** serial pre-pass + `PrintObject` sidecar; normalized-G-code regression + ThreadSanitizer.
- **RSK-02 (High) — Arachne edge cases:** conservative width bounds first; synthetic stress geometry (thin walls, narrow text, small holes, curvature steps).
- **RSK-03 (High) — Flow/overfill boundaries:** volumetric cross-section checks; never bypass existing flow limits.
- **RSK-08 (Critical) — Nozzle mismatch validation:** preserve interlocks; operate only through validated interfaces.
- **RSK-10 (Medium) — Upstream maintainability:** isolated files, append-only core edits, per-commit touched-file review.
- **RSK-12 (High) — No U1 access:** Stage 2 stays disabled/hidden/blocked until hardware; no mixed-nozzle claims before real prints.

## 9. Test ladder for the read-only prototype

1. Config-parse tests for the hidden flag (default false; profile value parses; missing keeps default).
2. Unit tests for value types and the stock fallback plan (`strategy = stock`, reason `read_only_no_behavior_change`).
3. Deterministic debug-JSON serialization tests (no paths, stable ordering).
4. Disabled-equivalence tests: flag off ⇒ output matches stock.
5. Read-only-enabled tests: flag on ⇒ debug artifact produced, toolpaths/G-code unchanged.
6. Geometry-scoring tests on synthetic regions (added only after the no-op path is stable).

## 10. Smallest first PRs (for low-friction review)

1. **PR 1:** hidden flag only (`adaptive_manufacturing_enable`) + config-parse test. Nothing consumes it.
2. **PR 2:** pure value-type module + `make_stock_fallback_plan()` + unit tests, referenced by no production translation unit — cannot change behavior because nothing calls it.
3. Subsequent PRs add the read-only API, JSON serialization, the guarded `PrintObject` serial pass, and scoring, each independently reviewable.

This ordering lets a maintainer approve early increments on "does it build and are the types sane," with no slicing-correctness analysis required, and keeps the project bounded against scope creep (RSK-13).
