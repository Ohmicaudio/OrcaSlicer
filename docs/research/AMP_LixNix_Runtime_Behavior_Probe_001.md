# AMP LixNix Runtime Behavior Probe 001

## Purpose

This probe follows the source audit in `docs/research/AMP_LixNix_Multi_Nozzle_Fork_Audit_001.md` by checking whether the external LixNix `multi_nozzle_multi_layer_height` branch can be built or runtime-probed locally, and by mapping the branch's behavior from source when a build is blocked.

This is external fork testing only. It does not merge LixNix code, does not mean AMP implements mixed-nozzle slicing, does not bypass Snapmaker validation, and does not prove touchscreen-compatible mixed-nozzle behavior.

## Official Orca Baseline Context

Official OrcaSlicer documentation now confirms manual/static mixed nozzle-size support since `v2.2.0-beta`:

<https://www.orcaslicer.com/wiki/guides/mixed_nozzle_sizes>

The documented official workflow includes per-extruder nozzle diameters, percentage-based line widths, and feature/tool assignment through Filament for Features or painting workflows. This should be used as AMP's first manual/static mixed-nozzle baseline.

The LixNix runtime probe remains useful because the external branch appears to go deeper into per-extruder layer-height behavior, combined-layer mechanics, support nozzle restrictions, wipe tower math, and hot-path slicer tests. It should not be treated as the only mixed-nozzle prior-art path.

## External Branch Inspected

External repository:

<https://github.com/LixNix/OrcaSlicer-multi-nozzle-size-printing>

Local external clone:

`B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing`

Branch:

`multi_nozzle_multi_layer_height`

Commit:

`944da137d8b36427c6659d83148a149e6c6eaa1e`

Commit date:

`2026-07-06 15:30:56 +0200`

Commit subject:

`Add per extruder layer height`

Merge base used for changed-file analysis:

`395e070a0e675fd4723f93967cefede730c482d9`

Changed-file count vs merge base:

`29`

Feature documentation in README:

No dedicated mixed-nozzle or per-extruder layer-height usage guide was found in the top-level README. The README remains generic OrcaSlicer documentation.

## Build Result

Build/configure was attempted in external build directories:

`B:\ohmic\external_builds\lixnix_multi_nozzle_probe`

`B:\ohmic\external_builds\lixnix_multi_nozzle_probe_reuse_deps`

`B:\ohmic\external_builds\lixnix_multi_nozzle_probe_reuse_deps_eigen_module`

`B:\ohmic\external_builds\lixnix_multi_nozzle_probe_reuse_deps_eigen_include`

Command attempted:

```powershell
cmake -S B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing `
      -B B:\ohmic\external_builds\lixnix_multi_nozzle_probe `
      -G "Visual Studio 17 2022" `
      -A x64
```

Result:

`exit code 1`

Observed toolchain:

- CMake: `4.0.1`
- MSVC: `19.44.35209.0`
- Windows SDK selected by CMake: `10.0.22000.0`

Blocker:

```text
Could not find a package configuration file provided by "Boost" (requested
version 1.83.0) with any of the following names:

  BoostConfig.cmake
  boost-config.cmake
```

### Dependency Reuse Retry

The existing Snapmaker Orca dependency prefix was then reused:

`B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local`

Command attempted:

```powershell
cmake -S B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing `
      -B B:\ohmic\external_builds\lixnix_multi_nozzle_probe_reuse_deps `
      -G "Visual Studio 17 2022" `
      -A x64 `
      -DCMAKE_PREFIX_PATH="B:/ohmic/Snapmaker-OrcaSlicer/deps/build/OrcaSlicer_dep/usr/local"
```

Result:

- Boost blocker resolved using Boost `1.84.0` from the Snapmaker dependency cache.
- Configure then stopped at missing Eigen3 package config.

Observed Eigen blocker:

```text
Could not find a package configuration file provided by "Eigen3" (requested
version 5.0.1)
```

### Eigen Module Retry

The CGAL-provided `FindEigen3.cmake` module from the existing dependency prefix was then added:

`B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\CGAL`

Result:

- CMake found the Eigen module.
- Configure then stopped because `EIGEN3_INCLUDE_DIR` was unset.

Observed Eigen include blocker:

```text
Could NOT find Eigen3 (missing: EIGEN3_INCLUDE_DIR) (Required is at least
version "5.0.1")
```

### Eigen Include Retry

The existing Eigen source include root was then passed explicitly:

`B:\ohmic\Snapmaker-OrcaSlicer\deps_src\eigen`

Command attempted:

```powershell
cmake -S B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing `
      -B B:\ohmic\external_builds\lixnix_multi_nozzle_probe_reuse_deps_eigen_include `
      -G "Visual Studio 17 2022" `
      -A x64 `
      -DCMAKE_PREFIX_PATH="B:/ohmic/Snapmaker-OrcaSlicer/deps/build/OrcaSlicer_dep/usr/local" `
      -DCMAKE_MODULE_PATH="B:/ohmic/Snapmaker-OrcaSlicer/deps/build/OrcaSlicer_dep/usr/local/lib/cmake/CGAL" `
      -DEIGEN3_INCLUDE_DIR="B:/ohmic/Snapmaker-OrcaSlicer/deps_src/eigen"
