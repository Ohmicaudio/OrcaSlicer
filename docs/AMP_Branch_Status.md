# AMP Branch Status

## Current Branch

`u1-adaptive-nozzle-strategy`

## Latest AMP Commits

Newest first:

```text
d15c66a planner: add AMP observation debug artifact mapper
2889bdd docs: design AMP observation debug artifact mapping
c39fce6 docs: update AMP branch status after observation scaffold
bfa16ab planner: add AMP observation summary value types
e1dc9fc docs: design AMP serial read-only observation pass
6260a78 docs: update AMP branch status after writer scaffold
7eae238 planner: add AMP debug artifact writer utility
fd62495 docs: design AMP debug artifact writer
084fd6f docs: update AMP branch status after serializer scaffold
9f3e25a planner: add AMP debug artifact JSON serializer
aa496ad docs: update AMP branch status after debug artifact scaffold
c5cb5e2 planner: add AMP debug artifact value types
b05da70 docs: design AMP read-only debug artifact
922204c docs: update AMP branch status after sidecar scaffold
7205998 planner: add AMP sidecar cache value types
2c4569d docs: add revised Snapmaker outreach email
601a3e0 docs: add AMP v0.2 architecture review
ee01d2a docs: add final Snapmaker submission packet
14388e1 docs: add AMP branch status ledger
3e5c76f docs: update AMP prior-art research
4e9c768 docs: design AMP PrintObject sidecar cache
7ce5040 docs: document AMP local test blocker
e8bb8cc docs: add AMP prior-art research draft
d1b1915 planner: add no-op AMP planner facade
7f8d499 docs: document AMP local test blocker
19f594d planner: add stock fallback AMP value types
a868b91 docs: document AMP local test blocker
27bf35d docs: reconcile AMP read-only integration map
b0042fd docs: expand AMP risk register
9e8bd9a docs: add AMP benchmark suite
b963d98 config: add hidden adaptive manufacturing flag
e491cbf docs: add AMP v0.2 architecture and read-only prototype plan
2c63cd7 docs: add adaptive manufacturing planner specification
```

## What Exists Today

- Hidden developer config flag `adaptive_manufacturing_enable` exists.
- The flag defaults to false and is marked developer-only through `comDevelop`.
- Stock fallback AMP value types exist.
- No-op `AdaptiveManufacturingPlanner` facade exists.
- AMP sidecar cache value types exist.
- The sidecar stores `AdaptiveManufacturingPlan` entries by object/layer/region key.
- The sidecar remains unconsumed by production slicing paths.
- AMP debug artifact value types exist.
- Debug entries are deterministic by object/layer/region key.
- Debug artifact schema version `0.1` exists.
- Debug artifact data remains in-memory only.
- AMP debug artifact JSON serializer exists.
- The serializer is in-memory only and returns `std::string`.
- Deterministic JSON output is covered by focused tests.
- AMP debug artifact writer utility exists.
- The writer accepts an explicit output path and already-serialized JSON string.
- The writer writes the serialized string exactly as provided and returns a success/failure result.
- The writer overwrites existing files deterministically when called directly.
- The writer has no default output path and is not called from production slicing paths.
- AMP serial read-only observation design exists.
- AMP observation summary value types exist.
- Observation entries are deterministic by object/layer/region key.
- Observation summaries store coarse counts, region category, and warnings only.
- Observation summaries contain no polygons, coordinates, toolpaths, G-code snippets, filesystem paths, or timestamps.
- AMP observation debug artifact mapping design exists.
- AMP observation debug artifact mapper helper exists.
- The mapper accepts an already-created `AdaptiveManufacturingObservationSummary`.
- The mapper attaches optional in-memory `observation_summary` data to `AdaptiveManufacturingDebugArtifact`.
- The serializer omits `observation_summary` when absent and emits deterministic JSON when present.
- Focused AMP tests pass with 148 assertions in 24 test cases.
- PrintObject sidecar design exists.
- Read-only debug artifact design exists.
- Debug artifact writer design exists.
- AMP risk register exists.
- AMP read-only integration map exists.
- AMP prior-art research exists.
- Snapmaker U1 mixed-nozzle technical constraints are documented.
- Stage 2A Fluidd-only validation path is identified.
- Stage 2B touchscreen-compatible path is blocked pending logical-to-physical toolhead mapping support.
- No production slicer path consumes AMP.

