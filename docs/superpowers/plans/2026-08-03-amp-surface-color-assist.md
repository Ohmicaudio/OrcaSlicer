# AMP Surface Color Assist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cancellable Color Painting assistant that previews mesh valleys and ridges, then applies an explicitly accepted selection through Orca's existing color-paint path.

**Architecture:** `SurfaceFeatureAnalysis` is a deterministic `libslic3r` component that accepts an immutable mesh and returns per-source-triangle valley/ridge scores plus warnings. A GUI-only `SurfaceColorAssist` owns UI-worker jobs, preview bands, settings, and stale-result rejection. `GLGizmoMmuSegmentation` remains the only code that mutates `mmu_segmentation_facets` and does so only after the user presses Apply.

**Tech Stack:** C++17, Eigen-backed Orca mesh types, Catch2, wxWidgets/ImGui, existing `Worker` UI job queue, OpenGL `GLModel`, `TriangleSelector`, CMake.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `src/libslic3r/SurfaceFeatureAnalysis.hpp` | Pure analysis types, options, color suggestion, and deterministic selection API. |
| `src/libslic3r/SurfaceFeatureAnalysis.cpp` | Edge adjacency, signed valley/ridge scoring, bounded smoothing, patch filtering, and color contrast implementation. |
| `tests/libslic3r/test_surface_feature_analysis.cpp` | Catch2 coverage for flat, trough, ridge, noise, deterministic, cancellation, and color-suggestion behavior. |
| `src/slic3r/GUI/Gizmos/SurfaceColorAssist.hpp` | GUI-only cache key, job/result state, preview bands, and application request state. |
| `src/slic3r/GUI/Gizmos/SurfaceColorAssist.cpp` | UI-worker handoff, stale-result rejection, banded preview geometry, and safe transfer of accepted triangle indices. |
| `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.hpp` | Owns one assist instance and exposes small private callbacks for Analyze, Cancel, Apply, and render. |
| `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.cpp` | Adds controls and delegates render/apply through the existing Color Painting and undo paths. |
| `src/libslic3r/CMakeLists.txt` | Registers the pure analysis component. |
| `src/slic3r/CMakeLists.txt` | Registers the GUI-only assist component. |
| `tests/libslic3r/CMakeLists.txt` | Registers the focused Catch2 file. |
| `docs/benchmarks/AMP_Surface_Color_Assist_Manual_Validation.md` | Reproducible GUI acceptance checklist; no generated models or screenshots are committed. |

The implementation does not add a new 3MF field. Accepted paint continues to serialize through `ModelVolume::mmu_segmentation_facets`.

### Task 0: Configure an isolated test build for this worktree

**Files:**
- No source changes.

- [ ] **Step 1: Configure the worktree against the existing B-drive dependency prefix**

Run:

```powershell
cmake -S B:\ohmic\worktrees\amp-surface-color-assist-design -B B:\ohmic\builds\amp-surface-color-assist -G "Visual Studio 16 2019" -A x64 -DBUILD_TESTING=ON -DBUILD_TESTS=ON -DCMAKE_PREFIX_PATH=B:\ohmic\Snapmaker-OrcaSlicer\deps\build\OrcaSlicer_dep\usr\local
```

Expected: CMake completes without downloading dependencies and writes build files under `B:\ohmic\builds\amp-surface-color-assist`.

- [ ] **Step 2: Establish a focused baseline**

Run:

```powershell
cmake --build B:\ohmic\builds\amp-surface-color-assist --config Release --target libslic3r_tests
B:\ohmic\builds\amp-surface-color-assist\tests\libslic3r\Release\libslic3r_tests.exe "[AdaptiveManufacturing]"
```

Expected: the existing AMP test subset passes before new source is added. Stop to resolve an unexpected baseline failure before implementing any task below.

### Task 1: Register the pure analysis seam and prove the empty/flat contract

