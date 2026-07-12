# AMP Orca 3MF Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and validate an Orca-loadable 3MF whose object/tool assignments and nozzle vector are derived from an AMP plan packet.

**Architecture:** Patch a compatible Orca-generated 3MF template with structured XML/JSON transforms, embed the AMP packet under `Metadata/AMP/`, and write atomically. Keep validation independent so a malformed or incomplete handoff cannot be reported as usable.

**Tech Stack:** Python 3 standard library (`argparse`, `hashlib`, `json`, `pathlib`, `tempfile`, `zipfile`, `xml.etree.ElementTree`, `unittest`).

---

### Task 1: Successful Handoff Contract

**Files:**
- Create: `tests/tools/__init__.py`
- Create: `tests/tools/test_amp_generate_orca_3mf_handoff.py`
- Create: `tools/amp_orca_3mf_handoff.py`

- [ ] **Step 1: Write the failing successful-mapping test**

Create a synthetic packet containing four `process_queue` entries and a synthetic Orca ZIP containing `Metadata/model_settings.config`, `Metadata/project_settings.config`, and an unchanged mesh member. Assert that `generate_handoff()`:

```python
result = generate_handoff(template, packet_dir, output)
self.assertEqual(result["region_count"], 4)
self.assertEqual(result["nozzle_diameters"], ["0.2", "0.4", "0.6", "0.8"])
self.assertEqual(read_object_extruders(output), {
    "micro_detail_zone": "1",
    "normal_visible_detail_zone": "2",
    "structural_shell_zone": "3",
    "bulk_zone": "4",
})
self.assertEqual(read_project_nozzles(output)[:4], ["0.2", "0.4", "0.6", "0.8"])
self.assertEqual(read_member(output, "3D/Objects/body.model"), b"unchanged mesh")
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```text
python -m unittest tests.tools.test_amp_generate_orca_3mf_handoff.AmpOrca3mfHandoffTests.test_maps_regions_and_preserves_mesh -v
```

Expected: import failure because `tools.amp_orca_3mf_handoff` does not exist.

- [ ] **Step 3: Implement the minimal transformer**

Implement these public functions:

```python
def load_plan(packet_dir: Path) -> HandoffPlan: ...
def patch_model_settings(data: bytes, assignments: dict[str, int]) -> bytes: ...
def patch_project_settings(data: bytes, nozzles: list[str]) -> bytes: ...
def generate_handoff(template: Path, packet_dir: Path, output: Path) -> dict[str, Any]: ...
```

Use normalized region names, numeric tool-class ordering, structured XML/JSON parsing, a temporary sibling file, and `os.replace()`.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the command from Step 2. Expected: one passing test.

- [ ] **Step 5: Commit**

```text
git add tools/amp_orca_3mf_handoff.py tests/tools/__init__.py tests/tools/test_amp_generate_orca_3mf_handoff.py
git commit -m "tools: generate Orca 3MF from AMP plan"
```

### Task 2: Embedded Packet And Deterministic Output

**Files:**
- Modify: `tests/tools/test_amp_generate_orca_3mf_handoff.py`
- Modify: `tools/amp_orca_3mf_handoff.py`

- [ ] **Step 1: Write failing packet and determinism tests**

Assert that the output contains:

```text
Metadata/AMP/plan.json
Metadata/AMP/process_queue.json
Metadata/AMP/tool_assignments.json
Metadata/AMP/handoff_manifest.json
```

Generate twice from identical inputs and assert identical SHA-256 values. Verify the manifest records the source template hash, ordered region assignments, nozzle vector, `hardware_preflight_status: not_ready`, and explicit non-claims.

- [ ] **Step 2: Run both tests and verify RED**

Run:

```text
python -m unittest tests.tools.test_amp_generate_orca_3mf_handoff.AmpOrca3mfHandoffTests.test_embeds_packet_and_manifest tests.tools.test_amp_generate_orca_3mf_handoff.AmpOrca3mfHandoffTests.test_output_is_deterministic -v
```

Expected: missing embedded members and differing archive hashes.

- [ ] **Step 3: Implement deterministic packet embedding**

Copy recognized packet files in sorted order under `Metadata/AMP/`. Create new `ZipInfo` members with:

```python
info.date_time = (1980, 1, 1, 0, 0, 0)
info.compress_type = zipfile.ZIP_DEFLATED
info.external_attr = 0o600 << 16
```

Write existing members in stable archive-name order while preserving their original `ZipInfo` fields and bytes except for the two patched metadata members.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the command from Step 2. Expected: two passing tests.

- [ ] **Step 5: Commit**

```text
git add tools/amp_orca_3mf_handoff.py tests/tools/test_amp_generate_orca_3mf_handoff.py
git commit -m "tools: embed deterministic AMP packet in Orca 3MF"
```

### Task 3: Fail-Closed And Atomic Behavior

**Files:**
- Modify: `tests/tools/test_amp_generate_orca_3mf_handoff.py`
- Modify: `tools/amp_orca_3mf_handoff.py`

- [ ] **Step 1: Write failing error-contract tests**

Cover:

```python
with self.assertRaisesRegex(HandoffError, "missing planned region"):
    generate_handoff(template_without_bulk, packet_dir, output)

