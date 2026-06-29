# AMP Local Test Blockers

## Scope

This note records the local verification state for the AMP hidden config flag, stock fallback value types, and no-op planner facade through commit `d1b1915` (`planner: add no-op AMP planner facade`).

No slicer behavior changes were made during this verification pass.

## Commit verification

Command:

```powershell
git show --name-only --pretty=format: HEAD
```

Observed files:

```text
src/libslic3r/PrintConfig.cpp
src/libslic3r/PrintConfig.hpp
tests/libslic3r/test_config.cpp
```

The latest AMP code commit only touches the intended config declaration, config definition, and config test file.

## Flag reference check

Command:

```powershell
rg -n "adaptive_manufacturing_enable" src tests | Sort-Object
```

Observed references:

```text
src\libslic3r\PrintConfig.cpp:6262:    def = this->add("adaptive_manufacturing_enable", coBool);
src\libslic3r\PrintConfig.hpp:917:    ((ConfigOptionBool,               adaptive_manufacturing_enable))
tests\libslic3r\test_config.cpp:272:    const ConfigOptionDef *def = print_config_def.get("adaptive_manufacturing_enable");
tests\libslic3r\test_config.cpp:275:    REQUIRE(config.opt<ConfigOptionBool>("adaptive_manufacturing_enable") != nullptr);
tests\libslic3r\test_config.cpp:276:    CHECK(config.opt<ConfigOptionBool>("adaptive_manufacturing_enable")->getBool() == false);
tests\libslic3r\test_config.cpp:278:    REQUIRE_NOTHROW(config.set_deserialize_strict("adaptive_manufacturing_enable", "1"));
tests\libslic3r\test_config.cpp:279:    CHECK(config.opt<ConfigOptionBool>("adaptive_manufacturing_enable")->getBool() == true);
tests\libslic3r\test_config.cpp:281:    REQUIRE_NOTHROW(config.set_deserialize_strict("adaptive_manufacturing_enable", "0"));
tests\libslic3r\test_config.cpp:282:    CHECK(config.opt<ConfigOptionBool>("adaptive_manufacturing_enable")->getBool() == false);
```

The flag is declared in `PrintConfig`, defined in `PrintConfig`, tested in `test_config.cpp`, and not referenced by slicing, toolpath, nozzle validation, or G-code output code.

## CMake version mismatch

Initial command:

```powershell
cmake -S . -B build-amp-tests -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTS=ON
```

Initial error:

```text
CMake Error at CMakeLists.txt:5 (message):
  Only cmake versions between 3.13.x and 3.31.x is supported on windows.
  Detected version: 4.0.1
```

Initial CMake version:

```text
cmake version 4.0.1
```

Resolution attempted:

- Installed CMake `3.31.12` locally under `work/tools`.
- CMake `3.31.12` passed the repository version guard but failed during compiler identification:

```text
No preprocessor test for "IntelLLVM"
```

Root cause observed:

- The `3.31.12` package contained `IntelLLVM-C.cmake`, `IntelLLVM-CXX.cmake`, and `IntelLLVM-ASM.cmake`.
- It did not contain `Compiler/IntelLLVM-DetermineCompiler.cmake`.

Resolution:

- Installed CMake `3.31.8` locally under `work/tools`.
- CMake `3.31.8` contains `Compiler/IntelLLVM-DetermineCompiler.cmake`.
- CMake `3.31.8` successfully identified the local MinGW C and C++ compilers.

Working local CMake path:

```text
C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe
```

## Full CMake configure attempt

Command attempted:

```powershell
& "C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe" `
  -S "C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\Snapmaker-OrcaSlicer" `
  -B "C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\build-snapmaker-orca-amp-tests" `
  -G Ninja `
  -DCMAKE_BUILD_TYPE=Debug `
  -DBUILD_TESTS=ON `
  -DSLIC3R_GUI=OFF `
  -DCMAKE_C_COMPILER="C:\Users\d\tools\winlibs-gcc-15.1.0-ucrt\mingw64\bin\gcc.exe" `
  -DCMAKE_CXX_COMPILER="C:\Users\d\tools\winlibs-gcc-15.1.0-ucrt\mingw64\bin\g++.exe"
```

Compiler detection output:

```text
-- The C compiler identification is GNU 15.1.0
-- The CXX compiler identification is GNU 15.1.0
-- Detecting C compiler ABI info - done
-- Detecting CXX compiler ABI info - done
```

Blocking error:

```text
CMake Error at CMakeLists.txt:514 (find_package):
  By not providing "FindBoost.cmake" in CMAKE_MODULE_PATH this project has
  asked CMake to find a package configuration file provided by "Boost", but
  CMake did not find one.

  Could not find a package configuration file provided by "Boost" (requested
  version 1.83.0) with any of the following names:

    BoostConfig.cmake
    boost-config.cmake
```

Latest command attempted:

```powershell
& "C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe" `
  -S "C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\Snapmaker-OrcaSlicer" `
  -B "C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\build-snapmaker-orca-amp-tests" `
  -G Ninja `
  -DCMAKE_BUILD_TYPE=Debug `
  -DBUILD_TESTS=ON `
  -DSLIC3R_GUI=OFF `
  -DCMAKE_C_COMPILER="C:\Users\d\tools\winlibs-gcc-15.1.0-ucrt\mingw64\bin\gcc.exe" `
  -DCMAKE_CXX_COMPILER="C:\Users\d\tools\winlibs-gcc-15.1.0-ucrt\mingw64\bin\g++.exe"
```

Latest blocking error:

```text
CMake Error at CMakeLists.txt:514 (find_package):
  By not providing "FindBoost.cmake" in CMAKE_MODULE_PATH this project has
  asked CMake to find a package configuration file provided by "Boost", but
  CMake did not find one.

  Could not find a package configuration file provided by "Boost" (requested
  version 1.83.0) with any of the following names:

    BoostConfig.cmake
    boost-config.cmake

  Add the installation prefix of "Boost" to CMAKE_PREFIX_PATH or set
  "Boost_DIR" to a directory containing one of the above files.
```

Full generated test target execution remains blocked because CMake configure stops before test targets are generated.

## Local toolchain versions

Command:

```powershell
& "...\work\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe" --version
ninja --version
gcc --version
g++ --version
git lfs version
```

Observed:

```text
cmake version 3.31.8
ninja 1.12.1
gcc.exe (MinGW-W64 x86_64-ucrt-posix-seh, built by Brecht Sanders, r1) 15.1.0
g++.exe (MinGW-W64 x86_64-ucrt-posix-seh, built by Brecht Sanders, r1) 15.1.0
git-lfs/3.5.1
```

Visual Studio detection:

```text
C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools
```

## AMP value-type standalone compile check

After commit `19f594d` (`planner: add stock fallback AMP value types`), the new value-type source and test translation units were checked directly with the local MinGW compiler.

Command:

```powershell
g++ -std=c++17 -Isrc -Itests -Ideps -c src\libslic3r\AdaptiveManufacturingPlan.cpp -o NUL
g++ -std=c++17 -Isrc -Itests -Ideps -c tests\libslic3r\test_adaptive_manufacturing_plan.cpp -o NUL
```

Observed result:

```text
Both commands exited with code 0.
```

This confirms the new AMP value-type files compile as standalone translation units. It does not prove the full `libslic3r_tests` target builds or runs, because full CMake configure still stops at the missing Boost `1.83.0` dependency package before test targets are generated.

## Focused AMP Catch test

Command:

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
  tests\libslic3r\test_adaptive_manufacturing_plan.cpp `
  tests\libslic3r\test_adaptive_manufacturing_planner.cpp `
  -o ..\build-amp-focused\amp_focused_tests.exe
& ..\build-amp-focused\amp_focused_tests.exe "[AdaptiveManufacturingPlan],[AdaptiveManufacturingPlanner]"
```

Observed result:

```text
Filters: [AdaptiveManufacturingPlan],[AdaptiveManufacturingPlanner]
Testing Adaptive manufacturing planner facade returns stock fallback
Passed in 7e-06 [seconds]

Testing Adaptive manufacturing stock fallback is conservative and deterministic
Passed in 5e-06 [seconds]

===============================================================================
All tests passed (13 assertions in 2 test cases)
```

This focused test verifies the stock fallback value types and no-op planner facade without generating or executing the full repo test target.

## Next recommended fix

The immediate CMake version mismatch is resolved by using local CMake `3.31.8`.

The remaining blocker is missing built dependency packages, starting with Boost `1.83.0`. The repository's Windows build scripts expect dependencies to be built into `deps/build/.../OrcaSlicer_dep/usr/local` and then passed to the slicer configure through `CMAKE_PREFIX_PATH`.

Recommended local path:

1. Open an x64 Native Tools Command Prompt for Visual Studio 2019.
2. Put CMake `3.31.8` ahead of CMake `4.0.1` in `PATH`.
3. From the repository root, run:

```bat
build_release.bat deps
```

4. Configure the slicer/test build with:

```powershell
-DCMAKE_PREFIX_PATH="C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local"
```

5. Build the smallest relevant test target:

```powershell
cmake --build "C:\Users\d\Documents\Codex\2026-06-28\finish-the-apps-administrator-private-model\work\build-snapmaker-orca-amp-tests" --target libslic3r_tests
```

6. Run the focused config test:

```powershell
.\tests\libslic3r\libslic3r_tests.exe "Adaptive manufacturing planner flag is hidden and disabled by default"
```

Alternative:

- Install Visual Studio 2022 and run `build_release_vs2022.bat deps`, then configure with the generated VS2022 dependency prefix.

Full repo test execution remains blocked locally until the dependency prefix is available.
