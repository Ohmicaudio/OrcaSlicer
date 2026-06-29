#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingObservation.hpp"

using namespace Slic3r;

TEST_CASE("Adaptive manufacturing observation summary starts empty", "[AdaptiveManufacturingObservation]")
{
    AdaptiveManufacturingObservationSummary summary;

    CHECK(summary.empty());
    CHECK(summary.size() == 0);
    CHECK(summary.entries().empty());
    CHECK(summary.warnings().empty());
}

TEST_CASE("Adaptive manufacturing observation summary stores sorted entries", "[AdaptiveManufacturingObservation]")
{
    AdaptiveManufacturingObservationSummary summary;

    AdaptiveManufacturingObservationEntry later;
    later.object_id = 2;
    later.layer_id = 3;
    later.region_id = 4;
    later.region_category = AdaptiveManufacturingObservationRegionCategory::Infill;
    later.observed_item_count = 12;
    later.warning_count = 1;

    AdaptiveManufacturingObservationEntry earlier;
    earlier.object_id = 1;
    earlier.layer_id = 9;
    earlier.region_id = 0;
    earlier.region_category = AdaptiveManufacturingObservationRegionCategory::Perimeter;
    earlier.observed_item_count = 3;

    AdaptiveManufacturingObservationEntry middle;
    middle.object_id = 2;
    middle.layer_id = 1;
    middle.region_id = 8;
    middle.region_category = AdaptiveManufacturingObservationRegionCategory::Support;
    middle.observed_item_count = 7;

    summary.add_entry(later);
    summary.add_entry(earlier);
    summary.add_entry(middle);

    REQUIRE_FALSE(summary.empty());
    REQUIRE(summary.size() == 3);
    REQUIRE(summary.entries().size() == 3);

    CHECK(summary.entries()[0].object_id == 1);
    CHECK(summary.entries()[0].layer_id == 9);
    CHECK(summary.entries()[0].region_id == 0);
    CHECK(summary.entries()[0].region_category == AdaptiveManufacturingObservationRegionCategory::Perimeter);
    CHECK(summary.entries()[0].observed_item_count == 3);
    CHECK(summary.entries()[0].warning_count == 0);

    CHECK(summary.entries()[1].object_id == 2);
    CHECK(summary.entries()[1].layer_id == 1);
    CHECK(summary.entries()[1].region_id == 8);
    CHECK(summary.entries()[1].region_category == AdaptiveManufacturingObservationRegionCategory::Support);

    CHECK(summary.entries()[2].object_id == 2);
    CHECK(summary.entries()[2].layer_id == 3);
    CHECK(summary.entries()[2].region_id == 4);
    CHECK(summary.entries()[2].region_category == AdaptiveManufacturingObservationRegionCategory::Infill);
    CHECK(summary.entries()[2].observed_item_count == 12);
    CHECK(summary.entries()[2].warning_count == 1);
}

TEST_CASE("Adaptive manufacturing observation summary order is deterministic for repeated add order", "[AdaptiveManufacturingObservation]")
{
    AdaptiveManufacturingObservationSummary first;
    AdaptiveManufacturingObservationSummary second;

    AdaptiveManufacturingObservationEntry a;
    a.object_id = 4;
    a.layer_id = 1;
    a.region_id = 9;

    AdaptiveManufacturingObservationEntry b;
    b.object_id = 1;
    b.layer_id = 5;
    b.region_id = 2;

    first.add_entry(a);
    first.add_entry(b);

    second.add_entry(b);
    second.add_entry(a);

    REQUIRE(first.entries().size() == 2);
    REQUIRE(second.entries().size() == 2);
    CHECK(first.entries()[0] == second.entries()[0]);
    CHECK(first.entries()[1] == second.entries()[1]);
}

TEST_CASE("Adaptive manufacturing observation summary preserves warnings and clears entries", "[AdaptiveManufacturingObservation]")
{
    AdaptiveManufacturingObservationSummary summary;
    AdaptiveManufacturingObservationEntry entry;
    entry.region_category = AdaptiveManufacturingObservationRegionCategory::Unknown;

    summary.add_entry(entry);
    summary.add_warning("summary warning only");

    CHECK(summary.size() == 1);
    REQUIRE(summary.warnings().size() == 1);
    CHECK(summary.warnings().front() == "summary warning only");
    CHECK(summary.entries().front().region_category == AdaptiveManufacturingObservationRegionCategory::Unknown);

    summary.clear();
    CHECK(summary.empty());
    CHECK(summary.size() == 0);
    CHECK(summary.entries().empty());
    REQUIRE(summary.warnings().size() == 1);
    CHECK(summary.warnings().front() == "summary warning only");
}

TEST_CASE("Adaptive manufacturing observation entry is summary-only", "[AdaptiveManufacturingObservation]")
{
    AdaptiveManufacturingObservationEntry entry;

    CHECK(entry.object_id == 0);
    CHECK(entry.layer_id == 0);
    CHECK(entry.region_id == 0);
    CHECK(entry.region_category == AdaptiveManufacturingObservationRegionCategory::Unknown);
    CHECK(entry.observed_item_count == 0);
    CHECK(entry.warning_count == 0);
}
