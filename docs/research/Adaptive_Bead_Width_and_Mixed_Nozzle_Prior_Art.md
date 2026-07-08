# Adaptive Bead-Width And Mixed-Nozzle Prior Art

**Document ID:** `docs/research/Adaptive_Bead_Width_and_Mixed_Nozzle_Prior_Art.md`

**Project:** Project Atlas / Adaptive Manufacturing Planner (AMP)

**Target ecosystem:** OrcaSlicer / Snapmaker Orca / Snapmaker U1

**Status:** Research draft

## 1. Summary

This report reviews prior art and public implementation context for two related but separate ideas:

- **Adaptive bead-width planning:** Software-controlled variation of extrusion width while using a declared physical nozzle size.
- **Physical mixed-nozzle switching:** Use of multiple physical toolheads or nozzles with different diameters in one manufacturing plan.

The important finding is that adaptive bead-width planning is already supported in modern slicer engines through Arachne-style variable-width wall generation, while automated geometry-driven assignment across physically different nozzle diameters remains a less settled workflow. This report did not identify a production-ready path that automatically partitions a single contiguous part into local regions, scores those regions, and assigns different physical nozzle diameters based on geometry, cosmetic priority, structural need, and tool-change cost.

Snapmaker's public U1 hot-end documentation confirms that U1 supports multiple hot-end nozzle diameter options, but it also states that "mixing different nozzle diameters in the same print job" is not currently supported. That makes physical mixed-nozzle behavior a hardware-validation and product-alignment question, not a safe assumption for early AMP code.

For the Adaptive Manufacturing Planner, this supports the staged plan already documented in this branch:

1. Validate experimental profile-only output using existing role-specific line-width settings and Arachne.
2. Add future AMP read-only debug artifacts before any manufacturing behavior changes.
3. Defer future AMP-influenced slicing output until equivalence and safety tests exist.
4. Block physical mixed-nozzle behavior until U1 hardware validation is available.

## 2. Taxonomy

### Adaptive Bead-Width Planning

Adaptive bead-width planning changes extrusion width in software while keeping the physical nozzle assumption explicit. Arachne-style wall generation fits this category: the slicer can vary wall width to better fit local geometry without implying that the nozzle diameter physically changes.

Relevant sources:

- Prusa documents Arachne as a perimeter generator that varies extrusion width to fit geometry: <https://help.prusa3d.com/article/arachne-perimeter-generator_352769>
- Ultimaker's `libArachne` describes adaptive-width toolpath generation for thin outline features: <https://github.com/Ultimaker/libArachne/blob/master/README.md>
- Kuipers et al. describe adaptive-width dense contour-parallel toolpaths for FDM: <https://arxiv.org/abs/2004.13497>

This category maps one declared physical nozzle size to a range of bead widths along generated extrusion lanes. It is the software-only foundation for AMP Stage 1.

### Role-Specific Extrusion Width Settings

Role-specific line-width settings are static profile parameters. They can set different widths for external perimeters, internal walls, infill, top surfaces, or support while still operating within the slicer's existing profile model.

For current AMP validation, this is the Level 1 path: experimental profile-only output. It does not prove AMP planning behavior exists. It only tests whether existing settings and Arachne provide a useful baseline.

### Physical Nozzle / Tool Switching

Physical nozzle switching refers to selecting, translating, parking, or activating a different toolhead/extruder with a different actual nozzle diameter. This is separate from adaptive bead width. It has hardware implications:

- tool selection
- nozzle state validation
- tool offsets
- purge and wipe behavior
- calibration state
- time cost
- possible material contamination

Snapmaker's U1 hot-end documentation lists 0.2 mm, 0.4 mm, 0.6 mm, and 0.8 mm nozzle diameter options: <https://wiki.snapmaker.com/en/snapmaker_u1/hot_end_guide>

### Automated Geometry-Driven Tool Assignment

Automated geometry-driven tool assignment is the future planner layer AMP is meant to explore. It would classify regions by local detail, structure, visibility, accessibility, and cost, then recommend a bead-width or tool strategy.

This report did not identify a stable, production-ready implementation of that full layer in the reviewed sources.

## 3. Slicer Capability Notes

| Capability | Current evidence | AMP interpretation |
| --- | --- | --- |
| Variable-width wall generation | Supported by Arachne-style engines. | Useful foundation for Stage 1 bead-width planning. |
| Role-specific width settings | Common slicer profile capability. | Useful for experimental profile-only validation. |
| Multi-extruder role assignment | Supported in slicers as static configuration. | Not the same as automated local region planning. |
| Mixed physical nozzle setup | Described in Orca-related documentation and issues, with workflow limits. | Needs careful validation and should not be treated as solved for U1. |
| Automated geometry-driven physical nozzle assignment | Not identified as production-ready in this review. | Core future AMP research area. |

