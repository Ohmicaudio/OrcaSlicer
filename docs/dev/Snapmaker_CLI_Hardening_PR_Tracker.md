# Snapmaker CLI Hardening PR Tracker

## Purpose

Track the Snapmaker Orca CLI fixes that were isolated while preparing AMP Benchmark Run 001.

These fixes are independent from Adaptive Manufacturing Planner behavior. They make CLI slicing and benchmark automation more reliable, but they do not add AMP planning logic, do not change production profiles, and do not change physical mixed-nozzle behavior.

## PRs and Branches

| Item | Status | Branch / URL | Scope |
| --- | --- | --- | --- |
| PR #560 | Open | https://github.com/Snapmaker/OrcaSlicer/pull/560 | Hardens CLI assemble-list plate loading. |
| PR #561 | Open | https://github.com/Snapmaker/OrcaSlicer/pull/561 | Guards `normalize_fdm()` when a process-only profile has `wipe_tower_filament` before `nozzle_diameter` is available. |
| PR #562 | Open | https://github.com/Snapmaker/OrcaSlicer/pull/562 | Avoids GUI-only filament state in CLI extruder expansion. |
| Future PR | Not opened | `fix/cli-u1-0p2-profile-line-width-resolution` | Resolves inherited process profiles in the CLI path. Validated only when stacked on PR #561; wait for #561 to land or for Snapmaker to request a stacked review branch. |

## Run 001 Relationship

Benchmark Run 001 used a local CLI-hardened Snapmaker Orca build with:

- `afc59c6b8 fix: harden CLI assemble-list plate loading`
- `fd26642c9 fix: guard CLI FDM normalization without nozzle diameter`
- `a0f6db925 fix: avoid GUI filament state in CLI extruder expansion`

That local hardened build allowed:

- exact stock U1 process profile slicing without a CLI-safe profile copy;
- stock-only and experimental-only G-code generation for all six generated models;
- same-plate stock-vs-experimental visual comparison G-code for all six generated models.

## Independence From AMP

The CLI hardening fixes are upstream Snapmaker Orca reliability fixes. They do not consume `adaptive_manufacturing_enable`, do not call `AdaptiveManufacturingPlanner`, and do not alter AMP value types, sidecars, debug artifacts, observation summaries, or mappers.

AMP remains behavior-neutral: no production slicer path consumes AMP, no G-code generation path is changed by AMP, and no Snapmaker validation or safety path is bypassed.

## Reproduction Notes

To reproduce Run 001 exact-stock CLI slicing without local workarounds, the local build currently needs all three CLI hardening fixes listed above.

Once equivalent fixes are merged upstream, Run 001 should be reproducible from a cleaner Snapmaker Orca branch without the local CLI-hardened benchmark branch.

## Stacked Profile-Resolution Validation

The future inherited-process-profile fix was validated on a local stacked branch:

```text
validation/cli-profile-resolution-stacked-on-normalize-guard
```

Commit stack:

```text
d5a1055f6 fix: resolve inherited process profiles in CLI
5ace7ea28 fix: guard CLI FDM normalization without nozzle diameter
```

Validation result:

```text
11/11 plain-cube U1 nozzle-family CLI cases exited 0 and exported G-code.
```

Passed cases:

- U1 0.2: 8 process wrappers.
- U1 0.4: exact stock `0.20 Standard @Snapmaker U1 (0.4 nozzle).json` with `Snapmaker PLA Translucent @U1 0.4 nozzle.json`.
- U1 0.6: `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` with `Generic PLA @U1 0.6 nozzle.json`.
- U1 0.8: `0.24 Standard @Snapmaker U1 (0.8 nozzle).json` with `Generic PLA @U1 0.8 nozzle.json`.

The inherited-profile fix should remain separate and should not be opened as an independent PR until PR #561 lands, unless Snapmaker asks for a stacked review branch.

