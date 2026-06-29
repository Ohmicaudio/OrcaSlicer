#include "AdaptiveManufacturingPlan.hpp"

namespace Slic3r {

bool AdaptiveRegionScore::operator==(const AdaptiveRegionScore &rhs) const
{
    return this->confidence == rhs.confidence;
}

bool AdaptiveRegionPlan::operator==(const AdaptiveRegionPlan &rhs) const
{
    return this->reason == rhs.reason
        && this->score == rhs.score
        && this->requires_toolchange == rhs.requires_toolchange
        && this->bead_width_override == rhs.bead_width_override
        && this->nozzle_diameter_override == rhs.nozzle_diameter_override;
}

bool AdaptiveManufacturingPlan::operator==(const AdaptiveManufacturingPlan &rhs) const
{
    return this->regions == rhs.regions;
}

AdaptiveManufacturingPlan make_stock_fallback_plan()
{
    AdaptiveManufacturingPlan plan;
    plan.regions.emplace_back();
    return plan;
}

} // namespace Slic3r
