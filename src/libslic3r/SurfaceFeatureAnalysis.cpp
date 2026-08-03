#include "SurfaceFeatureAnalysis.hpp"

#include <algorithm>
#include <tuple>
#include <utility>

namespace Slic3r {

namespace {

using Edge = std::pair<int, int>;

class SortCanceled {};

struct EdgeRecord
{
    Edge edge;
    size_t triangle_index;

    bool operator<(const EdgeRecord &rhs) const
    {
        return std::tie(this->edge.first, this->edge.second, this->triangle_index)
             < std::tie(rhs.edge.first, rhs.edge.second, rhs.triangle_index);
    }
};

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

    std::vector<EdgeRecord> edge_records;
    edge_records.reserve(triangle_count * 3);
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
            edge_records.push_back({ make_edge(triangle[edge], triangle[next]), triangle_index });
        }
    }

    if (should_cancel(is_canceled))
        return canceled_field();

    size_t sort_comparison_count = 0;
    try {
        std::sort(edge_records.begin(), edge_records.end(), [&is_canceled, &sort_comparison_count](const EdgeRecord &lhs, const EdgeRecord &rhs) {
            constexpr size_t cancellation_poll_interval = 64;
            if (++sort_comparison_count % cancellation_poll_interval == 0 && should_cancel(is_canceled))
                throw SortCanceled();
            return lhs < rhs;
        });
    } catch (const SortCanceled &) {
        return canceled_field();
    }

    for (size_t begin = 0; begin < edge_records.size();) {
        if (should_cancel(is_canceled))
            return canceled_field();

        size_t end = begin + 1;
        while (end < edge_records.size() && edge_records[end].edge == edge_records[begin].edge)
            ++end;

        const size_t incident_count = end - begin;
        if (incident_count == 1) {
            field.warnings.push_back({ SurfaceFeatureWarning::Code::BoundaryEdge, edge_records[begin].triangle_index });
        } else if (incident_count == 2) {
            const size_t first_triangle = edge_records[begin].triangle_index;
            const size_t second_triangle = edge_records[begin + 1].triangle_index;
            field.triangle_neighbors[first_triangle].push_back(second_triangle);
            field.triangle_neighbors[second_triangle].push_back(first_triangle);
        } else {
            for (size_t index = begin; index < end; ++index)
                field.warnings.push_back({ SurfaceFeatureWarning::Code::NonManifoldEdge, edge_records[index].triangle_index });
        }

        begin = end;
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
