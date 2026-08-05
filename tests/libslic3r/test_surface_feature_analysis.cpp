#include <algorithm>
#include <catch2/catch.hpp>
#include <limits>

#include "libslic3r/SurfaceFeatureAnalysis.hpp"
#include "libslic3r/TriangleMesh.hpp"

using namespace Slic3r;

namespace {

indexed_triangle_set make_two_triangle_plane()
{
    indexed_triangle_set mesh;
    mesh.vertices = {
        Vec3f(0.f, 0.f, 0.f),
        Vec3f(1.f, 0.f, 0.f),
        Vec3f(1.f, 1.f, 0.f),
        Vec3f(0.f, 1.f, 0.f),
    };
    mesh.indices = {
        stl_triangle_vertex_indices(0, 1, 2),
        stl_triangle_vertex_indices(0, 2, 3),
    };
    return mesh;
}

indexed_triangle_set make_disconnected_triangles(size_t triangle_count)
{
    indexed_triangle_set mesh;
    mesh.vertices.reserve(triangle_count * 3);
    mesh.indices.reserve(triangle_count);
    for (size_t triangle_index = 0; triangle_index < triangle_count; ++triangle_index) {
        const int first_vertex = int(triangle_index * 3);
        mesh.vertices.emplace_back(float(first_vertex), 0.f, 0.f);
        mesh.vertices.emplace_back(float(first_vertex), 1.f, 0.f);
        mesh.vertices.emplace_back(float(first_vertex), 0.f, 1.f);
        mesh.indices.emplace_back(first_vertex, first_vertex + 1, first_vertex + 2);
    }
    return mesh;
}

indexed_triangle_set make_v_crease(bool raised)
{
    const float outer_z = raised ? -1.0f : 1.0f;
    indexed_triangle_set mesh;
    mesh.vertices = {
        Vec3f(0.f, 0.f, 0.f),
        Vec3f(1.f, 0.f, 0.f),
        Vec3f(0.f, 1.f, outer_z),
        Vec3f(1.f, 1.f, outer_z),
        Vec3f(0.f, -1.f, outer_z),
        Vec3f(1.f, -1.f, outer_z),
    };
    mesh.indices = {
        stl_triangle_vertex_indices(0, 1, 3),
        stl_triangle_vertex_indices(0, 3, 2),
        stl_triangle_vertex_indices(1, 0, 4),
        stl_triangle_vertex_indices(1, 4, 5),
    };
    return mesh;
}

indexed_triangle_set make_v_trough()
{
    return make_v_crease(false);
}

indexed_triangle_set make_duplicate_vertex_trough()
{
    const indexed_triangle_set shared = make_v_trough();
    indexed_triangle_set duplicated;
    duplicated.vertices.reserve(shared.indices.size() * 3);
    duplicated.indices.reserve(shared.indices.size());
    for (const stl_triangle_vertex_indices &triangle : shared.indices) {
        const int first = int(duplicated.vertices.size());
        duplicated.vertices.push_back(shared.vertices[triangle[0]]);
        duplicated.vertices.push_back(shared.vertices[triangle[1]]);
        duplicated.vertices.push_back(shared.vertices[triangle[2]]);
        duplicated.indices.emplace_back(first, first + 1, first + 2);
    }
    return duplicated;
}

indexed_triangle_set make_v_ridge()
{
    return make_v_crease(true);
}

indexed_triangle_set make_feature_strip()
{
    indexed_triangle_set mesh;
    mesh.vertices = {
        Vec3f(0.f, 0.f, 0.f),
        Vec3f(1.f, 0.f, 0.f),
        Vec3f(0.f, 1.f, 0.f),
        Vec3f(1.f, 1.f, 1.f),
        Vec3f(0.f, 2.f, 1.f),
    };
    mesh.indices = {
        stl_triangle_vertex_indices(0, 1, 2),
        stl_triangle_vertex_indices(1, 2, 3),
        stl_triangle_vertex_indices(2, 3, 4),
    };
    return mesh;
}

float max_score(const std::vector<float> &scores)
{
    return *std::max_element(scores.begin(), scores.end());
}

} // namespace

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

