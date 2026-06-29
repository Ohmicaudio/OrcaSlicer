#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingDebugArtifactSerializer.hpp"
#include "libslic3r/AdaptiveManufacturingObservation.hpp"
#include "libslic3r/AdaptiveManufacturingObservationDebugMapper.hpp"

using namespace Slic3r;

TEST_CASE("Adaptive manufacturing debug artifact omits absent observation summary", "[AdaptiveManufacturingObservationDebugMapper]")
{
    AdaptiveManufacturingDebugArtifact artifact;

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);

    CHECK(json.find("observation_summary") == std::string::npos);
}

TEST_CASE("Adaptive manufacturing observation summary maps to debug artifact JSON", "[AdaptiveManufacturingObservationDebugMapper]")
{
    AdaptiveManufacturingObservationSummary summary;
    summary.add_warning("summary \"warning\"");
    summary.add_warning("line\nwarning");

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

    summary.add_entry(later);
    summary.add_entry(earlier);

    const std::vector<AdaptiveManufacturingObservationEntry> original_entries = summary.entries();
    const std::vector<std::string> original_warnings = summary.warnings();

    AdaptiveManufacturingDebugArtifact artifact;
    attach_observation_summary_to_debug_artifact(artifact, summary);

    const std::string expected =
        "{\"schema_version\":\"0.1\",\"generation_mode\":\"disabled\",\"warnings\":[],\"entries\":[],"
        "\"observation_summary\":{\"warnings\":[\"summary \\\"warning\\\"\",\"line\\nwarning\"],\"entries\":["
        "{\"object_id\":1,\"layer_id\":9,\"region_id\":0,\"region_category\":\"perimeter\",\"observed_item_count\":3,\"warning_count\":0},"
        "{\"object_id\":2,\"layer_id\":3,\"region_id\":4,\"region_category\":\"infill\",\"observed_item_count\":12,\"warning_count\":1}"
        "]}}";

    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) == expected);
    CHECK(summary.entries() == original_entries);
    CHECK(summary.warnings() == original_warnings);
}

TEST_CASE("Adaptive manufacturing observation category strings are stable", "[AdaptiveManufacturingObservationDebugMapper]")
{
    AdaptiveManufacturingObservationSummary summary;

    AdaptiveManufacturingObservationEntry unknown;
    unknown.object_id = 1;
    unknown.layer_id = 0;
    unknown.region_id = 0;
    unknown.region_category = AdaptiveManufacturingObservationRegionCategory::Unknown;

    AdaptiveManufacturingObservationEntry perimeter;
    perimeter.object_id = 1;
    perimeter.layer_id = 0;
    perimeter.region_id = 1;
    perimeter.region_category = AdaptiveManufacturingObservationRegionCategory::Perimeter;

    AdaptiveManufacturingObservationEntry infill;
    infill.object_id = 1;
    infill.layer_id = 0;
    infill.region_id = 2;
    infill.region_category = AdaptiveManufacturingObservationRegionCategory::Infill;

    AdaptiveManufacturingObservationEntry support;
    support.object_id = 1;
    support.layer_id = 0;
    support.region_id = 3;
    support.region_category = AdaptiveManufacturingObservationRegionCategory::Support;

    summary.add_entry(support);
    summary.add_entry(infill);
    summary.add_entry(perimeter);
    summary.add_entry(unknown);

    AdaptiveManufacturingDebugArtifact artifact;
    attach_observation_summary_to_debug_artifact(artifact, summary);

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);

    CHECK(json.find("\"region_category\":\"unknown\"") != std::string::npos);
    CHECK(json.find("\"region_category\":\"perimeter\"") != std::string::npos);
    CHECK(json.find("\"region_category\":\"infill\"") != std::string::npos);
    CHECK(json.find("\"region_category\":\"support\"") != std::string::npos);
    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) == serialize_adaptive_manufacturing_debug_artifact(artifact));
}