```

Result:

- Boost resolved.
- Eigen resolved.
- Configure progressed through OpenVDB, CGAL, OpenCV, JPEG, GMP, MPFR, and other dependencies.
- Configure then stopped at missing Draco.

Final blocker:

```text
CMake Error at cmake/modules/Finddraco.cmake:20 (message):
  Draco library not found.  Please install the dependency.
```

No Draco config, header, or dependency artifact was found in the reused Snapmaker dependency cache. Targeted checks for `draco/draco_features.h`, `draco.lib`, `draco.dll`, and Draco CMake config files were negative in:

- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps_src`
- `B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing\deps_src`
- prior B-drive Snapmaker/Orca build trees under `B:\ohmic\builds`

The external LixNix dependency recipe does include Draco:

`B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing\deps\Draco\Draco.cmake`

The recipe downloads Draco `1.5.7` from:

`https://github.com/google/draco/archive/refs/tags/1.5.7.zip`

### Bounded Draco Resolution Attempt

A bounded dependency-only build was attempted in:

`B:\ohmic\external_builds\lixnix_deps_draco_only`

Dependency configure command:

```powershell
B:\ohmic\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe `
  -S B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing\deps `
  -B B:\ohmic\external_builds\lixnix_deps_draco_only `
  -G "Visual Studio 17 2022" `
  -A x64 `
  -DDEP_DOWNLOAD_DIR="B:/ohmic/external/OrcaSlicer-multi-nozzle-size-printing/deps/DL_CACHE"
```

Targeted dependency build command:

```powershell
B:\ohmic\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe `
  --build B:\ohmic\external_builds\lixnix_deps_draco_only `
  --config Release `
  --target dep_Draco `
  -- /m:4
```

Result:

- `dep_Draco` built and installed successfully.
- CMake version used: `3.31.8`
- MSVC version reported by configure: `19.44.35209.0`

Installed Draco artifacts:

- `B:\ohmic\external_builds\lixnix_deps_draco_only\OrcaSlicer_dep\usr\local\include\draco\draco_features.h`
- `B:\ohmic\external_builds\lixnix_deps_draco_only\OrcaSlicer_dep\usr\local\lib\draco.lib`
- `B:\ohmic\external_builds\lixnix_deps_draco_only\OrcaSlicer_dep\usr\local\share\cmake\draco\draco-config.cmake`
- `B:\ohmic\external_builds\lixnix_deps_draco_only\OrcaSlicer_dep\usr\local\share\cmake\draco\draco-targets.cmake`

### Configure Retry With Draco

Main LixNix configure was retried in:

`B:\ohmic\external_builds\lixnix_multi_nozzle_probe_with_draco_q2`

Command attempted:

```powershell
B:\ohmic\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe `
  -S B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing `
  -B B:\ohmic\external_builds\lixnix_multi_nozzle_probe_with_draco_q2 `
  -G "Visual Studio 17 2022" `
  -A x64 `
  -DCMAKE_PREFIX_PATH="B:/ohmic/Snapmaker-OrcaSlicer/deps/build/OrcaSlicer_dep/usr/local;B:/ohmic/external_builds/lixnix_deps_draco_only/OrcaSlicer_dep/usr/local" `
  -DCMAKE_MODULE_PATH="B:/ohmic/Snapmaker-OrcaSlicer/deps/build/OrcaSlicer_dep/usr/local/lib/cmake/CGAL" `
  -DEIGEN3_INCLUDE_DIR="B:/ohmic/Snapmaker-OrcaSlicer/deps_src/eigen"
```

Result:

- The previous Draco blocker was resolved.
- Configure progressed past Boost, Eigen, OpenVDB, CGAL, OpenCV, JPEG, Draco, GMP, and MPFR.
- Configure then stopped on later dependency configuration issues before an executable was produced.

Remaining blockers observed:

```text
CMake Error at B:/ohmic/Snapmaker-OrcaSlicer/deps/build/dep_OCCT-prefix/src/dep_OCCT-build/OpenCASCADEConfig.cmake:95 (include):
  include could not find requested file:
    OpenCASCADEFoundationClassesTargets.cmake
    OpenCASCADEModelingDataTargets.cmake
    OpenCASCADEModelingAlgorithmsTargets.cmake
    OpenCASCADEVisualizationTargets.cmake
    OpenCASCADEApplicationFrameworkTargets.cmake
    OpenCASCADEDataExchangeTargets.cmake
```

