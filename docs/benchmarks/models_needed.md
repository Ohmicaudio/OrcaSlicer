# AMP Benchmark Models Needed

The AMP Stage 1 profile-only benchmark needs community test models that expose different geometry roles without requiring slicer behavior changes.

These models will be used to compare:

- stock Snapmaker Orca U1 profile output; and
- experimental effective-width profile output.

Preview and G-code inspection may show geometry/path differences. They cannot validate real print strength, print quality, dimensional accuracy, bonding, purge behavior, or mixed physical nozzle behavior.

## Requested Model Categories

### Thin-Wall Detail

Models with thin walls, narrow ribs, fine holes, or small exterior features.

Useful for checking whether the experimental effective-width profile preserves visible fine detail in preview.

### Large Bracket Or Box

Functional parts with large internal walls, broad sparse-infill regions, or large internal solid regions.

Useful for checking whether wider internal/bulk paths produce explainable profile-only preview differences.

### Cosmetic Top-Surface Detail

Models with broad visible top faces, shallow surface features, or surface patterns.

Useful for checking whether top surfaces remain visually plausible in preview.

### Embossed/Debossed Text

Models with raised or recessed text in multiple sizes.

Useful for checking whether letters remain legible and do not disappear in preview.

### Speaker Adapter Ring

Round or annular functional adapter geometry with visible exterior surfaces and structural inner regions.

Useful for Ohmic Audio Labs validation and for checking curved walls, rings, screw holes, and internal bulk.

### LED Speaker Ring Face

Cosmetic ring face geometry with visible front surfaces, pockets, holes, or diffuser-related features.

Useful for checking visible cosmetic detail and surface path behavior.

### Curved Badge

Small curved cosmetic object with raised/recessed details, logos, or trim contours.

Useful for checking curved visible walls and local detail preservation in preview.

### Sloped Surface Torture Test

Geometry with sloped surfaces, chamfers, shallow angles, and top/bottom transitions.

Useful for exposing preview artifacts that may not appear on flat or vertical surfaces.

### Multi-Region Modifier Model

Model or project file with modifier regions, separate bodies, or clearly distinct functional/cosmetic regions.

Useful for later comparison against future AMP read-only debug artifacts. For the current profile-only benchmark, this is still only a stock-vs-experimental profile comparison.

## Submission Notes

For each model, record:

- filename;
- source URL or author;
- license if known;
- units;
- intended scale;
- category from the list above;
- what feature the model is expected to stress.

Do not submit models that require unsupported production profile edits or slicer behavior changes for Run 001.
