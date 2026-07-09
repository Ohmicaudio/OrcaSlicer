# AMP 3MF Multi-Profile Representation Diagnostic 001

## Purpose

This diagnostic investigates whether Snapmaker Orca / OrcaSlicer 3MF project representation can preserve AMP's four-region process/tool intent better than the CLI assemble-list route.

This is representation investigation only. It does not implement mixed-nozzle slicing.

## Why This Matters

AMP's offline planner can already produce:

```text
region metadata
-> continuous resolution demand
-> U1 tool/profile assignment
-> toolchange-aware schedule
-> advisory plan packet
```

The next bridge is representation: carrying region/tool/profile intent into the slicer/project world without losing per-region information.

The current CLI assemble-list route did not preserve the full four-region process queue in one same-plate output. 3MF is the next representation candidate because it can carry project settings, model settings, object metadata, volume metadata, plates, and embedded presets.

## Assemble-List Collapse Recap

Earlier diagnostic:

```text
docs/benchmarks/AMP_Same_Plate_MultiProfile_Collapse_Diagnostic.md
```

Observed result:

- assemble-list accepted multiple objects and filament IDs
- object-level `print_params` could be set
- full independent process profiles were not represented per object
- exported G-code reported the global U1 0.4 process/profile state
- `nozzle_diameter` collapsed to `0.4,0.4,0.4,0.4`
- tool stream used one active tool behavior

Conclusion: assemble-list is useful for smoke/proxy tests, but not enough to carry AMP's full process/nozzle ladder into one job.

## 3MF / Project Code-Path Map

Inspected paths:

- `src/libslic3r/Format/bbs_3mf.cpp`
- `src/libslic3r/Format/bbs_3mf.hpp`
- `src/libslic3r/Format/3mf.cpp`
- `src/libslic3r/Format/3mf.hpp`
- `src/libslic3r/Preset.cpp`
- `src/libslic3r/PresetBundle.cpp`
- `src/libslic3r/ProjectTask.cpp`
- `src/slic3r/GUI/Plater.cpp`
- `src/slic3r/GUI/Project.cpp`
- `src/Snapmaker_Orca.cpp`

Key source findings:

| Area | Evidence | Meaning for AMP |
| --- | --- | --- |
| BBS/Snapmaker project config | `bbs_3mf.cpp` defines `Metadata/project_settings.config`. | Global project/process/printer/filament settings are stored at project level. |
| BBS/Snapmaker model config | `bbs_3mf.cpp` defines `Metadata/model_settings.config`. | Object and volume metadata are stored separately from global project settings. |
| Object config serialization | `_add_model_config_file_to_archive` writes each object's `obj->config.keys()` as metadata. | Object-level config can survive 3MF save/load when represented as object config. |
| Volume config serialization | `_add_model_config_file_to_archive` writes each volume's `volume->config.keys()` as metadata. | Volume/modifier settings can survive 3MF save/load when represented as volume config. |
| Object config import | BBS importer applies object metadata with `model_object->config.set_deserialize`. | 3MF can restore object-level config keys. |
| Volume config import | BBS importer applies volume metadata with `volume->config.set_deserialize`. | 3MF can restore volume-level config keys. |
| Extruder/material assignment | BBS importer and assemble-list paths set object/volume `extruder`. | Object/material slot assignment is a real represented field. |
| Embedded project presets | BBS exporter writes project embedded presets and project settings. | 3MF can carry project presets, but not necessarily one full process profile per object. |
| CLI 3MF load | `Snapmaker_Orca.cpp` calls `Model::read_from_file` and receives `plate_data_src`, `project_presets`, and `is_bbl_3mf`. | CLI can load BBS 3MF project structure. |
| CLI 3MF export | `Snapmaker_Orca.cpp` stores plate data and calls `export_project`. | CLI can export project 3MF, but global process state still matters. |

## What 3MF Can Store

Source and package inspection show BBS/Snapmaker 3MF can store:

- multiple objects
- multiple volumes/parts per object
- object names
- volume names
- object-level config metadata
- volume-level config metadata
- object/volume `extruder`
- project settings
- printer/process/filament setting IDs
- filament/material lists
- plate metadata
- embedded presets
- thumbnails and plate images

