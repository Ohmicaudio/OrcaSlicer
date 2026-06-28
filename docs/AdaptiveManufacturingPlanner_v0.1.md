# Adaptive Manufacturing Planner v0.1

## Summary

Adaptive Manufacturing Planner is the project name for the U1 adaptive slicing work. The planner should become a separate decision layer that evaluates model regions, available tools, material constraints, and user priorities before the slicer emits toolpaths.

The first implementation step is not an algorithm change. It is a hidden experimental configuration flag and a no-op planner scaffold. With the flag disabled, output must remain byte-for-byte equivalent or explainably identical to the current slicer path.

## Stages

### Stage 1: Adaptive Bead Widths

Software-only. The planner chooses effective bead widths for existing roles.

- Keep cosmetic/external detail conservative.
- Widen internal perimeters and infill only when confidence is high.
- Use Arachne as the first generator target because it already accepts distinct outer and inner bead widths.

### Stage 2: Adaptive Nozzle Selection

U1 hardware-backed. The planner assigns regions or roles to available U1 tools with different physical nozzle diameters.

- Small nozzle: exterior detail, text, small features.
- Larger nozzle: inner shells, sparse infill, internal solid infill, support.
- Requires real U1 validation and must preserve nozzle mismatch safety checks.

### Stage 3: Manufacturing Optimization

Global planning. The planner balances region geometry, structural need, cosmetic visibility, tool access, tool-change cost, and predicted time savings.

## Inputs

- Mesh-derived layer and region geometry.
- `PrintConfig`, `PrintObjectConfig`, and `PrintRegionConfig`.
- Available nozzle diameters from `nozzle_diameter`.
- Material and filament constraints.
- User priority preset.
- Optional later inputs: modifier volumes, painted attributes, cosmetic visibility hints, and calibration confidence.

## Outputs

- Region map.
- Tool assignment plan.
- Bead-width plan.
- Optional layer-height plan.
- Confidence score and reason code.

## Real Code Anchors

### PrintConfig Options

Config option declarations live in:

- `src/libslic3r/PrintConfig.hpp`

Observed relevant declarations:

- `wall_generator`
- `outer_wall_line_width`
- `inner_wall_line_width`
- `nozzle_diameter`

Config option definitions live in:

- `src/libslic3r/PrintConfig.cpp`

Observed relevant definition areas:

- `outer_wall_line_width` is added with `this->add("outer_wall_line_width", coFloatOrPercent)` and uses `ratio_over = "nozzle_diameter"`.
- `line_width` is added with `this->add("line_width", coFloatOrPercent)` and uses `ratio_over = "nozzle_diameter"`.
- `wall_generator` is added as an enum with values `classic` and `arachne`.

### Process Profile Keys Into Config

JSON process profiles are loaded through:

- `src/libslic3r/Config.cpp`
- `src/libslic3r/Preset.cpp`

Important paths:

- `ConfigBase::load_from_json(...)` parses JSON key/value pairs.
- `ConfigBase::set_deserialize(...)` maps string profile values into typed `ConfigOption` instances.
- `Preset::load(...)` calls `config.load_from_json(...)`.
- `PresetCollection` resolves `inherits` chains and copies inherited options.

This means new settings must be defined in `PrintConfig` before process profile JSON can use them safely.

### Arachne Bead Width Inputs

Arachne receives outer and inner bead widths through:

- `src/libslic3r/PerimeterGenerator.cpp`
- `src/libslic3r/Arachne/WallToolPaths.cpp`
- `src/libslic3r/Arachne/WallToolPaths.hpp`

Important path:

- `PerimeterGenerator::process_arachne()` computes:
  - `bead_width_0 = ext_perimeter_spacing`
  - `perimeter_spacing = this->perimeter_flow.scaled_spacing()`
- It then constructs:
  - `Arachne::WallToolPaths(last_p, bead_width_0, perimeter_spacing, ...)`
- `WallToolPaths` stores these as:
  - `bead_width_0`
  - `bead_width_x`

This is the Stage 1 insertion point. A hidden planner can eventually alter the planned external/internal bead widths before `WallToolPaths` is constructed.

### Nozzle Diameter Reads During Wall Generation

Nozzle diameter is read in several relevant places:

- `LayerRegion::flow(...)` reads `print_config.nozzle_diameter.get_at(this->extruder(role) - 1)` before calling `Flow::new_from_config_width(...)`.
- `Flow::new_from_config_width(...)` converts configured width and nozzle diameter into a `Flow`.
- `PerimeterGenerator::process_arachne()` reads `print_config->nozzle_diameter.get_at(config->wall_filament - 1)` for overhang support geometry.
- `Arachne::make_paths_params(...)` uses the minimum configured nozzle diameter to scale Arachne thresholds such as min feature size, min bead width, transition deviation, and transition length.

## Proposed Hidden Config Flag

First real code step:

- Add `adaptive_manufacturing_enable`.
- Type: `coBool`.
- Default: `false`.
- Mode: advanced/developer/hidden if the existing UI supports hiding.
- Behavior: no-op until later planner code is wired.

No behavior should change when this flag is absent or false.

## Proposed First Scaffold Files

Future code-only scaffold, not part of this docs commit:

- `src/libslic3r/AdaptiveManufacturingPlan.hpp`
- `src/libslic3r/AdaptiveManufacturingPlan.cpp`
- `src/libslic3r/AdaptiveManufacturingPlanner.hpp`
- `src/libslic3r/AdaptiveManufacturingPlanner.cpp`
- `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`

## Initial No-Op Contract

When `adaptive_manufacturing_enable` is false:

- Do not create region plan data.
- Do not alter `Flow`.
- Do not alter `PerimeterGenerator`.
- Do not alter `Arachne::WallToolPaths`.
- Do not alter profile loading.
- Do not alter nozzle validation.

When true but planner is still no-op:

- Planner may emit a stock fallback plan for debugging.
- Generated toolpaths must remain equivalent to stock behavior.

## Test Strategy

First code PR should include config tests only:

- The new flag exists.
- The default is false.
- The flag can be loaded from profile JSON.
- Unknown values are rejected by existing config parsing.

Later planner tests should verify:

- disabled planner returns no behavior changes
- stock fallback plan is stable
- planned outer width maps to `bead_width_0`
- planned inner width maps to `bead_width_x`
- nozzle mismatch safety checks remain intact

## Implementation Rule

Do not start algorithmic planning until the hidden flag, no-op planner boundary, and tests are in place.

