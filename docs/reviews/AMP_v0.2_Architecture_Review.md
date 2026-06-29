# AMP v0.2 — Architecture Review

**Reviewer role:** Senior engineer (slicer pipeline / upstream-acceptance lens)
**Scope reviewed:** `AdaptiveManufacturingPlanner_v0.1.md`, `Adaptive_Manufacturing_Planner_Design_v0.1.md`, `AdaptiveManufacturingPlanner_v0.2.md`, `AMP_ReadOnly_Prototype_Implementation_Plan.md`, `U1_Mixed_Nozzle_Risk_Register.md`, `U1_Profile_Only_Test_Plan.md`
**Code grounding:** anchors spot-checked against this tree (`src/libslic3r/PrintObject.cpp`, `LayerRegion.cpp`, `Arachne/WallToolPaths.cpp`, `src/slic3r/Utils/CalibUtils.cpp`).

**Constraints honored by this review:** no behavior change is proposed; Stage 1 stays software-only; Stage 2 stays hardware-backed and blocked on U1 access; nothing here weakens, defers, or routes around nozzle validation or printer safety checks. Several recommendations *tighten* the safety boundary.

---

## TL;DR verdict

The v0.2 direction is sound and unusually disciplined for a planner-style feature: read-only first, value types, flag-gated, removable, no consumption into generation. **Approve the read-only direction.** Three things need fixing before code lands:

1. **Reconcile the three docs into one source of truth.** v0.1-design, v0.2, and the implementation plan each define a *different* set of data types and names (`AdaptiveRegionPlan` vs `AMPRegion` vs `AMPScoreSet`). A maintainer reviewing the PR will not know which is canonical.
2. **Pick the planner's home explicitly: a sidecar owned by `PrintObject`, populated by its own read-only pass — not a call inside `LayerRegion::make_perimeters`.** The implementation plan's Task 5 guard sits inside a hot, `tbb::parallel_for` path; that is the wrong place for a "prove it changes nothing" prototype.
3. **Trim the data structures and config surface to what the read-only artifact actually populates.** Tool/nozzle/layer-height fields and the eight proposed `PrintConfig` settings are Stage 2/3 vocabulary leaking into a Stage 1 read-only milestone.

Everything else is detail.

---

## 1. Is the planner boundary clean?

**Mostly yes — cleaner than typical for this class of feature.** The v0.2 doc gets the hard parts right:

- **Observer, not mutator.** "The planner owns only derived analysis and recommendation data" and "later stages must consume copied or value-type recommendations" (v0.2 §Data ownership) is the correct invariant. The read-only planner cannot be on the required path for stock slicing (lifecycle step 7). Good.
- **No reverse dependencies.** The implementation plan forbids `AdaptiveManufacturingPlan.hpp` from including `Flow`, `PerimeterGenerator`, Arachne, the G-code writer, or UI headers. That keeps the dependency arrow pointing one way (planner → ids/values, never generation → planner). This is the single most important thing for upstream review and it's already specified.
- **Value-type outputs keyed by existing ids.** Referencing `object_id` / `layer_id` / `print_region_id` instead of holding slicer pointers is what makes the thing removable.

**Where the boundary is not yet clean:**

- **Naming/type drift across docs (boundary is described three ways).** A boundary you can't name precisely isn't clean yet:
  - `Adaptive_Manufacturing_Planner_Design_v0.1.md` defines `AdaptiveRegionPlan`, `AdaptiveBeadWidthPlan`, `AdaptiveToolPlan`, `AdaptiveManufacturingPlan` (with `find_region_plan`), `AdaptiveManufacturingPlanner::plan_object(const PrintObject&)`.
  - `AdaptiveManufacturingPlanner_v0.2.md` defines `AMPRegion`, `AMPRegionScores`, `AMPRecommendation`, `AMPDebugRecord`.
  - `AMP_ReadOnly_Prototype_Implementation_Plan.md` defines `AMPScoreSet`, `AMPRegion`, `AMPRecommendation`, `AMPDebugRecord`, and `analyze_read_only(const AdaptiveManufacturingPlannerInput&)`.

  These are not refinements of each other; they're three vocabularies. Pick one (recommend the `AMP*` prefix + `analyze_read_only` API from the implementation plan, since it's the most read-only-honest), and mark the v0.1 design's `plan_object`/tool-plan shapes as *superseded*.

