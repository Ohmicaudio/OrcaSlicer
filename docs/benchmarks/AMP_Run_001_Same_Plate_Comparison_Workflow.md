# AMP Run 001 Same-Plate Comparison Workflow

## Purpose

This workflow creates a visual side-by-side comparison for AMP Run 001 by placing a stock-profile object and an experimental effective-width object on the same Snapmaker Orca plate.

The goal is to make stock-vs-experimental path differences visible in a single G-code preview window. This is still a profile-only benchmark. It does not validate print strength, surface quality, dimensional accuracy, bonding, or physical mixed-nozzle behavior.

## Preferred Workflow

Use Snapmaker Orca's GUI object settings for the first same-plate comparison.

1. Open Snapmaker Orca.
2. Select the Snapmaker U1 0.4 mm printer profile.
3. Select the stock U1 0.4 process profile.
4. Import one Run 001 benchmark STL, such as:

   ```text
   outputs/amp_run_001/models/generated/thin_wall_comb.stl
   ```

5. Duplicate the object on the same plate.
6. Move the stock copy to the left side of the plate.
7. Move the experimental copy to the right side of the plate.
8. Leave the left object on stock settings.
9. Apply object-level process overrides to the right object:

   ```text
   wall_generator: arachne
   outer_wall_line_width: 0.42
   top_surface_line_width: 0.42
   support_line_width: 0.42
   inner_wall_line_width: 0.52
   internal_solid_infill_line_width: 0.52
   sparse_infill_line_width: 0.58
   ```

10. Slice the plate once.
11. Open the result in Snapmaker Orca Preview and/or Prusa G-code Viewer.
12. Compare both objects at the same layer height:

   ```text
   left: stock U1 profile
   right: experimental effective-width object overrides
   ```

## What To Look For

- outer-wall path preservation;
- inner-wall path count changes;
- infill spacing and path count changes;
- top-surface path behavior;
- thin-wall survival or dropout;
- text/detail path preservation;
- obvious overfill, missing paths, or broken islands.

Prusa G-code Viewer is useful here because it can show line-width visualization in one view. Snapmaker Orca Preview remains the primary viewer for Snapmaker U1 profile behavior.

## Current CLI Probe Result

Snapmaker Orca source includes a CLI assembly path that accepts per-object `print_params` through `load_assemble_list`. In principle, that path is a good fit for automated same-plate stock-vs-experimental benchmark generation.

Local probes on Snapmaker Orca V2.3.4 reached the `load_assemble_list` path, loaded the U1 machine/process/filament profiles, and applied the assemble-list parser. However, the CLI crashed during plate setup before exporting G-code, even for a single-object control assemble list with no experimental overrides.

Observed local exit code:

```text
-1073741819
```

Because the single-object control also crashed, the failure should not be treated as evidence that object-level line-width overrides are invalid. It only means this local CLI assembly path is not reliable enough for Run 001 automation yet.

## Upstream Orca CLI Probe

Official upstream OrcaSlicer V2.4.1 was also tested locally because it includes Snapmaker U1 profiles and may have newer CLI behavior than Snapmaker Orca V2.3.4.

Executable tested:

```text
C:\Users\d\tools\OrcaSlicer\V2.4.1_portable_full\orca-slicer.exe
```

Release:

```text
OrcaSlicer v2.4.1 Official Release
Published: 2026-06-28
```

The upstream Orca CLI successfully sliced `thin_wall_comb.stl` with its bundled exact U1 stock profile:

```text
C:\Users\d\tools\OrcaSlicer\V2.4.1_portable_full\resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json
C:\Users\d\tools\OrcaSlicer\V2.4.1_portable_full\resources\profiles\Snapmaker\process\0.20 Standard @Snapmaker U1 (0.4 nozzle).json
C:\Users\d\tools\OrcaSlicer\V2.4.1_portable_full\resources\profiles\Snapmaker\filament\Snapmaker PLA @U1.json
```

It also successfully sliced a same-plate assemble-list probe with two copies of `thin_wall_comb.stl`:

```text
left/object 1: stock profile behavior
right/object 2: experimental effective-width object print_params
```

Generated local file:

```text
outputs/amp_run_001/upstream_orca_cli_probe/same_plate/slice/plate_1.gcode
```

This file opens in Prusa G-code Viewer as a same-view comparison plate. Treat it as an upstream-Orca CLI comparison artifact, not as a Snapmaker Orca V2.3.4 result.

The useful conclusion is:

- `load_assemble_list` plus object-level `print_params` is a viable same-plate comparison mechanism in upstream Orca V2.4.1.
- The same path is not locally stable in Snapmaker Orca V2.3.4.
- For Snapmaker-branded validation, GUI same-plate slicing remains the preferred path unless the Snapmaker CLI crash is understood or Snapmaker publishes an updated CLI build with the upstream behavior.

## Why Not Use Synthetic Merged G-code First

A synthetic comparison G-code can be made by translating stock and experimental toolpaths into one visual-only file, but that file would not be a real Snapmaker Orca slice. It may still be useful later as a viewer aid, but the preferred evidence path is a real slicer-generated same-plate preview from Snapmaker Orca whenever the GUI allows it.

## Pass Criteria

- Both objects appear on one plate.
- The left object uses stock U1 profile behavior.
- The right object uses only the experimental effective-width overrides listed above.
- The resulting preview shows both objects in the same layer view.
- The benchmark notes clearly label the comparison as profile-only.
- No production profiles are modified.
- No C++ or slicer behavior is modified.

## Fail Criteria

- The GUI does not expose the needed object-level line-width overrides.
- The right object silently inherits the same line-width behavior as the left object.
- The generated plate cannot be sliced.
- The exported G-code cannot be opened in a viewer.
- The result is presented as proof of strength, surface quality, dimensional accuracy, or mixed physical nozzle behavior.

## Next Follow-Up

If the GUI workflow succeeds, capture screenshots of the same layer in Snapmaker Orca Preview or Prusa G-code Viewer and update the Run 001 results document with:

- model name;
- stock object location;
- experimental object location;
- settings overridden;
- screenshots collected;
- visual observations;
- limitations.

If the GUI workflow fails, keep the CLI probe notes and move to a clearly labeled visual-only merged G-code comparison helper.
