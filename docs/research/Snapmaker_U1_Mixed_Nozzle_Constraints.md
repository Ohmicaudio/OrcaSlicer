# Snapmaker U1 Mixed-Nozzle Constraints

## Source

- Source: Snapmaker support response from Leonard.
- Date received: June 30, 2026.
- Use: Summarized for Adaptive Manufacturing Planner project planning.

This document is a public-safe technical summary. It is not a verbatim copy of private support correspondence.

## Key Findings

- Touchscreen-started prints compare every used toolhead's configured nozzle size against the first `nozzle_diameter` value in the G-code.
- Touchscreen-started mixed physical nozzle jobs are not officially supported today.
- The current touchscreen-start path requires all used toolheads in one G-code file to be configured with the same nozzle size.
- Fluidd-started prints do not perform nozzle-size verification, so mixed physical nozzle-size printing may be possible through that path.
- No nozzle-size-specific calibration system exists; user configuration is authoritative.
- Toolhead offsets and Z offset are not related to nozzle size.
- Snapmaker has not observed significant wiping or tool-swap stability differences between nozzle sizes.
- Filament loading and unloading parameters vary by nozzle size and are mostly handled by firmware.
- Avoid a 0.2 mm nozzle with PETG-CF, PETG-GF, Wood, or TPU because of clog risk.

## Impact On AMP

Stage 2 should be split into two clearly separated validation paths:

- Stage 2A: Fluidd-only experimental validation path.
- Stage 2B: Touchscreen-compatible path blocked until Snapmaker finalizes logical-to-physical tool mapping support.

Current AMP constraints:

- Do not implement touchscreen mixed physical nozzle output yet.
- Do not disable or circumvent Snapmaker validation paths.
- Any future Fluidd mixed physical nozzle experiment must be developer-only and clearly labeled.
- Any future Fluidd experiment still requires U1 hardware access, real print validation, and explicit risk documentation.
- Stage 1 profile-only and adaptive bead-width work remains separate from physical mixed-nozzle validation.

## Open Questions

- Will future U1 G-code or job metadata support per-tool nozzle diameter declarations?
- Will future firmware or slicer state store nozzle diameter per physical toolhead?
- Which subsystem owns Fluidd load/unload nozzle-size behavior?
- What slicer-side contribution path would Snapmaker prefer for future logical-to-physical toolhead mapping?
- What minimal validation models would Snapmaker consider useful before any future Stage 2 behavior affects toolpaths?

## Project Position

AMP remains a staged FDM/FFF resolution-allocation planning project. Snapmaker U1 is the first submitted validation platform, not the only possible hardware tier.

For U1 specifically, physical mixed-nozzle behavior remains blocked for touchscreen-compatible workflows. Fluidd-only experimentation may be technically possible later, but it must remain developer-only until U1 hardware behavior, calibration assumptions, loading/unloading behavior, purge/wipe behavior, and bonding behavior are validated.
