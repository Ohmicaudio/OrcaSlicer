# AMP Ohmic-Style 0.6 Nozzle Proxy Validation 001 Results

## Purpose

This pass creates and slices a realistic Ohmic-style speaker/LED ring proxy fixture scaled for a 0.6 mm nozzle.

The question is narrow:

```text
On a 0.6 nozzle proxy setup, what visible/detail sizes are safe, borderline, or unrealistic, and does width-only internal/bulk widening still make sense on a detail-bearing part?
```

This is a 0.6 mm nozzle proxy test. It is not U1 hardware validation, not A1 mini hardware validation, and not mixed-nozzle validation.

## Context

- Printer context: Bambu A1 mini proxy.
- Nozzle: 0.6 mm.
- Material context: PETG.
- Automated slicer used for this run: local CLI-hardened Snapmaker Orca build.
- Slicer profile proxy: Snapmaker U1 0.6 nozzle PETG profiles.
- G-code header version: `Snapmaker Orca 2.3.5`.

The local Snapmaker Orca CLI is used because it is available for repeatable automation in this workspace. These slices are therefore slicer-proxy evidence for a 0.6 nozzle detail/bulk fixture, not final A1 mini hardware-target validation.

## Fixture

Generated STL:

```text
outputs/amp_ohmic_fixture/models/ohmic_led_speaker_ring_fixture_0p6_proxy.stl
```

Generator:

```text
tools/amp_generate_ohmic_validation_fixture.py
```

Generation command:

```powershell
python tools/amp_generate_ohmic_validation_fixture.py `
  --nozzle-diameter 0.6 `
  --out outputs/amp_ohmic_fixture/models/ohmic_led_speaker_ring_fixture_0p6_proxy.stl
```

The generated STL is intentionally not committed.

The fixture includes:

- speaker/LED ring shape;
- visible cosmetic face;
- side-wall inset-style label panel;
- raised border around the side label panel;
- OHMIC-style geometric side text surrogate;
- face detail ladder;
- side-wall detail ladder;
- mounting holes;
- counterbore/boss-like raised pads;
- LED channel/rail grooves;
- pinstripe/groove detail;
- hidden backside/internal bulk.

True text mesh and real Ohmic logo geometry are still deferred. This fixture uses geometric bar/text surrogates to keep the generator deterministic and dependency-light.

## Feature-Size Ladder

The fixture intentionally includes features that should not all resolve on a 0.6 mm nozzle.

| Category | Approximate feature size | Expected role |
| --- | ---: | --- |
| Safe detail | 1.2-1.8 mm | Expected to be the realistic 0.6 nozzle detail range. |
| Borderline detail | 0.6-0.9 mm | Should be inspected carefully; may depend on slicer, material, cooling, and orientation. |
| Stress detail | 0.25-0.45 mm | Intended to show where the 0.6 nozzle setup stops being credible. |
| 0.2-style micro detail | Below normal 0.6 nozzle expectations | Stress-only indicator, not expected to resolve cleanly on a 0.6 nozzle. |

Failure to resolve the micro detail on a 0.6 mm nozzle is expected and should not be treated as a failed print.

## Slicer Setup

