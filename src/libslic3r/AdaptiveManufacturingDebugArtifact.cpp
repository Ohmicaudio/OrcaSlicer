#include "AdaptiveManufacturingDebugArtifact.hpp"

#include <algorithm>
#include <tuple>

namespace Slic3r {

bool AdaptiveManufacturingDebugEntry::operator<(const AdaptiveManufacturingDebugEntry &rhs) const
{
    return std::tie(this->object_id, this->layer_id, this->region_id)
         < std::tie(rhs.object_id, rhs.layer_id, rhs.region_id);
}

bool AdaptiveManufacturingDebugObservationEntry::operator<(const AdaptiveManufacturingDebugObservationEntry &rhs) const
{
    return std::tie(this->object_id, this->layer_id, this->region_id)
         < std::tie(rhs.object_id, rhs.layer_id, rhs.region_id);
}

bool AdaptiveManufacturingDebugObservationSummary::empty() const
{
    return m_entries.empty();
}

std::size_t AdaptiveManufacturingDebugObservationSummary::size() const
{
    return m_entries.size();
}

void AdaptiveManufacturingDebugObservationSummary::clear()
{
    m_entries.clear();
}

void AdaptiveManufacturingDebugObservationSummary::add_entry(const AdaptiveManufacturingDebugObservationEntry &entry)
{
    m_entries.push_back(entry);
    std::sort(m_entries.begin(), m_entries.end());
}

const std::vector<AdaptiveManufacturingDebugObservationEntry> &AdaptiveManufacturingDebugObservationSummary::entries() const
{
    return m_entries;
}

void AdaptiveManufacturingDebugObservationSummary::add_warning(const std::string &warning)
{
    m_warnings.push_back(warning);
}

const std::vector<std::string> &AdaptiveManufacturingDebugObservationSummary::warnings() const
{
    return m_warnings;
}

bool AdaptiveManufacturingDebugArtifact::empty() const
{
    return m_entries.empty();
}

std::size_t AdaptiveManufacturingDebugArtifact::size() const
{
    return m_entries.size();
}

void AdaptiveManufacturingDebugArtifact::clear()
{
    m_entries.clear();
}

void AdaptiveManufacturingDebugArtifact::add_entry(const AdaptiveManufacturingDebugEntry &entry)
{
    m_entries.push_back(entry);
    std::sort(m_entries.begin(), m_entries.end());
}

const std::vector<AdaptiveManufacturingDebugEntry> &AdaptiveManufacturingDebugArtifact::entries() const
{
    return m_entries;
}

void AdaptiveManufacturingDebugArtifact::add_warning(const std::string &warning)
{
    m_warnings.push_back(warning);
}

const std::vector<std::string> &AdaptiveManufacturingDebugArtifact::warnings() const
{
    return m_warnings;
}

} // namespace Slic3r
