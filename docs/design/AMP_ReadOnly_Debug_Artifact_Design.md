# AMP Read-Only Debug Artifact Design

## Purpose

This document defines the first Adaptive Manufacturing Planner read-only debug artifact. The artifact is intended to make future AMP observations visible, support regression testing, and prove read-only planner behavior without modifying generated toolpaths or G-code.

The read-only debug artifact is a visibility and validation tool, not a manufacturing behavior change.

## Current Branch Context

The AMP branch currently has:

- hidden developer config flag `adaptive_manufacturing_enable`;
- stock fallback AMP value types;
- no-op planner facade;
- sidecar cache value types;
- focused AMP tests passing;
- PrintObject sidecar cache design;
- no production slicer path consuming AMP.

The artifact design must preserve that state. This document does not authorize C++ implementation, config consumption, PrintObject wiring, geometry inspection, or debug file emission.

## Artifact Formats

The first required artifact format should be JSON.

Rationale:

- JSON is easy to diff, parse, and feed into regression tooling.
- JSON can represent object/layer/region nesting without inventing a custom format.
- JSON can remain developer-only and machine-readable before any preview UI exists.

Optional later formats:

- CSV for spreadsheet inspection and benchmark summaries.
- SVG for static per-layer visualization.

No GUI overlay is part of this milestone. Preview overlay data may be designed later after the JSON artifact is stable and deterministic.

## Initial JSON Schema

The first no-op/read-only schema should be intentionally small and conservative.

Top-level fields:

```json
{
  "schema_version": "0.1",
  "slicer_build_info": null,
  "generation_mode": "enabled_noop",
  "source_stage": "no_op_planner",
  "objects": [],
  "warnings": [],
  "ordering": {
    "objects": "object_id_ascending",
    "layers": "layer_id_ascending",
    "regions": "region_id_ascending",
    "json_keys": "stable",
    "timestamps": "omitted_in_equivalence_sensitive_mode"
  }
}
```

Object record:

```json
{
  "object_id": 0,
  "layers": []
}
```

Layer record:

```json
{
  "layer_id": 0,
  "regions": []
}
```

Region record:

```json
{
  "region_id": 0,
  "amp_plan_reason": "StockFallback",
  "confidence": 0.0,
  "toolchange_requested": false,
  "bead_width_override_present": false,
  "nozzle_override_present": false,
  "source_stage": "stock_fallback",
  "generation_mode": "enabled_noop",
  "warnings": []
}
```

Allowed `source_stage` values:

- `stock_fallback`
- `no_op_planner`
- `future_observation`

Allowed `generation_mode` values:

- `disabled`
- `enabled_noop`
- `enabled_readonly`

`slicer_build_info` may be `null` until a stable build-info source is identified. If build metadata is added later, equivalence-sensitive tests must be able to omit or normalize it.

## Data The Artifact Must Not Contain Yet

The first artifact must not contain:

- geometry polygons;
- toolpath coordinates;
- G-code snippets;
- Arachne internal state;
- Flow mutation data;
- physical nozzle commands;
- printer safety override state;
- purge or wipe commands;
- firmware or device validation bypass state;
- raw pointers or process-local addresses;
- timestamps in equivalence-sensitive test mode.

The artifact should describe AMP-owned plan state only. It must not become a side channel for slicer internals.

## Output Safety Rules

Artifact writing must obey the same concurrency and safety constraints as the PrintObject sidecar design.

Rules:

- No debug artifact writes inside the `PrintObject::make_perimeters()` `tbb::parallel_for`.
- No writes from `LayerRegion::make_perimeters()`.
- Future artifact generation must happen after deterministic serial observation, or after thread-local records are merged deterministically.
- Artifact writing must be optional and developer-only.
- Artifact writing must never change slicing output.
- Artifact generation must not consume or mutate generated extrusion paths.
- Artifact generation must not alter profiles, tool assignment, G-code output, Arachne behavior, Flow behavior, or Snapmaker validation.

The safe future pattern is:

1. Build planner-owned records in stable order.
2. Store them in a PrintObject-scoped sidecar/cache or equivalent planner-owned data structure.
3. Continue stock slicing behavior.
4. Serialize the artifact outside parallel hot paths.

## Deterministic Ordering

Deterministic output is required for regression tests.

Ordering rules:

- Objects are sorted by `object_id`.
- Layers are sorted by `layer_id`.
- Regions are sorted by `region_id`.
- JSON object keys are emitted in a stable order.
- Arrays are emitted in sorted key order.
- No timestamps are emitted in equivalence-sensitive test mode.
- Build metadata, host paths, durations, random seeds, and pointer-like values must be omitted or normalized in equivalence-sensitive test mode.

The current sidecar value types use object/layer/region keys and deterministic `std::map` ordering. Future artifact value types should preserve that ordering rather than relying on hash-map iteration or worker-thread completion order.

## Validation Strategy

Validation must keep disabled behavior, no-op behavior, and future read-only behavior distinct.

Expected validation levels:

- With `adaptive_manufacturing_enable` false: no artifact is produced unless a separate explicit developer debug option is added later.
- With the no-op planner: the artifact may contain only stock fallback plans.
- With future enabled read-only observation: the artifact may contain observation summaries and scores, but generated toolpaths and G-code must remain unchanged.

Required checks for a future implementation:

- Generated G-code remains unchanged when artifact writing is disabled.
- Generated G-code remains unchanged when no-op/read-only artifact writing is enabled.
- Artifact output is deterministic across repeated runs on the same input.
- Artifact output contains no geometry polygons, toolpath coordinates, G-code snippets, Arachne internals, Flow mutation data, physical nozzle commands, or safety override state.
- Artifact output can be compared byte-for-byte in equivalence-sensitive mode after normalizing line endings.

## Future Extension Points

Future schema versions may add:

- geometry observation summary;
- region score summary;
- bead-width recommendation summary;
- confidence and fallback details;
- future preview overlay data;
- future benchmark comparison tooling;
- normalized per-object/per-layer aggregate counts.

These extensions must remain read-only until a later behavior-changing milestone is explicitly reviewed and tested.

## Non-Goals

This milestone explicitly does not include:

- C++ implementation;
- geometry scoring;
- debug artifact writing;
- PrintObject integration;
- LayerRegion integration;
- Arachne integration;
- Flow integration;
- PerimeterGenerator integration;
- G-code changes;
- profile changes;
- UI changes;
- physical mixed-nozzle behavior;
- Snapmaker validation changes.

## Cross-References

- `docs/AMP_Branch_Status.md`
- `docs/design/AMP_PrintObject_Sidecar_Cache_Design.md`
- `docs/risks/AMP_Project_Risk_Register_v0.2.md`
- `docs/code_maps/AMP_ReadOnly_Integration_Map.md`
- `docs/benchmarks/AMP_Benchmark_Suite_v0.1.md`

## Exit Criteria For Future Artifact Value Types

Before adding artifact value types, the next implementation plan should name:

- value-type files to add;
- tests proving deterministic serialization-ready ordering;
- tests proving no-op records contain only stock fallback values;
- tests proving missing optional metadata can be represented without host-specific output;
- explicit confirmation that no production slicer path consumes artifact values.
