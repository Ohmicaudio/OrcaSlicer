#include "SurfaceColorAssist.hpp"

#include "slic3r/GUI/3DScene.hpp"
#include "slic3r/GUI/Camera.hpp"
#include "slic3r/GUI/GUI_App.hpp"
#include "slic3r/GUI/GLShader.hpp"
#include "slic3r/GUI/Jobs/BoostThreadWorker.hpp"
#include "slic3r/GUI/Jobs/PlaterWorker.hpp"
#include "slic3r/GUI/Plater.hpp"
#include "slic3r/GUI/Jobs/Worker.hpp"

#include <algorithm>
#include <array>
#include <cmath>

namespace Slic3r::GUI {

struct SurfaceColorAssist::State
{
    std::optional<SurfaceColorAssistKey> current_key;
    std::optional<SurfaceFeatureField> field;
    std::optional<SurfaceColorAssistKey> active_key;
    SurfaceColorAssistSettings settings;
    size_t generation { 0 };
    bool analyzing { false };
    std::array<GLModel, PreviewBandCount> preview_bands;
    std::optional<SurfaceColorAssistKey> preview_key;
    SurfaceFeatureMode preview_mode { SurfaceFeatureMode::Valleys };
    float preview_threshold { -1.0f };
    float preview_falloff { -1.0f };
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
    m_state->analyzing = true;

