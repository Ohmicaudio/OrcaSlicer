# AMP LixNix Multi-Nozzle Orca Fork Audit 001

## Purpose

This audit reviews the external fork:

<https://github.com/LixNix/OrcaSlicer-multi-nozzle-size-printing>

The goal is to identify what the fork actually implements, whether it affects mixed physical nozzle workflows, and which ideas should inform Adaptive Manufacturing Planner (AMP) without merging or copying code into the AMP branch.

This is a source audit only. It does not validate the fork physically, does not mean AMP has mixed-nozzle slicing, does not merge or endorse the fork, does not bypass Snapmaker validation, and does not prove touchscreen-compatible mixed-nozzle behavior.

## External Repo Snapshot

Repository:

- URL: <https://github.com/LixNix/OrcaSlicer-multi-nozzle-size-printing>
- Default branch: `main`
- `main` HEAD inspected: `7abc216710e6e4b3ba89a9016d1b8fc9c4f7c45b`
- `main` HEAD date: `2026-06-30 02:05:09 +0200`
- `main` HEAD subject: `Refactor nozzle diameter retrieval logic`
- Feature branch inspected: `origin/multi_nozzle_multi_layer_height`
- Feature branch HEAD inspected: `944da137d8b36427c6659d83148a149e6c6eaa1e`
- Feature branch HEAD date: `2026-07-06 15:30:56 +0200`
- Feature branch HEAD subject: `Add per extruder layer height`
- GitHub releases found by `gh release list`: none
- README feature documentation: not found; visible README is generic OrcaSlicer documentation

Relevant remote branches:

- `origin/main`
- `origin/multi_nozzle_multi_layer_height`
- `origin/BCK-old`
- `origin/BCK-older`

## Changed-File Summary

### Default Branch

The default branch was compared against upstream OrcaSlicer using merge base:

`38ea91a6bb12d8d5eb153943e82bb69b1dc7bd9a`

`origin/main` changes 15 files with a small diff footprint:

- `src/libslic3r/Fill/Fill.cpp`
- `src/libslic3r/Flow.cpp`
- `src/libslic3r/GCode.cpp`
- `src/libslic3r/LayerRegion.cpp`
- `src/libslic3r/Print.cpp`
- `src/libslic3r/PrintConfig.cpp`
- `src/libslic3r/PrintConfig.hpp`
- `src/libslic3r/PrintObject.cpp`
- `src/libslic3r/PrintRegion.cpp`
- `src/libslic3r/Support/SupportMaterial.cpp`
- `src/libslic3r/Support/TreeSupport.cpp`
- `src/slic3r/GUI/AMSMaterialsSetting.cpp`
- `src/slic3r/GUI/Plater.cpp`
- `src/slic3r/GUI/SelectMachine.cpp`
- `src/slic3r/GUI/Tab.cpp`

The default branch primarily fixes nozzle-diameter lookup when filament identity and physical extruder identity are not the same.

### `multi_nozzle_multi_layer_height` Branch

The feature branch was compared against upstream OrcaSlicer using merge base:

`395e070a0e675fd4723f93967cefede730c482d9`

The feature branch changes 29 files:

- `src/libslic3r/Brim.cpp`
- `src/libslic3r/Fill/Fill.cpp`
- `src/libslic3r/Flow.cpp`
- `src/libslic3r/Flow.hpp`
- `src/libslic3r/GCode.cpp`
- `src/libslic3r/GCode/ToolOrdering.cpp`
- `src/libslic3r/GCode/WipeTower2.cpp`
- `src/libslic3r/GCode/WipeTower2.hpp`
- `src/libslic3r/Layer.cpp`
- `src/libslic3r/Layer.hpp`
- `src/libslic3r/LayerRegion.cpp`
- `src/libslic3r/PerimeterGenerator.cpp`
- `src/libslic3r/PerimeterGenerator.hpp`
- `src/libslic3r/Preset.cpp`
- `src/libslic3r/Print.cpp`
- `src/libslic3r/Print.hpp`
- `src/libslic3r/PrintConfig.cpp`
- `src/libslic3r/PrintConfig.hpp`
- `src/libslic3r/PrintObject.cpp`
- `src/libslic3r/PrintObjectSlice.cpp`
- `src/libslic3r/PrintRegion.cpp`
- `src/libslic3r/Slicing.cpp`
- `src/libslic3r/Support/SupportMaterial.cpp`
- `src/libslic3r/Support/SupportParameters.hpp`
- `src/libslic3r/Support/TreeSupport.cpp`
- `src/slic3r/GUI/ConfigManipulation.cpp`
- `src/slic3r/GUI/Tab.cpp`
- `tests/fff_print/CMakeLists.txt`
- `tests/fff_print/test_multi_nozzle_layer_height.cpp`