TEST_CASE("Surface feature analysis distinguishes a trough from a ridge", "[SurfaceFeatureAnalysis]")
{
    const SurfaceFeatureField trough = analyze_surface_features(make_v_trough(), {});
    const SurfaceFeatureField ridge = analyze_surface_features(make_v_ridge(), {});

    REQUIRE(trough.status == SurfaceFeatureAnalysisStatus::Complete);
    REQUIRE(ridge.status == SurfaceFeatureAnalysisStatus::Complete);
    CHECK(max_score(trough.valley_scores) > 0.0f);
    CHECK(max_score(trough.valley_scores) > max_score(trough.ridge_scores));
    CHECK(max_score(ridge.ridge_scores) > 0.0f);
    CHECK(max_score(ridge.ridge_scores) > max_score(ridge.valley_scores));
}

TEST_CASE("Surface feature analysis joins coincident STL vertices before scoring", "[SurfaceFeatureAnalysis]")
{
    const SurfaceFeatureField field = analyze_surface_features(make_duplicate_vertex_trough(), {});

    CHECK(max_score(field.valley_scores) > 0.0f);
}

TEST_CASE("Surface feature analysis preserves trough classification when triangle storage is reordered", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set original_mesh = make_v_trough();
    indexed_triangle_set reordered_mesh = original_mesh;
    reordered_mesh.indices = {
        original_mesh.indices[2],
        original_mesh.indices[0],
        original_mesh.indices[3],
        original_mesh.indices[1],
    };
    const std::vector<size_t> reordered_to_original = { 2, 0, 3, 1 };

    const SurfaceFeatureField original = analyze_surface_features(original_mesh, {});
    const SurfaceFeatureField reordered = analyze_surface_features(reordered_mesh, {});

    REQUIRE(original.status == SurfaceFeatureAnalysisStatus::Complete);
    REQUIRE(reordered.status == SurfaceFeatureAnalysisStatus::Complete);
    REQUIRE(original.valley_scores.size() == reordered.valley_scores.size());
    for (size_t reordered_index = 0; reordered_index < reordered_to_original.size(); ++reordered_index) {
        const size_t original_index = reordered_to_original[reordered_index];
        CHECK(reordered.valley_scores[reordered_index] == Approx(original.valley_scores[original_index]));
        CHECK(reordered.ridge_scores[reordered_index] == Approx(original.ridge_scores[original_index]));
    }
}

TEST_CASE("Surface feature analysis warns on non-manifold shared edges", "[SurfaceFeatureAnalysis]")
{
    indexed_triangle_set mesh;
    mesh.vertices = {
        Vec3f(0.f, 0.f, 0.f), Vec3f(1.f, 0.f, 0.f), Vec3f(0.f, 1.f, 0.f),
        Vec3f(0.f, -1.f, 0.f), Vec3f(0.f, 0.f, 1.f),
    };
    mesh.indices = {
        stl_triangle_vertex_indices(0, 1, 2),
        stl_triangle_vertex_indices(1, 0, 3),
        stl_triangle_vertex_indices(0, 1, 4),
    };

    const SurfaceFeatureField field = analyze_surface_features(mesh, {});
    CHECK(std::any_of(field.warnings.begin(), field.warnings.end(), [](const SurfaceFeatureWarning &warning) {
        return warning.code == SurfaceFeatureWarning::Code::NonManifoldEdge;
    }));
}

TEST_CASE("Surface feature analysis rejects invalid triangle indices", "[SurfaceFeatureAnalysis]")
{
    indexed_triangle_set mesh = make_two_triangle_plane();
    mesh.indices.front()[2] = 4;

    const SurfaceFeatureField field = analyze_surface_features(mesh, {});
    CHECK(field.status == SurfaceFeatureAnalysisStatus::InvalidMesh);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
}

TEST_CASE("Surface feature analysis rejects non-finite vertex coordinates", "[SurfaceFeatureAnalysis]")
{
    indexed_triangle_set mesh = make_two_triangle_plane();
    mesh.vertices[1].x() = std::numeric_limits<float>::quiet_NaN();

    const SurfaceFeatureField field = analyze_surface_features(mesh, {});
    CHECK(field.status == SurfaceFeatureAnalysisStatus::InvalidMesh);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
    CHECK(field.triangle_areas_mm2.empty());
    CHECK(field.triangle_neighbors.empty());
}

