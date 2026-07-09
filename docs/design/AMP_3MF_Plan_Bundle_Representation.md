# AMP 3MF Plan Bundle Representation

## Purpose

This design defines a conservative AMP 3MF plan-bundle path.

The goal is not to make 3MF execute mixed physical nozzle slicing. The goal is to preserve AMP plan intent in a project-review bundle while keeping the authoritative planner data in sidecar JSON.

## Representation Model

```text
AMP offline plan packet
-> separated region bodies
-> 3MF project object identities / tool-slot assignments
-> AMP sidecar JSON
-> read-only review / round-trip inspection
```

## Fields That May Map To 3MF Project/Object Metadata

| AMP field | Candidate 3MF location | Status |
| --- | --- | --- |
| region name | object name / object metadata | viable |
| region body | separate object or volume | viable |
| intended filament/tool slot | object or volume `extruder` | viable |
| line role / visibility | object metadata or sidecar | sidecar preferred |
| intended process profile name | sidecar, maybe object metadata | sidecar authoritative |
| intended nozzle diameter | sidecar, maybe object metadata | sidecar authoritative |
| intended layer height | sidecar, maybe object config if GUI supports it | not execution-proven |
| intended line-width class | sidecar, maybe object config if GUI supports it | not execution-proven |
| fallback tool | sidecar | sidecar only |
| confidence/reason | sidecar | sidecar only |
| safety/risk flags | sidecar | sidecar only |

## Sidecar JSON Responsibilities

The AMP sidecar remains authoritative for:

- exact process profile selected by the resolver
- intended nozzle/tool class
- bead-width plan
- layer-height plan
- cost-gate result
- fallback recommendation
- confidence/reason
- hardware and execution safety warnings
- validation status

This avoids confusing "stored in 3MF" with "executed by the slicer."

## What Must Wait For Slicer Integration

The following should not be treated as solved by a 3MF sidecar:

- per-object full process-profile execution
- per-object `nozzle_diameter` execution
- production `T0` / `T1` / `T2` / `T3` generation
- local per-region layer-height execution
- physical mixed-nozzle print output
- Snapmaker touchscreen-compatible mixed-nozzle execution

## Read-Only / Advisory Rules

- 3MF plan bundles are review artifacts.
- Sidecar JSON must not be consumed by production slicer paths without a separate integration design.
- Generated 3MF files, if created later, must not claim mixed-nozzle execution.
- G-code export remains a diagnostic step only until slicer integration explicitly supports the plan.
- Touchscreen mixed physical nozzle execution remains blocked.

## Official Orca 3MF Roundtrip Result

The official Orca 3MF/project roundtrip preservation probe is documented here:

```text
docs/benchmarks/AMP_Official_Orca_3MF_RoundTrip_Preservation_001.md
```

Result:

- official Orca 3MF preserves four distinct AMP region objects
- object-to-tool assignments are preserved as `extruder` metadata
- project-level nozzle vector `0.2,0.4,0.6,0.8,0.8` is preserved
- mixed probe process/printer IDs are preserved
- AMP's per-region process/profile/layer-height plan remains sidecar-authoritative

Decision:

Use official Orca 3MF as the first manual execution/review bridge, while keeping the AMP sidecar as the authority for planner intent, fallback reasoning, local-Z intent, confidence, and safety state.

## Next Probe

The next representation probe should export G-code after reopening the official Orca 3MF:

1. Reopen the saved official Orca 3MF.
2. Confirm object/tool assignments.
3. Export G-code.
4. Run the AMP G-code conformance validator.
5. Compare nozzle vector, active T commands, object comments, and process ID against the known successful GUI export.

## Non-Claims

- This does not implement mixed-nozzle slicing.
- This does not generate production tool-selection commands.
- This does not generate a verified mixed-nozzle print.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
