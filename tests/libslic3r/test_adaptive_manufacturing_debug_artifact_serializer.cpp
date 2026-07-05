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

TEST_CASE("Adaptive manufacturing debug artifact serializes offline advisory mode", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;

    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) ==
        "{\"schema_version\":\"0.1\",\"generation_mode\":\"offline_advisory\",\"warnings\":[],\"entries\":[]}");
}

TEST_CASE("Adaptive manufacturing debug artifact serializes packet-shaped tool fields", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;

    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = 0;
    entry.layer_id = 0;
    entry.region_id = 0;
    entry.region_name = "micro_detail_zone";
    entry.recommended_tool_class = "0.2";
    entry.fallback_tool_class = "0.4";
    entry.selected_process_profile = "0.06 Standard @Snapmaker U1 (0.2 nozzle)";
    entry.selected_layer_height_mm = 0.06;
    entry.selected_line_width_class = "0.22";
    entry.cost_gate_passed = true;
    entry.cost_gate_reason = "region-size gate passed";
    entry.fallback_reason = "fallback to 0.4";
    entry.risk_flags.push_back("local_z_future_required");
    entry.risk_flags.push_back("touchscreen_mixed_nozzle_blocked");
    entry.local_z_future_required = true;
    entry.touchscreen_mixed_nozzle_blocked = true;
    entry.source_stage = AdaptiveManufacturingDebugSourceStage::OfflinePlanPacket;
    artifact.add_entry(entry);

    const std::string expected =
        "{\"schema_version\":\"0.1\",\"generation_mode\":\"offline_advisory\",\"warnings\":[],\"entries\":["
        "{\"object_id\":0,\"layer_id\":0,\"region_id\":0,\"plan_reason\":\"StockFallback\",\"confidence\":0,\"toolchange_requested\":false,\"bead_width_override_present\":false,\"nozzle_override_present\":false,\"source_stage\":\"offline_plan_packet\","
        "\"region_name\":\"micro_detail_zone\",\"recommended_tool_class\":\"0.2\",\"fallback_tool_class\":\"0.4\",\"selected_process_profile\":\"0.06 Standard @Snapmaker U1 (0.2 nozzle)\",\"selected_layer_height_mm\":0.059999999999999998,\"selected_line_width_class\":\"0.22\",\"cost_gate_passed\":true,\"cost_gate_reason\":\"region-size gate passed\",\"fallback_reason\":\"fallback to 0.4\","
        "\"risk_flags\":[\"local_z_future_required\",\"touchscreen_mixed_nozzle_blocked\"],\"local_z_future_required\":true,\"touchscreen_mixed_nozzle_blocked\":true,\"warnings\":[]}"
        "]}";

    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) == expected);
}

TEST_CASE("Adaptive manufacturing debug artifact serializes four-region packet shape deterministically", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;

    AdaptiveManufacturingDebugEntry bulk;
    bulk.object_id = 0;
    bulk.layer_id = 3;
    bulk.region_id = 3;
    bulk.region_name = "bulk_zone";
    bulk.recommended_tool_class = "0.8";

    AdaptiveManufacturingDebugEntry micro;
    micro.object_id = 0;
    micro.layer_id = 0;
    micro.region_id = 0;
    micro.region_name = "micro_detail_zone";
    micro.recommended_tool_class = "0.2";

    AdaptiveManufacturingDebugEntry normal;
    normal.object_id = 0;
    normal.layer_id = 1;
    normal.region_id = 1;
    normal.region_name = "normal_visible_detail_zone";
    normal.recommended_tool_class = "0.4";

    AdaptiveManufacturingDebugEntry shell;
    shell.object_id = 0;
    shell.layer_id = 2;
    shell.region_id = 2;
    shell.region_name = "structural_shell_zone";
    shell.recommended_tool_class = "0.6";

    artifact.add_entry(bulk);
    artifact.add_entry(shell);
    artifact.add_entry(normal);
    artifact.add_entry(micro);

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);

    CHECK(json == serialize_adaptive_manufacturing_debug_artifact(artifact));
    CHECK(json.find("micro_detail_zone") < json.find("normal_visible_detail_zone"));
    CHECK(json.find("normal_visible_detail_zone") < json.find("structural_shell_zone"));
    CHECK(json.find("structural_shell_zone") < json.find("bulk_zone"));
    CHECK(json.find("\"recommended_tool_class\":\"0.2\"") != std::string::npos);
    CHECK(json.find("\"recommended_tool_class\":\"0.4\"") != std::string::npos);
    CHECK(json.find("\"recommended_tool_class\":\"0.6\"") != std::string::npos);
    CHECK(json.find("\"recommended_tool_class\":\"0.8\"") != std::string::npos);
}

TEST_CASE("Adaptive manufacturing debug artifact omits unset packet fields", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;

    AdaptiveManufacturingDebugEntry entry;
    artifact.add_entry(entry);

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);

    CHECK(json.find("region_name") == std::string::npos);
    CHECK(json.find("recommended_tool_class") == std::string::npos);
    CHECK(json.find("selected_process_profile") == std::string::npos);
    CHECK(json.find("cost_gate_passed") == std::string::npos);
    CHECK(json.find("local_z_future_required") == std::string::npos);
    CHECK(json.find("touchscreen_mixed_nozzle_blocked") == std::string::npos);
}

TEST_CASE("Adaptive manufacturing debug artifact packet risk flags preserve order and escaping", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;

    AdaptiveManufacturingDebugEntry entry;
    entry.risk_flags.push_back("first \"quoted\"");
    entry.risk_flags.push_back("second\\path");
    artifact.add_entry(entry);

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);

    CHECK(json.find("\"risk_flags\":[\"first \\\"quoted\\\"\",\"second\\\\path\"]") != std::string::npos);
}
