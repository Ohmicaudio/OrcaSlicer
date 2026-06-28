# AMP Read-Only Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the first Adaptive Manufacturing Planner module that observes geometry and emits debug output without changing generated toolpaths, generated G-code, profile defaults, nozzle validation, or printer safety behavior.

**Architecture:** Add a hidden experimental flag, planner-owned data structures, a no-op/read-only planner, and debug artifact serialization. The first working path produces stock fallback recommendations and optional geometry scores while the normal Snapmaker Orca slicing pipeline continues unchanged.

**Tech Stack:** C++ in `src/libslic3r`, Snapmaker Orca config system, existing libslic3r test framework, JSON serialization using project-available facilities selected during implementation.

---

## Purpose

Create the first planner module that observes layer/region geometry and emits a debug artifact without changing slicing behavior.

The read-only prototype is a visibility and validation tool, not a manufacturing behavior change.

## Hard constraints

- No G-code changes.
- No toolpath changes.
- No profile default changes.
- No nozzle safety bypass.
- No physical mixed-nozzle assumptions.
- Do not alter `Flow`, `PerimeterGenerator`, Arachne, tool assignment, or G-code output.
- Do not bypass nozzle mismatch checks or Snapmaker validation paths.
- Do not claim mixed-nozzle behavior works without U1 hardware.

## Prototype behavior

When disabled:

- The planner is not invoked.
- No debug artifact is emitted.
- Generated outputs remain equivalent to stock Snapmaker Orca behavior.

When enabled in read-only mode:

- The planner inspects object/layer/region geometry available before toolpath generation.
- The planner creates a stock fallback plan.
- The planner may assign provisional region scores for debug visibility.
- The planner emits a debug JSON artifact.
- The planner may prepare future preview-overlay data.
- Generated toolpaths and G-code remain unchanged.

## Proposed files

- `src/libslic3r/AdaptiveManufacturingPlan.hpp`
- `src/libslic3r/AdaptiveManufacturingPlan.cpp`
- `src/libslic3r/AdaptiveManufacturingPlanner.hpp`
- `src/libslic3r/AdaptiveManufacturingPlanner.cpp`
- `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`

Possible later files:

- `src/libslic3r/AdaptiveManufacturingDebug.hpp`
- `src/libslic3r/AdaptiveManufacturingDebug.cpp`
- `src/slic3r/GUI/AdaptiveManufacturingPreview.*`

The later files are not required for the first read-only prototype.

## First implementation phases

1. Add config flag only.
2. Add no-op planner data structures.
3. Add stock fallback plan output.
4. Add debug artifact export.
5. Add tests proving disabled behavior is unchanged.
6. Add geometry scoring only after the no-op path is stable.

## File responsibilities

### `src/libslic3r/AdaptiveManufacturingPlan.hpp`

Defines plain value types owned by the planner:

- `AMPScoreSet`
- `AMPRegion`
- `AMPRecommendation`
- `AMPDebugRecord`
- `AdaptiveManufacturingPlan`

This file should not include `Flow`, `PerimeterGenerator`, Arachne, G-code writer, or UI headers.

### `src/libslic3r/AdaptiveManufacturingPlan.cpp`

Implements helper functions for default values, reason-code strings, stock fallback construction, and debug serialization helpers that do not require slicer mutation.

### `src/libslic3r/AdaptiveManufacturingPlanner.hpp`

Declares the read-only planner API. The API should accept context and return an `AdaptiveManufacturingPlan` by value or through planner-owned storage.

Initial API shape:

```cpp
namespace Slic3r {

struct AdaptiveManufacturingPlannerInput;

class AdaptiveManufacturingPlanner
{
public:
    AdaptiveManufacturingPlan analyze_read_only(const AdaptiveManufacturingPlannerInput &input) const;
};

}
```

### `src/libslic3r/AdaptiveManufacturingPlanner.cpp`

Implements read-only analysis:

- Validate input presence.
- Build stock fallback plan.
- Optionally create deterministic region records.
- Attach reason code `read_only_no_behavior_change`.
- Never write into slicer-owned geometry or generation state.

### `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`

Tests value defaults, stock fallback behavior, serialization shape, and disabled/no-op contracts.

## Task 1: Add hidden config flag only

**Files:**

- Modify: `src/libslic3r/PrintConfig.hpp`
- Modify: `src/libslic3r/PrintConfig.cpp`
- Test: existing config test location selected from the repo's libslic3r tests

- [ ] **Step 1: Locate matching config patterns**

Run:

```powershell
rg -n "coBool|mode|category|full_label|tooltip" src/libslic3r/PrintConfig.cpp tests src | Select-Object -First 120
```

