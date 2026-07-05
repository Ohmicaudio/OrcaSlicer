#ifndef slic3r_tests_amp_debug_artifact_test_helpers_hpp_
#define slic3r_tests_amp_debug_artifact_test_helpers_hpp_

#include <catch2/catch.hpp>

#include "libslic3r/AdaptiveManufacturingDebugArtifact.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

namespace Slic3r {

inline std::string read_text_fixture(const std::string &path)
{
    std::ifstream file(path);
    REQUIRE(file.good());
    std::ostringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

inline std::string normalize_packet_json_for_exact_compare(std::string text)
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

inline std::size_t key_value_position(const std::string &json, const std::string &key)
{
    const std::string needle = "\"" + key + "\":";
    const std::size_t key_pos = json.find(needle);
    REQUIRE(key_pos != std::string::npos);
    std::size_t value_pos = key_pos + needle.size();
    while (value_pos < json.size() && std::isspace(static_cast<unsigned char>(json[value_pos])))
        ++value_pos;
    return value_pos;
}

inline std::string parse_json_string_at(const std::string &json, std::size_t pos)
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

inline std::string string_value(const std::string &json, const std::string &key)
{
    return parse_json_string_at(json, key_value_position(json, key));
}

inline bool contains_key(const std::string &json, const std::string &key)
{
    return json.find("\"" + key + "\":") != std::string::npos;
}

inline bool bool_value(const std::string &json, const std::string &key)
{
    const std::size_t pos = key_value_position(json, key);
    if (json.compare(pos, 4, "true") == 0)
        return true;
    REQUIRE(json.compare(pos, 5, "false") == 0);
    return false;
}

inline double double_value(const std::string &json, const std::string &key)
{
    const std::size_t pos = key_value_position(json, key);
    return std::stod(json.substr(pos));
}

inline int int_value(const std::string &json, const std::string &key)
{
    const std::size_t pos = key_value_position(json, key);
    return std::stoi(json.substr(pos));
}

inline std::size_t closing_delimiter(const std::string &json, std::size_t open_pos, char open, char close)
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

inline std::string array_value(const std::string &json, const std::string &key)
{
    const std::size_t open_pos = key_value_position(json, key);
    const std::size_t close_pos = closing_delimiter(json, open_pos, '[', ']');
    return json.substr(open_pos, close_pos - open_pos + 1);
}

inline std::vector<std::string> string_array_value(const std::string &json, const std::string &key)
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

inline std::vector<std::string> object_array_value(const std::string &json, const std::string &key)
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

inline std::set<std::string> top_level_object_keys(const std::string &json)
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

inline void require_only_keys(const std::string &json, const std::set<std::string> &allowed_keys)
{
    const std::set<std::string> keys = top_level_object_keys(json);
    for (const std::string &key : keys)
        REQUIRE(allowed_keys.count(key) == 1);
}

inline AdaptiveManufacturingDebugGenerationMode generation_mode_from_json(const std::string &value)
{
    if (value == "offline_advisory")
        return AdaptiveManufacturingDebugGenerationMode::OfflineAdvisory;
    if (value == "enabled_readonly")
        return AdaptiveManufacturingDebugGenerationMode::EnabledReadonly;
    if (value == "enabled_noop")
        return AdaptiveManufacturingDebugGenerationMode::EnabledNoop;
    return AdaptiveManufacturingDebugGenerationMode::Disabled;
}

inline AdaptiveManufacturingDebugSourceStage source_stage_from_json(const std::string &value)
{
    if (value == "offline_plan_packet")
        return AdaptiveManufacturingDebugSourceStage::OfflinePlanPacket;
    if (value == "future_observation")
        return AdaptiveManufacturingDebugSourceStage::FutureObservation;
    if (value == "no_op_planner")
        return AdaptiveManufacturingDebugSourceStage::NoOpPlanner;
    return AdaptiveManufacturingDebugSourceStage::StockFallback;
}

inline AdaptiveManufacturingDebugEntry entry_from_json(const std::string &json)
{
    require_only_keys(json, {
        "object_id", "layer_id", "region_id", "plan_reason", "confidence", "toolchange_requested",
        "bead_width_override_present", "nozzle_override_present", "source_stage", "region_name",
        "recommended_tool_class", "fallback_tool_class", "selected_process_profile",
        "selected_layer_height_mm", "selected_line_width_class", "cost_gate_passed", "cost_gate_reason",
        "fallback_reason", "risk_flags", "local_z_future_required", "touchscreen_mixed_nozzle_blocked",
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

inline AdaptiveManufacturingDebugArtifact import_debug_artifact_from_json_string(const std::string &json)
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

inline AdaptiveManufacturingDebugArtifact import_debug_artifact_from_json_fixture(const std::string &path)
{
    return import_debug_artifact_from_json_string(read_text_fixture(path));
}

inline const AdaptiveManufacturingDebugEntry *find_entry_by_region_name(
    const AdaptiveManufacturingDebugArtifact &artifact,
    const std::string &region_name)
{
    const auto &entries = artifact.entries();
    const auto it = std::find_if(entries.begin(), entries.end(), [&region_name](const AdaptiveManufacturingDebugEntry &entry) {
        return entry.region_name.has_value() && *entry.region_name == region_name;
    });
    return it == entries.end() ? nullptr : &*it;
}

} // namespace Slic3r

#endif
