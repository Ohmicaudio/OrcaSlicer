# AMP Packet Sidecar Adapter 001

## Purpose

This report documents the first behavior-neutral C++ adapter from packet-shaped AMP debug artifact entries into deterministic sidecar-style lookup data.

The bridge is:

```text
offline planner packet
-> debug artifact JSON
-> C++ AdaptiveManufacturingDebugArtifact value
-> packet sidecar lookup
```

This is still offline/test-only support code. It is not wired into production slicing.

## Why Sidecar-Style Lookup Matters

Future slicer-side AMP integration will need to look up advisory decisions by object/layer/region identity instead of scanning a JSON report.

The packet sidecar prototype preserves the planner packet fields in a lookup-friendly structure:

- region identity
- recommended tool class
- fallback tool class
- selected process profile
- selected layer height
- selected line-width class
- cost-gate result and reason
- fallback reason
- risk flags
- local-Z advisory state
- touchscreen mixed-nozzle block state

## New C++ Packet Sidecar Types

Added:

```text
src/libslic3r/AdaptiveManufacturingPacketSidecar.hpp
src/libslic3r/AdaptiveManufacturingPacketSidecar.cpp
tests/libslic3r/test_adaptive_manufacturing_packet_sidecar.cpp
```

Primary value types:

- `AdaptiveManufacturingPacketSidecarKey`
- `AdaptiveManufacturingPacketPlan`
- `AdaptiveManufacturingPacketSidecar`

The packet sidecar uses deterministic `std::map` storage and supports:

- `empty()`
- `size()`
- `clear()`
- `insert_or_assign()`
- `find()`
- `contains()`
- `entries()`

This does not replace `AdaptiveManufacturingSidecar`. It is a packet-shaped sidecar prototype for future debug/planner integration.

## Debug Artifact Conversion Behavior

Added pure adapter function:

```text
make_packet_sidecar_from_debug_artifact(const AdaptiveManufacturingDebugArtifact& artifact)
```

Behavior:

- Converts each debug artifact entry into a packet sidecar entry.
- Preserves object/layer/region identity where present.
- Preserves `region_name`.
- Preserves recommended/fallback tool classes.
- Preserves selected process profile, layer height, and line-width class.
- Preserves cost-gate and fallback reasons.
- Preserves risk flags.
- Preserves local-Z and touchscreen-block advisory flags.
- Uses empty/default values for missing optional packet fields.
- Uses stable synthetic IDs when numeric IDs are absent.
- Performs no geometry inspection and emits no files.

## Golden Packet Test Result

The sidecar adapter test constructs a four-region packet-shaped debug artifact matching the current U1 tool ladder:

- `micro_detail_zone`: `0.2`, `0.06 Standard @Snapmaker U1 (0.2 nozzle)`
- `normal_visible_detail_zone`: `0.4`, `0.16 Optimal @Snapmaker U1 (0.4 nozzle)`
- `structural_shell_zone`: `0.6`, `0.24 Standard @Snapmaker U1 (0.6 nozzle)`
- `bulk_zone`: `0.8`, `0.40 Standard @Snapmaker U1 (0.8 nozzle)`

The test verifies deterministic ordering, key lookup, risk flag preservation, local-Z advisory preservation, touchscreen-block preservation, missing optional field handling, and repeated conversion stability.

## Golden JSON End-to-End Result

The packet sidecar test also imports the committed golden artifact:

```text
tests/libslic3r/data/amp_debug_artifact_offline_plan_packet_golden.json
```

Path tested:

```text
golden debug_artifact.json
-> test-only JSON import helper
-> AdaptiveManufacturingDebugArtifact
-> make_packet_sidecar_from_debug_artifact()
-> deterministic packet sidecar lookup
```

The shared test-only helper lives at:

```text
tests/libslic3r/amp_debug_artifact_test_helpers.hpp
```

Lookup assertions cover all four U1 tool classes:

- `micro_detail_zone`: `0.2`, fallback `0.4`, `0.06 Standard @Snapmaker U1 (0.2 nozzle)`, local-Z advisory true, touchscreen block true
- `normal_visible_detail_zone`: `0.4`, `0.16 Optimal @Snapmaker U1 (0.4 nozzle)`
- `structural_shell_zone`: `0.6`, `0.24 Standard @Snapmaker U1 (0.6 nozzle)`
- `bulk_zone`: `0.8`, `0.40 Standard @Snapmaker U1 (0.8 nozzle)`

No production slicer path consumes this sidecar.

## Focused AMP Test Result

Focused compile command:

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
  src\libslic3r\AdaptiveManufacturingPacketSidecar.cpp `
  src\libslic3r\AdaptiveManufacturingPlan.cpp `
  src\libslic3r\AdaptiveManufacturingPlanner.cpp `
  src\libslic3r\AdaptiveManufacturingSidecar.cpp `
  tests\libslic3r\test_adaptive_manufacturing_debug_artifact.cpp `
  tests\libslic3r\test_adaptive_manufacturing_debug_artifact_serializer.cpp `
  tests\libslic3r\test_adaptive_manufacturing_debug_artifact_writer.cpp `
  tests\libslic3r\test_adaptive_manufacturing_observation.cpp `
  tests\libslic3r\test_adaptive_manufacturing_observation_debug_mapper.cpp `
  tests\libslic3r\test_adaptive_manufacturing_packet_sidecar.cpp `
  tests\libslic3r\test_adaptive_manufacturing_plan.cpp `
  tests\libslic3r\test_adaptive_manufacturing_planner.cpp `
  tests\libslic3r\test_adaptive_manufacturing_sidecar.cpp `
  -o ..\build-amp-focused\amp_focused_tests.exe
```

Focused test command:

```powershell
& ..\build-amp-focused\amp_focused_tests.exe "[AdaptiveManufacturingDebugArtifact],[AdaptiveManufacturingDebugArtifactSerializer],[AdaptiveManufacturingDebugArtifactWriter],[AdaptiveManufacturingObservation],[AdaptiveManufacturingObservationDebugMapper],[AdaptiveManufacturingPacketSidecar],[AdaptiveManufacturingPlan],[AdaptiveManufacturingPlanner],[AdaptiveManufacturingSidecar]"
```

Observed result:

```text
All tests passed (2149 assertions in 38 test cases)
```

## What This Proves

- AMP packet-shaped debug artifacts can now be converted into deterministic C++ sidecar-style lookup data.
- Packet fields can be preserved across debug-artifact value objects and sidecar-style lookup objects.
- Packet plans can be looked up by object/layer/region key and region name.
- The committed golden debug artifact JSON can be imported and converted into packet sidecar lookup data.
- Missing optional packet fields are handled without crashing.
- Repeated conversion of the same artifact produces identical sidecar contents.
- No production slicer path consumes the packet sidecar.

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

The next safe bridge is:

```text
packet sidecar lookup
-> test-only planner/debug adapter
-> future read-only sidecar/debug export
```

That should remain disconnected from `PrintObject`, `LayerRegion`, production G-code generation, profile defaults, UI, and Snapmaker validation until explicitly approved.
