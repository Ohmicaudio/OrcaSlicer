# AMP Fluidd Klipper Hardware Preflight 001

## Purpose

This preflight defines the conditions required before any future Fluidd/Klipper AMP dry-run is attempted.

The goal is to keep the alternative execution path controlled:

- Snapmaker touchscreen mixed physical nozzle execution remains blocked.
- Fluidd/Klipper remains future experimental only.
- No hardware action is allowed without physical evidence.
- The sandbox remains non-printing until every required check is passed.

## Required Hardware State

Before any Fluidd/Klipper AMP dry-run, the operator must have:

- physical U1 access
- confirmed physical toolhead count
- confirmed installed nozzle size per physical toolhead
- intended tool map covering:
  - 0.2 mm
  - 0.4 mm
  - 0.6 mm
  - 0.8 mm
- material compatibility confirmed per nozzle
- 0.2 mm nozzle restrictions understood

Avoid 0.2 mm nozzles with PETG-CF, PETG-GF, Wood, or TPU unless separately validated.

## Required Printer-State Checks

- Confirm Fluidd path only.
- Confirm no touchscreen-started mixed-nozzle job.
- Confirm emergency stop access.
- Confirm homing behavior.
- Confirm bed is clear.
- Confirm parking/docking coordinates.
- Confirm no real print is loaded from sandbox files.

## Required Tool Calibration Checks

- Physical nozzle installed and configured per tool.
- Tool offsets known.
- Z offsets checked.
- No assumption that nozzle-size calibration exists.
- Load/unload behavior understood.
- Purge/wipe behavior observed.

## Required Software Checks

- AMP plan packet validator passes.
- Firmware adapter validator passes.
- Generated sandbox files are comments-only or dry-run only.
- No uncommented `T0` / `T1` / `T2` / `T3` commands.
- No uncommented `G0` / `G1` motion commands.
- No heating commands.
- No extrusion commands.
- No real macro execution unless explicitly reviewed later.

## paxx12 U1 Extended Firmware Research Checks

The `paxx12_u1_extended_firmware` adapter is a concrete Fluidd/Klipper research target only. It is not installed, flashed, or recommended by AMP.

Before any future hardware experiment can be considered:

- confirm whether custom firmware is actually present on the test machine
- record the firmware source and version
- confirm the recovery method before any configuration work
- confirm the `extended/klipper` include path on hardware
- review every macro before any installation attempt
- do not install generated sandbox files without human review
- keep the paxx12 adapter `research_only` until hardware evidence exists

Invalid Klipper or Moonraker configuration can prevent services from starting. Recovery must be understood before moving beyond offline artifacts.

## First Dry-Run Ladder

| Step | Gate | Required result |
| ---: | --- | --- |
| 0 | Offline validation only | Validators pass; hardware state remains untouched. |
| 1 | Air/dry-run with no heating and no extrusion | No unexpected motion, heating, extrusion, or active-tool mismatch. |
| 2 | Single-tool dry-run only | One selected tool can be identified and validated without extrusion. |
| 3 | Two-tool dry-run with no extrusion | Tool identity, offset, park, and restore behavior are understood. |
| 4 | Single material / same nozzle size toolchange test | Toolchange mechanics are observed without mixed physical nozzle claims. |
| 5 | Fluidd-only mixed-nozzle test | Only after prior gates pass with hardware evidence. |

## Stop Conditions

Stop immediately if any of these occur:

- unexpected motion
- unexpected heating
- unexpected extrusion
- wrong active tool
- wrong offset
- purge/wipe instability
- any coordinate outside safe bounds
- any mismatch between AMP packet and physical tool state

## Required Evidence

The preflight gate requires explicit evidence before any status can change from `not_ready` to `ready`:

- filled checklist with every required item passed
- U1 hardware/toolhead inventory
- firmware source/version and recovery method if using a custom firmware research target
- installed nozzle/tool map
- offset evidence
- Fluidd-only path confirmation
- non-extruding dry-run evidence
- emergency stop confirmation
- material/nozzle compatibility evidence

## Non-Claims

- No physical mixed-nozzle validation has been performed.
- No touchscreen support exists for AMP mixed physical nozzle execution.
- No Snapmaker validation bypass exists.
- No production print is authorized by this document.