- **The debug-artifact side door.** Lifecycle step 6 ("planner writes debug artifacts") is the one place the planner reaches outside its own value types — to a filesystem/stream. That's a real boundary crossing and it's underspecified (per-object? per-plate? per-run? where on disk? who owns the handle?). The open questions acknowledge it, but for the prototype this should be **in-memory return + test-only serialization**, with any file write gated behind an env var or developer build, never wired into the slicing path. Don't let "emit a JSON file" become unguarded I/O inside `make_perimeters`.

- **Concurrency is unaddressed (new finding, not in the docs).** `PrintObject::make_perimeters()` dispatches layers through `tbb::parallel_for` (PrintObject.cpp:385), and `LayerRegion::make_perimeters` runs *inside* that loop. Any planner that observes per-layer/per-region geometry while that loop runs, or that appends to one shared `AdaptiveManufacturingPlan`, is writing from multiple threads. The boundary isn't clean until ownership states either (a) a separate **serial** pass, or (b) thread-local accumulation merged deterministically afterward. See Q2.

**Boundary verdict:** architecturally clean in intent; not yet clean in *specification*. Reconcile names, close the debug side door, and state the concurrency model.

---

## 2. Should the first planner live at `PrintObject`, `LayerRegion`, or as a sidecar cache?

**Recommendation: a sidecar owned by `PrintObject`, populated by a dedicated read-only pass — and explicitly *not* a call site inside `LayerRegion::make_perimeters`.**

Reasoning grounded in this tree:

- **`LayerRegion::make_perimeters` is the wrong host for the prototype.** It is the hot path that builds flows and constructs `PerimeterGenerator` → `Arachne::WallToolPaths` (LayerRegion.cpp:182), and it runs under `tbb::parallel_for`. Putting the planner call there (as Implementation Plan Task 5, Step 2 sketches) means: touching a behavior-critical signature, running planner code interleaved with generation, and inheriting the parallel context. For a milestone whose entire thesis is "prove I change nothing," that maximizes the surface you must prove over.

- **`PrintObject` is the right *owner*.** It already owns the layers, runs serially at the top of `make_perimeters()` (after `slice()` has produced layer/region surfaces, PrintObject.cpp:296), and is the natural lifetime for a per-object plan. A `std::unique_ptr<AdaptiveManufacturingPlan> m_amp_plan` member is removable and null when the flag is off.

- **The plan itself should be a sidecar, not state threaded through generation.** Nothing in generation should read it in v0.2. It is produced, optionally serialized for inspection, and dropped.

**Concrete shape:** add a separate read-only traversal, e.g. `PrintObject::run_adaptive_planner_readonly()`, invoked only when the flag is enabled, after `slice()` and either before the perimeter loop or as its own posStep-like phase. It walks `m_layers[i]->get_region(r)` read-only, builds `AMPRegion` records, and stores them in the sidecar. This:
- runs serially (no concurrency questions for the prototype),
- never enters `LayerRegion::make_perimeters` or the parallel loop,
- makes "flag off ⇒ method never runs ⇒ identical output" trivially true and trivially testable.

`LayerRegion` scope becomes relevant only at Stage 1 *consumption* time (mapping planned outer/inner widths to `bead_width_0`/`bead_width_x` before `WallToolPaths` is constructed — WallToolPaths.cpp:62). That's a later, behavior-changing PR and out of scope here. Don't pre-wire it.

So: **PrintObject owns it, sidecar holds it, a separate read-only pass fills it, LayerRegion stays untouched until Stage 1.**

---

## 3. Are the proposed data structures too early, too broad, or appropriate?