### Desktop Slicer Capability Summary

This review treats variable-width path generation and physical mixed-nozzle assignment as separate capabilities.

| Ecosystem | Variable bead-width engine | Static multi-extruder/tool assignment | Automated local mixed-nozzle assignment |
| --- | --- | --- | --- |
| Cura / Ultimaker lineage | Arachne/libArachne evidence exists. | Supported through normal multi-extruder workflows. | Not identified in this review. |
| PrusaSlicer lineage | Arachne perimeter generation is documented. | Supported through normal multi-extruder workflows. | Not identified in this review. |
| OrcaSlicer / Snapmaker Orca lineage | Arachne-derived wall generation and role-specific widths are available. | Supported through profile/tool configuration, with UI/workflow constraints reported for some printers. | Not identified as a validated U1 workflow. |

Relevant Orca context:

- OrcaSlicer wiki page describing mixed nozzle setup by extruder: <https://www.orcaslicer.com/wiki/guides/mixed_nozzle_sizes.html>
- OrcaSlicer issue about missing nozzle-size sidebar UI for non-BBL multi-extruder printers: <https://github.com/OrcaSlicer/OrcaSlicer/issues/14144>
- OrcaSlicer issue discussing toolchanger multiple nozzle sizes in the same print: <https://github.com/OrcaSlicer/OrcaSlicer/issues/11424>
- LixNix OrcaSlicer mixed-nozzle fork audit: `docs/research/AMP_LixNix_Multi_Nozzle_Fork_Audit_001.md`
- LixNix runtime behavior probe: `docs/research/AMP_LixNix_Runtime_Behavior_Probe_001.md`
- LixNix external fork: <https://github.com/LixNix/OrcaSlicer-multi-nozzle-size-printing>

The Orca issues are project/community issue reports, not proof that any particular workflow is safe on U1 hardware.

The LixNix fork is meaningful prior art. The inspected default branch adds mixed-nozzle plumbing around mapped filament/extruder nozzle-diameter lookup, while the `multi_nozzle_multi_layer_height` branch adds per-extruder layer-height configuration, combined-layer behavior, support nozzle restrictions, wipe tower adjustments, and fff_print tests. A local runtime probe built the branch with external-probe-only dependency/linker workarounds and exported G-code showing mixed width/layer behavior under scratch mixed-extruder configurations. The tested CLI paths did not emit observable `T0` / `T1` / `T2` / `T3` tool-change commands, so true mixed-nozzle tool-change output remains unconfirmed. It still appears to be manual/per-feature or per-extruder infrastructure rather than a production-level validated automated geometry-driven planner. It has not been physically validated by this project and does not replace U1-specific validation.

## 4. Academic Prior Art

Kuipers, Doubrovski, Wu, and Wang's paper, "A framework for adaptive width control of dense contour-parallel toolpaths in fused deposition modeling," is directly relevant to Stage 1 software planning. The paper discusses adaptive-width toolpaths for dense contour-parallel filling and highlights the physical challenge of realizing width changes accurately on FDM systems.

Stable references:

- arXiv: <https://arxiv.org/abs/2004.13497>
- DOI: <https://doi.org/10.1016/j.cad.2020.102907>
- TU Delft research record: <https://research.tudelft.nl/en/publications/a-framework-for-adaptive-width-control-of-dense-contour-parallel-/>

AMP implication:

- Adaptive bead widths should start conservative.
- Continuous bead-width changes are a toolpath and process-control problem, not only a geometric offset problem.
- Any future behavior-changing width plan needs regression geometry and physical print validation.
- Preview/G-code inspection can validate path differences, but not real strength, surface quality, dimensional accuracy, or bonding.

## 5. Snapmaker U1 Context

Snapmaker U1 is relevant because it has multiple toolheads and official hot-end options across several nozzle diameters. Public Snapmaker documentation confirms 0.2 mm, 0.4 mm, 0.6 mm, and 0.8 mm hot-end options, but it also states that mixed nozzle diameters in the same print job are not currently supported. The same guide documents nozzle diameter synchronization and printer-side mismatch handling.

Official reference:

- Snapmaker U1 hot-end guide: <https://wiki.snapmaker.com/en/snapmaker_u1/hot_end_guide>

Community reports and forum discussions indicate user interest in mixed nozzle sizes on U1/toolchanger workflows, but these should be treated as community reports rather than authoritative documentation:

- Snapmaker forum discussion, "Multiple nozzle sizes in the same print?": <https://forum.snapmaker.com/t/multiple-nozzle-sizes-in-the-same-print/42200>
- Reddit community report, "Tool Changer multiple nozzle sizes in same print": <https://www.reddit.com/r/snapmaker/comments/1p28jgq/tool_changer_multiple_nozzle_sizes_in_same_print/>

