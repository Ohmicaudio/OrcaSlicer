#include "SurfaceFeatureAnalysis.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <map>
#include <sstream>
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

    // Binary STL commonly duplicates a coordinate for every triangle. Build
    // shared topology for scoring only; the source mesh remains untouched.
    indexed_triangle_set topology = mesh;
    its_merge_vertices(topology);

    const size_t triangle_count = topology.indices.size();
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

        const stl_triangle_vertex_indices &triangle = topology.indices[triangle_index];
        const Vec3f &first = topology.vertices[triangle[0]];
        const Vec3f &second = topology.vertices[triangle[1]];
        const Vec3f &third = topology.vertices[triangle[2]];
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
                const Vec3f edge_direction = (topology.vertices[first_use.edge.second] - topology.vertices[first_use.edge.first]).normalized();
                const float edge_length = (topology.vertices[first_use.edge.second] - topology.vertices[first_use.edge.first]).norm();
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
                    // A broad convex form contains many small positive bends.
                    // Accumulating them makes it look like one large ridge;
                    // retain only the sharpest local convex edge instead.
                    field.ridge_scores[first_triangle] = std::max(field.ridge_scores[first_triangle], score);
                    field.ridge_scores[second_triangle] = std::max(field.ridge_scores[second_triangle], score);
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
    const unsigned ridge_passes = std::min(passes, options.ridge_smoothing_pass_limit);
    if (!smooth_scores(field.valley_scores, field.triangle_neighbors, passes, is_canceled)
        || !smooth_scores(field.ridge_scores, field.triangle_neighbors, ridge_passes, is_canceled))
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
    const size_t score_count = mode == SurfaceFeatureMode::Ridges ?
        field.ridge_scores.size() : field.valley_scores.size();
    const bool needs_ridge_scores = mode == SurfaceFeatureMode::Both;
    if (field.status != SurfaceFeatureAnalysisStatus::Complete
        || (needs_ridge_scores && field.ridge_scores.size() != score_count)
        || field.triangle_areas_mm2.size() != score_count
        || field.triangle_neighbors.size() != score_count)
        return {};

    const auto score_at = [&field, mode](size_t triangle_index) {
        switch (mode) {
        case SurfaceFeatureMode::Both:
            return std::max(field.valley_scores[triangle_index], field.ridge_scores[triangle_index]);
        case SurfaceFeatureMode::Valleys:
            return field.valley_scores[triangle_index];
        case SurfaceFeatureMode::Ridges:
            return field.ridge_scores[triangle_index];
        }
        return 0.0f;
    };

    const float minimum_area = std::max(0.0f, min_patch_area_mm2);
    std::vector<bool> visited(score_count, false);
    std::vector<size_t> selected;
    for (size_t triangle_index = 0; triangle_index < score_count; ++triangle_index) {
        if (visited[triangle_index] || score_at(triangle_index) < threshold)
            continue;

        std::vector<size_t> component { triangle_index };
        visited[triangle_index] = true;
        float component_area = 0.0f;
        for (size_t component_index = 0; component_index < component.size(); ++component_index) {
            const size_t current = component[component_index];
            component_area += field.triangle_areas_mm2[current];
            for (size_t neighbor : field.triangle_neighbors[current]) {
                if (neighbor < score_count && !visited[neighbor] && score_at(neighbor) >= threshold) {
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

std::vector<size_t> smooth_surface_feature_band_assignments(
    const SurfaceFeatureField &field,
    const std::vector<size_t> &triangle_indices,
    const std::vector<size_t> &band_assignments,
    unsigned smoothing_passes)
{
    if (field.status != SurfaceFeatureAnalysisStatus::Complete
        || triangle_indices.size() != band_assignments.size()
        || field.triangle_neighbors.empty() && !triangle_indices.empty())
        return {};

    std::vector<int> selected_index(field.triangle_neighbors.size(), -1);
    for (size_t index = 0; index < triangle_indices.size(); ++index) {
        const size_t triangle_index = triangle_indices[index];
        if (triangle_index >= selected_index.size() || selected_index[triangle_index] != -1)
            return {};
        selected_index[triangle_index] = static_cast<int>(index);
    }

    std::vector<size_t> current = band_assignments;
    for (unsigned pass = 0; pass < smoothing_passes; ++pass) {
        std::vector<size_t> next = current;
        for (size_t selected_idx = 0; selected_idx < triangle_indices.size(); ++selected_idx) {
            std::map<size_t, size_t> band_counts;
            ++band_counts[current[selected_idx]];
            for (const size_t neighbor : field.triangle_neighbors[triangle_indices[selected_idx]]) {
                if (neighbor >= selected_index.size() || selected_index[neighbor] == -1)
                    continue;
                ++band_counts[current[static_cast<size_t>(selected_index[neighbor])]];
            }

            const size_t current_band = current[selected_idx];
            size_t chosen_band = current_band;
            size_t highest_count = band_counts[current_band];
            for (const auto &[band, count] : band_counts) {
                // Keep the current band on ties. This avoids oscillation and
                // leaves an established boundary in place.
                if (count > highest_count) {
                    chosen_band = band;
                    highest_count = count;
                }
            }
            next[selected_idx] = chosen_band;
        }
        current = std::move(next);
    }

    return current;
}

std::vector<bool> select_surface_feature_enabled_bands(
    const std::vector<size_t> &band_assignments,
    const std::vector<bool> &enabled_bands)
{
    std::vector<bool> selected;
    selected.reserve(band_assignments.size());
    for (const size_t band : band_assignments)
        selected.emplace_back(band < enabled_bands.size() && enabled_bands[band]);
    return selected;
}

SurfaceColorPaintLayerStack::SurfaceColorPaintLayerStack(std::vector<unsigned int> base_filaments)
    : m_base_filaments(std::move(base_filaments))
{
}

size_t SurfaceColorPaintLayerStack::add_paint_layer(
    std::string name,
    std::vector<SurfaceColorPaintAssignment> assignments)
{
    m_layers.emplace_back(SurfaceColorPaintLayer {
        std::move(name), SurfaceColorPaintLayerRole::Paint, true, true, false, false, std::move(assignments)
    });
    return m_layers.size() - 1;
}

size_t SurfaceColorPaintLayerStack::add_protect_layer(std::string name, std::vector<size_t> triangle_indices)
{
    std::vector<SurfaceColorPaintAssignment> assignments;
    assignments.reserve(triangle_indices.size());
    for (const size_t triangle_index : triangle_indices)
        assignments.emplace_back(SurfaceColorPaintAssignment { triangle_index, 0, true });
    m_layers.emplace_back(SurfaceColorPaintLayer {
        std::move(name), SurfaceColorPaintLayerRole::Protect, true, true, false, false, std::move(assignments)
    });
    return m_layers.size() - 1;
}

bool SurfaceColorPaintLayerStack::move_layer(size_t from_index, size_t to_index)
{
    if (from_index >= m_layers.size() || to_index >= m_layers.size() || from_index == to_index)
        return from_index == to_index && from_index < m_layers.size();

    SurfaceColorPaintLayer layer = std::move(m_layers[from_index]);
    m_layers.erase(m_layers.begin() + from_index);
    m_layers.insert(m_layers.begin() + to_index, std::move(layer));
    return true;
}

bool SurfaceColorPaintLayerStack::erase_layer(size_t layer_index)
{
    if (layer_index >= m_layers.size())
        return false;
    m_layers.erase(m_layers.begin() + layer_index);
    return true;
}

bool SurfaceColorPaintLayerStack::duplicate_layer(size_t layer_index)
{
    if (layer_index >= m_layers.size())
        return false;
    SurfaceColorPaintLayer copy = m_layers[layer_index];
    copy.name += " copy";
    m_layers.insert(m_layers.begin() + layer_index + 1, std::move(copy));
    return true;
}

std::string serialize_surface_color_paint_layer_stack(const SurfaceColorPaintLayerStack &stack)
{
    std::ostringstream output;
    output << "surface_color_paint_layers_v1\n";
    output << "base " << stack.base_filaments().size();
    for (const unsigned int filament_id : stack.base_filaments())
        output << ' ' << filament_id;
    output << "\nlayers " << stack.layers().size() << '\n';

    for (const SurfaceColorPaintLayer &layer : stack.layers()) {
        output << "layer " << std::quoted(layer.name) << ' '
               << static_cast<unsigned int>(layer.role) << ' '
               << layer.enabled << ' ' << layer.visible << ' '
               << layer.protect_painted_facets << ' ' << layer.ignore_protection << ' '
               << layer.assignments.size() << '\n';
        for (const SurfaceColorPaintAssignment &assignment : layer.assignments)
            output << "assignment " << assignment.triangle_index << ' '
                   << assignment.filament_id << ' ' << assignment.enabled << '\n';
    }
    return output.str();
}

std::optional<SurfaceColorPaintLayerStack> deserialize_surface_color_paint_layer_stack(const std::string &serialized)
{
    std::istringstream input(serialized);
    std::string header;
    if (!std::getline(input, header) || header != "surface_color_paint_layers_v1")
        return std::nullopt;

    std::string tag;
    size_t base_count = 0;
    if (!(input >> tag >> base_count) || tag != "base")
        return std::nullopt;
    std::vector<unsigned int> base_filaments(base_count);
    for (unsigned int &filament_id : base_filaments)
        if (!(input >> filament_id))
            return std::nullopt;

    size_t layer_count = 0;
    if (!(input >> tag >> layer_count) || tag != "layers")
        return std::nullopt;

    SurfaceColorPaintLayerStack stack(std::move(base_filaments));
    for (size_t layer_index = 0; layer_index < layer_count; ++layer_index) {
        SurfaceColorPaintLayer layer;
        unsigned int role = 0;
        size_t assignment_count = 0;
        if (!(input >> tag >> std::quoted(layer.name) >> role >> layer.enabled >> layer.visible
              >> layer.protect_painted_facets >> layer.ignore_protection >> assignment_count)
            || tag != "layer" || role > static_cast<unsigned int>(SurfaceColorPaintLayerRole::Protect))
            return std::nullopt;
        layer.role = static_cast<SurfaceColorPaintLayerRole>(role);
        layer.assignments.resize(assignment_count);
        for (SurfaceColorPaintAssignment &assignment : layer.assignments)
            if (!(input >> tag >> assignment.triangle_index >> assignment.filament_id >> assignment.enabled)
                || tag != "assignment")
                return std::nullopt;
        stack.layers().emplace_back(std::move(layer));
    }

    input >> std::ws;
    return input.eof() ? std::optional<SurfaceColorPaintLayerStack>(std::move(stack)) : std::nullopt;
}

std::vector<unsigned int> SurfaceColorPaintLayerStack::resolve() const
{
    std::vector<unsigned int> resolved = m_base_filaments;
    std::vector<bool> protected_facets(resolved.size(), false);

    for (const SurfaceColorPaintLayer &layer : m_layers) {
        if (!layer.enabled)
            continue;
        for (const SurfaceColorPaintAssignment &assignment : layer.assignments) {
            if (!assignment.enabled || assignment.triangle_index >= resolved.size())
                continue;
            if (layer.role == SurfaceColorPaintLayerRole::Paint && assignment.filament_id != 0 &&
                (layer.ignore_protection || !protected_facets[assignment.triangle_index]))
                resolved[assignment.triangle_index] = assignment.filament_id;
        }
        if (layer.role == SurfaceColorPaintLayerRole::Protect || layer.protect_painted_facets)
            for (const SurfaceColorPaintAssignment &assignment : layer.assignments)
                if (assignment.enabled && assignment.triangle_index < protected_facets.size())
                    protected_facets[assignment.triangle_index] = true;
    }
    return resolved;
}

std::optional<size_t> suggest_surface_feature_filament(
    SurfaceFeatureMode mode,
    size_t base_filament,
    const std::vector<SurfaceFeatureColor> &palette)
{
    if (base_filament >= palette.size() || !is_usable_color(palette[base_filament]))
        return std::nullopt;

    constexpr float minimum_contrast = 0.10f;
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
