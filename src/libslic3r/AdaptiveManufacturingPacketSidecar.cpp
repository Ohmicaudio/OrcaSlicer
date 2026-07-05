#include "AdaptiveManufacturingPacketSidecar.hpp"

#include <tuple>

namespace Slic3r {
namespace {

std::string optional_string_or_empty(const std::optional<std::string> &value)
{
    return value.has_value() ? *value : std::string();
}

double optional_double_or_zero(const std::optional<double> &value)
{
    return value.has_value() ? *value : 0.0;
}

bool optional_bool_or_false(const std::optional<bool> &value)
{
    return value.has_value() ? *value : false;
}

AdaptiveManufacturingPacketPlan packet_plan_from_debug_entry(const AdaptiveManufacturingDebugEntry &entry)
{
    AdaptiveManufacturingPacketPlan plan;
    plan.region_name = optional_string_or_empty(entry.region_name);
    plan.recommended_tool_class = optional_string_or_empty(entry.recommended_tool_class);
    plan.fallback_tool_class = optional_string_or_empty(entry.fallback_tool_class);
    plan.selected_process_profile = optional_string_or_empty(entry.selected_process_profile);
    plan.selected_layer_height_mm = optional_double_or_zero(entry.selected_layer_height_mm);
    plan.selected_line_width_class = optional_string_or_empty(entry.selected_line_width_class);
    plan.cost_gate_passed = optional_bool_or_false(entry.cost_gate_passed);
    plan.cost_gate_reason = optional_string_or_empty(entry.cost_gate_reason);
    plan.fallback_reason = optional_string_or_empty(entry.fallback_reason);
    plan.risk_flags = entry.risk_flags;
    plan.local_z_future_required = optional_bool_or_false(entry.local_z_future_required);
    plan.touchscreen_mixed_nozzle_blocked = optional_bool_or_false(entry.touchscreen_mixed_nozzle_blocked);
    return plan;
}

bool has_numeric_key(const AdaptiveManufacturingDebugEntry &entry)
{
    return entry.object_id >= 0 && entry.layer_id >= 0 && entry.region_id >= 0;
}

AdaptiveManufacturingPacketSidecarKey packet_key_from_debug_entry(
    const AdaptiveManufacturingDebugEntry &entry,
    int synthetic_region_id)
{
    AdaptiveManufacturingPacketSidecarKey key;
    key.region_name = optional_string_or_empty(entry.region_name);
    if (has_numeric_key(entry)) {
        key.object_id = entry.object_id;
        key.layer_id = entry.layer_id;
        key.region_id = entry.region_id;
    } else {
        key.object_id = 0;
        key.layer_id = 0;
        key.region_id = synthetic_region_id;
    }
    return key;
}

} // namespace

bool AdaptiveManufacturingPacketSidecarKey::operator<(const AdaptiveManufacturingPacketSidecarKey &rhs) const
{
    return std::tie(this->object_id, this->layer_id, this->region_id, this->region_name)
         < std::tie(rhs.object_id, rhs.layer_id, rhs.region_id, rhs.region_name);
}

bool AdaptiveManufacturingPacketSidecarKey::operator==(const AdaptiveManufacturingPacketSidecarKey &rhs) const
{
    return this->object_id == rhs.object_id
        && this->layer_id == rhs.layer_id
        && this->region_id == rhs.region_id
        && this->region_name == rhs.region_name;
}

bool AdaptiveManufacturingPacketPlan::operator==(const AdaptiveManufacturingPacketPlan &rhs) const
{
    return this->region_name == rhs.region_name
        && this->recommended_tool_class == rhs.recommended_tool_class
        && this->fallback_tool_class == rhs.fallback_tool_class
        && this->selected_process_profile == rhs.selected_process_profile
        && this->selected_layer_height_mm == rhs.selected_layer_height_mm
        && this->selected_line_width_class == rhs.selected_line_width_class
        && this->cost_gate_passed == rhs.cost_gate_passed
        && this->cost_gate_reason == rhs.cost_gate_reason
        && this->fallback_reason == rhs.fallback_reason
        && this->risk_flags == rhs.risk_flags
        && this->local_z_future_required == rhs.local_z_future_required
        && this->touchscreen_mixed_nozzle_blocked == rhs.touchscreen_mixed_nozzle_blocked;
}

bool AdaptiveManufacturingPacketSidecar::empty() const
{
    return m_plans.empty();
}

std::size_t AdaptiveManufacturingPacketSidecar::size() const
{
    return m_plans.size();
}

void AdaptiveManufacturingPacketSidecar::clear()
{
    m_plans.clear();
}

void AdaptiveManufacturingPacketSidecar::insert_or_assign(
    const AdaptiveManufacturingPacketSidecarKey &key,
    const AdaptiveManufacturingPacketPlan &plan)
{
    m_plans[key] = plan;
}

const AdaptiveManufacturingPacketPlan *AdaptiveManufacturingPacketSidecar::find(
    const AdaptiveManufacturingPacketSidecarKey &key) const
{
    const auto it = m_plans.find(key);
    return it == m_plans.end() ? nullptr : &it->second;
}

bool AdaptiveManufacturingPacketSidecar::contains(const AdaptiveManufacturingPacketSidecarKey &key) const
{
    return this->find(key) != nullptr;
}

std::vector<AdaptiveManufacturingPacketSidecarEntry> AdaptiveManufacturingPacketSidecar::entries() const
{
    return {m_plans.begin(), m_plans.end()};
}

AdaptiveManufacturingPacketSidecar make_packet_sidecar_from_debug_artifact(
    const AdaptiveManufacturingDebugArtifact &artifact)
{
    AdaptiveManufacturingPacketSidecar sidecar;
    int synthetic_region_id = 0;
    for (const AdaptiveManufacturingDebugEntry &entry : artifact.entries()) {
        const AdaptiveManufacturingPacketSidecarKey key =
            packet_key_from_debug_entry(entry, synthetic_region_id);
        sidecar.insert_or_assign(key, packet_plan_from_debug_entry(entry));
        ++synthetic_region_id;
    }
    return sidecar;
}

} // namespace Slic3r