**Files:**
- Create: `src/libslic3r/SurfaceFeatureAnalysis.hpp`
- Create: `src/libslic3r/SurfaceFeatureAnalysis.cpp`
- Create: `tests/libslic3r/test_surface_feature_analysis.cpp`
- Modify: `src/libslic3r/CMakeLists.txt`
- Modify: `tests/libslic3r/CMakeLists.txt`

- [ ] **Step 1: Add the source and test registrations**

Add these entries beside the existing `AdaptiveManufacturing*.cpp/.hpp` sources and tests:

```cmake
SurfaceFeatureAnalysis.cpp
SurfaceFeatureAnalysis.hpp
```

```cmake
test_surface_feature_analysis.cpp
```

- [ ] **Step 2: Write the failing flat-mesh and deterministic-result tests**

```cpp
#include <catch2/catch.hpp>

#include "libslic3r/SurfaceFeatureAnalysis.hpp"

using namespace Slic3r;

TEST_CASE("Surface feature analysis leaves a flat mesh unscored", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set flat = make_two_triangle_plane();
    const SurfaceFeatureField field = analyze_surface_features(flat, {});

    REQUIRE(field.status == SurfaceFeatureAnalysisStatus::Complete);
    REQUIRE(field.valley_scores.size() == flat.indices.size());
    REQUIRE(field.ridge_scores.size() == flat.indices.size());
    CHECK(std::all_of(field.valley_scores.begin(), field.valley_scores.end(), [](float score) { return score == 0.0f; }));
    CHECK(std::all_of(field.ridge_scores.begin(), field.ridge_scores.end(), [](float score) { return score == 0.0f; }));
    CHECK(select_surface_feature_triangles(field, SurfaceFeatureMode::Valleys, 0.1f, 0.0f).empty());
}

TEST_CASE("Surface feature analysis is repeatable", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set mesh = make_two_triangle_plane();
    CHECK(analyze_surface_features(mesh, {}) == analyze_surface_features(mesh, {}));
}
```

Define `make_two_triangle_plane()` in the test file with four coplanar vertices and two consistently wound `stl_triangle_vertex_indices` triangles.

- [ ] **Step 3: Run the focused test and confirm it fails because the API is absent**

Run:

```powershell
cmake --build B:\ohmic\builds\amp-surface-color-assist --config Release --target libslic3r_tests
B:\ohmic\builds\amp-surface-color-assist\tests\libslic3r\Release\libslic3r_tests.exe "[SurfaceFeatureAnalysis]"
```

Expected: compilation fails until `SurfaceFeatureAnalysis.hpp` and its implementation exist.

- [ ] **Step 4: Add the minimum public analysis types and flat implementation**

```cpp
enum class SurfaceFeatureMode { Valleys, Ridges };
enum class SurfaceFeatureAnalysisStatus { Complete, Canceled, InvalidMesh };

struct SurfaceFeatureAnalysisOptions {
    float analysis_radius_mm { 1.0f };
    float min_patch_area_mm2 { 0.25f };
    unsigned smoothing_pass_limit { 6 };
};

struct SurfaceFeatureWarning {
    enum class Code { BoundaryEdge, NonManifoldEdge, DegenerateTriangle };
    Code code;
    size_t triangle_index;
    bool operator==(const SurfaceFeatureWarning&) const = default;
};

struct SurfaceFeatureField {
    SurfaceFeatureAnalysisStatus status { SurfaceFeatureAnalysisStatus::Complete };
    std::vector<float> valley_scores;
    std::vector<float> ridge_scores;
    std::vector<float> triangle_areas_mm2;
    std::vector<std::vector<size_t>> triangle_neighbors;
    std::vector<SurfaceFeatureWarning> warnings;
    bool operator==(const SurfaceFeatureField&) const = default;
};

SurfaceFeatureField analyze_surface_features(
    const indexed_triangle_set& mesh,
    const SurfaceFeatureAnalysisOptions& options,
    const std::function<bool()>& is_canceled = {});

std::vector<size_t> select_surface_feature_triangles(
    const SurfaceFeatureField& field,
    SurfaceFeatureMode mode,
    float threshold,
    float min_patch_area_mm2);
```

