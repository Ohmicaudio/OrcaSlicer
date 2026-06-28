# U1 Adaptive Nozzle Strategy

## Goal

Explore a U1-focused slicer workflow that preserves fine visible detail while using wider extrusion where detail matters less. The software-first version treats "adaptive nozzle diameter" as adaptive effective line width. The hardware-backed version tests U1 toolheads fitted with different physical nozzle diameters for role-specific printing.

## Why Start With Line Width

Changing physical nozzle diameter during a print is a hardware and firmware problem. Orca already has the safer first layer of this idea: role-specific extrusion widths and Arachne variable-width wall generation. U1 profiles also already define 0.2, 0.4, 0.6, and 0.8 nozzle families, so the project can start by comparing line-width strategies before requiring U1 hardware access.

## Current U1 Profile Facts

- `resources/profiles/Snapmaker/machine/Snapmaker U1.json` declares `nozzle_diameter` as `0.2;0.4;0.6;0.8`.
- `resources/profiles/Snapmaker/process/fdm_process_U1.json` defines the base 0.4-ish process widths:
  - `outer_wall_line_width`: `0.42`
  - `line_width`: `0.45`
  - `sparse_infill_line_width`: `0.45`
  - `inner_wall_line_width`: `0.45`
  - `internal_solid_infill_line_width`: `0.45`
  - `support_line_width`: `0.42`
  - `top_surface_line_width`: `0.42`
- `resources/profiles/Snapmaker/process/fdm_process_U1_common.json` currently sets `wall_generator` to `classic`.
- U1-specific process variants exist for 0.2, 0.4, 0.6, and 0.8 nozzle workflows.

## Recommended Prototype Order

### 1. Profile-Only Proof

Create an experimental U1 0.4 profile that changes effective line widths by role:

- Keep outer walls and top surfaces near the visible-detail width.
- Increase inner wall and infill widths where surface detail is less important.
- Enable Arachne for wall generation if preview and G-code output remain stable.
- Compare print time estimates and generated toolpaths against the stock `0.20 Standard @Snapmaker U1 (0.4 nozzle)` profile.

This can be tested without a printer by generating and inspecting G-code.

### 2. Arachne-Focused Slicer Prototype

If the profile-only proof is promising, add an experimental setting group that modifies wall bead width inputs before Arachne generates walls.

Likely code starting points:

- `src/libslic3r/Arachne/WallToolPaths.cpp`
- `src/libslic3r/Arachne/WallToolPaths.hpp`
- `src/libslic3r/Arachne/BeadingStrategy/BeadingStrategyFactory.cpp`
- `src/libslic3r/Flow.cpp`
- `src/libslic3r/Flow.hpp`

The first code prototype should affect walls only. It should avoid firmware assumptions and should not bypass nozzle mismatch safety checks.

### 3. Mixed Physical Nozzle Workflow

When U1 hardware is available, test role assignment using toolheads with different nozzle diameters:

- Small nozzle: outer walls, fine features, text, visible top detail.
- Medium/large nozzle: inner walls, sparse infill, internal solid infill, support.

This phase must measure purge/toolchange overhead, nozzle mismatch behavior, pressure/flow calibration, seams, dimensional accuracy, and wall bonding.

## Risks

- Wider internal extrusion may reduce detail, create overfill, or alter wall bonding.
- Arachne and classic wall generation may respond differently to role-specific widths.
- Mixed physical nozzles may lose more time to toolchanges and purge than they save.
- Printer-side nozzle validation may prevent unsafe mixed-nozzle jobs unless configured cleanly.

## Snapmaker Innovation Fund Angle

This project fits the U1 Innovation Fund as a slicer/software workflow first, with optional hardware-modification validation. The funding ask should be U1 access plus nozzle/toolhead support for responsible mixed-nozzle testing.

