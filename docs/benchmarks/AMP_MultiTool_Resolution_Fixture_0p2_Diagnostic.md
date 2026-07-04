# AMP Multi-Tool Resolution Fixture 0.2 Diagnostic

## Purpose

Diagnose why the U1 0.2 nozzle profile reports `Too small line width` when slicing the AMP multi-tool resolution fixture in the local Snapmaker Orca CLI path.

This diagnostic does not implement mixed-nozzle slicing.

This diagnostic does not validate physical mixed-nozzle behavior.

This diagnostic only defines safe geometry/profile boundaries for future tool-class assignment.

## Local Environment

Repository:

```text
B:\ohmic\Snapmaker-OrcaSlicer
```

Branch:

```text
u1-adaptive-nozzle-strategy
```

CLI executable:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe
```

CLI reported Snapmaker Orca version:

```text
01.10.01.50
```

## Original Failure

Full fixture model:

```text
outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture.stl
```

Machine profile:

```text
resources/profiles/Snapmaker/machine/Snapmaker U1 (0.2 nozzle).json
```

Process profile:

```text
resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json
```

Filament profiles tested:

```text
resources/profiles/Snapmaker/filament/Snapmaker PLA @U1.json
resources/profiles/Snapmaker/filament/Generic PLA @U1 0.2 nozzle.json
```

Representative command:

```powershell
B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe --debug 3 --slice 0 --outputdir B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_multitool_resolution_fixture\gcode\0p2_micro_fine_tmp --load-settings "B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\machine\Snapmaker U1 (0.2 nozzle).json;B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\process\0.06 Standard @Snapmaker U1 (0.2 nozzle).json" --load-filaments "B:\ohmic\Snapmaker-OrcaSlicer\resources\profiles\Snapmaker\filament\Snapmaker PLA @U1.json" B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_multitool_resolution_fixture\models\amp_multitool_resolution_fixture.stl
```

Observed result:

```text
exit code: -51
stderr: Too small line width
stdout: got error when validate: Too small line width
```

The same failure reproduced after retrying with:

```text
resources/profiles/Snapmaker/filament/Generic PLA @U1 0.2 nozzle.json
```

## Validator Source

The error string is emitted from `src/libslic3r/Print.cpp` in the pre-slice extrusion-width validator.

The relevant validation rule compares configured extrusion widths against the active object layer height:

```text
Configured extrusion width must be greater than layer_height.
```

This check happens before Arachne or classic wall generation produces wall paths. Therefore the local failure is a configuration validation failure, not an observed Arachne wall-generation failure.

## U1 0.2 Profile Constraints Found

The U1 0.2 machine profile declares:

| Setting | Value |
| --- | --- |
| `nozzle_diameter` | `0.2`, repeated for all four toolheads |
| `min_layer_height` | `0.04`, repeated for all four toolheads |
| `max_layer_height` | `0.14`, repeated for all four toolheads |

The 0.2 process bases share these width settings:

| Process base | `layer_height` | `line_width` | `outer_wall_line_width` | `inner_wall_line_width` | `top_surface_line_width` | `sparse_infill_line_width` | `internal_solid_infill_line_width` | `support_line_width` | `initial_layer_line_width` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fdm_process_U1_0.06_nozzle_0.2` | 0.06 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.25 |
| `fdm_process_U1_0.08_nozzle_0.2` | 0.08 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.25 |
| `fdm_process_U1_0.10_nozzle_0.2` | 0.10 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.25 |
| `fdm_process_U1_0.12_nozzle_0.2` | 0.12 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.25 |
| `fdm_process_U1_0.14_nozzle_0.2` | 0.14 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.22 | 0.25 |

The common U1 process profile contains:

| Setting | Value |
| --- | --- |
| `wall_generator` | `classic` |
| common `layer_height` | `0.2` |
| common `line_width` | `0.42` |
| common `internal_solid_infill_line_width` | `0.42` |

No explicit U1 0.2 profile key named as a minimum line width was found in the checked machine/process profiles. The effective local validator constraint is the code-level rule that each configured width must be greater than the active layer height.

The nominal 0.2 profile bases appear internally valid on paper because all 0.22 mm configured line widths are greater than the declared 0.06-0.14 mm layer heights. The local CLI failure on a plain cube suggests that the effective config reaching validation is inconsistent with those nominal profile values.

