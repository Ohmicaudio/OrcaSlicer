#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingDebugArtifactSerializer.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <set>
#include <sstream>

using namespace Slic3r;

namespace {

std::string read_text_fixture(const std::string &path)
{
    std::ifstream file(path);
    REQUIRE(file.good());
    std::ostringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

std::string normalize_packet_json_for_exact_compare(std::string text)
{
    std::string normalized;
    normalized.reserve(text.size());
    for (std::size_t i = 0; i < text.size(); ++i) {
        if (text[i] == '\r') {
            if (i + 1 < text.size() && text[i + 1] == '\n')
                continue;
            normalized.push_back('\n');
        } else {
            normalized.push_back(text[i]);
        }
    }
    if (!normalized.empty() && normalized.back() == '\n')
        normalized.pop_back();
    return normalized;
}

AdaptiveManufacturingDebugEntry make_packet_entry(
    int layer_id,
    int region_id,
    const std::string &region_name,
    const std::string &recommended_tool_class,
    const std::string &fallback_tool_class,
    const std::string &selected_process_profile,
    double selected_layer_height_mm,
    const std::string &selected_line_width_class,
    const std::string &cost_gate_reason,
    const std::string &fallback_reason,
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
    entry.cost_gate_reason = cost_gate_reason;
    entry.fallback_reason = fallback_reason;
    entry.risk_flags = risk_flags;
    entry.local_z_future_required = local_z_future_required;
    entry.touchscreen_mixed_nozzle_blocked = true;
    return entry;
}

std::size_t key_value_position(const std::string &json, const std::string &key)
{
    const std::string needle = "\"" + key + "\":";
    const std::size_t key_pos = json.find(needle);
    REQUIRE(key_pos != std::string::npos);
    std::size_t value_pos = key_pos + needle.size();
    while (value_pos < json.size() && std::isspace(static_cast<unsigned char>(json[value_pos])))
        ++value_pos;
    return value_pos;
}

std::string parse_json_string_at(const std::string &json, std::size_t pos)
{
    REQUIRE(pos < json.size());
    REQUIRE(json[pos] == '"');
    std::string value;
    bool escaped = false;
    for (std::size_t i = pos + 1; i < json.size(); ++i) {
        const char c = json[i];
        if (escaped) {
            switch (c) {
            case '"': value.push_back('"'); break;
            case '\\': value.push_back('\\'); break;
            case 'n': value.push_back('\n'); break;
            case 'r': value.push_back('\r'); break;
            case 't': value.push_back('\t'); break;
            default: value.push_back(c); break;
            }
            escaped = false;
        } else if (c == '\\') {
            escaped = true;
        } else if (c == '"') {
            return value;
        } else {
            value.push_back(c);
        }
    }
    FAIL("unterminated JSON string in test fixture");
    return {};
}

std::string string_value(const std::string &json, const std::string &key)
{
    return parse_json_string_at(json, key_value_position(json, key));
}

bool contains_key(const std::string &json, const std::string &key)
{
    return json.find("\"" + key + "\":") != std::string::npos;
}

bool bool_value(const std::string &json, const std::string &key)
{
    const std::size_t pos = key_value_position(json, key);
    if (json.compare(pos, 4, "true") == 0)
        return true;
    REQUIRE(json.compare(pos, 5, "false") == 0);
    return false;
}

double double_value(const std::string &json, const std::string &key)
{
    const std::size_t pos = key_value_position(json, key);
    return std::stod(json.substr(pos));
}

int int_value(const std::string &json, const std::string &key)
{
    const std::size_t pos = key_value_position(json, key);
    return std::stoi(json.substr(pos));
}

std::size_t closing_delimiter(const std::string &json, std::size_t open_pos, char open, char close)
{
    REQUIRE(open_pos < json.size());
    REQUIRE(json[open_pos] == open);
    int depth = 0;
    bool in_string = false;
    bool escaped = false;
    for (std::size_t i = open_pos; i < json.size(); ++i) {
        const char c = json[i];
        if (in_string) {
            if (escaped)
                escaped = false;
            else if (c == '\\')
                escaped = true;
            else if (c == '"')
                in_string = false;
            continue;
        }
        if (c == '"') {
            in_string = true;
        } else if (c == open) {
            ++depth;
        } else if (c == close) {
            --depth;
            if (depth == 0)
                return i;
        }
    }
    FAIL("unterminated JSON delimiter in test fixture");
    return std::string::npos;
}

std::string array_value(const std::string &json, const std::string &key)
{
    const std::size_t open_pos = key_value_position(json, key);
    const std::size_t close_pos = closing_delimiter(json, open_pos, '[', ']');
    return json.substr(open_pos, close_pos - open_pos + 1);
}

std::vector<std::string> string_array_value(const std::string &json, const std::string &key)
{
    const std::string array = array_value(json, key);
    std::vector<std::string> result;
    for (std::size_t pos = 1; pos + 1 < array.size();) {
        while (pos < array.size() && (std::isspace(static_cast<unsigned char>(array[pos])) || array[pos] == ','))
            ++pos;
        if (pos >= array.size() || array[pos] == ']')
            break;
        result.push_back(parse_json_string_at(array, pos));
        pos = array.find('"', pos + 1);
        while (pos != std::string::npos && array[pos - 1] == '\\')
            pos = array.find('"', pos + 1);
        REQUIRE(pos != std::string::npos);
        ++pos;
    }
    return result;
}

std::vector<std::string> object_array_value(const std::string &json, const std::string &key)
{
    const std::string array = array_value(json, key);
    std::vector<std::string> objects;
    for (std::size_t pos = 1; pos + 1 < array.size();) {
        while (pos < array.size() && (std::isspace(static_cast<unsigned char>(array[pos])) || array[pos] == ','))
            ++pos;
        if (pos >= array.size() || array[pos] == ']')
            break;
        REQUIRE(array[pos] == '{');
        const std::size_t close_pos = closing_delimiter(array, pos, '{', '}');
        objects.push_back(array.substr(pos, close_pos - pos + 1));
        pos = close_pos + 1;
    }
    return objects;
}

std::set<std::string> top_level_object_keys(const std::string &json)
{
    REQUIRE(!json.empty());
    REQUIRE(json.front() == '{');
    std::set<std::string> keys;
    bool in_string = false;
    bool escaped = false;
    int depth = 0;
    for (std::size_t i = 0; i < json.size(); ++i) {
        const char c = json[i];
        if (in_string) {
            if (escaped)
                escaped = false;
            else if (c == '\\')
                escaped = true;
            else if (c == '"')
                in_string = false;
            continue;
        }
        if (c == '"') {
            if (depth == 1) {
                const std::string key = parse_json_string_at(json, i);
                std::size_t after = i + key.size() + 2;
                while (after < json.size() && std::isspace(static_cast<unsigned char>(json[after])))
                    ++after;
                if (after < json.size() && json[after] == ':')
                    keys.insert(key);
            }
            in_string = true;
        } else if (c == '{' || c == '[') {
            ++depth;
        } else if (c == '}' || c == ']') {
            --depth;
        }
    }
    return keys;
}

void require_only_keys(const std::string &json, const std::set<std::string> &allowed_keys)
{
    const std::set<std::string> keys = top_level_object_keys(json);
    for (const std::string &key : keys)
        REQUIRE(allowed_keys.count(key) == 1);
}

AdaptiveManufacturingDebugGenerationMode generation_mode_from_json(const std::string &value)
{
    if (value == "offline_advisory")
        return AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;
    if (value == "enabled_readonly")
        return AdaptiveManufacturingDebugGenerationMode::EnabledReadonly;
    if (value == "enabled_noop")
        return AdaptiveManufacturingDebugGenerationMode::EnabledNoop;
    return AdaptiveManufacturingDebugGenerationMode::Disabled;
}

AdaptiveManufacturingDebugSourceStage source_stage_from_json(const std::string &value)
{
    if (value == "offline_plan_packet")
        return AdaptiveManufacturingDebugSourceStage::OfflinePlanPacket;
    if (value == "future_observation")
        return AdaptiveManufacturingDebugSourceStage::FutureObservation;
    if (value == "no_op_planner")
        return AdaptiveManufacturingDebugSourceStage::NoOpPlanner;
    return AdaptiveManufacturingDebugSourceStage::StockFallback;
}

AdaptiveManufacturingDebugEntry entry_from_json(const std::string &json)
{
    require_only_keys(json, {
        "object_id",
        "layer_id",
        "region_id",
        "plan_reason",
        "confidence",
        "toolchange_requested",
        "bead_width_override_present",
        "nozzle_override_present",
        "source_stage",
        "region_name",
        "recommended_tool_class",
        "fallback_tool_class",
        "selected_process_profile",
        "selected_layer_height_mm",
        "selected_line_width_class",
        "cost_gate_passed",
        "cost_gate_reason",
        "fallback_reason",
        "risk_flags",
        "local_z_future_required",
        "touchscreen_mixed_nozzle_blocked",
        "warnings",
    });
    AdaptiveManufacturingDebugEntry entry;
    entry.object_id = int_value(json, "object_id");
    entry.layer_id = int_value(json, "layer_id");
    entry.region_id = int_value(json, "region_id");
    entry.confidence = double_value(json, "confidence");
    entry.toolchange_requested = bool_value(json, "toolchange_requested");
    entry.bead_width_override_present = bool_value(json, "bead_width_override_present");
    entry.nozzle_override_present = bool_value(json, "nozzle_override_present");
    entry.source_stage = source_stage_from_json(string_value(json, "source_stage"));
    if (contains_key(json, "region_name"))
        entry.region_name = string_value(json, "region_name");
    if (contains_key(json, "recommended_tool_class"))
        entry.recommended_tool_class = string_value(json, "recommended_tool_class");
    if (contains_key(json, "fallback_tool_class"))
        entry.fallback_tool_class = string_value(json, "fallback_tool_class");
    if (contains_key(json, "selected_process_profile"))
        entry.selected_process_profile = string_value(json, "selected_process_profile");
    if (contains_key(json, "selected_layer_height_mm"))
        entry.selected_layer_height_mm = double_value(json, "selected_layer_height_mm");
    if (contains_key(json, "selected_line_width_class"))
        entry.selected_line_width_class = string_value(json, "selected_line_width_class");
    if (contains_key(json, "cost_gate_passed"))
        entry.cost_gate_passed = bool_value(json, "cost_gate_passed");
    if (contains_key(json, "cost_gate_reason"))
        entry.cost_gate_reason = string_value(json, "cost_gate_reason");
    if (contains_key(json, "fallback_reason"))
        entry.fallback_reason = string_value(json, "fallback_reason");
    if (contains_key(json, "risk_flags"))
        entry.risk_flags = string_array_value(json, "risk_flags");
    if (contains_key(json, "local_z_future_required"))
        entry.local_z_future_required = bool_value(json, "local_z_future_required");
    if (contains_key(json, "touchscreen_mixed_nozzle_blocked"))
        entry.touchscreen_mixed_nozzle_blocked = bool_value(json, "touchscreen_mixed_nozzle_blocked");
    if (contains_key(json, "warnings"))
        entry.warnings = string_array_value(json, "warnings");
    return entry;
}

AdaptiveManufacturingDebugArtifact import_debug_artifact_from_json_string(const std::string &json)
{
    require_only_keys(json, {"schema_version", "generation_mode", "warnings", "entries"});
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.schema_version = string_value(json, "schema_version");
    artifact.generation_mode = generation_mode_from_json(string_value(json, "generation_mode"));
    if (contains_key(json, "warnings")) {
        for (const auto &warning : string_array_value(json, "warnings"))
            artifact.add_warning(warning);
    }
    for (const auto &entry_json : object_array_value(json, "entries"))
        artifact.add_entry(entry_from_json(entry_json));
    return artifact;
}

AdaptiveManufacturingDebugArtifact import_debug_artifact_from_json_fixture(const std::string &path)
{
    return import_debug_artifact_from_json_string(read_text_fixture(path));
}

const AdaptiveManufacturingDebugEntry *find_entry_by_region_name(
    const AdaptiveManufacturingDebugArtifact &artifact,
    const std::string &region_name)
{
    const auto &entries = artifact.entries();
    const auto it = std::find_if(entries.begin(), entries.end(), [&region_name](const AdaptiveManufacturingDebugEntry &entry) {
        return entry.region_name.has_value() && *entry.region_name == region_name;
    });
    return it == entries.end() ? nullptr : &*it;
}

} // namespace

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

TEST_CASE("Adaptive manufacturing debug artifact imported missing optionals remain omitted", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    const std::string fixture_json =
        "{\"schema_version\":\"0.1\",\"generation_mode\":\"offline_advisory\",\"warnings\":[],\"entries\":["
        "{\"object_id\":2,\"layer_id\":3,\"region_id\":4,\"plan_reason\":\"StockFallback\",\"confidence\":0,\"toolchange_requested\":false,"
        "\"bead_width_override_present\":false,\"nozzle_override_present\":false,\"source_stage\":\"offline_plan_packet\"}"
        "]}";

    const AdaptiveManufacturingDebugArtifact artifact = import_debug_artifact_from_json_string(fixture_json);
    REQUIRE(artifact.entries().size() == 1);
    const auto &entry = artifact.entries().front();
    CHECK_FALSE(entry.region_name.has_value());
    CHECK_FALSE(entry.recommended_tool_class.has_value());
    CHECK_FALSE(entry.selected_process_profile.has_value());
    CHECK_FALSE(entry.cost_gate_passed.has_value());
    CHECK_FALSE(entry.local_z_future_required.has_value());
    CHECK(entry.risk_flags.empty());

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);
    CHECK(json.find("\"region_name\"") == std::string::npos);
    CHECK(json.find("\"recommended_tool_class\"") == std::string::npos);
    CHECK(json.find("\"selected_process_profile\"") == std::string::npos);
    CHECK(json.find("\"cost_gate_passed\"") == std::string::npos);
    CHECK(json.find("\"local_z_future_required\"") == std::string::npos);
    CHECK(json.find("\"risk_flags\"") == std::string::npos);
    CHECK(json.find(":null") == std::string::npos);
    CHECK(json.find(":\"\"") == std::string::npos);
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

TEST_CASE("Adaptive manufacturing debug artifact matches offline plan packet golden fixture", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    AdaptiveManufacturingDebugArtifact artifact;
    artifact.generation_mode = AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;
    artifact.add_warning("offline advisory golden contract");

    artifact.add_entry(make_packet_entry(
        3,
        3,
        "bulk_zone",
        "0.8",
        "0.6",
        "0.40 Standard @Snapmaker U1 (0.8 nozzle)",
        0.40,
        "0.82-0.88",
        "bulk region passes coarse tool class gate",
        "fallback to 0.6 if bulk spacing is insufficient",
        false,
        {"touchscreen_mixed_nozzle_blocked"}));

    artifact.add_entry(make_packet_entry(
        1,
        1,
        "normal_visible_detail_zone",
        "0.4",
        "0.2",
        "0.16 Optimal @Snapmaker U1 (0.4 nozzle)",
        0.16,
        "0.42-0.45",
        "visible detail uses stock U1 0.4 detail profile",
        "fallback to 0.2 if finer visible detail is required",
        false,
        {"touchscreen_mixed_nozzle_blocked"}));

    artifact.add_entry(make_packet_entry(
        0,
        0,
        "micro_detail_zone",
        "0.2",
        "0.4",
        "0.06 Standard @Snapmaker U1 (0.2 nozzle)",
        0.06,
        "0.22",
        "detail demand passes 0.2 tool class gate",
        "fallback to 0.4 detail-capable tool class",
        true,
        {"local_z_future_required", "touchscreen_mixed_nozzle_blocked"}));

    artifact.add_entry(make_packet_entry(
        2,
        2,
        "structural_shell_zone",
        "0.6",
        "0.4",
        "0.24 Standard @Snapmaker U1 (0.6 nozzle)",
        0.24,
        "0.62-0.66",
        "structural shell can use wider tool class",
        "fallback to 0.4 if shell feature spacing is too tight",
        false,
        {"touchscreen_mixed_nozzle_blocked"}));

    const std::string json = serialize_adaptive_manufacturing_debug_artifact(artifact);
    const std::string golden = normalize_packet_json_for_exact_compare(
        read_text_fixture("tests/libslic3r/data/amp_debug_artifact_offline_plan_packet_golden.json"));

    CHECK(json == golden);
    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) == json);
    CHECK(json.find("\"generation_mode\":\"offline_advisory\"") != std::string::npos);
    CHECK(json.find("\"recommended_tool_class\":\"0.2\"") != std::string::npos);
    CHECK(json.find("\"recommended_tool_class\":\"0.4\"") != std::string::npos);
    CHECK(json.find("\"recommended_tool_class\":\"0.6\"") != std::string::npos);
    CHECK(json.find("\"recommended_tool_class\":\"0.8\"") != std::string::npos);
    CHECK(json.find("\"selected_process_profile\":\"0.06 Standard @Snapmaker U1 (0.2 nozzle)\"") != std::string::npos);
    CHECK(json.find("\"cost_gate_passed\":true") != std::string::npos);
    CHECK(json.find("\"fallback_reason\":\"fallback to 0.4 detail-capable tool class\"") != std::string::npos);
    CHECK(json.find("\"risk_flags\":[\"local_z_future_required\",\"touchscreen_mixed_nozzle_blocked\"]") != std::string::npos);
    CHECK(json.find("\"local_z_future_required\":true") != std::string::npos);
    CHECK(json.find("\"touchscreen_mixed_nozzle_blocked\":true") != std::string::npos);
}