This branch is substantially more invasive than the default branch. It touches layer construction, region logic, perimeter generation, flow, support selection, tool ordering, and wipe tower behavior.

## Feature Classification

Classification:

- Default branch: Category 2, manual/per-extruder mixed nozzle plumbing.
- Feature branch: Category 2 plus partial Category 3-adjacent slicing support for per-extruder layer-height behavior.

The fork appears to support different nozzle diameter values per extruder and corrects nozzle-diameter lookup through filament-to-extruder mapping. The feature branch also adds per-extruder preferred layer heights and combines compatible region layers for coarse tools.

It is not a complete AMP-style automated geometry-driven planner. The inspected code does not appear to compute a continuous resolution field, score regions by cosmetic/structural importance, assign tool classes from cost gates, or produce confidence-bearing region plans. It relies on slicer configuration, filament/feature assignment, and per-extruder settings.

## Implementation Model

### Nozzle Diameter Lookup

The default branch adds:

- `nozzle_diameter_for_filament(const PrintConfig& config, int filament_id, bool is_bbl_printer)`

This helper maps a filament id to an extruder before reading `nozzle_diameter`, including Bambu-style `filament_map` handling. Direct `nozzle_diameter.get_at(filament - 1)` style reads are replaced across flow, fill, layer region, print object, support, and tree support paths.

AMP relevance:

- This is a useful implementation pattern. The future AMP C++ integration should avoid assuming that filament index, extruder index, and physical tool index are always identical.

### UI/Profile Plumbing

The default branch modifies GUI code around nozzle diameter selection. In `Plater.cpp`, it removes logic that forced left and right nozzle selectors to the same diameter and stores independent values into `nozzle_diameter`.

AMP relevance:

- This confirms that mixed nozzle UI behavior is partly a profile/config problem before it is a planner problem.
- It is not directly portable to Snapmaker U1 because U1 touchscreen validation and logical/physical tool mapping constraints are different.

### Per-Extruder Layer Height

The feature branch adds new configuration options:

- `extruder_layer_height`
- `extruder_layer_height_mode`
- `extruder_layer_height_tolerance`
- `support_nozzle_diameter`

The tooltip for `extruder_layer_height` describes printers whose extruders have different nozzle sizes. It allows object parts assigned to a coarse extruder to print every Nth layer where geometry allows, while preserving finer base layers when needed.

Important implementation paths:

- `PrintObject::extruder_preferred_layer_height`
- `PrintObject::layer_height_multiplier_for_filament`
- `PrintObject::region_layer_height_multiplier`
- `PrintObject::has_combined_layer_regions`
- `PrintObject::support_filament_allowed`
- `PrintObject::resolved_default_support_filament`
- `PrintObject::apply_extruder_layer_heights`

The code combines compatible runs of layers for regions whose printing filament/extruder has a preferred layer height that is an integer multiple of the object layer height. The implementation avoids combining across incompatible geometry, overhangs, nonuniform layer heights, and top/bottom constraints.

AMP relevance:

- This is the closest implementation found so far to AMP's long-term resolution-allocation direction.
- It supports the idea that layer height and nozzle/tool class should be planned together, not treated as separate afterthoughts.
- It still starts from assigned filaments/features; it does not appear to make AMP-style automatic tool decisions from region scoring.

## Key Code Paths

### PrintConfig / Profiles

Touched:

- `src/libslic3r/PrintConfig.cpp`
- `src/libslic3r/PrintConfig.hpp`
- `src/libslic3r/Preset.cpp`

Key findings:

- Adds per-extruder preferred layer-height configuration.
- Adds support nozzle diameter restriction.
- Adds config validation around layer height multiples and nozzle/max layer height constraints.
- Adds new options to extruder/printer option lists.

### Flow

Touched:

- `src/libslic3r/Flow.cpp`
- `src/libslic3r/Flow.hpp`

