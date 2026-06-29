#ifndef slic3r_AdaptiveManufacturingObservationDebugMapper_hpp_
#define slic3r_AdaptiveManufacturingObservationDebugMapper_hpp_

#include "AdaptiveManufacturingDebugArtifact.hpp"
#include "AdaptiveManufacturingObservation.hpp"

namespace Slic3r {

void attach_observation_summary_to_debug_artifact(
    AdaptiveManufacturingDebugArtifact &artifact,
    const AdaptiveManufacturingObservationSummary &summary);

} // namespace Slic3r

#endif