## Plain Cube Reproduction

To separate profile/config failure from fixture geometry, a plain 10 mm cube was generated:

```text
outputs/amp_multitool_resolution_fixture/probes/simple_cube_10mm.stl
```

All user-facing U1 0.2 wrapper profiles failed on that cube:

| Process profile | Result | Error |
| --- | --- | --- |
| `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed | `Too small line width` |
| `0.08 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed | `Too small line width` |
| `0.10 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed | `Too small line width` |
| `0.12 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed | `Too small line width` |
| `0.14 Standard @Snapmaker U1 (0.2 nozzle).json` | Failed | `Too small line width` |

The non-instantiated base process file:

```text
resources/profiles/Snapmaker/process/fdm_process_U1_0.06_nozzle_0.2.json
```

was not a valid replacement for the wrapper process in CLI testing. The CLI reported the base process as incompatible with the printer, so the real user-facing failure remains the instantiated wrapper profile path.

## Isolated Region Probes

The following isolated probes were generated under:

```text
outputs/amp_multitool_resolution_fixture/probes/
```

Generated probes:

```text
micro_detail_zone_only.stl
normal_visible_detail_zone_only.stl
structural_shell_zone_only.stl
bulk_zone_only.stl
simple_0p2_wall_ladder.stl
simple_0p2_gap_ladder.stl
```

Each probe was sliced with:

```text
U1 0.2 nozzle / 0.06 Standard / Generic PLA @U1 0.2 nozzle
U1 0.4 nozzle / 0.20 Standard / Snapmaker PLA @U1
```

Results:

| Probe | U1 0.2 result | U1 0.2 error | U1 0.4 comparison |
| --- | --- | --- | --- |
| `micro_detail_zone_only.stl` | Failed | `Too small line width` | Passed |
| `normal_visible_detail_zone_only.stl` | Failed | `Too small line width` | Passed |
| `structural_shell_zone_only.stl` | Failed | `Too small line width` | Passed |
| `bulk_zone_only.stl` | Failed | `Too small line width` | Passed |
| `simple_0p2_wall_ladder.stl` | Failed | `Too small line width` | Passed |
| `simple_0p2_gap_ladder.stl` | Failed | `Too small line width` | Passed |

This strongly indicates that the local 0.2 failure is not caused by one bad micro-detail region, one bad STL, or the full fixture's mixed feature set. The same local 0.2 profile path fails on simple geometry, while the same generated probe STLs are loadable and sliceable through the U1 0.4 profile path.

## Classic vs Arachne Probe

The U1 common process profile uses:

```text
wall_generator = classic
```

Temporary diagnostic process copies were created under ignored outputs to force:

```text
wall_generator = classic
wall_generator = arachne
```

Both variants failed the plain cube before wall generation:

| Wall generator | Result | Error |
| --- | --- | --- |
| `classic` | Failed | `Too small line width` |
| `arachne` | Failed | `Too small line width` |

Because validation fails before perimeter generation, the observed local failure is not an Arachne-vs-classic geometry behavior.

## Minimum Safe Feature Notes

The local CLI path did not establish a measured printable minimum for the U1 0.2 profile because even a plain cube fails validation.

Until the U1 0.2 CLI profile path is corrected or confirmed in the GUI, AMP fixture assumptions should stay conservative:

| Feature class | Planning note |
| --- | --- |
| Below 0.22 mm | Stress-only. Do not label as expected to resolve under the U1 0.2 profile. |
| Around 0.22 mm | Nominal line-width boundary. Treat as high-risk until a successful 0.2 slice and print path exists. |
| 0.30-0.45 mm | Candidate micro-detail range, still validation-needed. |
| 0.60 mm and above | More plausible visible-detail geometry for a first 0.2/0.4 comparison, but still not print-validated here. |

These are planning constraints, not physical print claims.

## Fixture Regions Needing Redesign

No immediate generator redesign was made in this diagnostic pass.

Reason:

```text
The 0.2 failure reproduces on a plain cube and on every isolated region probe.
```

That makes the local failure profile/config-path caused, not fixture-geometry caused.

Future Rev B fixture work should still improve labeling:

