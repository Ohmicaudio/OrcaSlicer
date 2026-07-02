# AMP Visual/Color Model Probe: Floating Island

## Purpose

This note records an exploratory multicolor 3MF model supplied by Josh for future AMP visual-resolution and surface/color planning work.

This is not part of Run 001's stock-versus-experimental profile-only metric table. It is not U1 validation. It is not physical mixed-nozzle validation. It is a candidate model for later planner reasoning around visibility, cosmetic surfaces, color/detail preservation, and region-specific resolution allocation.

## Source File

Local source:

```text
C:\Users\d\Downloads\Floating+Island.3mf
```

Observed package size:

```text
126,438,172 bytes
```

The source 3MF is not committed to the repository because it is large and its redistribution/license status has not been reviewed.

## Package Summary

Inspection of the 3MF package found:

- 27 model objects in `3D/3dmodel.model`.
- 27 build items.
- Object model files under `3D/Objects/`.
- Project settings under `Metadata/project_settings.config`.
- Model/object settings under `Metadata/model_settings.config`.
- Plate thumbnails for eight plates.
- Structured plate object metadata for `Metadata/plate_4.json`.
- Local thumbnail title appears to identify the model as `Minka Skyland`.

Local extracted thumbnails were written under:

```text
outputs/amp_visual_color_probe/floating_island/
```

Those extracted images are local inspection artifacts and are not committed.

## Object/Region Signals

The model has named parts that map naturally to visible/cosmetic regions:

| Object/part family | Example names | Observed extruder IDs | AMP relevance |
| --- | --- | --- | --- |
| Grass / leaves | `Base-Grass`, `Island-Grass`, `Island-Tree-Leaves`, `Grass-Mountain` | 1 | Cosmetic visible color regions and fine organic detail. |
| Tree trunk / roof beams | `Tree-Trunk`, `House-Upper-RoofBeams`, `House-Lower-RoofBeams` | 1, 2 | Small structural/cosmetic features. |
| House frame | `House-Lower-Frame`, `House-Upper-Frame` | 3 | Visible architectural detail. |
| Glass | `House-Lower-Glass`, `House-Upper-Glass` | 6 | Transparent/visual material region. |
| Rock / mountain | `Base-Rock-Perimeter`, `Island-Rock`, `Island-Mountain`, `Island-Rock-Cap` | 4 | Mixed cosmetic/bulk region candidate. |
| Water / waterfall | `Base-Lid-Water`, `Island-Water`, `Island-Waterfall` | 5 | Cosmetic surface and special top-pattern behavior. |
| Connector / ladder details | `Island-Mountain-Connectors`, `Ladder` | 3, 4 | Small detail/features where planner should preserve geometry. |

Some water objects use `archimedeanchords` surface/infill patterns, which makes the model useful for future top-surface and visual-pattern preservation checks.

## Why This Model Is Useful

This model is useful for AMP because it is not just a simple mechanical coupon. It contains:

- multicolor/object-assigned regions;
- visible architectural detail;
- top/cosmetic surfaces;
- organic surfaces;
- high-detail small features;
- likely hidden/internal bulk areas;
- multiple material/color roles;
- multiple plates.

That makes it a good later probe for the question:

```text
Where should AMP preserve visual resolution, and where can it reduce motion/resolution cost without hurting visible detail?
```

## Candidate AMP Questions

This model can help evaluate:

- whether visible/color-critical surfaces should be protected from wider paths;
- whether top-patterned water surfaces should be conservative;
- whether hidden rock/base bulk can tolerate wider internal widths or coarser layer height;
- whether small architectural features should be classified as detail-critical;
- whether color/material regions can act as early proxy labels for future AMP region classification;
- whether future preview/debug artifacts can make planner recommendations understandable to users.

## Suggested Future Probe

Future probe name:

```text
AMP Visual/Color Probe 001: Floating Island / Minka Skyland
```

Suggested stages:

1. Open the project in Bambu Studio or Orca-family preview and identify visible/cosmetic regions.
2. Record which parts are color/material-assigned.
3. Produce a manual AMP-style region map:
   - preserve visible detail;
   - preserve top/cosmetic pattern;
   - preserve small architectural features;
   - candidate hidden/internal bulk;
   - reject candidate due to thin/detail geometry.
4. Compare the manual region map against the offline resolution cost model.
5. Do not alter G-code or slicer behavior.

## Non-Claims

This probe does not claim:

- print-time improvement;
- print quality improvement;
- strength improvement;
- dimensional accuracy improvement;
- U1 validation;
- physical mixed-nozzle validation;
- working surface-color planning;
- implemented advanced surface-color behavior.

It is an exploratory model-selection and planning note only.