The first implementation validates triangle indices and degenerate normals, initializes one zero score per original triangle, returns warnings in triangle-index order, and returns `Canceled` before publishing any partially calculated score field.

- [ ] **Step 5: Run the focused test and confirm it passes**

Run the command from Step 3.

Expected: `2 test cases` pass with no output outside Catch2's normal summary.

- [ ] **Step 6: Commit the seam**

```powershell
git add src/libslic3r/SurfaceFeatureAnalysis.* src/libslic3r/CMakeLists.txt tests/libslic3r/test_surface_feature_analysis.cpp tests/libslic3r/CMakeLists.txt
git commit -m "planner: add surface feature analysis seam"
```

### Task 2: Implement signed valley and ridge scoring

**Files:**
- Modify: `src/libslic3r/SurfaceFeatureAnalysis.cpp`
- Modify: `tests/libslic3r/test_surface_feature_analysis.cpp`

- [ ] **Step 1: Write failing trough and ridge tests**

Create two consistently wound four-face fixtures: `make_v_trough()` with the shared center edge recessed and `make_v_ridge()` with the same edge raised. Add:

```cpp
TEST_CASE("Surface feature analysis distinguishes a trough from a ridge", "[SurfaceFeatureAnalysis]")
{
    const SurfaceFeatureField trough = analyze_surface_features(make_v_trough(), {});
    const SurfaceFeatureField ridge = analyze_surface_features(make_v_ridge(), {});

    CHECK(max_score(trough.valley_scores) > 0.0f);
    CHECK(max_score(trough.valley_scores) > max_score(trough.ridge_scores));
    CHECK(max_score(ridge.ridge_scores) > 0.0f);
    CHECK(max_score(ridge.ridge_scores) > max_score(ridge.valley_scores));
}

TEST_CASE("Surface feature analysis warns on non-manifold shared edges", "[SurfaceFeatureAnalysis]")
{
    const SurfaceFeatureField field = analyze_surface_features(make_three_faces_on_one_edge(), {});
    CHECK(field.status == SurfaceFeatureAnalysisStatus::Complete);
    CHECK(std::any_of(field.warnings.begin(), field.warnings.end(), [](const auto& warning) {
        return warning.code == SurfaceFeatureWarning::Code::NonManifoldEdge;
    }));
}
```

- [ ] **Step 2: Run the focused test and confirm the score assertions fail**

Run:

```powershell
B:\ohmic\builds\amp-surface-color-assist\tests\libslic3r\Release\libslic3r_tests.exe "[SurfaceFeatureAnalysis]"
```

Expected: the new trough/ridge score checks fail while the flat tests still pass.

- [ ] **Step 3: Implement deterministic edge adjacency and raw scores**

Use an ordered vertex-pair key so each undirected mesh edge has deterministic identity:

```cpp
struct EdgeKey {
    int first;
    int second;
    bool operator<(const EdgeKey& other) const
    {
        return std::tie(first, second) < std::tie(other.first, other.second);
    }
};

struct EdgeUse { size_t triangle; Vec3f directed_edge; };
```

For every valid source triangle, calculate its normalized face normal and add its three directed edges to `std::map<EdgeKey, std::vector<EdgeUse>>`. For an edge used by exactly two faces, calculate the signed bend from the two normals and the normalized directed edge. Clamp the magnitude into `[0, 1]`, add positive concavity to the two valley entries and positive convexity to the two ridge entries. For one use, emit `BoundaryEdge`; for more than two, emit `NonManifoldEdge` and do not score that edge. Sort warnings by `(triangle_index, code)` before return.

- [ ] **Step 4: Re-run the focused test**

Run the command from Step 2.

Expected: flat, trough, ridge, non-manifold, and repeatability tests pass.

- [ ] **Step 5: Commit raw scoring**

