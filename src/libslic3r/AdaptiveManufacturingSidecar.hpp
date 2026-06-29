#ifndef slic3r_AdaptiveManufacturingSidecar_hpp_
#define slic3r_AdaptiveManufacturingSidecar_hpp_

#include "AdaptiveManufacturingPlan.hpp"

#include <cstddef>
#include <map>

namespace Slic3r {

struct AdaptiveManufacturingSidecarKey
{
    int object_id = 0;
    int layer_id = 0;
    int region_id = 0;

    bool operator<(const AdaptiveManufacturingSidecarKey &rhs) const;
    bool operator==(const AdaptiveManufacturingSidecarKey &rhs) const;
};

class AdaptiveManufacturingSidecar
{
public:
    bool empty() const;
    std::size_t size() const;
    void clear();

    void insert_or_assign(const AdaptiveManufacturingSidecarKey &key, const AdaptiveManufacturingPlan &plan);
    const AdaptiveManufacturingPlan *find(const AdaptiveManufacturingSidecarKey &key) const;
    bool contains(const AdaptiveManufacturingSidecarKey &key) const;

private:
    std::map<AdaptiveManufacturingSidecarKey, AdaptiveManufacturingPlan> m_plans;
};

} // namespace Slic3r

#endif
