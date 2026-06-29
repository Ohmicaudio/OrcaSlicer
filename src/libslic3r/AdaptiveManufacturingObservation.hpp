#ifndef slic3r_AdaptiveManufacturingObservation_hpp_
#define slic3r_AdaptiveManufacturingObservation_hpp_

#include <cstddef>
#include <string>
#include <vector>

namespace Slic3r {

enum class AdaptiveManufacturingObservationRegionCategory {
    Unknown,
    Perimeter,
    Infill,
    Support
};

struct AdaptiveManufacturingObservationEntry
{
    int object_id = 0;
    int layer_id = 0;
    int region_id = 0;
    AdaptiveManufacturingObservationRegionCategory region_category = AdaptiveManufacturingObservationRegionCategory::Unknown;
    std::size_t observed_item_count = 0;
    std::size_t warning_count = 0;

    bool operator<(const AdaptiveManufacturingObservationEntry &rhs) const;
    bool operator==(const AdaptiveManufacturingObservationEntry &rhs) const;
};

class AdaptiveManufacturingObservationSummary
{
public:
    bool empty() const;
    std::size_t size() const;
    void clear();

    void add_entry(const AdaptiveManufacturingObservationEntry &entry);
    const std::vector<AdaptiveManufacturingObservationEntry> &entries() const;

    void add_warning(const std::string &warning);
    const std::vector<std::string> &warnings() const;

private:
    std::vector<AdaptiveManufacturingObservationEntry> m_entries;
    std::vector<std::string> m_warnings;
};

} // namespace Slic3r

#endif
