# AMP 0.6 and 0.8 Tool Break-Even Study 001

## Purpose

This study tests when U1 0.6 and 0.8 tool classes begin to make sense compared with the safe 0.4 baseline.

The question is:

```text
when does the tool switch earn its keep?
```

This is offline/advisory benchmarking only. It does not implement mixed-nozzle slicing and does not generate a single combined mixed-nozzle G-code file.

## Why This Study Exists

The previous assigned-tool vs 0.4 baseline comparison showed:

```text
0.2 = quality/detail-driven, not time-driven
0.4 = safe baseline
0.6 = possible structural-shell tool, threshold unknown
0.8 = possible bulk tool, threshold unknown
```

The break-even sweep replaces the unknown 0.6/0.8 thresholds with slice data from progressively larger generated region bodies.

## Generated Model Families

Generator:

```text
tools/amp_generate_tool_break_even_sweep.py
```

Command:

```powershell
python tools/amp_generate_tool_break_even_sweep.py `
  --out-dir outputs/amp_tool_break_even_sweep/models `
  --metadata-out outputs/amp_tool_break_even_sweep/models/metadata.json
```

Generated ignored outputs:

```text
outputs/amp_tool_break_even_sweep/models/
```

The sweep has two families:

| Family | Candidate tool | Baseline | Geometry intent |
| --- | --- | --- | --- |
| `structural_shell_sweep` | 0.6 | 0.4 | Shell/bracket/ring-like sections with ribs, bosses, and hole/counterbore surrogates. |
| `bulk_sweep` | 0.8 | 0.4 | Hidden/internal bulk mass with ribs and large simple pads. |

## Slicing Setup