Expected: find existing boolean options and the style used for labels, categories, defaults, and visibility.

- [ ] **Step 2: Add `adaptive_manufacturing_enable` with default false**

Add the option using the existing `PrintConfig` style:

```cpp
def = this->add("adaptive_manufacturing_enable", coBool);
def->label = L("Adaptive manufacturing planner");
def->tooltip = L("Enable experimental read-only Adaptive Manufacturing Planner diagnostics. This must not change generated toolpaths or G-code.");
def->mode = comAdvanced;
def->set_default_value(new ConfigOptionBool(false));
```

Use the repo's exact field names and mode conventions after confirming nearby options.

- [ ] **Step 3: Add config parsing test**

Test that:

- Default value is false.
- JSON/profile value `1` or `true` parses.
- Missing value keeps stock default false.

- [ ] **Step 4: Run focused config tests**

Run the smallest available config test target. If no focused target exists, run the nearest libslic3r test binary that covers config parsing.

Expected: config tests pass and no slicing behavior tests are required for this flag-only commit.

- [ ] **Step 5: Commit**

```powershell
git add src/libslic3r/PrintConfig.hpp src/libslic3r/PrintConfig.cpp tests
git commit -m "feat: add hidden adaptive manufacturing planner flag"
```

## Task 2: Add no-op planner data structures

**Files:**

- Create: `src/libslic3r/AdaptiveManufacturingPlan.hpp`
- Create: `src/libslic3r/AdaptiveManufacturingPlan.cpp`
- Test: `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`

- [ ] **Step 1: Write tests for default scores and stock fallback**

Add tests that assert:

- Default scores are zero except confidence fields chosen by the implementation.
- A stock fallback recommendation reports strategy `stock`.
- Reason code is `read_only_no_behavior_change`.

- [ ] **Step 2: Add value types**

Define small value types with explicit defaults. Keep fields deterministic and serializable.

Suggested enum names:

```cpp
enum class AMPStrategy {
    Stock,
    DetailPreserving,
    InternalThroughput,
    SupportThroughput
};

enum class AMPReasonCode {
    ReadOnlyNoBehaviorChange,
    LowConfidenceFallback,
    SafetyConstraintFallback,
    GeometryUnavailableFallback
};
```

- [ ] **Step 3: Implement stock fallback helper**

Add a helper such as:

```cpp
AdaptiveManufacturingPlan make_stock_fallback_plan(int object_id);
```

The helper should not require layer geometry.

- [ ] **Step 4: Run planner unit tests**

Run the focused planner test binary or the nearest libslic3r unit test target.

Expected: tests pass and no production slicing path references the new files yet.

- [ ] **Step 5: Commit**

```powershell
git add src/libslic3r/AdaptiveManufacturingPlan.hpp src/libslic3r/AdaptiveManufacturingPlan.cpp tests/libslic3r/test_adaptive_manufacturing_planner.cpp
git commit -m "feat: add AMP stock fallback plan types"
```

## Task 3: Add read-only planner API

**Files:**

- Create: `src/libslic3r/AdaptiveManufacturingPlanner.hpp`
- Create: `src/libslic3r/AdaptiveManufacturingPlanner.cpp`
- Modify: `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`

- [ ] **Step 1: Write planner API test**

Test that `analyze_read_only(...)` returns a stock fallback plan when given minimal valid input.

- [ ] **Step 2: Define read-only input**

Add an input type that references existing data without owning or mutating it:

```cpp
struct AdaptiveManufacturingPlannerInput
{
    int object_id = -1;
    const PrintConfig *print_config = nullptr;
    const PrintObjectConfig *object_config = nullptr;
    const PrintRegionConfig *region_config = nullptr;
};
```

Add geometry references only after the correct layer/region integration point is selected.

- [ ] **Step 3: Implement read-only planner**

Implement `analyze_read_only(...)` so it:

- Returns stock fallback when input is incomplete.
- Records fallback reason.
- Does not mutate any input.
- Does not call flow, perimeter, Arachne, tool assignment, or G-code code.

- [ ] **Step 4: Run planner tests**

Expected: planner returns stock fallback deterministically.

- [ ] **Step 5: Commit**

```powershell
git add src/libslic3r/AdaptiveManufacturingPlanner.hpp src/libslic3r/AdaptiveManufacturingPlanner.cpp tests/libslic3r/test_adaptive_manufacturing_planner.cpp
git commit -m "feat: add AMP read-only planner API"
```

## Task 4: Add debug JSON artifact export

**Files:**

- Modify: `src/libslic3r/AdaptiveManufacturingPlan.hpp`
- Modify: `src/libslic3r/AdaptiveManufacturingPlan.cpp`
- Modify: `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`

