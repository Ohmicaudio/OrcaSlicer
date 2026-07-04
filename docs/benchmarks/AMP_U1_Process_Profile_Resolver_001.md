# AMP U1 Process Profile Resolver 001

## Purpose

This report records the first offline AMP resolver that maps:

```text
region metadata
-> tool-class assignment
-> concrete Snapmaker U1 process profile
-> advisory slice queue
```

This connects the 3D/line-type-aware solver to real U1 profile files instead of leaving the output at abstract nozzle classes.

## U1 Process-Profile Ladder

The resolver uses only process profiles present in the Snapmaker U1 profile set.

| Tool class | Supported process layer heights | Width class |
| --- | --- | --- |
| 0.2 | 0.06, 0.08, 0.10, 0.12, 0.14 | 0.22 |
| 0.4 | 0.08, 0.12, 0.16, 0.20, 0.24, 0.28 | 0.42-0.45 |
| 0.6 | 0.18, 0.24, 0.30, 0.36, 0.42 | 0.62 |
| 0.8 | 0.24, 0.32, 0.40, 0.48, 0.56 | 0.82 |

Unsupported layer heights are not invented. If a requested height is unavailable, the resolver chooses the nearest safer/lower supported profile and records the reason.

## Resolver Rules

| Tool class / role | Rule |
| --- | --- |
| 0.2 micro detail | High/micro Z criticality prefers 0.06 or 0.08. Normal fine detail may use 0.10 or 0.12. Low Z criticality may use 0.14. Material risks remain warnings from the assignment solver. |
| 0.4 visible detail | Default is 0.20. Top/cosmetic surfaces stay within 0.12-0.20. Low-risk general shell may use 0.24-0.28. |
| 0.6 structural shell | Default is 0.24 or 0.30. 0.36/0.42 are only for non-visible, low-Z-risk shell candidates. Visible or sloped 0.6 candidates are flagged for review. |
| 0.8 bulk | Default is 0.32 or 0.40. 0.48/0.56 are only for hidden/internal bulk with low Z criticality. 0.8 is rejected for top/cosmetic/painted/support-interface/bridge roles. |
| Local-Z | Local-Z candidates are flagged, but local-Z is not implemented. The resolver selects the safest available global process profile for now. |

## Fixture Region Process-Profile Queue

Generated command:

```powershell
python tools/amp_u1_process_profile_resolver.py `
  --input docs/benchmarks/AMP_MultiTool_Resolution_Fixture_001_Region_Metadata.json `
  --out outputs/amp_process_profile_resolver/multitool_fixture_process_queue.json
```

Generated ignored outputs:

```text
outputs/amp_process_profile_resolver/multitool_fixture_process_queue.json
outputs/amp_process_profile_resolver/multitool_fixture_process_queue.csv
outputs/amp_process_profile_resolver/multitool_fixture_process_queue.md
```

| Region | Tool | Selected U1 process profile | Layer | Width class | Local-Z future flag | Fallback process |
| --- | --- | --- | ---: | --- | --- | --- |
| `micro_detail_zone` | 0.2 | `resources/profiles/Snapmaker/process/0.06 Standard @Snapmaker U1 (0.2 nozzle).json` | 0.06 | 0.22 | true | `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json` |
| `normal_visible_detail_zone` | 0.4 | `resources/profiles/Snapmaker/process/0.16 Optimal @Snapmaker U1 (0.4 nozzle).json` | 0.16 | 0.42-0.45 | false | `resources/profiles/Snapmaker/process/0.08 Standard @Snapmaker U1 (0.2 nozzle).json` |
| `structural_shell_zone` | 0.6 | `resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json` | 0.24 | 0.62 | false | `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json` |
| `bulk_zone` | 0.8 | `resources/profiles/Snapmaker/process/0.40 Standard @Snapmaker U1 (0.8 nozzle).json` | 0.40 | 0.82 | false | `resources/profiles/Snapmaker/process/0.24 Standard @Snapmaker U1 (0.6 nozzle).json` |

## Fallback Behavior

Fallback profiles follow the assignment solver's fallback tool class:

- 0.2 detail fallback resolves to a conservative 0.4 process profile.
- 0.4 visible-detail escalation fallback may resolve to a 0.2 process profile, but it is not the default.
- 0.6 structural fallback resolves to 0.4.
- 0.8 bulk fallback resolves to 0.6.

Fallbacks are advisory. They do not change slicer behavior.

## Local-Z Flag Behavior

The resolver preserves local-Z advisory flags from the solver:

```text
local_z_candidate
local_z_future_required
```

For `micro_detail_zone`, the resolver selected the 0.06 mm 0.2 process profile and retained `local_z_future_required`. This means the current offline plan recognizes shallow/fine Z detail, but does not implement local-Z or local sublayer behavior.

## What This Proves

- AMP can now map region metadata to a tool class and a concrete U1 process profile.
- 0.2 fine regions map to actual 0.06-0.14 U1 profile families.
- 0.4 visible regions map to actual 0.08-0.28 U1 profile families.
- 0.6 structural regions map to actual 0.18-0.42 U1 profile families.
- 0.8 bulk regions map to actual 0.24-0.56 U1 profile families.
- The offline slice queue now includes selected process profile, selected layer height, width class, fallback process profile, and local-Z flags.

## What This Does Not Prove

This is offline/advisory only.

This does not implement mixed-nozzle slicing.

This does not generate a single mixed-nozzle G-code file.

This does not validate physical mixed-nozzle behavior.

This does not bypass Snapmaker touchscreen nozzle validation.

Touchscreen-compatible mixed-nozzle execution remains blocked pending Snapmaker's future per-tool metadata/logical mapping path.

Fluidd-only experimentation remains future and hardware-dependent.

This does not implement local-Z.
