# Snapmaker Community Post Draft

Title:

Adaptive Manufacturing Planner for U1: bead widths first, mixed nozzles later

Post:

I am starting an open-source Snapmaker U1 slicer project tentatively called Adaptive Manufacturing Planner.

The idea is to explore a cleaner way to balance detail, strength, and print time on U1:

1. Stage 1: Adaptive bead widths
   - Software-only.
   - Preserve visible exterior detail.
   - Use wider internal walls or infill where it is safe.
   - Start from Snapmaker Orca and Arachne rather than rewriting a wall generator.

2. Stage 2: Adaptive nozzle selection
   - U1 hardware-backed.
   - Test workflows where different toolheads use different nozzle sizes.
   - Example: small nozzle for exterior detail, larger nozzle for inner shells or infill.

3. Stage 3: Manufacturing optimization
   - Longer-term planner that considers region detail, structural importance, visibility, tool-change cost, and print-time savings.

I have started by inspecting Snapmaker's Orca fork, not generic upstream Orca, because Snapmaker's fork already contains U1 profiles, nozzle validation, calibration paths, and device integration. The first work is documentation and a profile-only experiment. No safety checks are being disabled.

The initial technical finding is promising: Arachne already separates the first/outer wall bead width from subsequent/inner wall bead width through `bead_width_0` and `bead_width_x`. That gives us a practical software-only starting point before touching hardware.

I am looking for feedback from U1 users and Snapmaker maintainers:

- Which models would be good test cases?
- Which print failures should this planner avoid first?
- Would mixed nozzle sizes on U1 be useful if toolchange/purge overhead is controlled?
- What nozzle combinations are most realistic for U1 users?

The goal is a reproducible, open project that can eventually be reviewed for upstream Snapmaker Orca compatibility.

