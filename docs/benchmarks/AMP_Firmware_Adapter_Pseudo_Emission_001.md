# AMP Firmware Adapter Pseudo Emission 001

## Purpose

This report documents the first AMP firmware/controller adapter pseudo-emission pass.

The goal is to prove that the existing offline AMP plan packet can feed multiple execution-adapter views without generating printable mixed-nozzle G-code.

## Adapter Manifests Tested

Manifest:

```text
docs/benchmarks/AMP_Firmware_Adapter_Manifests.json
```

Adapters:

| Adapter | Status | Role |
| --- | --- | --- |
| `snapmaker_touchscreen_blocked` | blocked/advisory | Documents why touchscreen-started mixed physical nozzle execution remains blocked. |
| `snapmaker_fluidd_klipper_experimental` | future experimental | Models the likely U1 experimental path through Fluidd/Klipper. |
| `generic_klipper_macro` | reference/prototype | Models user-defined Klipper macro execution. |
| `klipper_ktcc_reference` | reference/prototype | Models KTCC-style tool objects, offsets, parking, heaters, and purge/wipe hooks. |
| `reprap_firmware_reference` | semantic reference | Models the RepRapFirmware-style T-code lifecycle. |

## Packet Input

Packet:

```text
outputs/amp_plan_packet_001/
```

Key packet input:

```text
outputs/amp_plan_packet_001/toolchange_schedule.json
outputs/amp_plan_packet_001/plan.json
```

The packet remains an offline advisory artifact. It does not drive production slicing.

## Pseudo Emission Outputs

Command pattern:

```powershell
python tools\amp_emit_firmware_adapter_pseudo.py --packet outputs\amp_plan_packet_001 --manifests docs\benchmarks\AMP_Firmware_Adapter_Manifests.json --adapter-id <adapter_id> --out outputs\amp_firmware_adapter_pseudo
```

Generated ignored outputs:

```text
outputs/amp_firmware_adapter_pseudo/<adapter_id>/schedule.md
outputs/amp_firmware_adapter_pseudo/<adapter_id>/pseudo.gcode.txt
outputs/amp_firmware_adapter_pseudo/<adapter_id>/safety_report.md
outputs/amp_firmware_adapter_pseudo/<adapter_id>/adapter_plan.json
```

Run result:

| Adapter | Pseudo output generated | Comments-only check |
| --- | --- | --- |
| `snapmaker_touchscreen_blocked` | yes | pass |
| `snapmaker_fluidd_klipper_experimental` | yes | pass |
| `generic_klipper_macro` | yes | pass |
| `klipper_ktcc_reference` | yes | pass |
| `reprap_firmware_reference` | yes | pass |

## Safety Report Summary

Every adapter output is comments-only. The pseudo files use advisory lines such as:

```gcode
; WOULD_SELECT_TOOL T0 for nozzle_class=0.2
; WOULD_RUN_KLIPPER_MACRO AMP_PICK_TOOL NOZZLE=0.2
; WOULD_RUN_RRF_TPRE tpre0.g
; WOULD_APPLY_OFFSET X=hardware_required Y=hardware_required Z=hardware_required
```

The pseudo-emitter does not emit executable production tool-selection commands.

## Adapter Status

| Adapter | Blocked | Experimental | Reference |
| --- | ---: | ---: | ---: |
| `snapmaker_touchscreen_blocked` | yes | no | no |
| `snapmaker_fluidd_klipper_experimental` | no | future only | no |
| `generic_klipper_macro` | no | no | yes |
| `klipper_ktcc_reference` | no | no | yes |
| `reprap_firmware_reference` | no | no | yes |

## NozzleChange Status

`klipper_nozzlechange_extra` was not emitted in this pass. It remains a research-only candidate until AMP has a concrete implementation source and documented command model for that adapter family.

The current emitted set intentionally focuses on:

- Snapmaker blocked/advisory behavior
- Snapmaker Fluidd/Klipper future experimental behavior
- generic Klipper macro behavior
- KTCC-style tool-object behavior
- RepRapFirmware reference semantics

## Recommended Next Path

1. Keep Snapmaker touchscreen mixed physical nozzle execution blocked/advisory.
2. Use Snapmaker Fluidd/Klipper as the first future experimental path after U1 hardware access.
3. Keep generic Klipper macro and KTCC adapters as practical macro architecture references.
4. Use RepRapFirmware as the clean semantic reference for the abstract toolchange lifecycle.
5. Do not emit executable mixed-nozzle commands until hardware validation, explicit developer controls, and safety review exist.

## What This Proves

- AMP can emit adapter-specific pseudo execution plans from the same offline packet.
- The adapter layer can separate planning from controller execution semantics.
- The same schedule can be viewed through blocked, Klipper-style, KTCC-style, and RepRapFirmware-style adapters.
- The pseudo-emitter can produce schedule, pseudo command, safety, and JSON adapter-plan artifacts without touching slicer behavior.

## What This Does Not Prove

- This does not implement mixed-nozzle slicing.
- This does not flash or modify printer firmware.
- This does not generate production `T0`, `T1`, `T2`, or `T3` commands.
- This does not generate a single mixed-nozzle G-code print.
- This does not validate physical mixed-nozzle behavior.
- This does not alter Snapmaker touchscreen nozzle validation.