TEST_CASE("Adaptive manufacturing debug artifact golden packet imports and serializes deterministically", "[AdaptiveManufacturingDebugArtifactSerializer]")
{
    const std::string fixture_path = "tests/libslic3r/data/amp_debug_artifact_offline_plan_packet_golden.json";
    const std::string golden = normalize_packet_json_for_exact_compare(read_text_fixture(fixture_path));
    const AdaptiveManufacturingDebugArtifact artifact = import_debug_artifact_from_json_fixture(fixture_path);

    REQUIRE(artifact.generation_mode == AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory);
    REQUIRE(artifact.entries().size() == 4);

    const AdaptiveManufacturingDebugEntry *micro_entry = find_entry_by_region_name(artifact, "micro_detail_zone");
    REQUIRE(micro_entry != nullptr);
    const auto &micro = *micro_entry;
    CHECK(micro.layer_id == 0);
    CHECK(micro.region_id == 0);
    CHECK(micro.recommended_tool_class == "0.2");
    CHECK(micro.fallback_tool_class == "0.4");
    CHECK(micro.selected_process_profile == "0.06 Standard @Snapmaker U1 (0.2 nozzle)");
    REQUIRE(micro.selected_layer_height_mm.has_value());
    CHECK(*micro.selected_layer_height_mm == Approx(0.06));
    CHECK(micro.local_z_future_required == true);
    CHECK(micro.touchscreen_mixed_nozzle_blocked == true);
    REQUIRE(micro.risk_flags.size() == 2);
    CHECK(micro.risk_flags[0] == "local_z_future_required");
    CHECK(micro.risk_flags[1] == "touchscreen_mixed_nozzle_blocked");

    const AdaptiveManufacturingDebugEntry *bulk_entry = find_entry_by_region_name(artifact, "bulk_zone");
    REQUIRE(bulk_entry != nullptr);
    const auto &bulk = *bulk_entry;
    CHECK(bulk.layer_id == 3);
    CHECK(bulk.region_id == 3);
    CHECK(bulk.recommended_tool_class == "0.8");
    CHECK(bulk.selected_process_profile == "0.40 Standard @Snapmaker U1 (0.8 nozzle)");

    const std::string json1 = serialize_adaptive_manufacturing_debug_artifact(artifact);
    CHECK(json1 == golden);
    CHECK(serialize_adaptive_manufacturing_debug_artifact(artifact) == json1);
    const AdaptiveManufacturingDebugArtifact imported_again = import_debug_artifact_from_json_string(json1);
    const std::string json2 = serialize_adaptive_manufacturing_debug_artifact(imported_again);
    CHECK(json1 == json2);
    CHECK(json1.find("observation_summary") == std::string::npos);
    CHECK(json1.find("slicer_build_info") == std::string::npos);
}
