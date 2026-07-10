# AMP Milestone 002: Offline Planner and Official Orca Mixed-Nozzle Workflow Bridge

## Summary

AMP now generates an offline advisory plan for Snapmaker U1 `0.2 / 0.4 / 0.6 / 0.8` region assignments and bridges that plan to the official Orca GUI mixed-nozzle workflow.

The clean architecture split is:

| System | Role |
| --- | --- |
| Official Orca GUI | Manual/static mixed-nozzle setup, 3MF preservation, and G-code export. |
| AMP | Automatic planning, sidecar authority, validation, fallback reasoning, and safety gating. |

This milestone is a planning and workflow bridge. It does not make AMP a production mixed-nozzle slicer.

## What Works

- Continuous resolution field.
- 3D and line-type-aware tool assignment.
- Cost gating.
- U1 process-profile resolver.
- Toolchange scheduler.
- Offline plan packet.
- Debug artifact JSON.
- C++ golden contract and packet sidecar lookup.
- 3MF sidecar bundle.
- Official Orca GUI workflow manifest.
- Official Orca exported mixed-nozzle G-code validation.
- Official Orca 3MF round-trip preservation.
- Fluidd/Klipper/paxx12 non-printable execution bundle.
- Hardware preflight gate.

## Official Orca Baseline Evidence

The repaired four-object official Orca GUI baseline preserved this AMP-adjacent region-to-tool mapping:

| Region object | Orca tool slot | G-code tool command | Nozzle class |
| --- | ---: | --- | ---: |
| `micro_detail_zone.stl` | 1 | `T0` | `0.2` |
| `normal_visible_detail_zone.stl` | 2 | `T1` | `0.4` |
| `structural_shell_zone.stl` | 3 | `T2` | `0.6` |
| `bulk_zone.stl` | 4 | `T3` | `0.8` |

Observed G-code header:

```text
; nozzle_diameter = 0.2,0.4,0.6,0.8,0.8
```

Observed active tools:

```text
T0, T1, T2, T3
```

Observed tool command count:

```text
80
```

The extra fifth `0.8` value is an unused preset/tool slot from the local official Orca toolchanger probe. It is not an AMP fifth region and does not indicate an additional active tool.

The official Orca 3MF round-trip also preserved:

- the four region objects
- object-to-extruder assignments
- the project-level nozzle vector
- the mixed probe process/printer identifiers

## What AMP Adds Over Manual Orca

Official Orca provides a manual/static workflow. AMP adds the advisory layer around it:

- automatic region/tool/profile planning
- fallback reasoning
- cost gates
- sidecar authority
- debug artifact contract
- conformance validation
- hardware preflight gating

AMP's current sidecar/debug packet carries planning intent that exported G-code and native Orca 3MF do not fully represent, including confidence, fallback tools, cost-gate reasons, local-Z advisory status, and hardware/preflight warnings.

## What This Does Not Prove

- No AMP-driven mixed-nozzle slicing exists yet.
- No automated Orca GUI control exists.
- No physical U1 validation has been completed.
- No touchscreen-compatible mixed-nozzle claim is made.
- No Snapmaker validation path is bypassed.
- No custom firmware install recommendation is made.
- Hardware preflight remains `not_ready`.
- Independent per-tool or per-region layer height remains unresolved in this official Orca baseline.

## Known Blockers

- Official Orca GUI setup is manual.
- Independent per-tool layer height remains unresolved.
- Snapmaker touchscreen path remains blocked for mixed physical nozzle execution.
- Physical U1 validation is still required.
- Local LixNix runtime probing did not observe `T0/T1/T2/T3` mixed-tool G-code evidence.
- The paxx12 path remains future experimental work only.

## Next Practical Steps

- Use the official Orca setup guide generated from the AMP manifest.
- Validate future exported G-code against the AMP packet.
- Watch Snapmaker CLI hardening PRs and keep them separate from AMP behavior.
- Complete U1 hardware preflight only when hardware evidence exists.
- Do not move to production mixed-nozzle emission yet.

## References

- `docs/benchmarks/AMP_Official_Orca_GUI_Mixed_Nozzle_vs_AMP_Plan_001.md`
- `docs/benchmarks/AMP_Official_Orca_Workflow_Bridge_001.md`
- `docs/benchmarks/AMP_Orca_Official_Mixed_Nozzle_Baseline_001_Results.md`
- `docs/benchmarks/AMP_3MF_Sidecar_Plan_Bundle_001.md`
- `docs/benchmarks/AMP_Offline_Plan_Packet_001.md`
- `docs/benchmarks/AMP_U1_Process_Profile_Resolver_001.md`
- `docs/safety/AMP_Fluidd_Klipper_Hardware_Preflight_001_Result.md`
- `docs/research/AMP_LixNix_Runtime_Behavior_Probe_001.md`
- `docs/research/AMP_U1_Extended_Firmware_Source_Audit_001.md`
