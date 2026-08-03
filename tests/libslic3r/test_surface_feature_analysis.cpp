#include <algorithm>

#include <catch2/catch.hpp>

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

TEST_CASE("Surface feature analysis rejects invalid triangle indices", "[SurfaceFeatureAnalysis]")
{
    indexed_triangle_set mesh = make_two_triangle_plane();
    mesh.indices.front()[2] = 4;

    const SurfaceFeatureField field = analyze_surface_features(mesh, {});
    CHECK(field.status == SurfaceFeatureAnalysisStatus::InvalidMesh);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
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
    const size_t checks_before_sort = 2 * mesh.indices.size() + 2;
    size_t cancellation_checks = 0;
    const SurfaceFeatureField field = analyze_surface_features(mesh, {}, [&] {
        return ++cancellation_checks > checks_before_sort;
    });

    CHECK(field.status == SurfaceFeatureAnalysisStatus::Canceled);
    CHECK(field.valley_scores.empty());
    CHECK(field.ridge_scores.empty());
    CHECK(cancellation_checks == checks_before_sort + 1);
}
