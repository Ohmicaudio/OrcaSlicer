# AMP LixNix Collaboration Draft

Draft message for a GitHub issue, discussion, or direct contact with the maintainer of:

<https://github.com/LixNix/OrcaSlicer-multi-nozzle-size-printing>

```text
Hi,

I am working on an open-source Adaptive Manufacturing Planner branch for Snapmaker Orca:

https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy

AMP is exploring resolution allocation for FDM/FFF: preserve fine visible/detail regions, use coarser bead/layer/tool strategies only where the geometry and cost model make sense, and keep physical mixed-nozzle behavior blocked until hardware constraints are validated.

I audited your OrcaSlicer multi-nozzle fork and found the nozzle_diameter_for_filament work and the multi_nozzle_multi_layer_height branch especially relevant. The per-extruder layer-height, combined-layer region, support_nozzle_diameter, tool ordering, and wipe tower changes are exactly the kind of implementation detail we need to understand before any future behavior-changing AMP integration.

A few questions, if you are open to comparing notes:

1. Is the intended workflow manual per-feature/per-filament assignment, or are you also planning automated geometry-driven nozzle assignment?
2. Do the new per-extruder layer-height and support nozzle settings persist cleanly through 3MF/project save/load?
3. Do you have sample projects or generated G-code that demonstrate 0.4/0.6 or other mixed nozzle combinations?
4. Have you physically tested the branch on H2D/X2D or other hardware, or is it currently source/test validation only?
5. Are there specific edge cases around wipe tower, support, or combined layers that you already know need more testing?

For AMP, I am keeping this as research only for now. I am not merging or copying code into the Snapmaker branch. The immediate goal is to understand the implementation shape and make sure our planner/packet/adapter architecture stays compatible with real slicer constraints.

Thanks for publishing the work. It is useful prior art either way.
```
