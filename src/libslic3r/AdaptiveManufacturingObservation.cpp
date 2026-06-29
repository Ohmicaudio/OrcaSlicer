#include "AdaptiveManufacturingObservation.hpp"

#include <algorithm>
#include <tuple>

namespace Slic3r {

bool AdaptiveManufacturingObservationEntry::operator<(const AdaptiveManufacturingObservationEntry &rhs) const
{
    return std::tie(this->object_id, this->layer_id, this->region_id)
         < std::tie(rhs.object_id, rhs.layer_id, rhs.region_id);
}

bool AdaptiveManufacturingObservationEntry::operator==(const AdaptiveManufacturingObservationEntry &rhs) const
{
    return this->object_id == rhs.object_id
        && this->layer_id == rhs.layer_id
        && this->region_id == rhs.region_id
        && this->region_category == rhs.region_category
        && this->observed_item_count == rhs.observed_item_count
        && this->warning_count == rhs.warning_count;
}

bool AdaptiveManufacturingObservationSummary::empty() const
{
    return m_entries.empty();
}

std::size_t AdaptiveManufacturingObservationSummary::size() const
{
    return m_entries.size();
}

void AdaptiveManufacturingObservationSummary::clear()
{
    m_entries.clear();
}

void AdaptiveManufacturingObservationSummary::add_entry(const AdaptiveManufacturingObservationEntry &entry)
{
    m_entries.push_back(entry);
    std::sort(m_entries.begin(), m_entries.end());
}

const std::vector<AdaptiveManufacturingObservationEntry> &AdaptiveManufacturingObservationSummary::entries() const
{
    return m_entries;
}

void AdaptiveManufacturingObservationSummary::add_warning(const std::string &warning)
{
    m_warnings.push_back(warning);
}

const std::vector<std::string> &AdaptiveManufacturingObservationSummary::warnings() const
{
    return m_warnings;
}

} // namespace Slic3r
