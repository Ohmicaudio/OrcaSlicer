# AMP Continuous Resolution Field Prototype

## Purpose

This report documents the first offline AMP prototype that computes a near-continuous resolution demand field before choosing a discrete U1 tool/profile class.

The prototype answers:

```text
What XY bead width and Z layer height does this region want?
Which available U1 nozzle/process profile best approximates that demand?
What quantization error and risk flags remain?
```

This is offline/advisory tooling only. It does not modify slicer behavior or emit toolchange G-code.

## Why This Exists

The earlier AMP chain could assign region labels to tool classes:

```text
region metadata
-> 3D / line-type-aware assignment
-> cost gate
-> concrete U1 process profile
```

The same-plate probe showed that carrying a four-tool queue into one G-code file is a representation problem, not an assignment problem.

This prototype fills the missing planner layer:

```text
continuous desired resolution
-> quantized available tool/profile
-> scheduling/toolchange later
```

## Continuous Demand Fields

The tool computes these continuous fields before quantization:

| Field | Meaning |
| --- | --- |
| `desired_xy_width_mm` | Desired bead/XY resolution before snapping to a U1 nozzle width class. |
| `desired_z_height_mm` | Desired layer/Z resolution before snapping to a supported U1 process layer height. |
| `desired_nozzle_class_mm` | Nearest conceptual nozzle class implied by desired XY width. |
| `desired_detail_score` | Detail pressure from feature size, visibility, and Z criticality. |
| `desired_bulk_score` | Bulk/internal pressure from line type, region area, path length, and wall/bulk role. |
| `desired_visibility_score` | Cosmetic/visible/mating sensitivity score. |
| `local_z_candidate` | Whether the region wants finer Z than the current global layer behavior can express. |
| `continuous_reason` | Human-readable reason for the desired XY/Z values. |

## Quantization To U1 Tool Ladder

The prototype quantizes continuous demand into the observed Snapmaker U1 profile ladder:

| Tool | Width class | Supported layer heights |
| --- | ---: | --- |
| 0.2 | 0.22 | 0.06, 0.08, 0.10, 0.12, 0.14 |
| 0.4 | 0.40-0.45, nominal 0.42 | 0.08, 0.12, 0.16, 0.20, 0.24, 0.28 |
| 0.6 | 0.62 | 0.18, 0.24, 0.30, 0.36, 0.42 |
| 0.8 | 0.82 | 0.24, 0.32, 0.40, 0.48, 0.56 |

Unsupported U1 layer heights are not invented. For example, a desired 0.05 mm Z height quantizes to the available 0.06 mm U1 0.2 process profile and records the quantization error.

The prototype uses a single nominal width class for calculations. For the U1 0.4 family, `0.42` represents the observed 0.40-0.45 mm process/profile range rather than a claim that only one 0.4-class width exists.

## Tool

Tool:

```text
tools/amp_continuous_resolution_field.py
```

Example metadata:

```text
docs/benchmarks/AMP_Continuous_Resolution_Field_Examples.json
```

Fixture command:

```powershell
python tools\amp_continuous_resolution_field.py --input docs\benchmarks\AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json --out outputs\amp_continuous_resolution_field\multitool_fixture_resolution_plan.json --csv outputs\amp_continuous_resolution_field\multitool_fixture_resolution_plan.csv --markdown outputs\amp_continuous_resolution_field\multitool_fixture_resolution_plan.md
```

Generated outputs are intentionally ignored under:

```text
outputs/amp_continuous_resolution_field/
```

## Example Table

