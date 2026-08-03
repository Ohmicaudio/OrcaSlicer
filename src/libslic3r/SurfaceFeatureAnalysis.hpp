#ifndef slic3r_SurfaceFeatureAnalysis_hpp_
#define slic3r_SurfaceFeatureAnalysis_hpp_

#include "TriangleMesh.hpp"

#include <cstddef>
#include <functional>
#include <vector>

namespace Slic3r {

enum class SurfaceFeatureMode {
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

} // namespace Slic3r

#endif