AMP implication:

- Stage 2 physical mixed-nozzle behavior remains blocked until U1 hardware validation.
- Do not bypass nozzle mismatch checks or Snapmaker validation paths.
- Do not claim mixed physical nozzle behavior works before real U1 prints.
- Do not generate physical mixed-nozzle commands until toolchange overhead, validation behavior, and purge/wipe implications are measured or documented for U1.

## 6. Solved, Partially Solved, And Open Areas

### Lower-Risk / No Behavior Change While Disabled

The current AMP branch already follows a lower-risk path:

- Hidden config flag exists but is not consumed.
- Stock fallback value types exist.
- No-op planner facade exists.
- No production slicing path calls AMP.

This means current code is scaffolding, not manufacturing behavior.

### Solved Or Mature Enough To Build On

- Arachne-style variable-width wall generation.
- Role-specific line-width settings for profile-only comparison.
- Static extruder/tool assignment workflows.

### Partially Solved

- Mixed physical nozzle setup in slicer profiles.
- UI/workflow support for multi-extruder nozzle sizes.
- Wipe/purge cost estimation for mixed tools.
- Open-source experimental per-extruder mixed-nozzle and per-extruder layer-height slicing paths, as seen in the LixNix fork audit, but not production-level validated for AMP or U1.

### Open Research Areas For AMP

- Region classification for detail, structure, cosmetic visibility, accessibility, and tool-change cost.
- Deterministic read-only debug artifacts.
- Safe conversion from advisory region maps into future behavior-changing bead-width plans.
- U1 physical validation for mixed nozzles, purge/wipe behavior, nozzle state validation, and print quality.

### Core Gap For AMP

The reviewed sources cover parts of the problem:

- Arachne-style engines handle local bead-width adaptation.
- Existing slicer profiles handle role-specific widths and static extruder/tool assignments.
- U1 hardware documentation covers nozzle options, calibration, and synchronization requirements.

The gap AMP targets is the orchestration layer between geometry analysis and manufacturing strategy: a planner that can evaluate local feature size, curvature density, structural/cosmetic importance, tool accessibility, and tool-change cost before recommending either software bead-width changes or future physical tool choices.

## 7. Roadmap Alignment

```text
Research
  -> experimental profile-only output
  -> future AMP read-only debug artifact
  -> future AMP-influenced slicing output
  -> U1 physical mixed-nozzle validation
```

Stage 1 should remain software-only until the read-only planner boundary is stable. Stage 2 should remain hardware-blocked until U1 validation is available.

## 8. References

- Prusa Research, "Arachne perimeter generator": <https://help.prusa3d.com/article/arachne-perimeter-generator_352769>
- Ultimaker, `libArachne` README: <https://github.com/Ultimaker/libArachne/blob/master/README.md>
- Kuipers, T.; Doubrovski, E. L.; Wu, J.; Wang, C. C. L., "A framework for adaptive width control of dense contour-parallel toolpaths in fused deposition modeling": <https://arxiv.org/abs/2004.13497>
- Kuipers, T.; Doubrovski, E. L.; Wu, J.; Wang, C. C. L., DOI record for "A framework for adaptive width control of dense contour-parallel toolpaths in fused deposition modeling": <https://doi.org/10.1016/j.cad.2020.102907>
- TU Delft research record for the Kuipers et al. paper: <https://research.tudelft.nl/en/publications/a-framework-for-adaptive-width-control-of-dense-contour-parallel-/>
- OrcaSlicer wiki, "Mixed Nozzle Sizes": <https://www.orcaslicer.com/wiki/guides/mixed_nozzle_sizes.html>
- OrcaSlicer issue #14144, "No nozzle size selector in the sidebar for non-BBL multi-extruder printers": <https://github.com/OrcaSlicer/OrcaSlicer/issues/14144>
- OrcaSlicer issue #11424, "Tool Changer multiple nozzle sizes in same print": <https://github.com/OrcaSlicer/OrcaSlicer/issues/11424>
- LixNix OrcaSlicer multi-nozzle fork: <https://github.com/LixNix/OrcaSlicer-multi-nozzle-size-printing>
- Snapmaker U1 hot-end guide: <https://wiki.snapmaker.com/en/snapmaker_u1/hot_end_guide>
- Snapmaker forum community discussion, "Multiple nozzle sizes in the same print?": <https://forum.snapmaker.com/t/multiple-nozzle-sizes-in-the-same-print/42200>
- Reddit community report, "Tool Changer multiple nozzle sizes in same print": <https://www.reddit.com/r/snapmaker/comments/1p28jgq/tool_changer_multiple_nozzle_sizes_in_same_print/>
