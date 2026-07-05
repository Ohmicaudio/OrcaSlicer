#include <catch2/catch.hpp>

#include "amp_debug_artifact_test_helpers.hpp"
#include "libslic3r/AdaptiveManufacturingPacketSidecar.hpp"

using namespace Slic3r;

namespace {

AdaptiveManufacturingDebugEntry make_packet_debug_entry(
    int layer_id,
    int region_id,
    const std::string &region_name,
    const std::string &recommended_tool_class,
    const std::string &fallback_tool_class,
    const std::string &selected_process_profile,
    double selected_layer_height_mm,
    const std::string &selected_line_width_class,
    bool local_z_future_required,
    const std::vector<std::string> &risk_flags)
{
    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = 0;
    entry.layer_id = layer_id;
    entry.region_id = region_id;
    entry.source_stage = AdaptiveManufacturingDebugSourceStage::OfflinePlanPacket;
    entry.region_name = region_name;
    entry.recommended_tool_class = recommended_tool_class;
    entry.fallback_tool_class = fallback_tool_class;
    entry.selected_process_profile = selected_process_profile;
    entry.selected_layer_height_mm = selected_layer_height_mm;
    entry.selected_line_width_class = selected_line_width_class;
    entry.cost_gate_passed = true;
    entry.cost_gate_reason = "cost gate passed for " + region_name;
    entry.fallback_reason = "fallback for " + region_name;
    entry.risk_flags = risk_flags;
    entry.local_z_future_required = local_z_future_required;
    entry.touchscreen_mixed_nozzle_blocked = true;
    return entry;
}

AdaptiveManufacturingDebugArtifact make_four_region_packet_artifact()
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;
    artifact.add_entry(make_packet_debug_entry(
        3, 3, "bulk_zone", "0.8", "0.6", "0.40 Standard @Snapmaker U1 (0.8 nozzle)", 0.40,
        "0.82-0.88", false, {"touchscreen_mixed_nozzle_blocked"}));
    artifact.add_entry(make_packet_debug_entry(
        0, 0, "micro_detail_zone", "0.2", "0.4", "0.06 Standard @Snapmaker U1 (0.2 nozzle)", 0.06,
        "0.22", true, {"local_z_future_required", "touchscreen_mixed_nozzle_blocked"}));
    artifact.add_entry(make_packet_debug_entry(
        2, 2, "structural_shell_zone", "0.6", "0.4", "0.24 Standard @Snapmaker U1 (0.6 nozzle)", 0.24,
        "0.62-0.66", false, {"touchscreen_mixed_nozzle_blocked"}));
    artifact.add_entry(make_packet_debug_entry(
        1, 1, "normal_visible_detail_zone", "0.4", "0.2", "0.16 Optimal @Snapmaker U1 (0.4 nozzle)", 0.16,
        "0.42-0.45", false, {"touchscreen_mixed_nozzle_blocked"}));
    return artifact;
}

} // namespace

TEST_CASE("AMP packet sidecar starts empty and supports deterministic insert", "[AdaptiveManufacturingPacketSidecar]")
{
    AdaptiveManufacturingPacketSidecar sidecar;
    const AdaptiveManufacturingPacketSidecarKey key {0, 1, 2, "region_b"};
    const AdaptiveManufacturingPacketSidecarKey earlier {0, 0, 1, "region_a"};

    CHECK(sidecar.empty());
    CHECK(sidecar.size() == 0);
    CHECK_FALSE(sidecar.contains(key));
    CHECK(sidecar.find(key) == nullptr);

    AdaptiveManufacturingPacketPlan plan;
    plan.region_name = "region_b";
    plan.recommended_tool_class = "0.6";
    sidecar.insert_or_assign(key, plan);

    AdaptiveManufacturingPacketPlan earlier_plan;
    earlier_plan.region_name = "region_a";
    earlier_plan.recommended_tool_class = "0.2";
    sidecar.insert_or_assign(earlier, earlier_plan);

    REQUIRE(sidecar.size() == 2);
    REQUIRE(sidecar.entries().size() == 2);
    CHECK(sidecar.entries()[0].first == earlier);
    CHECK(sidecar.entries()[1].first == key);

    REQUIRE(sidecar.find(key) != nullptr);
    CHECK(sidecar.find(key)->recommended_tool_class == "0.6");
    sidecar.clear();
    CHECK(sidecar.empty());
}

