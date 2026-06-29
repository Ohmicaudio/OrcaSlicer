# AMP PrintObject Sidecar Cache Design

## Purpose

This document defines the first read-only Adaptive Manufacturing Planner sidecar/cache boundary. The goal is to give AMP a safe place to store object-scoped observations and stock fallback recommendations before any planner output is allowed to influence slicing behavior.

The read-only sidecar is a visibility and validation tool, not a manufacturing behavior change.

## Scope

This design covers:

- PrintObject-scoped ownership.
- Serial and deterministic observation.
- Sidecar/cache contents.
- Lifecycle and invalidation.
- Future deterministic merge strategy.
- Future debug artifact emission.
- Test strategy.

This design does not authorize C++ implementation. It is the contract for a later implementation commit.

## Why PrintObject Scope Is The First Owner

`PrintObject` is the first safe owner for AMP read-only data because it sits above layer and region perimeter generation while still representing a single sliced object. At this boundary, AMP can describe object/layer/region observations without owning or mutating `Flow`, `PerimeterGenerator`, Arachne state, generated extrusion paths, G-code, profile defaults, or Snapmaker validation state.

A PrintObject-scoped sidecar also matches the first useful debug granularity:

- one object identity,
- ordered layer records,
- ordered region records,
- planner-owned fallback/reason data,
- optional future debug artifact metadata.

Keeping the cache scoped to `PrintObject` makes the first integration removable. If AMP is disabled, stock slicing should not need to allocate, populate, or consume planner data.

## Serial And Deterministic First Observation

The first AMP observation pass must be serial and deterministic.

Required properties:

- Iterate objects, layers, and regions in stable slicer order.
- Populate planner-owned values only.
- Produce the same sidecar records for the same input model and profile.
- Avoid shared mutable writes from worker threads.
- Avoid dependence on map iteration order, pointer addresses, or timing.

This is necessary because `PrintObject::make_perimeters()` uses `tbb::parallel_for` for layer perimeter work. Writing shared planner/debug state from that parallel path would make the first read-only prototype harder to reason about and harder to test for normalized G-code parity.

## Why LayerRegion::make_perimeters Is Not The First Owner

`LayerRegion::make_perimeters()` is an important future consumption point, but it is not the first read-only owner.

It is useful later because it has access to region configuration, object configuration, wall-generation decisions, and the point where `PerimeterGenerator` is constructed. That makes it a plausible future place to consume immutable AMP recommendations after the read-only path is proven.

It is unsafe as the first owner because:

- It is reached from the `PrintObject::make_perimeters()` parallel layer loop.
- Shared sidecar/debug writes from this function would require synchronization or thread-local accumulation.
- It is part of the wall-generation hot path, where Stage 0 must avoid behavior changes.
- It is too close to Arachne, Flow, and generated perimeter output for the first cache boundary.

For Stage 0/read-only work, `LayerRegion::make_perimeters()` may be documented as a future Stage 1 consumption point only.

## Sidecar Data Model

The first sidecar should store planner-owned value data only. It should be possible to compare, serialize, and discard the sidecar without touching slicer-owned toolpath data.

Recommended top-level fields:

- `object_id`
- `source_revision` or cache generation counter
- `planner_mode`
- `fallback_reason`
- `confidence`
- ordered `layers`
- optional future `debug_artifact_manifest`

Recommended layer record fields:

- `layer_index`
- `print_z`
- ordered `regions`
- optional layer-level summary counts

Recommended region record fields:

- `region_index`
- `print_region_id`
- stable region key derived from object/layer/region order
- coarse geometry summary
- stock fallback recommendation
- reason code
- conservative confidence

Recommended geometry summary fields for the first read-only cache:

- area, when cheaply available from existing geometry
- perimeter length, when cheaply available from existing geometry
- bounding box, when cheaply available from existing geometry
- surface role summary, when already available before perimeter generation
- feature counters only after they can be computed without changing generator behavior

Recommended recommendation fields:

- `reason = StockFallback`
- `requires_toolchange = false`
- `bead_width_override = none`
- `nozzle_diameter_override = none`
- `confidence = 0.0`

## Data The Sidecar Must Not Store Yet

The first sidecar must not store or own:

- `Flow` objects.
- `PerimeterGenerator` instances.
- Arachne `WallToolPaths` state.
- mutable `LayerRegion` generation outputs.
- extrusion paths.
- infill paths.
- support paths.
- G-code writer state.
- physical toolhead/nozzle state.
- Snapmaker validation state.
- profile default mutations.
- pointers whose lifetime is shorter than the sidecar.