with self.assertRaisesRegex(HandoffError, "tool slots"):
    generate_handoff(two_slot_template, packet_dir, output)

self.assertEqual(output.read_bytes(), b"existing output")
```

Also cover duplicate normalized object names, malformed XML, malformed JSON, missing `process_queue.json`, and `template == output`.

- [ ] **Step 2: Run error tests and verify RED**

Run:

```text
python -m unittest tests.tools.test_amp_generate_orca_3mf_handoff.AmpOrca3mfHandoffErrorTests -v
```

Expected: failures because errors are not normalized and output replacement is not fully guarded.

- [ ] **Step 3: Implement explicit validation and cleanup**

Add `HandoffError`. Validate all contracts before creating the final output. Catch parser/ZIP errors and raise contextual `HandoffError` messages. Remove temporary files in `finally`; replace the destination only after reopening and validating the temporary ZIP.

- [ ] **Step 4: Run the full generator test module**

Run:

```text
python -m unittest tests.tools.test_amp_generate_orca_3mf_handoff -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```text
git add tools/amp_orca_3mf_handoff.py tests/tools/test_amp_generate_orca_3mf_handoff.py
git commit -m "tools: fail closed on invalid Orca handoff inputs"
```

### Task 4: Independent Handoff Validator

**Files:**
- Create: `tools/amp_validate_orca_3mf_handoff.py`
- Create: `tests/tools/test_amp_validate_orca_3mf_handoff.py`

- [ ] **Step 1: Write failing validator tests**

Assert `validate_handoff()` passes a generated package and rejects independently corrupted object assignments, nozzle vectors, missing embedded files, and manifest/template hash mismatches:

```python
report = validate_handoff(generated_3mf, packet_dir)
self.assertTrue(report["valid"])
self.assertEqual(report["errors"], [])
```

- [ ] **Step 2: Run validator tests and verify RED**

Run:

```text
python -m unittest tests.tools.test_amp_validate_orca_3mf_handoff -v
```

Expected: import failure because the validator does not exist.

- [ ] **Step 3: Implement the independent validator**

Read the ZIP directly rather than calling generator internals. Recompute expected mappings from `process_queue.json`, parse the output XML/JSON, check embedded packet members and manifest fields, and return:

```python
{
    "valid": not errors,
    "errors": errors,
    "warnings": warnings,
    "region_assignments": observed_assignments,
    "nozzle_diameters": observed_nozzles,
}
```

The CLI exits `0` on valid and `1` on invalid, with optional JSON report output.

