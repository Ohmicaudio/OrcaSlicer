#include "AdaptiveManufacturingObservationDebugMapper.hpp"

namespace Slic3r {
namespace {

const char *to_debug_string(AdaptiveManufacturingObservationRegionCategory category)
{
    switch (category) {
    case AdaptiveManufacturingObservationRegionCategory::Unknown: return "unknown";
    case AdaptiveManufacturingObservationRegionCategory::Perimeter: return "perimeter";
    case AdaptiveManufacturingObservationRegionCategory::Infill: return "infill";
    case AdaptiveManufacturingObservationRegionCategory::Support: return "support";
    }
    return "unknown";
}

} // namespace

void attach_observation_summary_to_debug_artifact(
    AdaptiveManufacturingDebugArtifact &artifact,
    const AdaptiveManufacturingObservationSummary &summary)
{
    AdaptiveManufacturingDebugObservationSummary debug_summary;

    for (const std::string &warning : summary.warnings())
        debug_summary.add_warning(warning);

    for (const AdaptiveManufacturingObservationEntry &entry : summary.entries()) {
        AdaptiveManufacturingDebugObservationEntry debug_entry;
        debug_entry.object_id = entry.object_id;
        debug_entry.layer_id = entry.layer_id;
        debug_entry.region_id = entry.region_id;
        debug_entry.region_category = to_debug_string(entry.region_category);
        debug_entry.observed_item_count = entry.observed_item_count;
        debug_entry.warning_count = entry.warning_count;
        debug_summary.add_entry(debug_entry);
    }

    artifact.observation_summary = debug_summary;
}

} // namespace Slic3r
