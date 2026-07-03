# Snapmaker CLI Profile Resolution Stacked Validation

## Purpose

Record validation showing that the CLI inherited-process-profile resolution fix passes when stacked on the `normalize_fdm()` missing-nozzle-diameter guard.

This is validation evidence for Snapmaker Orca CLI hardening. It does not modify AMP planner behavior, production profiles, G-code generation, Snapmaker validation, or physical mixed-nozzle behavior.

## Validation Branch

```text
validation/cli-profile-resolution-stacked-on-normalize-guard
```

## Commit Stack

```text
d5a1055f6 fix: resolve inherited process profiles in CLI
5ace7ea28 fix: guard CLI FDM normalization without nozzle diameter
```

The stacked branch is for validation only. The inherited-profile fix should remain a separate future PR after PR #561 lands, unless Snapmaker asks for a stacked review branch.

## Changed Files

```text
src/libslic3r/PrintConfig.cpp
src/Snapmaker_Orca.cpp
```

No AMP files, benchmark docs, generated outputs, production profiles, or scratch logs are included in the stacked branch diff.

## Build

Command:

```text
cmake --build B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release --target Snapmaker_Orca --config Release --parallel 1
```

Result:

```text
exit code: 0
output target: B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\Snapmaker_Orca.dll
```

Build note:

```text
The first stacked rebuild hit a local Visual Studio PDB write error while linking Snapmaker_Orca.pdb. Removing the generated PDB build artifact and rebuilding allowed the target to complete with exit 0.
```

## CLI Validation Matrix

Model:

```text
plain 10 mm cube
```

Result:

```text
11/11 cases exited 0 and exported G-code.
```

Passed cases:

| Nozzle family | Machine profile | Process profile | Filament profile | Result |
| --- | --- | --- | --- | --- |
| U1 0.2 | `Snapmaker U1 (0.2 nozzle).json` | 8 checked U1 0.2 process wrappers | `Generic PLA @U1 0.2 nozzle.json` | Exit 0, G-code exported |
| U1 0.4 | `Snapmaker U1 (0.4 nozzle).json` | `0.20 Standard @Snapmaker U1 (0.4 nozzle).json` | `Snapmaker PLA Translucent @U1 0.4 nozzle.json` | Exit 0, G-code exported |
| U1 0.6 | `Snapmaker U1 (0.6 nozzle).json` | `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | `Generic PLA @U1 0.6 nozzle.json` | Exit 0, G-code exported |
| U1 0.8 | `Snapmaker U1 (0.8 nozzle).json` | `0.24 Standard @Snapmaker U1 (0.8 nozzle).json` | `Generic PLA @U1 0.8 nozzle.json` | Exit 0, G-code exported |

## Interpretation

The inherited-process-profile fix is valid under the stacked condition, but its clean PR timing depends on the normalize guard.

Without the normalize guard, the exact U1 0.4 stock wrapper crashes during partial config normalization because it contains `wipe_tower_filament` before `nozzle_diameter` is available.

With the normalize guard applied, the full U1 nozzle-family CLI matrix validates cleanly.

## Decision

Do not open the inherited-profile PR yet.

Wait until PR #561 lands, then rebase the inherited-process-profile fix and open it as the next clean Snapmaker CLI hardening PR. If Snapmaker requests a stacked review branch, use the stacked validation branch as evidence that the two fixes work together.

## PR #561 Comment

A validation note was posted to PR #561:

```text
https://github.com/Snapmaker/OrcaSlicer/pull/561#issuecomment-4878422338
```

## Non-Claims

This validation does not implement AMP planner behavior.

This validation does not implement mixed-nozzle slicing.

This validation does not validate physical mixed-nozzle behavior.

This validation does not change production profiles or Snapmaker safety behavior.