| Region | Desired XY | Desired Z | Tool | Layer | Width | XY error | Z error | Local-Z | Confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `micro_text_face` | 0.192 | 0.050 | 0.2 | 0.06 | 0.22 | 0.028 | 0.010 | true | 0.70 |
| `normal_cosmetic_wall` | 0.420 | 0.160 | 0.4 | 0.16 | 0.42 | 0.000 | 0.000 | false | 0.71 |
| `hidden_internal_wall` | 0.620 | 0.240 | 0.6 | 0.24 | 0.62 | 0.000 | 0.000 | false | 0.57 |
| `structural_boss` | 0.620 | 0.160 | 0.6 | 0.18 | 0.62 | 0.000 | 0.020 | false | 0.57 |
| `bulk_infill_mass` | 0.820 | 0.400 | 0.8 | 0.40 | 0.82 | 0.000 | 0.000 | false | 0.75 |
| `sloped_top_logo` | 0.341 | 0.080 | 0.2 | 0.08 | 0.22 | 0.121 | 0.000 | false | 0.67 |
| `painted_surface_skin` | 0.372 | 0.120 | 0.4 | 0.12 | 0.42 | 0.048 | 0.000 | false | 0.66 |
| `support_interface` | 0.420 | 0.160 | 0.4 | 0.16 | 0.42 | 0.000 | 0.000 | false | 0.65 |
| `bridge_region` | 0.420 | 0.160 | 0.4 | 0.16 | 0.42 | 0.000 | 0.000 | false | 0.65 |
| `local_z_micro_mark` | 0.210 | 0.050 | 0.2 | 0.06 | 0.22 | 0.010 | 0.010 | true | 0.70 |

## Multi-Tool Fixture Result

| Region | Desired XY | Desired Z | Tool | Layer | Width | XY error | Z error | Local-Z | Confidence | Reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| `micro_detail_zone` | 0.210 | 0.050 | 0.2 | 0.06 | 0.22 | 0.010 | 0.010 | true | 0.70 | visible micro detail asks for sub-0.25 XY width; micro/local-Z candidate asks for finer Z than the base layer plan |
| `normal_visible_detail_zone` | 0.420 | 0.160 | 0.4 | 0.16 | 0.42 | 0.000 | 0.000 | false | 0.66 | normal visible detail asks for 0.4-class XY width; visible or medium-Z detail asks for conservative Z |
| `structural_shell_zone` | 0.620 | 0.240 | 0.6 | 0.24 | 0.62 | 0.000 | 0.000 | false | 0.57 | structural/internal wall demand is based on available wall thickness; general region uses stock-ish Z demand |
| `bulk_zone` | 0.820 | 0.400 | 0.8 | 0.40 | 0.82 | 0.000 | 0.000 | false | 0.75 | hidden bulk demand grows with region size and feature allowance; hidden bulk can use coarse Z before quantization |

## Quantization Errors

Quantization error is recorded separately for XY and Z:

- `quantization_error_xy = abs(quantized_line_width_class - desired_xy_width_mm)`
- `quantization_error_z = abs(quantized_layer_height - desired_z_height_mm)`

For the fixture, the largest quantization error is the micro-detail Z request:

```text
desired Z 0.050 -> available U1 layer 0.06, error 0.010
```

This is intentional. Current U1 0.2 profiles begin at 0.06 mm, so the planner records the unmet fine-Z demand instead of inventing a nonexistent 0.05 mm profile.

## Local-Z Future Flags

`micro_detail_zone` and the example `local_z_micro_mark` both ask for finer Z than the current global layer path can express cleanly.

The prototype marks those as:

```text
local_z_candidate
local_z_future_required
```

Local-Z is not implemented. This is only a future requirement flag.

## Relationship To Future T-Code / Toolchange Emission

The continuous field does not decide final toolchange positions by itself.

Future stages remain:

```text
continuous resolution field
-> U1 tool/profile quantization
-> segmentation boundaries
-> scheduling and cost gates
-> toolchange/T-code emission plan
-> actual G-code integration later
```

The current prototype stops at quantized advisory planning. It does not emit `T0`, `T1`, `T2`, or `T3` commands.

## What This Proves

- AMP now computes a continuous desired resolution before choosing a discrete tool class.
- The discrete U1 ladder approximates the continuous field with recorded quantization error.
- 0.2 is selected for true XY/Z detail demand.
- 0.4 remains the safe visible/detail fallback.
- 0.6 is selected for internal/structural wall demand when geometry supports it.
- 0.8 is selected for hidden bulk/infill demand when region size supports it.
- Local-Z needs are flagged but not implemented.
- Toolchange/T-code emission is a later scheduling stage.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate a single mixed-nozzle G-code file.

This does not emit production `T0`, `T1`, `T2`, or `T3` commands.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

This does not prove print strength, surface quality, dimensional accuracy, or bonding.

## Next Step

The next low-risk step is to export this continuous-to-quantized plan as an AMP debug artifact JSON bundle. That connects the offline planner to the existing AMP debug artifact scaffolding without touching production slicing.