```powershell
git add src/libslic3r/SurfaceFeatureAnalysis.cpp tests/libslic3r/test_surface_feature_analysis.cpp
git commit -m "planner: score AMP surface valleys and ridges"
```

### Task 3: Add bounded smoothing, patch filtering, and cancellation

**Files:**
- Modify: `src/libslic3r/SurfaceFeatureAnalysis.cpp`
- Modify: `tests/libslic3r/test_surface_feature_analysis.cpp`

- [ ] **Step 1: Write failing noise, patch, and cancellation tests**

```cpp
TEST_CASE("Surface feature selection removes undersized isolated patches", "[SurfaceFeatureAnalysis]")
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Complete;
    field.valley_scores = { 0.9f, 0.9f, 0.05f };
    field.triangle_areas_mm2 = { 0.02f, 0.02f, 1.0f };
    field.triangle_neighbors = { {1}, {0}, {} };

    CHECK(select_surface_feature_triangles(field, SurfaceFeatureMode::Valleys, 0.5f, 0.1f).empty());
}

TEST_CASE("Surface feature analysis returns canceled without partial scores", "[SurfaceFeatureAnalysis]")
{
    const SurfaceFeatureField field = analyze_surface_features(make_dense_grid(), {}, [] { return true; });
    CHECK(field.status == SurfaceFeatureAnalysisStatus::Canceled);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
}
```

`SurfaceFeatureField` retains `triangle_areas_mm2` and sorted `triangle_neighbors` in memory so threshold selection can be deterministic without recomputing adjacency. It is not a persisted debug or 3MF contract.

- [ ] **Step 2: Run the focused test and confirm failures**

Run the command from Task 2, Step 2.

Expected: patch filtering and cancellation assertions fail.

- [ ] **Step 3: Implement bounded smoothing and thresholded connected components**

Use the edge map created in Task 2 to construct sorted unique triangle-neighbor lists. Convert `analysis_radius_mm` to a bounded pass count with:

```cpp
const float mean_edge_mm = total_valid_edge_length / float(valid_edge_count);
const unsigned passes = std::clamp(
    unsigned(std::ceil(options.analysis_radius_mm / std::max(mean_edge_mm, 0.001f))),
    0u,
    options.smoothing_pass_limit);
```

For each pass, replace each score with its own score plus direct-neighbor scores divided by one plus neighbor count. Run the same operation independently for valleys and ridges. Check `is_canceled()` once per 4096 source triangles and once before publishing the completed field.

`select_surface_feature_triangles()` must threshold the selected score vector, find connected components using the sorted neighbor lists, sum source-triangle areas for each component, retain only components whose total area is at least `min_patch_area_mm2`, then return ascending source-triangle indices.

- [ ] **Step 4: Run the focused test and add a determinism assertion for returned indices**

Add:

```cpp
CHECK(select_surface_feature_triangles(field, SurfaceFeatureMode::Valleys, 0.5f, 0.0f) == std::vector<size_t>{0, 1});
```

Run the command from Task 2, Step 2.

Expected: all focused analysis tests pass.

- [ ] **Step 5: Commit filtering and cancellation**

```powershell
git add src/libslic3r/SurfaceFeatureAnalysis.* tests/libslic3r/test_surface_feature_analysis.cpp
git commit -m "planner: filter AMP surface feature patches"
```

### Task 4: Add deterministic target-filament suggestion

**Files:**
- Modify: `src/libslic3r/SurfaceFeatureAnalysis.hpp`
- Modify: `src/libslic3r/SurfaceFeatureAnalysis.cpp`
- Modify: `tests/libslic3r/test_surface_feature_analysis.cpp`

- [ ] **Step 1: Write failing color-suggestion tests**

```cpp
TEST_CASE("Surface feature color suggestion prefers dark valleys and bright ridges", "[SurfaceFeatureAnalysis]")
{
    const std::vector<SurfaceFeatureColor> palette {
        { 220, 220, 220, 255 }, { 20, 20, 20, 255 }, { 250, 240, 80, 255 }
    };

    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 0, palette) == 1);
    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Ridges, 0, palette) == 2);
    CHECK_FALSE(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 0, { palette.front() }));
}
```

