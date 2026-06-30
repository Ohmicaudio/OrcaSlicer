# AMP Snapmaker CLI Assemble-List Issue Investigation

## Purpose

Document the local investigation into Snapmaker Orca's `--load-assemble-list` behavior while preparing AMP Run 001 same-plate benchmark comparisons.

This note does not propose an AMP behavior change. It records why the same-plate CLI path is currently treated as a local tooling blocker for Snapmaker Orca V2.3.4.

## Local versions checked

- Snapmaker Orca public release: `v2.3.4`, published June 11, 2026.
- Snapmaker Orca executable tested locally: `Snapmaker_Orca_Windows_V2.3.4_portable`, CLI log version `01.10.01.50`.
- Upstream OrcaSlicer public release: `v2.4.1`, published June 28, 2026.
- Upstream OrcaSlicer executable tested locally: `orca-slicer.exe` from `v2.4.1` portable release.

Public Snapmaker release metadata did not show a newer Snapmaker beta after `v2.3.4`. Older Snapmaker beta/prerelease entries exist, but no newer public beta was found during this check.

## Symptom

Snapmaker Orca V2.3.4 crashes when slicing through `--load-assemble-list`, even for a single-object control assemble list.

Observed Snapmaker CLI log pattern:

```text
construct_assemble_list: Plate 1, obj count 1
construct_assemble_list: Plate 1, used filaments 1
construct_assemble_list: has objects need to be merged
warning no filament colors found in projects
total 1 models, 0 objects
Slic3r::GUI::PartPlate::calc_exclude_triangles:Unable to create exclude triangles
PartPlate same shape, skip directly
```

The process then exits with Windows access violation code `-1073741819`.

The same object/profile family can be sliced by upstream OrcaSlicer V2.4.1 through a same-plate assemble-list workflow.

## Important correction

The `total 1 models, 0 objects` line is misleading in this code path. Local inspection shows the second value is derived from `orients_requirement.size()`, not directly from `m_models[0].objects.size()`.

This means public issue reports that interpret that line as proof that all model objects were lost may be over-reading the log. The crash may still involve plate/object setup, but this log line is not enough by itself to prove object transfer failure.

## Related public upstream issues

- OrcaSlicer issue #11588: `Bug: --load-assemble-list Segmentation Fault`
  - <https://github.com/OrcaSlicer/OrcaSlicer/issues/11588>
  - Reported against OrcaSlicer 2.3.1.
  - Shows similar `--load-assemble-list` crash symptoms and the same misleading `total 1 models, 0 objects` log line.
  - Closed as a duplicate of issue #6611.
- OrcaSlicer issue #6611: `CLI Assembly process fails with Segmentation fault: 11`
  - <https://github.com/OrcaSlicer/OrcaSlicer/issues/6611>
  - Older CLI assemble-list crash report.
  - Closed as stale.
- OrcaSlicer issue #12996: `CLI multi-extruder slicing fails on H2/H2D`
  - <https://github.com/OrcaSlicer/OrcaSlicer/issues/12996>
  - Newer CLI multi-extruder report; related to CLI robustness but not the same minimal single-object assemble-list reproduction.
- OrcaSlicer PR #13406: `Fix CLI multi-color slicing crash for single-extruder AMS printers`
  - <https://github.com/OrcaSlicer/OrcaSlicer/pull/13406>
  - Related CLI/profile indexing failure area, but not proven to be the same root cause as the Snapmaker assemble-list crash.

## Local code comparison findings

Snapmaker's current `src/Snapmaker_Orca.cpp` assemble-list path is behind upstream OrcaSlicer V2.4.1 in several relevant areas.

Notable differences:

- Snapmaker `construct_assemble_list(...)` has the older signature:
  - `construct_assemble_list(..., PlateDataPtrs &plate_list)`
- Upstream V2.4.1 has:
  - `construct_assemble_list(..., PlateDataPtrs &plate_list, std::vector<RGBA>& all_colours)`
- Upstream V2.4.1 includes more robust color/material handling for CLI-loaded objects.
- Snapmaker's STL object name handling removes only three characters from `.stl`, leaving a trailing dot:
  - `object_name.erase(object_name.end() - 3, object_name.end())`
- Upstream V2.4.1 removes four characters:
  - `object_name.erase(object_name.end() - 4, object_name.end())`
- Snapmaker `PartPlateList::load_from_3mf_structure(...)` has the older signature:
  - `load_from_3mf_structure(PlateDataPtrs& plate_data_list)`
- Upstream V2.4.1 has:
  - `load_from_3mf_structure(PlateDataPtrs& plate_data_list, int filament_count = 1)`
- Upstream V2.4.1 adds `PartPlate::check_objects_empty_and_gcode3mf(...)` and uses it in several plate/extruder paths.
- Upstream V2.4.1 wraps render-only plate shape work in `if (m_plater != nullptr)` inside `PartPlate::set_shape(...)`.

The last item lines up with the local Snapmaker crash log because the failing log includes `calc_exclude_triangles` during CLI plate setup. In upstream V2.4.1, part of that render-data path is skipped when no GUI plater exists.

## Current best hypothesis

The Snapmaker V2.3.4 `--load-assemble-list` crash appears to be a Snapmaker fork/upstream-version CLI assemble-list issue, not an AMP profile override issue.

Evidence:

- Snapmaker crashes even for a single-object assemble-list control.
- The crash occurs before meaningful AMP benchmark comparison work.
- Upstream OrcaSlicer V2.4.1 can slice the same same-plate comparison workflow locally.
- Snapmaker's assemble-list and PartPlate code paths lack several upstream V2.4.1 CLI hardening changes.

The likely issue area is the old CLI assemble-list plus PartPlate loading/setup path:

- `construct_assemble_list(...)`
- `PartPlateList::load_from_3mf_structure(...)`
- `PartPlate::set_shape(...)`
- CLI-safe guards around render-only plate data and empty-object/gcode-3mf cases

## Separate issue: exact stock profile CLI load

The earlier Snapmaker exact stock profile CLI failure involving `wipe_tower_filament` appears separate from the assemble-list crash.

For Run 001, a CLI-safe temporary profile was used to bypass that profile-load problem while preserving the benchmark intent. The assemble-list crash still occurred with that safer temporary profile, so the assemble-list issue should be investigated separately.

## Practical benchmark impact

For AMP Run 001, Snapmaker Orca GUI preview remains the most relevant visual review path.

For command-line same-plate comparisons, upstream OrcaSlicer V2.4.1 currently works better as a local tooling proxy. That result should not be presented as Snapmaker U1 validation; it is only a way to evaluate whether the same-plate comparison workflow is viable in the Orca CLI family.

## Suggested next investigation step

Before any fix is attempted, isolate a minimal patch branch that backports only the relevant upstream CLI/PartPlate hardening changes and verifies:

- single-object assemble-list no longer crashes in Snapmaker Orca;
- two-object same-plate assemble-list no longer crashes;
- normal one-model CLI slicing remains unchanged;
- no AMP code is consumed by production slicer paths;
- no Snapmaker nozzle validation or safety path is bypassed.

No such patch has been applied in this branch.