## What Does Not Exist Yet

- No PrintObject integration.
- No sidecar cache attached to `PrintObject`.
- No read-only geometry observation pass.
- No production observation pass.
- No production observation-to-debug mapping call.
- No production debug artifact output.
- No default filesystem output.
- No production output path handling.
- No geometry scoring.
- No bead-width influence.
- No Arachne integration.
- No Flow integration.
- No PerimeterGenerator integration.
- No LayerRegion integration or consumption.
- No G-code changes.
- No profile changes.
- No UI changes.
- No physical mixed-nozzle behavior.

## Code Reference Audit

Current AMP code references are limited to:

- Hidden config flag:
  - `src/libslic3r/PrintConfig.hpp`
  - `src/libslic3r/PrintConfig.cpp`
  - `tests/libslic3r/test_config.cpp`
- Stock fallback value types:
  - `src/libslic3r/AdaptiveManufacturingPlan.hpp`
  - `src/libslic3r/AdaptiveManufacturingPlan.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_plan.cpp`
- No-op planner facade:
  - `src/libslic3r/AdaptiveManufacturingPlanner.hpp`
  - `src/libslic3r/AdaptiveManufacturingPlanner.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`
- Sidecar cache value types:
  - `src/libslic3r/AdaptiveManufacturingSidecar.hpp`
  - `src/libslic3r/AdaptiveManufacturingSidecar.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_sidecar.cpp`
- Debug artifact value types:
  - `src/libslic3r/AdaptiveManufacturingDebugArtifact.hpp`
  - `src/libslic3r/AdaptiveManufacturingDebugArtifact.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_debug_artifact.cpp`
- Debug artifact JSON serializer:
  - `src/libslic3r/AdaptiveManufacturingDebugArtifactSerializer.hpp`
  - `src/libslic3r/AdaptiveManufacturingDebugArtifactSerializer.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_debug_artifact_serializer.cpp`
- Debug artifact writer utility:
  - `src/libslic3r/AdaptiveManufacturingDebugArtifactWriter.hpp`
  - `src/libslic3r/AdaptiveManufacturingDebugArtifactWriter.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_debug_artifact_writer.cpp`
- Observation summary value types:
  - `src/libslic3r/AdaptiveManufacturingObservation.hpp`
  - `src/libslic3r/AdaptiveManufacturingObservation.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_observation.cpp`
- Observation debug artifact mapper:
  - `src/libslic3r/AdaptiveManufacturingObservationDebugMapper.hpp`
  - `src/libslic3r/AdaptiveManufacturingObservationDebugMapper.cpp`
  - `tests/libslic3r/test_adaptive_manufacturing_observation_debug_mapper.cpp`
- Build registration:
  - `src/libslic3r/CMakeLists.txt`
  - `tests/libslic3r/CMakeLists.txt`

`adaptive_manufacturing_enable` is not consumed by production slicing code. `AdaptiveManufacturingPlanner` is not called from `PrintObject`, `LayerRegion`, `Flow`, `PerimeterGenerator`, Arachne, G-code export, UI, profiles, or Snapmaker validation. `AdaptiveManufacturingSidecar` is referenced only by its own source/header, its unit test, and CMake/build registration. `AdaptiveManufacturingDebugArtifact` is referenced only by its own source/header, its unit test, the serializer, the observation debug mapper, and CMake/build registration. `AdaptiveManufacturingDebugArtifactSerializer` is referenced only by its own source/header, its unit tests, the observation debug mapper tests, and CMake/build registration. `AdaptiveManufacturingDebugArtifactWriter` is referenced only by its own source/header, its unit test, and CMake/build registration. `AdaptiveManufacturingObservation` is referenced only by its own source/header, its unit tests, the observation debug mapper, and CMake/build registration. `AdaptiveManufacturingObservationDebugMapper` is referenced only by its own source/header, its unit test, and CMake/build registration.

