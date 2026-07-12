# AMP Milestone 003: Automatic Orca 3MF Handoff

## Summary

AMP can now apply an offline plan packet to a compatible official Orca 3MF template without manual object-to-tool assignment.

The handoff tool updates Orca's object-level extruder metadata and project nozzle vector, embeds the AMP sidecar packet under `Metadata/AMP/`, and writes a deterministic new 3MF. An independent validator checks the generated package against the source AMP packet.

This milestone automates project representation only. It does not slice, generate production G-code, connect to a printer, start a print, bypass Snapmaker validation, or validate physical mixed-nozzle behavior.

## Tools

Generator:

```text
tools/amp_orca_3mf_handoff.py
```

Validator:

```text
tools/amp_validate_orca_3mf_handoff.py
```

Focused tests:

```text
tests/tools/test_amp_generate_orca_3mf_handoff.py
tests/tools/test_amp_validate_orca_3mf_handoff.py
```

## Real Integration Input

Known-good official Orca project template:

```text
C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\orca_official_mixed_nozzle_original.3mf
```

Template SHA-256:

```text
5BF496E71255F45CD47943A6F0A4D5318123B3CC37721F0217BDD121ED7E19C7
```

AMP packet:

```text
B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_plan_packet_001
```

## Generation Command

```text
python tools\amp_orca_3mf_handoff.py ^
  --template "C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\orca_official_mixed_nozzle_original.3mf" ^
  --packet "B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_plan_packet_001" ^
  --out outputs\amp_orca_3mf_handoff\amp_generated_orca_handoff.3mf
```

Result:

```text
region_count=4
nozzle_diameters=0.2,0.4,0.6,0.8
```

Generated 3MF SHA-256:

```text
FD277845AECB7C6F0BA1B9F8C2D15077B9B4DBA48235A86E7FDEC5E21CFACFE6
```

An identical second generation produced the same SHA-256.

## Generated Mapping

| Region | Orca extruder | Expected G-code tool | Nozzle class |
| --- | ---: | --- | ---: |
| `micro_detail_zone` | 1 | `T0` | `0.2` |
| `normal_visible_detail_zone` | 2 | `T1` | `0.4` |
| `structural_shell_zone` | 3 | `T2` | `0.6` |
| `bulk_zone` | 4 | `T3` | `0.8` |

The template's fifth `0.8` tool slot remains present and unused. The validator reports it as a warning rather than treating it as another AMP region.

## Package Preservation

The original template contained 18 ZIP members. The generated package contains 29.

Of the original members:

- 16 remain byte-identical.
- `Metadata/model_settings.config` is structurally rewritten with AMP extruder assignments.
- `Metadata/project_settings.config` is structurally rewritten with the AMP nozzle vector.

Added AMP members:

```text
Metadata/AMP/debug_artifact.json
Metadata/AMP/handoff_manifest.json
Metadata/AMP/per_region_gcode_status.json
Metadata/AMP/plan.json
Metadata/AMP/process_queue.json
Metadata/AMP/regions.json
Metadata/AMP/resolution_field.json
Metadata/AMP/risk_report.md
Metadata/AMP/source_template.sha256
Metadata/AMP/tool_assignments.json
Metadata/AMP/toolchange_schedule.json
```

No mesh, thumbnail, plate image, object model, relationship, or content-type member changed.

## Independent Validation

Command:

```text
python tools\amp_validate_orca_3mf_handoff.py ^
  --3mf outputs\amp_orca_3mf_handoff\amp_generated_orca_handoff.3mf ^
  --packet "B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_plan_packet_001" ^
  --out outputs\amp_orca_3mf_handoff\validation.json
```

Result:

```text
PASS
errors=0
warnings=1
```

The warning is the expected unused fifth template tool slot.

The validator separately checks region/extruder assignments, the leading nozzle vector, source packet preservation, embedded handoff metadata, and the source-template hash contract.

## Official Orca CLI Control

Official Orca v2.4.1 CLI `--info` was run against both the untouched template and the generated handoff.

Both reached project configuration validation and exited `-18` with the same pre-existing template/profile error:

```text
bridge_line_width: Bridge line width must not exceed nozzle diameter: 0.800000
```

This error is not introduced by the AMP handoff because the untouched original produces the identical result. It is limited to this CLI inspection path; the fresh GUI acceptance run below succeeded.

## Fresh Official Orca GUI Acceptance

Official Orca v2.4.1 was launched in a separate process with the generated project path.

Observed window title:

```text
amp_generated_orca_handoff - OrcaSlicer
```

Orca's debug log confirms:

- the generated project loaded with four objects;
- slicing started for all four objects;
- G-code generation completed;
- the plate slice-valid state changed to valid;
- the preview loaded the generated G-code;
- the sliced-plate package embedded `Metadata/plate_1.gcode`.

Sliced-plate package:

```text
outputs/amp_orca_3mf_handoff/amp_generated_orca_handoff.gcode.3mf
```

Package size and SHA-256:

```text
238,169 bytes
3ED69EC76C2CE15FC738170AEAAAF9D867FC8682D63893826E40B7BCF90F7ED3
```

Extracted G-code:

```text
outputs/amp_orca_3mf_handoff/amp_generated_orca_handoff.gcode
```

G-code size and SHA-256:

```text
1,206,918 bytes
730BE59D77C0A6D089A46829235E0A5BFB74C8F6793C700C1302BF6D99D65D9A
```

AMP G-code conformance validator result:

```text
PASS
errors=0
warnings=3
```

Observed G-code evidence:

| Field | Result |
| --- | --- |
| Nozzle header | `0.2,0.4,0.6,0.8,0.8` |
| Unique planned nozzle classes | `0.2,0.4,0.6,0.8` |
| Active tools | `T0,T1,T2,T3` |
| Tool command count | 80 |
| Region identities | all four present |
| Print settings ID | `0.12mm Mixed Probe @AMP Mixed ToolChanger` |
| Forbidden claim text | none |

The three warnings are the existing extra unused fifth tool slot, shared/global layer-height limitations in the official Orca baseline, and the shared mixed-probe process ID. They do not invalidate the region/tool/nozzle mapping result.

The automatic output was also compared with the earlier manually configured official Orca baseline. Layer count, tool commands, extrusion moves, travel moves, positive E, extrusion-role counts, and the M73-derived time estimate are identical. See `docs/benchmarks/AMP_Orca_3MF_Handoff_Parity_001.md`.

## Fail-Closed Behavior

Generation stops without replacing an existing output when it encounters:

- a missing or malformed AMP process queue;
- a malformed Orca XML or JSON metadata member;
- a missing planned region;
- duplicate planned or template region names;
- insufficient configured Orca tool slots;
- a missing required 3MF metadata member;
- an in-place template/output path.

## Current Boundary

The working bridge is now:

```text
AMP offline plan packet
-> compatible official Orca 3MF template
-> automatic object/tool/nozzle metadata handoff
-> embedded AMP sidecar authority
-> independent package validation
-> successful official Orca GUI load and slice
-> sliced-plate package with embedded G-code
-> successful AMP G-code conformance validation
```

## Non-Claims

- This does not implement AMP-driven mixed-nozzle slicing inside Orca.
- This does not validate physical U1 mixed-nozzle behavior.
- This does not prove Snapmaker touchscreen compatibility.
- This does not bypass Snapmaker nozzle validation or safety behavior.
- This does not authorize printing the generated project.
- Hardware preflight remains `not_ready`.