## What 3MF Cannot Be Assumed To Store For AMP Today

Current evidence does not prove that 3MF can represent:

- full independent per-object process profiles
- per-object `nozzle_diameter` as an execution profile
- four simultaneous process/nozzle classes in one exported G-code job
- local per-region layer-height plans that become true mixed process execution
- production mixed physical nozzle tool selection

The source supports object/volume config keys, but execution still appears anchored by the loaded project/global process/printer configuration unless slicer behavior explicitly consumes richer per-object process intent.

## Floating Island 3MF Inspection

Inspected local file:

```text
C:\Users\d\Downloads\Floating+Island.3mf
```

This file was inspected locally and was not committed.

Package summary:

- 78 archive entries
- `3D/3dmodel.model`
- many `3D/Objects/object_*.model` files
- `Metadata/project_settings.config`
- `Metadata/model_settings.config`
- `Metadata/filament_sequence.json`
- `Metadata/slice_info.config`
- plate JSON/image metadata
- thumbnails and model pictures

`Metadata/model_settings.config` summary:

- 27 objects
- 31 object-level `extruder` metadata entries
- extruder slots observed: `1`, `2`, `3`, `4`, `5`, `6`
- object-level setting examples: `brim_type`, `enable_support`, `support_style`, `wall_generator`, pattern settings
- no `print_settings_id`
- no `filament_settings_id`
- no `printer_settings_id`
- no `nozzle_diameter`
- no per-object `layer_height`

`Metadata/project_settings.config` summary:

- `print_settings_id`: `0.20mm Standard @BBL X2D`
- `printer_settings_id`: `Bambu Lab X2D 0.4 nozzle`
- `filament_settings_id`: seven filament entries
- `nozzle_diameter`: `["0.4", "0.4"]`
- global `layer_height`: `0.2`
- line-width settings stored globally

Interpretation:

Floating Island demonstrates that Bambu-style 3MF can preserve multi-object and multi-filament/material assignment, plus object-level overrides. It does not demonstrate per-object process/nozzle profile preservation.

## AMP 3MF Representation Probe Result

Created tool:

```text
tools/amp_generate_3mf_representation_probe.py
```

Command:

```powershell
python tools\amp_generate_3mf_representation_probe.py --out outputs\amp_3mf_representation_probe
```

Result:

```text
region_count=4
all_bodies_exist=true
```

Generated ignored outputs:

```text
outputs/amp_3mf_representation_probe/amp_3mf_representation_probe_manifest.json
outputs/amp_3mf_representation_probe/amp_3mf_representation_probe_instructions.md
```

The probe intentionally does not generate a 3MF file. Directly writing a BBS/Snapmaker 3MF project is too risky without using the slicer's own project writer, because the archive must coordinate model geometry, object IDs, model settings, project settings, relationships, plates, and metadata.

The probe defines the four-object representation intent:

| Region | Intended tool | Intended process profile | Layer height | Width class | Tool slot |
| --- | ---: | --- | ---: | ---: | ---: |
| `micro_detail_zone` | 0.2 | `0.06 Standard @Snapmaker U1 (0.2 nozzle)` | 0.06 | 0.22 | 1 |
| `normal_visible_detail_zone` | 0.4 | `0.16 Optimal @Snapmaker U1 (0.4 nozzle)` | 0.16 | 0.42 | 2 |
| `structural_shell_zone` | 0.6 | `0.24 Standard @Snapmaker U1 (0.6 nozzle)` | 0.24 | 0.62 | 3 |
| `bulk_zone` | 0.8 | `0.40 Standard @Snapmaker U1 (0.8 nozzle)` | 0.40 | 0.82 | 4 |

## AMP 3MF Sidecar Plan-Bundle Path

AMP now has a sidecar plan-bundle path:

```text
tools/amp_pack_3mf_plan_bundle.py
tools/amp_validate_3mf_plan_bundle.py
docs/benchmarks/AMP_3MF_Sidecar_Plan_Bundle_001.md
```

Generated ignored bundle:

```text
outputs/amp_3mf_plan_bundle/amp_multitool_resolution_fixture.amp3mf.zip
```

The bundle packages:

