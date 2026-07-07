# AMP U1 Extended Firmware Source Audit 001

## Purpose

This document records a read-only source/config audit of
`paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware` for future AMP
Fluidd/Klipper adapter planning.

This is research and mapping only. AMP does not flash firmware, recommend
installation, emit executable mixed-nozzle G-code, or implement mixed-nozzle
slicing.

## External Repo Snapshot

External repository:
`https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware`

Local read-only clone inspected:
`B:\ohmic\external\SnapmakerU1-Extended-Firmware`

Snapshot inspected:

```text
branch: develop
commit: c7a4e66b973f98055e25d865e71a96ebccbd4a07
describe: v1.4.1-paxx12-20-2-gc7a4e66
```

Top-level tree summary:

```text
.github
deps
docs
overlays
scripts
tools
```

## Source/Config Paths Inspected

Primary docs:

- `docs/klipper_includes.md`
- `docs/klipper_hooks.md`
- `docs/firmware_config.md`
- `docs/faulty_toolhead.md`
- `docs/afc-lite.md`

Primary source/config patches:

- `overlays/firmware-extended/02-firmware-config/patches/01-add-klipper-includes.patch`
- `overlays/firmware-extended/02-firmware-config/patches/01-add-moonraker-includes.patch`
- `overlays/firmware-extended/35-feature-klipper-hooks/patches/home/lava/origin_printer_data/config/01-klipper-hooks.patch`

Relevant runtime/config helpers:

- `overlays/firmware-extended/02-firmware-config/root/etc/init.d/S49extended-config`
- `overlays/firmware-extended/02-firmware-config/root/etc/init.d/S99firmware-config`
- `overlays/firmware-extended/02-firmware-config/root/usr/local/bin/extended-config.py`
- `overlays/firmware-extended/02-firmware-config/root/usr/local/bin/firmware-config.py`
- `overlays/firmware-extended/02-firmware-config/root/etc/nginx/fluidd.d/firmware-config.conf`

## Klipper Include Findings

The source patch `01-add-klipper-includes.patch` modifies the stock U1
`printer.cfg`:

```text
/home/lava/origin_printer_data/config/printer.cfg
```

It adds this include block:

```cfg
[include extended/klipper/*.cfg]
```

The public docs also state that all `.cfg` files under `extended/klipper/`
are automatically included and persist across reboots. The docs explicitly warn
not to modify or remove `00_keep.cfg`, and warn that invalid config can prevent
Klipper from starting.

AMP interpretation:

- A future AMP Klipper sandbox would plausibly live under
  `extended/klipper/`.
- This is a future path only, not an installation instruction.
- Hardware preflight must confirm the include path on the actual machine before
  any file is considered for hardware-side testing.

## Moonraker Include Findings

The source patch `01-add-moonraker-includes.patch` modifies:

```text
/home/lava/origin_printer_data/config/moonraker.conf
```

It adds:

```ini
[include extended/moonraker/*.cfg]
```

AMP interpretation:

- A future Moonraker status/API integration could use
  `extended/moonraker/amp_status.cfg` if justified.
- The first AMP sandbox does not need Moonraker output.
- Moonraker config must be treated as safety-sensitive because invalid config
  can prevent Moonraker from starting.

## Print Hook Findings

The source patch `01-klipper-hooks.patch` modifies `fluidd.cfg` to dispatch
hooks from live Klipper config.

Hook prefixes found:

```text
_PRINT_START_
_PRINT_END_
_CANCEL_PRINT_
```

Dispatch placement:

| Event | Prefix | Placement |
| --- | --- | --- |
| `PRINT_START` | `_PRINT_START_` | after original print-start logic |
| `PRINT_END` | `_PRINT_END_` | before original print-end logic |
| `CANCEL_PRINT` | `_CANCEL_PRINT_` | before original cancel logic |

The dispatcher scans `printer.configfile.config` for `gcode_macro` sections
matching each prefix. Because the patched macro emits `section[12:]`, a section
named `[gcode_macro _PRINT_START_AMP_VALIDATE_PACKET]` is invoked as
`_PRINT_START_AMP_VALIDATE_PACKET`.

AMP hook names already used by the disabled sandbox are therefore source-aligned:

```text
_PRINT_START_AMP_VALIDATE_PACKET
_PRINT_END_AMP_CLEANUP
_CANCEL_PRINT_AMP_ABORT
```

## Fluidd/Mainsail Findings

The firmware config docs describe:

- Fluidd/Mainsail configuration access through the printer web interface.
- Firmware Config at `http://<printer-ip>/firmware-config/`.
- Firmware Config availability only after Advanced Mode is enabled on the
  touchscreen and the printer is restarted.
- Frontend selection between Fluidd and Mainsail.

The nginx source adds `fluidd.d` includes and exposes the firmware-config
frontend/API through:

```text
/etc/nginx/fluidd.d/*.conf
/firmware-config/
/firmware-config/api/
```

AMP interpretation:

- Fluidd/Mainsail is the only plausible future path for AMP adapter research.
- This does not create touchscreen-compatible mixed-nozzle support.
- Advanced Mode and service state must be verified on hardware before any
  hardware-side experiment.

## Recovery/Reset Findings

The docs and `S49extended-config` script identify these recovery paths:

- `extended-recover.txt` or `extended-recover.txt.txt` on USB resets extended
  configuration and moves the existing extended config to a backup directory.
