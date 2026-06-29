# AMP Surface Color Planner Design

## Purpose

This document defines a future Adaptive Manufacturing Planner (AMP) extension track for outer-layer-only color and detail planning. The goal is to make visible color/detail regions explicit without forcing the whole model into a color-mixing layer cadence.

The surface color planner should preserve normal structural printing for internal volume while applying CMYK-style or FullSpectrum-style optical color blending only where it is visually useful:

- visible outer shells;
- cosmetic faces;
- logo plates;
- speaker-ring faces;
- trim badges;
- labels and display panels;
- embossed or debossed text.

This is a design document only. It does not authorize C++ implementation, slicer behavior changes, G-code changes, local-Z implementation, or any production integration.

## Relationship To AMP

AMP's current core track asks where manufacturing detail and visibility matter. The surface color track adds a second decision axis: what apparent color recipe should be applied to those visible regions.

The relationship is:

```text
AMP core:
  visible exterior detail -> preserve fine geometry / small-nozzle candidate later
  internal bulk -> wider bead / large-nozzle candidate later

AMP surface color track:
  visible exterior detail -> preserve fine geometry + apply color skin
  internal bulk -> structural material only, no color blending by default
```

Surface color planning is a parallel AMP extension track. It is not part of AMP Stage 2 mixed physical nozzle validation, and it must not change the already-submitted Snapmaker Innovation Fund scope unless Snapmaker asks for future extension detail.

## Terminology

- Optical CMYK-style blending: apparent color produced by alternating visible filament layers or patterns, not pigment mixing inside a nozzle.
- FullSpectrum-style virtual mixed filament: a virtual filament recipe that resolves to alternating layers of physical component filaments.
- Outer skin: visible shell depth selected for color treatment, usually the outer one to three shells.
- Visible shell: geometry likely to be seen in the finished part.
- Color-critical region: a visible region where apparent color matters, such as a logo, badge, label, or front-facing cosmetic surface.
- Painted region: a region already marked by painting or future surface-classification logic.
- Structural region: internal or load-bearing material that should keep normal print settings unless explicitly reviewed.

## Prior Art

This track should build on existing public work and should keep claims conservative.

- Snapmaker U1 context: Snapmaker's U1 page describes four toolheads, a five-second toolhead swap claim, reduced purge waste versus filament-changing systems, automatic toolhead alignment, and multi-material flexibility. These properties make U1 a plausible candidate for outer-surface color workflows, but they do not prove any AMP behavior yet.
  Source: <https://www.snapmaker.com/snapmaker-u1>
- Ratdoux OrcaSlicer-FullSpectrum: the FullSpectrum fork describes virtual mixed-color filaments for Snapmaker U1, apparent color through layer alternation, ratio controls, bias controls, dithering controls, and assignment of mixed filaments like physical filaments.
  Source: <https://github.com/ratdoux/OrcaSlicer-FullSpectrum>
- Bambu Color Mixer reporting: Tom's Hardware describes Bambu's Color Mixer Studio as a filament-based optical blending approach related to halftoning and "Transmission Distance"; it also notes limits on sloped surfaces, top/bottom layers, and color accuracy.
  Source: <https://www.tomshardware.com/3d-printing/bambu-updates-its-3d-printers-to-print-unique-hues-or-gradients-using-two-or-three-filaments-company-acknowledges-orcaslicer-fullspectrum-fork-as-the-basis-for-the-color-prediction-part-of-the-new-feature>
- Prusa ColorMix reporting: Tom's Hardware describes Prusa's ColorMix direction as visually blending FDM filaments, notes banding and opacity/translucency limits, and describes a CMYKW direction.
  Source: <https://www.tomshardware.com/3d-printing/prusa-research-goes-full-spectrum-in-anticipation-of-indx>

The safe language for this project is "CMYK-style optical color blending for visible surface regions." Do not describe this as true CMYK pigment mixing.

## Proposed Staged Roadmap

### Phase 0: Research Only

Document how FullSpectrum-style layer alternation works, how it differs from pigment mixing, and what U1 can realistically validate. Keep this separate from AMP Stage 1 and Stage 2.

### Phase 1: Read-Only Visible-Surface Classification

No slicing changes. Future analysis may classify:

- visible outer walls;
- visible top skins;
- painted regions;
- logos and text;
- embossed or debossed details;
- color-critical regions.

Outputs should be debug artifacts only. Generated toolpaths and G-code must remain unchanged.

### Phase 2: Outer-Shell Color Assignment Plan

Still no G-code changes. Produce a read-only plan such as:

```text
region_id: 12
visible_surface: true
painted_region: true
color_mode: FullSpectrum-style optical blend
base_material: white PLA
color_recipe_id: CMYK_skin_on_white_base
outer_shell_depth: 2
```

