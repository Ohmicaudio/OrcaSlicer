# AMP Run 001 Findings

## Executive Summary

Run 001 compares profile-only slicing behavior between the stock Snapmaker U1 0.4 mm profile and the experimental effective-width/Arachne profile across six generated synthetic models.

The experimental profile reduced G-code file size and travel-move count on all six models in this run. Parsed positive E decreased on five models and increased on `embossed_text_plate`. That makes the profile worth further visual review, but it does not prove real print-time, strength, surface-quality, dimensional-accuracy, or bonding improvements.

G-code/preview cannot prove print strength. G-code/preview cannot prove surface quality. Run 001 does not validate physical mixed-nozzle behavior. Estimated time, extrusion, and travel values are slicer/G-code-derived unless confirmed on hardware.

## Model List

| Model | Category | Stock-only | Experimental-only | Same-plate visual comparison |
| --- | --- | --- | --- | --- |
| `thin_wall_comb` | Thin-wall detail | generated | generated | generated |
| `large_bracket_box` | Large bracket / box | generated | generated | generated |
| `embossed_text_plate` | Embossed/debossed text surrogate | generated | generated | generated |
| `speaker_adapter_ring` | Speaker adapter ring | generated | generated | generated |
| `led_ring_face` | LED speaker ring face | generated | generated | generated |
| `sloped_surface_torture` | Sloped surface torture | generated | generated | generated |

## Stock vs Experimental Comparison

These metrics are from separate stock-only and experimental-only G-code files. Same-plate comparison files are visual inspection artifacts and are not used for the table below.

| Model | File size delta | Travel move delta | Extrusion move delta | Parsed positive E delta | Initial finding |
| --- | ---: | ---: | ---: | ---: | --- |
| `thin_wall_comb` | -8.7% | -10.4% | -17.7% | -2.1% | Promising, but thin wall survival needs visual review. |
| `large_bracket_box` | -22.7% | -25.9% | -7.9% | -3.1% | Strong candidate for internal/bulk width experiments. |
| `embossed_text_plate` | -15.1% | -20.4% | +5.7% | +2.5% | Needs visual review because extrusion increased despite smaller file/travel counts. |
| `speaker_adapter_ring` | -17.4% | -17.8% | -21.0% | -27.9% | Strong candidate for ring/adapter workflow review. |
| `led_ring_face` | -5.9% | -4.5% | -7.2% | -23.0% | Needs top/cosmetic surface review before treating as favorable. |
| `sloped_surface_torture` | -27.0% | -33.1% | -1.1% | -7.0% | Largest travel/file-size reduction; likely high priority for visual review. |

## Biggest Reductions

Largest file-size reductions:

| Rank | Model | File size delta |
| ---: | --- | ---: |
| 1 | `sloped_surface_torture` | -27.0% |
| 2 | `large_bracket_box` | -22.7% |
| 3 | `speaker_adapter_ring` | -17.4% |

Largest travel-move reductions:

| Rank | Model | Travel move delta |
| ---: | --- | ---: |
| 1 | `sloped_surface_torture` | -33.1% |
| 2 | `large_bracket_box` | -25.9% |
| 3 | `embossed_text_plate` | -20.4% |

Largest parsed positive E reductions:

| Rank | Model | Parsed positive E delta |
| ---: | --- | ---: |
| 1 | `speaker_adapter_ring` | -27.9% |
| 2 | `led_ring_face` | -23.0% |
| 3 | `sloped_surface_torture` | -7.0% |

## Increases Or Regressions

`embossed_text_plate` is the main caution item in the numeric pass:

- File size decreased by 15.1%.
- Travel moves decreased by 20.4%.
- Extrusion moves increased by 5.7%.
- Parsed positive E increased by 2.5%.

This may be an acceptable profile-only result if the experimental profile preserves embossed/debossed detail and top surfaces. It may also indicate local overfill, extra wall compensation, or a region where the width settings are too aggressive. It needs layer-by-layer review before drawing conclusions.

No stock-only or experimental-only slicing failures were recorded for the six generated models.

## Models Needing Visual Layer Review

Priority 1:

- `thin_wall_comb`: verify thin features do not disappear or become overfilled.
- `embossed_text_plate`: inspect text strokes, top surfaces, and any apparent overfill because parsed positive E increased.
- `sloped_surface_torture`: inspect sloped surfaces for coarse path spacing or visible loss of surface fidelity.

Priority 2:

- `led_ring_face`: inspect cosmetic face and small LED/detail features.
- `speaker_adapter_ring`: inspect ring walls and mounting features because parsed positive E reduction is large.
- `large_bracket_box`: inspect large internal/bulk regions and external walls to confirm reductions are internal rather than cosmetic degradation.

## What The Experimental Profile Appears To Affect

The experimental profile appears to affect:

- G-code file size.
- Travel-move count.
- Extrusion-move count.
- Parsed positive E total.
- Likely path count and spacing in regions governed by role-specific line widths and Arachne.

The current metrics do not identify exact wall role, top-surface role, or infill role per move. Those distinctions require slicer preview inspection, richer G-code role parsing, or future debug artifacts.

## What Cannot Be Concluded

Run 001 cannot claim:

- real print-time improvement;
- print strength improvement;
- surface quality improvement;
- dimensional accuracy improvement;
- bonding improvement;
- filament reduction;
- U1 toolhead reliability;
- purge, wipe, or toolchange behavior;
- physical mixed-nozzle behavior.

The metrics parser also did not extract Snapmaker estimated print-time or filament-usage comments from these G-code files. File size, movement counts, and parsed positive E are G-code inspection metrics only.

## Recommended Next Benchmark Settings

Keep the current experimental effective-width profile for the first visual pass so the same-plate outputs can be reviewed consistently.

For follow-up profile sweeps, consider:

- Conservative internal width pass: keep `outer_wall_line_width` and `top_surface_line_width` near stock while reducing `sparse_infill_line_width` from `0.58` to a smaller intermediate value.
- Text/detail protection pass: reduce internal widening or add a separate embossed/debossed text benchmark setting if `embossed_text_plate` shows overfill or loss of detail.
- Ring/adapter pass: inspect whether the large parsed positive E reductions on `speaker_adapter_ring` and `led_ring_face` are path-count reductions, missing paths, or legitimate wider-region behavior.
- Visual-only same-plate review before adding downloaded community models.
- Physical/proxy bead-width coupons on available FDM hardware before claiming any real-world process benefit.

## Next Evidence Steps

1. Complete the Run 001 visual review checklist in Snapmaker Orca preview.
2. Use Prusa G-code Viewer as a secondary visual check where useful.
3. Record screenshots locally, but do not commit screenshots unless explicitly approved.
4. Start proxy bead-width characterization on available FDM hardware.
5. Use Run 001 plus proxy print evidence to decide Run 002 model categories.