```text
CMake Error at src/CMakeLists.txt:36 (find_package):
  Could not find a package configuration file provided by "wxWidgets"
  (requested version 3.3)
```

Interpretation:

Draco is no longer the current blocker after the targeted dependency build. Runtime probing remains blocked because the reused Snapmaker dependency prefix does not provide a cleanly reusable OpenCASCADE/wxWidgets configuration for this external LixNix configure.

Because configure still stopped before an executable was produced, no runtime slicing probe was performed.

### Bounded OpenCASCADE / wxWidgets Resolution Attempt

A bounded follow-up pass checked the remaining OpenCASCADE and wxWidgets blockers.

OpenCASCADE / OCCT artifacts found in the reused Snapmaker dependency prefix:

- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\occt\OpenCASCADEConfig.cmake`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\occt\OpenCASCADEFoundationClassesTargets.cmake`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\occt\OpenCASCADEModelingDataTargets.cmake`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\occt\OpenCASCADEModelingAlgorithmsTargets.cmake`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\occt\OpenCASCADEVisualizationTargets.cmake`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\occt\OpenCASCADEApplicationFrameworkTargets.cmake`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\cmake\occt\OpenCASCADEDataExchangeTargets.cmake`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\bin\occt\TKernel.dll`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\bin\occt\TK*.dll`

wxWidgets artifacts found in the reused Snapmaker dependency prefix:

- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxbase31u.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxmsw31u_core.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxmsw31u_adv.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxmsw31u_html.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxmsw31u_gl.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxmsw31u_aui.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxmsw31u_net.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\wxmsw31u_media.lib`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\lib\vc_x64_lib\mswu\wx\setup.h`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\include\wx`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local\include\msvc\wx\setup.h`

No `wxWidgetsConfig.cmake` or `wxWidgetsTargets.cmake` was found in the reused dependency prefix. This matters because the LixNix Windows CMake path calls:

```cmake
find_package(wxWidgets 3.3 CONFIG REQUIRED COMPONENTS html adv gl core base webview aui net media)
```

The LixNix OpenCASCADE path is also sensitive to `CMAKE_PREFIX_PATH` shape:

```cmake
set(OpenCASCADE_DIR "${CMAKE_PREFIX_PATH}/lib/cmake/occt")
find_package(OpenCASCADE REQUIRED)
```

Using a semicolon-list `CMAKE_PREFIX_PATH` caused OpenCASCADE path confusion. A no-GUI retry used a single Snapmaker dependency prefix, passed Draco separately with `draco_DIR`, and disabled GUI to avoid the wxWidgets config requirement.

No-GUI configure retry directory:

`B:\ohmic\external_builds\lixnix_multi_nozzle_probe_cli_nogui`

Command attempted:

```powershell
B:\ohmic\tools\cmake-3.31.8-windows-x86_64\bin\cmake.exe `
  -S B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing `
  -B B:\ohmic\external_builds\lixnix_multi_nozzle_probe_cli_nogui `
  -G "Visual Studio 17 2022" `
  -A x64 `
  -DSLIC3R_GUI=OFF `
  -DCMAKE_PREFIX_PATH="B:/ohmic/Snapmaker-OrcaSlicer/deps/build/OrcaSlicer_dep/usr/local" `
  -DCMAKE_MODULE_PATH="B:/ohmic/Snapmaker-OrcaSlicer/deps/build/OrcaSlicer_dep/usr/local/lib/cmake/CGAL" `
  -DEIGEN3_INCLUDE_DIR="B:/ohmic/Snapmaker-OrcaSlicer/deps_src/eigen" `
  -Ddraco_DIR="B:/ohmic/external_builds/lixnix_deps_draco_only/OrcaSlicer_dep/usr/local/share/cmake/draco"
```

Result:

- `SLIC3R_GUI=OFF` avoided the wxWidgets config blocker.
- Keeping `CMAKE_PREFIX_PATH` to a single Snapmaker dependency prefix avoided the OpenCASCADE target-file blocker.
- Configure progressed past Boost, OpenCASCADE, Draco, OpenVDB, CGAL, OpenCV, JPEG, GMP, MPFR, and other dependencies.
- CMake generation then failed because the imported Eigen target was missing.

Remaining blocker:

```text
CMake Error at deps_src/admesh/CMakeLists.txt:20 (target_link_libraries):
  Target "admesh" links to:
    Eigen3::Eigen
  but the target was not found.

CMake Error at deps_src/clipper/CMakeLists.txt:17 (target_link_libraries):
  Target "clipper" links to:
    Eigen3::Eigen
  but the target was not found.

CMake Error at src/libslic3r/CMakeLists.txt:577 (target_link_libraries):
  Target "libslic3r" links to:
    Eigen3::Eigen
  but the target was not found.
```