CLI build:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\snapmaker-orca-console.exe
```

Baseline 0.4:

```text
Snapmaker U1 (0.4 nozzle).json
0.20 Standard @Snapmaker U1 (0.4 nozzle).json
Snapmaker PLA Translucent @U1 0.4 nozzle.json
```

Structural 0.6 candidate:

```text
Snapmaker U1 (0.6 nozzle).json
0.24 Standard @Snapmaker U1 (0.6 nozzle).json
Generic PLA @U1 0.6 nozzle.json
```

Bulk 0.8 candidate:

```text
Snapmaker U1 (0.8 nozzle).json
0.40 Standard @Snapmaker U1 (0.8 nozzle).json
Generic PLA @U1 0.8 nozzle.json
```

All 16 slice jobs exited `0` and exported G-code.

Generated ignored outputs:

```text
outputs/amp_tool_break_even_sweep/gcode/
outputs/amp_tool_break_even_sweep/reports/metrics.csv
outputs/amp_tool_break_even_sweep/reports/summary.md
outputs/amp_tool_break_even_sweep/reports/cost_sensitivity.csv
outputs/amp_tool_break_even_sweep/reports/cost_sensitivity.md
```

## Structural Shell 0.6 vs 0.4 Sweep

| Model | Approx area | Approx volume | Approx path | 0.4 time | 0.6 time | File size delta | Extrusion moves delta | Travel moves delta | Positive E delta | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `structural_shell_small` | 2,808.0 mm^2 | 4,598.4 mm^3 | 3,300.0 mm | 19 min | 40 min | -19.6% | -23.1% | -20.3% | +42.6% | `fallback_0p4` |
| `structural_shell_medium` | 6,424.0 mm^2 | 11,804.0 mm^3 | 6,933.3 mm | 38 min | 90 min | -28.9% | -29.7% | -24.2% | +35.5% | `candidate_needs_visual_review` |
| `structural_shell_large` | 12,568.0 mm^2 | 25,171.2 mm^3 | 12,500.0 mm | 66 min | 177 min | -26.3% | -25.1% | -27.6% | +30.5% | `candidate_needs_visual_review` |
| `structural_shell_xlarge` | 21,272.0 mm^2 | 46,072.8 mm^3 | 20,000.0 mm | 101 min | 301 min | -25.6% | -24.7% | -25.8% | +27.2% | `candidate_needs_visual_review` |

The 0.6 structural-shell candidate consistently reduces file size and move counts, but the slicer-derived M73 estimate and positive E increase. This makes 0.6 a visual/structural-review candidate, not a time-saving default, for this sweep.

## Bulk 0.8 vs 0.4 Sweep

| Model | Approx area | Approx volume | Approx path | 0.4 time | 0.8 time | File size delta | Extrusion moves delta | Travel moves delta | Positive E delta | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `bulk_small` | 2,864.0 mm^2 | 7,488.0 mm^3 | 2,480.0 mm | 22 min | 61 min | -65.3% | -70.6% | -76.7% | +55.9% | `fallback_0p4` |
| `bulk_medium` | 8,352.0 mm^2 | 34,272.0 mm^3 | 6,600.0 mm | 49 min | 175 min | -64.9% | -67.3% | -79.2% | +43.0% | `fallback_0p4` |
| `bulk_large` | 17,840.0 mm^2 | 100,224.0 mm^3 | 13,280.0 mm | 96 min | 402 min | -65.2% | -67.3% | -77.3% | +38.1% | `fallback_0p4` |
| `bulk_xlarge` | 30,848.0 mm^2 | 218,880.0 mm^3 | 22,400.0 mm | 169 min | 764 min | -65.8% | -67.1% | -79.8% | +35.6% | `fallback_0p4` |

The 0.8 bulk candidate strongly reduces file size and move counts, but it does not produce a slicer-estimated time win in this sweep. Positive E also increases substantially. For these generated bulk bodies, 0.8 should not be selected automatically.

## Toolchange Cost Sensitivity

Positive values mean the candidate remains faster after the toolchange penalty. Negative values mean the candidate is slower than the 0.4 baseline after the penalty.

| Model | Candidate | Pre-toolchange savings | Net @0s | Net @5s | Net @15s | Net @30s | Net @60s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `structural_shell_small` | 0.6 | -1,260 s | -1,260 s | -1,265 s | -1,275 s | -1,290 s | -1,320 s |
| `structural_shell_medium` | 0.6 | -3,120 s | -3,120 s | -3,125 s | -3,135 s | -3,150 s | -3,180 s |
| `structural_shell_large` | 0.6 | -6,660 s | -6,660 s | -6,665 s | -6,675 s | -6,690 s | -6,720 s |
| `structural_shell_xlarge` | 0.6 | -12,000 s | -12,000 s | -12,005 s | -12,015 s | -12,030 s | -12,060 s |
| `bulk_small` | 0.8 | -2,340 s | -2,340 s | -2,345 s | -2,355 s | -2,370 s | -2,400 s |
| `bulk_medium` | 0.8 | -7,560 s | -7,560 s | -7,565 s | -7,575 s | -7,590 s | -7,620 s |
| `bulk_large` | 0.8 | -18,360 s | -18,360 s | -18,365 s | -18,375 s | -18,390 s | -18,420 s |
| `bulk_xlarge` | 0.8 | -35,700 s | -35,700 s | -35,705 s | -35,715 s | -35,730 s | -35,760 s |

Because the candidates are already time-negative before toolchange cost, all tested toolchange costs keep them time-negative.

## Break-Even Observations

This sweep did not find a M73-time break-even point for either 0.6 structural-shell or 0.8 bulk candidates.

The useful signal is different:

```text
0.6 / 0.8 reduce file size and motion count
0.6 / 0.8 increase slicer-derived M73 time here
0.6 / 0.8 increase positive E here
```

Therefore, the first threshold recommendation is not a larger automatic threshold. It is a stronger caution gate: wider tools need evidence from geometry-specific preview and physical validation before they are considered wins.

## Updated Candidate Thresholds

No solver threshold was changed from this study.

The data does not justify making 0.6 or 0.8 easier to select. It suggests the opposite:

- 0.6 should only be selected for structural shell regions above a minimum area/path/volume threshold when preview or physical intent supports the heavier extrusion behavior.
- 0.8 should only be selected for bulk regions above a larger threshold and should require evidence that material/time cost is acceptable.
- 0.4 remains the safe fallback when a region is too small or when the candidate increases time/material burden.
- M73 time estimates may not fully capture benefit, so visual and physical validation remain required.
- Positive E increases may be acceptable only if intentional structural/bulk output, not visible overfill.

## Solver Threshold Recommendations

Current solver thresholds remain unchanged.

Recommended next solver behavior, after more evidence:

```text
0.6 structural shell:
  keep as candidate_needs_visual_review unless M73/material/preview improves

0.8 bulk:
  keep strongly cost-gated
  fall back to 0.4 or 0.6 unless bulk-region evidence clears the gate

0.4:
  remain default fallback
```

Do not overfit the solver to this one generated sweep. The next data should come from real part regions and physical proxy prints.

## What This Proves

- The break-even tooling can generate structural-shell and bulk sweep models.
- The local CLI-hardened Snapmaker Orca build can slice the full 0.4/0.6/0.8 sweep.
- The metrics pipeline can compare candidate tools against 0.4 baselines.
- For this sweep, 0.6 and 0.8 reduce file size and move counts but do not win on M73 time.
- For this sweep, 0.8 should remain a cautious bulk-only candidate, not an automatic planner output.

## What This Does Not Prove

This does not implement mixed-nozzle slicing.

This does not generate a single mixed-nozzle G-code file.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or toolchange reliability.

## Next Step

Use this study to keep the solver conservative, then run one real-part region split where the 0.6/0.8 candidates are expected to have meaningful manufacturing value:

```text
real hidden bulk / structural region
-> 0.4 baseline
-> 0.6 or 0.8 candidate
-> preview review
-> physical proxy print
```

Only after that should planner thresholds move.
