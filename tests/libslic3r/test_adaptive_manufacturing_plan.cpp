#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingPlan.hpp"

using namespace Slic3r;

TEST_CASE("Adaptive manufacturing stock fallback is conservative and deterministic", "[AdaptiveManufacturingPlan]")
{
    const AdaptiveManufacturingPlan first = make_stock_fallback_plan();
    const AdaptiveManufacturingPlan second = make_stock_fallback_plan();

    REQUIRE(first == second);
    REQUIRE(first.regions.size() == 1);

    const AdaptiveRegionPlan &region = first.regions.front();
    CHECK(region.reason == AdaptiveManufacturingReason::StockFallback);
    CHECK(region.score.confidence == 0.0);
    CHECK(region.requires_toolchange == false);
    CHECK(region.bead_width_override == 0.0);
    CHECK(region.nozzle_diameter_override == 0.0);
}