- [ ] **Step 2: Run the focused test and confirm the suggestion symbols are absent**

Run the command from Task 2, Step 2.

Expected: compilation fails until `SurfaceFeatureColor` and `suggest_surface_feature_filament()` exist.

- [ ] **Step 3: Implement the non-binding suggestion helper**

```cpp
struct SurfaceFeatureColor { uint8_t red, green, blue, alpha; };

std::optional<size_t> suggest_surface_feature_filament(
    SurfaceFeatureMode mode,
    size_t base_filament,
    const std::vector<SurfaceFeatureColor>& palette);
```

Use sRGB relative luminance:

```cpp
const float luminance = 0.2126f * linear(red) + 0.7152f * linear(green) + 0.0722f * linear(blue);
```

Skip `base_filament` and candidates whose luminance contrast is below `0.20`. Valley mode chooses the lowest-luminance eligible candidate; ridge mode chooses the highest-luminance eligible candidate. Break equal scores by lower palette index. Return `std::nullopt` for an invalid base index or no candidate. The caller remains free to ignore or override this result.

- [ ] **Step 4: Run the focused test**

Run the command from Task 2, Step 2.

Expected: color-suggestion tests pass with the earlier analysis tests.

- [ ] **Step 5: Commit color suggestion**

```powershell
git add src/libslic3r/SurfaceFeatureAnalysis.* tests/libslic3r/test_surface_feature_analysis.cpp
git commit -m "planner: suggest AMP surface paint colors"
```

### Task 5: Add GUI-only assist state and cancellable worker handoff

**Files:**
- Create: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.hpp`
- Create: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.cpp`
- Modify: `src/slic3r/CMakeLists.txt`

- [ ] **Step 1: Add the GUI source registrations**

Add beside `GUI/Gizmos/GLGizmoMmuSegmentation.*`:

```cmake
GUI/Gizmos/SurfaceColorAssist.cpp
GUI/Gizmos/SurfaceColorAssist.hpp
```

- [ ] **Step 2: Define the cache key and state types**

```cpp
struct SurfaceColorAssistKey {
    std::shared_ptr<const TriangleMesh> mesh;
    Transform3d volume_transform;
    size_t triangle_count { 0 };
};

struct SurfaceColorAssistSettings {
    SurfaceFeatureMode mode { SurfaceFeatureMode::Valleys };
    float threshold { 0.50f };
    float preview_falloff { 0.15f };
    float analysis_radius_mm { 1.0f };
    float min_patch_area_mm2 { 0.25f };
    std::optional<size_t> target_filament;
};
```

`SurfaceColorAssist` owns `std::optional<SurfaceFeatureField>`, the active key, settings, a job generation number, and a fixed eight-band preview cache. It does not own `ModelVolume`, `TriangleSelector`, or paint data.

- [ ] **Step 3: Start jobs with the existing UI worker and reject stale results**

Use `ModelVolume::get_mesh_shared_ptr()` so the queued job keeps an immutable mesh alive without duplicating it. Queue through the existing API:

```cpp
auto result = std::make_shared<SurfaceFeatureField>();
auto& worker = wxGetApp().plater()->get_ui_job_worker();
replace_job(worker,
    [mesh, options, result](Job::Ctl& ctl) {
        *result = analyze_surface_features(mesh->its, options, [&ctl] { return ctl.was_canceled(); });
    },
    [this, key, generation, result](bool canceled, std::exception_ptr& error) {
        if (canceled || error || generation != m_generation || !matches_current_volume(key))
            return;
        adopt_completed_field(std::move(*result));
    });
```

Implement `matches_current_volume()` by comparing the current `ModelVolume` mesh shared pointer, source-triangle count, and volume transformation against the key. Cancel and clear preview on selected-volume change, gizmo shutdown, or a new Analyze request.

