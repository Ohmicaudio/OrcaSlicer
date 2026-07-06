# AMP Fluidd Klipper Hardware Preflight 001 Result

## Default Validator Result

Command:

```powershell
python tools\amp_validate_hardware_preflight.py --checklist docs\safety\AMP_Fluidd_Klipper_Hardware_Preflight_001_Checklist.json --out outputs\amp_hardware_preflight\default_preflight_result.json --markdown outputs\amp_hardware_preflight\default_preflight_result.md
```

Result:

```text
status=not_ready ready=false pending_required=21 failed_required=0 invalid=0
```

Expected status:

```text
not_ready
```

## Why It Is Not Ready

No hardware evidence has been supplied.

The default checklist intentionally keeps every required item at `pending`. This means the project cannot proceed to any Fluidd/Klipper hardware dry-run until evidence is recorded for hardware state, tool map, material compatibility, firmware path, motion safety, offsets, purge/wipe behavior, software packet validation, emergency stop access, and dry-run ladder stage.

## Required Evidence Before Status Can Change

- Physical U1 access.
- Toolhead count.
- Installed nozzle size per physical toolhead.
- Intended 0.2 / 0.4 / 0.6 / 0.8 tool map.
- Material/nozzle compatibility evidence.
- Fluidd-only path confirmation.
- Emergency stop access.
- Homing and bed-clear confirmation.
- Parking/docking coordinates.
- Tool offsets and Z offsets.
- Purge/wipe behavior observations.
- AMP packet validation result.
- Firmware adapter validation result.
- Sandbox command-safety scan.
- Step-by-step non-extruding dry-run evidence.

## Next Future Hardware Action

The next possible hardware action is not a print. It is a controlled Step 1 air/dry-run with no heating and no extrusion, and only after Step 0 offline validation and all required hardware/software checks are filled with evidence.

## Required Conclusions

- AMP has a preflight gate before any Fluidd/Klipper experiment.
- The default state is `not_ready`.
- The project cannot move to real execution without physical evidence.
- This keeps the alternative execution path controlled rather than speculative.

## Non-Claims

- This does not implement mixed-nozzle slicing.
- This does not flash or modify firmware.
- This does not generate production `T0`, `T1`, `T2`, or `T3` commands.
- This does not generate a printable mixed-nozzle file.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
