# AMP Public Posts To Make

## Purpose

This document tracks public posts and follow-up messages that can help Adaptive Manufacturing Planner (AMP) collect useful Stage 1 benchmark feedback without overclaiming current capabilities.

The current promotion angle is:

```text
We are collecting Stage 1 test models for benchmark Run 001.
```

That is stronger and cleaner than asking people to "look at the project." It gives the community a concrete way to contribute.

General project framing:

```text
Adaptive Manufacturing Planner is a FDM/FFF resolution-allocation planning layer. Snapmaker U1 is the first submitted validation platform.
```

## Public Links

- Public branch: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy>
- Snapmaker forum thread: <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359>
- Stage 1 benchmark package: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy/docs/benchmarks>

## Messaging Rules

- Say "profile-only benchmark" for current Stage 1 validation.
- Say "experimental effective-width profile" for the current test profile.
- Say Stage 1 is useful for ordinary single-nozzle printers because it studies bead-width, line-width, visible-surface, and internal/bulk allocation before any toolchanger behavior.
- Say U1 is the first submitted validation target, not the only possible platform.
- Say AMP is behavior-neutral when discussing current code state.
- Say no production slicer path consumes AMP yet.
- Say Stage 2 mixed physical nozzle behavior remains blocked until U1 hardware validation.
- Do not claim print-time improvement until measured.
- Do not claim strength improvement from preview.
- Do not claim print quality improvement from preview.
- Do not claim mixed physical nozzle behavior works.
- Do not imply Snapmaker has endorsed the project unless they explicitly do.

## Posting Order

Recommended order:

1. Snapmaker forum benchmark model request.
2. Reddit `r/snapmaker` benchmark model request.
3. Facebook Snapmaker U1 group request, if an appropriate group is available.
4. Discord channel-location question, then a short benchmark request after guidance.
5. GitHub project status update or issue template announcement.
6. Ohmic Audio Labs progress update after the first model set is selected.

Do not post all channels at once. Leave time for replies and avoid looking spammy.

## Post Queue

### 1. Snapmaker Forum Benchmark Model Request

Status: ready to post after user approval

Where:

- Existing Snapmaker forum thread.

Goal:

- Ask for community model suggestions for Stage 1 profile-only benchmark Run 001.

Draft:

```text
Small next step for the AMP branch: I added a Stage 1 profile-only benchmark package.

The current benchmark is intentionally limited:
- stock Snapmaker U1 0.4 profile
- experimental effective-width profile
- preview/G-code inspection only
- no slicer behavior changes
- no physical mixed-nozzle claims

Benchmark package:
https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy/docs/benchmarks

I am looking for model suggestions in these categories:
- thin-wall detail
- large bracket/box
- cosmetic top-surface detail
- embossed/debossed text
- speaker adapter ring
- LED speaker ring face
- curved badge
- sloped surface torture test
- multi-region modifier model

For this first pass I am not trying to prove print quality or strength. I am only trying to see whether the experimental effective-width profile produces explainable path differences while keeping visible detail plausible in preview.
```

### 2. Reddit r/snapmaker Post

Status: draft only; check community rules before posting

Title:

```text
Looking for U1 test models for Adaptive Manufacturing Planner benchmark Run 001
```

Post:

```text
I have started an open-source Snapmaker Orca branch called Adaptive Manufacturing Planner.

AMP is a FDM/FFF resolution-allocation planning layer. Snapmaker U1 is the first submitted validation platform.

Public branch:
https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy

The project is staged carefully. The current implementation is behavior-neutral: no production slicer path consumes AMP yet, no G-code output changes, and no Snapmaker nozzle validation or safety paths are bypassed.

I just added the first Stage 1 profile-only benchmark package.

The goal of Run 001 is simple:
compare a stock U1 0.4 profile against an experimental effective-width/Arachne profile.

This does not claim print strength or print-quality improvements. It is only meant to compare slicer preview/G-code behavior and see whether role-specific width changes are worth studying further.

I am looking for U1-relevant test models in these categories:

- thin-wall detail
- large bracket or box
- cosmetic top-surface detail
- embossed/debossed text
- speaker adapter ring
- LED speaker ring face
- curved badge
- sloped surface torture test
- multi-region/modifier model

What I am hoping to learn:
- Which models expose bad behavior early?
- Where should visible detail stay conservative?
- Where could internal walls or infill safely use wider effective widths?
- What failure modes should be avoided before this ever affects toolpaths?

Stage 2 mixed physical nozzle behavior is still blocked until U1 hardware validation is possible.

If you have a good torture model, practical U1 part, or failure case, I would appreciate suggestions.
```

### 3. Facebook Snapmaker U1 Group Post

Status: draft only; use only in an appropriate Snapmaker U1 group

Draft:

```text
I have started an open-source FDM/FFF slicer project called Adaptive Manufacturing Planner. Snapmaker U1 is the first submitted validation platform.

Project branch:
https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy

The current branch is still behavior-neutral:
- no G-code changes
- no production slicer path consumes AMP
- no Snapmaker validation or safety checks are bypassed

I just added the first Stage 1 profile-only benchmark package.

The goal is to compare a stock U1 0.4 profile against an experimental effective-width/Arachne profile and see whether role-specific line-width changes are worth studying further.

I am looking for practical U1 test models:
- brackets
- boxes
- speaker rings
- LED ring faces
- badges/logos/text
- thin-wall parts
- sloped surface torture tests
- parts where visible detail matters but internal bulk could maybe print faster

This does not claim print-quality or strength improvements yet. It is just the first safe benchmark pass before any toolpath behavior changes.

If anyone has good test models or failure cases, I would appreciate suggestions.
```