TEST_CASE("AMP packet sidecar converts four-region debug artifact deterministically", "[AdaptiveManufacturingPacketSidecar]")
{
    const AdaptiveManufacturingDebugArtifact artifact = make_four_region_packet_artifact();
    const AdaptiveManufacturingPacketSidecar sidecar = make_packet_sidecar_from_debug_artifact(artifact);

    REQUIRE(sidecar.size() == 4);
    REQUIRE(sidecar.entries().size() == 4);
    CHECK(sidecar.entries()[0].second.region_name == "micro_detail_zone");
    CHECK(sidecar.entries()[1].second.region_name == "normal_visible_detail_zone");
    CHECK(sidecar.entries()[2].second.region_name == "structural_shell_zone");
    CHECK(sidecar.entries()[3].second.region_name == "bulk_zone");

    const AdaptiveManufacturingPacketSidecarKey micro_key {0, 0, 0, "micro_detail_zone"};
    const AdaptiveManufacturingPacketPlan *micro = sidecar.find(micro_key);
    REQUIRE(micro != nullptr);
    CHECK(micro->recommended_tool_class == "0.2");
    CHECK(micro->fallback_tool_class == "0.4");
    CHECK(micro->selected_process_profile == "0.06 Standard @Snapmaker U1 (0.2 nozzle)");
    CHECK(micro->selected_layer_height_mm == Approx(0.06));
    CHECK(micro->selected_line_width_class == "0.22");
    CHECK(micro->cost_gate_passed);
    CHECK(micro->cost_gate_reason == "cost gate passed for micro_detail_zone");
    CHECK(micro->fallback_reason == "fallback for micro_detail_zone");
    REQUIRE(micro->risk_flags.size() == 2);
    CHECK(micro->risk_flags[0] == "local_z_future_required");
    CHECK(micro->risk_flags[1] == "touchscreen_mixed_nozzle_blocked");
    CHECK(micro->local_z_future_required);
    CHECK(micro->touchscreen_mixed_nozzle_blocked);

    const AdaptiveManufacturingPacketPlan *bulk = sidecar.find({0, 3, 3, "bulk_zone"});
    REQUIRE(bulk != nullptr);
    CHECK(bulk->recommended_tool_class == "0.8");
    CHECK(bulk->selected_process_profile == "0.40 Standard @Snapmaker U1 (0.8 nozzle)");

    const AdaptiveManufacturingPacketSidecar repeated = make_packet_sidecar_from_debug_artifact(artifact);
    CHECK(repeated.entries() == sidecar.entries());
}

TEST_CASE("AMP packet sidecar tolerates missing optional packet fields", "[AdaptiveManufacturingPacketSidecar]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = 7;
    entry.layer_id = 8;
    entry.region_id = 9;
    artifact.add_entry(entry);

    const AdaptiveManufacturingPacketSidecar sidecar = make_packet_sidecar_from_debug_artifact(artifact);
    REQUIRE(sidecar.size() == 1);
    const AdaptiveManufacturingPacketPlan *plan = sidecar.find({7, 8, 9, ""});
    REQUIRE(plan != nullptr);
    CHECK(plan->region_name.empty());
    CHECK(plan->recommended_tool_class.empty());
    CHECK(plan->selected_layer_height_mm == 0.0);
    CHECK_FALSE(plan->cost_gate_passed);
    CHECK_FALSE(plan->local_z_future_required);
    CHECK_FALSE(plan->touchscreen_mixed_nozzle_blocked);
}

