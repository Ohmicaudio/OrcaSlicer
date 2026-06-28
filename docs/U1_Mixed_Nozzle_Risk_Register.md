# U1 Mixed Nozzle Risk Register

## Scope

This register covers Stage 2: adaptive nozzle selection with U1 toolheads using different physical nozzle diameters. It is intentionally separate from Stage 1 adaptive bead-width work.

## Risks

### R1: Nozzle Mismatch Safety

- Risk: The slicer profile and printer memorized nozzle state disagree.
- Impact: Failed print start, wrong extrusion assumptions, or unsafe user workflow.
- Mitigation: Do not bypass checks in `src/slic3r/Utils/CalibUtils.cpp` or Snapmaker device validation paths. Mixed-nozzle mode must work with official nozzle state.

### R2: Toolchange Overhead Exceeds Savings

- Risk: Purge, wipe, heating, and motion overhead erase gains from larger nozzles.
- Impact: Slower prints despite complex planning.
- Mitigation: Planner must estimate toolchange cost and require minimum region size/time savings before assigning a different nozzle.

### R3: Purge And Contamination

- Risk: Mixed nozzle/material assignments increase purge needs or create contamination.
- Impact: Surface defects, clogs, weak bonding.
- Mitigation: Defer physical mixed-nozzle claims until U1 tests measure purge volume and wipe reliability.

### R4: Flow Calibration Per Nozzle

- Risk: Different nozzle sizes require different flow, pressure advance, and temperature behavior.
- Impact: Over/under-extrusion and inconsistent walls.
- Mitigation: Treat each nozzle/tool as separately calibrated; document required calibration steps.

### R5: Wall Bonding Between Width Regimes

- Risk: Small outer beads and large inner beads may bond poorly or leave voids.
- Impact: Weak shells or visible artifacts.
- Mitigation: Stage 1 tests must inspect outer/inner wall adjacency. Hardware tests must include strength and cross-section inspection.

### R6: Thin Feature Loss

- Risk: Planner assigns a wide nozzle or bead to geometry that cannot support it.
- Impact: Lost details or dimensional errors.
- Mitigation: Low local feature-size confidence must force small/no-change behavior.

### R7: Arachne Edge Cases

- Risk: Arachne variable-width logic may behave unexpectedly when fed aggressive outer/inner width differences.
- Impact: Missing paths, too many transitions, unstable preview.
- Mitigation: Start with conservative width scales and synthetic regression geometry.

### R8: User Mental Model

- Risk: Users misunderstand "adaptive nozzle" as physical nozzle morphing.
- Impact: Wrong expectations and unsafe setup.
- Mitigation: Public language should use "Adaptive Manufacturing Planner" and distinguish bead width planning from physical nozzle selection.

### R9: Upstream Acceptance

- Risk: A large planner patch is too invasive for Snapmaker Orca maintainers.
- Impact: Harder review and maintenance.
- Mitigation: Stage code behind a hidden flag, keep planner files separate, and land no-op/config scaffolding before algorithms.

### R10: No U1 Access

- Risk: Hardware-specific stages cannot be validated.
- Impact: Stage 2 remains speculative.
- Mitigation: Submit to Snapmaker Innovation Fund requesting U1 access and nozzle/toolhead support.

## Current Recommendation

Do not implement mixed physical nozzle behavior until:

- U1 access is available.
- Nozzle state APIs/checks are understood.
- Toolchange/purge cost can be measured.
- Stage 1 bead-width tests produce stable results.