**Mixed: appropriate core, too broad at the edges, and parts are too early.**

**Appropriate for v0.2 read-only:**
- `AdaptiveManufacturingPlan` container keyed by object/layer/region ids.
- `AMPRegion` with `bounds`, `area`, `perimeter_length`, `surface_roles`.
- A small score set + `confidence`.
- `AMPDebugRecord` for serialization.
- `AMPReasonCode` with `ReadOnlyNoBehaviorChange` / fallback reasons.

These map directly to things a read-only observer can compute and a reviewer can verify.

**Too broad (reserve in docs, not in code, for the first PRs):**
- `AMPRegionScores` ships **seven** scores (`detail`, `structural`, `cosmetic_visibility`, `accessibility`, `toolchange_penalty`, `time_savings_potential`, `classification_confidence`). A deterministic, explainable v0.2 needs maybe three to be honest: `detail_score`, `structural_score`, `classification_confidence`. `toolchange_penalty` and `time_savings_potential` are *tool-selection* economics — Stage 2/3 vocabulary. Adding empty-but-named fields invites reviewers to ask "where's the logic?" and invites future code to fill them prematurely. Start narrow; widen with the algorithm.
- `accessibility_score` only means something once tool reachability exists. Premature.

**Too early (Stage 2/3 leaking into Stage 1):**
- The v0.1-design `AdaptiveToolPlan` (`preferred_extruder_id`, `preferred_nozzle_diameter`, `fallback_extruder_id`, `estimated_toolchange_cost_s`, `requires_toolchange`) and `AMPRecommendation`'s `preferred_nozzle_diameter` / `preferred_extruder_id`. Per the risk register (R1, R3, R10) and your own non-goals, **mixed-nozzle is blocked on U1 hardware.** Shipping the fields now creates the exact "looks supported" trap R8 warns about, and a future careless commit could route `preferred_extruder_id` into assignment. Keep these out of the read-only types entirely; they can be added in the Stage 2 branch behind hardware validation.
- `AdaptiveBeadWidthPlan` / layer-height plan fields: Stage 1.5 / optional. Not needed to observe geometry.
- The `AMPStrategy` enum values `DetailPreserving`, `InternalThroughput`, `SupportThroughput` describe *behaviors that don't exist*. For read-only, strategy should resolve to `Stock` only. Either collapse the enum to `{ Stock }` for now or document the others as reserved-and-unreachable so a reviewer doesn't read intent into them.

**Config surface is too broad too.** `Adaptive_Manufacturing_Planner_Design_v0.1.md` proposes eight `PrintConfig` settings (`...priority`, `...stage`, `...min_confidence`, `...max_inner_width_scale`, `...max_infill_width_scale`, `...max_toolchange_cost_s`, `...allow_mixed_nozzles`). For the read-only milestone ship **exactly one**: `adaptive_manufacturing_enable` (`coBool`, default `false`). Every other setting is a tuning knob for behavior that doesn't exist yet, and each one is a permanent profile-serialization commitment once it ships. Add knobs alongside the behavior they gate.

**Structures verdict:** keep the plan/region/score/debug spine; cut tool, nozzle, layer-height, accessibility, toolchange-economics, and seven-of-eight config flags until the stage that uses them. Right altitude for v0.2 is "describe geometry + confidence + reason," nothing that names a nozzle.

---

## 4. Is the no-op/read-only prototype scoped correctly?

**Largely yes.** The phase ladder (flag → value types → stock fallback → debug export → disabled-equivalence test → scoring last) is the right order, and "disabled ⇒ not invoked ⇒ equivalent output" is the correct contract. Four corrections:

1. **Integration point (Task 5).** As in Q2, move the guarded call out of `LayerRegion`/the parallel loop into a serial `PrintObject` read-only pass. The Task 5 sketch (`if (print_config.adaptive_manufacturing_enable.value) { ... }` near `make_perimeters`) is close but should not live where it can perturb the perimeter hot path.