TEST_CASE("Surface feature analysis does not publish partial results when canceled after analysis begins", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set mesh = make_two_triangle_plane();
    size_t cancellation_checks = 0;
    const SurfaceFeatureField field = analyze_surface_features(mesh, {}, [&cancellation_checks] {
        return ++cancellation_checks >= 5;
    });

    CHECK(field.status == SurfaceFeatureAnalysisStatus::Canceled);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
}

TEST_CASE("Surface feature analysis cancels while sorting edge records", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set mesh = make_disconnected_triangles(64);
    const size_t checks_before_sort = 4;
    size_t cancellation_checks = 0;
    const SurfaceFeatureField field = analyze_surface_features(mesh, {}, [&] {
        return ++cancellation_checks > checks_before_sort;
    });

    CHECK(field.status == SurfaceFeatureAnalysisStatus::Canceled);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
    CHECK(cancellation_checks == checks_before_sort + 1);
}

TEST_CASE("Surface feature analysis smooths feature scores across direct neighbors", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set mesh = make_feature_strip();
    SurfaceFeatureAnalysisOptions raw_options;
    raw_options.analysis_radius_mm = 0.0f;
    const SurfaceFeatureField raw = analyze_surface_features(mesh, raw_options);

    SurfaceFeatureAnalysisOptions smoothed_options = raw_options;
    smoothed_options.analysis_radius_mm = 10.0f;
    smoothed_options.smoothing_pass_limit = 1;
    const SurfaceFeatureField smoothed = analyze_surface_features(mesh, smoothed_options);

    REQUIRE(raw.status == SurfaceFeatureAnalysisStatus::Complete);
    REQUIRE(smoothed.status == SurfaceFeatureAnalysisStatus::Complete);
    REQUIRE(raw.valley_scores.size() == 3);
    REQUIRE(smoothed.valley_scores.size() == 3);
    CHECK((smoothed.valley_scores != raw.valley_scores || smoothed.ridge_scores != raw.ridge_scores));
}

TEST_CASE("Surface feature analysis can keep ridge smoothing localized", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set mesh = make_v_ridge();
    SurfaceFeatureAnalysisOptions raw_options;
    raw_options.analysis_radius_mm = 0.0f;
    const SurfaceFeatureField raw = analyze_surface_features(mesh, raw_options);

    SurfaceFeatureAnalysisOptions limited_options;
    limited_options.analysis_radius_mm = 10.0f;
    limited_options.smoothing_pass_limit = 3;
    limited_options.ridge_smoothing_pass_limit = 0;
    const SurfaceFeatureField limited = analyze_surface_features(mesh, limited_options);

    REQUIRE(raw.status == SurfaceFeatureAnalysisStatus::Complete);
    REQUIRE(limited.status == SurfaceFeatureAnalysisStatus::Complete);
    CHECK(limited.ridge_scores == raw.ridge_scores);
}

TEST_CASE("Surface feature analysis bounds a non-finite radius before deriving smoothing passes", "[SurfaceFeatureAnalysis]")
{
    const indexed_triangle_set mesh = make_feature_strip();
    SurfaceFeatureAnalysisOptions finite_options;
    finite_options.analysis_radius_mm = 10.0f;
    finite_options.smoothing_pass_limit = 1;

    SurfaceFeatureAnalysisOptions non_finite_options = finite_options;
    non_finite_options.analysis_radius_mm = std::numeric_limits<float>::infinity();

    CHECK(analyze_surface_features(mesh, non_finite_options) == analyze_surface_features(mesh, finite_options));
}

TEST_CASE("Surface feature analysis cancels during smoothing without publishing scores", "[SurfaceFeatureAnalysis]")
{
    SurfaceFeatureAnalysisOptions options;
    options.analysis_radius_mm = 10.0f;
    options.smoothing_pass_limit = 1;
    size_t cancellation_checks = 0;
    const SurfaceFeatureField field = analyze_surface_features(make_two_triangle_plane(), options, [&cancellation_checks] {
        return ++cancellation_checks >= 7;
    });

    CHECK(field.status == SurfaceFeatureAnalysisStatus::Canceled);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
}

