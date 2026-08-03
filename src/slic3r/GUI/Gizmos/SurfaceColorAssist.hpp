#ifndef slic3r_GUI_SurfaceColorAssist_hpp_
#define slic3r_GUI_SurfaceColorAssist_hpp_

#include "libslic3r/Model.hpp"
#include "libslic3r/SurfaceFeatureAnalysis.hpp"

#include <array>
#include <cstddef>
#include <optional>
#include <vector>

namespace Slic3r::GUI {

struct SurfaceColorAssistKey
{
    std::shared_ptr<const TriangleMesh> mesh;
    Transform3d                         volume_transform;
    size_t                              triangle_count { 0 };
};

struct SurfaceColorAssistSettings
{
    SurfaceFeatureMode  mode { SurfaceFeatureMode::Valleys };
    float               threshold { 0.50f };
    float               preview_falloff { 0.15f };
    float               analysis_radius_mm { 1.0f };
    float               min_patch_area_mm2 { 0.25f };
    std::optional<size_t> target_filament;
};

// GUI-only asynchronous state for the future color-painting assistant. It owns
// analysis results but deliberately has no paint, model-mutation, or persistence API.
class SurfaceColorAssist
{
public:
    static constexpr size_t PreviewBandCount = 8;

    void set_current_volume(const ModelVolume *volume);
    bool analyze_current_volume();
    void cancel();
    void clear();

    const SurfaceColorAssistSettings& settings() const { return m_settings; }
    SurfaceColorAssistSettings&       settings() { return m_settings; }
    const std::optional<SurfaceFeatureField>& field() const { return m_field; }
    const std::optional<SurfaceColorAssistKey>& active_key() const { return m_active_key; }

private:
    SurfaceColorAssistKey make_key(const ModelVolume &volume) const;
    bool matches_current_volume(const SurfaceColorAssistKey &key) const;
    void adopt_completed_field(SurfaceFeatureField field);

    const ModelVolume *m_current_volume { nullptr };
    std::optional<SurfaceFeatureField> m_field;
    std::optional<SurfaceColorAssistKey> m_active_key;
    SurfaceColorAssistSettings m_settings;
    size_t m_generation { 0 };
    std::array<std::vector<size_t>, PreviewBandCount> m_preview_bands;
};

} // namespace Slic3r::GUI

#endif
