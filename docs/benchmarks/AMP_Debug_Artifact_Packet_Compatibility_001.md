# AMP Debug Artifact Packet Compatibility 001

## Purpose

This report documents the first compatibility bridge between the offline AMP plan packet and the C++ AMP debug artifact schema.

The goal is:

```text
offline Python planner packet
-> C++ debug artifact value types
-> deterministic JSON serializer
-> future sidecar/debug output target
```

This remains behavior-neutral. It does not wire AMP into production slicing.

## Offline Packet Fields

The offline packet shape requires debug-artifact support for:

- `generation_mode: offline_advisory`
- `region_name`
- `recommended_tool_class`
- `fallback_tool_class`
- `selected_process_profile`
- `selected_layer_height_mm`
- `selected_line_width_class`
- `cost_gate_passed`
- `cost_gate_reason`
- `fallback_reason`
- `risk_flags`
- `local_z_future_required`
- `touchscreen_mixed_nozzle_blocked`

These fields describe the advisory plan packet without storing geometry polygons, toolpath coordinates, production G-code snippets, Arachne state, Flow mutation data, or physical nozzle commands.

## C++ Debug Artifact Fields Added

Updated:

```text
src/libslic3r/AdaptiveManufacturingDebugArtifact.hpp
```

Added enum values:

- `AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory`
- `AdaptiveManufacturingDebugSourceStage::OfflinePlanPacket`

Added optional/value-only packet fields to `AdaptiveManufacturingDebugEntry`:

- `region_name`
- `recommended_tool_class`
- `fallback_tool_class`
- `selected_process_profile`
- `selected_layer_height_mm`
- `selected_line_width_class`
- `cost_gate_passed`
- `cost_gate_reason`
- `fallback_reason`
- `risk_flags`
- `local_z_future_required`
- `touchscreen_mixed_nozzle_blocked`

No file I/O, geometry references, slicer integration, or G-code behavior was added.

## Serializer Behavior

Updated:

```text
src/libslic3r/AdaptiveManufacturingDebugArtifactSerializer.cpp
```

Serializer behavior:

- `OfflineAdvisory` serializes as `offline_advisory`.
- `OfflinePlanPacket` serializes as `offline_plan_packet`.
- Optional packet fields are omitted when unset.
- Optional packet booleans serialize only when explicitly set.
- `risk_flags` serializes as a string array.
- Existing entry ordering remains deterministic by object/layer/region key.
- Repeated serialization of the same artifact produces identical JSON.

## Focused Test Result

Focused AMP test command:

```powershell
New-Item -ItemType Directory -Force -Path ..\build-amp-focused | Out-Null
& "C:\Users\d\tools\winlibs-gcc-15.1.0-ucrt\mingw64\bin\g++.exe" `
  -std=c++17 `
  -Isrc `
  -Itests `
  -Ideps `
  -x c++ tests\catch_main.hpp `
  src\libslic3r\AdaptiveManufacturingDebugArtifact.cpp `
  src\libslic3r\AdaptiveManufacturingDebugArtifactSerializer.cpp `
  src\libslic3r\AdaptiveManufacturingDebugArtifactWriter.cpp `
  src\libslic3r\AdaptiveManufacturingObservation.cpp `
  src\libslic3r\AdaptiveManufacturingObservationDebugMapper.cpp `
  src\libslic3r\AdaptiveManufacturingPlan.cpp `
  src\libslic3r\AdaptiveManufacturingPlanner.cpp `
  src\libslic3r\AdaptiveManufacturingSidecar.cpp `
  tests\libslic3r\test_adaptive_manufacturing_debug_artifact.cpp `
  tests\libslic3r\test_adaptive_manufacturing_debug_artifact_serializer.cpp `
  tests\libslic3r\test_adaptive_manufacturing_debug_artifact_writer.cpp `
  tests\libslic3r\test_adaptive_manufacturing_observation.cpp `
  tests\libslic3r\test_adaptive_manufacturing_observation_debug_mapper.cpp `
  tests\libslic3r\test_adaptive_manufacturing_plan.cpp `
  tests\libslic3r\test_adaptive_manufacturing_planner.cpp `
  tests\libslic3r\test_adaptive_manufacturing_sidecar.cpp `
  -o ..\build-amp-focused\amp_focused_tests.exe
& ..\build-amp-focused\amp_focused_tests.exe "[AdaptiveManufacturingDebugArtifact],[AdaptiveManufacturingDebugArtifactSerializer],[AdaptiveManufacturingDebugArtifactWriter],[AdaptiveManufacturingObservation],[AdaptiveManufacturingObservationDebugMapper],[AdaptiveManufacturingPlan],[AdaptiveManufacturingPlanner],[AdaptiveManufacturingSidecar]"
```

Observed result:

```text
All tests passed (191 assertions in 30 test cases)
```

New test coverage includes:

- offline advisory generation mode serialization
- packet-shaped tool/profile fields
- four-region packet-shaped deterministic serialization
- unset optional packet fields omitted from JSON
- risk flag order and escaping

## Packet Compatibility Result

Optional contract check tool:

```text
tools/amp_debug_artifact_contract_check.py
```

Command:

```powershell
python tools\amp_debug_artifact_contract_check.py outputs\amp_plan_packet_001\debug_artifact.json outputs\amp_plan_packet_001_detail_first\debug_artifact.json
```

Observed result before the generator-side field population update:

```text
outputs/amp_plan_packet_001/debug_artifact.json: passed, 0 errors, 1 warning
outputs/amp_plan_packet_001_detail_first/debug_artifact.json: passed, 0 errors, 1 warning
```

The warning was expected at that point: the artifacts were schema-compatible, but the Python packet generator populated only `region_name` from the newly supported packet-compatible field set.

Follow-up generator update:

```text
tools/amp_generate_plan_packet.py
```

The Python packet generator now emits full packet-compatible debug artifact fields:

- `recommended_tool_class`
- `fallback_tool_class`
- `selected_process_profile`
- `selected_layer_height_mm`
- `selected_line_width_class`
- `cost_gate_passed`
- `cost_gate_reason`
- `fallback_reason`
- `risk_flags`
- `local_z_future_required`
- `touchscreen_mixed_nozzle_blocked`

Observed result after regenerating the packets:

```text
outputs/amp_plan_packet_001/debug_artifact.json: passed, 0 errors, 0 warnings
outputs/amp_plan_packet_001_detail_first/debug_artifact.json: passed, 0 errors, 0 warnings
```

The generated artifact now includes region/tool/profile/cost/risk/local-Z/touchscreen-block fields while remaining offline/advisory only.

## What This Proves

- The offline AMP plan packet now has a C++ debug artifact representation.
- The C++ serializer can emit packet-shaped advisory entries deterministically.
- Packet-shaped entries can carry tool class, fallback, process profile, layer height, line-width class, cost-gate, risk, local-Z, and touchscreen-block fields.
- The current generated offline debug artifact is compatible with the supported C++ schema.
- The Python packet generator now populates the full packet-compatible debug artifact field set.
- This artifact shape is suitable as a future sidecar/debug output target.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate production `T0`, `T1`, `T2`, or `T3` commands.

This does not generate a single mixed-nozzle G-code print.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future/hardware-dependent.

This does not prove print strength, surface quality, dimensional accuracy, or bonding.

## Next Integration Target

The next safe target is:

```text
Python offline packet debug_artifact.json
-> C++ debug artifact compatibility check
-> future read-only sidecar/debug export
```

That should remain disconnected from production slicing, G-code generation, PrintObject integration, and Snapmaker validation until explicitly approved.