Bounded searches did not find a local `Eigen3Config.cmake`, `eigen3-config.cmake`, `Eigen3Targets.cmake`, or `signature_of_eigen3_matrix_library`.

Interpretation:

The bounded OpenCASCADE/wxWidgets pass resolved the specific OpenCASCADE and wx blockers for a no-GUI configure path, but runtime probing remains blocked by external dependency configuration because the LixNix branch expects an `Eigen3::Eigen` imported target that is not available from the reused local dependency artifacts.

## Self-Generated Probe Harness

AMP now owns the probe geometry and inspection harness. We do not need the LixNix author to provide models.

Probe model generator:

`tools/amp_generate_lixnix_probe_models.py`

Ignored generated models:

- `outputs/lixnix_runtime_probe/models/lixnix_two_object_detail_bulk.stl`
- `outputs/lixnix_runtime_probe/models/lixnix_four_region_tool_ladder.stl`
- `outputs/lixnix_runtime_probe/models/lixnix_support_restriction_probe.stl`
- `outputs/lixnix_runtime_probe/models/lixnix_layer_height_probe.stl`

Generated model intent:

- Two-object detail/bulk probe for manual object assignment.
- Four-region tool ladder for 0.2 / 0.4 / 0.6 / 0.8 style manual assignment.
- Support restriction probe for `support_nozzle_diameter` behavior.
- Layer-height probe for per-extruder layer-height behavior.

G-code inspection tool:

`tools/amp_inspect_mixed_nozzle_gcode.py`

Expected future use:

```powershell
python tools/amp_inspect_mixed_nozzle_gcode.py outputs/lixnix_runtime_probe/gcode --out outputs/lixnix_runtime_probe/reports
```

The inspector reports nozzle diameter metadata, print settings id, T command counts, active tools, Z/layer-height patterns, per-tool extrusion counts, wipe/purge/support comment hits, line-width comment hits, and warnings when output appears to contain only one tool or one nozzle value.

Checklist:

`docs/research/AMP_LixNix_Self_Generated_Probe_Checklist.md`

## Runtime Probe Result

### Build Status Update

The external LixNix branch was eventually built far enough to produce a runnable Windows executable for local probing.

Runnable probe executable:

`B:\ohmic\external_builds\lixnix_runtime_probe\run_direct\orca-slicer.exe`

Build source branch:

`multi_nozzle_multi_layer_height`

Build source commit:

`944da137d8b36427c6659d83148a149e6c6eaa1e`

Important build caveat:

The GUI app build required an external-probe-only linker workaround, `/FORCE:MULTIPLE`, because the mixed dependency set produced duplicate JPEG symbols from `libjpeg-turbo.lib` and `jpeg-static.lib`. This is not an upstreamable build fix and was used only to enable runtime inspection.

Additional build fixes/conditions discovered:

- LixNix needs Eigen available as an imported `Eigen3::Eigen` target.
- A targeted Eigen 5.0.1 install was used for the successful build path.
- A targeted Draco dependency build resolved the earlier missing-Draco blocker.
- CGAL 5.6.3 was used.
- The Windows build needed explicit `/DWIN32=1` and `/EHsc` in the successful local configuration.
- Keeping `CMAKE_PREFIX_PATH` focused on the Snapmaker dependency prefix avoided the earlier OpenCASCADE path confusion.
- wxWidgets 3.3.2 had to be built from the LixNix dependency recipe for the GUI target.

### Single-Model Control

A direct single-model CLI control exported G-code successfully.

Output:

`B:\ohmic\external_builds\lixnix_runtime_probe\gcode\direct_single_model_control_0p10_abs_0p84_bridge_0p2_layer_g92\plate_1.gcode`

Observed:

- CLI exit code: `0`
- G-code exported.
- Header reported `OrcaSlicer 2.5.0-dev`.
- `;HEIGHT:0.1` markers were present.
- Width comments reflected the scratch process settings.
- Only one filament/tool was active in this control.

Interpretation:

The executable is runnable and can export G-code from the external branch. This control does not prove mixed-nozzle output.

### Four-Object Assemble-List Probe

The first four-object assemble-list probe used the AMP-generated four-region tool-ladder geometry. It initially failed because one object was placed partly outside the bed.

Observed failure:

```text
plate 1, object bbox: min {-45, -55, 0} - max {170, 87, 62}
plate 1: Found Object lixnix_four_region_tool_ladder_1 partly inside, can not be sliced.
```