Key findings:

- Flow/nozzle lookup is made filament-aware.
- Feature branch tests verify that fill line width follows the filament that prints the surface.

### Layer / LayerRegion / PrintObject

Touched:

- `src/libslic3r/Layer.cpp`
- `src/libslic3r/Layer.hpp`
- `src/libslic3r/LayerRegion.cpp`
- `src/libslic3r/PrintObject.cpp`
- `src/libslic3r/PrintObjectSlice.cpp`

Key findings:

- Adds combined-layer concepts to layers and layer regions.
- Combined-away layers can carry no slices for a coarse region and therefore trigger no toolchange for that region.
- Top/bottom surfaces, overhangs, support, and incompatible geometry keep finer base-layer treatment.

### PerimeterGenerator

Touched:

- `src/libslic3r/PerimeterGenerator.cpp`
- `src/libslic3r/PerimeterGenerator.hpp`

Key findings:

- Perimeter generation is affected by combined layer height/count.
- This is behavior-changing slicing code and should not be copied into AMP until a dedicated integration plan and tests exist.

### G-code / Tool Ordering

Touched:

- `src/libslic3r/GCode.cpp`
- `src/libslic3r/GCode/ToolOrdering.cpp`

Key findings:

- The default branch G-code diff contains a small guard around empty filament instance labels.
- The feature branch changes G-code processing to account for combined layer spans and support nozzle restrictions.
- Tool ordering skips empty layer tools caused by combined layers and keeps wipe tower scheduling aware of the last printing layer.

The audit did not build the fork or inspect generated G-code. Therefore it does not prove a particular `T0`/`T1`/`T2`/`T3` sequence. The code appears to rely on Orca's existing tool ordering and toolchange mechanisms, with changes to make them consistent with mixed nozzle/layer-height behavior.

### Wipe Tower / Purge

Touched:

- `src/libslic3r/GCode/WipeTower2.cpp`
- `src/libslic3r/GCode/WipeTower2.hpp`

Key findings:

- Wipe tower line width and wipe-depth calculations are adjusted to use the active tool's perimeter width.
- The feature branch distinguishes purge line width from tower row spacing width.
- Wipe-into-infill/support logic is guarded so wiping only targets entities compatible with the nozzle/tool involved.

AMP relevance:

- Wipe/purge is not optional for future physical mixed-nozzle behavior.
- This fork is useful evidence that mixed nozzle support reaches beyond simple `Tn` emission.

### Tests

The feature branch adds:

- `tests/fff_print/test_multi_nozzle_layer_height.cpp`

Test coverage includes:

- Per-extruder layer height combines region layers.
- Per-extruder layer height respects minimum layer height.
- Feature filament assignment controls which region can combine layers.
- Fill line width follows the filament that prints the surface.
- Combined infill respects the printing extruder's layer height limits.
- Support nozzle diameter restricts support printing.
- Raft behavior keeps bottom surfaces of combined regions.
- Invalid per-extruder layer heights are rejected.

This is strong evidence of serious implementation work. It is not physical validation.

## Safety Posture

Safety classification for AMP/U1 reuse: safety-unclear.

Reasons:

- The fork is based on upstream OrcaSlicer, not Snapmaker's U1-specific fork.
- It does not touch `CalibUtils.cpp` or Snapmaker-specific nozzle validation paths in the inspected diff.
- It does not appear to implement U1 touchscreen nozzle-state validation.
- It changes core slicing, wipe tower, tool ordering, and G-code-adjacent behavior.

This does not look like an obvious validation bypass in its own target context. It also does not preserve Snapmaker U1 safety paths because those paths are not part of the fork being audited.

AMP should not copy this into the U1 branch without a separate U1 validation design, a Fluidd-only/developer-only execution boundary, and explicit checks against Snapmaker nozzle-state behavior.

## 3MF / Project Representation Findings

No dedicated 3MF schema or sidecar representation change was identified in the changed-file list.

The feature appears to add normal PrintConfig keys, which should likely persist through Orca's existing project/config mechanisms when supported by the normal preset serialization path. That is useful, but it is not the same as AMP's advisory plan packet or 3MF sidecar plan bundle.

Comparison to AMP:

- LixNix provides slicer-config representation for per-extruder layer-height/nozzle behavior.
- AMP provides planner representation: region names, tool classes, confidence, reasons, and execution packet data.
- The two approaches are complementary rather than replacements.

## G-code / Toolchange Findings

The fork changes tool ordering and wipe tower logic, but this audit did not build the fork or generate G-code.

Observed from source:

- Different nozzle diameters are read per mapped filament/extruder.
- Tool ordering accounts for combined-away layers.
- Wipe tower planning uses tool-specific line widths.
- Support nozzle restrictions can force support/raft/interface onto matching-nozzle tools.

Not proven by this audit:

- Exact emitted `T0`/`T1`/`T2`/`T3` sequences.
- Physical toolchange reliability.
- Compatibility with Snapmaker U1 touchscreen start.
- Compatibility with U1 Fluidd-started jobs.

## Build / Probe Result

No build or slicing probe was attempted for this audit.

Reasons:

- The fork has no published release binary.
- Full Orca builds are expensive in the local Windows environment.
- The audit question could be answered from source diffs, tests, and changed-file scope.

Recommended future probe if needed:

- Build the feature branch in a separate worktree.
- Create a two-extruder test profile with 0.4 mm and 0.6 mm nozzles.
- Slice a two-region object assigned to different filaments/features.
- Inspect G-code header, tool commands, layer heights, wipe tower paths, and extrusion widths.

## Comparison To AMP Architecture

AMP currently has:

- offline region metadata and continuous resolution demand work
- tool matrix extraction
- cost-gated tool assignment
- plan packet JSON
- debug artifact schema and serializer
- C++ value types and adapter-side validation
- 3MF sidecar plan bundle
- Fluidd/Klipper-style execution sandbox and hardware preflight gate

LixNix appears to provide:

- a nozzle-diameter lookup correction pattern
- manual/per-feature mixed-nozzle plumbing
- per-extruder layer-height configuration
- combined-layer region implementation
- support-nozzle filtering
- wipe tower and tool ordering adjustments
- a useful fff_print test suite for these behaviors

LixNix does not appear to provide:

- an automated geometry-driven AMP planner
- cost-gated region scoring
- confidence-bearing region plans
- U1-specific logical/physical toolhead mapping
- U1 touchscreen validation compatibility
- an external advisory packet format
- a Fluidd/Klipper execution adapter

## What AMP Can Learn

Useful ideas to study:

- Keep nozzle lookup tied to the actual printing filament/tool, not just a positional vector index.
- Treat layer height as part of resolution allocation, not a separate global profile tweak.
- Restrict support/raft/interface to compatible nozzle classes when needed.
- Combined layers must respect top/bottom surfaces, overhangs, support, and geometric continuity.
- Wipe tower and purge math must use tool-specific line width and cannot be left as a single-width assumption.
- Unit tests for mixed nozzle/layer-height behavior should be added before any AMP behavior-changing integration.

## What AMP Should Not Copy

Do not copy directly:

- core slicing changes into the AMP branch without a staged integration plan
- per-extruder layer-height behavior into Snapmaker U1 output before U1 validation
- wipe tower changes without dedicated purge/wipe test coverage
- assumptions from Bambu/H2D/X2D workflows into U1 touchscreen workflows
- manual assignment logic as a substitute for AMP's planner/debug/sidecar architecture

Do not claim:

- AMP has mixed-nozzle slicing because this fork exists
- LixNix validates U1 mixed-nozzle behavior
- 3MF representation is solved for AMP
- execution is solved for U1

## Recommended Next Action

Recommended actions:

1. Add this fork to AMP prior-art and toolchanger watchlist docs.
2. Contact the author with a short, respectful note asking about project save/load, test cases, and intended hardware targets.
3. Keep AMP's sidecar/packet/adapter architecture in place.
4. Use LixNix as an implementation reference for future C++ behavior-changing stages, especially nozzle lookup, per-extruder layer height, support nozzle restrictions, and wipe tower math.
5. Do not merge or cherry-pick code into AMP until the current offline planner and U1 execution boundaries are stronger.

Bottom line:

The LixNix fork is meaningful prior art. The default branch looks like practical mixed-nozzle plumbing for mapped filaments/extruders. The feature branch goes further and implements real per-extruder layer-height slicing mechanics with tests. It does not replace AMP's planner, sidecar, or U1 validation path.
