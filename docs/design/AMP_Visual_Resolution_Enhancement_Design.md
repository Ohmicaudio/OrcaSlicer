# AMP Visual Resolution Enhancement Design

## Purpose

This document defines a future Adaptive Manufacturing Planner (AMP) design track for visual/perceptual resolution enhancement.

The goal is the smallest controlled, repeatable visible detail in X/Y/Z where it matters, especially on cosmetic surfaces, labels, speaker rings, badges, trim pieces, logos, and text.

This is separate from true mechanical feature resolution. Visual resolution can make an edge, groove, stripe, or text feature appear sharper than raw nozzle diameter or layer height suggests, but it does not mean the printer has produced an isolated sub-nozzle mechanical feature.

This is future-track documentation only. It does not authorize C++ implementation, profile changes, slicer behavior changes, G-code changes, UI work, or production integration.

## Terminology

- Mechanical resolution: whether the printer can physically produce an isolated feature at a given size.
- Visual/perceptual resolution: whether a viewer can perceive a smaller or sharper-looking feature because of contrast, overlap, flattening, shadow, color, or surface treatment.
- Tactile/geometric resolution: whether the feature can be measured or felt as separate geometry.
- Visible skin: the outer surface region where cosmetic detail matters.
- Detail skin: a planned visible-surface region that may use finer line/layer/color treatment than the structural body.
- Contrast-backed detail: visible detail produced or enhanced by a color or shadow boundary behind, under, or beside the feature.

## Core Idea

AMP is a resolution-allocation planning layer. This track asks where visible detail actually needs expensive treatment, then reserves special handling for those visible/cosmetic regions.

Possible visual-resolution methods include:

- surface treatment;
- line overlap;
- squished or flattened beads;
- color contrast;
- shadow grooves;
- local-Z/detail skins;
- outer-skin color treatment.

The result should be treated as perceived detail improvement, not as proof of sub-nozzle mechanical accuracy.

## Relationship To AMP

AMP's guiding rule remains:

```text
Spend resolution only where it earns its keep.
```

Visual resolution enhancement complements:

- bead-width planning: preserve exterior/detail regions while widening internal/bulk regions where safe;
- surface-color planning: apply optical color/detail treatment only on visible skins;
- local-Z planning: subdivide detail/color zones without forcing the whole part into finer layers;
- future mixed-nozzle planning: use smaller tools only where visible-surface detail justifies the cost.

This track is useful for single-nozzle printers and toolchanger systems. Single-nozzle users can still benefit from line width, layer height, contrast, skin depth, and top-surface treatment. Toolchanger systems could later route only visible skins to a small nozzle or color/detail tool while internal bulk stays on normal or wider settings.

## Techniques To Investigate

### Squished-Line Detail

A bead may be intentionally flattened or overlapped so the visible edge reads as sharper than the nominal extrusion width.

This does not imply that the machine printed a truly independent sub-nozzle bead. It means the visible boundary or highlight may appear sharper than the bead width.

### Two-Line Visual Compression

Two adjacent lines may create a perceived seam, ridge, groove, or highlight narrower than either line alone.

Potential uses:

- small lettering;
- logo outlines;
- pinstripes;
- speaker-ring trim lines;
- cosmetic grooves;
- edge highlights.

### Overlapped Cosmetic Ridges

Small overlap between cosmetic ridges and a backing surface may make the visible boundary read sharper, but it may also create overfill, roughness, or dimensional error. This must be measured, not assumed.

### Color-Behind / Backing Color Detail

A dark or contrasting backing color can make a groove, stripe, or shallow relief feature appear sharper.

Example uses:

- black base with light visible line;
- colored backing behind a shallow groove;
- contrast layer under a thin raised feature;
- trim badges and labels.

This connects directly to AMP surface-color planning: only the visible skin needs color/detail treatment, while internal bulk remains normal.

### Visible Skin Overprint

A cosmetic surface layer can be treated like a printed skin over a structural body.

Possible uses:

- logo plates;
- speaker-ring faces;
- front trim faces;
- badges;
- label panels.

This may pair with CMYK-style or FullSpectrum-style optical color blending, but it must be described as optical surface treatment, not true pigment mixing.

### Recessed Grooves / Shadow Lines

A recessed groove, dark backing, or relief boundary may look sharper than a tiny raised feature. This may be useful for car-audio trim, speaker rings, amp plates, and interior panels where a small shadow line reads as high detail from normal viewing distance.

### Local-Z Cosmetic Surface Subdivision

Local-Z detail skins are the Z-axis version of resolution allocation:

