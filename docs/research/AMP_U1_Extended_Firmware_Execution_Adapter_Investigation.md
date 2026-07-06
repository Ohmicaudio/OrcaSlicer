# AMP U1 Extended Firmware Execution Adapter Investigation

## Purpose

This document records a public-safe investigation of `paxx12_u1_extended_firmware` as a future AMP execution-adapter target.

The adapter target is useful because it gives AMP a concrete U1 Fluidd/Klipper path to model:

- custom Klipper include files
- Fluidd/Mainsail configuration access
- print lifecycle hooks
- future developer-only hardware preflight gates

This is research only. AMP does not install firmware, flash firmware, emit executable mixed-nozzle G-code, or recommend using custom firmware.

## Sources Reviewed

- Source repository: [paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware)
- Documentation: [Snapmaker U1 Extended Firmware Docs](https://snapmakeru1-extended-firmware.pages.dev/)
- Klipper includes: [Custom Klipper / Moonraker includes](https://snapmakeru1-extended-firmware.pages.dev/klipper_includes)
- Klipper hooks: [Klipper PRINT_START / PRINT_END / CANCEL_PRINT hooks](https://snapmakeru1-extended-firmware.pages.dev/klipper_hooks)
- Firmware config: [Firmware configuration interface](https://snapmakeru1-extended-firmware.pages.dev/firmware_config)

Observed on 2026-07-06, the public GitHub project described itself as a custom Snapmaker U1 firmware project that enables debug features such as SSH access and additional capabilities. The project also states that it is independent from Snapmaker and includes warranty/recovery risk warnings for custom firmware use.

## Relevant Public Capabilities

The public docs describe these capabilities relevant to AMP adapter research:

- custom Klipper configuration files can be added through Fluidd/Mainsail
- Klipper files under `extended/klipper/*.cfg` are automatically included
- Moonraker files under `extended/moonraker/*.cfg` are automatically included
- invalid Klipper or Moonraker configuration can prevent the service from starting
- recovery documentation is part of the extended firmware docs
- print lifecycle hooks are provided for `PRINT_START`, `PRINT_END`, and `CANCEL_PRINT`
- hook macro names are discovered by prefix:
  - `_PRINT_START_`
  - `_PRINT_END_`
  - `_CANCEL_PRINT_`
- the docs recommend placing hook macros in loaded configuration files, including under `extended/klipper/`
- the firmware config page exposes Fluidd/Mainsail selection when the relevant advanced access is available

## AMP Adapter Interpretation

AMP models this as:

```text
adapter_id: paxx12_u1_extended_firmware
family: Snapmaker U1 Extended Firmware / Klipper
status: research_only_future_experimental
source_of_truth: amp_plan_packet
emission: comments-only pseudo output
future path: extended/klipper/amp_macros.cfg
future tools path: extended/klipper/amp_tools.cfg
future hooks:
  _PRINT_START_AMP_VALIDATE_PACKET
  _PRINT_END_AMP_CLEANUP
  _CANCEL_PRINT_AMP_ABORT
```

This lets AMP test the shape of a future execution adapter without making the artifact executable.

## Safety Boundary

The current AMP branch keeps these hard boundaries:

- no firmware installation
- no firmware flashing
- no config copied to a printer
- no executable mixed-nozzle commands
- no touchscreen validation bypass
- no G-code generation changes
- no slicer behavior changes
- no assumption that warranty coverage exists for custom firmware changes
- no assumption that invalid Klipper/Moonraker config can be recovered without a known recovery path

## Why This Matters

The paxx12 path is more concrete than a generic Klipper macro model because it names U1-specific configuration locations and lifecycle hooks.

That makes it a useful future target for:

- validating AMP plan-packet preflight logic
- validating per-tool metadata checks
- testing dry-run adapter output
- comparing touchscreen-blocked versus Fluidd-only paths
- eventually determining whether U1 mixed physical nozzle experiments can be staged safely

It does not prove that mixed physical nozzle printing works on U1.

## Risks

| Risk | AMP response |
| --- | --- |
| Custom firmware can affect warranty assumptions. | AMP records warranty risk and does not recommend installation. |
| Invalid Klipper/Moonraker config can prevent services from starting. | Hardware preflight requires recovery method and macro review. |
| Generated sandbox files could be mistaken for installable config. | Headers say sandbox/template only, and validators reject live motion/heating/extrusion/toolchange leakage. |
| Fluidd path could be confused with touchscreen support. | Adapter is marked `fluidd_only: true` and `touchscreen_safe: false`. |
| Mixed-nozzle execution could be inferred from pseudo output. | Pseudo output is comments-only and non-printable. |

## Recommended Next Step

Keep `paxx12_u1_extended_firmware` as a research-only adapter target.

The next useful step is to keep improving offline validation:

1. generate paxx12-specific pseudo output
2. generate paxx12-specific disabled sandbox templates
3. validate that no live commands appear
4. keep hardware preflight status `not_ready`
5. wait for U1 hardware evidence before any executable adapter work

## Non-Claims

- This does not implement mixed-nozzle slicing.
- This does not install or flash firmware.
- This does not recommend installing custom firmware.
- This does not generate production tool-selection commands.
- This does not generate a printable mixed-nozzle file.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