The shifted four-object retry entered the slicer but opened a GUI window and did not complete as a clean CLI job in the bounded runtime window. That run was stopped and not treated as a valid result.

Interpretation:

The four-object probe remains useful, but it is too large/flaky for first-pass runtime proof. The smaller two-object probes below produced clearer data.

### Two-Object 0.4 / 0.8 Runtime Probe

A reduced two-object probe was run with scratch-only external configs:

- tool/extruder 1: `0.4` nozzle-class proxy
- tool/extruder 2: `0.8` nozzle-class proxy
- manual filament map: `1,2`
- generated G-code outputs kept outside the repo under `B:\ohmic\external_builds`

The first reduced run failed with:

```text
Line width too small
```

Root cause:

The machine config still included the `0.2` tool. LixNix validation considered the smallest nozzle in the mixed machine when checking line/bridge constraints, so a reduced 0.4/0.8 probe needed a scratch 0.4/0.8-only machine config.

The 0.4/0.8 scratch machine then failed once with:

```text
CLI_PROCESS_NOT_COMPATIBLE
```

Root cause:

The scratch process lacked `compatible_printers`. Adding `compatible_printers: ["MyToolChanger 0.4 nozzle"]` allowed the probe to proceed.

Successful two-object outputs:

- `B:\ohmic\external_builds\lixnix_runtime_probe\gcode\assemble_two_object_0p4_0p8_probe_compatible\plate_1.gcode`
- `B:\ohmic\external_builds\lixnix_runtime_probe\gcode\assemble_two_object_0p4_0p8_probe_manual_map\plate_1.gcode`
- `B:\ohmic\external_builds\lixnix_runtime_probe\gcode\assemble_two_object_0p4_0p8_probe_variant_filaments\plate_1.gcode`
- `B:\ohmic\external_builds\lixnix_runtime_probe\gcode\direct_two_model_0p4_0p8_load_filament_ids\plate_1.gcode`

Observed in exported G-code:

- G-code export succeeded with exit code `0`.
- Width comments such as `;WIDTH:0.42` and `;WIDTH:0.84` were observed in assemble-list probes.
- Layer-height comments included values around `0.2` and occasional `0.4` combined-layer markers.
- Direct two-model input with `--load-filament-ids 1,2` also exported successfully.

Not observed in exported G-code:

- No plain `T0`, `T1`, `T2`, or `T3` tool-change commands were observed in the tested CLI outputs.
- Headers still reported `; filament: 1` in the tested outputs.
- No multi-nozzle `nozzle_diameter` header metadata suitable for U1 validation was observed.

Additional source/log finding:

LixNix does not treat different `nozzle_diameter` values alone as enough to mark extruders different. The branch's `support_different_extruders()` path checks `extruder_variant_list` diversity. Adding scratch variant metadata made the log report:

```text
extruder_count=2, different_extruder=1
```

Even with manual filament mapping and variant-mapped scratch filament profiles, the CLI outputs tested here still did not emit observable `T` tool-change commands.

Interpretation:

The runtime probe confirms that the LixNix branch can build and can emit G-code that reflects different width/layer behavior under scratch mixed-extruder configurations. It does not yet prove real mixed-nozzle tool-change G-code emission from the tested CLI paths.

## Source-Level Behavior Map

### Per-Extruder Nozzle Lookup

Files:

- `src/libslic3r/PrintConfig.cpp`
- `src/libslic3r/PrintConfig.hpp`
- `src/libslic3r/Flow.cpp`
- `src/libslic3r/Fill/Fill.cpp`
- `src/libslic3r/LayerRegion.cpp`
- `src/libslic3r/PrintObject.cpp`
- `src/libslic3r/Support/SupportMaterial.cpp`
- `src/libslic3r/Support/TreeSupport.cpp`

Behavior:

The fork introduces and uses nozzle-diameter lookup based on the filament or mapped extruder that actually prints a feature. This avoids assuming that filament id and physical extruder/nozzle index are always identical.

Risk level:

Medium. The idea is sound, but the lookup affects flow, fill, support, and region behavior.

AMP equivalent:

AMP currently has offline tool-class metadata and plan packets, not production slicer lookup integration.

Lesson:

Future AMP C++ integration should separate logical region/filament/tool identity from physical nozzle identity.

### Per-Extruder Layer Height

Files:

- `src/libslic3r/PrintConfig.cpp`
- `src/libslic3r/PrintConfig.hpp`
- `src/libslic3r/Print.cpp`
- `src/libslic3r/Print.hpp`
- `src/libslic3r/PrintObject.cpp`
- `src/libslic3r/PrintObjectSlice.cpp`
- `src/libslic3r/Layer.cpp`
- `src/libslic3r/Layer.hpp`
- `src/libslic3r/LayerRegion.cpp`

Key options:

- `extruder_layer_height`
- `extruder_layer_height_mode`
- `extruder_layer_height_tolerance`

Key functions/classes:

- `PrintObject::extruder_preferred_layer_height`
- `PrintObject::layer_height_multiplier_for_filament`
- `PrintObject::region_layer_height_multiplier`
- `PrintObject::has_combined_layer_regions`
- `PrintObject::apply_extruder_layer_heights`
- `LayerRegion::combined_height`
- `LayerRegion::combined_layer_count`

Behavior:

Regions assigned to an extruder with a preferred coarse layer height can be combined into thicker extrusion layers when the geometry permits. The code validates integer multiples of object layer height and checks nozzle/min/max layer-height constraints. Combined-away layers carry no slices for that region.

Risk level:

High. This changes slicing, layer ownership, surface processing, perimeters, fill, and tool ordering.

AMP equivalent:

AMP has offline continuous resolution demand and tool assignment planning. It does not yet modify layer generation.

Lesson:

Layer height is a first-class part of resolution allocation. AMP should continue treating bead width, nozzle/tool class, and layer height as coupled planning dimensions.

### Combined Layer Regions

Files:

- `src/libslic3r/PrintObjectSlice.cpp`
- `src/libslic3r/Layer.cpp`
- `src/libslic3r/Layer.hpp`
- `src/libslic3r/LayerRegion.cpp`
- `src/libslic3r/PerimeterGenerator.cpp`
- `src/libslic3r/PerimeterGenerator.hpp`
- `src/libslic3r/PrintObject.cpp`

Behavior:

`PrintObject::apply_extruder_layer_heights` greedily combines compatible layer runs for regions whose extruder prefers a thicker layer. It avoids combining across unsupported or incompatible geometry. Top/bottom surfaces and difficult geometry remain finer where needed.

Risk level:

High. This is hot-path slicer behavior.

AMP equivalent:

AMP can currently recommend tool/layer strategies offline, but it does not change layer topology.

Lesson:

Any future AMP behavior-changing implementation must have deterministic tests around top surfaces, overhangs, support, internal surfaces, and fallback regions.

### Support Nozzle Restrictions

Files:

- `src/libslic3r/PrintConfig.cpp`
- `src/libslic3r/PrintConfig.hpp`
- `src/libslic3r/Flow.cpp`
- `src/libslic3r/Print.cpp`
- `src/libslic3r/PrintObject.cpp`
- `src/libslic3r/GCode.cpp`
- `src/libslic3r/GCode/ToolOrdering.cpp`
- `src/libslic3r/Slicing.cpp`
- `src/slic3r/GUI/ConfigManipulation.cpp`
- `src/slic3r/GUI/Tab.cpp`

Key option:

- `support_nozzle_diameter`

Key functions:

- `PrintObject::support_filament_allowed`
- `PrintObject::resolved_default_support_filament`

Behavior:

Support, raft, or interface behavior can be restricted to extruders whose nozzle diameter matches the configured support nozzle diameter. Validation reports errors when no matching extruder exists.

Risk level:

Medium to high. Support selection affects geometry, flow, first layer, and tool ordering.

AMP equivalent:

AMP has offline support-region categories and tool-class planning, but no slicer support routing.

Lesson:

Support should be a separate planning category. It should not simply inherit bulk-region nozzle choices.

### Tool Ordering

Files:

- `src/libslic3r/GCode/ToolOrdering.cpp`
- `src/libslic3r/GCode.cpp`

Behavior:

Tool ordering accounts for combined-away layers and support nozzle restrictions. Empty layer tools created by combined regions are skipped when appropriate. The source indicates the feature uses Orca's existing tool ordering and toolchange mechanisms with mixed-nozzle-aware scheduling changes.

Risk level:

High. Incorrect tool ordering can corrupt output or create unsafe execution assumptions.

AMP equivalent:

AMP has an offline scheduler and execution packet contract, not production G-code tool ordering.

Lesson:

AMP's scheduler remains useful. Even if slicer internals later execute a plan, the advisory packet should preserve ordered tool-class decisions and fallback reasons.

### Wipe Tower / Purge

Files:

- `src/libslic3r/GCode/WipeTower2.cpp`
- `src/libslic3r/GCode/WipeTower2.hpp`

Key helper:

- `tool_perimeter_width`

Behavior:

Wipe tower and purge calculations use tool-specific line widths. The code distinguishes the line width of the old/new tool during ramming, wipe, planned wipe depth, and finish-layer calculations.

Risk level:

High. Wipe and purge behavior is critical for real multi-tool output.

AMP equivalent:

AMP has a Fluidd/Klipper sandbox and hardware preflight gate, but no production wipe tower integration.

Lesson:

Physical mixed-nozzle behavior cannot be represented only as `Tn` changes. Purge/wipe volume and geometry must be nozzle-aware.

### Tests

File:

- `tests/fff_print/test_multi_nozzle_layer_height.cpp`

Coverage observed:

- per-extruder layer height combines region layers
- per-extruder layer height respects minimum layer height
- feature filament assignment controls combined infill behavior
- fill line width follows the filament that prints the surface
- combined infill respects maximum layer-height limits
- support nozzle diameter restricts support printing
- raft behavior preserves bottom surfaces of combined regions
- invalid per-extruder layer-height configurations are rejected

Risk level:

Positive signal. The branch has meaningful source-level unit coverage, but local test execution was not possible because configure was blocked.

AMP equivalent:

AMP has focused tests for value types, debug artifacts, packet contract, adapter output validation, and offline solver behavior.

Lesson:

If AMP later enters the slicer hot path, it should add fff_print-style tests before any production integration.

## G-code Findings

Generated G-code was observed after the external branch was built locally.

Observed:

- Single-model control G-code exported successfully.
- Two-object 0.4/0.8 scratch probes exported successfully.
- Width comments changed according to the scratch process/object settings.
- Layer-height comments included normal `0.2` values and occasional `0.4` combined-layer markers.
- LixNix logs showed manual filament-map mode when `--filament-map-mode Manual --filament-map 1,2` was supplied.
- LixNix logs showed `different_extruder=1` after scratch `extruder_variant_list` metadata was added.

Not observed:

- No `T0` / `T1` / `T2` / `T3` tool-change commands were observed in the tested CLI G-code outputs.
- Header metadata still reported a single filament in the tested outputs.
- No U1-compatible mixed-nozzle header behavior was observed.

Source-level findings still suggest:

- multiple nozzle diameters can influence flow and support calculations
- tool ordering is modified for combined layers and support restrictions
- wipe tower planning uses tool-specific line widths

Unproven:

- exact emitted tool commands for a fully configured LixNix mixed-nozzle workflow
- whether the branch requires GUI/project setup rather than CLI assemble-list/direct-model setup for true tool changes
- generated header shape for a confirmed multi-tool output
- whether multiple `nozzle_diameter` values appear in a way compatible with U1 or another target printer
- whether a generated project can round-trip through save/load and preserve these settings

## 3MF / Project Findings

No runtime 3MF/project save-load test was performed.

Source-level finding:

The branch adds normal PrintConfig keys rather than a dedicated sidecar or explicit 3MF schema. Those keys may persist through Orca's existing project/config path, but this probe did not verify that behavior.

Comparison to AMP:

- LixNix has slicer-native config keys.
- AMP has sidecar/advisory plan bundles and execution packets.
- LixNix does not appear to replace AMP's sidecar bundle because it does not carry planner confidence, region reasoning, or fallback metadata.

## LixNix vs AMP Comparison

| Capability | LixNix branch | AMP current branch | Gap | Lesson |
| --- | --- | --- | --- | --- |
| Official Orca manual/static baseline | Separate official Orca workflow exists and should be tested first. | AMP can compare its packet assignment against official manual assignment. | Baseline runtime test still needs to be run. | Do not treat external forks as the only mixed-nozzle path. |
| Per-extruder nozzle lookup | Implemented in slicer paths. | Offline tool matrix and packet metadata. | AMP has no production slicer lookup integration. | Future integration must map logical region/tool to physical nozzle carefully. |
| Per-extruder layer height | Implemented with `extruder_layer_height` and combined layers. | Planned offline through resolution demand and tool assignment. | AMP does not alter layer topology. | Layer height must be co-planned with nozzle class. |
| Geometry-driven automatic assignment | Not identified. Appears manual/per-feature/per-extruder. | Offline automatic planning exists. | AMP still needs eventual slicer integration. | AMP's planner layer remains distinct. |
| Cost gating | Not identified as planner cost model. | Implemented offline. | LixNix has slicer execution mechanics, not AMP-style decision economics. | Keep AMP cost gates. |
| Confidence/fallback | Not identified. | Implemented in packets and artifacts. | LixNix lacks advisory explainability. | Preserve fallback reasons. |
| Support nozzle restrictions | Implemented. | Offline category only. | AMP does not route support in slicer. | Support should remain its own planning class. |
| Wipe tower/purge handling | Implemented at source level. | Sandbox/adapter only, no slicer wipe tower. | AMP does not modify wipe tower. | Future execution needs nozzle-aware purge math. |
| 3MF/project preservation | Not verified; likely normal config persistence only. | Sidecar plan bundle exists. | Neither path is proven as final U1 representation. | Sidecar remains useful for planner metadata. |
| G-code toolchange emission | Runtime probe exported G-code, but tested CLI paths did not emit observable `T` tool-change commands. Source changes tool ordering. | No production G-code changes. | AMP intentionally lacks production emission. | Do not shortcut into output without validation. |
| Safety/nozzle validation | Not U1-specific. | U1 validation remains blocked/gated. | LixNix does not solve U1 touchscreen constraints. | Keep U1 hardware gates. |
| Tests | fff_print tests added. | Focused AMP unit/offline tests exist. | Runtime probe is partial: export works, true tool-change emission is unconfirmed. | Study test patterns before hot-path AMP work. |
| Hardware validation | Not found in repo docs. | Not yet available for U1 mixed nozzle. | Both remain hardware-unvalidated for U1. | No physical claims. |