TEST_CASE("Surface feature selection removes undersized isolated patches", "[SurfaceFeatureAnalysis]")
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Complete;
    field.valley_scores = { 0.9f, 0.9f, 0.05f };
    field.triangle_areas_mm2 = { 0.02f, 0.02f, 1.0f };
    field.triangle_neighbors = { { 1 }, { 0 }, {} };

    CHECK(select_surface_feature_triangles(field, SurfaceFeatureMode::Valleys, 0.5f, 0.1f).empty());
    CHECK(select_surface_feature_triangles(field, SurfaceFeatureMode::Valleys, 0.5f, 0.0f) == std::vector<size_t> { 0, 1 });
}

TEST_CASE("Surface feature selection combines valleys and ridges for a deviation preview", "[SurfaceFeatureAnalysis]")
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Complete;
    field.valley_scores = { 0.8f, 0.1f };
    field.ridge_scores = { 0.1f, 0.8f };
    field.triangle_areas_mm2 = { 1.0f, 1.0f };
    field.triangle_neighbors = { { 1 }, { 0 } };

    CHECK(select_surface_feature_triangles(field, SurfaceFeatureMode::Both, 0.5f, 0.0f) == std::vector<size_t> { 0, 1 });
}

TEST_CASE("Surface feature band smoothing removes isolated color islands", "[SurfaceFeatureAnalysis]")
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Complete;
    field.triangle_neighbors = { { 1 }, { 0, 2 }, { 1, 3 }, { 2 } };

    CHECK(smooth_surface_feature_band_assignments(field, { 0, 1, 2, 3 }, { 0, 1, 0, 0 }, 1) ==
          std::vector<size_t> { 0, 0, 0, 0 });
}

TEST_CASE("Surface feature band smoothing keeps an established boundary", "[SurfaceFeatureAnalysis]")
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Complete;
    field.triangle_neighbors = { { 1 }, { 0, 2 }, { 1, 3 }, { 2 } };

    CHECK(smooth_surface_feature_band_assignments(field, { 0, 1, 2, 3 }, { 0, 0, 1, 1 }, 3) ==
          std::vector<size_t> { 0, 0, 1, 1 });
}

TEST_CASE("Surface feature band smoothing stays within the selected facets", "[SurfaceFeatureAnalysis]")
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Complete;
    field.triangle_neighbors = { { 1 }, { 0, 2 }, { 1, 3 }, { 2 } };

    CHECK(smooth_surface_feature_band_assignments(field, { 1, 2 }, { 0, 1 }, 2) ==
          std::vector<size_t> { 0, 1 });
}

TEST_CASE("Surface feature enabled bands preserve disabled facets", "[SurfaceFeatureAnalysis]")
{
    CHECK(select_surface_feature_enabled_bands({ 0, 1, 2, 1, 4 }, { true, false, true }) ==
          std::vector<bool> { true, false, true, false, false });
}

TEST_CASE("Surface color layers resolve in stack order", "[SurfaceColorPaintLayers]")
{
    SurfaceColorPaintLayerStack stack({ 1, 1, 1, 1 });
    stack.add_paint_layer("Base accent", { { 1, 2 }, { 2, 3 } });
    stack.add_paint_layer("Highlight", { { 2, 4 } });
    CHECK(stack.resolve() == std::vector<unsigned int> { 1, 2, 4, 1 });
}

TEST_CASE("Surface color protection rejects later paint", "[SurfaceColorPaintLayers]")
{
    SurfaceColorPaintLayerStack stack({ 1, 1, 1 });
    const size_t protected_layer = stack.add_paint_layer("Protected", { { 1, 2 } });
    stack.layers()[protected_layer].protect_painted_facets = true;
    stack.add_paint_layer("Later", { { 1, 3 }, { 2, 3 } });
    CHECK(stack.resolve() == std::vector<unsigned int> { 1, 2, 3 });
}

TEST_CASE("Generic masks protect facets without producing a filament", "[SurfaceColorPaintLayers]")
{
    SurfaceColorPaintLayerStack stack({ 1, 1, 1 });
    stack.add_protect_layer("Keep face", { 0, 2 });
    stack.add_paint_layer("Later", { { 0, 3 }, { 1, 3 }, { 2, 3 } });
    CHECK(stack.resolve() == std::vector<unsigned int> { 1, 3, 1 });
}

