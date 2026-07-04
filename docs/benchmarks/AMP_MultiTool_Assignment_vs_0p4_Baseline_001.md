# AMP Multi-Tool Assignment vs 0.4 Baseline 001

## Purpose

This report compares the offline AMP multi-tool assignment against a single-nozzle 0.4 mm baseline for the isolated multi-tool resolution fixture regions.

The comparison asks:

```text
assigned tool-class slicing
vs.
normal 0.4 mm baseline slicing
```

This is offline/advisory benchmarking only. It does not implement mixed-nozzle slicing, does not generate a single combined mixed-nozzle print job, and does not modify slicer behavior.

## Tool Ladder

| Tool class | Planner role | Layer-height class | Line-width class |
| --- | --- | --- | --- |
| 0.2 | Fine/micro visible detail | 0.06-0.10 | 0.22 |
| 0.4 | Safe/general visible detail fallback | 0.12-0.20 | 0.42-0.45 |
| 0.6 | Structural shell / medium bulk | 0.24-0.36 | 0.62 |
| 0.8 | Hidden/internal bulk | 0.32-0.56 | 0.82 |

## Region List

| Region | Assigned tool | Baseline tool | Assignment intent |
| --- | --- | --- | --- |
| `micro_detail_zone` | 0.2 | 0.4 | Quality/detail-driven micro feature planning. |
| `normal_visible_detail_zone` | 0.4 | 0.4 | Control case; visible detail remains on the baseline tool. |
| `structural_shell_zone` | 0.6 | 0.4 | Structural shell candidate. |
| `bulk_zone` | 0.8 | 0.4 | Hidden/internal bulk candidate. |

## Slice Inputs

Region bodies:

```text
outputs/amp_multitool_resolution_fixture/region_bodies/
```

Assigned-tool G-code:

```text
outputs/amp_multitool_resolution_fixture/region_gcode/
```

0.4 baseline G-code generated for this comparison:

```text
outputs/amp_multitool_resolution_fixture/baseline_0p4_gcode/
```

Baseline profile:

```text
resources/profiles/Snapmaker/machine/Snapmaker U1 (0.4 nozzle).json
resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json
resources/profiles/Snapmaker/filament/Snapmaker PLA Translucent @U1 0.4 nozzle.json
```

