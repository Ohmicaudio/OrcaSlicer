# AMP Milestone 001: Offline Multi-Tool Resolution Planner Contract

## Summary

Milestone 001 establishes a behavior-neutral offline planner chain for Adaptive Manufacturing Planner (AMP). The current chain is advisory only and does not alter production slicing, G-code, profiles, or Snapmaker validation behavior.

The chain now covers:

- region metadata
- continuous resolution field
- 3D and line-type-aware tool assignment
- cost gating
- U1 process-profile resolution
- toolchange scheduling
- offline plan packet
- packet validator
- debug artifact JSON
- C++ golden contract
- C++ packet sidecar lookup

This milestone turns AMP from isolated planning experiments into a reproducible offline contract between Python planning tools and C++ value types.

## What Works

- U1 tool ladder extracted: 0.2 / 0.4 / 0.6 / 0.8.
- Multi-tool resolution fixture generated.
- Per-region bodies sliced with assigned U1 profiles.
- Offline plan packet generated.
- Packet validator passes.
- Debug artifact contract check passes.
- C++ focused AMP tests pass.
- Golden JSON round-trip contract exists.
- Packet sidecar adapter exists.
- Snapmaker CLI hardening PRs opened:
  - [#560](https://github.com/Snapmaker/OrcaSlicer/pull/560)
  - [#561](https://github.com/Snapmaker/OrcaSlicer/pull/561)
  - [#562](https://github.com/Snapmaker/OrcaSlicer/pull/562)

## Current Verified Test Result

Focused AMP test baseline:

```text
2149 assertions in 38 test cases
```

## Key Outputs

- `tools/amp_continuous_resolution_field.py`
- `tools/amp_tool_class_assignment_solver.py`
- `tools/amp_u1_process_profile_resolver.py`
- `tools/amp_toolchange_scheduler.py`
- `tools/amp_generate_plan_packet.py`
- `tools/amp_validate_plan_packet.py`
- `tools/amp_export_pseudo_toolchange_schedule.py`
- `tools/amp_debug_artifact_contract_check.py`
- `tests/libslic3r/data/amp_debug_artifact_offline_plan_packet_golden.json`
- `AdaptiveManufacturingDebugArtifact*`
- `AdaptiveManufacturingPacketSidecar*`

## Reproduction Commands

Generate the offline packet:

```powershell
python tools\amp_generate_plan_packet.py --input docs\benchmarks\AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json --out outputs\amp_plan_packet_001 --schedule-mode minimize_toolchanges
```

Validate the packet:

```powershell
python tools\amp_validate_plan_packet.py --packet outputs\amp_plan_packet_001 --out outputs\amp_plan_packet_001\validation_report.json --markdown outputs\amp_plan_packet_001\validation_report.md
```

Export the comments-only pseudo schedule:

```powershell
python tools\amp_export_pseudo_toolchange_schedule.py --packet outputs\amp_plan_packet_001 --out outputs\amp_plan_packet_001\pseudo_toolchange_schedule.md
```

Run the debug artifact contract check:

```powershell
python tools\amp_debug_artifact_contract_check.py outputs\amp_plan_packet_001\debug_artifact.json --golden tests\libslic3r\data\amp_debug_artifact_offline_plan_packet_golden.json
```

Run the focused AMP tests:

```powershell
build-tests\tests\libslic3r\Release\libslic3r_tests.exe "[AdaptiveManufacturingDebugArtifactSerializer],[AdaptiveManufacturingPacketSidecar]"
```

## What This Proves

- AMP can produce a deterministic offline advisory packet for the U1 0.2 / 0.4 / 0.6 / 0.8 tool ladder.
- Offline planner output can be validated before any slicer integration point consumes it.
- The packet-shaped debug artifact can be checked against a golden JSON fixture.
- C++ value types can round-trip the packet-shaped debug artifact without changing slicer behavior.
- C++ packet sidecar lookup can be populated from packet-shaped debug entries.
- The project has a concrete contract for future read-only ingestion work.

## What This Does Not Prove

- No mixed-nozzle slicing implementation exists.
- No production `T0` / `T1` / `T2` / `T3` output exists.
- No single mixed-nozzle G-code print has been generated.
- No physical mixed-nozzle validation has been performed.
- No touchscreen-compatible mixed-nozzle execution has been validated.
- No Snapmaker validation bypass exists.

## Known Blockers

- Snapmaker touchscreen-started jobs currently use the first `nozzle_diameter` value as a single authoritative validation value.
- Mixed-nozzle touchscreen support is blocked pending future per-tool metadata and logical-to-physical tool mapping support.
- Fluidd-only experimentation is future work and depends on hardware access and explicit developer-only controls.
- Same-plate assemble-list slicing does not currently preserve four distinct process/nozzle classes for the AMP tool ladder.
- Physical U1 validation is still needed before any Stage 2 mixed physical nozzle claims.

## Next Technical Steps

- Watch Snapmaker PRs #560, #561, and #562.
- Add a packet-sidecar fixture loader test if the next C++ ingestion step needs a broader fixture.
- Design a read-only C++ packet-sidecar loader without wiring it into `PrintObject`.
- Begin 3MF representation investigation for multi-body/process preservation.
- Later, design a read-only observation hook.
- Much later, consider Fluidd-only experimental toolchange emission after hardware validation and explicit developer controls.

## Non-Claims And Safety

- This milestone is behavior-neutral.
- No production slicer path consumes AMP.
- No G-code behavior changes are introduced by AMP.
- No Snapmaker validation or printer safety path is changed.
- No physical mixed-nozzle behavior is claimed.
