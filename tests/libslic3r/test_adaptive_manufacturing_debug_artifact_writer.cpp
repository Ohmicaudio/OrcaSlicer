#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingDebugArtifactSerializer.hpp"
#include "libslic3r/AdaptiveManufacturingDebugArtifactWriter.hpp"

#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

using namespace Slic3r;

namespace {

std::filesystem::path amp_writer_test_dir()
{
    const std::filesystem::path dir = std::filesystem::temp_directory_path() / "amp_debug_artifact_writer_tests";
    std::filesystem::create_directories(dir);
    return dir;
}

std::string read_file(const std::filesystem::path &path)
{
    std::ifstream in(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

} // namespace

TEST_CASE("Adaptive manufacturing debug artifact writer writes exact serialized JSON", "[AdaptiveManufacturingDebugArtifactWriter]")
{
    const std::filesystem::path path = amp_writer_test_dir() / "exact.json";
    const std::string serialized_json = "{\"schema_version\":\"0.1\",\"warnings\":[],\"entries\":[]}";

    const AdaptiveManufacturingDebugArtifactWriteResult result = write_debug_artifact(path, serialized_json);

    CHECK(result.success);
    CHECK(result.error_message.empty());
    CHECK(read_file(path) == serialized_json);
}

TEST_CASE("Adaptive manufacturing debug artifact writer overwrites deterministically", "[AdaptiveManufacturingDebugArtifactWriter]")
{
    const std::filesystem::path path = amp_writer_test_dir() / "overwrite.json";
    const std::string first_json = "{\"first\":true}";
    const std::string second_json = "{\"second\":false}";

    REQUIRE(write_debug_artifact(path, first_json).success);
    CHECK(read_file(path) == first_json);

    REQUIRE(write_debug_artifact(path, second_json).success);
    CHECK(read_file(path) == second_json);

    REQUIRE(write_debug_artifact(path, second_json).success);
    CHECK(read_file(path) == second_json);
}

TEST_CASE("Adaptive manufacturing debug artifact writer fails cleanly for missing parent path", "[AdaptiveManufacturingDebugArtifactWriter]")
{
    const std::filesystem::path missing_dir = amp_writer_test_dir() / "missing-parent";
    std::filesystem::remove_all(missing_dir);
    const std::filesystem::path path = missing_dir / "artifact.json";

    const AdaptiveManufacturingDebugArtifactWriteResult result = write_debug_artifact(path, "{}");

    CHECK_FALSE(result.success);
    CHECK_FALSE(result.error_message.empty());
    CHECK_FALSE(std::filesystem::exists(path));
}

TEST_CASE("Adaptive manufacturing debug artifact writer preserves input string and serializer output", "[AdaptiveManufacturingDebugArtifactWriter]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::EnabledNoop;
    artifact.add_warning("writer test");

    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = 2;
    entry.layer_id = 3;
    entry.region_id = 4;
    entry.source_stage = AdaptiveManufacturingDebugSourceStage::NoOpPlanner;
    artifact.add_entry(entry);

    const std::string serialized_json = serialize_adaptive_manufacturing_debug_artifact(artifact);
    const std::string original_json = serialized_json;
    const std::filesystem::path path = amp_writer_test_dir() / "serializer-output.json";

    const AdaptiveManufacturingDebugArtifactWriteResult result = write_debug_artifact(path, serialized_json);

    CHECK(result.success);
    CHECK(serialized_json == original_json);
    CHECK(read_file(path) == serialized_json);
    CHECK(read_file(path).find("timestamp") == std::string::npos);
}
