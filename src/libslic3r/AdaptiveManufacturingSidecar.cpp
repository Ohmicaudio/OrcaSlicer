#include "AdaptiveManufacturingSidecar.hpp"

#include <tuple>

namespace Slic3r {

bool AdaptiveManufacturingSidecarKey::operator<(const AdaptiveManufacturingSidecarKey &rhs) const
{
    return std::tie(this->object_id, this->layer_id, this->region_id)
         < std::tie(rhs.object_id, rhs.layer_id, rhs.region_id);
}

bool AdaptiveManufacturingSidecarKey::operator==(const AdaptiveManufacturingSidecarKey &rhs) const
{
    return this->object_id == rhs.object_id
        && this->layer_id == rhs.layer_id
        && this->region_id == rhs.region_id;
}

bool AdaptiveManufacturingSidecar::empty() const
{
    return m_plans.empty();
}

std::size_t AdaptiveManufacturingSidecar::size() const
{
    return m_plans.size();
}

void AdaptiveManufacturingSidecar::clear()
{
    m_plans.clear();
}

void AdaptiveManufacturingSidecar::insert_or_assign(const AdaptiveManufacturingSidecarKey &key, const AdaptiveManufacturingPlan &plan)
{
    m_plans[key] = plan;
}

const AdaptiveManufacturingPlan *AdaptiveManufacturingSidecar::find(const AdaptiveManufacturingSidecarKey &key) const
{
    const auto it = m_plans.find(key);
    return it == m_plans.end() ? nullptr : &it->second;
}

bool AdaptiveManufacturingSidecar::contains(const AdaptiveManufacturingSidecarKey &key) const
{
    return this->find(key) != nullptr;
}

} // namespace Slic3r
