#ifndef slic3r_AdaptiveManufacturingPlanner_hpp_
#define slic3r_AdaptiveManufacturingPlanner_hpp_

#include "AdaptiveManufacturingPlan.hpp"

namespace Slic3r {

class AdaptiveManufacturingPlanner
{
public:
    AdaptiveManufacturingPlanner() = default;

    AdaptiveManufacturingPlan plan_stock_fallback() const;
};

} // namespace Slic3r

#endif