## Required Conclusions

### Does LixNix emit real mixed-nozzle G-code?

Not proven by this probe. A local executable was produced and G-code was inspected, but the tested CLI paths did not emit observable `T0` / `T1` / `T2` / `T3` tool-change commands. The branch does emit G-code with different width/layer behavior under scratch mixed-extruder configurations, and logs can report `different_extruder=1`, but true mixed-nozzle tool-change output remains unconfirmed.

### Does it preserve multiple nozzle diameters in headers/project data?

Not proven. Runtime G-code headers inspected in this probe still reported a single filament and did not expose a U1-useful multi-nozzle header shape. The branch uses normal config keys and per-extruder values, but project persistence and header behavior still require a dedicated save/load or GUI workflow test.

### Does it implement per-extruder layer height?

Yes, at source level. The branch adds `extruder_layer_height`, validation, combined-layer region behavior, and tests.

### Does it solve support/wipe tower/tool ordering better than AMP currently does?

It implements source-level support, wipe tower, and tool ordering changes that AMP intentionally does not yet have in production slicer code. It is more advanced in hot-path slicer execution mechanics, but AMP is more advanced in offline planner reasoning, confidence, cost gating, and execution gating.

### Does it provide a representation path better than our sidecar bundle?

Not clearly. It provides slicer-native settings, which are useful for execution, but it does not appear to represent AMP-style region reasoning, confidence, cost, or fallback data. The AMP sidecar bundle remains valuable.

### Is it manual infrastructure or automated geometry-driven planning?

It appears to be manual/per-feature/per-extruder infrastructure with per-extruder layer-height behavior. It is not an automated geometry-driven AMP planner.

### Should AMP contact the author?

Yes. The implementation is meaningful enough that comparing notes is worthwhile, especially around project persistence, wipe tower behavior, tests, and intended hardware targets.

## What AMP Should Learn

- Treat filament, extruder, tool, and physical nozzle as separate concepts.
- Co-plan nozzle/tool class and layer height.
- Keep support/interface/raft as special planning categories.
- Do not ignore wipe tower and purge math.
- Add hot-path tests before any behavior-changing slicer integration.
- Preserve AMP's explainable planner packet even if execution eventually moves into slicer internals.

## What AMP Should Not Copy

- Do not copy core slicer changes into the AMP branch without a dedicated implementation plan.
- Do not assume Bambu/H2D/X2D behavior maps to Snapmaker U1.
- Do not bypass U1 touchscreen validation.
- Do not claim physical mixed-nozzle behavior works from source inspection.
- Do not replace AMP's planner/sidecar/execution-gate architecture with manual assignment plumbing.

## Recommended Next Action

Recommended next steps:

1. Keep LixNix on the AMP toolchanger watchlist.
2. Contact the author using `docs/community/AMP_LixNix_Collaboration_Draft.md`.
3. Ask the LixNix author for the intended mixed-nozzle workflow, especially whether true tool-change G-code is expected through GUI/project setup, CLI direct input, assemble-list input, or another path.
4. Ask which config fields are required for a confirmed mixed-tool output, including `filament_map`, `filament_map_mode`, `extruder_variant_list`, `filament_extruder_variant`, and any project-only metadata.
5. Ask for expected G-code examples or test outputs if available; AMP will provide its own probe geometry.
6. Use LixNix tests as inspiration for future AMP hot-path tests.
7. Do not start production AMP slicer integration from this fork until U1 safety constraints and AMP's own representation boundary are stronger.

Bottom line:

The LixNix branch is the most concrete external deeper mixed-nozzle/per-extruder-layer-height slicer-infrastructure example found so far, but official Orca mixed nozzle-size support is now the first manual/static baseline. The local LixNix runtime probe confirms the branch is buildable with work and can emit G-code influenced by mixed width/layer settings, but the tested CLI paths did not prove actual mixed-tool `T` command emission. It strengthens AMP's direction rather than replacing it: official Orca covers manual/static assignment, LixNix shows how hard deeper execution becomes inside slicer internals, and AMP remains the planner, packet, sidecar, and gated-execution layer.
