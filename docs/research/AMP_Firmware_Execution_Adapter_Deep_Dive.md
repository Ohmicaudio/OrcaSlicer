# AMP Firmware Execution Adapter Deep Dive

## Purpose

AMP should not wait for Snapmaker touchscreen mixed-nozzle support before the execution layer is designed.

The planner can remain behavior-neutral while still producing adapter-specific advisory schedules:

```text
AMP planner packet
-> firmware/controller capability adapter
-> toolchange schedule
-> adapter-specific pseudo commands
-> future Fluidd/Klipper experimental path
```

This keeps planning separate from execution. Snapmaker touchscreen mixed-nozzle execution remains blocked, while Fluidd/Klipper-style and reference firmware models can be studied without emitting printable mixed-nozzle G-code.

## Controller Targets

### Snapmaker Touchscreen

Status: blocked for mixed physical nozzle sizes.

Snapmaker support reported that touchscreen-started U1 jobs compare every used toolhead's configured nozzle size with the first `nozzle_diameter` value in the G-code. Under that path, all tools used by a job must match that single authoritative value.

AMP use: advisory only.

### Snapmaker Fluidd / Klipper Path

Status: best future experimental route.

Snapmaker support reported that Fluidd-started jobs do not perform the same nozzle-size verification. That makes the Fluidd path the realistic future route for developer-only mixed physical nozzle experiments, after U1 hardware validation.

AMP use: future developer-only experimental adapter. No executable commands yet.

### Generic Klipper Macro Path

Status: practical macro model.

Klipper supports multiple extruder configuration sections such as `[extruder1]`, and supports user-defined `[gcode_macro]` sections. Its G-code command set includes state and offset primitives such as `SET_GCODE_OFFSET`, `SAVE_GCODE_STATE`, and `RESTORE_GCODE_STATE`. Those primitives are enough to model the kind of save, offset, tool-selection, purge/wipe, and restore lifecycle AMP needs to reason about before real hardware output exists.

References:

- Klipper configuration reference: <https://www.klipper3d.org/Config_Reference.html>
- Klipper command templates: <https://www.klipper3d.org/Command_Templates.html>
- Klipper G-code reference: <https://www.klipper3d.org/G-Codes.html>

AMP use: macro adapter model.

### KTCC / Klipper ToolChanger Code

Status: practical Klipper toolchanger reference.

KTCC describes a Klipper toolchanger architecture with tool objects, tool offsets, parking coordinates, extruder/fan association, active/standby heater states, restore-position behavior, purge/wipe controls, and tool remapping.

Reference:

- KTCC GitHub repository: <https://github.com/TypQxQ/Klipper_ToolChanger>

AMP use: reference for how an adapter can map planner tool classes into tool objects rather than raw T-code.

### Klipper NozzleChange Extra

Status: research-only candidate.

`klipper_nozzlechange_extra` is not emitted by the current adapter manifest. It remains on the research list until AMP has a concrete implementation source, command model, assumptions, and safety boundary for that adapter family.

AMP use: possible future adapter after documentation and source review.

### RepRapFirmware / Duet Path

Status: clean conceptual model.

RepRapFirmware provides a clear tool semantics reference. Its toolchange lifecycle uses tool selection, `tfree#`, `tpre#`, and `tpost#` macros, tool temperature handling, and G10-defined offsets. Tool definitions are handled with commands such as `M563`, and tool offsets/temperatures are commonly associated with `G10`.

Reference:

- Duet3D G-code dictionary: <https://docs.duet3d.com/en/User_manual/Reference/Gcodes>

AMP use: semantic reference for a portable toolchange lifecycle.

### Other Firmware / Marlin / Repetier

Status: lower priority.

These should remain reference targets unless an active toolchanger path becomes relevant to AMP. The immediate project pressure is Snapmaker Fluidd/Klipper and clean reference semantics.

## Key Comparison Dimensions

| Dimension | Why AMP Cares |
| --- | --- |
| Tool definition model | Maps AMP tool classes to physical or logical tools. |
| Per-tool offsets | Needed before mixed physical nozzle execution is realistic. |
| Per-tool heaters/standby | Needed for idle/active tool temperature control. |
| Toolchange macros | Needed for pick/drop, lock/unlock, and sequencing. |
| Parking/docking | Needed for physical toolchanger safety. |
| Purge/wipe support | Needed before material/nozzle transitions can be validated. |
| State save/restore | Needed around toolchange moves and offsets. |
| Nozzle metadata support | Needed for touchscreen-compatible mixed-nozzle workflows. |
| Compatibility with AMP packet | Determines whether the offline packet can feed the adapter. |
| Risk level | Controls whether an adapter is blocked, reference-only, or future experimental. |
| Implementation difficulty | Guides sequencing. |

## Capability Matrix

| Target | Tool model | Offsets | Heaters/standby | Toolchange macros | Parking | Purge/wipe | State save/restore | Nozzle metadata | AMP status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Snapmaker touchscreen | U1 job validation path | Not enough for mixed sizes | Firmware/profile dependent | Not exposed as AMP target | Not AMP-controlled | Not AMP-controlled | Not AMP-controlled | Single first `nozzle_diameter` behavior | Blocked/advisory |
| Snapmaker Fluidd/Klipper | Klipper-style path | Future hardware validation | Unknown on U1 | Future macro path | Future macro path | Future macro path | Klipper-style primitives | No touchscreen verification path | Future experimental |
| Generic Klipper macro | User macros | `SET_GCODE_OFFSET` style | Macro dependent | `[gcode_macro]` | Macro dependent | Macro dependent | `SAVE_GCODE_STATE` / `RESTORE_GCODE_STATE` | Not native nozzle metadata | Reference/prototype |
| KTCC | Tool objects | Tool config | Active/standby/off model | Tool object macros | Tool zone/park | Toolchanger macros | Configurable restore | Tool config dependent | Reference/prototype |
| RepRapFirmware | Defined tools | `G10` offsets | Tool temperature model | `tfree#` / `tpre#` / `tpost#` | Macro based | Macro based | Macro dependent | Tool definition dependent | Semantic reference |
| Marlin/Repetier | Varies | Varies | Varies | Varies | Varies | Varies | Varies | Varies | Low priority |

## Findings

- AMP should target an adapter model, not one firmware.
- RepRapFirmware provides the cleanest reference semantics for the tool lifecycle.
- Klipper/Fluidd is likely the first practical experimental route for U1-adjacent work.
- KTCC is worth studying as a macro/plugin architecture for tool objects, parking, offsets, heaters, and state.
- Snapmaker touchscreen remains blocked until official per-tool metadata and logical-to-physical tool mapping support exists.
- Adapter output should stay comments-only until hardware validation, explicit developer controls, and safety review exist.

## Non-Claims

- No firmware flashing is recommended yet.
- This does not implement production mixed-nozzle output.
- This does not change Snapmaker validation behavior.
- No physical mixed-nozzle validation has been performed.