2. **Pin the equivalence standard.** v0.1 says "byte-for-byte equivalent *or* explainably identical"; that "or" is a loophole. For the prototype, commit to **deterministic G-code equality** on a fixed stock U1 profile, asserted two ways: flag **off**, and flag **on (read-only)**. The read-only-on case proving identical output is the whole point — Task 5 Step 4 already gestures at it; make it a hard, automated assertion, not a manual slice-and-eyeball.

3. **Determinism of the artifact.** Because the eventual scoring pass touches per-layer geometry, the debug artifact must be order-stable regardless of threading. Specify: regions emitted in sorted `(layer_id, region_id)` order, no map iteration order, no floats formatted locale-dependently, no filesystem paths in output (Task 4 Step 3 says this — good, keep it).

4. **Keep file I/O out of the slice path.** Scope the first artifact as an in-memory structure returned to a test, plus an opt-in dump. Shipping unconditional file writes inside slicing is a behavior change in spirit (timing, disk, failure modes) even if G-code is identical.

Scoping nit: Task 6 (scoring) correctly stays advisory and keeps `strategy = stock`. Good — that's the line between "read-only prototype" and "Stage 1." Don't cross it in this milestone.

---

## 5. What should be explicitly forbidden before hardware validation?

State these as hard gates in the canonical doc and (better) as test/CI assertions. None of these weaken existing safety checks — several add new guards.

**Generation / output:**
- No planner output may flow into `Flow`, `LayerRegion::flow`, `PerimeterGenerator`, `Arachne::WallToolPaths`, infill, support, tool assignment, or the G-code writer. (v0.2 lists these as must-stay-unchanged — make it enforceable, e.g. the planner header cannot be included by those TUs.)
- No emission of toolchange G-code, purge/wipe sequences, or per-region extruder switches.

**Nozzle / printer safety (do not touch):**
- Do not bypass, short-circuit, or duplicate the nozzle-mismatch / calibration checks in `src/slic3r/Utils/CalibUtils.cpp` or Snapmaker device-validation paths (Risk R1). The planner must remain downstream-blind to them.
- No `preferred_nozzle_diameter` / `preferred_extruder_id` may exist in code paths reachable from assignment until U1 validation (Risk R3, R10).

**Profiles / shipping defaults:**
- No change to any registered Snapmaker process/machine profile default.
- The experimental width profile from `U1_Profile_Only_Test_Plan.md` stays unregistered (not in `resources/profiles/Snapmaker.json`) and clearly marked docs-only.
- No shipped U1 preset may flip `wall_generator` to `arachne` or imply mixed nozzles are validated.

**Claims / UX:**
- No user-facing claim of strength, quality, or time improvement from profile-only or read-only work (Test Plan §Hardware Validation Is Deferred).
- Any mixed-nozzle UI must stay hidden unless multi-tool U1 capability is detected *and* validated (Risk R8); a hidden flag is not a license to expose nozzle selection.
- Preview/overlay colors are diagnostics, never confirmed assignments (v0.2 says this — keep it).

**Determinism / invisibility when off:**
- Flag off ⇒ planner object not constructed, no allocation, no I/O, no timing delta.
- No non-deterministic debug output (threading/map order/locale).

---

## 6. What would make this easier for Snapmaker maintainers to review?

This feature's biggest risk (R9) is upstream rejection for being too invasive. Optimize the whole rollout for a reviewer who has never seen the design docs:

- **One canonical design doc, linked from the PR.** Today there are three with diverging type names. Collapse to a single source of truth; mark v0.1 docs "superseded by v0.2." A maintainer should never have to diff three vocabularies.
- **Tiny, strictly additive first PRs.** Flag-only PR, then unreferenced value-types PR (see Q7). Each should be reviewable in one sitting and obviously incapable of changing output because nothing calls it.
- **Self-contained files, no hot-header edits.** New `AMP*` TUs include nothing from generation; generation includes nothing from AMP. Forward-declare. This lets a reviewer confirm "can't affect slicing" by inspecting the include graph alone.
- **Append, don't reorder, in `PrintConfig`.** Add `adaptive_manufacturing_enable` at the end of its group; do not renumber enums or reorder option registration, which can perturb profile (de)serialization and explode the diff. Match the exact `def->mode` / `category` / `L()` conventions of neighboring `coBool` options.
- **Ship a golden-output regression in the same PR series.** A test that slices a stock U1 model and asserts identical G-code with the flag off *and* on is the single most persuasive artifact you can hand a maintainer — it turns "trust me, it's read-only" into CI.
- **Minimal, obvious build diff.** Keep the CMake/source-list change to the new files only; call it out in the PR description.
- **PR description in their language:** "experimental, hidden, default-off, no toolpath/G-code/profile/validation change," plus a one-line pointer to the doc and the regression test. Mirror that in the option tooltip (the implementation plan's tooltip already does this — good).
- **Keep nozzle/tool vocabulary out of early PRs entirely** so a safety-minded reviewer never has to evaluate mixed-nozzle claims to approve a read-only diagnostic.

---

## 7. What is the smallest possible first code PR after the hidden config flag?

**PR #1** is the flag itself (`adaptive_manufacturing_enable`, `coBool`, default `false`, advanced/hidden, + config-parse test). Implementation Plan Task 1. Nothing observes it yet.

**Smallest PR #2 (the answer):** the **pure value-type module, referenced by nobody.**

- Add `src/libslic3r/AdaptiveManufacturingPlan.hpp` / `.cpp` containing only:
  - the trimmed value types (`AMPScoreSet` with ~3 fields, `AMPRegion`, `AdaptiveManufacturingPlan` container, `AMPReasonCode`, `AMPStrategy` collapsed to `{ Stock }`),
  - `make_stock_fallback_plan(int object_id)` with reason `read_only_no_behavior_change`.
- Add `tests/libslic3r/test_adaptive_manufacturing_planner.cpp` asserting default values and that the stock fallback reports `strategy = stock`.
- Wire only the new files into the build. **No planner class, no input struct, no JSON, no `PrintObject`/`LayerRegion` edit, no integration.**

Why this is the floor: it compiles into `libslic3r`, is fully unit-tested, and **cannot change behavior because no production translation unit references it.** A reviewer can approve it purely on "does it build and are the types sane," with zero slicing-correctness analysis. That's Task 2 of the implementation plan, and it's correctly the right next step — the planner *API* (`analyze_read_only`, the input struct — Task 3), JSON serialization (Task 4), the guarded `PrintObject` invocation (Task 5), and scoring (Task 6) should each be their own subsequent PR, in that order.

(If you want an even smaller seed: enums + `AMPScoreSet` defaults + one test, deferring the plan container. But the value-types-plus-stock-fallback unit is the natural smallest *useful* increment.)

---

## Summary of required changes before code

| # | Change | Severity |
|---|--------|----------|
| 1 | Collapse three docs into one canonical type vocabulary (`AMP*`); mark v0.1 design superseded | Blocking for review clarity |
| 2 | Host the plan as a `PrintObject`-owned sidecar filled by a **serial** read-only pass; keep it out of `LayerRegion::make_perimeters` and the `tbb::parallel_for` path | Blocking for "no behavior change" provability |
| 3 | Ship one config flag, not eight; cut tool/nozzle/layer-height/accessibility/toolchange fields from read-only types | High |
| 4 | Pin equivalence to deterministic G-code equality, asserted flag-off **and** flag-on, in CI | High |
| 5 | Keep debug artifact in-memory/test-only; gate any file write behind a developer opt-in | Medium |
| 6 | State the concurrency/determinism model for the artifact explicitly | Medium |
| 7 | Enumerate the pre-hardware "forbidden" list (Q5) as enforced gates, not prose | Medium |

The thesis — read-only observer, value types, flag-gated, removable, U1 behavior blocked on hardware — is right and worth pursuing. The work before code is mostly *subtraction and reconciliation*, not addition.
