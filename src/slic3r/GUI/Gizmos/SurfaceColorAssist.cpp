#include "SurfaceColorAssist.hpp"

#include "slic3r/GUI/Jobs/BoostThreadWorker.hpp"
#include "slic3r/GUI/Jobs/PlaterWorker.hpp"
#include "slic3r/GUI/Jobs/Worker.hpp"

namespace Slic3r::GUI {

struct SurfaceColorAssist::State
{
    std::optional<SurfaceColorAssistKey> current_key;
    std::optional<SurfaceFeatureField> field;
    std::optional<SurfaceColorAssistKey> active_key;
    SurfaceColorAssistSettings settings;
    size_t generation { 0 };
    std::array<std::vector<size_t>, PreviewBandCount> preview_bands;
};

SurfaceColorAssist::SurfaceColorAssist(wxWindow *event_owner)
    : m_state(std::make_shared<State>())
    , m_worker(std::make_unique<PlaterWorker<BoostThreadWorker>>(event_owner, "surface_color_assist"))
{
}

SurfaceColorAssist::~SurfaceColorAssist()
{
    cancel();
    m_state.reset();
}

void SurfaceColorAssist::set_current_volume(const ModelVolume *volume)
{
    const std::optional<SurfaceColorAssistKey> key =
        volume == nullptr ? std::nullopt : std::optional<SurfaceColorAssistKey>(make_key(*volume));
    if (key && m_state->current_key && keys_match(*key, *m_state->current_key))
        return;

    cancel();
    m_state->current_key = key;
}

bool SurfaceColorAssist::analyze_current_volume()
{
    if (!m_state->current_key)
        return false;

    const SurfaceColorAssistKey key = *m_state->current_key;
    if (!key.mesh || key.triangle_count == 0)
        return false;

    ++m_state->generation;
    clear_cached_result(*m_state);

    const size_t generation = m_state->generation;
    const auto mesh = key.mesh;
    const SurfaceFeatureAnalysisOptions options {
        m_state->settings.analysis_radius_mm,
        m_state->settings.min_patch_area_mm2,
        SurfaceFeatureAnalysisOptions {}.smoothing_pass_limit
    };
    const auto result = std::make_shared<SurfaceFeatureField>();
    const std::weak_ptr<State> state = m_state;
    return replace_job(*m_worker,
        [mesh, options, result](Job::Ctl &ctl) {
            *result = analyze_surface_features(mesh->its, options, [&ctl] { return ctl.was_canceled(); });
        },
        [state, key, generation, result](bool canceled, std::exception_ptr &error) {
            const std::shared_ptr<State> locked_state = state.lock();
            if (!locked_state || canceled || error || generation != locked_state->generation)
                return;

            if (!locked_state->current_key ||
                !SurfaceColorAssist::keys_match(*locked_state->current_key, key) ||
                result->status != SurfaceFeatureAnalysisStatus::Complete)
                return;

            locked_state->field = std::move(*result);
            locked_state->active_key = key;
        });
}

void SurfaceColorAssist::cancel()
{
    if (!m_state)
        return;

    ++m_state->generation;
    clear_cached_result(*m_state);
    if (m_worker)
        m_worker->cancel_all();
}

void SurfaceColorAssist::clear()
{
    cancel();
}

SurfaceColorAssistKey SurfaceColorAssist::make_key(const ModelVolume &volume) const
{
    const auto mesh = volume.get_mesh_shared_ptr();
    return { mesh, volume.get_matrix(), mesh ? mesh->its.indices.size() / 3 : 0 };
}

bool SurfaceColorAssist::keys_match(const SurfaceColorAssistKey &lhs, const SurfaceColorAssistKey &rhs)
{
    return lhs.mesh == rhs.mesh &&
           lhs.triangle_count == rhs.triangle_count &&
           lhs.volume_transform.isApprox(rhs.volume_transform);
}

void SurfaceColorAssist::clear_cached_result(State &state)
{
    state.field.reset();
    state.active_key.reset();
    for (auto &band : state.preview_bands)
        band.clear();
}

const SurfaceColorAssistSettings& SurfaceColorAssist::settings() const
{
    return m_state->settings;
}

SurfaceColorAssistSettings& SurfaceColorAssist::settings()
{
    return m_state->settings;
}

const SurfaceFeatureField* SurfaceColorAssist::current_field(const ModelVolume &volume) const
{
    if (!m_state->field || !m_state->active_key ||
        !keys_match(*m_state->active_key, make_key(volume)))
        return nullptr;

    return &*m_state->field;
}

} // namespace Slic3r::GUI
