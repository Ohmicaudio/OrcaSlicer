# Adaptive Manufacturing Planner (AMP) — One-Page Project Summary

**For:** Snapmaker U1 Innovation Fund, Phase 1
**Project:** Adaptive Manufacturing Planner (AMP) for Snapmaker Orca
**Working title note:** Earlier drafts used "Adaptive Nozzle Strategy." We have standardized on "Adaptive Manufacturing Planner" so the work is not mistaken for physical nozzle morphing — AMP plans manufacturing strategy; it does not change a nozzle's physical diameter.
**Category:** Slicer / software (secondary: hardware-validated workflow, Stage 2 only)
**Repository:** https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy

---

## The problem

Most FDM slicing treats nozzle diameter and line width as static, whole-print profile choices. A small setting preserves exterior detail but slows the print; a large setting prints faster and stronger but coarsens visible surfaces. The U1's multi-toolhead design makes this tradeoff unusually interesting: different roles in the *same* part could, in principle, be matched to different effective widths or — later, and only after hardware validation — different physical nozzles.

## What AMP is

AMP is a planning/decision layer for Snapmaker Orca that **is being developed toward geometry-aware region classification and manufacturing planning**: a separate, optional module that observes already-sliced layer and region geometry and produces explainable recommendations (region descriptions, scores, confidence, reason codes). It is designed so that, when disabled, generated output is unchanged, and so that early milestones produce **diagnostics only** — no toolpath or G-code changes.

AMP does **not** today perform geometry partitioning or generate behavior-changing G-code. The current work is design, risk analysis, a profile-only validation methodology, and a code-grounded architecture plan.

## Staged plan

- **Stage 1 — Adaptive bead widths (software-only).** Preserve exterior/cosmetic detail while allowing wider effective widths for inner walls and infill where confidence is high. This is a **lower-risk software-only validation path**: it reuses Snapmaker Orca's existing line-width/Arachne mechanisms (existing role-specific line-width settings and Arachne's outer/inner bead-width inputs) rather than introducing new toolpath logic, makes **no behavior change while disabled**, and makes **no strength or print-quality claims from preview alone**.
- **Stage 2 — Adaptive nozzle selection (U1 hardware-backed).** Evaluate small nozzles for visible detail and larger nozzles for inner shells, infill, and supports. **Stage 2 is blocked until U1 hardware access**, stays disabled and hidden, uses **no safety bypasses**, and makes **no mixed-nozzle claims before physical validation** — until real U1 prints, nozzle/toolhead state, tool-change cost, and purge behavior are measured.
- **Stage 3 — Manufacturing optimization (longer-term).** Future cost-aware planning and optimization that balances detail, structure, cosmetic visibility, tool access, tool-change cost, and predicted time savings across regions.

## Safety and maintainability posture

- **No safety-check bypasses.** AMP does not modify or bypass Snapmaker nozzle-mismatch checks, firmware safety behavior, or device-validation paths (e.g. `CalibUtils.cpp`). It operates only through declared configuration and existing validated interfaces.
- **Off means off.** A hidden experimental flag (`adaptive_manufacturing_enable`, default `false`) gates everything; disabled output is equivalent to stock.
- **Upstream-friendly.** New code lives in self-contained files; edits to shared files are append-only. The first code PR is a hidden flag plus a no-op scaffold — small and easy to review.
- **No overstated claims.** No strength, quality, dimensional, bonding, or mixed-nozzle claims are made before real U1 validation. This is a lower-risk software-only validation path and staged engineering — not an acceleration pitch.

## Why this matters for U1

- **Demonstrate the U1 as a practical multi-tool manufacturing platform.** AMP turns the U1's multi-toolhead design into a concrete, role-aware workflow rather than a static whole-print profile choice.
- **Validate on real functional parts.** Benchmarks use functional, inspectable components (speaker adapters, LED rings, amplifier mounts, trim, fabrication fixtures) — not decorative test cubes.
- **Open-source documentation and community feedback.** All design docs, risk registers, and validation methodology are public so Snapmaker maintainers and the community can review and steer the work.

## What we are requesting

U1 hardware access, and where possible nozzle/toolhead state guidance, so **Stage 2** can be validated responsibly. Stages 1 and the read-only prototype proceed in software regardless; hardware unblocks the physical mixed-nozzle research that cannot be proven any other way.
