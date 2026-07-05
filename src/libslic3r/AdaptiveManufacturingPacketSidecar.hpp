#ifndef slic3r_AdaptiveManufacturingPacketSidecar_hpp_
#define slic3r_AdaptiveManufacturingPacketSidecar_hpp_

#include "AdaptiveManufacturingDebugArtifact.hpp"

#include <cstddef>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace Slic3r {

struct AdaptiveManufacturingPacketSidecarKey
{
    int object_id = 0;
    int layer_id = 0;
    int region_id = 0;
    std::string region_name;

    bool operator<(const AdaptiveManufacturingPacketSidecarKey &rhs) const;
    bool operator==(const AdaptiveManufacturingPacketSidecarKey &rhs) const;
};

struct AdaptiveManufacturingPacketPlan
{
    std::string region_name;
    std::string recommended_tool_class;
    std::string fallback_tool_class;
    std::string selected_process_profile;
    double selected_layer_height_mm = 0.0;
    std::string selected_line_width_class;
    bool cost_gate_passed = false;
    std::string cost_gate_reason;
    std::string fallback_reason;
    std::vector<std::string> risk_flags;
    bool local_z_future_required = false;
    bool touchscreen_mixed_nozzle_blocked = false;

    bool operator==(const AdaptiveManufacturingPacketPlan &rhs) const;
};

using AdaptiveManufacturingPacketSidecarEntry =
    std::pair<AdaptiveManufacturingPacketSidecarKey, AdaptiveManufacturingPacketPlan>;

class AdaptiveManufacturingPacketSidecar
{
public:
    bool empty() const;
    std::size_t size() const;
    void clear();

    void insert_or_assign(const AdaptiveManufacturingPacketSidecarKey &key, const AdaptiveManufacturingPacketPlan &plan);
    const AdaptiveManufacturingPacketPlan *find(const AdaptiveManufacturingPacketSidecarKey &key) const;
    bool contains(const AdaptiveManufacturingPacketSidecarKey &key) const;
    std::vector<AdaptiveManufacturingPacketSidecarEntry> entries() const;

private:
    std::map<AdaptiveManufacturingPacketSidecarKey, AdaptiveManufacturingPacketPlan> m_plans;
};

AdaptiveManufacturingPacketSidecar make_packet_sidecar_from_debug_artifact(
    const AdaptiveManufacturingDebugArtifact &artifact);

} // namespace Slic3r

#endif
