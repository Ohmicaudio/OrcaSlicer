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