TEST_CASE("AMP packet sidecar assigns stable synthetic ids when numeric ids are absent", "[AdaptiveManufacturingPacketSidecar]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    AdaptiveManufacturingDebugEntry first;
    first.object_id = -1;
    first.layer_id = -1;
    first.region_id = -1;
    first.region_name = "synthetic_first";
    first.recommended_tool_class = "0.4";
    artifact.add_entry(first);

    AdaptiveManufacturingDebugEntry second;
    second.object_id = -1;
    second.layer_id = -1;
    second.region_id = -1;
    second.region_name = "synthetic_second";
    second.recommended_tool_class = "0.8";
    artifact.add_entry(second);

    const AdaptiveManufacturingPacketSidecar sidecar = make_packet_sidecar_from_debug_artifact(artifact);
    REQUIRE(sidecar.size() == 2);
    CHECK(sidecar.entries()[0].first.object_id == 0);
    CHECK(sidecar.entries()[0].first.layer_id == 0);
    CHECK(sidecar.entries()[0].first.region_id == 0);
    CHECK(sidecar.entries()[0].first.region_name == "synthetic_first");
    CHECK(sidecar.entries()[1].first.object_id == 0);
    CHECK(sidecar.entries()[1].first.layer_id == 0);
    CHECK(sidecar.entries()[1].first.region_id == 1);
    CHECK(sidecar.entries()[1].first.region_name == "synthetic_second");
}

TEST_CASE("AMP golden packet debug artifact imports into packet sidecar", "[AdaptiveManufacturingPacketSidecar]")
{
    const AdaptiveManufacturingDebugArtifact artifact =
        import_debug_artifact_from_json_fixture("tests/libslic3r/data/amp_debug_artifact_offline_plan_packet_golden.json");
    const AdaptiveManufacturingPacketSidecar sidecar = make_packet_sidecar_from_debug_artifact(artifact);

    REQUIRE(sidecar.size() == 4);

    const AdaptiveManufacturingPacketPlan *micro = sidecar.find({0, 0, 0, "micro_detail_zone"});
    REQUIRE(micro != nullptr);
    CHECK(micro->recommended_tool_class == "0.2");
    CHECK(micro->fallback_tool_class == "0.4");
    CHECK(micro->selected_process_profile == "0.06 Standard @Snapmaker U1 (0.2 nozzle)");
    CHECK(micro->selected_layer_height_mm == Approx(0.06));
    CHECK(micro->local_z_future_required);
    CHECK(micro->touchscreen_mixed_nozzle_blocked);
    REQUIRE(micro->risk_flags.size() == 2);
    CHECK(micro->risk_flags[0] == "local_z_future_required");
    CHECK(micro->risk_flags[1] == "touchscreen_mixed_nozzle_blocked");

    const AdaptiveManufacturingPacketPlan *normal = sidecar.find({0, 1, 1, "normal_visible_detail_zone"});
    REQUIRE(normal != nullptr);
    CHECK(normal->recommended_tool_class == "0.4");
    CHECK(normal->selected_process_profile == "0.16 Optimal @Snapmaker U1 (0.4 nozzle)");

    const AdaptiveManufacturingPacketPlan *shell = sidecar.find({0, 2, 2, "structural_shell_zone"});
    REQUIRE(shell != nullptr);
    CHECK(shell->recommended_tool_class == "0.6");
    CHECK(shell->selected_process_profile == "0.24 Standard @Snapmaker U1 (0.6 nozzle)");

    const AdaptiveManufacturingPacketPlan *bulk = sidecar.find({0, 3, 3, "bulk_zone"});
    REQUIRE(bulk != nullptr);
    CHECK(bulk->recommended_tool_class == "0.8");
    CHECK(bulk->selected_process_profile == "0.40 Standard @Snapmaker U1 (0.8 nozzle)");

    const AdaptiveManufacturingPacketSidecar repeated = make_packet_sidecar_from_debug_artifact(artifact);
    CHECK(repeated.entries() == sidecar.entries());
}
