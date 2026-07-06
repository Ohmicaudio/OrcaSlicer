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

## Next Probe

The next representation probe should be a manual or slicer-supported GUI round trip:

1. Import the four AMP region bodies as separate objects.
2. Assign object names matching AMP regions.
3. Assign tool/material slots if the GUI supports it.
4. Apply only GUI-supported object overrides.
5. Save 3MF.
6. Reopen 3MF.
7. Inspect object identity and assignments.
8. Export G-code only to diagnose whether the representation collapses or survives.

## Non-Claims

- This does not implement mixed-nozzle slicing.
- This does not generate production tool-selection commands.
- This does not generate a verified mixed-nozzle print.
- This does not validate physical mixed-nozzle behavior.
- This does not bypass Snapmaker touchscreen nozzle validation.
