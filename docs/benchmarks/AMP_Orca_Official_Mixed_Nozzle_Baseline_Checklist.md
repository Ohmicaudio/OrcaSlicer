# AMP Orca Official Mixed Nozzle Baseline Checklist

## Purpose

Checklist for inspecting official Orca mixed nozzle-size baseline output.

Use with:

`docs/benchmarks/AMP_Orca_Official_Mixed_Nozzle_Baseline_001.md`

This is a manual inspection checklist. It does not modify slicer behavior.

## Source References

- Official Orca mixed nozzle-size workflow: <https://www.orcaslicer.com/wiki/guides/mixed_nozzle_sizes>
- Orca discussion on shared layer-height limitation: <https://github.com/OrcaSlicer/OrcaSlicer/discussions/10175>

## Setup Checklist

- [ ] Record slicer name and version.
- [ ] Record whether the test is upstream Orca or Snapmaker Orca.
- [ ] Record printer/machine profile.
- [ ] Configure extruder/tool nozzle diameters:
  - [ ] tool 1: `0.2`
  - [ ] tool 2: `0.4`
  - [ ] tool 3: `0.6`
  - [ ] tool 4: `0.8`
- [ ] Use percentage-based line widths where possible.
- [ ] Assign model regions manually:
  - [ ] `micro_detail_zone` -> `0.2`
  - [ ] `normal_visible_detail_zone` -> `0.4`
  - [ ] `structural_shell_zone` -> `0.6`
  - [ ] `bulk_zone` -> `0.8`
- [ ] Record whether assignment used Filament for Features, color painting, object assignment, or another route.
- [ ] Save project/3MF if testing persistence.
- [ ] Export G-code.

## G-code Inspection Checklist

Inspect the exported G-code for:

- [ ] `nozzle_diameter` header values.
- [ ] `print_settings_id`.
- [ ] filament/tool metadata.
- [ ] `T0` / `T1` / `T2` / `T3` or equivalent tool-selection commands.
- [ ] active tool count.
- [ ] line-width comments such as `;WIDTH:`.
- [ ] layer-height comments such as `;HEIGHT:`.
- [ ] feature/tool assignment comments, if present.
- [ ] wipe tower or purge behavior, if generated.
- [ ] whether all four U1 tool classes are represented.

## Project / 3MF Persistence Checklist

If a project file is saved and re-opened:

- [ ] Extruder nozzle diameters are preserved.
- [ ] Percentage line-width settings are preserved.
- [ ] Region/tool assignments are preserved.
- [ ] Filament for Features assignments are preserved.
- [ ] Painted assignments are preserved, if used.
- [ ] Exported G-code after reload matches the intended tool-class mapping.

## Layer-Height Checklist

Record:

- [ ] global layer height setting.
- [ ] whether all tools share one layer height.
- [ ] whether any per-tool layer-height UI exists.
- [ ] whether G-code shows different layer heights by tool.
- [ ] whether layer-height behavior matches Orca discussion #10175 expectations.

## Snapmaker U1 Constraint Checklist

For Snapmaker Orca / U1-oriented tests:

- [ ] Record whether the workflow permits more than one nozzle diameter in the project.
- [ ] Record whether the UI collapses to one nozzle diameter per plate/object.
- [ ] Record whether slicing/export is blocked.
- [ ] Record whether G-code header uses one or multiple nozzle diameter values.
- [ ] Record touchscreen compatibility as unknown unless validated on hardware.
- [ ] Do not bypass Snapmaker validation paths.

## AMP Comparison Checklist

Compare official manual assignment against AMP offline packet output:

- [ ] same region names
- [ ] same intended tool classes
- [ ] same or explainably different line-width assumptions
- [ ] same or explainably different layer-height assumptions
- [ ] AMP confidence values
- [ ] AMP fallback reasons
- [ ] AMP preflight requirements
- [ ] gaps between manual Orca workflow and AMP automated planning

## Required Non-Claims

Do not claim:

- AMP implements mixed-nozzle slicing.
- Official Orca baseline validates U1 mixed-nozzle behavior.
- Snapmaker touchscreen-compatible mixed-nozzle execution works.
- Physical print strength is proven.
- Surface quality is proven.
- Local-Z or independent per-tool layer height is implemented.
