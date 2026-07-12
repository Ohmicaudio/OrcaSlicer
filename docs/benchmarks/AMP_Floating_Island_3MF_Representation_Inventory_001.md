# AMP Floating Island 3MF Representation Inventory 001

## Purpose

Inventory the user-provided detailed multi-color `Floating+Island.3mf` as a real-world AMP representation stress case.

This is read-only project inspection. The source model is not committed or redistributed.

## Source

```text
C:\Users\d\Downloads\Floating+Island.3mf
```

Embedded project metadata:

| Field | Value |
| --- | --- |
| Title | `Minka Skyland - Levitating Island` |
| Designer | `Entropy` |
| License | `Standard Digital File License` |
| Application | `BambuStudio-02.07.01.62` |
| SHA-256 | `8399E4FF4E428969D092844DDAC6C6FD8C063B062FCBFEDC7C02F3099D600E17` |

The license metadata means the model is suitable for local evaluation but should not be added to the public repository without explicit redistribution permission.

## Package Scale

| Metric | Value |
| --- | ---: |
| Compressed file size | 126,438,172 bytes |
| ZIP members | 78 |
| Total uncompressed member size | 905,698,105 bytes |
| 3MF resource objects | 27 |
| Build items | 27 |
| Model-settings objects | 27 |
| Model parts | 29 |
| Plates | 8 |

The largest individual object-model members are approximately 84 MB uncompressed. Many others are approximately 42 MB. Future analysis must stream archive members instead of extracting the entire package into the repository.

## Plate Structure

| Plate | Name | Instances |
| ---: | --- | ---: |
| 1 | Floating Island | 5 |
| 2 | Base Rocks | 2 |
| 3 | Base & Island Water | 4 |
| 4 | Grass & Tree Leaves | 8 |
| 5 | Tree Trunk | 1 |
| 6 | House Frames | 3 |
| 7 | House Glass | 2 |
| 8 | House Roofs | 2 |

The project preserves semantic grouping that is useful to a future planner: visible vegetation, rocks, water, structural frames, transparent glass, roofs, and base components are already separated into named objects and plates.

## Object Assignment Inventory

The 27 object records use assignment values `1` through `6`:

| Assignment value | Object count | Example roles |
| ---: | ---: | --- |
| 1 | 10 | grass, leaves, roof beams |
| 2 | 1 | tree trunk |
| 3 | 3 | house frames, ladder |
| 4 | 7 | rock, mountain, connectors |
| 5 | 4 | water, waterfall, base main |
| 6 | 2 | house glass |

Representative object names include:

```text
Island-Tree-Leaves.stl
Tree-Trunk.stl
House-Lower-Frame.stl
House-Upper-Glass.stl
Island-Mountain.stl
Island-Waterfall.stl
Ladder.stl
```

## Printer And Process State

| Field | Value |
| --- | --- |
| Printer model | `Bambu Lab X2D` |
| Printer preset | `Bambu Lab X2D 0.4 nozzle` |
| Process preset | `0.20mm Standard @BBL X2D` |
| Layer height | `0.2` mm |
| Nozzle vector | `0.4,0.4` |
| Wall generator | `classic` |
| Filament profile slots | 7 |
| Filament colors | 7 |

The filament set includes basic, wood, silk, marble, and translucent PLA profiles.

## Important Representation Finding

The object assignment values are material/color assignments, not physical nozzle-diameter classes.

Evidence:

- objects reference six assignment values;
- the project carries seven filament/color slots;
- the printer configuration declares only two physical nozzle entries;
- both physical nozzle entries are `0.4` mm.

AMP must not reinterpret an existing object's `extruder` value as a `0.2 / 0.4 / 0.6 / 0.8` resolution-tool decision. Material/color identity and physical nozzle/tool identity need separate fields in the planning contract.

## Value To AMP

This model is useful for testing:

- preservation of large multi-plate 3MF packages;
- separation of material/color assignment from nozzle-class assignment;
- visible versus hidden object classification;
- semantic object-name hints;
- transparent, cosmetic, structural, and bulk role distinctions;
- future surface-color planning;
- streaming geometry observation on a high-detail project.

It is not yet a valid input to the four-region automatic handoff because AMP has not created a geometry-derived region plan for its 27 objects.

## Next Technical Boundary

The next safe implementation step is a read-only 3MF observation tool that streams project metadata and object-model XML into deterministic summaries without modifying the 3MF.

The observation record should keep these concepts separate:

```text
object identity
material/color assignment
physical nozzle/tool capability
visible/cosmetic likelihood
structural/bulk likelihood
geometry complexity summary
planner confidence and warnings
```

Only after those observations exist should AMP recommend resolution-tool classes for this model.

## Non-Claims

- AMP has not assigned mixed nozzle sizes to this model.
- This model has not been sliced through the AMP handoff.
- This does not validate physical U1 behavior.
- This does not grant redistribution rights for the model.
- This does not bypass slicer or printer validation.
