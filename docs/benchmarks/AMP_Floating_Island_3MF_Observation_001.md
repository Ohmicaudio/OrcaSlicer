# AMP Floating Island 3MF Observation 001

## Purpose

Verify the read-only streaming AMP 3MF observer on a detailed multi-plate, multi-material project without redistributing or modifying the source model.

## Source And Method

The source filename was `Floating+Island.3mf`. Concrete source and output paths are intentionally omitted from this public report. In the commands below, `$source` referred to the local source file and `$out` referred to an ignored local evidence directory.

| Measure | Observed value |
| --- | --- |
| Final observer implementation commit | `2d0593017d75c3625aa52b2c535c9e2617e5ce9a` |
| Retained two-run evidence commit | `0e92a6e8a6dfd2a159aa01aa3b46e6e045ffe42a` |
| Observation schema | `0.1` |
| Source SHA-256 before observation | `8399e4ff4e428969d092844ddac6c6fd8c063b062fcbfedc7c02f3099d600e17` |
| Source SHA-256 after observation | `8399e4ff4e428969d092844ddac6c6fd8c063b062fcbfedc7c02f3099d600e17` |
| Compressed source size | 126,438,172 bytes |
| Archive members | 78 |
| Declared uncompressed member bytes | 905,698,105 bytes |

The observer was run twice, sequentially:

```powershell
$source = Join-Path '<local source directory>' 'Floating+Island.3mf'
$out = '<ignored local evidence directory>'

python tools\amp_observe_3mf.py --3mf $source --out-json "$out\observation-1.json" --out-md "$out\observation-1.md"
python tools\amp_observe_3mf.py --3mf $source --out-json "$out\observation-2.json" --out-md "$out\observation-2.md"
```

Both observer processes exited `0`. The source hash and size were unchanged afterward. The evidence directory contained zero subdirectories, and a source scan of the observer found no `extract()` or `extractall()` call. The generated observer reports and measurement evidence remained in the ignored local evidence directory.

After the final ambiguous-assignment and cross-plate identity fixes, one additional read-only confirmation run used final implementation commit `2d0593017d75c3625aa52b2c535c9e2617e5ce9a`. It exited `0`, left the source hash unchanged, and produced JSON SHA-256 `f276584714d27c580a05f50a11f50bfa0efdd92afeaa3102000eb7b3ff8024ca` and Markdown SHA-256 `39b669835a8ab0fed5377ab0620cd5abbf95f68d50459b36e7854dfd1c6d30a5`, exactly matching both retained reports. Because the serialized output was unchanged, the retained two-run hashes, totals, and performance measurements below were not replaced.

## Source Provenance And License

The observer reported this embedded metadata:

| Field | Embedded value |
| --- | --- |
| Title | `Minka Skyland - Levitating Island` |
| Designer | `Entropy` |
| License | `Standard Digital File License` |

These are package metadata observations, not a legal interpretation. This report does not evaluate or grant redistribution rights. The source model, any embedded user identifiers, embedded profile assets, thumbnails, generated observer reports, and local measurement evidence were not committed or redistributed by this observation.

## Local Process Evidence

The two observations used this machine-class environment. User name, host name, serial identifiers, and concrete filesystem paths are omitted.

| Field | Local value |
| --- | --- |
| Python | `3.13.5` |
| Operating system | Microsoft Windows 10 Home, build `19045`, 64-bit |
| CPU | AMD Ryzen Threadripper 1920X 12-Core Processor |
| Installed RAM | 32 GiB |

Python version came from `python --version`. Windows name, version, and architecture came from `Win32_OperatingSystem`; CPU model came from `Win32_Processor.Name`; installed RAM came from `Win32_ComputerSystem.TotalPhysicalMemory` rounded to the nearest whole GiB.

The following is the measurement portion of the PowerShell harness actually used, with only the concrete `$source` and `$out` values redacted above. The `foreach` loop made run 1 complete before run 2 started. `Stopwatch` started immediately before `Process.Start`; it stopped immediately after `WaitForExit(50)` reported process exit. CPU time came from `Process.TotalProcessorTime.TotalSeconds`. Working set was sampled from `Process.WorkingSet64` every 50 ms. After exit, the harness also read `Process.PeakWorkingSet64`.

```powershell
$python = (Get-Command python -ErrorAction Stop).Source
$runs = @()

foreach ($run in 1, 2) {
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $python
    $psi.WorkingDirectory = (Get-Location).Path
    $psi.UseShellExecute = $false
    $psi.Arguments = ('tools\amp_observe_3mf.py --3mf "{0}" --out-json "{1}" --out-md "{2}"' -f $source, "$out\observation-$run.json", "$out\observation-$run.md")

    $startedUtc = [DateTime]::UtcNow
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $process = [System.Diagnostics.Process]::Start($psi)
    $sampledPeakWorkingSet = 0L
    while (-not $process.WaitForExit(50)) {
        try {
            $process.Refresh()
            if ($process.WorkingSet64 -gt $sampledPeakWorkingSet) {
                $sampledPeakWorkingSet = $process.WorkingSet64
            }
        } catch {}
    }
    $stopwatch.Stop()
    $process.Refresh()
    $processPeakWorkingSet = $process.PeakWorkingSet64
    $retainedPeakWorkingSet = [Math]::Max($sampledPeakWorkingSet, $processPeakWorkingSet)

    $result = [ordered]@{
        run = $run
        execution_order = $run
        started_utc = $startedUtc.ToString('o')
        finished_utc = [DateTime]::UtcNow.ToString('o')
        exit_code = $process.ExitCode
        stopwatch_elapsed_seconds = $stopwatch.Elapsed.TotalSeconds
        process_total_processor_time_seconds = $process.TotalProcessorTime.TotalSeconds
        sampled_working_set_peak_bytes = $sampledPeakWorkingSet
        process_peak_working_set_bytes = $processPeakWorkingSet
        retained_peak_working_set_bytes = $retainedPeakWorkingSet
        json_name = "observation-$run.json"
        markdown_name = "observation-$run.md"
    }
    $runs += [pscustomobject]$result
    if ($process.ExitCode -ne 0) { throw "observer run $run failed" }
}
```

