# AMP Multi-Tool Resolution Fixture 001 Results

## Purpose

This pass creates the first AMP artifact aimed at the long-view target:

```text
multi-tool resolution allocation across 0.2 / 0.4 / 0.6 / 0.8 nozzle classes
```

The goal is not to implement mixed-nozzle slicing. The goal is to create the tool matrix, fixture, region assignment plan, and optional per-tool slice probes that can feed a future offline assignment solver.

## Generated Artifacts

Tool capability matrix CSV:

```text
outputs/amp_tool_matrix/u1_tool_capability_matrix.csv
```

Multi-tool fixture STL:

```text
outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture.stl
```

Region sidecar:

```text
outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture_regions.json
```

Generated G-code probe outputs:

```text
outputs/amp_multitool_resolution_fixture/gcode/
```

These generated outputs are intentionally not committed.

## Committed Inputs

Generator scripts:

```text
tools/amp_extract_u1_tool_capability_matrix.py
tools/amp_generate_multitool_resolution_fixture.py
```

Committed docs:

```text
docs/benchmarks/AMP_U1_Tool_Capability_Matrix.md
docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Assignment_Plan.md
docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Results.md
```

## Tool Capability Matrix Status

The U1 tool capability matrix was generated successfully.

Summary:

| Nozzle class | Layer-height class from profiles | Width class from profiles | Intended AMP role |
| --- | --- | --- | --- |
| 0.2 mm | 0.06-0.14 mm | 0.22 mm | Micro/fine visible detail |
| 0.4 mm | 0.08-0.28 mm | 0.40-0.45 mm | General visible/detail and normal shell |
| 0.6 mm | 0.18-0.42 mm | 0.62 mm | Structural shell / medium bulk |
| 0.8 mm | 0.24-0.56 mm | 0.82 mm | Bulk / fast internal regions |

The current U1 profile ladder begins at 0.06 mm for the 0.2 nozzle family. A 0.05 mm value should be treated as a conceptual fine-detail class, not a profile-backed U1 value in this branch.

## Fixture Status

The fixture was generated successfully and contains all four tool-class regions:

| Region | Intended class | Present |
| --- | --- | --- |
| `micro_detail_zone` | 0.2 nozzle / fine Z | Yes |
| `normal_visible_detail_zone` | 0.4 nozzle / normal visible detail | Yes |
| `structural_shell_zone` | 0.6 nozzle / structural shell | Yes |
| `bulk_zone` | 0.8 nozzle / hidden/internal bulk | Yes |

The fixture also includes holes, boss/counterbore-like features, a sloped cosmetic panel, visible detail features, and hidden backside/internal mass.

## Original Per-Tool Slice Probe

The original optional probe sliced the same full fixture as separate single-tool jobs. This is not a mixed-nozzle print and not a region-assigned toolpath. It only checks whether representative U1 tool-class profiles can process the fixture in the local CLI path.

| Probe | Machine/profile class | Result | Notes |
| --- | --- | --- | --- |
| `0p2_micro_fine` | U1 0.2 nozzle, 0.06 Standard | Blocked | CLI validation returned `Too small line width`, including after retry with `Generic PLA @U1 0.2 nozzle.json`. |
| `0p4_normal_visible` | U1 0.4 nozzle, 0.20 Standard | Succeeded | G-code exported. |
| `0p6_structural_shell` | U1 0.6 nozzle, 0.24 Standard | Succeeded | G-code exported. |
| `0p8_bulk` | U1 0.8 nozzle, 0.40 Standard | Succeeded | G-code exported. |

Probe metrics for successful exports:

| Probe | File size | Layers | Extrusion moves | Travel moves | Positive E |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.4 normal visible | 2,035,950 bytes | 62 | 4,254 | 57,988 | 9,003.556 |
| 0.6 structural shell | 1,458,139 bytes | 62 | 3,923 | 40,725 | 10,508.850 |
| 0.8 bulk | 1,082,888 bytes | 62 | 4,523 | 26,341 | 13,230.521 |

These metrics are not a fair quality comparison because the entire fixture was sliced under each single tool class. They are useful only as a coarse capability probe and path-complexity signal.

## Stacked CLI Fix Rerun - July 4, 2026

The fixture was rerun with a local stacked CLI validation build that includes:

```text
validation/cli-profile-resolution-stacked-on-normalize-guard
d5a1055f6 fix: resolve inherited process profiles in CLI
5ace7ea28 fix: guard CLI FDM normalization without nozzle diameter
```

