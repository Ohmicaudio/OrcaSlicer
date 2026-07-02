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

## Optional Per-Tool Slice Probe

The optional probe sliced the same full fixture as separate single-tool jobs. This is not a mixed-nozzle print and not a region-assigned toolpath. It only checks whether representative U1 tool-class profiles can process the fixture in the local CLI path.

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

## What This Proves

- The profile-backed U1 resolution ladder can be extracted into a planner-readable matrix.
- The project now has a four-region fixture with explicit intended 0.2 / 0.4 / 0.6 / 0.8 assignments.
- The fixture sidecar can carry region-level metadata before any slicer integration exists.
- The local CLI can slice the full fixture with 0.4, 0.6, and 0.8 U1 profile classes.
- The local 0.2 full-fixture probe is blocked by line-width validation and should be investigated separately if needed.

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
