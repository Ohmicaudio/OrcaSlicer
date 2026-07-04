# AMP 0.2 Micro-Region Proxy Diagnostic

## Purpose

This diagnostic investigates why the first AMP multi-tool assignment proxy reported:

```text
micro_detail_zone_0p2:
28 layers
1 extrusion move
9,944 travel moves
```

That result did not look like healthy 0.2 micro-detail G-code. The goal was to determine whether the cause was a parser issue, geometry issue, profile issue, fixture design issue, slicer behavior issue, or unresolved.

This does not implement mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This only verifies printable/sliceable proxy geometry for the 0.2 tool class.

## Inputs

Micro-region STL:

```text
outputs/amp_multitool_resolution_fixture/region_bodies/micro_detail_zone.stl
```

0.2 G-code:

```text
outputs/amp_multitool_resolution_fixture/region_gcode/micro_detail_zone_0p2.gcode
```

Slicer executable:

```text
B:\ohmic\builds\Snapmaker-OrcaSlicer-cli-0p2-fix\msvc-release\src\Release\snapmaker-orca-console.exe
```

Stacked CLI validation context:

```text
validation/cli-profile-resolution-stacked-on-normalize-guard
d5a1055f6 fix: resolve inherited process profiles in CLI
5ace7ea28 fix: guard CLI FDM normalization without nozzle diameter
```

## STL Analysis

The generated micro-region STL has:

| Property | Value |
| --- | ---: |
| Triangles | 228 |
| Vertices | 684 |
| Bounding box min | `(-18.0, -12.0, 0.0)` |
| Bounding box max | `(18.0, 12.0, 1.75)` |
| Size | `(36.0, 24.0, 1.75)` |
| Crude connected components | 19 |

The crude component check found 19 small box-like components. That means the body is intentionally fragmented into stress/detail marks rather than being one watertight continuous product body.

That fragmentation is worth improving in a future Rev B micro fixture, but it did not explain the original `1 extrusion move` metric by itself because the G-code contains real printable extrusion moves.

## G-code Analysis

The 0.2 G-code uses relative extrusion after `M83`.

The G-code contains role/type comments such as:

```text
;TYPE:Inner wall
;TYPE:Outer wall
;TYPE:Bottom surface
;TYPE:Internal solid infill
;TYPE:Sparse infill
;TYPE:Top surface
```

The print body includes extrusion lines such as:

```text
G1 X118.461 Y147.039 E.3238
```

The original metrics parser only recognized extrusion values with a leading digit, such as:

```text
E0.3238
```

It did not recognize Snapmaker Orca's compact decimal form:

```text
E.3238
```

Therefore the original `1 extrusion move` count was a parser bug. The single counted move was the initial purge line:

```text
G1 X185 E15 F360
```

## Parser Fix

Updated:

```text
tools/amp_gcode_metrics.py
```

The E-value regex now accepts both:

```text
E0.3238
E.3238
```

Tiny parser check:

| Input | Parsed value |
| --- | ---: |
| `G1 X118.461 Y147.039 E.3238` | 0.3238 |
| `G1 X118.461 Y147.039 E0.3238` | 0.3238 |

## Corrected 0.2 Micro Metrics

After fixing the parser:

| File | Layers | Extrusion moves | Travel moves | Positive E | M73 estimate |
| --- | ---: | ---: | ---: | ---: | --- |
| `micro_detail_zone_0p2.gcode` | 28 | 8,790 | 924 | 540.789 | 20 min |

The 0.2 micro output is no longer a `1 extrusion move` anomaly.

## 0.2 vs 0.4 Comparison

The same `micro_detail_zone.stl` was sliced with the U1 0.4 profile as a diagnostic comparison.

| Profile | Exit | G-code exported | Layers | Extrusion moves | Travel moves | Positive E | M73 estimate |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| U1 0.2 / `0.06 Standard` | 0 | Yes | 28 | 8,790 | 924 | 540.789 | 20 min |
| U1 0.4 / `0.20 Standard` | 0 | Yes | 8 | 1,323 | 176 | 472.317 | not used as final metric |

The 0.4 comparison confirms the geometry is sliceable under a coarser tool class. It also shows the expected resolution-cost difference: the 0.2 path uses many more layers and extrusion moves.

## Simple 0.2 Sanity Probes

Generated ignored probes:

```text
outputs/amp_multitool_resolution_fixture/diagnostic_probes/
```

Probe results with U1 0.2 / `0.06 Standard`:

| Probe | Exit | G-code exported | Layers | Extrusion moves | Travel moves | Positive E | Notes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `0p2_simple_cube.stl` | 0 | Yes | 166 | 8,042 | 1,167 | 354.553 | Baseline sanity pass. |
| `0p2_single_bar_0p25.stl` | -100 | No | n/a | n/a | n/a | n/a | Failed with `Unable to create exclude triangles`; too narrow/fragile for this CLI path. |
| `0p2_single_bar_0p35.stl` | 0 | Yes | 19 | 96 | 20 | 26.678 | Pass. |
| `0p2_single_bar_0p50.stl` | 0 | Yes | 19 | 114 | 38 | 27.350 | Pass. |
| `0p2_parallel_ladder.stl` | 0 | Yes | 19 | 657 | 206 | 103.546 | Pass. |
| `0p2_dot_array.stl` | 0 | Yes | 16 | 961 | 193 | 92.536 | Pass. |

The sanity probes show that the U1 0.2 profile can slice simple 0.2-class proxy geometry in the stacked CLI build. The 0.25 mm bar failure suggests that very small standalone slivers remain a geometry/slicer boundary risk and should be marked stress-only.

## Diagnosis

Root cause:

```text
parser issue
```

The alarming `1 extrusion move / 9,944 travel moves` result was caused by `tools/amp_gcode_metrics.py` failing to parse compact decimal extrusion values like `E.3238`.

Secondary finding:

```text
fixture design caution
```

The micro-region STL is fragmented into many small stress-detail components. This is acceptable for a diagnostic stress body, but a future Rev B should include fewer disconnected fragments and clearer labels distinguishing printable detail from stress-only detail.

The current evidence does not show a profile-resolution failure or a C++ slicer behavior failure.

## Fixture Revision Decision

The fixture was not revised in this commit.

Reason:

```text
The primary anomaly was the metrics parser, not the micro STL or U1 0.2 profile.
```

Recommended future Rev B improvements:

- reduce disconnected fragments;
- keep at least one connected, clearly printable 0.2-class detail feature;
- keep sub-0.30 mm marks stress-only;
- explicitly label printable vs stress-only detail in the sidecar.

## Final Recommendation

Continue using the 0.2 micro body as a slicer/profile feasibility proxy, but keep `preview_required` on the assignment.

Treat 0.35 mm and larger simple marks as plausible 0.2 proxy geometry for this CLI path.

Treat 0.25 mm standalone bars as stress-only until a better geometry construction and preview/physical validation path exists.

Do not use this diagnostic to claim print quality, strength, dimensional accuracy, bonding, or physical mixed-nozzle behavior.
