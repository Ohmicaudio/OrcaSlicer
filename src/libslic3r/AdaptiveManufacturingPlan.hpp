#ifndef slic3r_AdaptiveManufacturingPlan_hpp_
#define slic3r_AdaptiveManufacturingPlan_hpp_

#include <vector>

namespace Slic3r {

enum class AdaptiveManufacturingReason {
    StockFallback
};

struct AdaptiveRegionScore
{
    double confidence = 0.0;

    bool operator==(const AdaptiveRegionScore &rhs) const;
};

struct AdaptiveRegionPlan
{
    AdaptiveManufacturingReason reason = AdaptiveManufacturingReason::StockFallback;
    AdaptiveRegionScore         score;
    bool                        requires_toolchange = false;
    double                      bead_width_override = 0.0;
    double                      nozzle_diameter_override = 0.0;

    bool operator==(const AdaptiveRegionPlan &rhs) const;
};

struct AdaptiveManufacturingPlan
{
    std::vector<AdaptiveRegionPlan> regions;

    bool operator==(const AdaptiveManufacturingPlan &rhs) const;
};

AdaptiveManufacturingPlan make_stock_fallback_plan();

} // namespace Slic3r

#endif