- [ ] **Step 4: Build the GUI target**

Run:

```powershell
cmake --build B:\ohmic\builds\amp-surface-color-assist --config Release --target Slic3r
```

Expected: `Slic3r` compiles with the new GUI-only component linked and no existing behavior is called yet.

- [ ] **Step 5: Commit the worker/cache component**

```powershell
git add src/slic3r/GUI/Gizmos/SurfaceColorAssist.* src/slic3r/CMakeLists.txt
git commit -m "ui: add AMP surface color assist cache"
```

### Task 6: Render the soft preview in score bands

**Files:**
- Modify: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.hpp`
- Modify: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.cpp`
- Modify: `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.hpp`
- Modify: `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.cpp`

- [ ] **Step 1: Implement eight deterministic preview bands**

Do not add a new shader or a new vertex-color format. Build up to eight `GLModel` triangle batches because existing `GLModel` supports one color per model. For a score `s`, preview threshold `t`, and falloff `f`, calculate:

```cpp
const float normalized = std::clamp((s - (t - f)) / std::max(2.0f * f, 0.001f), 0.0f, 1.0f);
const size_t band = std::min<size_t>(7, size_t(normalized * 8.0f));
```

Duplicate only source-triangle vertices that belong to a nonzero band, offset no vertices, and use alpha/color from a fixed valley teal-to-amber ramp or ridge cool-gray-to-light ramp. Rebuild bands only when the adopted field, mode, threshold, falloff, or mesh key changes.

- [ ] **Step 2: Render after standard painted triangles and before the paint cursor**

In `GLGizmoMmuSegmentation::render_painter_gizmo()`, retain existing triangle rendering and insert:

```cpp
m_surface_color_assist.render_preview(m_parent.get_selection(), current_volume_transform);
```

before `render_cursor()`. Preview rendering must be skipped when there is no current field or its key is stale.

- [ ] **Step 3: Add Analyze and Cancel controls without Apply**

In `on_render_input_window()`, add a collapsed `Surface Color Assist` section with mode, analysis radius, threshold, preview falloff, minimum patch area, Analyze, Cancel, and warnings. Do not add Apply in this task. Changing a control updates only preview state; it does not call `update_model_object()`.

- [ ] **Step 4: Build and manually verify the no-mutation preview**

Run:

```powershell
cmake --build B:\ohmic\builds\amp-surface-color-assist --config Release --target Slic3r
```

Open a small engraved-text model, enter Color Painting, run Analyze, adjust Threshold, close the gizmo, and verify the project remains unmodified and undo has no new entry.

- [ ] **Step 5: Commit preview-only integration**

```powershell
git add src/slic3r/GUI/Gizmos/SurfaceColorAssist.* src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.*
git commit -m "ui: preview AMP surface color features"
```

### Task 7: Add target-filament suggestion and explicit Apply

**Files:**
- Modify: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.hpp`
- Modify: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.cpp`
- Modify: `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.cpp`

- [ ] **Step 1: Render the non-binding target suggestion**

Convert `m_extruders_colors` into `SurfaceFeatureColor` values, call `suggest_surface_feature_filament()`, and show the result as the initial target only when the user has not manually overridden it. The target selector must list the existing physical paint filaments. If fewer than two are available, show `Load at least two filaments to apply` and keep Apply disabled.

- [ ] **Step 2: Implement explicit apply through `TriangleSelector::set_facet()`**

When the user presses Apply, reject stale keys and empty selections. Otherwise take a normal gizmo snapshot and mutate only the current volume's matching selector:

```cpp
Plater::TakeSnapshot snapshot(wxGetApp().plater(), "Apply surface color assist", UndoRedo::SnapshotType::GizmoAction);
const EnforcerBlockerType state = EnforcerBlockerType(int(selected_filament) + int(EnforcerBlockerType::Extruder1));
for (const size_t facet : selected_surface_feature_triangles)
    selector->set_facet(int(facet), state);
selector->request_update_render_data(true);
update_model_object();
m_parent.set_as_dirty();
```

