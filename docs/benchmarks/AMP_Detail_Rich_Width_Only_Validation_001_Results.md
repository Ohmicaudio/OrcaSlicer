# AMP Detail-Rich Width-Only Validation 001 Results

## Purpose

This pass generates and slices a detail-rich AMP validation fixture to test the first conservative Stage 1 heuristic candidate:

```text
Stock
vs.
Width-only conservative
```

The goal is to decide whether width-only internal widening is worth carrying forward before any planner implementation touches slicing behavior.

## Fixture Description

Generated fixture:

```text
outputs/amp_detail_fixture/models/amp_detail_ring_fixture.stl
```

Generator:

```text
tools/amp_generate_detail_rich_validation_fixture.py
```

The generated STL is intentionally not committed.

The fixture is a ring/badge-like product surrogate with:

- visible cosmetic face;
- central ring opening;
- mounting holes;
- raised boss/counterbore-like regions around mounting holes;
- raised geometric text/logo surrogate;
- small bar/slot detail surrogate;
- raised pinstripe rings;
- thicker hidden backside/internal bulk.

True text mesh and real Ohmic logo geometry are deferred to future real-part input models. The current fixture uses geometric text/detail surrogates to avoid font and boolean dependencies.

Revision note:

- Rev A used a square-grid heightfield and produced an unacceptable low-poly visual result.
- Rev B replaces that with circular annular geometry, real holes, raised bosses, raised pinstripes, block-letter detail surrogates, and a backside bulk rib.
- The metrics below are from Rev B.

## Why This Model Is Decision-Relevant

This fixture is useful because it contains both sides of the AMP question:

- visible/detail regions that should be preserved;
- internal/bulk regions where wider paths may reduce path burden.

A plain ring or simple block would not answer whether AMP is preserving visible detail. This fixture is still synthetic, but it is decision-oriented rather than smoke-test-only geometry.

## Slicer Build And Method

- Target slicer: local CLI-hardened Snapmaker Orca build.
- Executable: `B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe`
- G-code header version: `Snapmaker Orca 2.3.5`
- Machine profile: `resources/profiles/Snapmaker/machine/Snapmaker U1 (0.4 nozzle).json`
- Stock process: `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`
- Width-only process: temporary ignored profile at `outputs/amp_detail_fixture/profiles/amp_detail_fixture_width_only.process.json`
- Filament: `resources/profiles/Snapmaker/filament/Snapmaker PLA @U1.json`
- Command ledger: `outputs/amp_detail_fixture/reports/detail_fixture_cli_commands.json`

Both Stock and Width-only CLI slices exited `0` and exported G-code.

Metrics were generated with:

```powershell
python tools/amp_gcode_metrics.py `
  outputs/amp_detail_fixture/gcode `
  --csv outputs/amp_detail_fixture/reports/metrics.csv `
  --summary outputs/amp_detail_fixture/reports/summary.md