- [ ] **Step 1: Write serialization test**

Test that a stock fallback plan serializes to JSON containing:

- `plan_version`
- `mode`
- `object_id`
- `strategy`
- `reason_code`
- `confidence`

- [ ] **Step 2: Implement deterministic JSON serialization**

Use project-approved JSON facilities. If no local helper is already used in libslic3r tests, implement a small internal serializer for the first artifact and keep escaping correct for known string values.

- [ ] **Step 3: Run serialization tests**

Expected: JSON is deterministic and contains no filesystem-dependent paths.

- [ ] **Step 4: Commit**

```powershell
git add src/libslic3r/AdaptiveManufacturingPlan.hpp src/libslic3r/AdaptiveManufacturingPlan.cpp tests/libslic3r/test_adaptive_manufacturing_planner.cpp
git commit -m "feat: serialize AMP debug plan"
```

## Task 5: Wire disabled/read-only invocation without consuming output

**Files:**

- Modify: selected `PrintObject` or `LayerRegion` integration file after code inspection
- Modify: build system files required to compile new AMP sources
- Test: add or update focused integration test if the repo has a suitable harness

- [ ] **Step 1: Inspect integration points**

Run:

```powershell
rg -n "make_perimeters|LayerRegion::make_perimeters|PrintObject::make_perimeters|process\\(" src/libslic3r
```

Expected: identify the narrowest place where layer/region geometry can be observed before perimeters are generated.

- [ ] **Step 2: Add guarded read-only call**

Add a call only when `adaptive_manufacturing_enable` is true. Store or discard the returned plan without changing generation inputs.

Guard shape:

```cpp
if (print_config.adaptive_manufacturing_enable.value) {
    AdaptiveManufacturingPlanner planner;
    AdaptiveManufacturingPlannerInput input;
    input.object_id = static_cast<int>(object_id);
    input.print_config = &print_config;
    AdaptiveManufacturingPlan plan = planner.analyze_read_only(input);
    // Debug export wiring is separate; do not consume recommendations here.
}
```

Adapt names to actual local types after inspection.

- [ ] **Step 3: Verify disabled behavior**

Slice a small model or run the nearest deterministic slicing test with the flag absent/false.

Expected: output remains equivalent to baseline.

- [ ] **Step 4: Verify enabled read-only behavior**

Run with the hidden flag enabled.

Expected: planner path executes and output toolpaths/G-code remain unchanged.

- [ ] **Step 5: Commit**

```powershell
git add src/libslic3r build files tests
git commit -m "feat: run AMP in read-only mode behind flag"
```

## Task 6: Add geometry scoring after no-op path is stable

**Files:**

- Modify: `src/libslic3r/AdaptiveManufacturingPlanner.cpp`
- Modify: `src/libslic3r/AdaptiveManufacturingPlan.hpp`
- Modify: `tests/libslic3r/test_adaptive_manufacturing_planner.cpp`

- [ ] **Step 1: Add synthetic region tests**

Create tests for simple geometry descriptors:

- Large area, low perimeter-to-area ratio: higher time-savings potential.
- Small area, high perimeter-to-area ratio: higher detail score.
- Missing geometry: stock fallback with low confidence.

- [ ] **Step 2: Implement deterministic scoring**

Use simple normalized calculations and reason codes. Avoid tool/nozzle assignment.

- [ ] **Step 3: Emit scores in debug JSON**

Include score fields in the debug artifact while keeping strategy `stock` unless a later milestone allows advisory labels.

- [ ] **Step 4: Verify no generation output changes**

Run the same disabled and enabled read-only comparison used in Task 5.

Expected: only debug artifacts differ.

- [ ] **Step 5: Commit**

```powershell
git add src/libslic3r/AdaptiveManufacturingPlanner.cpp src/libslic3r/AdaptiveManufacturingPlan.hpp src/libslic3r/AdaptiveManufacturingPlan.cpp tests/libslic3r/test_adaptive_manufacturing_planner.cpp
git commit -m "feat: add AMP read-only geometry scoring"
```

## Exit criteria

The read-only prototype is complete when:

- Project builds.
- Config flag parses.
- Planner can run in no-op/debug mode.
- Debug output is produced when enabled.
- Generated toolpaths remain unchanged.
- Generated G-code remains unchanged.
- Nozzle mismatch checks and Snapmaker validation paths remain intact.
- Any mixed-nozzle recommendation remains advisory and unclaimed until U1 hardware validation exists.

## Milestone boundary

After this plan, the next acceptable code change is a hidden experimental config flag and no-op planner scaffold. Algorithmic behavior changes remain out of scope until the read-only planner is observable, tested, and proven not to affect stock output.