Clear only the in-memory preview after successful apply. Do not add a custom clear command. Existing Undo is the only safe reversal action.

- [ ] **Step 3: Build and manually verify Apply/Undo/3MF persistence**

Run:

```powershell
cmake --build B:\ohmic\builds\amp-surface-color-assist --config Release --target Slic3r
```

Manual checks:

1. Load an engraved-text model with at least two loaded filament colors.
2. Analyze valleys and confirm no paint appears in saved project state before Apply.
3. Apply one target color and confirm only selected source triangles become standard paint.
4. Undo once and confirm the original paint is restored.
5. Apply again, save 3MF, reopen it, and confirm normal Color Painting shows the accepted result.

- [ ] **Step 4: Commit Apply integration**

```powershell
git add src/slic3r/GUI/Gizmos/SurfaceColorAssist.* src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.cpp
git commit -m "ui: apply AMP surface color painting"
```

### Task 8: Record manual validation and perform final focused verification

**Files:**
- Create: `docs/benchmarks/AMP_Surface_Color_Assist_Manual_Validation.md`

- [ ] **Step 1: Add the manual validation checklist**

Document these fixtures and outcomes:

```text
Engraved text: valley preview follows letter recesses without selecting the flat face.
Raised text: ridge preview follows letter tops and border trim.
Panel groove: valley preview remains one coherent feature after minimum-area filtering.
Rough/low-poly mesh: surface breaks are not enabled; valleys/ridges do not blanket-paint facets.
Dense representative mesh: Analyze shows progress, Cancel works, and stale result is never applied.
```

Include these required statements:

```text
The preview is read-only until Apply.
Applied output is ordinary discrete Orca color paint.
This feature does not change G-code generation logic.
This feature does not validate FullSpectrum blending, physical nozzle assignment, or color accuracy.
```

- [ ] **Step 2: Run focused library tests**

Run:

```powershell
cmake --build B:\ohmic\builds\amp-surface-color-assist --config Release --target libslic3r_tests
B:\ohmic\builds\amp-surface-color-assist\tests\libslic3r\Release\libslic3r_tests.exe "[SurfaceFeatureAnalysis]"
B:\ohmic\builds\amp-surface-color-assist\tests\libslic3r\Release\libslic3r_tests.exe "[AdaptiveManufacturing]"
```

Expected: all new surface-analysis tests and the existing AMP test subset pass.

- [ ] **Step 3: Run source-boundary audits**

Run:

```powershell
rg -n "SurfaceColorAssist|SurfaceFeatureAnalysis" src tests CMakeLists.txt cmake -g "*"
rg -n "SurfaceColorAssist|SurfaceFeatureAnalysis" src/libslic3r/Flow.* src/libslic3r/LayerRegion.* src/libslic3r/PerimeterGenerator.* src/libslic3r/Arachne* src/libslic3r/GCode* -g "*"
git diff --check HEAD~6..HEAD
```

Expected: references are limited to the new pure analysis, GUI assist, Color Painting host, CMake registrations, and tests. The forbidden hot paths return no new references.

- [ ] **Step 4: Commit validation documentation**

```powershell
git add docs/benchmarks/AMP_Surface_Color_Assist_Manual_Validation.md
git commit -m "docs: add AMP surface color assist validation"
```

## Final Acceptance Checklist

- [ ] Preview-only use creates no project mutation or undo entry.
- [ ] Valley and ridge results are deterministic for the same mesh/options.
- [ ] Non-manifold and degenerate geometry warns instead of silently receiving a feature score.
- [ ] Large-model analysis can be canceled and stale results are rejected.
- [ ] Apply creates exactly one normal Color Painting undo step.
- [ ] The user can override the suggested target filament.
- [ ] Accepted paint survives normal 3MF save/reload.
- [ ] No Flow, LayerRegion, PerimeterGenerator, Arachne, nozzle validation, profile, or G-code-generation logic is changed.
