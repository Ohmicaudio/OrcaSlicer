#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingDebugArtifactSerializer.hpp"

using namespace Slic3r;

TEST_CASE("Adaptive manufacturing debug artifact serializes empty artifact deterministically", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);

    CHECK(json == "{\"schema_version\":\"0.1\",\"generation_mode\":\"disabled\",\"warnings\":[],\"entries\":[]}");
}

TEST_CASE("Adaptive manufacturing debug artifact serializes optional build info only when set", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact).find("slicer_build_info") == std::string::npos);

    artifact.slicer_build_info = "amp-test-build";
    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) ==
        "{\"schema_version\":\"0.1\",\"slicer_build_info\":\"amp-test-build\",\"generation_mode\":\"disabled\",\"warnings\":[],\"entries\":[]}");
}

TEST_CASE("Adaptive manufacturing debug artifact serializes sorted stock fallback entries", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::EnabledNoop;

    AdaptiveManufacturingDebugEntry later;
    later.object_id = 1;
    later.layer_id = 2;
    later.region_id = 3;
    later.source_stage = AdaptiveManufacturingDebugSourceStage::NoOpPlanner;

    AdaptiveManufacturingDebugEntry earlier;
    earlier.object_id = 1;
    earlier.layer_id = 1;
    earlier.region_id = 9;
    earlier.source_stage = AdaptiveManufacturingDebugSourceStage::StockFallback;

    artifact.add_entry(later);
    artifact.add_entry(earlier);

    const std::string expected =
        "{\"schema_version\":\"0.1\",\"generation_mode\":\"enabled_noop\",\"warnings\":[],\"entries\":["
        "{\"object_id\":1,\"layer_id\":1,\"region_id\":9,\"plan_reason\":\"StockFallback\",\"confidence\":0,\"toolchange_requested\":false,\"bead_width_override_present\":false,\"nozzle_override_present\":false,\"source_stage\":\"stock_fallback\",\"warnings\":[]},"
        "{\"object_id\":1,\"layer_id\":2,\"region_id\":3,\"plan_reason\":\"StockFallback\",\"confidence\":0,\"toolchange_requested\":false,\"bead_width_override_present\":false,\"nozzle_override_present\":false,\"source_stage\":\"no_op_planner\",\"warnings\":[]}"
        "]}";

    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) == expected);
}

TEST_CASE("Adaptive manufacturing debug artifact escapes warning strings", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::EnabledReadonly;
    artifact.add_warning("quoted \"warning\"");
    artifact.add_warning("slash\\newline\n");

    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = 4;
    entry.layer_id = 5;
    entry.region_id = 6;
    entry.source_stage = AdaptiveManufacturingDebugSourceStage::FutureObservation;
    entry.warnings.push_back("entry\twarning");
    artifact.add_entry(entry);

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);

    CHECK(json.find("\"generation_mode\":\"enabled_readonly\"") != std::string::npos);
    CHECK(json.find("\"warnings\":[\"quoted \\\"warning\\\"\",\"slash\\\\newline\\n\"]") != std::string::npos);
    CHECK(json.find("\"source_stage\":\"future_observation\"") != std::string::npos);
    CHECK(json.find("\"warnings\":[\"entry\\twarning\"]") != std::string::npos);
}

TEST_CASE("Adaptive manufacturing debug artifact serialization is repeatable", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::EnabledNoop;
    artifact.add_warning("developer-only");

    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = 7;
    entry.layer_id = 8;
    entry.region_id = 9;
    artifact.add_entry(entry);

    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) == serialize_adaptive_manufacturing_debug_artifact(artifact));
}
