# AMP U1 Extended Firmware Adapter Probe 001

## Purpose

This probe records the first AMP adapter pass for `paxx12_u1_extended_firmware`.

The goal is to model a concrete U1 Fluidd/Klipper execution-adapter target while preserving the current AMP boundary:

- research only
- comments-only pseudo output
- sandbox templates only
- no firmware installation
- no slicer behavior changes
- no executable mixed-nozzle G-code

## External Sources Inspected

- Source repository: [paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware)
- Documentation: [Snapmaker U1 Extended Firmware Docs](https://snapmakeru1-extended-firmware.pages.dev/)
- Klipper include docs: [Custom Klipper / Moonraker includes](https://snapmakeru1-extended-firmware.pages.dev/klipper_includes)
- Klipper hook docs: [PRINT_START / PRINT_END / CANCEL_PRINT hooks](https://snapmakeru1-extended-firmware.pages.dev/klipper_hooks)
- Firmware config docs: [Firmware configuration interface](https://snapmakeru1-extended-firmware.pages.dev/firmware_config)

## Relevant Capabilities

The public docs make this a concrete AMP research target because they describe:

- Fluidd/Mainsail configuration access
- custom Klipper includes under `extended/klipper/*.cfg`
- print lifecycle hooks for `PRINT_START`, `PRINT_END`, and `CANCEL_PRINT`
- hook macro prefixes:
  - `_PRINT_START_`
  - `_PRINT_END_`
  - `_CANCEL_PRINT_`
- recovery considerations for invalid Klipper/Moonraker configuration

## Manifest Entry

Added adapter:

```text
adapter_id: paxx12_u1_extended_firmware
adapter_family: snapmaker_u1_extended_firmware
execution_status: research_only_future_experimental
emission_style: macro_pseudo
touchscreen_safe: false
fluidd_only: true
requires_hardware_validation: true
source_of_truth: amp_plan_packet
```

The adapter records:

- custom Klipper include support
- print hook support
- Fluidd/Mainsail support
- SSH support only if enabled by the firmware environment
- no current install requirement
- no current firmware modification by AMP
- warranty risk not assumed away
- recovery required before hardware experimentation

## Pseudo Emission Result

Command pattern:

```powershell
python tools\amp_emit_firmware_adapter_pseudo.py --packet outputs\amp_plan_packet_001 --manifests docs\benchmarks\AMP_Firmware_Adapter_Manifests.json --adapter-id paxx12_u1_extended_firmware --out outputs\amp_firmware_adapter_pseudo
```

Generated ignored output:

```text
outputs/amp_firmware_adapter_pseudo/paxx12_u1_extended_firmware/
```

The emitted pseudo file includes comments such as:

```gcode
; PSEUDO ONLY - NOT PRINTABLE
; AMP adapter target: paxx12 U1 Extended Firmware
; Intended future location: extended/klipper/amp_macros.cfg
; Intended future hooks: PRINT_START / PRINT_END / CANCEL_PRINT
; WOULD_PLACE_MACRO_IN extended/klipper/amp_macros.cfg
; WOULD_REGISTER_PRINT_START_HOOK _PRINT_START_AMP_VALIDATE_PACKET
; WOULD_DRY_RUN_SELECT_TOOL TOOL_CLASS=0.4 REGION="normal_visible_detail_zone"
; WOULD_VALIDATE_TOOL_MAP_FROM_AMP_PACKET
; WOULD_REQUIRE_HARDWARE_PREFLIGHT_PASS
```

Every emitted line remains commented.

## Sandbox Result

Command:

```powershell
python tools\amp_generate_fluidd_klipper_macro_sandbox.py --packet outputs\amp_plan_packet_001 --out outputs\amp_fluidd_klipper_sandbox_paxx12 --target paxx12_u1_extended_firmware
```

Result:

```text
target=paxx12_u1_extended_firmware
tool_count=4
step_count=4
```

Generated ignored output:

```text
outputs/amp_fluidd_klipper_sandbox_paxx12/
```

The sandbox records future documentation targets:

```text
extended/klipper/amp_tools.cfg
extended/klipper/amp_macros.cfg
_PRINT_START_AMP_VALIDATE_PACKET
_PRINT_END_AMP_CLEANUP
_CANCEL_PRINT_AMP_ABORT
```

The generated files remain templates/dry-run artifacts. They do not contain motion, heating, extrusion, real toolchange commands, or production G-code.

## Validation Result

Command:

```powershell
python tools\amp_validate_firmware_adapter_outputs.py --manifest docs\benchmarks\AMP_Firmware_Adapter_Manifests.json --pseudo-root outputs\amp_firmware_adapter_pseudo --sandbox-root outputs\amp_fluidd_klipper_sandbox_paxx12 --out-json outputs\amp_firmware_adapter_validation\paxx12_adapter_validation_report.json --out-md outputs\amp_firmware_adapter_validation\paxx12_adapter_validation_report.md
```

Result:

```text
passed=true
errors=0
warnings=1
```

The single warning remains intentional: `klipper_nozzlechange_extra` is not in the manifest and remains research-only/not emitted.

## Hardware Preflight Impact

The hardware preflight checklist now includes paxx12-specific checks:

- custom firmware presence confirmed
- firmware source/version recorded
- recovery method known
- `extended/klipper` include path confirmed
- macros reviewed before installation
- no sandbox file installed without review
- paxx12 adapter remains research-only until hardware evidence exists

Default validation result:

```text
status=not_ready
ready=false
pending_required=28
failed_required=0
invalid=0
```

This is the intended result. The paxx12 adapter does not make the hardware path ready.

## Risk Posture

| Area | Current posture |
| --- | --- |
| Firmware installation | Not performed by AMP. |
| Firmware recommendation | Not made by AMP. |
| Touchscreen path | Blocked for mixed physical nozzle execution. |
| Fluidd path | Future experimental only. |
| Macro files | Generated as ignored templates only. |
| Executable output | None. |
| Hardware validation | Required before status changes. |
| Recovery | Required before future hardware experiments. |

## What This Proves

- AMP can represent the paxx12 U1 Extended Firmware path as a concrete adapter target.
- AMP can emit paxx12-specific comments-only pseudo output.
- AMP can emit paxx12-specific disabled sandbox templates.
- The validator accepts the paxx12 adapter while preserving non-printable output rules.
- The hardware preflight gate remains closed by default.

## What This Does Not Prove

- This does not implement mixed-nozzle slicing.
- This does not install or flash firmware.
- This does not recommend installing custom firmware.
- This does not generate production tool-selection commands.
- This does not generate a printable mixed-nozzle file.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
- This does not prove that paxx12 U1 Extended Firmware supports AMP mixed-nozzle execution.

## Recommended Next Step

Keep the paxx12 adapter as a research-only Fluidd/Klipper target.

The next useful work is to keep the execution track offline:

1. maintain plan-packet to adapter validation
2. keep sandbox output disabled and ignored
3. require hardware preflight evidence before any status change
4. wait for U1 hardware access before considering executable macro experiments