### Phase 3: FullSpectrum Interop

Use existing FullSpectrum concepts instead of inventing a separate color engine:

- virtual mixed filaments;
- layer alternation;
- ratio controls;
- bias controls;
- dithering cadence;
- compatibility with multi-material painting where available.

Interop should remain advisory/read-only until disabled equivalence, debug output, and test models are stable.

### Phase 4: Local-Z Painted Surface Mode

This is the hard phase. Painted surface zones may need local Z subdivision so color-mixing cadence applies only to color-critical outer skin, while non-painted/internal regions stay at the base layer height.

This phase is not part of the current implementation milestone.

## Local-Z Interaction

This track depends on the constraints described in `docs/U1_Local_Z_Dithering_Design_Draft.md`.

Current constraints from that draft:

- Dithering can alternate component filaments in Z.
- Layer height is resolved globally per object layer.
- Mixed painting segmentation is applied after layers already exist.
- `Layer` has one `height`, `slice_z`, and `print_z` for the whole layer.

Future surface color planning should therefore use a two-level model:

```text
base part:
  normal layer height
  normal structural material
  normal strength-oriented settings

visible painted skin:
  local Z subdivision
  FullSpectrum-style alternation
  thin surface color layers only
```

Non-painted and internal regions should keep the base layer height. The design target is not full non-planar slicing; it is limited local Z expansion for painted visible surface zones.

No local-Z code, G-code scheduling, or layer model changes are authorized by this document.

## Data Model Sketch

Future value types may include a read-only region description like:

```cpp
struct SurfaceColorRegion {
    int object_id;
    int layer_id;
    int region_id;
    bool visible_surface;
    bool painted_region;
    std::string color_recipe_id;
    std::vector<int> physical_filaments;
    std::string virtual_mixed_filament_id;
    int outer_shell_depth;
    double confidence;
    std::vector<std::string> warnings;
};
```

The first implementation, if this track is ever started, should be pure value types and debug output only. It should not inspect real geometry until the read-only observation boundary is explicitly designed.

## Restrictions

- No color blending inside internal infill by default.
- No support color blending by default.
- No geometry scoring yet.
- No physical mixed-nozzle behavior.
- No safety or validation bypasses.
- No claims of accurate color reproduction before calibration prints.
- No assumptions that optical blending is equivalent to true pigment mixing.
- No production consumption from `PrintObject`, `LayerRegion`, `Flow`, Arachne, `PerimeterGenerator`, G-code export, profiles, UI, Snapmaker validation, or `CalibUtils.cpp`.

## Validation Plan

Validation should proceed from visibility to behavior only after explicit review:

1. Preview-only validation first.
2. Debug artifact only.
3. Test models:
   - logo plate;
   - speaker ring face;
   - curved badge;
   - text label;
   - sloped surface torture test.
4. Hardware validation later with color swatches.
5. Compare C/M/Y/K and C/M/Y/W setups.

Potential profile concepts:

```text
CMYK Skin on White Base
  C/M/Y/K outer skin, white or light base material.

CMYW Bright Surface Mode
  C/M/Y/W outer skin, no true black, better brightness and opacity control.
```

Preview and G-code inspection may show path or assignment differences. They cannot validate perceived color accuracy, translucency behavior, banding, surface quality, dimensional accuracy, layer bonding, purge/wipe behavior, or U1 toolhead reliability.

## Risks

- Color unpredictability on sloped surfaces and top/bottom surfaces.
- Opacity and translucency dependence across filament brands and colors.
- Toolchange overhead.
- Visible banding.
- Purge and wipe behavior.
- Local-Z complexity.
- Boundary defects between base-height structure and color sublayers.
- User confusion between optical blending and true mixing.
- Calibration dependence for tool offsets, Z offsets, flow, seam placement, and surface finish.

## Non-Goals

- No implementation in this milestone.
- No G-code changes.
- No local-Z implementation.
- No Arachne changes.
- No Flow changes.
- No `LayerRegion` changes.
- No `PerimeterGenerator` changes.
- No profile changes.
- No UI changes.
- No physical mixed-nozzle behavior.
- No update to the already-submitted Snapmaker Innovation Fund form.

## Future Snapmaker Response Language

If Snapmaker asks about future extensions, use conservative language:

```text
A natural extension of AMP is outer-surface color planning: using the same visibility/detail classification layer to limit FullSpectrum-style optical color blending to visible shells, logos, and cosmetic regions while keeping internal structure on normal print settings. This would complement, not replace, the current bead-width and mixed-nozzle roadmap.
```

This language should not be added to the already-submitted form unless Snapmaker asks for more detail.
