#include "SurfaceFeatureAnalysis.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <tuple>
#include <utility>

namespace Slic3r {

namespace {

using Edge = std::pair<int, int>;

constexpr float pi = 3.14159265358979323846f;

class SortCanceled {};

struct EdgeRecord
{
    Edge edge;
    size_t triangle_index;
    int directed_first_vertex;
    int directed_second_vertex;

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

bool follows_canonical_edge_direction(const EdgeRecord &record)
{
    return record.directed_first_vertex == record.edge.first
        && record.directed_second_vertex == record.edge.second;
}

float linear_srgb(uint8_t component)
{
    const float normalized = float(component) / 255.0f;
    return normalized <= 0.04045f
        ? normalized / 12.92f
        : std::pow((normalized + 0.055f) / 1.055f, 2.4f);
}

float relative_luminance(const SurfaceFeatureColor &color)
{
    return 0.2126f * linear_srgb(color.red)
         + 0.7152f * linear_srgb(color.green)
         + 0.0722f * linear_srgb(color.blue);
}

bool is_usable_color(const SurfaceFeatureColor &color)
{
    return color.alpha != 0;
}

bool should_cancel(const std::function<bool()> &callback)
{
    return callback && callback();
}

bool is_canceled_at_interval(const std::function<bool()> &callback, size_t index)
{
    constexpr size_t cancellation_poll_interval = 4096;
    return index % cancellation_poll_interval == 0 && should_cancel(callback);
}

SurfaceFeatureField canceled_field()
{
    SurfaceFeatureField field;
    field.status = SurfaceFeatureAnalysisStatus::Canceled;
    return field;
}

bool smooth_scores(
    std::vector<float> &scores,
    const std::vector<std::vector<size_t>> &neighbors,
    unsigned passes,
    const std::function<bool()> &is_canceled)
{
    std::vector<float> smoothed(scores.size());
    for (unsigned pass = 0; pass < passes; ++pass) {
        for (size_t triangle_index = 0; triangle_index < scores.size(); ++triangle_index) {
            if (is_canceled_at_interval(is_canceled, triangle_index))
                return false;

            float total = scores[triangle_index];
            for (size_t neighbor : neighbors[triangle_index])
                total += scores[neighbor];
            smoothed[triangle_index] = total / float(neighbors[triangle_index].size() + 1);
        }
        scores.swap(smoothed);
    }
    return !should_cancel(is_canceled);
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
    const SurfaceFeatureAnalysisOptions &options,
    const std::function<bool()> &is_canceled)
{
    if (should_cancel(is_canceled))
        return canceled_field();

    for (size_t vertex_index = 0; vertex_index < mesh.vertices.size(); ++vertex_index) {
        if (is_canceled_at_interval(is_canceled, vertex_index))
            return canceled_field();

        const Vec3f &vertex = mesh.vertices[vertex_index];
        if (!std::isfinite(vertex.x()) || !std::isfinite(vertex.y()) || !std::isfinite(vertex.z())) {
            SurfaceFeatureField field;
            field.status = SurfaceFeatureAnalysisStatus::InvalidMesh;
            return field;
        }
    }

    const size_t triangle_count = mesh.indices.size();
    for (size_t triangle_index = 0; triangle_index < triangle_count; ++triangle_index) {
        if (is_canceled_at_interval(is_canceled, triangle_index))
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

    std::vector<Vec3f> face_normals(triangle_count, Vec3f::Zero());

    std::vector<EdgeRecord> edge_records;
    edge_records.reserve(triangle_count * 3);
    for (size_t triangle_index = 0; triangle_index < triangle_count; ++triangle_index) {
        if (is_canceled_at_interval(is_canceled, triangle_index))
            return canceled_field();

        const stl_triangle_vertex_indices &triangle = mesh.indices[triangle_index];
        const Vec3f &first = mesh.vertices[triangle[0]];
        const Vec3f &second = mesh.vertices[triangle[1]];
        const Vec3f &third = mesh.vertices[triangle[2]];
        const Vec3f normal = (second - first).cross(third - first);
        const float doubled_area = normal.norm();

        if (doubled_area == 0.0f)
            field.warnings.push_back({ SurfaceFeatureWarning::Code::DegenerateTriangle, triangle_index });
        else {
            field.triangle_areas_mm2[triangle_index] = 0.5f * doubled_area;
            face_normals[triangle_index] = normal / doubled_area;
        }

        for (size_t edge = 0; edge < 3; ++edge) {
            const int next = edge == 2 ? 0 : int(edge) + 1;
            edge_records.push_back({ make_edge(triangle[edge], triangle[next]), triangle_index, triangle[edge], triangle[next] });
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

    float total_valid_edge_length = 0.0f;
    size_t valid_edge_count = 0;
    for (size_t begin = 0; begin < edge_records.size();) {
        if (is_canceled_at_interval(is_canceled, begin))
            return canceled_field();

        size_t end = begin + 1;
        while (end < edge_records.size() && edge_records[end].edge == edge_records[begin].edge)
            ++end;

        const size_t incident_count = end - begin;
        if (incident_count == 1) {
            field.warnings.push_back({ SurfaceFeatureWarning::Code::BoundaryEdge, edge_records[begin].triangle_index });
        } else if (incident_count == 2) {
            const EdgeRecord &first_record = edge_records[begin];
            const EdgeRecord &second_record = edge_records[begin + 1];
            const bool first_follows_canonical_direction = follows_canonical_edge_direction(first_record);
            const EdgeRecord &first_use = first_follows_canonical_direction ? first_record : second_record;
            const EdgeRecord &second_use = first_follows_canonical_direction ? second_record : first_record;
            const size_t first_triangle = first_use.triangle_index;
            const size_t second_triangle = second_use.triangle_index;
            field.triangle_neighbors[first_triangle].push_back(second_triangle);
            field.triangle_neighbors[second_triangle].push_back(first_triangle);

            if (field.triangle_areas_mm2[first_triangle] > 0.0f && field.triangle_areas_mm2[second_triangle] > 0.0f) {
                const Vec3f edge_direction = (mesh.vertices[first_use.edge.second] - mesh.vertices[first_use.edge.first]).normalized();
                const float edge_length = (mesh.vertices[first_use.edge.second] - mesh.vertices[first_use.edge.first]).norm();
                if (edge_length > 0.0f) {
                    total_valid_edge_length += edge_length;
                    ++valid_edge_count;
                }
                const float signed_sine = edge_direction.dot(face_normals[first_triangle].cross(face_normals[second_triangle]));
                const float cosine = face_normals[first_triangle].dot(face_normals[second_triangle]);
                const float signed_bend = std::atan2(signed_sine, cosine);
                const float score = std::min(1.0f, std::abs(signed_bend) / pi);

                if (signed_bend < 0.0f) {
                    field.valley_scores[first_triangle] += score;
                    field.valley_scores[second_triangle] += score;
                } else if (signed_bend > 0.0f) {
                    field.ridge_scores[first_triangle] += score;
                    field.ridge_scores[second_triangle] += score;
                }
            }
        } else {
            for (size_t index = begin; index < end; ++index)
                field.warnings.push_back({ SurfaceFeatureWarning::Code::NonManifoldEdge, edge_records[index].triangle_index });
        }

        begin = end;
    }

    for (size_t triangle_index = 0; triangle_index < field.triangle_neighbors.size(); ++triangle_index) {
        if (is_canceled_at_interval(is_canceled, triangle_index))
            return canceled_field();
        std::vector<size_t> &neighbors = field.triangle_neighbors[triangle_index];
        std::sort(neighbors.begin(), neighbors.end());
        neighbors.erase(std::unique(neighbors.begin(), neighbors.end()), neighbors.end());
    }

    std::sort(field.warnings.begin(), field.warnings.end(), [](const SurfaceFeatureWarning &lhs, const SurfaceFeatureWarning &rhs) {
        return lhs.triangle_index != rhs.triangle_index
            ? lhs.triangle_index < rhs.triangle_index
            : lhs.code < rhs.code;
    });

    const double mean_edge_mm = valid_edge_count == 0 ? 0.0 : double(total_valid_edge_length) / double(valid_edge_count);
    const double smoothing_step_mm = std::max(mean_edge_mm, 0.001);
    const double requested_radius_mm = std::isfinite(options.analysis_radius_mm)
        ? std::max(0.0, double(options.analysis_radius_mm))
        : std::numeric_limits<double>::infinity();
    const double bounded_pass_count = std::min(
        std::ceil(requested_radius_mm / smoothing_step_mm),
        double(options.smoothing_pass_limit));
    const unsigned passes = static_cast<unsigned>(bounded_pass_count);
    if (!smooth_scores(field.valley_scores, field.triangle_neighbors, passes, is_canceled)
        || !smooth_scores(field.ridge_scores, field.triangle_neighbors, passes, is_canceled))
        return canceled_field();

    if (should_cancel(is_canceled))
        return canceled_field();

    return field;
}

std::vector<size_t> select_surface_feature_triangles(
    const SurfaceFeatureField &field,
    SurfaceFeatureMode mode,
    float threshold,
    float min_patch_area_mm2)
{
    const std::vector<float> &scores = mode == SurfaceFeatureMode::Valleys ? field.valley_scores : field.ridge_scores;
    if (field.status != SurfaceFeatureAnalysisStatus::Complete
        || field.triangle_areas_mm2.size() != scores.size()
        || field.triangle_neighbors.size() != scores.size())
        return {};

    const float minimum_area = std::max(0.0f, min_patch_area_mm2);
    std::vector<bool> visited(scores.size(), false);
    std::vector<size_t> selected;
    for (size_t triangle_index = 0; triangle_index < scores.size(); ++triangle_index) {
        if (visited[triangle_index] || scores[triangle_index] < threshold)
            continue;

        std::vector<size_t> component { triangle_index };
        visited[triangle_index] = true;
        float component_area = 0.0f;
        for (size_t component_index = 0; component_index < component.size(); ++component_index) {
            const size_t current = component[component_index];
            component_area += field.triangle_areas_mm2[current];
            for (size_t neighbor : field.triangle_neighbors[current]) {
                if (neighbor < scores.size() && !visited[neighbor] && scores[neighbor] >= threshold) {
                    visited[neighbor] = true;
                    component.push_back(neighbor);
                }
            }
        }

        if (component_area >= minimum_area)
            selected.insert(selected.end(), component.begin(), component.end());
    }
    std::sort(selected.begin(), selected.end());
    return selected;
}

std::optional<size_t> suggest_surface_feature_filament(
    SurfaceFeatureMode mode,
    size_t base_filament,
    const std::vector<SurfaceFeatureColor> &palette)
{
    if (base_filament >= palette.size() || !is_usable_color(palette[base_filament]))
        return std::nullopt;

    constexpr float minimum_contrast = 0.20f;
    const float base_luminance = relative_luminance(palette[base_filament]);
    std::optional<size_t> suggestion;
    float best_luminance = mode == SurfaceFeatureMode::Valleys
        ? std::numeric_limits<float>::infinity()
        : -std::numeric_limits<float>::infinity();

    for (size_t candidate = 0; candidate < palette.size(); ++candidate) {
        if (candidate == base_filament || !is_usable_color(palette[candidate]))
            continue;

        const float candidate_luminance = relative_luminance(palette[candidate]);
        if (std::abs(candidate_luminance - base_luminance) < minimum_contrast)
            continue;

        const bool is_better = mode == SurfaceFeatureMode::Valleys
            ? candidate_luminance < best_luminance
            : candidate_luminance > best_luminance;
        if (is_better) {
            suggestion = candidate;
            best_luminance = candidate_luminance;
        }
    }

    return suggestion;
}

} // namespace Slic3r