- separated region STL bodies
- AMP plan packet JSON
- tool assignments
- process queue
- toolchange schedule
- per-region G-code status
- debug artifact
- risk report
- adapter target metadata
- hardware preflight status
- manifest and file hashes

Validation result:

```text
passed=true
errors=0
warnings=2
region_count=4
```

The warnings are intentional:

- bundle is a sidecar authority, not native slicer mixed-profile support
- hardware preflight remains not_ready

This sidecar bundle is the current authority path for full AMP planner intent. Official Orca GUI 3MF roundtrip testing now shows that native 3MF preserves region object identity, object-to-tool assignment, project-level nozzle vector, and mixed probe process/printer IDs. It does not prove native 3MF carries AMP's richer per-region process/layer-height intent.

## Official Orca 3MF Round-Trip Test

The official Orca 3MF/project roundtrip preservation probe is documented here:

```text
docs/benchmarks/AMP_Official_Orca_3MF_RoundTrip_Preservation_001.md
```

Result:

- original 3MF saved through official Orca GUI
- original 3MF reopened through official Orca GUI
- four distinct region objects preserved
- object `extruder` metadata preserved as `1`, `2`, `3`, `4`
- project-level nozzle vector preserved as `0.2,0.4,0.6,0.8,0.8`
- mixed probe process/printer IDs preserved
- independent per-region AMP process/layer-height intent remains sidecar-only

## 3MF vs Assemble-List Comparison

| Capability | CLI assemble-list | 3MF project | manual GUI object override | AMP offline packet | Notes |
| --- | --- | --- | --- | --- | --- |
| multiple objects | yes | yes | yes | yes | All paths can represent separate region bodies. |
| per-object `print_params` | partial | object config metadata supported | likely, through GUI-supported object settings | yes | Assemble-list and 3MF can carry some object config keys. |
| full per-object process profile | no evidence | no evidence | unknown | yes, advisory | This is the core gap. |
| per-object nozzle diameter | no | no evidence | unknown | yes, advisory | Current package evidence shows nozzle diameter global/project-level. |
| per-object layer-height profile | partial object key only | no proven execution | possible GUI support needs manual test | yes, advisory | Representation and execution are different. |
| filament/tool assignment | yes, filament IDs | yes, object `extruder` | yes | yes | 3MF improves confidence for material/tool slot preservation. |
| modifier/volume support | limited | yes, volume config metadata supported | yes | region metadata | 3MF is better for object/volume structure. |
| round-trip stability | weak for full AMP queue | preserved for object/tool/nozzle metadata in official Orca GUI probe | preserved for manual object/tool setup | deterministic sidecar | Full per-region process/layer intent remains sidecar-only. |
| CLI load support | yes | yes | not applicable | no direct slicer load | CLI can load BBS 3MF. |
| GUI load support | not primary | yes | yes | sidecar only | GUI likely best next test surface. |
| G-code export fidelity | collapsed in same-plate test | unknown | unknown | not G-code | Must be measured with a real 3MF project. |

## Whether 3MF Is A Viable Bridge For AMP

3MF is a viable bridge for object identity, object/volume metadata, material/tool-slot assignment, project-level nozzle vector, and project-bundle review.

3MF is not yet proven as a bridge for full per-object process/nozzle execution. Current evidence suggests that process and nozzle identity remain project/global unless the slicer has explicit behavior to consume richer per-object process metadata.

## Next Recommended Representation Path

Recommended path:

```text
AMP packet
-> AMP 3MF sidecar plan bundle
-> official Orca 3MF object/tool-slot bridge
-> inspect 3MF reload
-> inspect exported G-code after round trip
```

Because GUI 3MF preserves object/material assignments and the project-level nozzle vector but not full AMP per-region process/layer-height intent, use it as the first manual execution/review bridge and keep the authoritative AMP plan in sidecar JSON.

If 3MF also collapses to one global process/nozzle on export, true mixed-profile execution requires later slicer integration.

If manual GUI can represent more than CLI, document the GUI-only limitation and do not treat CLI assemble-list as equivalent.

## Non-Claims

- This does not implement mixed-nozzle slicing.
- This does not generate production `T0`, `T1`, `T2`, or `T3` commands.
- This does not generate a verified mixed-nozzle print.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
