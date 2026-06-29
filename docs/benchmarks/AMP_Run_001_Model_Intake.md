# AMP Run 001 Model Intake

## Goal

Collect practical Snapmaker U1 model candidates and failure cases for Adaptive Manufacturing Planner (AMP) Stage 1 benchmark Run 001.

Run 001 compares stock Snapmaker Orca U1 0.4 mm profile output against the experimental effective-width profile:

- Baseline: stock Snapmaker U1 0.4 mm process profile.
- Experimental: `docs/experimental_profiles/u1_0.4_adaptive_effective_width.process.json`

This is a profile-only benchmark. It does not modify slicer behavior, production profiles, G-code generation, Snapmaker validation, or printer safety behavior.

Preview and G-code inspection can help identify path-layout differences, slicing warnings, obvious preview regressions, and candidate models worth testing later. They cannot prove real print strength, print quality, dimensional accuracy, bonding, surface finish, purge behavior, toolchange reliability, or mixed physical nozzle behavior.

## Public Links

- Public AMP branch: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy>
- Run 001 benchmark package: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy/docs/benchmarks>
- Snapmaker forum post: <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359>
- Reddit post: <https://www.reddit.com/r/snapmaker/comments/1uiu84u/looking_for_u1_test_models_for_adaptive/>

## Model Categories Needed

Run 001 needs models that expose different U1 slicing and preview conditions:

- Thin-wall detail.
- Large bracket or box.
- Cosmetic top-surface detail.
- Embossed or debossed text.
- Speaker adapter ring.
- LED speaker ring face.
- Curved badge or trim model.
- Sloped surface torture test.
- Multi-region or modifier-volume model.

Related model request document:

- `docs/benchmarks/models_needed.md`

## Suggested GitHub Labels

- `amp`
- `benchmark`
- `model-needed`
- `u1-feedback`
- `stage-1`
- `surface-color-future`
- `mixed-nozzle-blocked`

Use `surface-color-future` only when the model is useful for future visible-surface planning, such as logos, skins, text, badges, trim, or surface color work.

Use `mixed-nozzle-blocked` only for U1 toolhead/nozzle feedback or models that are relevant to future Stage 2 physical nozzle validation. Stage 2 remains blocked until U1 hardware behavior is validated.

## Instructions For Model Suggestions

When submitting a model idea, include:

- Model category.
- Model file or source URL.
- Author or source name.
- License or permission status.
- Units and intended scale.
- Why this model is useful for Run 001.
- What visible detail should stay conservative.
- What internal or non-cosmetic region might tolerate wider effective widths.
- Expected failure modes to watch for in preview.
- Whether hardware print results already exist, if any.

Do not submit models unless the license or author permission allows benchmark use, public discussion, and repository issue tracking. If the model is not yours, link to the original source and state the license clearly.

Do not upload private, customer, paid, or restricted models unless the author explicitly permits public benchmark use.

## GitHub Issue Checklist

Create one issue per model category or feedback area. Suggested issue links:

- [Thin-wall/detail benchmark model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20thin-wall%2Fdetail%20benchmark%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [Functional bracket/box benchmark model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20functional%20bracket%2Fbox%20benchmark%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [Cosmetic top-surface detail model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20cosmetic%20top-surface%20detail%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [Embossed/debossed text model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20embossed%2Fdebossed%20text%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [Speaker adapter ring model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20speaker%20adapter%20ring%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [LED speaker ring face model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20LED%20speaker%20ring%20face%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [Curved badge / trim model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20curved%20badge%20or%20trim%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback,surface-color-future)
- [Sloped surface torture model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20sloped%20surface%20torture%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [Multi-region/modifier-volume model](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_benchmark_model.yml&title=AMP%20Run%20001%3A%20multi-region%20or%20modifier-volume%20model&labels=amp,benchmark,model-needed,stage-1,u1-feedback)
- [U1 toolhead/nozzle calibration feedback](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_u1_constraint_feedback.yml&title=AMP%20U1%20feedback%3A%20toolhead%2Fnozzle%20calibration%20constraints&labels=amp,u1-feedback,mixed-nozzle-blocked)
- [U1 purge/wipe/toolchange feedback](https://github.com/Ohmicaudio/OrcaSlicer/issues/new?template=amp_u1_constraint_feedback.yml&title=AMP%20U1%20feedback%3A%20purge%2Fwipe%2Ftoolchange%20constraints&labels=amp,u1-feedback,mixed-nozzle-blocked)

## Intake Triage

For each submitted model or feedback issue:

1. Confirm the model has a usable license or explicit permission.
2. Assign one primary benchmark category.
3. Record whether the model is synthetic, functional, cosmetic, or U1-specific.
4. Note which feature should remain conservative in preview.
5. Note which internal or non-cosmetic regions may be useful for profile-only comparison.
6. Add the model to the Run 001 candidate list only after source and permission are clear.
7. Keep U1 hardware claims out of the benchmark notes unless measured print data is provided.

## What Run 001 Can Report

Run 001 may report:

- Whether stock and experimental profile-only output both slice.
- Slicer warnings and errors.
- Slicer-estimated print time.
- Slicer-estimated filament usage.
- Previewed path-layout differences.
- G-code comments or metadata useful for inspection.
- Obvious preview regressions, such as missing thin features or visibly degraded top surfaces.

Run 001 must not claim:

- Measured print-time improvement.
- Strength improvement.
- Print quality improvement.
- Dimensional accuracy improvement.
- Bonding improvement.
- Surface finish improvement.
- Mixed physical nozzle success.
- U1 purge, wipe, toolchange, or calibration reliability.

## Current Status

Status: ready to collect model suggestions and U1 failure cases.

Next step: create GitHub issues from the checklist as useful model candidates or U1 constraint reports arrive from Reddit, the Snapmaker forum, Facebook, Discord, or direct project feedback.
