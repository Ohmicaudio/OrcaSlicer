# Surface Color Paint Layers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add editable, reorderable surface-color paint layers with protected facets and generic editor-only mask layers.

**Architecture:** A pure `SurfaceColorPaintLayerStack` stores triangle-index assignments separately from the GUI selector. The MMU segmentation gizmo resolves the stack from bottom to top into the existing standard facet-color representation before slicing.

**Tech Stack:** C++17, Catch2, ImGui, `TriangleSelectorPatch`, existing Plater undo and project serialization.

---

### Task 1: Add a testable layer resolver

**Files:**
- Create: `src/libslic3r/SurfaceColorPaintLayers.hpp`
- Create: `src/libslic3r/SurfaceColorPaintLayers.cpp`
- Create: `tests/libslic3r/test_surface_color_paint_layers.cpp`
- Modify: `src/libslic3r/CMakeLists.txt`
- Modify: `tests/libslic3r/CMakeLists.txt`

- [ ] Write failing Catch2 tests for bottom-to-top resolution, disabled layers, a protected paint layer, a generic mask layer, and an ignore-protection exception.
- [ ] Build `libslic3r_tests` with `/m:1`; confirm the new tests fail until the resolver exists.
- [ ] Implement `SurfaceColorPaintLayer`, `SurfaceColorPaintLayerRole`, and `SurfaceColorPaintLayerStack`. The stack must support add, duplicate, delete, move, enable, visibility, protect, and resolve operations.
- [ ] Rebuild and run `B:\ohmic\builds\amp-surface-color-assist\tests\libslic3r\Release\libslic3r_tests.exe "[SurfaceColorPaintLayers]"`.
- [ ] Commit: `feat: add surface color paint layer resolver`.

### Task 2: Persist volume layer stacks

**Files:**
- Modify: `src/libslic3r/SurfaceColorPaintLayers.hpp`
- Modify: `src/libslic3r/SurfaceColorPaintLayers.cpp`
- Modify: `tests/libslic3r/test_surface_color_paint_layers.cpp`
- Modify: `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.hpp`
- Modify: `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.cpp`

- [ ] Write a deterministic serialize/deserialize round-trip test, including layer order and protection flags.
- [ ] Implement serialization using volume identity and original triangle indices. Reconstruct the stack when a project is loaded.
- [ ] Make every stack edit a `GizmoAction` undo snapshot.
- [ ] Save, reopen, and verify the layer order and masks are retained.
- [ ] Commit: `feat: persist surface color paint layers`.

### Task 3: Connect analysis, blending, and the Paint layers panel

**Files:**
- Modify: `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.cpp`
- Modify: `src/slic3r/GUI/Gizmos/GLGizmoMmuSegmentation.hpp`
- Modify: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.cpp`
- Modify: `src/slic3r/GUI/Gizmos/SurfaceColorAssist.hpp`

- [ ] Change Apply, intensity ramp, and surface blend actions to append paint layers rather than writing selectors directly.
- [ ] Add a `Paint layers` panel with name, visible, enabled, protect, ignore-protection, up/down, duplicate, delete, and `New mask layer` controls.
- [ ] Resolve the visible stack into the existing selector and call `update_model_object()` only after resolution.
- [ ] Build `Snapmaker_Orca_app_gui` with `/m:1`, run all layer tests, and verify a protected valley blend resists a later ridge application on the Dragon Skull model.
- [ ] Save/reopen and slice to confirm resolved standard facet paint remains slicable.
- [ ] Commit: `ui: add editable surface color paint layers`.
