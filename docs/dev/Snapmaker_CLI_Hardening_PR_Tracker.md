# Snapmaker CLI Hardening PR Tracker

## Purpose

Track the Snapmaker Orca CLI fixes that were isolated while preparing AMP Benchmark Run 001.

These fixes are independent from Adaptive Manufacturing Planner behavior. They make CLI slicing and benchmark automation more reliable, but they do not add AMP planning logic, do not change production profiles, and do not change physical mixed-nozzle behavior.

## PRs and Branches

| Item | Status | Branch / URL | Scope |
| --- | --- | --- | --- |
| PR #560 | Open | https://github.com/Snapmaker/OrcaSlicer/pull/560 | Hardens CLI assemble-list plate loading. |
| PR #561 | Open | https://github.com/Snapmaker/OrcaSlicer/pull/561 | Guards `normalize_fdm()` when a process-only profile has `wipe_tower_filament` before `nozzle_diameter` is available. |
| Extruder expansion fix | Ready to open | https://github.com/Snapmaker/OrcaSlicer/compare/main...Ohmicaudio:OrcaSlicer:fix/cli-extruder-expansion-without-gui-state?expand=1 | Avoids GUI-only filament state in CLI extruder expansion. |

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
