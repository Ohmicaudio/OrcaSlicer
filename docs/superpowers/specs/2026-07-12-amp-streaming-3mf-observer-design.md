# AMP Streaming 3MF Observer Design

## Purpose

Create a standalone, read-only observer that summarizes large Orca/Bambu-style 3MF projects for future Adaptive Manufacturing Planner analysis.

The first target is the 126 MB compressed, approximately 906 MB uncompressed Floating Island project. The observer must inspect that project without extracting the archive, rewriting it, assigning nozzle classes, or changing slicer behavior.

The observer establishes a critical representation boundary: existing object `extruder` values may describe material or color assignments and must not be interpreted automatically as physical nozzle or AMP resolution-tool assignments.

## Chosen Approach

Implement a Python standard-library CLI in `tools/amp_observe_3mf.py`. It will open the 3MF as a ZIP archive, read small metadata members directly, and stream large object-model XML members with `xml.etree.ElementTree.iterparse`.

This is preferred over two alternatives:

1. Extending `amp_orca_3mf_handoff.py` would mix read-only observation with package mutation and weaken both tools' safety boundaries.
2. Implementing the observer in slicer C++ would add production integration before the observation contract and memory behavior are proven.

The standalone observer can be tested against synthetic packages and real projects without involving Orca, Snapmaker Orca, G-code generation, or printer state.

## Command Interface

The initial CLI accepts:

- `--3mf PATH`: required source 3MF.
- `--out-json PATH`: optional deterministic JSON report.
- `--out-md PATH`: optional human-readable Markdown summary.

If neither output path is supplied, the JSON report is written to standard output. Supplying output paths never changes the input archive.

The tool returns a nonzero exit code for unreadable archives, malformed required metadata, or an internally inconsistent object inventory. Partial optional metadata produces explicit warnings rather than guessed values.

## Data Sources

The observer inspects only members needed for deterministic project inventory:

- ZIP central directory metadata;
- `3D/3dmodel.model`;
- `Metadata/model_settings.config`;
- `Metadata/project_settings.config`;
- plate metadata and plate thumbnails only as names or member-presence records;
- referenced `3D/Objects/*.model` members.

Large object-model members are parsed directly from `ZipFile.open()` streams. The observer does not call `extract()` or `extractall()`, does not create an expanded project directory, and does not retain complete XML trees after member summaries are calculated.

## Observation Contract

The JSON report has a stable top-level schema:

```text
schema_version
source
project
physical_tools
materials
plates
objects
warnings
```

### Source

The source record includes:

- source file name;
- SHA-256;
- compressed file size;
- ZIP member count;
- total declared uncompressed member size;
- required and optional member-presence results.

Absolute source paths are excluded from deterministic report content. They may appear in human-facing error messages but not in the JSON contract.

### Project

The project record contains safely available metadata such as title, designer, license, source application, printer preset, process preset, wall generator, and nominal layer height. Missing optional values remain absent or null and produce no fabricated defaults.

### Physical Tools

Physical tool capability is reported from explicit project metadata only. The initial record contains the configured nozzle-diameter vector and its source member.

The observer does not infer that a physical tool is assigned to any object.

### Materials

Material records summarize explicit filament slots, profile names, colors, and other stable identifiers when available. Material slots preserve their project numbering.

### Plates

Plate records contain plate ID, plate name, and deterministic object membership. Plates are sorted by numeric plate ID, then name when IDs are unavailable or equal.

### Objects

Each object record contains, when safely available:

- object ID and name;
- plate ID and plate name;
- source object-model member;
- part count;
- vertex count;
- triangle count;
- axis-aligned bounds and dimensions;
- material/color assignment;
- resolved material slot/profile/color, if unambiguous;
- normalized semantic name tokens;
- observation warnings.

The following fields are always explicit to prevent assignment conflation:

```json
{
  "material_assignment": 4,
  "physical_nozzle_assignment": null,
  "recommended_tool_class": null
}
```

Name tokens are advisory inventory data only. Words such as `glass`, `frame`, `rock`, or `leaf` are not geometry scores and do not authorize tool assignment.

## Geometry Summary Boundary

The first implementation may compute counts and axis-aligned bounds while streaming vertices and triangles. It may compute surface area or enclosed volume only if those values can be accumulated in one pass without retaining mesh arrays and are covered by focused tests.

The implementation must not store polygons, triangles, coordinates, or complete meshes in the output. It must not classify visible surfaces, structural importance, accessibility, or manufacturing regions. Those are later observation and planner layers.