CLI executable:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\snapmaker-orca-console.exe
```

Ignored rerun outputs:

```text
outputs/amp_multitool_resolution_fixture/stacked_cli_rerun_2026-07-04/
```

Each case stores its exact argument vector in an ignored `command.json` file under its output directory. The command shape was:

```powershell
snapmaker-orca-console.exe --debug 1 --slice 0 --outputdir <case-output> --load-settings <machine-profile> --load-settings <process-profile> --load-filaments <filament-profile> <model>
```

Full-fixture single-tool rerun results:

| Case | Process profile | Filament profile | Exit | G-code exported | G-code size |
| --- | --- | --- | ---: | --- | ---: |
| `full_fixture_u1_0p2_0p06` | `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | `Generic PLA @U1 0.2 nozzle.json` | 0 | Yes | 7,223,550 bytes |
| `full_fixture_u1_0p4_0p20` | `0.20 Standard @Snapmaker U1 (0.4 nozzle).json` | `Snapmaker PLA Translucent @U1 0.4 nozzle.json` | 0 | Yes | 1,416,518 bytes |
| `full_fixture_u1_0p6_0p24` | `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | `Generic PLA @U1 0.6 nozzle.json` | 0 | Yes | 917,310 bytes |
| `full_fixture_u1_0p8_0p40` | `0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | `Generic PLA @U1 0.8 nozzle.json` | 0 | Yes | 579,789 bytes |

Intended isolated-probe rerun results:

| Case | Intended class | Exit | G-code exported | G-code size |
| --- | --- | ---: | --- | ---: |
| `micro_detail_zone_only_u1_0p2_0p06` | 0.2 micro/fine detail | 0 | Yes | 404,677 bytes |
| `simple_0p2_wall_ladder_u1_0p2_0p06` | 0.2 wall/detail ladder | 0 | Yes | 342,261 bytes |
| `simple_0p2_gap_ladder_u1_0p2_0p06` | 0.2 gap/detail ladder | 0 | Yes | 572,000 bytes |
| `normal_visible_detail_zone_only_u1_0p4_0p20` | 0.4 normal visible detail | 0 | Yes | 112,358 bytes |
| `structural_shell_zone_only_u1_0p6_0p24` | 0.6 structural shell | 0 | Yes | 190,090 bytes |
| `bulk_zone_only_u1_0p8_0p40` | 0.8 bulk | 0 | Yes | 117,766 bytes |

Metrics summary from the rerun:

| Case | Layers | Extrusion moves | Travel moves | Positive E |
| --- | ---: | ---: | ---: | ---: |
| `full_fixture_u1_0p2_0p06` | 206 | 156 | 229,272 | 206.198 |
| `full_fixture_u1_0p4_0p20` | 62 | 3,393 | 38,780 | 7,602.702 |
| `full_fixture_u1_0p6_0p24` | 51 | 4,134 | 22,320 | 12,003.982 |
| `full_fixture_u1_0p8_0p40` | 31 | 3,356 | 13,767 | 15,314.416 |
| `micro_detail_zone_only_u1_0p2_0p06` | 29 | 1 | 10,891 | 15.000 |
| `simple_0p2_wall_ladder_u1_0p2_0p06` | 22 | 1 | 9,321 | 15.000 |
| `simple_0p2_gap_ladder_u1_0p2_0p06` | 26 | 1 | 14,586 | 15.000 |
| `normal_visible_detail_zone_only_u1_0p4_0p20` | 11 | 266 | 1,852 | 335.501 |
| `structural_shell_zone_only_u1_0p6_0p24` | 25 | 633 | 3,670 | 1,142.681 |
| `bulk_zone_only_u1_0p8_0p40` | 30 | 798 | 1,420 | 2,380.671 |

The 0.2 tool-class path is no longer blocked by inherited profile resolution in this stacked build. The 0.2 exports should still be treated as planning probes, not quality evidence. The low extrusion-move counts and high travel-move counts in the 0.2 isolated probes need preview inspection before they are used as a design signal.

## What This Proves

- The profile-backed U1 resolution ladder can be extracted into a planner-readable matrix.
- The project now has a four-region fixture with explicit intended 0.2 / 0.4 / 0.6 / 0.8 assignments.
- The fixture sidecar can carry region-level metadata before any slicer integration exists.
- The local stacked CLI validation build can slice the full fixture with 0.2, 0.4, 0.6, and 0.8 U1 profile classes.
- The 0.2 full-fixture and isolated-probe paths are unblocked when the normalize guard and inherited process profile resolution fixes are both present.
- The ladder is now viable for slicer/profile capability planning, but the 0.2 outputs still need preview and physical validation before any quality claim.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker validation.

This does not prove that one G-code file can safely use 0.2 / 0.4 / 0.6 / 0.8 tools on U1.

This does not prove print strength, surface quality, dimensional accuracy, or bonding.

This is a planning and fixture-generation step toward multi-tool resolution slicing.

Touchscreen-compatible mixed-nozzle behavior remains blocked pending Snapmaker's future metadata/tool-mapping path.

Fluidd-only experimental validation remains future and hardware-dependent.

## Next Recommended Technical Step

The next useful code step is still offline and behavior-neutral:

```text
region metadata + U1 tool matrix -> recommended tool/layer/width assignment
```

That solver should emit a deterministic assignment table and confidence/fallback reasons. It should not wire into Flow, Arachne, LayerRegion, PerimeterGenerator, PrintObject, G-code output, profiles, UI, or Snapmaker validation.
