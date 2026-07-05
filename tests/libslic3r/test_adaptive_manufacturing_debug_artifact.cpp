#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingDebugArtifact.hpp"
#include "libslic3r/AdaptiveManufacturingPlan.hpp"

using namespace Slic3r;

TEST_CASE("Adaptive manufacturing debug artifact starts empty with stable schema", "[AdaptiveManufacturingDebugArtifact]")
{
    AdaptiveManufacturingDebugArtifact artifact;

    CHECK(artifact.empty());
    CHECK(artifact.size() == 0);
    CHECK(artifact.entries().empty());
    CHECK(artifact.warnings().empty());
    CHECK(artifact.schema_version == "0.1");
    CHECK_FALSE(artifact.slicer_build_info.has_value());

    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::EnabledNoop;
    CHECK(artifact.generation_mode == AdaptiveManufacturingDebugGenerationMode::EnabledNoop);

    artifact.slicer_build_info = "local-test-build";
    REQUIRE(artifact.slicer_build_info.has_value());
    CHECK(*artifact.slicer_build_info == "local-test-build");
}

TEST_CASE("Adaptive manufacturing debug artifact stores sorted no-op fallback entries", "[AdaptiveManufacturingDebugArtifact]")
{
    AdaptiveManufacturingDebugArtifact artifact;

    AdaptiveManufacturingDebugEntry later;
    later.object_id = 1;
    later.layer_id = 2;
    later.region_id = 3;
    later.plan_reason = AdaptiveManufacturingReason::StockFallback;
    later.source_stage = AdaptiveManufacturingDebugSourceStage::NoOpPlanner;

    AdaptiveManufacturingDebugEntry earlier;
    earlier.object_id = 1;
    earlier.layer_id = 1;
    earlier.region_id = 9;
    earlier.plan_reason = AdaptiveManufacturingReason::StockFallback;
    earlier.source_stage = AdaptiveManufacturingDebugSourceStage::StockFallback;
    earlier.warnings.push_back("stock fallback only");

    artifact.add_entry(later);
    artifact.add_entry(earlier);

    REQUIRE_FALSE(artifact.empty());
    REQUIRE(artifact.size() == 2);
    REQUIRE(artifact.entries().size() == 2);

    const AdaptiveManufacturingDebugEntry &first = artifact.entries().front();
    CHECK(first.object_id == 1);
    CHECK(first.layer_id == 1);
    CHECK(first.region_id == 9);
    CHECK(first.plan_reason == AdaptiveManufacturingReason::StockFallback);
    CHECK(first.confidence == 0.0);
    CHECK(first.toolchange_requested == false);
    CHECK(first.bead_width_override_present == false);
    CHECK(first.nozzle_override_present == false);
    CHECK(first.source_stage == AdaptiveManufacturingDebugSourceStage::StockFallback);
    REQUIRE(first.warnings.size() == 1);
    CHECK(first.warnings.front() == "stock fallback only");

    const AdaptiveManufacturingDebugEntry &second = artifact.entries().back();
    CHECK(second.object_id == 1);
    CHECK(second.layer_id == 2);
    CHECK(second.region_id == 3);
    CHECK(second.source_stage == AdaptiveManufacturingDebugSourceStage::NoOpPlanner);
}

TEST_CASE("Adaptive manufacturing debug artifact preserves warnings and clears entries", "[AdaptiveManufacturingDebugArtifact]")
{
    AdaptiveManufacturingDebugArtifact artifact;

    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = 2;
    entry.layer_id = 0;
    entry.region_id = 1;

    artifact.add_entry(entry);
    artifact.add_warning("developer-only artifact");

    CHECK(artifact.size() == 1);
    REQUIRE(artifact.warnings().size() == 1);
    CHECK(artifact.warnings().front() == "developer-only artifact");

    artifact.clear();
    CHECK(artifact.empty());
    CHECK(artifact.size() == 0);
    CHECK(artifact.entries().empty());
    REQUIRE(artifact.warnings().size() == 1);
    CHECK(artifact.warnings().front() == "developer-only artifact");
}

TEST_CASE("Adaptive manufacturing debug artifact stores packet-compatible advisory fields", "[AdaptiveManufacturingDebugArtifact]")
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

    REQUIRE(artifact.generation_mode == AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory);
    REQUIRE(artifact.entries().size() == 1);

    const AdaptiveManufacturingDebugEntry &stored = artifact.entries().front();
    REQUIRE(stored.region_name.has_value());
    CHECK(*stored.region_name == "micro_detail_zone");
    REQUIRE(stored.recommended_tool_class.has_value());
    CHECK(*stored.recommended_tool_class == "0.2");
    REQUIRE(stored.fallback_tool_class.has_value());
    CHECK(*stored.fallback_tool_class == "0.4");
    REQUIRE(stored.selected_process_profile.has_value());
    CHECK(*stored.selected_process_profile == "0.06 Standard @Snapmaker U1 (0.2 nozzle)");
    REQUIRE(stored.selected_layer_height_mm.has_value());
    CHECK(*stored.selected_layer_height_mm == 0.06);
    REQUIRE(stored.selected_line_width_class.has_value());
    CHECK(*stored.selected_line_width_class == "0.22");
    REQUIRE(stored.cost_gate_passed.has_value());
    CHECK(*stored.cost_gate_passed);
    REQUIRE(stored.cost_gate_reason.has_value());
    CHECK(*stored.cost_gate_reason == "region-size gate passed");
    REQUIRE(stored.fallback_reason.has_value());
    CHECK(*stored.fallback_reason == "fallback to 0.4");
    CHECK(stored.risk_flags.size() == 2);
    REQUIRE(stored.local_z_future_required.has_value());
    CHECK(*stored.local_z_future_required);
    REQUIRE(stored.touchscreen_mixed_nozzle_blocked.has_value());
    CHECK(*stored.touchscreen_mixed_nozzle_blocked);
    CHECK(stored.source_stage == AdaptiveManufacturingDebugSourceStage::OfflinePlanPacket);
}
