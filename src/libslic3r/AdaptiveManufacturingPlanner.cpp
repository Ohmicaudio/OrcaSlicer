#include "AdaptiveManufacturingPlanner.hpp"

namespace Slic3r {

AdaptiveManufacturingPlan AdaptiveManufacturingPlanner::plan_stock_fallback() const
{
    return make_stock_fallback_plan();
}

} // namespace Slic3r
