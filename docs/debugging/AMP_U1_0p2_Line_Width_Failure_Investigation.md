# AMP U1 0.2 Line-Width Failure Investigation

## Purpose

Investigate why the local Snapmaker Orca CLI path reports:

```text
Too small line width
```

when slicing a plain cube with U1 0.2 nozzle profiles.

This is a CLI/profile-resolution investigation. It does not modify AMP planner behavior, production profiles, G-code generation, Flow, LayerRegion, PerimeterGenerator, Arachne, UI behavior, PrintObject, Snapmaker validation, or CalibUtils.cpp.

## Summary

The U1 0.2 failure is not caused by the AMP multi-tool fixture geometry.

The failure reproduces on:

```text
plain 10 mm cube
simple 0.2 wall ladder
simple 0.2 gap ladder
isolated micro/detail region probes
```

The same isolated STLs slice successfully with a U1 0.4 profile.

The likely root cause is that the Snapmaker Orca CLI path applies the thin instantiated process wrapper JSON without resolving the inherited U1 0.2 process base before validation.

For U1 0.2, this leaves some default/common width or layer-height values in the effective print config. The important failing interaction is:

```text
layer_height = 0.2
skin_infill_line_width = 100% of 0.2 nozzle = 0.2
skeleton_infill_line_width = 100% of 0.2 nozzle = 0.2
```

The validator rejects extrusion widths where:

```text
width <= layer_height
```

So `0.2 <= 0.2` triggers `Too small line width`.

## Red Test

Model:

```text
outputs/amp_multitool_resolution_fixture/probes/simple_cube_10mm.stl
```

Machine:

```text
resources/profiles/Snapmaker/machine/Snapmaker U1 (0.2 nozzle).json
```

Process:

```text
resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json
```

Filament:

```text
resources/profiles/Snapmaker/filament/Generic PLA @U1 0.2 nozzle.json
```

Observed result:

```text
exit code: -51
stderr: Too small line width
stdout: got error when validate: Too small line width
```

The same cube failed with all checked U1 0.2 wrapper profiles:

| U1 0.2 wrapper profile | Result |
| --- | --- |
| `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed: `Too small line width` |
| `0.08 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed: `Too small line width` |
| `0.10 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed: `Too small line width` |
| `0.12 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed: `Too small line width` |
| `0.14 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed: `Too small line width` |

## Control Test

The same isolated probe STLs passed with:

```text
Snapmaker U1 (0.4 nozzle)
0.20 Standard @Snapmaker U1 (0.4 nozzle)
Snapmaker PLA @U1
```

This confirms the generated probe STLs are loadable and sliceable in the local CLI path.

## Source Path

The error is emitted in:

```text
src/libslic3r/Print.cpp
```

The relevant validation rule is:

```text
if (extrusion_width_min <= layer_height) {
    err_msg = L("Too small line width");
    return false;
}
```

The validation loop checks:

```text
line_width
support_line_width when support or raft is active
inner_wall_line_width
outer_wall_line_width
sparse_infill_line_width
internal_solid_infill_line_width
top_surface_line_width
skin_infill_line_width
skeleton_infill_line_width
```

The failure happens before Arachne or classic wall generation. Temporary diagnostic process copies forcing either `classic` or `arachne` both failed the same plain cube with the same error.

## Profile Values

The U1 0.2 machine profile declares:

| Setting | Value |
| --- | --- |
| `nozzle_diameter` | `0.2`, repeated for all four toolheads |
| `min_layer_height` | `0.04`, repeated for all four toolheads |
| `max_layer_height` | `0.14`, repeated for all four toolheads |

The U1 0.2 base process profiles declare:

| Process base | `layer_height` | main line-width values |
| --- | ---: | ---: |
| `fdm_process_U1_0.06_nozzle_0.2` | 0.06 | 0.22 |
| `fdm_process_U1_0.08_nozzle_0.2` | 0.08 | 0.22 |
| `fdm_process_U1_0.10_nozzle_0.2` | 0.10 | 0.22 |
| `fdm_process_U1_0.12_nozzle_0.2` | 0.12 | 0.22 |
| `fdm_process_U1_0.14_nozzle_0.2` | 0.14 | 0.22 |

The common U1 process profile declares:

| Setting | Value |
| --- | --- |
| `layer_height` | 0.2 |
| `line_width` | 0.42 |
| `wall_generator` | classic |

`skin_infill_line_width` and `skeleton_infill_line_width` are defined in `PrintConfig.cpp` with defaults:

```text
100% of nozzle_diameter
```

For a 0.2 nozzle, that resolves to:

```text
0.2 mm
```

## Setting-Isolation Matrix

Temporary diagnostic process files were generated under ignored outputs to isolate the interaction.

The important cases were:

| Temporary process case | Result | Interpretation |
| --- | --- | --- |
| Complete 0.2 process values, no explicit skin/skeleton widths | Passed | With `layer_height=0.06`, default 0.2 skin/skeleton widths are greater than layer height. |
| Complete 0.2 process values plus `skin_infill_line_width=0.22`, `skeleton_infill_line_width=0.22` | Passed | Explicit 0.22 values are valid. |
| Common `layer_height=0.2`, no explicit skin/skeleton widths | Failed | Default 0.2 skin/skeleton widths equal layer height and trip validation. |
| Common `layer_height=0.2`, explicit `skin_infill_line_width=0.22`, `skeleton_infill_line_width=0.22` | Passed | Widths greater than layer height avoid the immediate failure. |
| Common `layer_height=0.2`, explicit `skin_infill_line_width=0.24`, `skeleton_infill_line_width=0.24` | Passed | Wider explicit values also avoid the immediate failure. |

Wrapper-profile copies also passed when either:

```text
layer_height = 0.06
```

was placed directly in the wrapper, or when:

```text
skin_infill_line_width = 0.22
skeleton_infill_line_width = 0.22
```

were placed directly in the wrapper.

This indicates the thin wrapper is not receiving all inherited base-process values before validation in the CLI path.

## Likely Cause

The CLI path in:

```text
src/Snapmaker_Orca.cpp
```

loads process JSON files through `load_config_file`, then applies the loaded process config to `m_print_config`.

The code near the process-application path includes:

```text
//todo: support system process preset
```

The observed behavior matches that comment: when the CLI is given an instantiated process wrapper, it applies that wrapper as a partial process config instead of resolving the inherited base process chain first.

This is mostly invisible for U1 0.4 because the common/default values are compatible with a 0.4 nozzle and 0.2 layer height. It breaks U1 0.2 because the unresolved defaults land on a validator boundary.

## GUI Parity

GUI parity was not completed in this pass.

Required manual check:

1. Open Snapmaker Orca GUI.
2. Load a plain 10 mm cube.
3. Select `Snapmaker U1 (0.2 nozzle)`.
4. Select `0.06 Standard @Snapmaker U1 (0.2 nozzle)`.
5. Slice.
6. Record whether the GUI slices successfully or reports `Too small line width`.

Interpretation:

| GUI result | Meaning |
| --- | --- |
| GUI passes, CLI fails | Clean CLI profile-resolution bug candidate. |
| GUI fails, CLI fails | U1 0.2 profile/config validation issue or local profile mismatch. |
| GUI and CLI pass with a different profile-loading sequence | Previous CLI command was incomplete or using the wrong preset chain. |

## Clean Fix Branch Status

A clean branch was created from `origin/main` in a separate worktree:

```text
B:\ohmic\Snapmaker-OrcaSlicer-cli-0p2-fix
fix/cli-u1-0p2-profile-line-width-resolution
```

The clean branch was committed and pushed as:

```text
f6916ba3b fix: resolve inherited process profiles in CLI
https://github.com/Ohmicaudio/OrcaSlicer/tree/fix/cli-u1-0p2-profile-line-width-resolution
```

Changed source file:

```text
src/Snapmaker_Orca.cpp
```

Fix intent:

```text
Resolve same-directory inherited process JSON files before applying an instantiated process wrapper in the CLI path.
```

Build notes:

- A portable CMake 3.31.8 was installed under `B:\ohmic\tools` because the PATH CMake is 4.0.1 and the repo rejects CMake 4.x on Windows.
- Configure succeeded with `SLIC3R_MSVC_COMPILE_PARALLEL=OFF`.
- The first measured serial build failed in `libslic3r_gui` with `error C1090: PDB API call failed, error code '3'`.
- Removing the generated `libslic3r_gui.pdb` build artifact and resuming the same serial build allowed the target to finish.
- A follow-up `Snapmaker_Orca` target rebuild exited 0.

The local build target produces `Snapmaker_Orca.dll`. For CLI verification, the existing console wrapper executable was copied into the clean build `Release` directory as a local test artifact so it would load the newly built DLL from the same directory.

## Patched CLI Verification

Exact plain-cube repro after the fix:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\snapmaker-orca-console.exe
  --debug 3
  --slice 0
  --outputdir B:\ohmic\Snapmaker-OrcaSlicer-cli-0p2-fix\outputs\cli_0p2_fix_verify\simple_cube_0p2
  --load-settings B:\ohmic\Snapmaker-OrcaSlicer-cli-0p2-fix\resources\profiles\Snapmaker\machine\Snapmaker U1 (0.2 nozzle).json
  --load-settings B:\ohmic\Snapmaker-OrcaSlicer-cli-0p2-fix\resources\profiles\Snapmaker\process\0.06 Standard @Snapmaker U1 (0.2 nozzle).json
  --load-filaments B:\ohmic\Snapmaker-OrcaSlicer-cli-0p2-fix\resources\profiles\Snapmaker\filament\Generic PLA @U1 0.2 nozzle.json
  B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_multitool_resolution_fixture\probes\simple_cube_10mm.stl
```