## Recent Commit Boundaries

`b963d98 config: add hidden adaptive manufacturing flag`

```text
src/libslic3r/PrintConfig.cpp
src/libslic3r/PrintConfig.hpp
tests/libslic3r/test_config.cpp
```

`19f594d planner: add stock fallback AMP value types`

```text
src/libslic3r/AdaptiveManufacturingPlan.cpp
src/libslic3r/AdaptiveManufacturingPlan.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_plan.cpp
```

`d1b1915 planner: add no-op AMP planner facade`

```text
src/libslic3r/AdaptiveManufacturingPlanner.cpp
src/libslic3r/AdaptiveManufacturingPlanner.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_planner.cpp
```

`4e9c768 docs: design AMP PrintObject sidecar cache`

```text
docs/design/AMP_PrintObject_Sidecar_Cache_Design.md
```

`7205998 planner: add AMP sidecar cache value types`

```text
src/libslic3r/AdaptiveManufacturingSidecar.cpp
src/libslic3r/AdaptiveManufacturingSidecar.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_sidecar.cpp
```

`c5cb5e2 planner: add AMP debug artifact value types`

```text
src/libslic3r/AdaptiveManufacturingDebugArtifact.cpp
src/libslic3r/AdaptiveManufacturingDebugArtifact.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_debug_artifact.cpp
```

`9f3e25a planner: add AMP debug artifact JSON serializer`

```text
src/libslic3r/AdaptiveManufacturingDebugArtifactSerializer.cpp
src/libslic3r/AdaptiveManufacturingDebugArtifactSerializer.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_debug_artifact_serializer.cpp
```

`fd62495 docs: design AMP debug artifact writer`

```text
docs/design/AMP_Debug_Artifact_Writer_Design.md
```

`7eae238 planner: add AMP debug artifact writer utility`

```text
src/libslic3r/AdaptiveManufacturingDebugArtifactWriter.cpp
src/libslic3r/AdaptiveManufacturingDebugArtifactWriter.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_debug_artifact_writer.cpp
```

`e1dc9fc docs: design AMP serial read-only observation pass`

```text
docs/design/AMP_Serial_ReadOnly_Observation_Design.md
```

`bfa16ab planner: add AMP observation summary value types`

```text
src/libslic3r/AdaptiveManufacturingObservation.cpp
src/libslic3r/AdaptiveManufacturingObservation.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_observation.cpp
```

`2889bdd docs: design AMP observation debug artifact mapping`

```text
docs/design/AMP_Observation_Debug_Artifact_Mapping_Design.md
```

`d15c66a planner: add AMP observation debug artifact mapper`

```text
src/libslic3r/AdaptiveManufacturingDebugArtifact.cpp
src/libslic3r/AdaptiveManufacturingDebugArtifact.hpp
src/libslic3r/AdaptiveManufacturingDebugArtifactSerializer.cpp
src/libslic3r/AdaptiveManufacturingObservationDebugMapper.cpp
src/libslic3r/AdaptiveManufacturingObservationDebugMapper.hpp
src/libslic3r/CMakeLists.txt
tests/libslic3r/CMakeLists.txt
tests/libslic3r/test_adaptive_manufacturing_observation_debug_mapper.cpp
```

These commit boundaries do not modify `Flow`, `LayerRegion`, `PerimeterGenerator`, Arachne, G-code output, profiles, UI, Snapmaker nozzle validation, or `CalibUtils.cpp`.

## Documentation Status

