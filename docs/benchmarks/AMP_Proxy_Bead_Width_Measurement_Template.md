# AMP Proxy Bead-Width Measurement Template

## Purpose

This template records physical/proxy bead-width characterization measurements for AMP Stage 1.

The first intended use is a small Bambu or other available FDM/FFF proxy run with PLA, a 0.4 mm nozzle, and the generated AMP coupon models. These results can help validate the measurement method and bead-width assumptions, but they do not validate Snapmaker U1 behavior or physical mixed-nozzle behavior.

## Required Non-Claims

Bambu proxy tests do not validate U1 mixed-nozzle behavior.

Proxy coupon tests do not validate U1 touchscreen nozzle-state behavior, Fluidd-started mixed-nozzle behavior, U1 toolchange/purge behavior, U1 calibration behavior, or U1 bonding behavior.

Coupon tests do not prove final part strength. Dedicated mechanical testing would be required for strength claims.

Preview/G-code and coupon prints do not prove final product surface quality.

## First-Pass Test Set

Start small before expanding to a full matrix.

Recommended first pass:

| Coupon | Target line width | Speed | Nozzle temperature | Material |
| --- | ---: | ---: | ---: | --- |
| `single_wall_width_coupon` | 0.42 mm | 80 mm/s | 215 C | PLA |
| `single_wall_width_coupon` | 0.52 mm | 80 mm/s | 215 C | PLA |
| `single_wall_width_coupon` | 0.58 mm | 80 mm/s | 215 C | PLA |
| `wall_adjacency_coupon` | 0.42 mm | 80 mm/s | 215 C | PLA |
| `wall_adjacency_coupon` | 0.52 mm | 80 mm/s | 215 C | PLA |
| `wall_adjacency_coupon` | 0.58 mm | 80 mm/s | 215 C | PLA |
| `top_surface_coupon` | 0.42 mm | 80 mm/s | 215 C | PLA |
| `top_surface_coupon` | 0.52 mm | 80 mm/s | 215 C | PLA |
| `top_surface_coupon` | 0.58 mm | 80 mm/s | 215 C | PLA |
| `detail_surrogate_coupon` | 0.42 mm | 80 mm/s | 215 C | PLA |
| `detail_surrogate_coupon` | 0.52 mm | 80 mm/s | 215 C | PLA |
| `detail_surrogate_coupon` | 0.58 mm | 80 mm/s | 215 C | PLA |

After the measurement method is stable, expand speed and temperature:

| Variable | Suggested values |
| --- | --- |
| Speed | 40 / 80 / 120 mm/s |
| PLA nozzle temperature | 205 / 215 / 225 C |
| Target line width | 0.42 / 0.52 / 0.58 mm |

Do not run the full matrix until measurement repeatability is acceptable.

## Measurement Columns

Use these columns in a spreadsheet or CSV:

```text
run_id
printer
printer_firmware
material
material_brand
material_color
nozzle_diameter
slicer_profile
slicer_version
coupon_name
target_line_width
layer_height
speed
nozzle_temperature
bed_temperature
measured_single_wall_width_1
measured_single_wall_width_2
measured_single_wall_width_3
average_measured_width
wall_thickness
dimensional_deviation
visible_artifacts
top_surface_notes
adhesion_notes
pass_fail
notes
photo_path
preview_notes
```

CSV header:

```csv
run_id,printer,printer_firmware,material,material_brand,material_color,nozzle_diameter,slicer_profile,slicer_version,coupon_name,target_line_width,layer_height,speed,nozzle_temperature,bed_temperature,measured_single_wall_width_1,measured_single_wall_width_2,measured_single_wall_width_3,average_measured_width,wall_thickness,dimensional_deviation,visible_artifacts,top_surface_notes,adhesion_notes,pass_fail,notes,photo_path,preview_notes
```

## Measurement Record Template

```text
Run ID:
Printer:
Printer firmware:
Material:
Material brand:
Material color:
Nozzle diameter:
Slicer/profile:
Slicer version:
Coupon name:
Target line width:
Layer height:
Speed:
Nozzle temperature:
Bed temperature:

Measured single-wall width 1:
Measured single-wall width 2:
Measured single-wall width 3:
Average measured width:
Wall thickness:
Dimensional deviation:

Visible artifacts:
Top-surface notes:
Adhesion notes:
Preview notes:
Photo path:
Pass/fail:
Notes:
```

## Caliper Measurement Guidance

Use consistent technique:

- Let the coupon cool before measuring.
- Measure at three separated locations, not only at the cleanest-looking spot.
- Avoid measuring elephant-foot regions unless the test is specifically about first-layer behavior.
- Note whether measurements are from the middle of a wall, a corner, or a transition.
- Record caliper resolution if known.
- If a feature is too small or flexible for reliable caliper measurement, mark it as unreliable rather than forcing a number.

For single-wall coupons:

- Measure wall width near the left third, center, and right third.
- Avoid start/stop artifacts unless the measurement is intentionally checking seam behavior.
- Record visible waviness, inconsistent bead width, or tearing.

For wall-adjacency coupons:

- Measure total wall thickness.
- Note whether adjacent beads merge, leave a gap, or show overfill.
- Record whether the gap behavior matches slicer preview.

For top-surface coupons:

- Measure overall dimensions.
- Note top-surface ridges, gaps, scarring, or roughness.
- Use photos for comparison because calipers will not capture cosmetic surface quality well.

For detail-surrogate coupons:

- Note whether small raised features remain legible.
- Record edge rounding, missing strokes, or merged features.
- Use macro photos if available.

## Photo / Macro Photo Guidance

Store local photos under:

```text
outputs/amp_proxy_characterization/photos/
```

Do not commit photos unless explicitly approved.

Suggested naming:

```text
outputs/amp_proxy_characterization/photos/<run_id>_<coupon_name>_<width>_<speed>_<temp>.jpg
```

Useful photos:

- Top-down full coupon.
- Close-up of the measured wall.
- Close-up of start/stop or seam artifacts.
- Close-up of top-surface artifacts.
- Close-up of small detail features.

Include a ruler, caliper jaw, or known-size reference in photos where practical.

## Pass / Fail Guidance

Pass:

- Three width measurements are repeatable enough to compare settings.
- The print is stable enough to measure.
- Visible artifacts are recorded.
- Proxy status is clearly labeled.

Conditional:

- Measurements vary significantly but the variation is explainable.
- One coupon fails but other coupons in the same setting are measurable.
- Photo evidence is needed to interpret the result.

Fail:

- Coupon cannot be measured reliably.
- Under-extrusion, over-extrusion, or adhesion failure prevents useful measurement.
- Settings are not recorded.
- The result is described as U1 validation or mixed-nozzle validation.

## Results Summary Template

```text
Run ID:
Date:
Printer:
Material:
Nozzle:
Slicer/profile:

Summary:

Best-behaved target width:
Risky target width:
Temperature sensitivity:
Speed sensitivity:
Preview vs print agreement:
Recommended next setting:

Non-claims:
- Not U1 validation.
- Not mixed-nozzle validation.
- Not strength validation.
- Not final surface-quality validation.
```
