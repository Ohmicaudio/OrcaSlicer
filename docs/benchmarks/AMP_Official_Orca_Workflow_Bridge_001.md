# AMP Official Orca Workflow Bridge 001

## Purpose

Create a practical bridge from the AMP offline plan packet to the official Orca GUI mixed-nozzle workflow.

This bridge has two parts:

- a generated setup manifest that translates AMP region decisions into manual Orca GUI tool assignments
- a G-code validator that checks the exported Orca G-code against the AMP plan packet

This is workflow and validation tooling only. It does not implement AMP-driven mixed-nozzle slicing.

## Why This Bridge Exists

The repaired official Orca GUI probe established that upstream Orca can manually export mixed-nozzle G-code for the four-region fixture. AMP therefore does not need to invent the basic mixed-nozzle representation.

The useful split is now:

| System | Role |
| --- | --- |
| Official Orca | manual/static mixed-nozzle setup and G-code export |
| AMP | automatic planning, mapping, validation, fallback reasoning, and safety gating |

## Official Orca GUI Baseline Result

Input G-code:

```text
C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\gcode\official_orca_mixed_probe_0p12_fixed_models.gcode
```

Observed G-code evidence:

| Field | Result |
| --- | --- |
| Nozzle header | `0.2,0.4,0.6,0.8,0.8` |
| Expected used nozzle classes | `0.2,0.4,0.6,0.8` |
| Active tools | `T0,T1,T2,T3` |
| Tool command count | 80 |
| Print settings ID | `0.12mm Mixed Probe @AMP Mixed ToolChanger` |

The extra fifth `0.8` is treated as an unused preset/tool-slot artifact because the custom Orca toolchanger preset had five tool slots while AMP used four.

## AMP Plan Packet Mapping

Source packet:

```text
outputs/amp_plan_packet_001/
```

AMP intended mapping:

| Region | AMP tool class | Orca tool index | Expected T command | AMP selected process profile | AMP selected layer height |
| --- | ---: | ---: | --- | --- | ---: |
| `micro_detail_zone` | `0.2` | 0 | `T0` | `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | `0.06` |
| `normal_visible_detail_zone` | `0.4` | 1 | `T1` | `0.16 Optimal @Snapmaker U1 (0.4 nozzle).json` | `0.16` |
| `structural_shell_zone` | `0.6` | 2 | `T2` | `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | `0.24` |
| `bulk_zone` | `0.8` | 3 | `T3` | `0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | `0.40` |

## Generated Workflow Manifest

Generator:

```text
tools/amp_generate_orca_gui_workflow_manifest.py
```

Command:

```text
python tools\amp_generate_orca_gui_workflow_manifest.py --packet outputs\amp_plan_packet_001 --out outputs\amp_orca_gui_workflow_bridge
```

Generated ignored outputs:

```text
outputs\amp_orca_gui_workflow_bridge\orca_gui_setup_manifest.json
outputs\amp_orca_gui_workflow_bridge\orca_gui_setup_instructions.md
outputs\amp_orca_gui_workflow_bridge\expected_tool_map.json
outputs\amp_orca_gui_workflow_bridge\expected_gcode_checks.json
outputs\amp_orca_gui_workflow_bridge\region_to_orca_tool_table.csv
```

The manifest records:

- region name
- inferred region STL path
- AMP recommended tool class
- Orca tool index
- expected T command
- expected nozzle diameter
- selected U1 process profile
- selected AMP layer height
- fallback tool
- risk flags

## Expected Tool Map

The generated expected tool map is:

| Region | Expected nozzle | Expected T command |
| --- | ---: | --- |
| `micro_detail_zone` | `0.2` | `T0` |
| `normal_visible_detail_zone` | `0.4` | `T1` |
| `structural_shell_zone` | `0.6` | `T2` |
| `bulk_zone` | `0.8` | `T3` |

## G-code Conformance Validation Result

Validator:

```text
tools/amp_validate_orca_mixed_nozzle_gcode_against_plan.py
```

Command:

```text
python tools\amp_validate_orca_mixed_nozzle_gcode_against_plan.py --packet outputs\amp_plan_packet_001 --gcode "C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\gcode\official_orca_mixed_probe_0p12_fixed_models.gcode" --expected-tool-map outputs\amp_orca_gui_workflow_bridge\expected_tool_map.json --out outputs\amp_orca_gui_workflow_bridge\orca_gui_gcode_validation.json --markdown outputs\amp_orca_gui_workflow_bridge\orca_gui_gcode_validation.md
```

Result:

```text
PASS
errors=0
warnings=3
```

Validation checks passed:

- G-code file exists.
- Header includes the expected used nozzle classes: `0.2`, `0.4`, `0.6`, `0.8`.
- Active tool commands include `T0`, `T1`, `T2`, and `T3`.
- Tool command count is greater than zero.
- Region names are present in G-code comments.
- No forbidden touchscreen/safety claim text was found.

## Warnings And Limitations

Validator warnings:

```text
Nozzle header contains more tool-slot values than AMP expected used nozzle classes; treat unused duplicate slots as preset artifacts if no extra active T command appears.
Layer-height observations are G-code-derived; official Orca manual workflow may use shared/global layer height.
Observed print_settings_id `0.12mm Mixed Probe @AMP Mixed ToolChanger`; manual baseline may expose one global process profile.
```

These warnings are expected for this bridge:

- The fifth `0.8` header value is an unused extra tool slot from the custom Orca preset.
- The official Orca GUI baseline uses a shared `0.12mm Mixed Probe` process rather than AMP's richer per-region U1 process/layer-height plan.
- The bridge validates representation and mapping, not physical behavior.

## What This Proves

Official Orca GUI can produce manual mixed-nozzle G-code for the repaired four-region probe.

AMP can generate a workflow manifest and validation target for that official GUI workflow.

The exported G-code contains the expected used nozzle classes and active `T0`, `T1`, `T2`, and `T3` commands.

The extra fifth `0.8` nozzle entry can be treated as an unused preset/tool-slot artifact for this probe because no `T4` path is active.

Official Orca remains the manual/static mixed-nozzle baseline.

AMP remains the automatic planner, validator, sidecar, fallback, and execution-gating layer.

## What This Does Not Prove

This does not implement AMP-driven mixed-nozzle slicing.

This does not automate the official Orca GUI.

This does not validate physical mixed-nozzle behavior.

This does not prove Snapmaker U1 touchscreen compatibility.

This does not bypass Snapmaker validation.

This does not prove independent per-tool or per-region layer height.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or safe printer execution.

## 3MF Roundtrip Update

The official Orca 3MF/project preservation probe is documented here:

```text
docs/benchmarks/AMP_Official_Orca_3MF_RoundTrip_Preservation_001.md
```

Result:

- original 3MF exists
- reopened project preserved the four region objects
- object-to-tool assignments are stored as extruder metadata `1`, `2`, `3`, and `4`
- project-level nozzle vector `0.2,0.4,0.6,0.8,0.8` is preserved
- mixed probe process/printer IDs are preserved
- full per-region AMP process/layer-height intent remains sidecar-authoritative

Decision:

Use official Orca 3MF as the first manual execution/review bridge, with AMP sidecar JSON remaining authoritative for planner intent, fallback, local-Z, and safety metadata.

## Next Bridge

The next bridge is:

```text
AMP plan packet
-> official Orca 3MF/project setup
-> AMP sidecar authority
-> G-code export validation after project round trip
```

The next specific question is whether a G-code export after reopening the 3MF remains conformant with the AMP expected tool map:

- expected nozzle classes `0.2`, `0.4`, `0.6`, `0.8`
- active `T0`, `T1`, `T2`, `T3`
- no extra active tool beyond the unused preset slot
- object comments still carrying region identity

Until that export-after-roundtrip is tested, 3MF/project preservation is valid for representation, not physical execution.
