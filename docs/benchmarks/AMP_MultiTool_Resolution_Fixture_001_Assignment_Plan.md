# AMP Multi-Tool Resolution Fixture 001 Assignment Plan

## Purpose

This plan defines the intended tool-class assignment for the first AMP multi-tool resolution fixture. It moves the benchmark framing from width-only profile tweaks toward the long-view AMP target:

```text
region -> target nozzle -> target layer-height class -> target line-width class -> fallback
```

## Fixture Outputs

Generated STL:

```text
outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture.stl
```

Generated region sidecar:

```text
outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture_regions.json
```

Generator:

```text
tools/amp_generate_multitool_resolution_fixture.py
```

The generated STL and JSON sidecar are intentionally not committed.

## Fixture Description

The fixture is a four-zone product-surrogate plate with:

- visible exterior face;
- micro text/groove/dot stress features;
- normal visible text/detail surrogate;
- sloped/chamfered cosmetic panel;
- holes and counterbore/boss-like shell features;
- hidden backside/internal mass;
- a large bulk zone.

The zones are spatially separated so they can be inspected manually and so future offline assignment tooling can read the region sidecar without needing slicer integration.

## Assignment Table

| Region | Visibility | Detail criticality | Wall/bulk character | Target nozzle | Target layer height | Target line width | Fallback | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `micro_detail_zone` | Visible | Very high | Thin raised bars, grooves, dots | 0.2 mm | 0.06-0.10 mm | 0.22 mm | 0.4 mm only if micro detail is non-critical | Fine text/groove/dot features should spend resolution where visible detail matters. |
| `normal_visible_detail_zone` | Visible | High | Cosmetic face, readable text surrogate, sloped panel | 0.4 mm | 0.12-0.20 mm | 0.42-0.45 mm | 0.2 mm if text/slope quality fails; stock 0.4 if uncertainty is high | General visible detail does not need 0.2 everywhere, but should avoid 0.6/0.8 coarse settings. |
| `structural_shell_zone` | Partly visible / functional | Medium | Thick shell, holes, bosses | 0.6 mm | 0.24-0.36 mm | 0.62 mm | 0.4 mm for tight holes or visible/mating surfaces | This region is a candidate for structural shell resolution if visible/mating details remain protected. |
| `bulk_zone` | Hidden/internal | Low | Large internal mass / large infill-like region | 0.8 mm | 0.32-0.56 mm | 0.82 mm | 0.6 mm if geometry is too narrow; 0.4 mm if close to visible/mating detail | Hidden mass is the intended coarse-resolution target. |

## Fallback Rules

Fallback to a smaller/finer tool if:

- the region touches visible text, logo, grooves, or decorative surfaces;
- holes, bosses, mating faces, or tolerance-sensitive features are nearby;
- the region is thinner than the target tool's practical bead/layer envelope;
- the predicted material increase outweighs path/travel savings;
- confidence is low or region classification is ambiguous.

Fallback to stock/single-nozzle behavior if:

- the printer path cannot validate mixed physical nozzles safely;
- the job is intended for U1 touchscreen start and requires unsupported mixed-nozzle metadata;
- the planner cannot produce deterministic region assignment;
- the tool-change/purge cost would dominate savings;
- physical validation has not been performed.

## Planning Boundary

This is an assignment plan, not slicer behavior. It does not create mixed-nozzle G-code and does not alter Snapmaker validation paths.

The first implementation should remain offline:

```text
region metadata + tool matrix -> recommended tool/layer/width class
```

No Flow, Arachne, LayerRegion, PerimeterGenerator, PrintObject, UI, G-code, profile defaults, or Snapmaker validation behavior is changed by this plan.
