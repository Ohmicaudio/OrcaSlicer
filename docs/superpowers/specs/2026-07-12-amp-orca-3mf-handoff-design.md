# AMP Orca 3MF Handoff Design

## Purpose

Milestone 003 removes the manual object-to-tool assignment step between the AMP offline planner and official Orca. It converts a compatible Orca project template plus an AMP plan packet into a new Orca-loadable 3MF whose object assignments and project nozzle vector reflect the AMP plan.

The handoff is representation tooling only. It does not slice, emit G-code, control Orca, start a printer, bypass Snapmaker validation, or claim physical mixed-nozzle compatibility.

## Chosen Approach

Use a known-good official Orca 3MF as a template and patch its structured metadata.

This is preferred over two alternatives:

1. Building a complete 3MF from raw STL files would require reproducing Orca's object-resource, thumbnail, plate, relationship, and profile serialization behavior before the useful planner mapping could be tested.
2. Automating the GUI would reproduce the existing manual workflow but remain focus-sensitive and unsuitable for deterministic regression tests.

Template patching preserves the mesh objects and Orca-generated package structure that already survived a save/reopen round trip. The bridge changes only the metadata AMP owns.

## Inputs And Outputs

The command accepts:

- `--template`: an Orca 3MF containing the region objects and enough configured tool slots.
- `--packet`: an AMP plan-packet directory containing `process_queue.json` and the packet sidecar files.
- `--out`: a new `.3mf` path.

The output is a new Orca 3MF. The template is never modified in place.

## Data Flow

```text
AMP plan packet + compatible Orca 3MF template
                    |
                    v
          validate package contract
                    |
                    v
       map AMP regions to Orca objects
                    |
                    v
  set object extruder metadata and nozzle vector
                    |
                    v
     embed AMP packet under Metadata/AMP/
                    |
                    v
       atomically write Orca-ready 3MF
                    |
                    v
       validate generated package contract
```

## Region And Tool Mapping

The existing `amp_generate_orca_gui_workflow_manifest` mapping remains authoritative for the handoff:

- AMP tool classes are sorted numerically.
- The first class maps to Orca extruder `1` / G-code `T0`.
- The second class maps to extruder `2` / `T1`, and so on.
- Region names are matched to Orca object metadata after removing only a final `.stl` suffix.

Every planned region must match exactly one template object. Unmatched, ambiguous, or duplicate planned regions are errors. Template objects not named in the plan are preserved unchanged.

## 3MF Changes

### `Metadata/model_settings.config`

Parse the XML and update the object-level `extruder` metadata for each planned region. Preserve object IDs, parts, transforms, mesh statistics, plate instances, and assembly records.

### `Metadata/project_settings.config`

Parse the JSON and update the leading `nozzle_diameter` entries to the numerically ordered AMP tool classes. The template must already expose at least that many tool slots. Additional template slots remain unchanged because creating complete new extruder profiles is outside this milestone.

### Embedded AMP packet

Copy the packet's recognized sidecar files under `Metadata/AMP/`. Add a deterministic `handoff_manifest.json` recording schema version, source template SHA-256, region mapping, nozzle vector, and non-claims.

New ZIP members use a fixed timestamp and stable ordering. Existing unchanged members retain their original bytes and ZIP metadata.

## Safety And Failure Behavior

- The template cannot be the output path.
- The output is written to a temporary sibling and atomically replaced only after validation succeeds.
- Missing 3MF metadata entries, malformed JSON/XML, missing packet files, unmatched regions, duplicate regions, invalid tool classes, or insufficient template tool slots stop generation.
- No G-code, printer address, credentials, firmware commands, or execution instructions are generated.
- Hardware preflight remains `not_ready` and is preserved as packet data, not interpreted as permission to print.

## Validation

The standalone validator checks:

- the result is a readable ZIP/3MF;
- required Orca metadata entries remain present;
- every planned region has the expected one-based extruder assignment;
- the leading project nozzle vector matches the AMP tool ladder;
- embedded AMP files and the handoff manifest are present;
- manifest hashes and mapping agree with the package and source packet.

The first integration proof uses the known-good official Orca mixed-nozzle 3MF template. Orca GUI open/save and G-code export remain separate validation steps and do not authorize printing.

## Test Strategy

Python standard-library unit tests create a minimal synthetic Orca-style 3MF and AMP packet. Tests cover successful mapping, deterministic output, unchanged mesh members, packet embedding, missing regions, duplicate names, insufficient tool slots, malformed metadata, and atomic failure behavior.

The focused test command is:

```text
python -m unittest tests.tools.test_amp_generate_orca_3mf_handoff -v
```

## Files

- `tools/amp_orca_3mf_handoff.py`: structured package transformation and CLI.
- `tools/amp_validate_orca_3mf_handoff.py`: independent package validator and CLI.
- `tests/tools/test_amp_generate_orca_3mf_handoff.py`: focused unit and contract tests.
- `docs/milestones/AMP_Milestone_003_Automatic_Orca_3MF_Handoff.md`: verified milestone report after implementation.

## Non-Goals

- No mesh generation or mesh replacement.
- No automatic geometry analysis in Orca.
- No per-region layer-height implementation.
- No slicer C++ integration.
- No GUI automation requirement.
- No G-code generation changes.
- No printer connection or print start.
- No U1 touchscreen validation bypass.
- No physical mixed-nozzle validation claim.
