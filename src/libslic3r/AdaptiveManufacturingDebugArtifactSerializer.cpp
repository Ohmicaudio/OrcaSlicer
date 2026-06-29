#include "AdaptiveManufacturingDebugArtifactSerializer.hpp"

#include <cstddef>
#include <iomanip>
#include <locale>
#include <sstream>

namespace Slic3r {
namespace {

std::string json_escape(const std::string &value)
{
    std::ostringstream out;
    for (const unsigned char c : value) {
        switch (c) {
        case '"': out << "\\\""; break;
        case '\\': out << "\\\\"; break;
        case '\b': out << "\\b"; break;
        case '\f': out << "\\f"; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default:
            if (c < 0x20)
                out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(c) << std::dec;
            else
                out << static_cast<char>(c);
            break;
        }
    }
    return out.str();
}

const char *to_json(AdaptiveManufacturingDebugGenerationMode mode)
{
    switch (mode) {
    case AdaptiveManufacturingDebugGenerationMode::Disabled: return "disabled";
    case AdaptiveManufacturingDebugGenerationMode::EnabledNoop: return "enabled_noop";
    case AdaptiveManufacturingDebugGenerationMode::EnabledReadonly: return "enabled_readonly";
    }
    return "disabled";
}

const char *to_json(AdaptiveManufacturingDebugSourceStage stage)
{
    switch (stage) {
    case AdaptiveManufacturingDebugSourceStage::StockFallback: return "stock_fallback";
    case AdaptiveManufacturingDebugSourceStage::NoOpPlanner: return "no_op_planner";
    case AdaptiveManufacturingDebugSourceStage::FutureObservation: return "future_observation";
    }
    return "stock_fallback";
}

const char *to_json(AdaptiveManufacturingReason reason)
{
    switch (reason) {
    case AdaptiveManufacturingReason::StockFallback: return "StockFallback";
    }
    return "StockFallback";
}

void append_json_string_array(std::ostringstream &out, const std::vector<std::string> &values)
{
    out << "[";
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i > 0)
            out << ",";
        out << "\"" << json_escape(values[i]) << "\"";
    }
    out << "]";
}

void append_entry(std::ostringstream &out, const AdaptiveManufacturingDebugEntry &entry)
{
    out << "{";
    out << "\"object_id\":" << entry.object_id;
    out << ",\"layer_id\":" << entry.layer_id;
    out << ",\"region_id\":" << entry.region_id;
    out << ",\"plan_reason\":\"" << to_json(entry.plan_reason) << "\"";
    out << ",\"confidence\":" << entry.confidence;
    out << ",\"toolchange_requested\":" << (entry.toolchange_requested ? "true" : "false");
    out << ",\"bead_width_override_present\":" << (entry.bead_width_override_present ? "true" : "false");
    out << ",\"nozzle_override_present\":" << (entry.nozzle_override_present ? "true" : "false");
    out << ",\"source_stage\":\"" << to_json(entry.source_stage) << "\"";
    out << ",\"warnings\":";
    append_json_string_array(out, entry.warnings);
    out << "}";
}

void append_observation_entry(std::ostringstream &out, const AdaptiveManufacturingDebugObservationEntry &entry)
{
    out << "{";
    out << "\"object_id\":" << entry.object_id;
    out << ",\"layer_id\":" << entry.layer_id;
    out << ",\"region_id\":" << entry.region_id;
    out << ",\"region_category\":\"" << json_escape(entry.region_category) << "\"";
    out << ",\"observed_item_count\":" << entry.observed_item_count;
    out << ",\"warning_count\":" << entry.warning_count;
    out << "}";
}

void append_observation_summary(std::ostringstream &out, const AdaptiveManufacturingDebugObservationSummary &summary)
{
    out << "{";
    out << "\"warnings\":";
    append_json_string_array(out, summary.warnings());
    out << ",\"entries\":[";
    const auto &entries = summary.entries();
    for (std::size_t i = 0; i < entries.size(); ++i) {
        if (i > 0)
            out << ",";
        append_observation_entry(out, entries[i]);
    }
    out << "]}";
}

} // namespace

std::string serialize_adaptive_manufacturing_debug_artifact(const AdaptiveManufacturingDebugArtifact &artifact)
{
    std::ostringstream out;
    out.imbue(std::locale::classic());
    out << std::setprecision(17);
    out << "{";
    out << "\"schema_version\":\"" << json_escape(artifact.schema_version) << "\"";
    if (artifact.slicer_build_info.has_value())
        out << ",\"slicer_build_info\":\"" << json_escape(*artifact.slicer_build_info) << "\"";
    out << ",\"generation_mode\":\"" << to_json(artifact.generation_mode) << "\"";
    out << ",\"warnings\":";
    append_json_string_array(out, artifact.warnings());
    out << ",\"entries\":[";
    const auto &entries = artifact.entries();
    for (std::size_t i = 0; i < entries.size(); ++i) {
        if (i > 0)
            out << ",";
        append_entry(out, entries[i]);
    }
    out << "]";
    if (artifact.observation_summary.has_value()) {
        out << ",\"observation_summary\":";
        append_observation_summary(out, *artifact.observation_summary);
    }
    out << "}";
    return out.str();
}

} // namespace Slic3r