TEST_CASE("Disabled surface color layers leave base paint unchanged", "[SurfaceColorPaintLayers]")
{
    SurfaceColorPaintLayerStack stack({ 1, 1 });
    const size_t layer = stack.add_paint_layer("Disabled", { { 0, 2 }, { 1, 3 } });
    stack.layers()[layer].enabled = false;
    CHECK(stack.resolve() == std::vector<unsigned int> { 1, 1 });
}

TEST_CASE("Surface color layers can explicitly ignore earlier protection", "[SurfaceColorPaintLayers]")
{
    SurfaceColorPaintLayerStack stack({ 1, 1 });
    stack.add_protect_layer("Mask", { 0 });
    const size_t layer = stack.add_paint_layer("Override", { { 0, 4 } });
    stack.layers()[layer].ignore_protection = true;
    CHECK(stack.resolve() == std::vector<unsigned int> { 4, 1 });
}

TEST_CASE("Surface color layers round trip deterministically", "[SurfaceColorPaintLayers]")
{
    SurfaceColorPaintLayerStack stack({ 1, 3, 1, 2 });
    const size_t accent = stack.add_paint_layer("Valley blend", { { 1, 5 }, { 3, 6, false } });
    stack.layers()[accent].visible = false;
    stack.layers()[accent].protect_painted_facets = true;
    const size_t mask = stack.add_protect_layer("Do not repaint", { 0, 2 });
    stack.layers()[mask].ignore_protection = true;

    const std::string serialized = serialize_surface_color_paint_layer_stack(stack);
    const auto restored = deserialize_surface_color_paint_layer_stack(serialized);

    REQUIRE(restored);
    CHECK(serialize_surface_color_paint_layer_stack(*restored) == serialized);
    CHECK(restored->base_filaments() == stack.base_filaments());
    REQUIRE(restored->layers().size() == 2);
    CHECK(restored->layers()[0].name == "Valley blend");
    CHECK(restored->layers()[0].role == SurfaceColorPaintLayerRole::Paint);
    CHECK_FALSE(restored->layers()[0].visible);
    CHECK(restored->layers()[0].protect_painted_facets);
    CHECK(restored->layers()[0].assignments[1].enabled == false);
    CHECK(restored->layers()[1].role == SurfaceColorPaintLayerRole::Protect);
    CHECK(restored->layers()[1].ignore_protection);
}

TEST_CASE("Surface feature color suggestion prefers dark valleys and bright ridges", "[SurfaceFeatureAnalysis]")
{
    const std::vector<SurfaceFeatureColor> palette {
        { 180, 180, 180, 255 },
        { 20, 20, 20, 255 },
        { 250, 240, 80, 255 },
    };

    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 0, palette) == 1);
    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Ridges, 0, palette) == 2);
    CHECK_FALSE(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 0, { palette.front() }));
}

TEST_CASE("Surface feature color suggestion rejects insufficient contrast and invalid bases", "[SurfaceFeatureAnalysis]")
{
    const std::vector<SurfaceFeatureColor> palette {
        { 100, 100, 100, 255 },
        { 110, 110, 110, 255 },
        { 10, 10, 10, 255 },
        { 245, 245, 245, 255 },
    };

    CHECK_FALSE(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, palette.size(), palette));
    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 0, palette) == 2);
    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Ridges, 0, palette) == 3);
}

TEST_CASE("Surface feature color suggestion ignores unavailable colors", "[SurfaceFeatureAnalysis]")
{
    const std::vector<SurfaceFeatureColor> palette {
        { 220, 220, 220, 255 },
        { 10, 10, 10, 0 },
        { 20, 20, 20, 255 },
    };

    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 0, palette) == 2);
    CHECK_FALSE(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 1, palette));
}

TEST_CASE("Surface feature color suggestion breaks equal luminance ties by palette index", "[SurfaceFeatureAnalysis]")
{
    const std::vector<SurfaceFeatureColor> palette {
        { 180, 180, 180, 255 },
        { 20, 20, 20, 255 },
        { 20, 20, 20, 255 },
        { 250, 250, 250, 255 },
        { 250, 250, 250, 255 },
    };

    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Valleys, 0, palette) == 1);
    CHECK(suggest_surface_feature_filament(SurfaceFeatureMode::Ridges, 0, palette) == 3);
}
