# AMP Proxy Bead-Width Characterization Run 001

## Purpose

This package defines the first physical/proxy test for Adaptive Manufacturing Planner bead-width behavior on available FDM/FFF hardware.

The goals are:

- Measure actual bead width and wall behavior across speed, temperature, and line-width settings.
- Validate the measurement method before U1 hardware is available.
- Support AMP's resolution-allocation philosophy: spend resolution only where it earns its keep.
- Compare physical coupon behavior against slicer preview and G-code expectations.

## Scope

This is generic FDM/FFF proxy testing.

Allowed hardware:

- Bambu or other available FDM/FFF printer.
- Single-nozzle hardware.
- One material for the first run, preferably PLA or PETG.

This is not U1 validation. This is not mixed-nozzle validation. Bambu or other proxy printer results may inform bead-width measurement methods, but they do not validate Snapmaker U1 nozzle-state behavior, toolchange behavior, purge/wipe behavior, calibration behavior, or mixed physical nozzle behavior.

## Test Coupons

Generate coupons with:

```powershell
python tools/amp_generate_bead_width_coupons.py
```

Default output:

```text
outputs/amp_proxy_characterization/models/
```

Generated coupons:

- `single_wall_width_coupon.stl`
- `wall_adjacency_coupon.stl`
- `top_surface_coupon.stl`
- `detail_surrogate_coupon.stl`

Do not commit generated STL files unless explicitly approved.

## Coupon Intent

### Single-wall strip

Purpose:

- Measure actual bead width for nominal line-width settings.
- Check whether bead width is stable across long straight paths.

Measurements:

- Printed wall width at several positions.
- Any visible waviness, gaps, or over-extrusion.
- Difference between commanded line width and actual bead width.

### Two-wall / adjacency coupon

Purpose:

- Check how adjacent walls behave when line width changes.
- Expose overfill, wall merging, and gap behavior.

Measurements:

- Overall wall thickness.
- Visible gap/merge behavior between adjacent walls.
- Dimensional deviation at each strip.

### Top-surface coupon

Purpose:

- Check whether wider internal/top-region settings make top surfaces visibly worse.
- Compare previewed top fill against printed top-surface appearance.

Measurements:

- Top-surface smoothness.
- Visible ridges, gaps, or overfill.
- Dimensional deviation across the coupon.

### Detail surrogate coupon

Purpose:

- Check whether small cosmetic features survive width changes.
- Provide a proxy for text, logos, badges, trim faces, and speaker-ring detail.

Measurements:

- Small feature readability.
- Edge definition.
- Whether preview-visible features survive the print.

## Test Matrix

Start with one material and one nozzle size.

Suggested first material:

- PLA, if available.
- PETG only if PLA is not representative for the intended workflow.

Suggested line widths:

| Width | Intent |
| ---: | --- |
| stock profile width | baseline |
| 0.52 mm | moderate wider-region proxy |
| 0.58 mm | aggressive sparse/internal-region proxy |

Suggested nozzle temperatures:

| Material | Low | Middle | High |
| --- | ---: | ---: | ---: |
| PLA | normal profile minus 5 C | normal profile | normal profile plus 5 C |
| PETG | normal profile minus 5 C | normal profile | normal profile plus 5 C |

Suggested speeds:

| Speed tier | Intent |
| --- | --- |
| stock profile speed | baseline |
| moderate reduction | flow-stability check |
| moderate increase | stress check |

Keep the first matrix small. Do not combine every width, temperature, and speed until the measurement method is proven.

## Measurements

Record:

- Printer and firmware/software version.
- Slicer and profile used.
- Material brand/type/color.
- Nozzle diameter.
- Requested line width.
- Speed setting.
- Temperature setting.
- Actual bead width.
- Wall thickness.
- Dimensional deviation.
- Visible artifacts.
- Under-extrusion or over-extrusion signs.
- Top-surface appearance.
- Notes on where slicer preview diverges from print.

## Tools

Recommended:

- Calipers.
- Macro photo or microscope photo if available.
- Spreadsheet or CSV.

Optional:

- Scale.
- Repeat prints for variability.
- Prusa G-code Viewer or Snapmaker Orca preview screenshots for comparison.

## Suggested CSV Columns

```text
run_id,printer,material,nozzle_diameter,nominal_line_width,speed_setting,temperature_c,coupon,measurement_location,actual_width_mm,wall_thickness_mm,dimension_error_mm,artifact_notes,preview_divergence_notes
```

## Non-Claims

Bambu tests do not validate U1 behavior.

Bambu tests do not validate mixed physical nozzle behavior.

Preview/G-code does not prove strength.

Physical coupon tests still do not prove final part strength without proper mechanical testing.

Coupon results do not prove U1 touchscreen nozzle-state behavior, Fluidd-started mixed-nozzle behavior, purge/wipe behavior, bonding behavior, or toolhead calibration behavior.

## Pass Criteria

The proxy method passes if:

- Coupons slice and print without toolpath errors.
- Actual bead-width measurements can be repeated consistently enough to compare settings.
- The measurement notes identify where preview and physical output agree or diverge.
- Results remain clearly labeled as proxy FDM characterization.

## Fail Criteria

The proxy method fails if:

- Coupons cannot be measured repeatably.
- Width, speed, and temperature settings are not recorded.
- Results are described as U1 validation.
- Results are described as mixed-nozzle validation.
- Strength, surface-quality, or bonding conclusions are claimed without dedicated tests.

## Next Step After Run 001

Use proxy coupon results to decide whether the Stage 1 experimental effective-width settings should stay at:

- stock exterior/detail settings;
- moderate internal widening;
- aggressive sparse/internal widening;
- or a more conservative follow-up profile for Run 002.
