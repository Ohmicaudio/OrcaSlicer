#ifndef slic3r_AdaptiveManufacturingDebugArtifact_hpp_
#define slic3r_AdaptiveManufacturingDebugArtifact_hpp_

#include "AdaptiveManufacturingPlan.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace Slic3r {

enum class AdaptiveManufacturingDebugSourceStage {
    StockFallback,
    NoOpPlanner,
    FutureObservation
};

enum class AdaptiveManufacturingDebugGenerationMode {
    Disabled,
    EnabledNoop,
    EnabledReadonly
};

struct AdaptiveManufacturingDebugEntry
{
    int object_id = 0;
    int layer_id = 0;
    int region_id = 0;
    AdaptiveManufacturingReason plan_reason = AdaptiveManufacturingReason::StockFallback;
    double confidence = 0.0;
    bool toolchange_requested = false;
    bool bead_width_override_present = false;
    bool nozzle_override_present = false;
    AdaptiveManufacturingDebugSourceStage source_stage = AdaptiveManufacturingDebugSourceStage::StockFallback;
    std::vector<std::string> warnings;

    bool operator<(const AdaptiveManufacturingDebugEntry &rhs) const;
};

struct AdaptiveManufacturingDebugArtifact
{
    std::string schema_version = "0.1";
    std::optional<std::string> slicer_build_info;
    AdaptiveManufacturingDebugGenerationMode generation_mode = AdaptiveManufacturingDebugGenerationMode::Disabled;

    bool empty() const;
    std::size_t size() const;
    void clear();

    void add_entry(const AdaptiveManufacturingDebugEntry &entry);
    const std::vector<AdaptiveManufacturingDebugEntry> &entries() const;

    void add_warning(const std::string &warning);
    const std::vector<std::string> &warnings() const;

private:
    std::vector<AdaptiveManufacturingDebugEntry> m_entries;
    std::vector<std::string> m_warnings;
};

} // namespace Slic3r

#endif