- `docs/risks/AMP_Project_Risk_Register_v0.2.md` is committed in `b0042fd`.
- `docs/code_maps/AMP_ReadOnly_Integration_Map.md` is committed in `27bf35d`.
- `docs/design/AMP_PrintObject_Sidecar_Cache_Design.md` is committed in `4e9c768`.
- `docs/design/AMP_ReadOnly_Debug_Artifact_Design.md` is committed in `b05da70`.
- `docs/design/AMP_Debug_Artifact_Writer_Design.md` is committed in `fd62495`.
- `docs/design/AMP_Serial_ReadOnly_Observation_Design.md` is committed in `e1dc9fc`.
- `docs/design/AMP_Observation_Debug_Artifact_Mapping_Design.md` is committed in `2889bdd`.
- `docs/research/Adaptive_Bead_Width_and_Mixed_Nozzle_Prior_Art.md` is committed in `e8bb8cc` and updated in `3e5c76f`.
- `docs/submission/Snapmaker_Form_Answers_Final.md`, `docs/submission/Snapmaker_One_Page_Project_Summary_Final.md`, and `docs/submission/Snapmaker_Technical_Appendix_Final.md` are committed in `ee01d2a`.
- `docs/reviews/AMP_v0.2_Architecture_Review.md` is committed in `601a3e0`.
- `docs/Snapmaker_Email_Rev2.md` is committed in `2c4569d`.

The risk register includes the current concurrency guardrails, four validation levels, synthetic and automotive benchmarks, normalized G-code parity where applicable, developer-only configuration visibility such as `comDevelop`, and Stage 2 physical mixed-nozzle blocking until U1 hardware validation.

The integration map agrees with the PrintObject sidecar design: the first safe owner is a PrintObject-owned sidecar or PrintObject-scoped cache, the first observation pass is serial and deterministic, `LayerRegion::make_perimeters()` is a future Stage 1 consumption point only, and future threaded accumulation must be serial before the parallel loop or thread-local with deterministic merge.

## Test Status

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

Observed focused AMP result:

```text
All tests passed (148 assertions in 24 test cases)
```

Full CMake configure command still stops before repo test target generation because Boost `1.83.0` is not available through `CMAKE_PREFIX_PATH` or `Boost_DIR`.

Observed CMake blocker:

```text
Could not find a package configuration file provided by "Boost" (requested version 1.83.0)
BoostConfig.cmake
boost-config.cmake
```

## Known Local Build Blockers

- CMake `3.31.8` is the supported local CMake version currently used for this branch.
- Local MinGW GCC/G++ `15.1.0` can compile the focused AMP runner.
- Full project configure remains blocked by missing Boost `1.83.0` dependency package.
- The recommended fix remains building or installing the repo dependency prefix and passing it through `CMAKE_PREFIX_PATH`.

## Untracked Files

Current untracked files/directories:

```text
docs/submission/Snapmaker_Innovation_Fund_Form_Answers.md
docs/submission/Snapmaker_One_Page_Project_Summary.md
docs/submission/Snapmaker_Technical_Appendix.md
```

These are non-final submission drafts. The final submission packet is committed separately.

## Next Safe Implementation Step

The next safe implementation step is a docs-only design for a future developer-only debug/observation enablement path, still without wiring into production slicing.

That future design must keep observation serial, deterministic, developer-only/read-only, must not consume `adaptive_manufacturing_enable` as an output trigger, must not write files by default, must not wire into `PrintObject`, must not inspect geometry in production code, and must not change slicing output.

## Forbidden Implementation Areas

Do not modify or consume AMP from:

- `Flow`
- `LayerRegion`
- `PerimeterGenerator`
- Arachne
- G-code output
- profiles
- UI
- Snapmaker nozzle validation
- `CalibUtils.cpp`

Stage 2 mixed physical nozzle behavior remains blocked until U1 hardware access and validation. Do not bypass `CalibUtils.cpp` or Snapmaker nozzle validation. Do not write planner/debug artifacts inside the `PrintObject::make_perimeters()` `tbb::parallel_for`. The first real observation pass must be serial and deterministic.

For U1 specifically, touchscreen-compatible mixed physical nozzle behavior remains blocked pending logical-to-physical toolhead mapping support. Any future Fluidd-only validation path must be developer-only and hardware-validated before it can influence slicer output.

Do not implement:

- geometry scoring,
- production geometry observation,
- production observation-to-debug mapping,
- sidecar cache production integration,
- production debug artifact writing,
- default filesystem output,
- PrintObject integration,
- production output path handling,
- bead-width influence,
- physical mixed-nozzle behavior.
