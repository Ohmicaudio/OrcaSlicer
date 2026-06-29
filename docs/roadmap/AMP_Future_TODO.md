# AMP Future TODO

## Purpose

This document collects the next useful Adaptive Manufacturing Planner (AMP) work after the Snapmaker submission, public forum post, support-ticket submission, and Stage 1 profile-only benchmark package.

The goal is to keep momentum organized without drifting into behavior-changing slicer work too early.

AMP should be framed as a FDM/FFF resolution-allocation planning layer. Snapmaker U1 is the first submitted validation platform, not the only possible platform.

## Current Ground Rules

- Do not modify production slicer behavior without an explicit future milestone.
- Do not wire AMP into `PrintObject`, `LayerRegion`, `Flow`, `PerimeterGenerator`, Arachne, G-code export, UI, profiles, Snapmaker validation, or `CalibUtils.cpp`.
- Do not consume `adaptive_manufacturing_enable` from production slicing paths yet.
- Do not claim print-time, strength, print quality, dimensional, bonding, or mixed-nozzle improvements without measured hardware results.
- Keep Stage 2 physical mixed-nozzle behavior blocked until U1 hardware validation and Snapmaker guidance are available.
- Keep the architecture portable where possible: single-nozzle Stage 1 work should remain useful without U1 hardware, and future toolchanger work should be guarded by platform-specific capability assumptions.

## Hardware Tier Framing

Use:

- `docs/design/AMP_Hardware_Tiers_and_Resolution_Allocation.md`

Public framing:

```text
Adaptive Manufacturing Planner is a FDM/FFF resolution-allocation planning layer. Snapmaker U1 is the first submitted validation platform.
```

Working tiers:

- Tier 1: single-nozzle FDM/FFF profile-only bead-width, role-specific line-width, visible-surface, internal/bulk, and adaptive-layer-height characterization.
- Tier 2: multi-material, IDEX, support-tool, material-region, and color/surface-region planning without mixed physical nozzle assumptions.
- Tier 3: toolchanger and mixed-nozzle systems with hardware-specific validation.

## Immediate Public-Facing TODOs

### 1. Collect Stage 1 Benchmark Models

Status: open

Use:

- `docs/benchmarks/AMP_Stage1_Profile_Only_Benchmark_Run_001.md`
- `docs/benchmarks/models_needed.md`

Tasks:

- Ask the Snapmaker forum for candidate models.
- Ask U1 users for functional parts that are safe to inspect publicly.
- Collect source URLs, licenses, units, and expected stress features.
- Prefer functional models over novelty benchmark toys.
- Keep all benchmark requests clear that this is profile-only validation.
- Make clear that Stage 1 is useful beyond U1 because single-nozzle profile-only characterization is part of the core AMP resolution-allocation path.

### 2. Run Profile-Only Benchmark Pass

Status: pending model selection

Tasks:

- Slice each selected model with the stock Snapmaker U1 0.4 mm profile.
- Slice each selected model with the experimental effective-width profile.
- Record slicer-estimated time, filament, warnings, preview observations, and G-code/path observations.
- Do not claim real print-time improvement from slicer estimates alone.
- Do not claim strength or print quality improvements from preview.

### 3. Track Snapmaker Support Response

Status: awaiting response

Tasks:

- Watch `support@ohmicaudio.com` for Snapmaker support replies.
- Save engineering-relevant guidance in a follow-up record.
- If Snapmaker answers mixed-nozzle feasibility questions, update the risk register and Stage 2 blockers.
- Do not turn support guidance into behavior-changing code without a new design milestone.

### 4. Keep Community Thread Active

Status: active

Tasks:

- Respond to technical questions with public branch, current behavior-neutral state, and benchmark model request.
- Avoid repeating the whole project pitch in every reply.
- Point people to the benchmark package when asking for models.
- Keep mixed physical nozzle claims conditional on future U1 hardware validation.

## Near-Term Docs TODOs

### Benchmark Results Template

Create a result log after the first model set is selected:

- `docs/benchmarks/AMP_Stage1_Profile_Only_Results_Run_001.md`

It should include one record per model and must distinguish:

- slicer estimate;
- preview observation;
- G-code/path observation;
- unavailable physical print observation.

### Support Response Record

Create after Snapmaker replies:

- `docs/submission/Snapmaker_Support_Response_Record.md`

It should include:

- date received;
- reply summary;
- any explicit U1 constraints;
- any unclear statements needing follow-up;
- impact on Stage 2 blockers.

### Public Progress Update

After benchmark models are selected or first results exist, create:

- `docs/community/AMP_Public_Update_001.md`

It should summarize what changed without overclaiming.

## Next Safe Code Milestones

These remain future milestones and should not start until public submission follow-up and Stage 1 benchmark planning are stable.

### 1. Developer-Only Debug Enablement Design

Docs first. Define how a future developer-only option would explicitly request in-memory debug artifacts without changing G-code or default behavior.

Required constraints:

- no default filesystem output;
- no production debug writing;
- no writes inside `PrintObject::make_perimeters()` parallel loops;
- no `LayerRegion::make_perimeters()` debug writes;
- serial and deterministic first observation path.

### 2. PrintObject Sidecar Integration Design Review

Before implementation, re-review:

- `docs/design/AMP_PrintObject_Sidecar_Cache_Design.md`
- `docs/code_maps/AMP_ReadOnly_Integration_Map.md`
- `docs/risks/AMP_Project_Risk_Register_v0.2.md`

Output should be a go/no-go checklist, not code.

### 3. Read-Only Observation Hook Prototype

Future code only after design review.

Must remain:

- developer-only;
- read-only;
- serial and deterministic;
- no G-code change;
- no toolpath change;
- no profile default change;
- no Snapmaker validation bypass.

## Surface Color Planner Track

Status: future extension track

Use:

- `docs/design/AMP_Surface_Color_Planner_Design.md`

Next docs-only steps:

- Create a surface color value-type design.
- Create a safe public explanation separating optical blending from true pigment mixing.
- Keep FullSpectrum-style surface color as an extension track, not part of the submitted mixed-nozzle AMP promise.
- Treat this as Tier 2-style visible-surface planning: color/surface regions, skins, logos, text, badges, and trim can use the same "where does detail matter?" region logic without assuming physical mixed-nozzle printing.

Do not implement local-Z, FullSpectrum interop, UI, or G-code behavior yet.

## Stage 2 Mixed Physical Nozzle Track

Status: blocked

Blocked on:

- U1 hardware access.
- Snapmaker guidance on nozzle-state validation.
- Toolhead/nozzle calibration behavior.
- Toolchange and purge/wipe cost.
- Wall bonding and seam behavior.
- Safe test model selection.

No mixed physical nozzle behavior should be claimed or implemented until these are understood.

When this track resumes, model it as platform-specific toolchanger capability work, not as U1 only core planner logic.

## Maintenance TODOs

- Keep `docs/AMP_Branch_Status.md` updated after code scaffolds or major docs packages.
- Keep old non-final submission drafts uncommitted unless cleaned.
- Run the standard AMP overclaim scan before public-facing commits. Keep the scan pattern in task notes or command history, not in committed docs, so the scan does not match its own documentation.

- Refresh the public branch after useful docs or verified code scaffolds:

```powershell
git push public u1-adaptive-nozzle-strategy
```
