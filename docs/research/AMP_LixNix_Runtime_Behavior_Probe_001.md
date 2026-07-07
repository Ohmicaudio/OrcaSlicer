# AMP LixNix Runtime Behavior Probe 001

## Purpose

This probe follows the source audit in `docs/research/AMP_LixNix_Multi_Nozzle_Fork_Audit_001.md` by checking whether the external LixNix `multi_nozzle_multi_layer_height` branch can be built or runtime-probed locally, and by mapping the branch's behavior from source when a build is blocked.

This is external fork testing only. It does not merge LixNix code, does not mean AMP implements mixed-nozzle slicing, does not bypass Snapmaker validation, and does not prove touchscreen-compatible mixed-nozzle behavior.

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

No Draco config, header, or dependency artifact was found in the reused Snapmaker dependency cache. Targeted checks for `draco/draco_features.h` were negative in:

- `B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local`
- `B:\ohmic\Snapmaker-OrcaSlicer\deps_src`
- `B:\ohmic\external\OrcaSlicer-multi-nozzle-size-printing\deps_src`
- prior B-drive Snapmaker/Orca build trees under `B:\ohmic\builds`

Because configure still stopped before an executable was produced, no runtime slicing probe was performed.

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

No runtime G-code was generated from the LixNix branch in this probe. The second build pass resolved the earlier Boost and Eigen blockers, but configure still failed before producing an executable because Draco was unavailable.

The probe geometry and inspector are now ready for a future run if the LixNix branch can be built.

Not observed:

- G-code header behavior
- emitted `T0` / `T1` / `T2` / `T3` sequences
- actual layer-height changes in exported G-code
- actual wipe tower geometry
- 3MF save/load persistence
- physical print behavior

This means the probe cannot claim that LixNix emits validated mixed-nozzle G-code. The source and tests indicate intended behavior, but runtime output remains unverified locally.

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

No generated G-code was observed.

Source-level findings suggest:

- multiple nozzle diameters can influence flow and support calculations
- tool ordering is modified for combined layers and support restrictions
- wipe tower planning uses tool-specific line widths

Unproven:

- exact emitted tool commands
- generated header shape
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
| Per-extruder nozzle lookup | Implemented in slicer paths. | Offline tool matrix and packet metadata. | AMP has no production slicer lookup integration. | Future integration must map logical region/tool to physical nozzle carefully. |
| Per-extruder layer height | Implemented with `extruder_layer_height` and combined layers. | Planned offline through resolution demand and tool assignment. | AMP does not alter layer topology. | Layer height must be co-planned with nozzle class. |
| Geometry-driven automatic assignment | Not identified. Appears manual/per-feature/per-extruder. | Offline automatic planning exists. | AMP still needs eventual slicer integration. | AMP's planner layer remains distinct. |
| Cost gating | Not identified as planner cost model. | Implemented offline. | LixNix has slicer execution mechanics, not AMP-style decision economics. | Keep AMP cost gates. |
| Confidence/fallback | Not identified. | Implemented in packets and artifacts. | LixNix lacks advisory explainability. | Preserve fallback reasons. |
| Support nozzle restrictions | Implemented. | Offline category only. | AMP does not route support in slicer. | Support should remain its own planning class. |
| Wipe tower/purge handling | Implemented at source level. | Sandbox/adapter only, no slicer wipe tower. | AMP does not modify wipe tower. | Future execution needs nozzle-aware purge math. |
| 3MF/project preservation | Not verified; likely normal config persistence only. | Sidecar plan bundle exists. | Neither path is proven as final U1 representation. | Sidecar remains useful for planner metadata. |
| G-code toolchange emission | Not runtime-verified; source changes tool ordering. | No production G-code changes. | AMP intentionally lacks production emission. | Do not shortcut into output without validation. |
| Safety/nozzle validation | Not U1-specific. | U1 validation remains blocked/gated. | LixNix does not solve U1 touchscreen constraints. | Keep U1 hardware gates. |
| Tests | fff_print tests added. | Focused AMP unit/offline tests exist. | Runtime probe blocked locally. | Study test patterns before hot-path AMP work. |
| Hardware validation | Not found in repo docs. | Not yet available for U1 mixed nozzle. | Both remain hardware-unvalidated for U1. | No physical claims. |

## Required Conclusions

### Does LixNix emit real mixed-nozzle G-code?

Not proven by this probe. The branch modifies source paths that should affect mixed-nozzle slicing, tool ordering, and wipe tower behavior, but no local executable was produced and no G-code was inspected.

### Does it preserve multiple nozzle diameters in headers/project data?

Not proven. The branch uses normal config keys and per-extruder values. Project persistence and header behavior require runtime tests.

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
3. Ask the LixNix author for intended workflow, expected G-code behavior, and dependency/build instructions; AMP will provide its own probe geometry.
4. Use LixNix tests as inspiration for future AMP hot-path tests.
5. Do not start production AMP slicer integration from this fork until U1 safety constraints and AMP's own representation boundary are stronger.

Bottom line:

The LixNix branch is the most concrete external mixed-nozzle slicer-infrastructure example found so far. It strengthens AMP's direction rather than replacing it: LixNix shows how hard execution becomes inside slicer internals, while AMP remains the planner, packet, sidecar, and gated-execution layer.