    const size_t generation = m_state->generation;
    const auto mesh = key.mesh;
    const SurfaceFeatureAnalysisOptions options {
        m_state->settings.analysis_radius_mm,
        m_state->settings.min_patch_area_mm2,
        SurfaceFeatureAnalysisOptions {}.smoothing_pass_limit
    };
    const auto result = std::make_shared<SurfaceFeatureField>();
    const std::weak_ptr<State> state = m_state;
    const bool started = replace_job(*m_worker,
        [mesh, options, result](Job::Ctl &ctl) {
            *result = analyze_surface_features(mesh->its, options, [&ctl] { return ctl.was_canceled(); });
        },
        [state, key, generation, result](bool canceled, std::exception_ptr &error) {
            const std::shared_ptr<State> locked_state = state.lock();
            if (!locked_state || generation != locked_state->generation)
                return;

            locked_state->analyzing = false;
            if (canceled || error)
                return;

            if (!locked_state->current_key ||
                !SurfaceColorAssist::keys_match(*locked_state->current_key, key) ||
                result->status != SurfaceFeatureAnalysisStatus::Complete)
                return;

            locked_state->field = std::move(*result);
            locked_state->active_key = key;
        });
    if (!started)
        m_state->analyzing = false;
    return started;
}

void SurfaceColorAssist::cancel()
{
    if (!m_state)
        return;

    ++m_state->generation;
    m_state->analyzing = false;
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
        band.reset();
    state.preview_key.reset();
    state.preview_threshold = -1.0f;
    state.preview_falloff = -1.0f;
}

const SurfaceColorAssistSettings& SurfaceColorAssist::settings() const
{
    return m_state->settings;
}

SurfaceColorAssistSettings& SurfaceColorAssist::settings()
{
    return m_state->settings;
}

bool SurfaceColorAssist::is_analyzing() const
{
    return m_state && m_state->analyzing;
}

void SurfaceColorAssist::render_preview(const ModelVolume &volume, const Transform3d &world_transform)
{
    if (!current_field(volume))
        return;

    rebuild_preview_bands(volume);
    GLShaderProgram *shader = wxGetApp().get_shader("gouraud_light");
    if (shader == nullptr)
        return;

    const Camera &camera = wxGetApp().plater()->get_camera();
    const Transform3d view_model_matrix = camera.get_view_matrix() * world_transform;
    const Matrix3d view_normal_matrix = camera.get_view_matrix().matrix().block(0, 0, 3, 3) *
        world_transform.matrix().block(0, 0, 3, 3).inverse().transpose();
    const bool mirrored = world_transform.matrix().determinant() < 0.0;

    shader->start_using();
    shader->set_uniform("view_model_matrix", view_model_matrix);
    shader->set_uniform("projection_matrix", camera.get_projection_matrix());
    shader->set_uniform("view_normal_matrix", view_normal_matrix);
    shader->set_uniform("emission_factor", 0.10f);
    if (mirrored)
        glsafe(::glFrontFace(GL_CW));
    for (GLModel &band : m_state->preview_bands)
        band.render();
    if (mirrored)
        glsafe(::glFrontFace(GL_CCW));
    shader->stop_using();
}

void SurfaceColorAssist::rebuild_preview_bands(const ModelVolume &volume)
{
    const SurfaceFeatureField *field = current_field(volume);
    if (!field || !m_state->active_key)
        return;

    const SurfaceColorAssistKey &key = *m_state->active_key;
    const SurfaceColorAssistSettings &settings = m_state->settings;
    if (m_state->preview_key && keys_match(*m_state->preview_key, key) &&
        m_state->preview_mode == settings.mode &&
        m_state->preview_threshold == settings.threshold &&
        m_state->preview_falloff == settings.preview_falloff)
        return;

    for (GLModel &band : m_state->preview_bands)
        band.reset();

    const indexed_triangle_set &its = key.mesh->its;
    const std::vector<float> &scores = settings.mode == SurfaceFeatureMode::Valleys ?
        field->valley_scores : field->ridge_scores;
    if (scores.size() != its.indices.size() / 3)
        return;

    std::array<GLModel::Geometry, PreviewBandCount> geometry;
    for (GLModel::Geometry &band : geometry)
        band.format = { GLModel::Geometry::EPrimitiveType::Triangles, GLModel::Geometry::EVertexLayout::P3N3 };

    const float denominator = std::max(2.0f * settings.preview_falloff, 0.001f);
    for (size_t triangle_idx = 0; triangle_idx < scores.size(); ++triangle_idx) {
        const float normalized = std::clamp((scores[triangle_idx] - (settings.threshold - settings.preview_falloff)) /
                                                denominator, 0.0f, 1.0f);
        if (normalized <= 0.0f)
            continue;
        const size_t band_idx = std::min<size_t>(PreviewBandCount - 1, size_t(normalized * PreviewBandCount));
        GLModel::Geometry &band = geometry[band_idx];
        const Vec3i &triangle = its.indices[triangle_idx];
        const Vec3f &a = its.vertices[triangle[0]];
        const Vec3f &b = its.vertices[triangle[1]];
        const Vec3f &c = its.vertices[triangle[2]];
        const Vec3f normal = (b - a).cross(c - a).normalized();
        const unsigned int base = static_cast<unsigned int>(band.vertices_count());
        band.add_vertex(a, normal);
        band.add_vertex(b, normal);
        band.add_vertex(c, normal);
        band.add_triangle(base, base + 1, base + 2);
    }

    const ColorRGBA start = settings.mode == SurfaceFeatureMode::Valleys ?
        ColorRGBA(0.02f, 0.65f, 0.62f, 0.20f) : ColorRGBA(0.55f, 0.70f, 0.84f, 0.18f);
    const ColorRGBA end = settings.mode == SurfaceFeatureMode::Valleys ?
        ColorRGBA(1.00f, 0.62f, 0.18f, 0.55f) : ColorRGBA(0.88f, 0.94f, 1.00f, 0.48f);
    for (size_t band_idx = 0; band_idx < PreviewBandCount; ++band_idx) {
        const float t = float(band_idx + 1) / float(PreviewBandCount);
        geometry[band_idx].color = ColorRGBA(start.r() + (end.r() - start.r()) * t,
                                              start.g() + (end.g() - start.g()) * t,
                                              start.b() + (end.b() - start.b()) * t,
                                              start.a() + (end.a() - start.a()) * t);
        if (!geometry[band_idx].is_empty())
            m_state->preview_bands[band_idx].init_from(std::move(geometry[band_idx]));
    }

    m_state->preview_key = key;
    m_state->preview_mode = settings.mode;
    m_state->preview_threshold = settings.threshold;
    m_state->preview_falloff = settings.preview_falloff;
}

const SurfaceFeatureField* SurfaceColorAssist::current_field(const ModelVolume &volume) const
{
    if (!m_state->field || !m_state->active_key ||
        !keys_match(*m_state->active_key, make_key(volume)))
        return nullptr;

    return &*m_state->field;
}

} // namespace Slic3r::GUI