Result:

```text
exit code: 0
G-code exported:
B:\ohmic\Snapmaker-OrcaSlicer-cli-0p2-fix\outputs\cli_0p2_fix_verify\simple_cube_0p2\plate_1.gcode
```

Additional U1 0.2 process-wrapper checks on the same cube:

| Process wrapper | G-code exported |
| --- | --- |
| `0.06 High Quality @Snapmaker U1 (0.2 nozzle).json` | Yes |
| `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | Yes |
| `0.08 High Quality @Snapmaker U1 (0.2 nozzle).json` | Yes |
| `0.08 Standard @Snapmaker U1 (0.2 nozzle).json` | Yes |
| `0.10 High Quality @Snapmaker U1 (0.2 nozzle).json` | Yes |
| `0.10 Standard @Snapmaker U1 (0.2 nozzle).json` | Yes |
| `0.12 Standard @Snapmaker U1 (0.2 nozzle).json` | Yes |
| `0.14 Standard @Snapmaker U1 (0.2 nozzle).json` | Yes |

One attempted U1 0.4 control did not complete because the initially selected `Generic PLA @U1 0.4 nozzle.json` filament file does not exist in this clean worktree, and a substitute 0.4 U1 filament crashed very early. That separate control issue was not used as evidence for the U1 0.2 fix.

## Recommended Next Step

The next practical step is:

```text
Confirm GUI parity for U1 0.2 cube slicing.
```

Then:

| Result | Action |
| --- | --- |
| GUI passes | Open a small Snapmaker PR from the clean CLI fix branch. |
| GUI fails | Document the exact invalid profile/config state before proposing a profile fix. |

## Required Validation Before Any PR

Before opening a Snapmaker PR, verify:

```text
U1 0.2 plain cube exits 0: done
U1 0.2 process wrapper matrix exports G-code: done
U1 0.2 micro/detail probe exits 0 when geometry is valid: still recommended
U1 0.4 cube/probe control still exits 0: still needs a clean matching filament/profile control
U1 0.6 and U1 0.8 fixture probes still exit 0 if practical
```

Do not include AMP planner commits, benchmark docs, generated outputs, or profile changes in the clean PR branch.

## Non-Claims

This investigation does not implement mixed-nozzle slicing.

This investigation does not validate physical mixed-nozzle behavior.

This investigation does not prove U1 0.2 print quality or detail resolution.

This investigation does not change production slicer behavior.

This investigation only isolates the likely local CLI/profile-resolution failure blocking the 0.2 tool class in automated AMP probe work.