- `full-recover.txt` or `full-recover.txt.txt` on USB removes
  `/oem/.printer_data` and `/oem/.debug`, flags extended recovery, and reboots.
- Firmware Config actions can restart Klipper, restart Moonraker, reboot, reset
  extended settings to defaults, and switch to backup firmware.

Safety implication:

- A future AMP hardware experiment cannot proceed until recovery is understood
  and confirmed by the operator.
- Recovery paths reset broad configuration state, so they are not a substitute
  for careful macro review.

## Tool/Extruder Findings

The faulty-toolhead docs and configs identify the U1 extruder section names:

| Toolhead | Klipper section |
| --- | --- |
| Toolhead 1 | `[extruder]` |
| Toolhead 2 | `[extruder1]` |
| Toolhead 3 | `[extruder2]` |
| Toolhead 4 | `[extruder3]` |

The AFC-lite config maps lanes E0-E3 to those extruders:

| Lane | Extruder |
| --- | --- |
| E0 | `extruder` |
| E1 | `extruder1` |
| E2 | `extruder2` |
| E3 | `extruder3` |

AFC-lite also exposes macros such as `CHANGE_TOOL`, `LANE_UNLOAD`,
`TOOL_UNLOAD`, `SET_MAP`, and wrappers around `AUTO_FEEDING`.

Important limitation:

- AFC-lite is documented as a compatibility/status layer for Fluidd/Mainsail
  panels and U1 extruder management, not as an AMP mixed-nozzle execution
  interface.
- This audit did not identify an official paxx12 mixed-nozzle tool assignment
  API, per-tool nozzle metadata contract, or AMP-ready toolchange scheduler.

## AMP Sandbox Mapping Table

| AMP sandbox file | Future paxx12 path | Install status | Risk level | Required preflight evidence |
| --- | --- | --- | --- | --- |
| `amp_tools.cfg.template` | `extended/klipper/amp_tools.cfg` | Future only; do not install | High | U1 hardware present, exact firmware version recorded, include path confirmed, tool/nozzle map confirmed, macro reviewed |
| `amp_macros.cfg.template` | `extended/klipper/amp_macros.cfg` | Future only; do not install | High | Hook prefixes confirmed on hardware, macro reviewed, emergency stop confirmed, dry-run plan approved |
| `amp_dry_run_schedule.gcode.txt` | No direct include path; possible future disabled review artifact only | Do not install | High | Must remain non-printing until an explicit dry-run gate exists |
| `amp_preflight_checklist.md` | Operator record outside printer config | Documentation only | Low | Filled checklist retained with validation records |
| `amp_safety_report.md` | Operator record outside printer config | Documentation only | Low | Safety review retained with validation records |
| `amp_tool_map.json` | External AMP metadata; no direct Klipper JSON include path | Documentation/metadata only | Medium | Tool map must be reviewed and converted manually if any future macro consumes it |
| Future Moonraker status config | `extended/moonraker/amp_status.cfg` only if justified | Future optional | Medium | Moonraker include path confirmed; no first-pass need identified |

## Safety-Sensitive Files

AMP should not touch these directly:

- `/home/lava/origin_printer_data/config/printer.cfg`
- `/home/lava/origin_printer_data/config/fluidd.cfg`
- `/home/lava/origin_printer_data/config/moonraker.conf`
- `/home/lava/printer_data/config/extended/extended2.cfg`
- `extended/klipper/00_keep.cfg`
- `extended/moonraker/00_keep.cfg`
- Faulty-toolhead bypass configs unless troubleshooting an actual faulty
  toolhead outside AMP scope
- AFC-lite configs unless explicitly validating ordinary U1 extruder UI status
  behavior outside AMP mixed-nozzle scope

## Recommended Integration Path

Recommended future path, still offline until hardware preflight passes:

1. Keep AMP source of truth in the offline plan packet.
2. Keep paxx12 adapter outputs comments-only or disabled templates.
3. Use `extended/klipper/amp_tools.cfg` and `extended/klipper/amp_macros.cfg`
   only as future reviewed targets.
4. Use paxx12 lifecycle hooks only for validation/cleanup placeholders:
   `_PRINT_START_AMP_VALIDATE_PACKET`, `_PRINT_END_AMP_CLEANUP`, and
   `_CANCEL_PRINT_AMP_ABORT`.
5. Avoid Moonraker config until a concrete status/API need exists.
6. Keep hardware preflight `not_ready` until U1 hardware, recovery, tool
   inventory, offsets, and dry-run evidence exist.

## What This Proves

- paxx12 remains a concrete U1 Fluidd/Klipper adapter candidate.
- The source tree provides automatic Klipper and Moonraker include paths.
- The source tree provides PRINT_START, PRINT_END, and CANCEL_PRINT hook
  prefixes usable by future AMP sandbox macros.
- AMP sandbox files have plausible future locations under
  `extended/klipper/`, if all hardware preflight gates pass.
- Recovery paths exist in docs/source and must be understood before hardware
  work.

## What This Does Not Prove

- This does not implement mixed-nozzle slicing.
- This does not flash or modify firmware.
- This does not recommend installing custom firmware.
- This does not generate production `T0` / `T1` / `T2` / `T3` commands.
- This does not generate a printable mixed-nozzle file.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
- This does not prove that paxx12 firmware supports AMP mixed-nozzle execution.

