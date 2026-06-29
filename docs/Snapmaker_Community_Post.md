# Snapmaker Community Post Draft

Title:

Adaptive Manufacturing Planner for U1: bead widths first, mixed nozzles later

Post:

I've started an open-source Snapmaker U1 slicer project called **Adaptive Manufacturing Planner**.

Project branch:
https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy

The goal is to explore a safer, staged way to balance detail, strength, and print time on the U1.

### Stage 1: Adaptive bead-width planning

Software-only. The first focus is using existing slicer mechanisms, including role-specific line widths and Arachne-style wall generation, to preserve visible exterior detail while allowing wider internal walls or infill where appropriate.

### Stage 2: Adaptive nozzle selection

U1 hardware-backed. This would test workflows where different U1 toolheads use different physical nozzle diameters, such as a smaller nozzle for exterior detail and a larger nozzle for inner shells, infill, or support.

This stage is intentionally blocked until real U1 hardware validation is available. I do not intend to bypass nozzle mismatch checks, calibration paths, firmware safety behavior, or Snapmaker validation logic.

### Stage 3: Manufacturing optimization

Longer-term, the planner could consider region detail, structural importance, cosmetic visibility, tool-change cost, and predicted time savings.

Current branch status:

- Hidden developer config flag exists.
- Stock fallback planner value types exist.
- No-op planner facade exists.
- Sidecar cache value types exist.
- Debug artifact value types, serializer, and standalone writer exist.
- Observation summary and observation-to-debug mapping scaffolds exist.
- Focused AMP tests pass.
- No production slicer path consumes AMP yet.
- No G-code, Arachne, Flow, LayerRegion, PerimeterGenerator, profile, UI, or Snapmaker validation behavior has been changed.

I'm looking for feedback from U1 users and Snapmaker maintainers:

- Which models would make good test cases?
- Which failure modes should this planner avoid first?
- Would mixed physical nozzle sizes be useful on U1 if toolchange and purge overhead are controlled?
- What nozzle combinations would actually be useful: 0.2/0.4, 0.4/0.8, 0.2/0.8, or something else?
- Are there U1-specific calibration or nozzle-state constraints this project should account for early?

The goal is a reproducible, open project that can eventually be reviewed for Snapmaker Orca compatibility.
