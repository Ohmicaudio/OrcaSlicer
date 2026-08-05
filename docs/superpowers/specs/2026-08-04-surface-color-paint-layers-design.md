# Surface Color Paint Layers

## Purpose

Surface Color Assist needs editable, reorderable paint operations instead of
writing a single destructive facet-color result. A layer stack lets a user
combine feature analysis, brush paint, and future fills while preserving a
clear answer to which operation owns each painted facet.

## Layer Model

Each model volume owns an ordered stack of paint layers. A layer stores its
name, visibility, enabled state, paint assignments by original triangle index,
and one of these roles:

- **Paint**: assigns a physical or virtual filament to its painted facets.
- **Protect**: does not emit a filament assignment; it prevents later layers
  from altering its painted facets.

Any paint layer may enable **Protect painted facets**. This makes its painted
facets act like a protect layer while retaining its visible, printable color.
A dedicated protect layer is available for generic brush, fill, and future
selection-based masking.

## Resolution

The stack resolves bottom-to-top for a volume:

1. Start with the volume's existing/base facet colors.
2. Visit enabled layers in stack order.
3. Skip a paint assignment when an earlier enabled protect layer owns that
   triangle, unless the layer has explicitly been set to ignore protection.
4. Apply the remaining color assignments.
5. Add protection from protect layers and protected paint layers.
6. Write only the resolved standard color-paint facets to the existing triangle
   selector and model serialization path.

The mask is editor-only metadata. It never occupies a filament slot, creates
G-code, or appears as a printable material.

## User Interface

The Surface Color Assist panel gains a **Paint layers** section:

- layer name, visibility, and enabled controls;
- up/down controls for deterministic reordering;
- paint/protect role and `Protect painted facets` toggle;
- delete and duplicate actions;
- an `Ignore protection` option for exceptional later paint layers;
- an editor-only mask overlay color for protect layers.

The existing analysis and blend actions create a new paint layer rather than
mutating the resolved selector directly. The current blend-band checkboxes
remain part of creating that layer: disabled bands contain no assignments and
therefore leave their original color untouched.

## Persistence and Undo

The stack is serialized with project data using stable volume identity and
triangle-index assignments. Loading a project rebuilds the stack and resolves
the standard facet paint. Reorder, visibility, role, edit, and delete are all
single undoable gizmo actions.

## Boundaries

This feature is GUI/editor state only. It does not alter Flow, Arachne,
PerimeterGenerator, LayerRegion, G-code generation, profiles, Snapmaker
validation, or physical tool/nozzle behavior. The resolved output remains the
existing standard color-paint facet representation.

## Validation

Unit tests cover deterministic layer ordering, protected facets, generic mask
layers, disabled layers, ignore-protection exceptions, and resolution back to
base paint. GUI validation covers analysis-generated layers, reorder/delete,
undo, project save/load, and an unchanged slicing path for resolved standard
facet paint.
