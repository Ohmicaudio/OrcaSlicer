# AMP Firmware Execution Adapter Schema

## Purpose

The firmware execution adapter schema describes how AMP maps an offline advisory plan packet into a controller-specific pseudo execution model.

This is not a production G-code schema. It is a developer-side contract for comparing execution paths while preserving the current AMP safety boundary:

- planning stays separate from slicing
- adapter output stays comments-only
- no production slicer path consumes AMP
- no Snapmaker validation behavior is changed

## Adapter Object

```json
{
  "adapter_id": "generic_klipper_macro",
  "adapter_name": "Generic Klipper Macro Adapter",
  "target_controller": "Generic Klipper with user-defined macros",
  "supports_toolchange_commands": true,
  "supports_per_tool_offsets": true,
  "supports_per_tool_heaters": "macro_dependent",
  "supports_standby_temperature": "macro_dependent",
  "supports_tool_parking": "macro_dependent",
  "supports_state_save_restore": true,
  "supports_purge_wipe_macros": "macro_dependent",
  "supports_nozzle_metadata": false,
  "touchscreen_safe": false,
  "fluidd_only": false,
  "requires_hardware_validation": true,
  "command_style": "klipper_macro",
  "tool_map": {},
  "safety_warnings": []
}
```

## Required Fields

| Field | Meaning |
| --- | --- |
| `adapter_id` | Stable machine-readable adapter key. |
| `adapter_name` | Human-readable adapter name. |
| `target_controller` | Controller or firmware/control path represented by the adapter. |
| `supports_toolchange_commands` | Whether the target has an execution mechanism for tool changes. |
| `supports_per_tool_offsets` | Whether per-tool X/Y/Z offsets are representable. |
| `supports_per_tool_heaters` | Whether per-tool heater control is representable. |
| `supports_standby_temperature` | Whether active/standby tool temperature behavior is representable. |
| `supports_tool_parking` | Whether tool parking/docking is representable. |
| `supports_state_save_restore` | Whether toolchange state save/restore can be represented. |
| `supports_purge_wipe_macros` | Whether purge/wipe can be represented. |
| `supports_nozzle_metadata` | Whether the target can represent nozzle size as explicit per-tool metadata. |
| `touchscreen_safe` | Whether the adapter is compatible with Snapmaker touchscreen-started mixed physical nozzle execution. |
| `fluidd_only` | Whether the adapter is intended only for a Fluidd-style start path. |
| `requires_hardware_validation` | Whether hardware validation is required before executable output is considered. |
| `command_style` | Pseudo-emission family. |
| `tool_map` | Mapping from AMP tool class (`0.2`, `0.4`, `0.6`, `0.8`) to adapter tool descriptors. |
| `safety_warnings` | Adapter-specific warnings copied into pseudo output and safety reports. |

## Command Styles

| Command style | Use |
| --- | --- |
| `blocked` | Advisory-only path for targets that must not emit executable mixed-nozzle output. |
| `snapmaker_fluidd_klipper` | Future Snapmaker Fluidd/Klipper experimental path. |
| `klipper_macro` | Generic Klipper macro model. |
| `klipper_ktcc` | KTCC-style tool object model. |
| `reprap_firmware` | RepRapFirmware reference model. |

## Tool Map

Each adapter maps AMP tool classes into adapter-local tool descriptions:

```json
{
  "0.2": {
    "tool_id": "T0",
    "nozzle_diameter_mm": 0.2,
    "macro_name": "AMP_PICK_TOOL",
    "offset": {
      "x": "hardware_required",
      "y": "hardware_required",
      "z": "hardware_required"
    }
  }
}
```

The first manifest keeps offsets symbolic. Real offsets must come from printer-specific calibration and hardware validation, not from the offline planner.

## Example Adapters

The first manifest set includes:

- `snapmaker_touchscreen_blocked`
- `snapmaker_fluidd_klipper_experimental`
- `generic_klipper_macro`
- `klipper_ktcc_reference`
- `reprap_firmware_reference`

## Output Contract

The pseudo-emitter consumes:

```text
AMP plan packet directory
adapter manifest JSON
adapter_id
```

It emits ignored developer artifacts:

```text
schedule.md
pseudo.gcode.txt
safety_report.md
adapter_plan.json
```

`pseudo.gcode.txt` must remain comments-only. It may contain lines such as:

```gcode
; WOULD_SELECT_TOOL T0
; WOULD_RUN_KLIPPER_MACRO AMP_PICK_TOOL NOZZLE=0.2
; WOULD_RUN_RRF_TPRE tpre0.g
; WOULD_APPLY_OFFSET X=hardware_required Y=hardware_required Z=hardware_required
; WOULD_PARK_TOOL ktcc_zone_and_park
; WOULD_PURGE_OR_WIPE AMP_PURGE_OR_WIPE
```

It must not contain executable tool-selection commands.

## Safety Rules

- Adapter output is advisory and comments-only.
- Adapter output must not be treated as printable mixed-nozzle G-code.
- Snapmaker touchscreen remains blocked for mixed physical nozzle execution.
- Fluidd/Klipper experimentation remains future, developer-only, and hardware-dependent.
- Per-tool offsets, parking, purge, wipe, and heater behavior must be validated on real hardware before executable output is considered.
- The adapter layer must not alter Flow, Arachne, LayerRegion, PerimeterGenerator, G-code generation, profiles, UI, PrintObject, Snapmaker validation, or CalibUtils.cpp.