## Data Flow

```text
source 3MF
   |
   v
validate ZIP and required members
   |
   v
hash source and inventory central directory
   |
   v
parse project, plate, material, and object metadata
   |
   v
stream referenced object-model XML members
   |
   v
join explicit identities and assignments
   |
   v
sort and validate deterministic observation model
   |
   +--> JSON report
   |
   +--> optional Markdown summary
```

## Determinism

- Source content is identified by SHA-256.
- Objects are sorted by numeric object ID, then normalized name.
- Plates are sorted by numeric plate ID, then name.
- Material slots preserve numeric slot order.
- JSON uses stable key ordering, UTF-8, LF line endings, and one final newline.
- Reports contain no timestamps, temporary paths, host names, process IDs, or random identifiers.
- Repeated observation of unchanged input produces byte-identical JSON.

## Memory And Performance

- ZIP members remain compressed on disk and are never bulk-extracted.
- Large XML members use `iterparse` over `ZipExtFile` streams.
- Processed XML elements are cleared promptly.
- Mesh counts and bounds are accumulated as scalar values.
- The implementation avoids `ZipFile.read()` for large object-model members.
- A test seam records whether large members used the streaming path so regression tests do not depend only on peak-memory measurements.

The first implementation does not promise a fixed memory ceiling because XML parser and ZIP overhead vary by platform. Its required property is that memory use scales with parser state and summary data, not total uncompressed package size.

## Error And Warning Behavior

Generation fails without writing a final report when:

- the source is not a readable ZIP/3MF;
- a required project member is missing;
- required XML or JSON is malformed;
- an object references a missing object-model member;
- duplicate IDs make identity resolution ambiguous;
- plate/object membership is contradictory;
- an existing requested output would be left partially replaced.

Optional or unresolved data produces warnings, including:

- missing project title, author, preset, or license;
- material assignment that cannot be resolved to one slot;
- object name without semantic tokens;
- object-model metadata that omits optional statistics;
- physical nozzle metadata that is absent or incomplete.

Output files are written to temporary siblings and atomically replaced only after the complete observation model is validated and serialized.

## Test Strategy

Focused Python tests will create small synthetic 3MF packages and cover:

- multi-plate and multi-material inventory;
- explicit separation of material assignment, physical nozzle assignment, and recommended tool class;
- deterministic plate/object/material ordering;
- vertex, triangle, bounds, and dimension summaries;
- repeated byte-identical JSON serialization;
- optional Markdown generation;
- malformed ZIP, XML, and JSON handling;
- missing required members and missing referenced object models;
- duplicate and ambiguous object identities;
- atomic output failure behavior;
- unchanged source SHA-256 before and after observation;
- streaming-path use for object-model members.

A local integration test against `C:\Users\d\Downloads\Floating+Island.3mf` will verify the known inventory without committing or redistributing the model:

- source SHA-256 `8399E4FF4E428969D092844DDAC6C6FD8C063B062FCBFEDC7C02F3099D600E17`;
- 78 ZIP members;
- 8 plates;
- 27 project objects;
- assignment values remain material/color assignments;
- physical nozzle vector remains `0.4,0.4`;
- every `physical_nozzle_assignment` and `recommended_tool_class` remains null.

## Files Planned

- `tools/amp_observe_3mf.py`: read-only observer, deterministic serializers, and CLI.
- `tests/tools/test_amp_observe_3mf.py`: synthetic contract and failure tests.
- `docs/benchmarks/AMP_Floating_Island_3MF_Observation_001.md`: verified local integration report after implementation.

No production C++, profile, UI, G-code, or printer-control files are part of this milestone.

## Non-Goals

- No 3MF modification or handoff generation.
- No archive extraction to a project directory.
- No geometry scoring or region splitting.
- No visible-surface, cosmetic, structural, or accessibility classification.
- No nozzle, extruder, tool, bead-width, or layer-height recommendation.
- No automatic reinterpretation of material/color assignments.
- No slicer C++ integration.
- No G-code generation or validation changes.
- No GUI or preview overlay.
- No printer connection, print start, or firmware command.
- No U1 validation bypass or physical mixed-nozzle claim.

## Exit Criteria

The milestone is complete when:

- focused synthetic tests pass;
- the observer processes Floating Island without extracting the archive;
- its deterministic report matches the known package inventory;
- source hash is unchanged;
- material assignments remain separate from physical nozzle and recommendation fields;
- a repeated run produces byte-identical JSON;
- no production slicer path references or consumes the observer.
