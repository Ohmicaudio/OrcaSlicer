# AMP Run 001 Model Manifest

## Purpose

This manifest records the model inputs prepared for AMP Stage 1 profile-only benchmark Run 001.

Generated and downloaded model files are stored under `outputs/amp_run_001/models/`, which is intentionally ignored by git. Do not commit generated STL, downloaded STL, generated G-code, or other large output artifacts unless a later task explicitly approves a small redistributable fixture.

## Generated Synthetic Models

Generated with:

```powershell
python tools/amp_generate_benchmark_models.py
```

Output directory:

```text
outputs/amp_run_001/models/generated/
```

| Local filename | Category | Reason for inclusion | Notes |
| --- | --- | --- | --- |
| `thin_wall_comb.stl` | Thin-wall detail | Exposes thin-feature loss and narrow-wall handling. | Multiple wall widths from sub-nozzle-scale through wider ribs. |
| `large_bracket_box.stl` | Large bracket / box | Exercises broad internal volume and box-like functional geometry. | Includes raised bosses as geometry stressors; holes are not boolean-cut in this dependency-free fixture. |
| `embossed_text_plate.stl` | Embossed/debossed text surrogate | Tests visible detail preservation on a flat plate. | Uses block-stroke text surrogates instead of font-generated lettering to avoid extra dependencies. |
| `speaker_adapter_ring.stl` | Speaker adapter ring | Automotive/audio functional ring with curved walls and mounting features. | Mounting bosses are modeled as raised cylinders, not cut holes. |
| `led_ring_face.stl` | LED speaker ring face | Thin cosmetic ring with small visible surface details. | Uses radial small features as LED/detail surrogates. |
| `sloped_surface_torture.stl` | Sloped surface torture | Exercises shallow-angle surfaces, stepped top regions, and sloped transitions. | Useful for preview-only inspection of top-surface behavior. |

## Downloaded Public Models

Downloaded model files are not committed.

| Local filename | Model title | Source URL | Author/source | License | Category | Reason for inclusion |
| --- | --- | --- | --- | --- | --- | --- |
| `3DBenchy.stl` | 3DBenchy | <https://raw.githubusercontent.com/CreativeTools/3DBenchy/master/Single-part/3DBenchy.stl> | Creative Tools / 3DBenchy | Creative Commons Attribution-NoDerivatives 4.0 International, per the 3DBenchy project repository license notice | General slicer torture model | Common public benchmark model with overhangs, curves, small features, and visible surface details. |

Downloaded to:

```text
outputs/amp_run_001/models/downloaded/3DBenchy.stl
```

Downloaded file size during Run 001 preparation:

```text
11285384 bytes
```

## Models Not Yet Added

Additional community/public models should be added only after source, license, author, and redistribution constraints are clear.

Desired future additions:

- public functional bracket or enclosure model;
- public embossed/debossed text model with a clear license;
- public modifier-volume or multi-body model;
- U1 community-provided model with explicit permission for benchmark use.

## License Reminder

Do not commit or redistribute downloaded models unless the license permits redistribution and the file size is reasonable for the repository.

For models submitted by community members, record:

- source URL or direct permission;
- author;
- license;
- category;
- intended feature stress;
- whether public benchmark use is allowed.
