#include "SurfaceFeatureAnalysis.hpp"

#include <algorithm>
#include <map>
#include <utility>

namespace Slic3r {

namespace {

using Edge = std::pair<int, int>;
using EdgeFaces = std::map<Edge, std::vector<size_t>>;

Edge make_edge(int first, int second)
{
    return first < second ? Edge(first, second) : Edge(second, first);
}

bool should_cancel(const std::function<bool()> &callback)
{
    return callback && callback();
}

SurfaceFeatureField canceled_field()
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Canceled;
    return field;
}

} // namespace

bool SurfaceFeatureWarning::operator==(const SurfaceFeatureWarning &rhs) const
{
    return this->code == rhs.code && this->triangle_index == rhs.triangle_index;
}

bool SurfaceFeatureField::operator==(const SurfaceFeatureField &rhs) const
{
    return this->status == rhs.status
        && this->valley_scores == rhs.valley_scores
        && this->ridge_scores == rhs.ridge_scores
        && this->triangle_areas_mm2 == rhs.triangle_areas_mm2
        && this->triangle_neighbors == rhs.triangle_neighbors
        && this->warnings == rhs.warnings;
}

SurfaceFeatureField analyze_surface_features(
    const indexed_triangle_set &mesh,
    const SurfaceFeatureAnalysisOptions &,
    const std::function<bool()> &is_canceled)
{
    if (should_cancel(is_canceled))
        return canceled_field();

    const size_t triangle_count = mesh.indices.size();
    for (size_t triangle_index = 0; triangle_index < triangle_count; ++triangle_index) {
        if (should_cancel(is_canceled))
            return canceled_field();

        const stl_triangle_vertex_indices &triangle = mesh.indices[triangle_index];
        for (size_t vertex = 0; vertex < 3; ++vertex) {
            if (triangle[vertex] < 0 || size_t(triangle[vertex]) >= mesh.vertices.size()) {
                SurfaceFeatureField field;
                field.status = SurfaceFeatureAnalysisStatus::InvalidMesh;
                return field;
            }
        }
    }

    SurfaceFeatureField field;
    field.valley_scores.assign(triangle_count, 0.0f);
    field.ridge_scores.assign(triangle_count, 0.0f);
    field.triangle_areas_mm2.assign(triangle_count, 0.0f);
    field.triangle_neighbors.resize(triangle_count);

    EdgeFaces edge_faces;
    for (size_t triangle_index = 0; triangle_index < triangle_count; ++triangle_index) {
        if (should_cancel(is_canceled))
            return canceled_field();

        const stl_triangle_vertex_indices &triangle = mesh.indices[triangle_index];
        const Vec3f &first = mesh.vertices[triangle[0]];
        const Vec3f &second = mesh.vertices[triangle[1]];
        const Vec3f &third = mesh.vertices[triangle[2]];
        const Vec3f normal = (second - first).cross(third - first);
        const float doubled_area = normal.norm();

        if (doubled_area == 0.0f)
            field.warnings.push_back({ SurfaceFeatureWarning::Code::DegenerateTriangle, triangle_index });
        else
            field.triangle_areas_mm2[triangle_index] = 0.5f * doubled_area;

        for (size_t edge = 0; edge < 3; ++edge) {
            const int next = edge == 2 ? 0 : int(edge) + 1;
            edge_faces[make_edge(triangle[edge], triangle[next])].push_back(triangle_index);
        }
    }

    for (const auto &entry : edge_faces) {
        if (should_cancel(is_canceled))
            return canceled_field();

        const std::vector<size_t> &incident_triangles = entry.second;
        if (incident_triangles.size() == 1) {
            field.warnings.push_back({ SurfaceFeatureWarning::Code::BoundaryEdge, incident_triangles.front() });
        } else if (incident_triangles.size() == 2) {
            field.triangle_neighbors[incident_triangles[0]].push_back(incident_triangles[1]);
            field.triangle_neighbors[incident_triangles[1]].push_back(incident_triangles[0]);
        } else {
            for (size_t triangle_index : incident_triangles)
                field.warnings.push_back({ SurfaceFeatureWarning::Code::NonManifoldEdge, triangle_index });
        }
    }

    for (std::vector<size_t> &neighbors : field.triangle_neighbors)
        std::sort(neighbors.begin(), neighbors.end());

    std::sort(field.warnings.begin(), field.warnings.end(), [](const SurfaceFeatureWarning &lhs, const SurfaceFeatureWarning &rhs) {
        return lhs.triangle_index != rhs.triangle_index
            ? lhs.triangle_index < rhs.triangle_index
            : lhs.code < rhs.code;
    });

    return field;
}

std::vector<size_t> select_surface_feature_triangles(
    const SurfaceFeatureField &field,
    SurfaceFeatureMode mode,
    float threshold,
    float)
{
    const std::vector<float> &scores = mode == SurfaceFeatureMode::Valleys ? field.valley_scores : field.ridge_scores;
    std::vector<size_t> selected;
    for (size_t triangle_index = 0; triangle_index < scores.size(); ++triangle_index) {
        if (scores[triangle_index] >= threshold)
            selected.push_back(triangle_index);
    }
    return selected;
}

} // namespace Slic3r
