# AMP Surface Color Assist Design

## Purpose

Define a future Orca GUI feature that helps a user color recessed and raised surface details without manually tracing every triangle. The feature analyzes a selected model volume, previews a soft geometry field, suggests a loaded filament color, and converts only an explicitly accepted selection into ordinary Orca color painting.

The first version is an authoring aid. It does not change slicing algorithms, G-code generation, physical nozzle assignment, AMP tool planning, or FullSpectrum behavior.

## Product Boundary

The user-facing flow is:

```text
selected model volume
  -> read-only surface analysis
  -> soft valley or ridge preview
  -> user tunes controls and target filament
  -> explicit Apply
  -> existing Orca triangle color paint, undo, and 3MF persistence
```

Until Apply, no project data changes. Apply is an intentional authoring action, equivalent in authority to a user painting triangles through Orca's existing Color Painting gizmo. It may change later slicing output only through that existing paint path.

The first feature covers:

- valleys: recessed lettering, grooves, panel lines, and crevices;
- ridges: raised lettering, borders, and trim;
- soft visual preview with a thresholded, discrete applied result;
- a non-binding automatic target-filament suggestion.

Surface-break detection is deferred. It can over-select faceted or low-poly geometry and needs separate validation.

## Existing Orca Integration

The implementation should extend the established Color Painting path rather than introduce a parallel paint format.

Relevant existing code boundaries are:

- `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.*`: Color Painting UI, rendering, selected extruder state, undo integration, and model synchronization.
- `src/slic3r/GUI/Gizmos/GLGizmoPainterBase.*`: mesh-paint interaction, triangle selection, clipping, and render-data lifecycle.
- `src/libslic3r/TriangleSelector.*`: triangle-level selection and splitting behavior.
- `src/libslic3r/Model.*`: `mmu_segmentation_facets` ownership.
- `src/libslic3r/Format/3mf.cpp` and `src/libslic3r/Format/bbs_3mf.cpp`: existing paint serialization.

The recommended source layout is deliberately split:

```text
src/libslic3r/SurfaceFeatureAnalysis.hpp/.cpp
  Pure mesh analysis and deterministic surface-score result.

src/slic3r/GUI/Gizmos/SurfaceColorAssist.hpp/.cpp
  GUI-only cache, async job ownership, preview state, and Apply conversion.

src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.*
  Hosts the controls and calls the assist; remains the sole owner of normal paint mutation.
```

Exact filenames may follow local naming conventions during implementation, but the pure analysis and GUI mutation boundaries must remain separate.

## Surface Analysis Model

The first algorithm is a view-independent mesh-shape analysis. It must not depend on viewport lighting, camera position, G-code, or predicted print appearance.

For each triangle, the analyzer builds edge adjacency and evaluates signed dihedral change across shared edges:

- inward local bends contribute to a valley score;
- outward local bends contribute to a ridge score;
- boundary, non-manifold, and invalid-normal conditions are recorded as warnings rather than silently treated as shape detail.

Scores are accumulated and locally smoothed across mesh adjacency with a radius expressed in model units. A minimum patch-area filter removes small isolated responses caused by dense tessellation, scan noise, or mesh chatter.

The output is a deterministic, in-memory `SurfaceFeatureField` conceptually containing:

```text
volume identity and geometry signature
triangle count
valley score per source triangle [0, 1]
ridge score per source triangle [0, 1]
component/patch identity where available
warnings
```

The result must not contain toolpaths, G-code, physical-nozzle commands, material recipes, or FullSpectrum cadence.

## Preview And Controls

The Color Painting gizmo gains an assist panel with:

- mode: Valleys or Ridges;
- analysis radius: scale of neighboring faces considered one feature;
- score threshold: minimum score eligible for Apply;
- preview falloff: visual alpha around the selected threshold only;
- minimum patch area: noise rejection;
- target filament: suggested by contrast, editable by the user;
- Analyze, Cancel, and Apply controls.

The preview uses a continuous color/alpha ramp. It is intentionally softer than the first persisted painting result. The Apply control must state that ordinary paint is discrete in the first release.

No preview selection is written into `mmu_segmentation_facets`. Closing the gizmo, switching tools, cancelling a job, or reloading the project discards the preview field.

## Target Filament Suggestion

The assist may inspect the loaded filament display colors already used by the Color Painting gizmo. It suggests but never assigns a target:

- valley mode prefers the darkest available color with useful contrast to the selected/base color;
- ridge mode prefers the brightest available color with useful contrast;
- the user can choose any eligible loaded filament before Apply;
- if a base color or usable contrast cannot be determined, no automatic suggestion is made;
- if fewer than two usable filaments exist, preview remains available but Apply is disabled with an explanation.

