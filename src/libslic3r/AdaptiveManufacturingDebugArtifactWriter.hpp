#ifndef slic3r_AdaptiveManufacturingDebugArtifactWriter_hpp_
#define slic3r_AdaptiveManufacturingDebugArtifactWriter_hpp_

#include <filesystem>
#include <string>

namespace Slic3r {

struct AdaptiveManufacturingDebugArtifactWriteResult
{
    bool success = false;
    std::string error_message;
};

AdaptiveManufacturingDebugArtifactWriteResult write_debug_artifact(
    const std::filesystem::path &path,
    const std::string &serialized_json);

} // namespace Slic3r

#endif