- Mark sub-0.22 mm details as stress-only.
- Treat 0.22 mm detail as nominal-boundary, not guaranteed-resolvable.
- Keep the micro-detail region separate from normal visible detail.
- Preserve 0.4, 0.6, and 0.8 regions because those single-tool probe paths currently slice successfully.

## Diagnostic Conclusion

Original conclusion:

```text
The local U1 0.2 failure is profile/config-path caused, not geometry-caused.
```

Evidence:

- The full fixture fails with U1 0.2.
- A plain 10 mm cube fails with all checked U1 0.2 wrapper profiles.
- Every isolated region probe fails with U1 0.2.
- The same isolated probe STLs pass with U1 0.4.
- Classic and Arachne diagnostic process copies both fail before wall generation.
- The nominal 0.2 profile bases specify 0.22 mm line widths and 0.06-0.14 mm layer heights, which should satisfy the visible validator rule on paper.

Recommended next fix path:

1. Treat this as a Snapmaker Orca CLI/profile-resolution issue separate from AMP planner behavior.
2. Investigate whether the CLI path fully resolves inherited U1 0.2 process settings before `Print::validate`.
3. Confirm whether the same U1 0.2 profiles slice a plain cube in the GUI.
4. Do not redesign the AMP multi-tool fixture as the primary fix unless a working U1 0.2 slice path later reveals specific geometry limits.

## Stacked CLI Fix Rerun - July 4, 2026

The diagnostic was rerun with a local stacked CLI validation build:

```text
validation/cli-profile-resolution-stacked-on-normalize-guard
d5a1055f6 fix: resolve inherited process profiles in CLI
5ace7ea28 fix: guard CLI FDM normalization without nozzle diameter
```

CLI executable:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\snapmaker-orca-console.exe
```

Rerun output directory:

```text
outputs/amp_multitool_resolution_fixture/stacked_cli_rerun_2026-07-04/
```

The rerun used the same generated fixture/probe family, but loaded the 0.2 user-facing wrapper profile through the stacked CLI fixes:

```text
resources/profiles/Snapmaker/machine/Snapmaker U1 (0.2 nozzle).json
resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json
resources/profiles/Snapmaker/filament/Generic PLA @U1 0.2 nozzle.json
```

0.2 rerun results:

| Model | Exit | G-code exported | G-code size |
| --- | ---: | --- | ---: |
| `amp_multitool_resolution_fixture.stl` | 0 | Yes | 7,223,550 bytes |
| `micro_detail_zone_only.stl` | 0 | Yes | 404,677 bytes |
| `simple_0p2_wall_ladder.stl` | 0 | Yes | 342,261 bytes |
| `simple_0p2_gap_ladder.stl` | 0 | Yes | 572,000 bytes |

Cross-tool ladder rerun summary:

| Tool class | Representative process | Intended probe | Result |
| --- | --- | --- | --- |
| 0.2 mm | `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | micro/detail, wall ladder, gap ladder | Passed |
| 0.4 mm | `0.20 Standard @Snapmaker U1 (0.4 nozzle).json` | normal visible detail | Passed |
| 0.6 mm | `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | structural shell | Passed |
| 0.8 mm | `0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | bulk | Passed |

Updated conclusion:

```text
The 0.2 tool-class failure is unblocked by the stacked CLI profile fixes.
```

This does not mean the micro-detail geometry is print-quality validated. It only means the user-facing U1 0.2 profile family can now export G-code for the fixture/probe set in the local stacked CLI validation path.

Remaining constraints:

- Preview inspection is still needed for the 0.2 G-code because the metrics show unusually low extrusion-move counts and high travel-move counts in isolated 0.2 probes.
- Physical validation is still required before claiming 0.2 detail quality, surface quality, strength, bonding, or dimensional accuracy.
- The inherited profile resolution fix should remain sequenced after the normalize_fdm guard unless Snapmaker asks for a stacked review branch.
- This does not implement mixed-nozzle slicing.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
- This only verifies slicer/profile capability for tool-class planning.

## Non-Claims

This diagnostic does not implement mixed-nozzle slicing.

This diagnostic does not validate physical mixed-nozzle behavior.

This diagnostic does not prove 0.2 mm detail is printable on U1.

This diagnostic does not prove surface quality, strength, bonding, dimensional accuracy, or touchscreen compatibility.

This diagnostic only defines the current local CLI blocker and conservative planning boundaries for future tool-class assignment.