This is a display-color heuristic only. It makes no claim about calibrated physical color, optical blending, perceived print appearance, or material compatibility.

## Apply, Undo, And Persistence

Apply is the only mutating operation.

1. Confirm the selected volume still matches the analyzed geometry signature.
2. Resolve the thresholded source triangles into the existing `TriangleSelector` representation.
3. Create one standard Orca gizmo undo snapshot.
4. Assign the user-selected extruder state through the existing color-paint code path.
5. Refresh the standard paint rendering and mark the project dirty.

The first release intentionally has no `Clear Assist Result` command. Orca's persisted paint representation does not distinguish an assist-generated region from manually painted work after save/reload. A targeted clear action could erase user paint. Undo is the safe reversal path.

No new 3MF schema is introduced. After Apply, standard `mmu_segmentation_facets` persistence saves the result exactly as normal Orca Color Painting does today. The in-memory score field itself is never saved in version one.

## Cache, Threading, And Invalidation

Analysis must not freeze the GUI on dense models such as the Floating Island 3MF inventory. It runs in a cancellable background job over one selected model volume.

The GUI cache is keyed by a geometry signature that includes at minimum the selected model-volume identity, mesh revision, triangle count, and any transform state that changes physical model-space distances. A rigid camera change does not invalidate analysis. Mesh edits, non-uniform scale, model replacement, or topology changes do.

The job produces a complete immutable result, then the UI thread adopts it only if its signature still matches the current selection. Partial results are never applied. New Analyze requests cancel and supersede earlier work.

The initial algorithm should be linear in triangle plus adjacency count after mesh access. It must avoid per-triangle global nearest-neighbor searches and unbounded temporary geometry copies.

## Errors And Warnings

The assist disables Apply and explains why when:

- no eligible model volume is selected;
- analysis has not completed;
- the current geometry no longer matches the result;
- the mesh has unrecoverable adjacency or normal problems;
- no second usable filament is available;
- the threshold produces no eligible patch.

Warnings may describe non-manifold edges, open boundaries, omitted noise patches, or a cancelled/obsolete result. The feature never guesses through an invalid mesh or silently changes existing paint.

## Test Strategy

Pure analysis tests use compact synthetic meshes and cover:

- a stable recessed trough produces stronger valley scores than surrounding flats;
- a raised ridge produces stronger ridge scores;
- flat geometry remains near zero;
- score order is deterministic across repeated runs;
- minimum-patch filtering removes isolated noise triangles;
- invalid and non-manifold input produces warnings and does not invent scores;
- cache signatures invalidate on geometry-relevant changes.

GUI and integration tests cover:

- Analyze and Cancel leave `mmu_segmentation_facets` unchanged;
- Apply creates a single undoable normal paint operation;
- Undo restores the pre-apply state;
- target-filament suggestion is non-binding;
- fewer than two usable filaments disables Apply;
- save/reload preserves the accepted ordinary color paint through existing 3MF behavior;
- a dense representative model remains cancellable and does not accept stale results.

Manual visual fixtures should include engraved text, raised text, panel grooves, a curved trim/badge surface, and intentionally rough/low-poly geometry. The rough fixture is specifically a rejection test: it should not become a blanket surface-break selection.

## Non-Goals

- No slicer-core or G-code changes.
- No `Flow`, `LayerRegion`, `PerimeterGenerator`, Arachne, `PrintObject`, profile, nozzle-validation, or firmware changes.
- No automatic painting on model load or during slicing.
- No physical nozzle assignment.
- No support, seam, or structural-region planning.
- No automatic color calibration or guarantee of a desired real-world print color.
- No persistent surface-score data.
- No continuous printed blend in the first release.

## Future FullSpectrum/Blend Track

The same stable valley/ridge field can later feed a separate optical surface-treatment design. That track may use a transition band, dither, or FullSpectrum-style material cadence to soften a printed color boundary.

It is explicitly later work. It requires its own representation, material, purge, visual-calibration, and hardware-validation design. This Surface Color Assist design neither implements nor validates that behavior.

## Acceptance Criteria For The First Feature

- A user can analyze a selected, valid model volume without changing project paint or slicer output.
- Valleys and ridges display as a coherent soft preview with adjustable threshold and noise filtering.
- The user can override the suggested target filament.
- Apply creates only normal Orca color-paint state and one undo step.
- Closing or cancelling without Apply leaves the project unchanged.
- Existing 3MF save/reload preserves only accepted ordinary paint.
- The implementation remains disconnected from AMP physical tool/nozzle execution and FullSpectrum blending.