On this host, `Process.PeakWorkingSet64` was unavailable after both process exits and was recorded as null. No value was inferred for it. The table therefore reports only the maximum sampled `WorkingSet64`, rounded to the nearest whole MiB. Wall and CPU times are rounded to the nearest whole second.

| Run | Exit | Wall time | CPU time | Sampled working-set peak |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 135 seconds | 134 seconds | 27 MiB |
| 2 | 0 | 142 seconds | 141 seconds | 27 MiB |

These timings are two local observations on the machine class above. They are not a benchmark guarantee for other runs or systems.

## Observation Result

| Measure | Observed value |
| --- | ---: |
| Plates | 8 |
| Objects | 27 |
| Parts | 29 |
| Declared material slots | 7 (`1` through `7`) |
| Positive object material summaries | 6 (`1` through `6`) |
| Effective part material assignments | 7 (`1` through `7`) |
| Physical nozzle vector | `0.4, 0.4` millimeters |
| Total vertices | 5,685,664 |
| Total triangles | 11,372,080 |
| Top-level observer diagnostics | 0 |
| Object-level observer diagnostics | 2 |
| Optional plate members | 17 total; 16 image members |
| Deterministic repeats | 2 of 2 retained reports matched; the final-code confirmation matched both formats |

Report hashes:

| Output | SHA-256 |
| --- | --- |
| Observation JSON, run 1 | `f276584714d27c580a05f50a11f50bfa0efdd92afeaa3102000eb7b3ff8024ca` |
| Observation JSON, run 2 | `f276584714d27c580a05f50a11f50bfa0efdd92afeaa3102000eb7b3ff8024ca` |
| Observation Markdown, run 1 | `39b669835a8ab0fed5377ab0620cd5abbf95f68d50459b36e7854dfd1c6d30a5` |
| Observation Markdown, run 2 | `39b669835a8ab0fed5377ab0620cd5abbf95f68d50459b36e7854dfd1c6d30a5` |

Plate inventory:

| Plate | Name | Objects |
| ---: | --- | ---: |
| 1 | Floating Island | 5 |
| 2 | Base Rocks | 2 |
| 3 | Base & Island Water | 4 |
| 4 | Grass & Tree Leaves | 8 |
| 5 | Tree Trunk | 1 |
| 6 | House Frames | 3 |
| 7 | House Glass | 2 |
| 8 | House Roofs | 2 |

The two object diagnostics are identical mixed-part summaries for `House-Upper-RoofBeams` and `House-Lower-RoofBeams`. Each object contains effective part assignments `3` and `7`, so its singular `material_assignment` and `resolved_material` fields are null. The diagnostics preserve that ambiguity rather than collapsing it to one slot. The absence of a top-level diagnostic and the presence of only these two object diagnostics do not establish model validity, slicability, printability, quality, strength, or safety.

## Report Field Notes

The observation schema remains `0.1`. This refreshed report records the following schema behavior from final implementation commit `2d0593017d75c3625aa52b2c535c9e2617e5ce9a`:

- `source.plate_members` and `source.plate_thumbnail_members` are always present. They contain only canonically ordered archive member names, not file content or absolute paths. This package reported 17 `plate_*` members under `Metadata`, including 16 PNG image members and one JSON member.
- Each object has ordered `part_assignments` records with part ID, explicit assignment, effective assignment after inheritance, and resolved material. A singular object material summary is retained only when every part has the same non-null effective assignment. Known assignments mixed with unresolved part assignments produce a null singular summary and a deterministic diagnostic; all-unresolved parts remain null without fabricating a slot. Objects with no part records retain their object-level assignment.
- Each object has sorted `source_model_members`; the legacy singular `source_model_member` is populated only when exactly one unique member is used. All 27 objects in this package referenced one member each.
- Plate membership is instance-aware. Plates contain unique sorted `object_ids` and ordered instance records, while objects contain ordered instances plus sorted unique `plate_ids` and `plate_names`. Explicit `(object_id, instance_id)` identities must be globally unique across plates; absent instance IDs remain null and do not create an invented global identity. All 27 objects in this package appeared on exactly one plate with one recorded instance.
- Report validation requires every `physical_nozzle_assignment` and `recommended_tool_class` field to be null. Non-null mutations are rejected before report outputs are replaced.

## Assignment Separation

The positive singular object summaries use material assignments `1` through `6`. The 29 part records use effective assignments `1` through `7`; the two mixed roof-beam objects have null singular summaries as described above. These values remain material/color metadata and are resolved separately from the project-level physical nozzle vector.

All 27 `physical_nozzle_assignment` fields are null. All 27 `recommended_tool_class` fields are also null. The observer therefore did not reinterpret material assignments as physical nozzle selections and did not recommend an AMP tool class.

## Limits

- This is read-only representation observation.
- No geometry scoring or manufacturing-region split was performed.
- No nozzle or tool class was recommended.
- No 3MF was modified.
- No G-code was generated.
- No physical U1 or mixed-nozzle behavior was validated.
- No model validity, slicability, printability, quality, strength, or safety conclusion was made.
- The report does not evaluate or grant redistribution rights.
- The source model and generated evidence are not committed or redistributed.
