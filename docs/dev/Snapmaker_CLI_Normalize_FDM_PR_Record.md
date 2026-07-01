# Snapmaker CLI Normalize FDM PR Record

## Pull Request

- PR title as opened: `fix: guard CLI FDM normalization without nozzle diameter`
- PR URL: https://github.com/Snapmaker/OrcaSlicer/pull/561
- Clean branch URL: https://github.com/Ohmicaudio/OrcaSlicer/tree/fix/cli-normalize-fdm-missing-nozzle-diameter
- Clean fix commit: `7d7ad89a3 fix: guard CLI FDM normalization without nozzle diameter`
- Changed file: `src/libslic3r/PrintConfig.cpp`
- Date recorded: July 1, 2026

## Root Cause Summary

Snapmaker Orca CLI loads each `--load-settings` file and calls `DynamicPrintConfig::normalize_fdm()` before the machine, process, and filament configs are fully merged.

The exact stock U1 process profile:

`resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`

contains `wipe_tower_filament`, but the process-only profile does not contain `nozzle_diameter`. `normalize_fdm()` dereferenced `nozzle_diameter` while validating `wipe_tower_filament`, causing a `0xC0000005` access violation when the partial process config was normalized.

## Fix Summary

`normalize_fdm()` now validates `wipe_tower_filament` against `nozzle_diameter` only when `nozzle_diameter` is present in the current config.

This keeps partial process-profile normalization from crashing while preserving validation when a complete config includes nozzle diameter data.

## Validation Summary

Local validation before the fix:

- Exact stock U1 process profile crashed with `0xC0000005` in `DynamicPrintConfig::normalize_fdm`.

Local validation after the fix:

- `Snapmaker_Orca` target built successfully.
- Exact stock U1 process profile exited `0` and exported G-code.
- CLI-safe stock copy control exited `0` and exported G-code.

The successful build used CMake `3.31.8` copied under `B:\ohmic\tools` and temporary build files directed to `B:\ohmic\tmp` to reduce pressure on the nearly full `C:` drive.

## AMP Relationship

This PR is independent from AMP. It contains only the Snapmaker Orca CLI normalization fix and does not include AMP planner code, benchmark docs, submission docs, profile changes, generated output, or local build artifacts.

The fix helps future AMP benchmark automation because the exact stock U1 process profile can be loaded by the CLI without requiring a temporary CLI-safe copy.