Executable:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer\msvc-release\src\Release\snapmaker-orca-console.exe
```

Machine profile:

```text
resources/profiles/Snapmaker/machine/Snapmaker U1 (0.6 nozzle).json
```

Stock process profile:

```text
resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json
```

Filament profile:

```text
resources/profiles/Snapmaker/filament/Generic PETG @U1 0.6 nozzle.json
```

Command ledger:

```text
outputs/amp_ohmic_fixture/reports/ohmic_0p6_proxy_cli_commands.json
```

Both stock and width-only proxy slices exited `0` and exported G-code.

## Variant Definitions

### Stock 0.6 Proxy

Header-reported widths:

```text
external perimeters extrusion width = 0.68mm
perimeters extrusion width = 0.68mm
infill extrusion width = 0.68mm
solid infill extrusion width = 0.68mm
top infill extrusion width = 0.60mm
```

### Width-Only 0.6 Proxy

Temporary ignored profile:

```text
outputs/amp_ohmic_fixture/profiles/amp_ohmic_fixture_0p6_width_only.process.json
```

Header-reported widths:

```text
external perimeters extrusion width = 0.62mm
perimeters extrusion width = 0.78mm
infill extrusion width = 0.86mm
solid infill extrusion width = 0.78mm
top infill extrusion width = 0.62mm
```

No layer-height changes were used. No combined mode was used. No mixed-nozzle behavior was used.

## Metrics

Metrics were generated with:

```powershell
python tools/amp_gcode_metrics.py `
  outputs/amp_ohmic_fixture/gcode `
  --csv outputs/amp_ohmic_fixture/reports/metrics.csv `
  --summary outputs/amp_ohmic_fixture/reports/summary.md
```

The metrics parser was updated in this pass to handle Snapmaker G-code using `M83` relative extrusion.

| Metric | Stock 0.6 proxy | Width-only 0.6 proxy | Delta |
| --- | ---: | ---: | ---: |
| M73 estimate | 164 min | 163 min | -0.6% |
| G-code file size | 1,755,870 bytes | 1,566,040 bytes | -10.8% |
| Layer count | 32 | 32 | +0.0% |
| Extrusion moves | 2,544 | 2,469 | -2.9% |
| Travel moves | 51,636 | 45,048 | -12.8% |
| Positive relative E total | 5,382.756 | 5,744.162 | +6.7% |

Warnings:

- Filament usage comments were not present in the parsed Snapmaker G-code.
- Positive relative E is a parser-derived extrusion total, not a weighed part mass.

## Visual Checks Needed

Preview and physical review should focus on:

- side-wall inset-style label panel;
- raised side-panel border;
- OHMIC-style side text surrogate;
- face detail ladder;
- side-wall detail ladder;
- LED channel rails;
- pinstripe/groove detail;
- boss/counterbore-like pads;
- mounting holes;
- hidden backside/internal bulk.

Expected visual outcomes:

- Safe detail should remain recognizable.
- Borderline detail should be inspected closely.
- Stress detail may partially disappear, merge, or become visually muddy.
- 0.2-style micro detail is included only as a stress indicator and is not expected to resolve cleanly on a 0.6 mm nozzle.

## Interpretation

The 0.6 proxy width-only slice gives a useful but caution-marked signal.

Positive signals:

- G-code file size decreased by 10.8%.
- Extrusion moves decreased by 2.9%.
- Travel moves decreased by 12.8%.
- Layer count stayed unchanged, confirming this is width-only and not a hidden layer-height test.

Caution signals:

- M73 estimate improved by only 0.6%.
- Positive relative E increased by 6.7%.
- The fixture intentionally contains details that are too small for reliable 0.6 mm output, so visual inspection must distinguish expected micro-detail loss from actual candidate failure.

This result supports continuing width-only as a proxy candidate for internal/bulk path reduction, but it does not support treating width-only as a universal improvement.

## Recommendation

Recommendation: continue, but caution-marked.

Use this fixture as the first physical 0.6 nozzle proxy print target:

```text
Stock 0.6 proxy
Width-only 0.6 proxy
```

Record:

- actual printer used;
- nozzle diameter;
- material;
- slicer/profile;
- actual print time;
- part weight if available;
- visible face quality;
- side text/panel quality;
- safe/borderline/stress ladder visibility;
- LED channel and pinstripe clarity;
- boss/hole quality;
- any PETG stringing, blobbing, or side-wall artifacts.

## Required Non-Claims

This is a 0.6 mm nozzle proxy test.

This does not validate U1 mixed-nozzle behavior.

This does not prove final part strength.

This does not prove final surface quality.

This does not prove 0.2 mm detail on a 0.6 mm nozzle.

This is used to understand visual/detail/bulk tradeoffs.