CLI build used:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\snapmaker-orca-console.exe
```

All four 0.4 baseline slices exited `0` and exported G-code.

## Assigned Tool vs 0.4 Baseline Metrics

| Region | Assigned | 0.4 baseline time | Assigned time | File size delta | Extrusion move delta | Travel move delta | Positive E delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `micro_detail_zone` | 0.2 | 3 min | 20 min | +321.3% | +552.6% | +402.2% | +14.5% |
| `normal_visible_detail_zone` | 0.4 | 9 min | 9 min | +1.0% | +0.8% | +1.7% | +0.1% |
| `structural_shell_zone` | 0.6 | 11 min | 32 min | -39.4% | -42.0% | -44.3% | +20.3% |
| `bulk_zone` | 0.8 | 14 min | 46 min | -64.8% | -70.6% | -89.0% | +43.4% |

Estimated time is taken from slicer/G-code `M73 R` values.

Generated metrics:

```text
outputs/amp_multitool_resolution_fixture/reports/assigned_metrics.csv
outputs/amp_multitool_resolution_fixture/reports/baseline_0p4_metrics.csv
outputs/amp_multitool_resolution_fixture/reports/assignment_vs_baseline_metrics.csv
outputs/amp_multitool_resolution_fixture/reports/assignment_vs_baseline_summary.md
```

## Toolchange Cost Sensitivity

Positive values mean the assigned tool remains faster after the toolchange penalty. Negative values mean the assigned tool is slower than the 0.4 baseline after the penalty.

| Region | Assigned | Pre-toolchange savings | Net @0s | Net @5s | Net @15s | Net @30s | Net @60s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `micro_detail_zone` | 0.2 | -1020 s | -1020 s | -1025 s | -1035 s | -1050 s | -1080 s |
| `normal_visible_detail_zone` | 0.4 | 0 s | 0 s | -5 s | -15 s | -30 s | -60 s |
| `structural_shell_zone` | 0.6 | -1260 s | -1260 s | -1265 s | -1275 s | -1290 s | -1320 s |
| `bulk_zone` | 0.8 | -1920 s | -1920 s | -1925 s | -1935 s | -1950 s | -1980 s |

This result is intentionally cautionary: on these isolated region bodies, the wider assigned tools reduce file size and move counts for structural/bulk regions, but the slicer-derived time estimate and positive extrusion increase. That means the assigned 0.6 and 0.8 regions are not automatically cost wins.

## Region-by-Region Interpretation

### `micro_detail_zone`

The 0.2 assignment is detail/resolution driven, not time-saving. It is much slower than the 0.4 baseline by slicer estimate, with more layers, moves, and file size.

Decision: `quality_driven_keep`

Reason: keep 0.2 only when the region is visibly detail-critical and the detail value justifies cost. This requires visual and physical validation.

Required validation:

```text
preview review
physical fine-detail print
material/clog risk check
U1 hardware validation before any physical mixed-nozzle claim
```

### `normal_visible_detail_zone`

The assigned tool is 0.4, matching the baseline. Metrics remain effectively stable, which is the expected control behavior.

Decision: `keep_assigned_tool`

Reason: 0.4 remains the safe visible-detail baseline and fallback.

Required validation:

```text
preview parity
visible surface check if printed
```

### `structural_shell_zone`

The 0.6 assignment reduces file size, extrusion moves, and travel moves, but the slicer-derived time estimate and positive E increase relative to the 0.4 baseline.

Decision: `needs_visual_review`

Reason: this may still be useful for structural or wall-behavior reasons, but it is not justified as a time-saving assignment on this fixture region.

Required validation:

```text
preview review for wall/path simplification
physical shell print comparison
material use comparison
structural or fitment check before treating as useful
```

### `bulk_zone`

The 0.8 assignment strongly reduces file size and move counts, but the slicer-derived time estimate and positive E increase substantially relative to the 0.4 baseline.

Decision: `fallback_0p4`

Reason: hidden/internal bulk should be cost-gated. For this isolated region body, 0.8 does not clear the time/material burden implied by the baseline comparison. It may still become useful on larger, thicker, or more appropriate bulk geometries, but this fixture body does not prove that.

Required validation:

```text
larger bulk-region test
preview review
physical print comparison
material/time measurement
toolchange-cost sensitivity review
```

## Decision Table

| Region | Assigned tool | 0.4 baseline result | Assigned result | Net benefit before toolchange | Toolchange sensitivity | Decision | Reason | Required validation |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `micro_detail_zone` | 0.2 | Fast but lower-resolution baseline. | Slower, much denser fine-detail output. | -1020 s | Cost-negative at every tested toolchange cost. | `quality_driven_keep` | Detail-driven assignment can be valid even when slower. | Preview and physical fine-detail validation. |
| `normal_visible_detail_zone` | 0.4 | Baseline/control. | Essentially unchanged. | 0 s | No toolchange should be needed if already on 0.4. | `keep_assigned_tool` | 0.4 remains the visible-detail default. | Preview parity. |
| `structural_shell_zone` | 0.6 | Faster slicer estimate, more moves. | Fewer moves, larger positive E, slower estimate. | -1260 s | Cost-negative at every tested toolchange cost. | `needs_visual_review` | Potential path simplification is not enough by itself. | Preview, material, and physical shell checks. |
| `bulk_zone` | 0.8 | Faster slicer estimate, more moves. | Much fewer moves, much larger positive E, slower estimate. | -1920 s | Cost-negative at every tested toolchange cost. | `fallback_0p4` | 0.8 bulk assignment must be cost-gated and this body does not clear the gate. | Larger bulk test plus physical validation. |

## Conclusions

- The offline planner can now compare assigned tool classes against a single-nozzle 0.4 baseline.
- 0.2 assignments are quality/detail driven, not necessarily time-saving.
- 0.8 assignments must be cost-gated by region size, toolchange cost, slicer-estimated time, and material behavior.
- 0.4 remains the safe fallback.
- The plan remains advisory/offline only.

## Required Non-Claims

This does not implement mixed-nozzle slicing.

This does not generate a single combined mixed-nozzle print job.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or toolchange reliability.

## Next Step

The next useful offline step is to feed this comparison back into the advisory planner as a rejection/caution signal:

```text
region metadata
-> assigned tool class
-> 0.4 baseline comparison
-> cost sensitivity
-> keep / fallback / visual-review decision
```

That should happen before any production slicer path consumes AMP data.
