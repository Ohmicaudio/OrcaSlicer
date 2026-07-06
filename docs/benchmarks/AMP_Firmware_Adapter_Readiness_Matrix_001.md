# AMP Firmware Adapter Readiness Matrix 001

## Purpose

This matrix records the current readiness of AMP firmware/controller adapters after mechanical validation of generated pseudo and sandbox outputs.

Validation report generated locally:

```text
outputs/amp_firmware_adapter_validation/adapter_validation_report.md
```

Result:

```text
passed=true
errors=0
warnings=1
```

The single warning is intentional: `klipper_nozzlechange_extra` remains research-only/not emitted.

## Readiness Matrix

| adapter_id | family | status | pseudo emitted | sandbox emitted | executable now | hardware validation required | touchscreen safe | Fluidd path | source confidence | notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `snapmaker_touchscreen_blocked` | Snapmaker | blocked/advisory | yes | no | no | yes | no | no | high | Represents the current blocked touchscreen path for mixed physical nozzle execution. |
| `snapmaker_fluidd_klipper_experimental` | Snapmaker/Klipper | future experimental | yes | yes | no | yes | no | yes | medium | Most realistic future experimental route after U1 hardware validation. |
| `paxx12_u1_extended_firmware` | Snapmaker U1 Extended Firmware / Klipper | research-only/future experimental | yes | yes | no | yes | no | yes | medium/high for documented include and hook paths; low for mixed-nozzle execution | Concrete U1 Fluidd/Klipper adapter candidate based on public paxx12 extended-firmware docs. |
| `generic_klipper_macro` | Klipper | reference/prototype | yes | no | no | yes | no | possible | medium | Macro model for future adapter shape; not printer-specific. |
| `klipper_ktcc_reference` | Klipper/KTCC | reference/prototype | yes | no | no | yes | no | possible | medium | Tool-object reference model; not currently emitted as executable output. |
| `reprap_firmware_reference` | RepRapFirmware/Duet | semantic reference | yes | no | no | yes | no | no | high | Clean reference model for T-code lifecycle semantics. |
| `klipper_nozzlechange_extra` | Klipper extension candidate | research-only/not emitted | no | no | no | yes | no | possible | low | Not emitted until a concrete source, command model, and safety boundary are reviewed. |

## Validator Coverage

The validator checks:

- comments-only pseudo output
- non-printable warnings
- no uncommented `T0` / `T1` / `T2` / `T3` commands
- no uncommented `G0` / `G1` motion commands
- no uncommented extrusion commands
- no uncommented `M104` / `M109` heating commands
- no uncommented `M140` / `M190` bed heating commands
- no uncommented `M106` fan commands
- no uncommented `M82` / `M83` extrusion mode commands
- no uncommented `SET_GCODE_OFFSET`
- no uncommented `SAVE_GCODE_STATE` / `RESTORE_GCODE_STATE`
- no uncommented live macro calls
- required sandbox headers
- 0.2 / 0.4 / 0.6 / 0.8 tool-map entries
- hardware-validation flags
- safety-report consistency

## Conclusions

- AMP has adapter manifests and pseudo-emission for reference/future execution paths.
- Current outputs are non-printable and comments-only.
- Snapmaker touchscreen remains blocked.
- Fluidd/Klipper remains the most realistic future experimental route.
- paxx12 U1 Extended Firmware is a concrete U1 Fluidd/Klipper research target, but executable mixed-nozzle behavior remains unvalidated.
- NozzleChange remains research-only unless concrete command semantics are reviewed.
- KTCC and RepRapFirmware remain reference models.
- No adapter is production-executable today.

## What This Does Not Prove

- This does not implement mixed-nozzle slicing.
- This does not flash or modify printer firmware.
- This does not generate production `T0`, `T1`, `T2`, or `T3` commands.
- This does not generate a single mixed-nozzle G-code print.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
- This does not install, flash, or recommend custom firmware.
