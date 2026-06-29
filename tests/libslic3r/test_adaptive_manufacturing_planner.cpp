#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingPlanner.hpp"

using namespace Slic3r;

TEST_CASE("Adaptive manufacturing planner facade returns stock fallback", "[AdaptiveManufacturingPlanner]")
{
    const AdaptiveManufacturingPlanner planner;
    const AdaptiveManufacturingPlan first = planner.plan_stock_fallback();
    const AdaptiveManufacturingPlan second = planner.plan_stock_fallback();

    REQUIRE(first == second);
    REQUIRE(first.regions.size() == 1);

    const AdaptiveRegionPlan &region = first.regions.front();
    CHECK(region.reason == AdaptiveManufacturingReason::StockFallback);
    CHECK(region.requires_toolchange == false);
    CHECK(region.bead_width_override == 0.0);
    CHECK(region.nozzle_diameter_override == 0.0);
}