- [ ] **Step 4: Run generator and validator tests**

Run:

```text
python -m unittest tests.tools.test_amp_generate_orca_3mf_handoff tests.tools.test_amp_validate_orca_3mf_handoff -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```text
git add tools/amp_validate_orca_3mf_handoff.py tests/tools/test_amp_validate_orca_3mf_handoff.py
git commit -m "tools: validate AMP Orca 3MF handoff"
```

### Task 5: Known-Good Orca Integration Proof

**Files:**
- Create: `docs/milestones/AMP_Milestone_003_Automatic_Orca_3MF_Handoff.md`

- [ ] **Step 1: Generate from the known-good reference project**

Run:

```text
python tools/amp_orca_3mf_handoff.py --template "C:\Users\d\Desktop\AMP Official Orca Mixed Nozzle GUI Probe\02_save_outputs_here\orca_official_mixed_nozzle_original.3mf" --packet outputs/amp_plan_packet_001 --out outputs/amp_orca_3mf_handoff/amp_generated_orca_handoff.3mf
```

Expected: four mapped regions and nozzle ladder `0.2,0.4,0.6,0.8`.

- [ ] **Step 2: Validate the generated project**

Run:

```text
python tools/amp_validate_orca_3mf_handoff.py --3mf outputs/amp_orca_3mf_handoff/amp_generated_orca_handoff.3mf --packet outputs/amp_plan_packet_001 --out outputs/amp_orca_3mf_handoff/validation.json
```

Expected: `PASS`, zero errors.

- [ ] **Step 3: Check deterministic regeneration**

Generate a second output from identical inputs and compare SHA-256 hashes with `Get-FileHash`. Expected: identical hashes.

- [ ] **Step 4: Record the milestone**

Document exact commands, hashes, mapping, archive member preservation, embedded packet members, validator result, and these limits:

- Generated 3MF is for Orca inspection and slicing validation only.
- No physical U1 validation exists.
- No touchscreen-compatible mixed-nozzle claim is made.
- No Snapmaker validation is bypassed.
- Hardware preflight remains `not_ready`.

- [ ] **Step 5: Commit**

```text
git add docs/milestones/AMP_Milestone_003_Automatic_Orca_3MF_Handoff.md
git commit -m "docs: record AMP automatic Orca 3MF handoff"
```

### Task 6: Final Verification And Integration

**Files:**
- Modify only files already listed if verification exposes a defect.

- [ ] **Step 1: Run all focused Python tests**

```text
python -m unittest tests.tools.test_amp_generate_orca_3mf_handoff tests.tools.test_amp_validate_orca_3mf_handoff -v
```

- [ ] **Step 2: Compile-check the tools**

```text
python -m py_compile tools/amp_orca_3mf_handoff.py tools/amp_validate_orca_3mf_handoff.py
```

- [ ] **Step 3: Run repository checks**

```text
git diff --check
rg -n "zero-risk|Zero Risk|mathematically optimized|mixed-nozzle works|bypass safety|reverse-engineered|100% deterministic|ready to print" docs/milestones/AMP_Milestone_003_Automatic_Orca_3MF_Handoff.md tools/amp_orca_3mf_handoff.py tools/amp_validate_orca_3mf_handoff.py tests/tools
```

Expected: no whitespace errors and no overclaim hits.

- [ ] **Step 4: Inspect commit boundaries**

```text
git status --short
git diff u1-adaptive-nozzle-strategy...HEAD --stat
git log --oneline u1-adaptive-nozzle-strategy..HEAD
```

Expected: only the design, plan, two tools, focused tests, and Milestone 003 report are included.

- [ ] **Step 5: Fast-forward AMP branch and push**

From `B:\ohmic\Snapmaker-OrcaSlicer`, fast-forward `u1-adaptive-nozzle-strategy` to the feature branch and push `public/u1-adaptive-nozzle-strategy` after all verification succeeds.
