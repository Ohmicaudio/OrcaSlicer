#ifndef slic3r_SurfaceFeatureAnalysis_hpp_
#define slic3r_SurfaceFeatureAnalysis_hpp_

#include "TriangleMesh.hpp"

#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace Slic3r {

enum class SurfaceFeatureMode {
    Both,
    Valleys,
    Ridges
};

enum class SurfaceFeatureAnalysisStatus {
    Complete,
    Canceled,
    InvalidMesh
};

struct SurfaceFeatureAnalysisOptions
{
    float analysis_radius_mm { 1.0f };
    float min_patch_area_mm2 { 0.25f };
    unsigned smoothing_pass_limit { 6 };
    // Convex surface variation spreads visually much faster than concave
    // recesses on dense organic meshes, so keep ridge smoothing tighter.
    unsigned ridge_smoothing_pass_limit { 2 };
};

struct SurfaceFeatureColor
{
    uint8_t red;
    uint8_t green;
    uint8_t blue;
    uint8_t alpha;

    bool operator==(const SurfaceFeatureColor &rhs) const
    {
        return red == rhs.red && green == rhs.green && blue == rhs.blue && alpha == rhs.alpha;
    }
};

struct SurfaceFeatureWarning
{
    enum class Code {
        BoundaryEdge,
        NonManifoldEdge,
        DegenerateTriangle
    };

    Code code;
    size_t triangle_index;

    bool operator==(const SurfaceFeatureWarning &rhs) const;
};

struct SurfaceFeatureField
{
    SurfaceFeatureAnalysisStatus status { SurfaceFeatureAnalysisStatus::Complete };
    std::vector<float> valley_scores;
    std::vector<float> ridge_scores;
    std::vector<float> triangle_areas_mm2;
    std::vector<std::vector<size_t>> triangle_neighbors;
    std::vector<SurfaceFeatureWarning> warnings;

    bool operator==(const SurfaceFeatureField &rhs) const;
};

SurfaceFeatureField analyze_surface_features(
    const indexed_triangle_set &mesh,
    const SurfaceFeatureAnalysisOptions &options,
    const std::function<bool()> &is_canceled = {});

std::vector<size_t> select_surface_feature_triangles(
    const SurfaceFeatureField &field,
    SurfaceFeatureMode mode,
    float threshold,
    float min_patch_area_mm2);

std::vector<size_t> smooth_surface_feature_band_assignments(
    const SurfaceFeatureField &field,
    const std::vector<size_t> &triangle_indices,
    const std::vector<size_t> &band_assignments,
    unsigned smoothing_passes,
    float minimum_component_area_mm2 = 0.0f);

// Returns one flag per assignment. Disabled bands deliberately leave their
// facets unchanged when a surface-color ramp is applied.
std::vector<bool> select_surface_feature_enabled_bands(
    const std::vector<size_t> &band_assignments,
    const std::vector<bool> &enabled_bands);

enum class SurfaceColorPaintLayerRole {
    Paint,
    Protect
};

struct SurfaceColorPaintAssignment
{
    size_t triangle_index { 0 };
    unsigned int filament_id { 0 };
    bool enabled { true };
};

struct SurfaceColorPaintLayer
{
    std::string name;
    SurfaceColorPaintLayerRole role { SurfaceColorPaintLayerRole::Paint };
    bool enabled { true };
    bool visible { true };
    bool protect_painted_facets { false };
    bool ignore_protection { false };
    std::vector<SurfaceColorPaintAssignment> assignments;
};

class SurfaceColorPaintLayerStack
{
public:
    explicit SurfaceColorPaintLayerStack(std::vector<unsigned int> base_filaments = {});

    size_t add_paint_layer(std::string name, std::vector<SurfaceColorPaintAssignment> assignments);
    size_t add_protect_layer(std::string name, std::vector<size_t> triangle_indices);
    bool move_layer(size_t from_index, size_t to_index);
    bool erase_layer(size_t layer_index);
    bool duplicate_layer(size_t layer_index);
    std::vector<unsigned int> resolve() const;

    const std::vector<unsigned int>& base_filaments() const { return m_base_filaments; }
    const std::vector<SurfaceColorPaintLayer>& layers() const { return m_layers; }
    std::vector<SurfaceColorPaintLayer>& layers() { return m_layers; }

private:
    std::vector<unsigned int> m_base_filaments;
    std::vector<SurfaceColorPaintLayer> m_layers;
};

// Stable, in-memory representation for project metadata. The encoding is
// deliberately independent of GUI and selector state so it can be stored by a
// future project-format extension without changing the resolved paint format.
std::string serialize_surface_color_paint_layer_stack(const SurfaceColorPaintLayerStack &stack);
std::optional<SurfaceColorPaintLayerStack> deserialize_surface_color_paint_layer_stack(const std::string &serialized);

std::optional<size_t> suggest_surface_feature_filament(
    SurfaceFeatureMode mode,
    size_t base_filament,
    const std::vector<SurfaceFeatureColor> &palette);

} // namespace Slic3r

#endif
