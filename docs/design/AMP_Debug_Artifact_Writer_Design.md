# AMP Debug Artifact Writer Design

## Purpose

This document defines the future Adaptive Manufacturing Planner debug artifact writer boundary. The writer's job is to persist already-serialized AMP debug JSON for developer inspection and deterministic regression testing.

The writer is a visibility and validation tool, not a manufacturing behavior change.

The writer must remain separate from:

- planning;
- debug artifact value construction;
- JSON serialization;
- slicing;
- toolpath generation;
- G-code export.

Keeping this boundary narrow prevents debug output from becoming a hidden planner side effect or a second path for slicer state mutation.

## Current Branch Context

The AMP branch currently has:

- hidden developer config flag `adaptive_manufacturing_enable`;
- stock fallback AMP value types;
- no-op `AdaptiveManufacturingPlanner` facade;
- sidecar cache value types;
- debug artifact value types;
- in-memory JSON serializer returning `std::string`;
- focused AMP tests passing with 81 assertions in 12 test cases;
- no production slicer path consuming AMP.

This document does not authorize writer implementation, filesystem output, `PrintObject` wiring, config consumption, geometry inspection, or any slicing behavior change.

## Writer Boundary

The future writer should accept an already-serialized JSON string and a destination chosen by an explicit future developer-only debug option.

The writer may:

- receive a path or destination handle selected outside the planner;
- receive a serialized JSON string produced by the serializer;
- write the exact serialized bytes using stable line-ending and encoding rules;
- return a success/failure result to the caller.

The writer must not:

- inspect geometry;
- inspect, own, or mutate `AdaptiveManufacturingPlan`;
- inspect, own, or mutate `AdaptiveManufacturingDebugArtifact`;
- generate JSON;
- sort entries;
- add timestamps;
- add build metadata;
- allocate or mutate sidecar records;
- read or write G-code;
- influence slicer decisions;
- bypass Snapmaker validation.

The writer has no slicing authority. It is an I/O boundary only.

## Output Rules

Debug artifact writing must be developer-only and optional.

Required rules:

- No output unless an explicit future debug output option exists.
- No default filesystem writes.
- No writes when adaptive manufacturing is disabled unless a future explicit debug test mode allows it.
- No hidden writes from normal slicing paths.
- No file output that changes G-code, toolpaths, planner state, profile state, or slicer behavior.
- No output path inferred from model geometry, printer state, or host-specific transient state.

Future output configuration should be separate from the existing `adaptive_manufacturing_enable` flag. Enabling AMP read-only behavior should not, by itself, imply filesystem output.

## Safety Rules

Writer calls must stay outside parallel slicing hot paths and outside behavior-changing paths.

Required rules:

- No writes inside the `PrintObject::make_perimeters()` `tbb::parallel_for`.
- No writes from `LayerRegion::make_perimeters()`.
- Future writes must happen after deterministic serial observation, or after thread-local records are merged deterministically.
- Writer failures must not mutate planner state.
- Writer failures must not partially change slicer behavior.
- Writer failures must not cause fallback to behavior-changing planner output.
- Writer errors must be reported through an explicit developer/debug result channel.

Failure handling should distinguish test mode from developer inspection mode:

- In unit tests, writer failure should be a test failure.
- In future developer debug mode, writer failure should produce a warning or structured failure result.
- In production slicing paths, the writer should not be reachable until an explicit developer debug output option is added and validated.

If the repo's local error-handling style prefers exceptions for filesystem failures, exceptions must not cross a slicing boundary unreviewed. A small result type is preferred for this writer boundary because it makes failure handling explicit and testable.

## Determinism

The writer must preserve byte-for-byte determinism when given identical serialized input and the same destination policy.

Required deterministic behavior:

- No timestamps in equivalence-sensitive mode.
- No host-specific absolute paths embedded in file content.
- No random suffixes in deterministic test mode.
- Stable file naming strategy for tests.
- Stable line endings.
- UTF-8 output.
- Repeated identical artifact input produces identical file content.

