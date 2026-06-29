# AMP Hardware Tiers and Resolution Allocation

## Purpose

Adaptive Manufacturing Planner (AMP) should be positioned as a general FDM/FFF resolution-allocation planning layer.

Snapmaker U1 is the first submitted validation platform because this branch is based on Snapmaker Orca and was submitted to the U1 Innovation Fund. That does not make AMP a U1 only project. The same planning idea can help ordinary single-nozzle printers, multi-material systems, IDEX machines, toolchangers, and future mixed-nozzle platforms when each platform's capabilities and safety constraints are represented explicitly.

## Core Philosophy

AMP is about resolution allocation.

Preferred shorthand:

```text
Spend resolution only where it earns its keep.
```

The end-user goal is the smallest controlled repeatable detail in X/Y/Z where that detail is actually needed.

The goal is not pure speed. The goal is also not giving up speed everywhere just to preserve detail somewhere. The planner should eventually help separate visible detail, structural regions, support-critical regions, and internal bulk so each region can use an appropriate manufacturing strategy.

## Hardware Tier Model

### Tier 1: Single-Nozzle FDM/FFF

Tier 1 covers ordinary single-nozzle printers and should remain useful even without toolchanging hardware.

Potential AMP capabilities:

- adaptive bead width;
- role-specific line width;
- adaptive layer height;
- visible-surface preservation;
- internal/bulk region planning;
- profile-only Arachne experiments;
- conservative fallback behavior.

This tier is useful immediately for ordinary printers because it can explore how much resolution is needed in each region using existing slicer mechanisms before any physical tool assignment exists.

Stage 1 belongs here: profile-only effective-width characterization using existing role-specific line-width settings and Arachne.

### Tier 2: Multi-Material / IDEX / Support-Tool Workflows

Tier 2 covers systems that can assign different materials, extruders, support tools, or colors without assuming different physical nozzle diameters.

Potential AMP capabilities:

- support interface assignment;
- material-specific regions;
- color and visible-surface regions;
- soluble or breakaway support region planning;
- cosmetic surface planning;
- tool-accessibility and toolchange-cost awareness.

This tier does not require any mixed physical nozzle assumption. It can benefit from the same region classification and visibility planning as Tier 1.

### Tier 3: Toolchanger / Mixed-Nozzle Systems

Tier 3 covers systems where physical tools or nozzle diameters may differ.

Potential AMP capabilities:

- physical tool/nozzle assignment;
- small nozzle for visible detail;
- large nozzle for internal/bulk structure;
- toolchange and purge cost modeling;
- hardware-specific calibration and safety validation;
- bonding and seam-risk validation.

This tier requires hardware-specific validation. It must not be claimed as working from preview, profile-only slicing, or value-type scaffolding.

## U1 Relationship

U1 remains the first concrete validation target because:

- this branch is based on Snapmaker Orca;
- the project was submitted to the U1 Innovation Fund;
- U1 has a multi-tool architecture that makes future validation technically interesting;
- Snapmaker-specific profile, nozzle-state, calibration, purge, and validation paths need project-specific review.

The existing U1-specific docs remain valid:

- `docs/U1_Profile_Only_Test_Plan.md`
- `docs/U1_Mixed_Nozzle_Risk_Register.md`

U1 mixed physical nozzle behavior remains blocked until U1 hardware validation is possible. That validation must cover nozzle-state behavior, calibration assumptions, toolchange and purge cost, seam behavior, wall bonding, and Snapmaker validation paths.

The architecture should avoid hard-coding U1 only assumptions where possible. U1 should be treated as the first platform adapter and validation path, not the definition of AMP itself.

## Other Platform Relevance

AMP should be portable conceptually to other FDM/FFF slicer ecosystems.

Single-nozzle users still benefit from Stage 1 because role-specific line widths, Arachne behavior, adaptive layer height, and preview/G-code inspection can be characterized without any multi-tool behavior.

Toolchanger support should be implemented behind platform capability adapters. A future adapter can describe:

- available tools;
- whether tools can use different physical nozzle diameters;
- per-tool material constraints;
- calibration assumptions;
- purge and wipe behavior;
- safety checks;
- printer-side validation behavior.

Platform adapters should prevent the core planner from assuming that a U1, IDEX machine, Bambu printer, Prusa toolchanger, Voron toolchanger, or any other machine has the same capabilities or safety constraints.

## Sequencing Rationale

The safest sequence is:

1. Start with single-nozzle/profile-only bead-width and layer-height characterization.
2. Collect models that expose visible detail, internal bulk, supports, top surfaces, text, badges, rings, and sloped surfaces.
3. Run physical proxy tests on available printers, including Bambu hardware where useful.
4. Do not claim Bambu tests validate U1 mixed-nozzle behavior.
5. Use U1 hardware later for U1-specific nozzle-state, calibration, toolchange, purge, and bonding validation.

Proxy tests can help characterize general FDM/FFF behavior, such as where wider effective widths look plausible or where visible detail degrades. They cannot validate U1-specific mixed physical nozzle behavior.

## Public Wording

Preferred phrase:

```text
Adaptive Manufacturing Planner is a FDM/FFF resolution-allocation planning layer. Snapmaker U1 is the first submitted validation platform.
```

Avoid framing AMP as:

- a U1 only mixed-nozzle slicer;
- a speed-first optimizer;
- working mixed-nozzle support.

Better public framing:

- Stage 1 is useful for ordinary single-nozzle printers because it studies profile-only effective-width behavior and visible-detail preservation.
- U1 is the first submitted validation platform because the public branch is based on Snapmaker Orca.
- Toolchanger and mixed-nozzle work is a future hardware-specific tier, not a current claim.

## Cross-References

- `docs/AMP_Branch_Status.md`
- `docs/U1_Profile_Only_Test_Plan.md`
- `docs/U1_Mixed_Nozzle_Risk_Register.md`
- `docs/design/AMP_Surface_Color_Planner_Design.md`

Optional future cross-reference when present:

- `docs/benchmarks/AMP_Resolution_Control_and_Proxy_Characterization.md`
