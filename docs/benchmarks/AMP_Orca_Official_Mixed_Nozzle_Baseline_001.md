# AMP Orca Official Mixed Nozzle Baseline 001

## Purpose

Establish official OrcaSlicer mixed nozzle-size support as the first manual/static baseline for AMP comparison.

Official OrcaSlicer documentation states that mixed nozzle sizes are supported since `v2.2.0-beta`:

<https://www.orcaslicer.com/wiki/guides/mixed_nozzle_sizes>

This baseline is not an AMP behavior-changing test. It is a representation and G-code inspection plan for comparing the official manual workflow against AMP's automated planner packet.

## Official Workflow Summary

Official Orca's documented workflow is manual/static:

- set nozzle diameter per extruder in machine settings
- make process profiles nozzle-agnostic by using percentage-based line widths
- assign tools to features using Filament for Features or painting workflows
- calibrate material/nozzle combinations, especially pressure advance and flow

This workflow should be treated as baseline capability. AMP should not claim that mixed nozzle-size workflows do not exist in Orca.

## AMP Difference

AMP targets automated mixed-resolution planning:

- geometry-driven region metadata
- continuous resolution demand
- quantized tool-class assignment
- cost gating
- confidence and fallback reasoning
- sidecar/debug packet contracts
- execution and preflight gating

The official Orca workflow is a useful manual baseline, not a replacement for the AMP planner.

## U1 Tool-Class Mapping

Use the current U1 ladder from `docs/benchmarks/AMP_U1_Tool_Capability_Matrix.md`:

| AMP region body | Baseline tool class | Intended role |
| --- | --- | --- |
| `micro_detail_zone` | `0.2` | fine/detail |
| `normal_visible_detail_zone` | `0.4` | normal visible/default |
| `structural_shell_zone` | `0.6` | structural shell |
| `bulk_zone` | `0.8` | bulk/internal |

This mapping is for baseline representation only. It does not validate U1 mixed physical nozzle behavior.

## Test Matrix

### A. Upstream Orca V2.4.1 Official Workflow

Attempt:

- per-extruder nozzle setup for `0.2`, `0.4`, `0.6`, and `0.8`
- percentage-based line widths
- manual feature/tool assignment using Filament for Features or painting
- G-code export
- optional 3MF/project save-load round trip

Inspect:

- `nozzle_diameter` header metadata
- `print_settings_id`
- `T` commands or equivalent tool-selection output
- active tool count
- line-width comments
- layer-height comments
- feature/tool assignment comments if present

### B. Snapmaker Orca V2.3.4 Workflow

Attempt the same baseline if UI/CLI/profile behavior allows it.

Record:

- whether Snapmaker Orca exposes the same workflow
- whether settings collapse to one nozzle per plate or object
- whether U1 process/profile constraints block the setup
- whether G-code export is possible
- how this interacts with known Snapmaker touchscreen/nozzle validation constraints

Snapmaker U1 mixed-nozzle execution remains blocked unless hardware behavior and validation constraints are understood.

### C. AMP Offline Packet Comparison

Compare the official manual assignment against the current AMP offline packet:

- region names
- planned tool classes
- line-width/layer-height recommendations
- cost and confidence fields
- fallback reasons
- execution/preflight requirements

AMP should not claim to replace the official manual workflow. The comparison should show what automation and safety metadata AMP adds.

## Shared Layer-Height Limitation

Mixed nozzle size does not necessarily imply independent layer heights.

OrcaSlicer discussion #10175 identifies shared layer height as a limitation for multi-nozzle, toolchanger, and IDEX workflows:

<https://github.com/OrcaSlicer/OrcaSlicer/discussions/10175>

The discussion describes a common need: fine surface/detail tools and coarse infill/bulk tools may need compatible but different layer heights, often in multiples of each other. This maps directly to AMP's future local-Z and multi-resolution planning direction.

This baseline should record whether layer height remains shared in official Orca output.

## What This Test Should Prove

This baseline should determine:

- whether official Orca can represent U1-like `0.2` / `0.4` / `0.6` / `0.8` manual assignments
- whether generated G-code preserves multiple nozzle diameters or tool classes
- whether expected tool selections are emitted
- whether layer height remains shared across tools
- whether 3MF/project save-load preserves manual assignments
- how the official manual workflow compares to AMP's offline automated packet

## What This Test Does Not Prove

This baseline does not prove:

- physical U1 mixed-nozzle behavior
- U1 touchscreen compatibility
- Snapmaker nozzle-validation compatibility
- automated geometry-driven assignment
- local-Z or independent per-tool layer-height implementation
- final strength, surface quality, bonding, or dimensional accuracy

## Pass / Caution / Fail Criteria

### Pass

- all four tool classes can be represented
- G-code export succeeds
- tool/nozzle metadata can be inspected
- tool assignments survive project save-load, if tested
- limitations are clearly documented

### Caution

- export succeeds but metadata is ambiguous
- tool assignment works only through GUI, not CLI
- project save-load is not tested
- layer height is shared
- Snapmaker Orca differs from upstream Orca

### Fail

- official workflow cannot represent the four tool classes
- G-code cannot be exported
- assignments collapse to one nozzle/tool
- generated output cannot be inspected well enough to compare against AMP

## Required Wording For Results

Use this wording in future results:

- This is an official Orca manual/static mixed-nozzle baseline.
- This does not implement AMP mixed-nozzle slicing.
- This does not validate U1 physical mixed-nozzle behavior.
- This does not bypass Snapmaker validation.
- AMP remains an automated planning, confidence, sidecar, and execution-gating layer.

## Next Action

Run this baseline against the existing AMP four-region bodies:

- `micro_detail_zone`
- `normal_visible_detail_zone`
- `structural_shell_zone`
- `bulk_zone`

Use the companion checklist:

`docs/benchmarks/AMP_Orca_Official_Mixed_Nozzle_Baseline_Checklist.md`
