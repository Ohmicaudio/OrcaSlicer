# Snapmaker U1 Innovation Fund — Form Answers (Final)

**Program:** U1 Innovation Fund, Phase 1
**Phase 1 deadline:** September 7, 2026
**Submission portal:** https://www.snapmaker.com/innovation-fund
**Pre-submission contact:** community@snapmaker.com
**Prepared:** 2026-06-29

> These are final, copy-ready answers for the Innovation Fund form. Fill the bracketed placeholders (name, repo URL, contact) before submitting. Wording deliberately avoids implying that any behavior-changing slicer code exists today.

---

## Project name

Adaptive Manufacturing Planner (AMP) for Snapmaker Orca

*(Earlier drafts used "Adaptive Nozzle Strategy for U1." We renamed it to "Adaptive Manufacturing Planner" so reviewers and users do not read it as physical nozzle morphing. AMP plans manufacturing strategy — effective widths now, and later physical tool selection — it does not change a nozzle's physical diameter.)*

## Project URL

https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy

Happy to share the repository and design docs directly with the Snapmaker team ahead of the formal form if that is preferred.

## Category

Slicer / software.

Secondary, applicable to Stage 2 only: hardware-validated workflow (mixed physical nozzles on U1).

## Short description (one to two sentences)

An open-source Snapmaker Orca planning layer that is being developed toward geometry-aware region classification and manufacturing planning, so that exterior detail can be preserved while inner walls and infill use wider effective line widths where it is safe. Stage 1 is a lower-risk software-only validation path that reuses existing line-width settings and Arachne; a later stage explores physical mixed-nozzle U1 workflows and is blocked on U1 hardware validation.

## Problem statement

FDM slicing usually treats nozzle diameter and line width as static, whole-print profile choices, forcing one tradeoff between detail, strength, and print time across an entire part. The U1's multi-toolhead design makes role-specific manufacturing strategy worth exploring: different regions of the same part have different needs (visible detail vs. bulk structure), and could be matched to different effective widths now, or different physical nozzles later after validation.

## Proposed solution

AMP introduces an optional, separable planning layer in Snapmaker Orca that observes already-sliced layer/region geometry and emits explainable recommendations. It is staged to keep risk and review burden low:

- **Stage 1 — Adaptive bead widths (software-only).** Preserve exterior/cosmetic detail; allow wider effective widths for inner walls and infill where confidence is high. This is a **lower-risk software-only validation path**: it reuses Snapmaker Orca's existing line-width/Arachne mechanisms (role-specific line-width settings and Arachne's outer/inner bead-width inputs, `bead_width_0` / `bead_width_x`) rather than introducing new toolpath logic, makes **no behavior change while disabled**, and makes **no strength or print-quality claims from preview alone**.
- **Stage 2 — Adaptive nozzle selection (U1 hardware-backed).** Small nozzles for visible detail; larger nozzles for inner shells, infill, and supports. **Blocked until U1 hardware access** — disabled and hidden, with **no safety bypasses** and **no mixed-nozzle claims before physical validation**, until real prints, nozzle/toolhead state, tool-change cost, and purge behavior are measured.
- **Stage 3 — Manufacturing optimization (longer-term).** Future cost-aware planning and optimization across detail, structure, cosmetic visibility, tool access, tool-change cost, and predicted time savings.

The first code milestone is deliberately minimal: a hidden experimental configuration flag (`adaptive_manufacturing_enable`, default `false`) and a no-op planner scaffold. With the flag off, generated output is equivalent to stock. Behavior-changing logic comes only after the read-only extension points are validated.

## Current status (what exists today)

This is a design-and-validation stage, not a behavior-changing release. AMP does **not** yet perform geometry partitioning or generate behavior-changing G-code. Completed or in-progress deliverables:

- v0.1 and v0.2 architecture/design specifications.
- Read-only prototype implementation plan (hidden flag → value types → stock fallback → debug artifact → tests).
- Project risk register (v0.2), including a concurrency finding from reading the real codebase.
- Profile-only test plan and a benchmark suite defining repeatable validation levels.
- A code-grounded integration map identifying the safe observation points in Snapmaker Orca.

## What we are requesting from Snapmaker

1. **U1 hardware access** for Stage 2 validation (mixed physical nozzles).
2. **Nozzle/toolhead state guidance** — how slicer-side code can read or validate the printer's known nozzle/toolhead state, so AMP can cooperate with, never bypass, existing validation.
3. **Guidance on tool-change and purge behavior** needed to model swap cost honestly.
4. Confirmation that this scope fits Phase 1, and the preferred channel for sharing the repository before the formal form.

Stage 1 and the read-only prototype proceed in software with or without hardware; the request specifically unblocks the physical work that cannot be proven any other way.

## Deliverables we will produce

- Public fork or companion repository with all design docs and the read-only prototype.
- Hidden experimental flag plus no-op planner scaffold (first reviewable PR).
- Read-only planner that emits debug/region/scoring artifacts with no toolpath or G-code change.
- Profile-only G-code comparison notes across stock vs. experimental U1 profiles.
- Benchmark results separated strictly by validation level so diagnostics are never conflated with behavior change.
- If U1 access is granted: a Stage 2 hardware validation report covering nozzle state, tool-change/purge cost, and measured outcomes.

## Timeline (indicative, from grant of access)

- **Weeks 0–3:** Hidden flag + no-op value-type scaffold + unit tests; profile-only Level 0/Level 1 benchmark pass.
- **Weeks 3–8:** Read-only planner emitting debug artifacts; geometry scoring; equivalence tests proving disabled and read-only output match stock.
- **Stage 2 (gated on U1 access):** Hardware bring-up, nozzle-state/tool-change/purge measurement, then a validation report. No mixed-nozzle behavior is enabled before this completes.

## Safety and risk posture

- **No safety-check bypasses.** AMP does not modify or bypass Snapmaker nozzle-mismatch checks, firmware safety behavior, or device-validation paths such as `CalibUtils.cpp`. It works only through declared configuration and existing validated toolpath-generation interfaces, preserving job metadata and validation behavior.
- **Disabled means unchanged.** Everything is gated by a default-off hidden flag; stock behavior is the fallback whenever confidence is low or geometry analysis is unavailable.
- **Hardware claims are gated.** No strength, surface-quality, dimensional, bonding, purge, or mixed-nozzle claims are made before real U1 prints.
- **Maintainer-friendly by construction.** Self-contained files, append-only edits to shared code, small staged PRs. We are not proposing a large, invasive patch — this is a lower-risk software-only validation path and staged, reviewable engineering with explicit guardrails.

## Why Snapmaker / why U1

Snapmaker Orca already contains the right U1-specific foundation: U1 process profiles, nozzle-diameter variants, nozzle validation, and calibration/device integration. AMP builds on that foundation instead of replacing it, and the U1's multi-toolhead design is what makes role-specific manufacturing strategy worth validating on real hardware.

The business case:

- **Demonstrate the U1 as a practical multi-tool manufacturing platform.** AMP makes the multi-toolhead design usable as a role-aware manufacturing workflow, not just a static profile choice.
- **Validate on real functional parts.** Benchmarks use functional, inspectable components (speaker adapters, LED rings, amplifier mounts, trim, fabrication fixtures), not decorative test cubes.
- **Open-source documentation and community feedback.** All design docs, the risk register, and the validation methodology are public so Snapmaker maintainers and the community can review and shape the direction early.

## Applicant

- **Name:** *[applicant name]*
- **Organization:** Ohmic Audio Labs (functional benchmark parts: speaker adapters, LED rings, amplifier mounts, trim, fabrication fixtures)
- **Contact:** support@ohmicaudio.com