Recommended line-ending policy:

- Treat the serializer output as canonical JSON text.
- Write the serialized string exactly as provided.
- Do not translate line endings in the writer.
- If pretty-printed JSON is added later, normalize line endings before the writer receives the string.

Recommended test naming policy:

- Use explicit test-provided filenames in temporary directories.
- Avoid clock time, process IDs, thread IDs, pointer values, and random values in equivalence-sensitive tests.
- If collision avoidance is needed outside test mode, keep it outside deterministic comparison paths.

## Future API Sketch

This is a non-binding sketch only. It is not an implementation requirement for this milestone.

```cpp
struct AdaptiveManufacturingDebugArtifactWriteResult
{
    bool success = false;
    std::string error_message;
};

AdaptiveManufacturingDebugArtifactWriteResult write_debug_artifact(
    const std::filesystem::path &path,
    const std::string &serialized_json);
```

Boundary notes:

- The writer receives serialized JSON, not artifact value objects.
- The writer does not call the serializer.
- The writer does not own output path selection policy.
- The writer does not inspect planner state.
- The writer returns a result instead of changing slicer behavior.
- No exceptions should cross the slicing boundary unless that matches established repo style and is explicitly reviewed.

The final implementation may use repo-specific path and filesystem abstractions instead of `std::filesystem` if that better matches existing Snapmaker Orca conventions.

## Validation Strategy

Future writer implementation should be validated independently before any production integration.

Unit tests should cover:

- writing to a temporary directory only;
- exact file contents match the serializer output;
- repeated writes with identical input produce identical file content;
- overwrite behavior or reject-existing behavior is explicit and tested;
- invalid path failure behavior returns a structured failure result;
- writer does not append timestamps or nondeterministic content;
- UTF-8 content is preserved;
- no output path is created unless the writer is explicitly called;
- no production slicer references the writer.

Integration checks, before any later wiring, should confirm:

- `adaptive_manufacturing_enable` remains unconsumed by the writer;
- `PrintObject`, `LayerRegion`, `Flow`, `PerimeterGenerator`, Arachne, G-code export, UI, profiles, Snapmaker validation, and `CalibUtils.cpp` do not reference the writer;
- generated G-code remains unchanged when debug artifact writing is absent;
- generated G-code remains unchanged if a future developer-only writer path is enabled for a no-op/read-only artifact.

## Future Output Policy Questions

These questions should be answered before implementation:

- Should the first writer overwrite existing files or reject existing destinations?
- Should the result type include a normalized error code in addition to an error message?
- Should the writer create parent directories, or should the caller prepare the destination?
- Should developer-mode write failures be warnings in the GUI, log messages, or structured test failures only?
- Should deterministic test mode require byte-for-byte output with no trailing newline, or a canonical trailing newline?

The first implementation plan should choose conservative answers and document them before adding C++.

## Non-Goals

This design explicitly does not include:

- writer implementation;
- new config option;
- filesystem output;
- output path handling;
- `PrintObject` integration;
- `LayerRegion` integration;
- geometry observation;
- geometry scoring;
- bead-width influence;
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
- `docs/design/AMP_ReadOnly_Debug_Artifact_Design.md`
- `docs/design/AMP_PrintObject_Sidecar_Cache_Design.md`
- `docs/risks/AMP_Project_Risk_Register_v0.2.md`
- `docs/code_maps/AMP_ReadOnly_Integration_Map.md`

## Exit Criteria For Future Writer Value/Tests

Before adding writer C++ or tests, the branch should satisfy:

- debug artifact serializer remains in-memory only;
- serializer output remains deterministic;
- no production slicer path consumes AMP;
- no writer or filesystem output exists yet;
- the implementation plan names exact files, tests, failure behavior, and path policy;
- the planned writer accepts serialized JSON rather than planner or artifact objects.
