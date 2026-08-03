#ifndef slic3r_GUI_SurfaceColorAssist_hpp_
#define slic3r_GUI_SurfaceColorAssist_hpp_

#include "libslic3r/Model.hpp"
#include "libslic3r/SurfaceFeatureAnalysis.hpp"
#include "slic3r/GUI/GLModel.hpp"

#include <array>
#include <cstddef>
#include <optional>
#include <memory>
#include <vector>

class wxWindow;

namespace Slic3r::GUI {

class Worker;

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

    explicit SurfaceColorAssist(wxWindow *event_owner);
    ~SurfaceColorAssist();

    SurfaceColorAssist(const SurfaceColorAssist&) = delete;
    SurfaceColorAssist& operator=(const SurfaceColorAssist&) = delete;

    void set_current_volume(const ModelVolume *volume);
    bool analyze_current_volume();
    void cancel();
    void clear();
    bool is_analyzing() const;

    // Draws only transient score geometry. This never touches color-paint data.
    void render_preview(const ModelVolume &volume);

    const SurfaceColorAssistSettings& settings() const;
    SurfaceColorAssistSettings&       settings();
    const SurfaceFeatureField*        current_field(const ModelVolume &volume) const;

private:
    struct State;

    SurfaceColorAssistKey make_key(const ModelVolume &volume) const;
    static bool keys_match(const SurfaceColorAssistKey &lhs, const SurfaceColorAssistKey &rhs);
    static void clear_cached_result(State &state);
    void rebuild_preview_bands(const ModelVolume &volume);

    std::shared_ptr<State> m_state;
    std::unique_ptr<Worker> m_worker;
};

} // namespace Slic3r::GUI

#endif