The sidecar may reference existing object/layer/region identity by stable value keys, but it should not become an alternate owner of slicer internals.

## Lifecycle

The first implementation should treat the sidecar as a derived cache.

Suggested lifecycle:

1. Stock slicing creates object/layer/region geometry through existing paths.
2. If AMP is disabled, no sidecar is required.
3. If AMP read-only mode is enabled, `PrintObject` owns or can access a sidecar cache.
4. A serial observation pass populates the sidecar before parallel perimeter generation.
5. Perimeter, infill, support, and G-code generation continue through stock behavior.
6. Future debug emission reads the completed sidecar after the observation pass, outside parallel hot paths.
7. The sidecar is discarded or invalidated when the owning object geometry/config changes.

## Invalidation

The sidecar should be invalidated whenever any input that affects observed geometry or planner interpretation changes.

Invalidation triggers should include:

- mesh or object geometry change,
- object transform change,
- modifier/painted attribute change,
- layer height or slicing setting change,
- print profile change relevant to wall/region interpretation,
- material or nozzle configuration change,
- switching AMP mode,
- rebuilding object layers,
- clearing or regenerating perimeters.

The first implementation can use coarse invalidation. It is safer to rebuild the sidecar too often than to reuse stale planner records.

## Future Deterministic Merge Strategy

The preferred Stage 0 design is a serial pre-pass. If future performance work requires per-layer threaded observation, all threaded data must be accumulated into thread-local records and merged afterward.

Deterministic merge requirements:

- Thread-local records must not write into shared sidecar state directly.
- Each record must carry stable object/layer/region keys.
- Merge order must sort by object key, layer index, region index, and record type.
- Duplicate keys must be resolved by explicit rules, not by last-writer-wins timing.
- Debug artifact serialization must happen after the merge completes.

Thread-local accumulation is a future optimization, not the first implementation path.

## Future Debug Artifact Emission

Debug artifacts should be emitted later from completed sidecar data, not from inside parallel loops.

Allowed future pattern:

1. Populate sidecar in a serial pass.
2. Continue stock slicing behavior.
3. Serialize sidecar-derived debug JSON/CSV/SVG after the sidecar is complete.

Disallowed pattern:

- writing JSON, CSV, SVG, logs, or preview overlay data from inside `LayerRegion::make_perimeters()`;
- writing shared debug buffers from inside the `PrintObject::make_perimeters()` `tbb::parallel_for`;
- letting debug serialization consume or mutate generated extrusion paths.

The first debug artifact should be machine-readable and clearly marked as read-only planner diagnostics.

## Test Strategy

The sidecar design should be tested before it is connected to behavior-changing planning.

Unit-level tests:

- default sidecar is empty or stock fallback only;
- region records compare deterministically;
- generated keys are stable for repeated construction;
- invalidation clears stale records;
- stock fallback records contain no toolchange, bead-width override, or nozzle override.

Integration-level read-only tests:

- AMP disabled does not allocate or consume planner data in production paths;
- AMP read-only mode produces sidecar records without changing generated toolpaths;
- repeated runs produce byte-stable debug data once debug artifacts exist;
- normalized G-code remains equivalent where applicable.

Concurrency tests:

- no shared mutable sidecar writes occur inside `PrintObject::make_perimeters()` parallel execution;
- no planner/debug writes occur inside `LayerRegion::make_perimeters()`;
- any future thread-local path merges records in stable order.

Regression tests:

- synthetic thin-feature model;
- synthetic multi-region model;
- synthetic high-layer-count model;
- functional automotive benchmark part after benchmark assets are selected.

## Non-Goals

This design explicitly does not include:

- C++ implementation.
- Geometry scoring.
- Debug artifact writing.
- Preview overlay wiring.
- Arachne integration.
- Flow integration.
- PerimeterGenerator integration.
- LayerRegion consumption.
- G-code changes.
- Profile default changes.
- UI changes.
- mixed physical nozzle behavior.
- Snapmaker nozzle validation changes.

## Exit Criteria For The Next Code Step

Before implementing the sidecar, the branch should satisfy these conditions:

- hidden AMP config flag remains default false and developer-only;
- current stock fallback value types remain behavior-neutral;
- no-op planner facade remains unconsumed by production slicing paths;
- risk register and read-only integration map remain committed;
- local full-build blockers are documented if unresolved;
- the sidecar implementation plan names exact files and tests before C++ is added.