### 4. Snapmaker Discord First Message

Status: draft only

Do not paste a giant announcement first. Ask where it belongs:

```text
Hey everyone - I am working on an open-source Snapmaker Orca branch called Adaptive Manufacturing Planner.

AMP is a FDM/FFF resolution-allocation planning layer. Snapmaker U1 is the first submitted validation platform.

It is behavior-neutral right now: no G-code changes, no production slicer path consumes it, and no Snapmaker validation/safety paths are bypassed.

I just added a Stage 1 profile-only benchmark package and I am looking for U1 test models / failure cases.

Is there a preferred channel for posting the branch and asking for benchmark model suggestions?
```

After they tell you where to post:

```text
Project branch:
https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy

I am looking for U1 models for Stage 1 benchmark Run 001:
stock U1 0.4 profile vs experimental effective-width/Arachne profile.

Useful model categories:
thin walls, brackets, text/logos, speaker rings, LED ring faces, curved badges, sloped surfaces, and parts where visible detail matters but internal bulk could potentially print faster.

No mixed-nozzle behavior exists yet. Stage 2 remains future hardware-specific work and remains blocked until U1 hardware validation.
```

### 5. GitHub Repository Status Update

Status: draft only; use as an issue/discussion if useful

Draft:

```text
AMP public status update

Current state:
- hidden developer config flag exists
- stock fallback value types exist
- no-op planner facade exists
- sidecar, debug artifact, serializer, writer, observation summary, and mapper scaffolds exist
- focused AMP tests pass
- no production slicer path consumes AMP
- no G-code or Snapmaker validation behavior has been changed

Current public validation:
- Stage 1 profile-only benchmark package
- stock U1 0.4 profile vs experimental effective-width profile
- preview/G-code inspection only

Help wanted:
- test model suggestions
- U1-specific constraints
- failure modes the planner should avoid before any behavior-changing work
```

### 6. Ohmic Audio Labs Progress Post

Status: draft only

Where:

- Ohmic Audio Labs website, newsletter, GitHub profile, or social channel.

Draft:

```text
We have opened a public Snapmaker Orca branch for Adaptive Manufacturing Planner, a staged FDM/FFF resolution-allocation research project focused on preserving visible detail where it matters while characterizing internal/bulk regions separately.

Current work is intentionally conservative: behavior-neutral scaffolding, tests, documentation, and a Stage 1 profile-only benchmark package. No production slicer path consumes AMP yet, and no G-code or Snapmaker validation behavior has been changed.

The first benchmark pass will use functional parts such as speaker adapters, LED speaker rings, trim pieces, brackets, boxes, and cosmetic badges.
```

## Response Templates

### If Someone Offers A Model

```text
Thanks. That could be useful for the Stage 1 profile-only benchmark.

Could you share:
- source link or file location
- license or permission to use it publicly
- units/scale
- what feature it stresses
- whether it has known slicing or print issues on U1

For Run 001 I will only use preview/G-code inspection, so no print-quality or strength claims will be made from the result.
```

### If Someone Asks Whether Mixed Nozzles Work

```text
Not claiming that yet.

Stage 2 mixed physical nozzle behavior remains blocked until U1 hardware validation and Snapmaker guidance are available. The current branch does not change G-code, does not bypass nozzle validation, and no production slicer path consumes AMP.
```

### If Someone Asks What Exists Today

```text
Today the branch has behavior-neutral scaffolding: hidden developer flag, fallback plan value types, no-op planner facade, sidecar/debug/observation value types, serializer/writer helpers, observation-to-debug mapping, tests, risk docs, and benchmark docs.

No production slicer path consumes AMP yet.
```

### If Snapmaker Replies With Engineering Guidance

```text
Thanks, this is helpful. I will record this guidance in the repo and keep Stage 2 blocked until the constraints are reflected in the risk register and validation plan.
```

## Community Promotion Log Task

After posts are made, create or update:

- `docs/submission/AMP_Community_Promotion_Log.md`

Include:

- Snapmaker forum URL.
- Reddit `r/snapmaker` post URL.
- Snapmaker U1 Facebook post status/URL, if available.
- Snapmaker Discord channel/message status, if available.
- GitHub branch URL.
- Date/time posted.
- Main ask: Stage 1 benchmark Run 001 test models.
- Questions asked.
- Replies received.
- Follow-up actions.

Also update `docs/submission/Snapmaker_Submission_Record.md` with Reddit, Facebook, and Discord entries when public links exist.

## Tracking Table

| Post | Channel | Status | Public URL | Notes |
| --- | --- | --- | --- | --- |
| Initial AMP thread | Snapmaker Forum | posted | <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359> | Public and replied to early feedback. |
| Benchmark model request | Snapmaker Forum | ready | pending | Use after user approval. |
| Benchmark model request | Reddit | draft | pending | Check rules first. |
| Benchmark model request | Facebook | draft | pending | Use a simpler version. |
| Channel-location question | Discord | draft | pending | Ask where it belongs before posting the full request. |
| Project status update | GitHub | draft | pending | Use if issues/discussions are enabled. |
| Ohmic progress update | Ohmic channel | draft | pending | Useful after first benchmark model set. |