```text
normal body -> normal layer height
visible/color/detail skin -> finer local subdivision
```

The existing local-Z draft notes that current layers use one global height per object layer. Future local-Z support would require a planning model that subdivides only selected XY zones while leaving the rest of the layer at base height.

### FullSpectrum-Style Outer-Skin Color Treatment

FullSpectrum-style workflows may be relevant for visible-skin color/detail planning. AMP should treat this as optical blending or apparent color on visible regions, not as calibrated color accuracy unless measured.

## Explicit Limits

Visual resolution is not the same as mechanical resolution.

Preview/G-code does not prove print quality.

Color contrast does not prove dimensional accuracy.

Do not claim calibrated CMYK-style output, calibrated color accuracy, or production-ready FullSpectrum-style behavior before calibration and measured prints.

Do not claim sub-nozzle physical feature size unless it is measured.

Do not claim strength, bonding, dimensional accuracy, surface quality, or mixed physical nozzle behavior from visual preview alone.

## Test Coupon Set

Future coupon set:

| Coupon | Purpose |
| --- | --- |
| Parallel line spacing coupon | Tests how close visible lines can be before they blur together. |
| Raised text coupon | Tests minimum readable raised lettering. |
| Engraved text coupon | Tests minimum readable recessed lettering. |
| Color-behind groove coupon | Tests whether contrast makes a groove look sharper. |
| Surface skin stripe coupon | Tests cosmetic overprint on a flat face. |
| Sloped face detail coupon | Tests how layer stepping affects perceived detail. |
| Speaker-ring / badge coupon | Tests real-world trim, ring, and badge details. |

These coupons should be generated and tracked separately from the current bead-width proxy coupon set unless the test matrix is intentionally combined.

## Measurements

Record:

- smallest readable text;
- smallest visible line spacing;
- perceived edge sharpness;
- measured physical line width;
- measured groove/ridge width where applicable;
- color bleed;
- ridge/groove visibility;
- macro photos;
- normal viewing distance photos;
- viewing distance and lighting conditions;
- whether the feature is readable by eye;
- whether the same feature survives macro close-up.

The key comparison is:

```text
visible/perceived detail vs. measured physical geometry
```

This is where AMP can separate cosmetic value from true mechanical capability.

## Proxy Testing

This track can start on available single-nozzle FDM hardware.

Proxy testing can validate:

- measurement workflow;
- coupon usefulness;
- readability thresholds;
- visual vs measured feature differences;
- photo documentation method;
- whether preview expectations match prints.

Bambu or other proxy tests do not validate U1 behavior.

Proxy tests do not validate physical mixed-nozzle behavior.

Proxy tests do not validate U1 nozzle-state behavior, toolchange/purge behavior, wipe behavior, calibration behavior, or bonding behavior.

## U1 / Toolchanger Future

Toolchanger systems could eventually use:

- a smaller nozzle for visible detail skins;
- a normal or larger nozzle for internal bulk;
- a color/detail tool only on visible skins;
- different tool choices for cosmetic and structural regions.

For U1 specifically, physical mixed-nozzle behavior remains hardware-validation dependent. Touchscreen-compatible mixed-nozzle support remains blocked until Snapmaker's nozzle-state and logical/physical toolhead mapping constraints are understood and supported.

Any future Fluidd-only experiment must be developer-only, clearly labeled, and hardware-validated.

## Integration Boundaries

This design does not add a production planner path.

Future implementation should remain staged:

1. Design and coupon definition.
2. Proxy coupon generation.
3. Manual physical measurement.
4. Read-only debug artifacts.
5. Preview overlays.
6. Only later, behavior-changing planner influence.

Do not write visual-resolution planner data from inside parallel perimeter generation loops. Do not alter Flow, Arachne, PerimeterGenerator, LayerRegion, G-code export, profile defaults, UI, or Snapmaker validation without a separate reviewed implementation plan.

## Cross-References

- `docs/design/AMP_Surface_Color_Planner_Design.md`
- `docs/U1_Local_Z_Dithering_Design_Draft.md`
- `docs/benchmarks/AMP_Proxy_Bead_Width_Characterization_Run_001.md`
- `docs/benchmarks/AMP_Proxy_Bead_Width_Measurement_Template.md`
- `docs/AMP_Branch_Status.md`

## Exit Criteria For This Design Track

This design track is ready for the next evidence step when:

- coupon definitions are documented;
- proxy measurement columns are defined;
- non-claims are explicit;
- results can distinguish perceived visual detail from measured geometry;
- no slicer behavior changes are implied by the design doc alone.
