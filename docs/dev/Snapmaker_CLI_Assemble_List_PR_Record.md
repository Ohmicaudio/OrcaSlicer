# Snapmaker CLI Assemble-List PR Record

## PR

- Title: Fix CLI assemble-list crash during plate loading
- URL: https://github.com/Snapmaker/OrcaSlicer/pull/560
- Target: `Snapmaker/OrcaSlicer` `main`
- Source branch: `Ohmicaudio/OrcaSlicer` `fix/cli-assemble-list-plate-loading`
- Clean branch URL: https://github.com/Ohmicaudio/OrcaSlicer/tree/fix/cli-assemble-list-plate-loading
- Clean fix commit: `6fbafd5b7 fix: harden CLI assemble-list plate loading`

## Changed Files

- `src/Snapmaker_Orca.cpp`
- `src/slic3r/GUI/PartPlate.cpp`
- `src/slic3r/GUI/PartPlate.hpp`

## Validation Summary

- `Snapmaker_Orca` target built successfully locally.
- Single-object assemble-list CLI control exited `0` and exported G-code.
- Two-object same-plate assemble-list CLI control exited `0` and exported G-code.

## AMP Relationship

This PR is independent from AMP. It contains only the Snapmaker Orca CLI assemble-list fix and does not include AMP planner code, benchmark docs, submission docs, profile changes, generated output, or local build artifacts.

The fix enables future benchmark automation by making CLI assemble-list loading usable without requiring manual GUI slicing. It is not required for AMP behavior and does not change AMP planning logic.
