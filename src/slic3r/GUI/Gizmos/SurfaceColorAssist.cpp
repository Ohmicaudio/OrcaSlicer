#include "SurfaceColorAssist.hpp"

#include "slic3r/GUI/GUI_App.hpp"
#include "slic3r/GUI/Jobs/Worker.hpp"
#include "slic3r/GUI/Plater.hpp"

namespace Slic3r::GUI {

void SurfaceColorAssist::set_current_volume(const ModelVolume *volume)
{
    if (m_current_volume == volume)
        return;

    cancel();
    m_current_volume = volume;
}

bool SurfaceColorAssist::analyze_current_volume()
{
    if (m_current_volume == nullptr || wxGetApp().plater() == nullptr)
        return false;

    const SurfaceColorAssistKey key = make_key(*m_current_volume);
    if (!key.mesh || key.triangle_count == 0)
        return false;

    ++m_generation;
    m_field.reset();
    m_active_key.reset();
    for (auto &band : m_preview_bands)
        band.clear();

    const size_t generation = m_generation;
    const auto mesh = key.mesh;
    const SurfaceFeatureAnalysisOptions options {
        m_settings.analysis_radius_mm,
        m_settings.min_patch_area_mm2,
        SurfaceFeatureAnalysisOptions {}.smoothing_pass_limit
    };
    const auto result = std::make_shared<SurfaceFeatureField>();
    auto &worker = wxGetApp().plater()->get_ui_job_worker();
    return replace_job(worker,
        [mesh, options, result](Job::Ctl &ctl) {
            *result = analyze_surface_features(mesh->its, options, [&ctl] { return ctl.was_canceled(); });
        },
        [this, key, generation, result](bool canceled, std::exception_ptr &error) {
            if (canceled || error || generation != m_generation || !matches_current_volume(key))
                return;
            adopt_completed_field(std::move(*result));
        });
}

void SurfaceColorAssist::cancel()
{
    ++m_generation;
    m_field.reset();
    m_active_key.reset();
    for (auto &band : m_preview_bands)
        band.clear();

    if (wxGetApp().plater() != nullptr)
        wxGetApp().plater()->get_ui_job_worker().cancel_all();
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

bool SurfaceColorAssist::matches_current_volume(const SurfaceColorAssistKey &key) const
{
    if (m_current_volume == nullptr)
        return false;

    const SurfaceColorAssistKey current = make_key(*m_current_volume);
    return current.mesh == key.mesh &&
           current.triangle_count == key.triangle_count &&
           current.volume_transform.isApprox(key.volume_transform);
}

void SurfaceColorAssist::adopt_completed_field(SurfaceFeatureField field)
{
    if (field.status != SurfaceFeatureAnalysisStatus::Complete)
        return;

    m_field = std::move(field);
    m_active_key = make_key(*m_current_volume);
}

} // namespace Slic3r::GUI
