#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingSidecar.hpp"

using namespace Slic3r;

TEST_CASE("Adaptive manufacturing sidecar stores stock fallback plans by key", "[AdaptiveManufacturingSidecar]")
{
    AdaptiveManufacturingSidecar sidecar;
    const AdaptiveManufacturingSidecarKey key {1, 2, 3};
    const AdaptiveManufacturingSidecarKey missing_key {1, 2, 4};

    CHECK(sidecar.empty());
    CHECK(sidecar.size() == 0);
    CHECK_FALSE(sidecar.contains(key));
    CHECK(sidecar.find(key) == nullptr);

    sidecar.insert_or_assign(key, make_stock_fallback_plan());

    CHECK_FALSE(sidecar.empty());
    CHECK(sidecar.size() == 1);
    CHECK(sidecar.contains(key));
    CHECK_FALSE(sidecar.contains(missing_key));
    CHECK(sidecar.find(missing_key) == nullptr);

    const AdaptiveManufacturingPlan *stored = sidecar.find(key);
    REQUIRE(stored != nullptr);
    REQUIRE(stored->regions.size() == 1);

    const AdaptiveRegionPlan &region = stored->regions.front();
    CHECK(region.reason == AdaptiveManufacturingReason::StockFallback);
    CHECK(region.score.confidence == 0.0);
    CHECK(region.requires_toolchange == false);
    CHECK(region.bead_width_override == 0.0);
    CHECK(region.nozzle_diameter_override == 0.0);
}

TEST_CASE("Adaptive manufacturing sidecar clear and repeated insert are deterministic", "[AdaptiveManufacturingSidecar]")
{
    AdaptiveManufacturingSidecar sidecar;
    const AdaptiveManufacturingSidecarKey key {4, 5, 6};

    sidecar.insert_or_assign(key, make_stock_fallback_plan());
    const AdaptiveManufacturingPlan *first = sidecar.find(key);
    REQUIRE(first != nullptr);
    const AdaptiveManufacturingPlan first_copy = *first;

    sidecar.insert_or_assign(key, make_stock_fallback_plan());
    const AdaptiveManufacturingPlan *second = sidecar.find(key);
    REQUIRE(second != nullptr);
    CHECK(first_copy == *second);
    CHECK(sidecar.size() == 1);

    sidecar.clear();
    CHECK(sidecar.empty());
    CHECK(sidecar.size() == 0);
    CHECK_FALSE(sidecar.contains(key));
    CHECK(sidecar.find(key) == nullptr);
}
