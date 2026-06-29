#ifndef slic3r_AdaptiveManufacturingDebugArtifactSerializer_hpp_
#define slic3r_AdaptiveManufacturingDebugArtifactSerializer_hpp_

#include "AdaptiveManufacturingDebugArtifact.hpp"

#include <string>

namespace Slic3r {

std::string serialize_adaptive_manufacturing_debug_artifact(const AdaptiveManufacturingDebugArtifact &artifact);

} // namespace Slic3r

#endif
