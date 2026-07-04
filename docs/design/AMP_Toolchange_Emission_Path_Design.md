# AMP Toolchange Emission Path Design

## Purpose

This document defines the future boundary between AMP advisory planning and actual toolchange/T-code emission.

The continuous resolution field prototype can now describe what each region wants:

```text
desired XY resolution
desired Z resolution
quantized U1 tool/profile class
fallback tool class
quantization error
risk flags
confidence
```

That is not enough to emit production toolchanges. Toolchange emission is a later integration stage with additional safety, scheduling, hardware, and validation requirements.

## Current Boundary

Current AMP tooling is offline and advisory.

It may:

- compute near-continuous region resolution demand
- quantize that demand to the U1 0.2 / 0.4 / 0.6 / 0.8 ladder
- name a selected process profile
- record fallback and risk flags
- write benchmark/debug planning artifacts

It must not:

- emit `T0`, `T1`, `T2`, or `T3`
- generate mixed-nozzle production G-code
- bypass Snapmaker nozzle validation
- alter production slicer behavior
- assume touchscreen-started mixed-nozzle jobs are supported

## Future Emission Pipeline

A future toolchange path should be staged like this:

```text
region metadata
-> continuous resolution field
-> U1 tool/profile quantization
-> region segmentation boundaries
-> scheduling and cost gates
-> hardware capability checks
-> validation/fallback plan
-> toolchange emission plan
-> G-code integration
```

The current branch stops before segmentation, scheduling, hardware capability checks, and G-code integration.

## Required Inputs Before Emission

Toolchange emission should require:

- a region map with stable object/layer/region identifiers
- selected tool/profile class per region
- fallback tool/profile class per region
- per-region confidence and risk flags
- explicit hardware capability metadata
- nozzle-state validation behavior for the target start path
- measured or configured toolchange and purge cost
- visible-surface and seam risk policy
- generated G-code parity tests for disabled mode

No future emission path should rely only on a region label or desired nozzle class.

## U1 Start-Path Constraints

Snapmaker support guidance currently makes the U1 start path important:

- Touchscreen-started jobs compare used toolheads against the first `nozzle_diameter` value in the G-code.
- Under that touchscreen path, all used toolheads in a job must currently be configured with the same nozzle size.
- Snapmaker Orca does not officially support mixed physical nozzle-size printing today.
- Fluidd-started jobs may be a future experimental path because they do not perform the same nozzle-size verification.

Therefore:

- Touchscreen-compatible mixed-nozzle emission remains blocked.
- Any future Fluidd-only mixed-nozzle experiment must be developer-only and hardware-validated.
- AMP must not bypass Snapmaker validation or safety behavior.

## Scheduling Requirements

The planner must eventually decide whether a toolchange is worth it.

Scheduling should consider:

- region area
- path length
- visible/detail sensitivity
- estimated toolchange cost
- purge/wipe cost
- seam placement risk
- tool availability
- fallback tool quality
- whether adjacent regions can share a tool without excessive quality loss

A toolchange should be rejected when the expected benefit is smaller than the measured or configured cost.

## Emission Safety Rules

Future T-code emission must follow these rules:

- Disabled AMP behavior must remain equivalent to stock behavior.
- No T-code should be emitted unless an explicit future developer/experimental mode enables it.
- No toolchange code should be emitted from inside parallel geometry loops.
- No writer/debug side effects should occur inside `PrintObject::make_perimeters` parallel work.
- Any per-layer or per-region accumulation must be serial before parallel work or thread-local with deterministic merge.
- Emission failures must fall back to a stock/single-tool plan rather than producing ambiguous mixed-tool output.

## Validation Strategy

Before any emission path can affect production G-code, it needs:

- unit tests for emission plan value types
- deterministic serialization tests for planned toolchange events
- disabled-mode G-code parity tests
- explicit tests showing no production path consumes AMP unless enabled
- same-input/repeated-run determinism checks
- visual preview review
- physical hardware validation for any mixed physical nozzle behavior

For U1 specifically, hardware validation must include:

- nozzle-state behavior
- toolhead/nozzle calibration assumptions
- Z-offset and toolhead offset behavior
- purge/wipe behavior
- toolchange reliability
- seam and bonding behavior
- touchscreen vs Fluidd start-path differences

## Non-Goals

This milestone does not implement:

- T-code emission
- mixed-nozzle slicing
- geometry segmentation
- scheduling
- production G-code integration
- UI controls
- Snapmaker validation changes
- physical mixed-nozzle behavior

## Cross-References

- `docs/benchmarks/AMP_Continuous_Resolution_Field_Prototype.md`
- `docs/benchmarks/AMP_Continuous_Resolution_Field_Examples.json`
- `docs/research/Snapmaker_U1_Mixed_Nozzle_Constraints.md`
- `docs/risks/AMP_Project_Risk_Register_v0.2.md`
- `docs/code_maps/AMP_ReadOnly_Integration_Map.md`
- `docs/design/AMP_PrintObject_Sidecar_Cache_Design.md`
