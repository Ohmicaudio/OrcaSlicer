#include "AdaptiveManufacturingDebugArtifactWriter.hpp"

#include <fstream>
#include <exception>

namespace Slic3r {

AdaptiveManufacturingDebugArtifactWriteResult write_debug_artifact(
    const std::filesystem::path &path,
    const std::string &serialized_json)
{
    if (path.empty())
        return {false, "debug artifact output path is empty"};

    try {
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        if (!out)
            return {false, "failed to open debug artifact output path"};

        out.write(serialized_json.data(), static_cast<std::streamsize>(serialized_json.size()));
        if (!out)
            return {false, "failed to write debug artifact output"};

        out.close();
        if (!out)
            return {false, "failed to close debug artifact output"};
    } catch (const std::exception &err) {
        return {false, err.what()};
    }

    return {true, {}};
}

} // namespace Slic3r
