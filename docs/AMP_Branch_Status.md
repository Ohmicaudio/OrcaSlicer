# AMP Branch Status

## Current Branch

`u1-adaptive-nozzle-strategy`

## Latest AMP Commits

Newest first:

```text
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
3f8fb16 docs: define adaptive manufacturing planner
```

## What Exists Today

- Hidden developer config flag `adaptive_manufacturing_enable` exists.
- The flag defaults to false and is marked developer-only through `comDevelop`.
- Stock fallback AMP value types exist.
- No-op `AdaptiveManufacturingPlanner` facade exists.
- AMP sidecar cache value types exist.
- The sidecar stores `AdaptiveManufacturingPlan` entries by object/layer/region key.
- The sidecar remains unconsumed by production slicing paths.
- Focused AMP tests pass with 37 assertions in 4 test cases.
- PrintObject sidecar design exists.
- AMP risk register exists.
- AMP read-only integration map exists.
- AMP prior-art research exists.
- No production slicer path consumes AMP.

## What Does Not Exist Yet

- No PrintObject integration.
- No sidecar cache attached to `PrintObject`.
- No read-only geometry observation.
- No debug artifact output.
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
- Build registration:
  - `src/libslic3r/CMakeLists.txt`
  - `tests/libslic3r/CMakeLists.txt`

`adaptive_manufacturing_enable` is not consumed by production slicing code. `AdaptiveManufacturingPlanner` is not called from `PrintObject`, `LayerRegion`, `Flow`, `PerimeterGenerator`, Arachne, G-code export, UI, profiles, or Snapmaker validation. `AdaptiveManufacturingSidecar` is referenced only by its own source/header, its unit test, and CMake/build registration.

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

These commit boundaries do not modify `Flow`, `LayerRegion`, `PerimeterGenerator`, Arachne, G-code output, profiles, UI, Snapmaker nozzle validation, or `CalibUtils.cpp`.

## Documentation Status

- `docs/risks/AMP_Project_Risk_Register_v0.2.md` is committed in `b0042fd`.
- `docs/code_maps/AMP_ReadOnly_Integration_Map.md` is committed in `27bf35d`.
- `docs/design/AMP_PrintObject_Sidecar_Cache_Design.md` is committed in `4e9c768`.
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
  src\libslic3r\AdaptiveManufacturingPlan.cpp `
  src\libslic3r\AdaptiveManufacturingPlanner.cpp `
  src\libslic3r\AdaptiveManufacturingSidecar.cpp `
  tests\libslic3r\test_adaptive_manufacturing_plan.cpp `
  tests\libslic3r\test_adaptive_manufacturing_planner.cpp `
  tests\libslic3r\test_adaptive_manufacturing_sidecar.cpp `
  -o ..\build-amp-focused\amp_focused_tests.exe
& ..\build-amp-focused\amp_focused_tests.exe "[AdaptiveManufacturingPlan],[AdaptiveManufacturingPlanner],[AdaptiveManufacturingSidecar]"
```

Observed focused AMP result:

```text
All tests passed (37 assertions in 4 test cases)
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

The next safe implementation step is a read-only debug artifact design document.

That future document should describe how debug artifacts will be emitted later from completed planner-owned data without writing from `PrintObject::make_perimeters()` parallel execution or from `LayerRegion::make_perimeters()`. It should not implement debug artifact output.

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

Do not implement:

- geometry scoring,
- sidecar cache production integration,
- debug artifact writing,
- bead-width influence,
- physical mixed-nozzle behavior.
