# AMP Fluidd Klipper Macro Sandbox 001

## Purpose

This report documents the first disabled Fluidd/Klipper macro sandbox generated from an AMP offline plan packet.

The sandbox maps the advisory AMP packet into:

```text
AMP plan packet
-> Fluidd/Klipper adapter
-> disabled macro template
-> dry-run schedule
-> safety/preflight checklist
```

The sandbox is a template only. It is not printable and is not intended to be installed on a printer without review.

## Why This Exists

Snapmaker touchscreen-started mixed physical nozzle execution remains blocked by the current U1 nozzle validation behavior. The Fluidd/Klipper path is the likely first future experimental route because it can be studied without depending on Snapmaker touchscreen support.

This package makes that execution path concrete while keeping the current safety boundary:

- no production mixed-nozzle slicing
- no real tool-selection commands
- no motion
- no heating
- no extrusion
- no firmware changes

## Input AMP Plan Packet

Input packet:

```text
outputs/amp_plan_packet_001/
```

Key packet files:

```text
outputs/amp_plan_packet_001/toolchange_schedule.json
outputs/amp_plan_packet_001/tool_assignments.json
```

## Generated Sandbox Files

Generator:

```powershell
python tools\amp_generate_fluidd_klipper_macro_sandbox.py --packet outputs\amp_plan_packet_001 --out outputs\amp_fluidd_klipper_sandbox
```

Generated ignored outputs:

```text
outputs/amp_fluidd_klipper_sandbox/amp_tools.cfg.template
outputs/amp_fluidd_klipper_sandbox/amp_macros.cfg.template
outputs/amp_fluidd_klipper_sandbox/amp_dry_run_schedule.gcode.txt
outputs/amp_fluidd_klipper_sandbox/amp_preflight_checklist.md
outputs/amp_fluidd_klipper_sandbox/amp_safety_report.md
outputs/amp_fluidd_klipper_sandbox/amp_tool_map.json
```

Generation result:

```text
tool_count=4
step_count=4
```

## Tool Map

| Tool class | Sandbox macro | Intended region |
| --- | --- | --- |
| 0.2 | `AMP_TOOL_0P2` | `micro_detail_zone` |
| 0.4 | `AMP_TOOL_0P4` | `normal_visible_detail_zone` |
| 0.6 | `AMP_TOOL_0P6` | `structural_shell_zone` |
| 0.8 | `AMP_TOOL_0P8` | `bulk_zone` |

Each tool-map entry includes:

- `tool_class`
- `nozzle_diameter`
- `selected_process_profile`
- `intended_regions`
- `fallback_tool`
- `risk_flags`
- `requires_hardware_validation`

## Macro Template Summary

Generated template:

```text
outputs/amp_fluidd_klipper_sandbox/amp_macros.cfg.template
```

Macro placeholders:

- `AMP_DRY_RUN_SELECT_TOOL`
- `AMP_VALIDATE_TOOL_CLASS`
- `AMP_APPLY_TOOL_OFFSET_PLACEHOLDER`
- `AMP_SAVE_STATE_PLACEHOLDER`
- `AMP_RESTORE_STATE_PLACEHOLDER`
- `AMP_PARK_TOOL_PLACEHOLDER`
- `AMP_PICK_TOOL_PLACEHOLDER`
- `AMP_PURGE_WIPE_PLACEHOLDER`
- `AMP_PRINT_REGION_PLACEHOLDER`

The macro bodies contain placeholder comments and `RESPOND` dry-run messages only. They do not contain real movement, heating, extrusion, or tool-selection commands.

## Dry-Run Schedule Summary

Generated dry-run schedule:

```text
outputs/amp_fluidd_klipper_sandbox/amp_dry_run_schedule.gcode.txt
```

Safety check:

```text
dry_run_non_comment_lines=0
```

The dry-run schedule records each planned step:

- region name
- planned tool class
- selected process profile
- layer height
- line width class
- risk flags
- whether a toolchange would be needed
- fallback if rejected

## Preflight Checklist Summary

Generated checklist:

```text
outputs/amp_fluidd_klipper_sandbox/amp_preflight_checklist.md
```

The checklist requires review of:

- physical nozzle installed per tool
- tool offsets
- Z offsets
- purge/wipe behavior
- material/nozzle compatibility
- 0.2 mm nozzle material restrictions
- Fluidd-only path
- blocked touchscreen path
- emergency stop access
- first hardware test as air/dry-run or non-extruding

## Adapter Coverage And NozzleChange Status

Current emitted firmware/controller adapters:

- `snapmaker_touchscreen_blocked`
- `snapmaker_fluidd_klipper_experimental`
- `generic_klipper_macro`
- `klipper_ktcc_reference`
- `reprap_firmware_reference`

`klipper_nozzlechange_extra` was not emitted in this pass. It remains a research-only candidate because the current AMP packet and sandbox need stable generic Klipper, KTCC, and RepRapFirmware reference coverage first. A NozzleChange-specific adapter should only be added after its command model, assumptions, and safety boundaries are documented from a concrete implementation source.

## What This Proves

- AMP can map its offline packet into a disabled Fluidd/Klipper macro sandbox.
- The sandbox can produce a tool map, macro templates, a dry-run schedule, a preflight checklist, and a safety report.
- The dry-run schedule can remain comments-only.
- The Fluidd/Klipper path can be advanced without changing production slicing behavior.

## What This Does Not Prove

- This does not implement mixed-nozzle slicing.
- This does not flash or modify printer firmware.
- This does not generate production `T0`, `T1`, `T2`, or `T3` commands.
- This does not generate a single mixed-nozzle G-code print.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.

## Next Safe Hardware Step

The next safe hardware step, once U1 hardware access exists, is an air/dry-run or non-extruding Fluidd-only macro test. That test must verify tool identity, offsets, parking, purge/wipe placeholders, emergency stop access, and material/nozzle compatibility before any extrusion or printable mixed physical nozzle job is considered.