```

## Variant Definitions

### Stock

Stock Snapmaker U1 0.4 profile.

Header-reported widths:

```text
external perimeters extrusion width = 0.45mm
perimeters extrusion width = 0.45mm
infill extrusion width = 0.45mm
solid infill extrusion width = 0.45mm
top infill extrusion width = 0.40mm
```

### Width-Only Conservative

Width-only candidate with no layer-height changes and no combined mode.

Header-reported widths:

```text
external perimeters extrusion width = 0.42mm
perimeters extrusion width = 0.52mm
infill extrusion width = 0.58mm
solid infill extrusion width = 0.52mm
top infill extrusion width = 0.42mm
```

## Metrics

| Metric | Stock | Width-only | Delta |
| --- | ---: | ---: | ---: |
| M73 estimate | 109 min | 107 min | -1.8% |
| G-code file size | 1,638,732 bytes | 1,536,873 bytes | -6.2% |
| Layer count | 33 | 33 | +0.0% |
| Extrusion moves | 1,055 | 1,226 | +16.2% |
| Travel moves | 49,768 | 45,624 | -8.3% |
| Positive E total | 1,237.189 | 1,293.074 | +4.5% |

Warnings:

- Filament usage comments were not present in the parsed Snapmaker G-code.
- The Snapmaker G-code uses `M83` relative extrusion. A separate visual-review parser treated positive `E` moves as extrusion for layer rendering. The current metrics table remains useful as a lightweight comparison, but material-use conclusions require slicer-reported filament, corrected parsing, or physical weighing.

Relative-extrusion sanity counters used for the visual review:

| Metric | Stock | Width-only | Direction |
| --- | ---: | ---: | --- |
| Extrusion moves | 1,247 | 1,458 | Width-only higher |
| Travel moves | 50,024 | 45,895 | Width-only lower |
| Positive relative E total | 1,941.234 | 2,306.316 | Width-only higher |

These counters reinforce the same caution signal: width-only reduced travel but increased local extrusion work on this geometry.

## Visual/Detail Regions To Preserve

These fixture regions must be reviewed in Snapmaker Orca preview before the candidate is trusted:

- raised geometric text/logo surrogate;
- small lower bar/slot detail surrogate;
- pinstripe groove rings;
- outer cosmetic face;
- central opening edge;
- mounting holes;
- boss/counterbore-like regions;
- chamfer-like sloped face.

## Internal/Bulk Regions Expected To Benefit

Width-only is expected to affect:

- thicker ring body;
- internal/perimeter mass away from the visible face;
- sparse infill regions;
- backside/internal bulk rib region.

The intended benefit is lower or simpler internal/bulk path burden while preserving visible/detail surfaces.

## Rev B Visual Preview Review

This is a preview-only review of the Rev B fixture. Preview does not prove surface quality. Preview does not prove strength. This does not validate physical mixed-nozzle behavior.

Reviewed files:

```text
outputs/amp_detail_fixture/gcode/stock.gcode
outputs/amp_detail_fixture/gcode/width_only.gcode
```

Local review images were generated from the G-code for inspection:

```text
outputs/amp_detail_fixture/visual_review/rev_b_stock_vs_width_layers_m83.png
outputs/amp_detail_fixture/visual_review/rev_b_stock_width_overlay_layers_m83.png
outputs/amp_detail_fixture/visual_review/rev_b_upper_logo_bosses_zoom_m83.png
outputs/amp_detail_fixture/visual_review/rev_b_lower_stripe_bulk_zoom_m83.png
```

These generated preview images are not committed.

Same-plate G-code was not available for this Rev B pass, so the review compares the separate Stock and Width-only G-code exports.

### Areas Inspected

| Area | Preview observation |
| --- | --- |
| Outer cosmetic face | Major outer annular paths remain present in both variants. No obvious missing exterior loop was visible in the reviewed layers. |
| Raised text/logo surrogate | Raised surrogate regions remain present in both variants. Width-only changes local fill direction/spacing behavior but does not visibly remove the surrogate features in the reviewed G-code layers. |
| Grooves/pinstripes | Stripe-like paths remain visible in the reviewed layers. Width-only does not obviously erase them, but the preview should still be checked in Snapmaker Orca before printing. |
| Mounting holes | Hole openings remain visible in both variants. No obvious closure of the inspected holes was seen in the generated layer previews. |
| Counterbores/bosses | Boss/counterbore-like islands remain present in both variants. Width-only adds local path density around some raised/detail layers. |
| Hidden backside/internal bulk | Width-only changes the internal/bulk path layout as expected, especially around the lower backside rib region. |
| Top surfaces | Top/detail layers remain present, but the width-only candidate changes local top-fill distribution enough that physical print review is required. |
| Missing loops | No obvious missing protected/detail loop was visible in the generated review sheets. |
| Overfill-looking risk | The visual review does not prove overfill, but the higher positive relative E total and increased extrusion moves make this a caution item. |

### Stock Vs Width-Only Notes

Width-only preserved the broad visible/detail geometry in preview, including the ring outline, central opening, raised detail surrogate, boss regions, and lower stripe/detail areas. That is the positive signal.

The caution signal is also clear: width-only did not simply reduce path burden. It reduced travel and file size, but it increased extrusion moves and positive relative E in this fixture. In the detail-bearing layers around the raised features and bosses, width-only often created denser or more segmented local path behavior.

This means the fixture does not support a blanket rule such as widening all internal lines. It supports a narrower rule candidate: preserve visible/detail regions, and consider internal widening only where the region is thick enough and the predicted path burden actually improves.

### Visual Review Recommendation

Recommendation: continue, but caution-marked.

Do not reject the width-only candidate yet because the preview did not show obvious loss of protected exterior/detail features. Do not promote it to an automatic AMP rule yet because this geometry shows increased extrusion complexity and higher positive relative E.

Next step for this fixture:

```text
Stock physical print
Width-only physical print
```

Only those two variants should be printed first. Layer-height-only and combined mode should remain blocked for this fixture until the width-only physical comparison is understood.

## Decision From This Fixture

The width-only result is a promising but caution-marked candidate pending visual and physical validation.

Reason:

- M73 estimate decreased by 1.8%.
- G-code file size decreased by 6.2%.
- Travel moves decreased by 8.3%.
- Layer count stayed unchanged, confirming this was not a hidden layer-height/combined test.

Caution:

- Extrusion moves increased by 16.2%.
- Positive E increased by 4.5%.
- Those increases may indicate extra local segmentation, changed perimeter/infill allocation, or detail/boss handling that needs viewer inspection.
- Preview must confirm that raised detail, grooves, holes, bosses, and cosmetic face features remain intact.
- Physical printing is still required before any print-performance conclusion.

## Next Required Visual Review

Manual Snapmaker Orca preview remains recommended as a second visual pass:

```text
outputs/amp_detail_fixture/gcode/stock.gcode
outputs/amp_detail_fixture/gcode/width_only.gcode
```

Check:

- no missing visible loops;
- text/detail surrogate remains present;
- grooves remain visible;
- mounting holes remain open;
- boss/counterbore-like regions remain plausible;
- cosmetic face does not show obvious degradation;
- internal/bulk path differences occur where expected.

Use Prusa G-code Viewer as a secondary view if useful.

## Next Required Physical Print Test

Print the fixture or a real Ohmic detail-ring part as:

```text
Stock
Width-only conservative
```

Record:

- printer;
- nozzle;
- material;
- slicer/profile;
- actual print time;
- visible outer wall quality;
- top/cosmetic face;
- grooves/text/detail visibility;
- hole quality;
- fitment, if applicable;
- material use or part weight, if measured;
- photos status;
- any artifacts or failures.

## Required Non-Claims

This does not claim strength improvement.

This does not claim surface-quality improvement.

This does not claim dimensional-accuracy improvement.

This does not validate physical mixed-nozzle behavior.

This does not change AMP slicer behavior.

This is Stage 1 profile-only evidence until physical prints are performed and recorded.
