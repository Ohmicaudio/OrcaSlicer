# AMP Multi-Tool Assignment Proxy 001 Results

## Purpose

This pass converts the offline AMP tool-class assignment into concrete slicer-facing proxy inputs.

The assignment solver currently maps the multi-tool fixture regions as:

```text
micro_detail_zone              -> 0.2
normal_visible_detail_zone     -> 0.4
structural_shell_zone          -> 0.6
bulk_zone                      -> 0.8
```

This proxy package generates separate STL bodies for those regions and slices each body with its intended U1 profile.

## Why This Is A Proxy

This is not mixed-nozzle slicing implementation.

Each region body is sliced as a separate single-tool job. That proves the assigned region body can be presented to the slicer with the matching U1 profile, but it does not produce one coordinated multi-tool G-code file.

This does not modify C++ slicer code, production profiles, G-code generation, Flow, LayerRegion, PerimeterGenerator, Arachne, UI, PrintObject, Snapmaker validation, or CalibUtils.

## Region Body List

Generated command:

```powershell
python tools/amp_generate_multitool_resolution_fixture.py --split-regions
```

Generated ignored region bodies:

| Region body | Intended tool class |
| --- | --- |
| `outputs/amp_multitool_resolution_fixture/region_bodies/micro_detail_zone.stl` | 0.2 |
| `outputs/amp_multitool_resolution_fixture/region_bodies/normal_visible_detail_zone.stl` | 0.4 |
| `outputs/amp_multitool_resolution_fixture/region_bodies/structural_shell_zone.stl` | 0.6 |
| `outputs/amp_multitool_resolution_fixture/region_bodies/bulk_zone.stl` | 0.8 |

Generated ignored sidecar:

```text
outputs/amp_multitool_resolution_fixture/region_bodies/region_assignments.json
```

## Tool-Class Assignment Table

| Region | Intended tool | Layer class | Width class | Fallback | Risk flags |
| --- | --- | --- | --- | --- | --- |
| `micro_detail_zone` | 0.2 | 0.06-0.10 | 0.22 | 0.4 | `preview_required`, `touchscreen_mixed_nozzle_blocked` |
| `normal_visible_detail_zone` | 0.4 | 0.12-0.20 | 0.42-0.45 | 0.2 | `avoid_large_visible_tool`, `touchscreen_mixed_nozzle_blocked` |
| `structural_shell_zone` | 0.6 | 0.24-0.36 | 0.62 | 0.4 | `touchscreen_mixed_nozzle_blocked` |
| `bulk_zone` | 0.8 | 0.32-0.56 | 0.82 | 0.6 | `touchscreen_mixed_nozzle_blocked` |

## Slice Result Table

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

Each case stores its exact argument vector in an ignored `command.json` file under the corresponding `_tmp` output directory.

| Region | Process profile | Filament profile | Exit | G-code exported | G-code size |
| --- | --- | --- | ---: | --- | ---: |
| `micro_detail_zone_0p2` | `0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | `Generic PLA @U1 0.2 nozzle.json` | 0 | Yes | 372,294 bytes |
| `normal_visible_detail_zone_0p4` | `0.20 Standard @Snapmaker U1 (0.4 nozzle).json` | `Snapmaker PLA Translucent @U1 0.4 nozzle.json` | 0 | Yes | 209,503 bytes |
| `structural_shell_zone_0p6` | `0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | `Generic PLA @U1 0.6 nozzle.json` | 0 | Yes | 255,782 bytes |
| `bulk_zone_0p8` | `0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | `Generic PLA @U1 0.8 nozzle.json` | 0 | Yes | 97,702 bytes |

Generated ignored G-code:

```text
outputs/amp_multitool_resolution_fixture/region_gcode/micro_detail_zone_0p2.gcode
outputs/amp_multitool_resolution_fixture/region_gcode/normal_visible_detail_zone_0p4.gcode
outputs/amp_multitool_resolution_fixture/region_gcode/structural_shell_zone_0p6.gcode
outputs/amp_multitool_resolution_fixture/region_gcode/bulk_zone_0p8.gcode
```

## Metrics Table

Metrics command:

```powershell
python tools/amp_gcode_metrics.py outputs/amp_multitool_resolution_fixture/region_gcode --csv outputs/amp_multitool_resolution_fixture/reports/region_metrics.csv --summary outputs/amp_multitool_resolution_fixture/reports/region_summary.md
```

| Region G-code | Layers | Extrusion moves | Travel moves | Positive E | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `micro_detail_zone_0p2.gcode` | 28 | 1 | 9,944 | 15.000 | Export succeeded, but preview inspection is required before using this as a quality signal. |
| `normal_visible_detail_zone_0p4.gcode` | 16 | 209 | 4,812 | 294.637 | Export succeeded. |
| `structural_shell_zone_0p6.gcode` | 16 | 542 | 6,280 | 1,046.271 | Export succeeded. |
| `bulk_zone_0p8.gcode` | 17 | 649 | 1,160 | 2,115.332 | Export succeeded. |

The metrics are slicer/G-code-derived only. They do not prove print time, print quality, strength, bonding, or dimensional accuracy.

## What This Proves

- AMP now has an offline solver that assigns fixture regions to 0.2 / 0.4 / 0.6 / 0.8 tool classes.
- The generator can emit separate slicer-facing bodies for those assigned regions.
- Each assigned region body can be sliced with its intended U1 profile in the local stacked CLI validation build.
- This proves slicer/profile feasibility for separated region bodies.
- The assignment can now be represented as concrete region bodies, sidecar metadata, G-code outputs, and metrics.

## What This Does Not Prove

This does not implement a single-object mixed-nozzle toolpath.

This does not implement mixed-nozzle slicing.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

This does not prove print strength, surface quality, bonding, dimensional accuracy, or toolchange reliability.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only mixed-nozzle experimentation remains future and hardware-dependent.

## Next Required Step

The next safe step is preview review of the separated region G-code, especially the 0.2 micro/detail body.

Only after preview review should the project move to either:

- a better 0.2 region-body fixture if the current micro body slices poorly; or
- a physical proxy print of the separated bodies on available hardware; or
- an offline compositor/design document for how separated region bodies could eventually become one coordinated mixed-tool plan.
