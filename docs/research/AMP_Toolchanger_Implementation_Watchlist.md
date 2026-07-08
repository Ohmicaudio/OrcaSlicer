# AMP Toolchanger Implementation Watchlist

## Purpose

This watchlist tracks firmware, slicer, and project threads that affect the future AMP execution layer.

The current adapter layer is offline and advisory only. Items on this list should inform design and validation, not trigger production mixed-nozzle output.

## Firmware / Controller References

### Klipper Official Documentation

Links:

- <https://www.klipper3d.org/Config_Reference.html>
- <https://www.klipper3d.org/Command_Templates.html>
- <https://www.klipper3d.org/G-Codes.html>

What to watch:

- Multiple extruder configuration patterns.
- `gcode_macro` patterns.
- Offset commands such as `SET_GCODE_OFFSET`.
- State commands such as `SAVE_GCODE_STATE` and `RESTORE_GCODE_STATE`.
- Any official toolchanger or multi-tool macro guidance.

AMP relevance:

- Best practical model for future Fluidd/Klipper-style experimentation.
- Macro layer can represent tool pick/drop, parking, purge/wipe, offset, and state lifecycle.

### KTCC / Klipper ToolChanger Code

Link:

- <https://github.com/TypQxQ/Klipper_ToolChanger>

What to watch:

- Tool object schema.
- Tool offsets.
- Parking coordinates.
- Active/standby/off heater behavior.
- Fan association.
- Restore-position support.
- Tool remapping.
- Purge/wipe hooks.

AMP relevance:

- Practical reference for a tool-object execution adapter.
- Useful comparison target for `klipper_ktcc_reference`.

### RepRapFirmware / Duet

Link:

- <https://docs.duet3d.com/en/User_manual/Reference/Gcodes>

What to watch:

- `Tn` tool selection behavior.
- `tfree#`, `tpre#`, and `tpost#` lifecycle.
- `M563` tool definition.
- `G10` offsets and temperatures.
- Tool parking and temperature examples.

AMP relevance:

- Clean semantic reference for the abstract AMP toolchange lifecycle.

## Snapmaker / Orca Watchlist

### Official Orca Mixed Nozzle Sizes Baseline

Links:

- <https://www.orcaslicer.com/wiki/guides/mixed_nozzle_sizes>
- <https://github.com/OrcaSlicer/OrcaSlicer/discussions/10175>
- `docs/benchmarks/AMP_Orca_Official_Mixed_Nozzle_Baseline_001.md`

What to watch:

- Whether official Orca's manual/static workflow can represent the AMP U1-like tool ladder: 0.2 / 0.4 / 0.6 / 0.8.
- Whether percentage-based line widths keep process profiles nozzle-agnostic across tools.
- Whether Filament for Features and painting workflows can map the existing AMP region bodies to tools.
- Whether generated G-code preserves multiple nozzle/tool metadata and emits expected tool changes.
- Whether layer height remains shared across tools, as raised in Orca discussion #10175.
- Whether 3MF/project save-load preserves manual assignments.

AMP relevance:

- This is now the primary manual/static mixed-nozzle baseline.
- AMP should compare its automated packet output against this baseline instead of claiming manual mixed-nozzle workflows do not exist.
- The shared-layer-height limitation is directly relevant to AMP's future local-Z and multi-resolution planning work.
- U1 touchscreen compatibility remains a separate Snapmaker validation question.

### LixNix OrcaSlicer Multi-Nozzle Fork

Links:

- <https://github.com/LixNix/OrcaSlicer-multi-nozzle-size-printing>
- `docs/research/AMP_LixNix_Multi_Nozzle_Fork_Audit_001.md`

What to watch:

- Whether the `multi_nozzle_multi_layer_height` branch keeps developing.
- Whether per-extruder layer-height support is submitted upstream.
- How the fork handles project save/load for new PrintConfig keys.
- Whether generated G-code examples or physical validation results are published.
- How wipe tower, support, and tool ordering behave with different nozzle sizes.

AMP relevance:

- Useful implementation reference for future behavior-changing C++ work.
- Secondary/deeper experimental reference now that official Orca manual/static mixed-nozzle support is documented.
- Confirms that mixed-nozzle support touches Flow, LayerRegion, PerimeterGenerator, ToolOrdering, WipeTower, and PrintConfig.
- Does not replace AMP's planner, sidecar packet, U1 validation, or Fluidd/Klipper adapter path.
- Should remain research/watchlist material until it is validated against AMP's safety and U1 constraints.

### Snapmaker CLI Hardening PRs

Links:

- <https://github.com/Snapmaker/OrcaSlicer/pull/560>
- <https://github.com/Snapmaker/OrcaSlicer/pull/561>
- <https://github.com/Snapmaker/OrcaSlicer/pull/562>

What to watch:

- Whether Snapmaker accepts separate CLI hardening fixes.
- Whether maintainers request consolidation.
- Whether CLI assemble-list, profile normalization, or extruder expansion changes affect benchmark automation.

AMP relevance:

- Reliable CLI slicing is necessary for repeatable offline benchmark and packet generation work.
- These PRs are independent from AMP planner behavior.

### 3MF / Profile Representation Issue

What to watch:

- How Snapmaker Orca preserves per-object or per-body process/profile assignment in 3MF.
- Whether same-plate assemble-list can preserve multiple process/nozzle classes.
- Whether a future packet-to-3MF representation path is feasible before any G-code integration.

AMP relevance:

- Same-plate process preservation is a likely bridge between offline planning and read-only visual review.

### Future Snapmaker Metadata Support

What to watch:

- Per-tool nozzle metadata.
- Logical-to-physical toolhead mapping.
- Touchscreen validation changes.
- Slicer-side metadata Snapmaker prefers for multi-tool jobs.

AMP relevance:

- Touchscreen-compatible mixed physical nozzle execution remains blocked until this class of support exists.

## Current Rule

Do not use this watchlist to justify executable mixed-nozzle output. Use it to keep the offline adapter schema aligned with real controller capabilities.
