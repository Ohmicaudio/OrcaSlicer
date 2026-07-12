# AMP Floating Island 3MF Observation 001

## Purpose

Verify the read-only streaming AMP 3MF observer on a detailed multi-plate, multi-material project without redistributing or modifying the source model.

## Source And Method

The local source was `C:\Users\d\Downloads\Floating+Island.3mf`. It was observed in place and was not copied into the repository or output directory.

| Measure | Observed value |
| --- | ---: |
| Source SHA-256 before observation | `8399e4ff4e428969d092844ddac6c6fd8c063b062fcbfedc7c02f3099d600e17` |
| Source SHA-256 after observation | `8399e4ff4e428969d092844ddac6c6fd8c063b062fcbfedc7c02f3099d600e17` |
| Compressed source size | 126,438,172 bytes |
| Archive members | 78 |
| Declared uncompressed member bytes | 905,698,105 bytes |
| Observation JSON SHA-256, run 1 | `d0487e55edbef1546e8efd470173ff8e1250e5e126a4f1bb8a748371366fbbda` |
| Observation JSON SHA-256, run 2 | `d0487e55edbef1546e8efd470173ff8e1250e5e126a4f1bb8a748371366fbbda` |
| Observation Markdown SHA-256, run 1 | `6f0ffe5a7efb663d03734538e028f204ce572be7c1375c553c9b23224546137e` |
| Observation Markdown SHA-256, run 2 | `6f0ffe5a7efb663d03734538e028f204ce572be7c1375c553c9b23224546137e` |

Observer command, repeated with `observation-2` output names for the second run:

```powershell
python tools\amp_observe_3mf.py --3mf 'C:\Users\d\Downloads\Floating+Island.3mf' --out-json 'B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_floating_island_observation\observation-1.json' --out-md 'B:\ohmic\Snapmaker-OrcaSlicer\outputs\amp_floating_island_observation\observation-1.md'
```

Both commands exited `0`. The source hash and size were unchanged afterward. The output directory contained only the two JSON and two Markdown reports and contained zero directories, confirming that no expanded 3MF directory was created. The observer read archive members as streams; it did not extract the archive.

| Run | Wall time | CPU time | Peak working set |
| ---: | ---: | ---: | ---: |
| 1 | 137.617528 seconds | 137.062500 seconds | 27,648,000 bytes |
| 2 | 133.067233 seconds | 132.625000 seconds | 26,263,552 bytes |

## Observation Result

| Measure | Observed value |
| --- | ---: |
| Plates | 8 |
| Objects | 27 |
| Parts | 29 |
| Declared material slots | 7 (`1` through `7`) |
| Material assignments used by objects | 6 (`1` through `6`) |
| Physical nozzle vector | `0.4, 0.4` |
| Total vertices | 5,685,664 |
| Total triangles | 11,372,080 |
| Top-level warnings | 0 |
| Object warnings | 0 |
| Deterministic repeats | 2 of 2 JSON reports matched; 2 of 2 Markdown reports matched |

Plate inventory:

| Plate | Name | Objects |
| ---: | --- | ---: |
| 1 | Floating Island | 5 |
| 2 | Base Rocks | 2 |
| 3 | Base & Island Water | 4 |
| 4 | Grass & Tree Leaves | 8 |
| 5 | Tree Trunk | 1 |
| 6 | House Frames | 3 |
| 7 | House Glass | 2 |
| 8 | House Roofs | 2 |

Across the independently reported object-local bounds, the coordinate envelope was `[-60.0199432, -53.9653931, -60.9595261]` to `[60.0199432, 53.9653931, 60.9595261]`. This is an observation summary, not a transformed plate or manufacturing bound.

## Assignment Separation

The 27 object records use material assignments `1` through `6`. These values remain material/color metadata and are resolved separately from the project-level physical nozzle vector.

All 27 `physical_nozzle_assignment` fields are null. All 27 `recommended_tool_class` fields are also null. The observer therefore did not reinterpret material assignments as physical nozzle selections and did not recommend an AMP tool class.

## Limits

- This is read-only representation observation.
- No geometry scoring or manufacturing-region split was performed.
- No nozzle or tool class was recommended.
- No 3MF was modified.
- No G-code was generated.
- No physical U1 or mixed-nozzle behavior was validated.
- The source model is not committed or redistributed.
