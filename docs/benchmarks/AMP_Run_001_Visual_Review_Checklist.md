# AMP Run 001 Visual Review Checklist

## Purpose

This checklist guides manual review of Run 001 G-code outputs in Snapmaker Orca preview and, where useful, Prusa G-code Viewer.

Run 001 compares profile-only slicing behavior. Same-plate comparison is for visual inspection. Preview/G-code cannot prove print strength. Preview/G-code cannot prove surface quality. Run 001 does not validate physical mixed-nozzle behavior.

## Local Files

Open the same-plate comparison files first:

```text
outputs/amp_run_001/gcode/thin_wall_comb/same_plate_stock_vs_experimental.gcode
outputs/amp_run_001/gcode/large_bracket_box/same_plate_stock_vs_experimental.gcode
outputs/amp_run_001/gcode/embossed_text_plate/same_plate_stock_vs_experimental.gcode
outputs/amp_run_001/gcode/speaker_adapter_ring/same_plate_stock_vs_experimental.gcode
outputs/amp_run_001/gcode/led_ring_face/same_plate_stock_vs_experimental.gcode
outputs/amp_run_001/gcode/sloped_surface_torture/same_plate_stock_vs_experimental.gcode
```

Use the separate stock-only and experimental-only files when same-plate review suggests a difference that needs isolation:

```text
outputs/amp_run_001/gcode/<model>/stock_only.gcode
outputs/amp_run_001/gcode/<model>/experimental_only.gcode
```

## Screenshot Storage

Store local screenshots under:

```text
outputs/amp_run_001/screenshots/
```

Do not commit screenshots unless explicitly approved.

Suggested naming:

```text
outputs/amp_run_001/screenshots/<model>_<viewer>_<layer-or-feature>_<stock-or-experimental>.png
```

## General Review Criteria

Acceptable:

- Exterior walls remain comparable to stock in preview.
- Top surfaces are not visibly coarser or sparse.
- Thin walls and small features remain present.
- Internal paths are reduced or widened where expected.
- No obvious overfill, missing loops, or unstable paths.
- Same-plate visual comparison matches separate stock/experimental behavior.

Blocker:

- Thin walls disappear.
- Cosmetic outer walls visibly degrade.
- Top surfaces become sparse, coarse, or unstable.
- Experimental profile loses expected detail features.
- Experimental profile creates obvious overfill or self-overlap-looking regions.
- Same-plate output contradicts separate stock-only or experimental-only output.

## Viewer Procedure

1. Open the same-plate G-code in Snapmaker Orca preview.
2. Identify which side/object is stock and which is experimental from the generated same-plate setup.
3. Use the layer slider to inspect bottom layers, mid-height layers, top surface layers, and any feature-specific layers.
4. Compare path count, line spacing, exterior walls, top surfaces, infill, and travel density.
5. Capture screenshots only for clear differences, likely regressions, or useful examples.
6. Open the same G-code in Prusa G-code Viewer if a second visual check is useful.
7. If same-plate behavior is unclear, open `stock_only.gcode` and `experimental_only.gcode` separately.

## Model Checklist

### `thin_wall_comb`

Inspect:

- Narrowest comb teeth.
- Transition from very thin to thicker walls.
- Bottom layer and representative mid-height layers.

Checklist:

- [ ] Thin walls remain visible in experimental preview.
- [ ] Experimental preview does not merge adjacent teeth unexpectedly.
- [ ] Exterior walls remain comparable to stock.
- [ ] No obvious overfill-looking regions.
- [ ] Same-plate comparison matches separate stock/experimental behavior.

Blocker notes:

- Any missing tooth or merged detail should block further widening until settings are reduced or isolated.

### `large_bracket_box`

Inspect:

- Outer box walls.
- Internal/bulk wall regions.
- Corners and hole/perimeter regions.
- Infill-heavy mid-height layers.

Checklist:

- [ ] Exterior walls remain comparable to stock.
- [ ] Internal paths appear reduced/widened where expected.
- [ ] Holes or mounting features do not lose perimeter definition.
- [ ] No missing loops around corners or holes.
- [ ] Same-plate comparison matches separate stock/experimental behavior.

Blocker notes:

- Cosmetic degradation on exterior box walls should block using this profile unchanged.

### `embossed_text_plate`

Inspect:

- Raised text strokes.
- Top surface around text.
- Layers where text begins and ends.

Checklist:

- [ ] Text strokes remain readable in experimental preview.
- [ ] Top surfaces remain dense and comparable to stock.
- [ ] Experimental preview does not show obvious overfill around text.
- [ ] Extra parsed positive E from metrics has a plausible visual explanation.
- [ ] Same-plate comparison matches separate stock/experimental behavior.

Blocker notes:

- Loss of text readability or visible top-surface coarsening should block this exact profile for cosmetic/text cases.

### `speaker_adapter_ring`

Inspect:

- Inner and outer ring perimeters.
- Mounting holes or boss-like features.
- Top and bottom surface rings.

Checklist:

- [ ] Ring perimeters remain complete.
- [ ] Mounting features retain expected paths.
- [ ] Large parsed positive E reduction does not correspond to missing walls.
- [ ] Internal/bulk region reductions look plausible.
- [ ] Same-plate comparison matches separate stock/experimental behavior.

Blocker notes:

- Any missing ring perimeter or hole feature should block adapter/ring use until settings are revised.

### `led_ring_face`

Inspect:

- Cosmetic face surface.
- Small LED/detail features.
- Radial feature spacing.
- Top layers.

Checklist:

- [ ] Cosmetic face remains comparable to stock.
- [ ] Small detail features remain present.
- [ ] Top surfaces do not become visibly sparse.
- [ ] Parsed positive E reduction does not correspond to missing visible geometry.
- [ ] Same-plate comparison matches separate stock/experimental behavior.

Blocker notes:

- Visible face degradation should block use for cosmetic U1/Ohmic examples.

### `sloped_surface_torture`

Inspect:

- Shallow sloped regions.
- Stepped regions.
- Topmost paths on the ramp.
- Any regions where Arachne path spacing changes visibly.

Checklist:

- [ ] Sloped surfaces remain plausible in experimental preview.
- [ ] Path spacing does not look visibly coarse on cosmetic slopes.
- [ ] Large travel/file-size reduction does not come from missing surfaces.
- [ ] No obvious unsupported sparse regions appear.
- [ ] Same-plate comparison matches separate stock/experimental behavior.

Blocker notes:

- Coarse-looking slopes should trigger a conservative top-surface/outer-wall setting pass.

## Review Output Template

Use one block per model:

```text
Model:
Viewer:
Files opened:
Layer/features inspected:
Stock observations:
Experimental observations:
Same-plate agreement:
Screenshots captured:
Acceptable:
Blockers:
Recommended setting change:
Physical print needed:
```

## Follow-Up

After visual review:

- Update `docs/benchmarks/AMP_Run_001_Findings.md` only with reviewed observations.
- Keep screenshots local unless explicitly approved.
- Do not claim print-time, strength, print-quality, dimensional, or bonding results without hardware.
- Use visual review results to decide whether Run 002 should use the same experimental profile, a more conservative internal-width profile, or a model-specific split.
