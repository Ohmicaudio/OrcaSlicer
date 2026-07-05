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
