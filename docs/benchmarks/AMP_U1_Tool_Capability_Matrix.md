# AMP U1 Tool Capability Matrix

## Purpose

This document summarizes the U1 0.2 / 0.4 / 0.6 / 0.8 nozzle ladder from the Snapmaker Orca profile set for Adaptive Manufacturing Planner planning work.

Generated CSV:

```text
outputs/amp_tool_matrix/u1_tool_capability_matrix.csv
```

Generator:

```text
tools/amp_extract_u1_tool_capability_matrix.py
```

Generation command:

```powershell
python tools/amp_extract_u1_tool_capability_matrix.py `
  --out outputs/amp_tool_matrix/u1_tool_capability_matrix.csv
```

The generated CSV is intentionally not committed.

## Sources

- `resources/profiles/Snapmaker/machine/Snapmaker U1.json`
- `resources/profiles/Snapmaker/machine/Snapmaker U1 (0.2 nozzle).json`
- `resources/profiles/Snapmaker/machine/Snapmaker U1 (0.4 nozzle).json`
- `resources/profiles/Snapmaker/machine/Snapmaker U1 (0.6 nozzle).json`
- `resources/profiles/Snapmaker/machine/Snapmaker U1 (0.8 nozzle).json`
- `resources/profiles/Snapmaker/process/`
- `docs/U1_Adaptive_Nozzle_Profile_Inventory.md`

The U1 model profile declares nozzle diameters:

```text
0.2;0.4;0.6;0.8
```

## Matrix

| Nozzle | Available layer heights from U1 profiles | Observed line width class | Visible/detail suitability | Structural-shell suitability | Bulk suitability | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 0.2 mm | 0.06, 0.08, 0.10, 0.12, 0.14 | 0.22 | High: micro/fine visible detail | Limited: small shells and fine features | Low: too slow for bulk except tiny parts | Current U1 profiles begin at 0.06 mm for the 0.2 nozzle family. |
| 0.4 mm | 0.08, 0.12, 0.16, 0.20, 0.24, 0.25, 0.28 | 0.40, 0.42, 0.45 | High: general visible/detail | Medium: normal shell work | Medium: general-purpose fallback | General U1 detail/shell class. |
| 0.6 mm | 0.18, 0.24, 0.25, 0.30, 0.36, 0.42 | 0.62 | Medium: coarse visible detail only | High: structural shell / medium bulk | High: useful for larger internal regions | Candidate class for non-cosmetic shell and medium bulk regions. |
| 0.8 mm | 0.24, 0.32, 0.40, 0.48, 0.56 | 0.82 | Low: avoid fine visible detail | Medium: large simple shells only | High: bulk / fast internal regions | Bulk class. 0.56 mm is the largest observed U1 layer height in current profiles. |

## Fine-End Note

The long-view AMP framing may refer to a `0.05 mm` fine-detail class. Current U1 profiles found in this branch begin at `0.06 mm` for the 0.2 nozzle family. Therefore, `0.05 mm` should be treated as a conceptual fine-detail target class, not a currently observed U1 profile value.

## Planning Interpretation

AMP should treat this as a resolution ladder:

```text
0.2 nozzle -> micro/fine visible detail
0.4 nozzle -> normal visible/detail and ordinary shell
0.6 nozzle -> structural shell / medium bulk
0.8 nozzle -> hidden/internal bulk
```

This matrix does not implement tool assignment. It only records the available profile-backed tool classes that an offline planner can reason about.

## Safety Boundary

This document does not claim working mixed-nozzle output.

This document does not validate physical mixed-nozzle behavior.

This document does not bypass Snapmaker validation.

Touchscreen-compatible mixed-nozzle behavior remains blocked pending Snapmaker's future metadata/tool-mapping path. Fluidd-only mixed-nozzle validation remains future and hardware-dependent.
