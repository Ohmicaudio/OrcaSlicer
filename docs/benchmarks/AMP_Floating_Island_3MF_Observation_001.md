# AMP Floating Island 3MF Observation 001

## Purpose

Verify the read-only streaming AMP 3MF observer on a detailed multi-plate, multi-material project without redistributing or modifying the source model.

## Source And Method

The source filename was `Floating+Island.3mf`. Concrete source and output paths are intentionally omitted from this public report. In the commands below, `$source` referred to the local source file and `$out` referred to an ignored local evidence directory.

| Measure | Observed value |
| --- | --- |
| Observer implementation commit | `c3fa3a890e9ad9242b7ef4f8d141a379696b39f2` |
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
| 1 | 0 | 129 seconds | 129 seconds | 26 MiB |
| 2 | 0 | 130 seconds | 130 seconds | 25 MiB |

These timings are two local observations on the machine class above. They are not a benchmark guarantee for other runs or systems.

## Observation Result

| Measure | Observed value |
| --- | ---: |
| Plates | 8 |
| Objects | 27 |
| Parts | 29 |
| Declared material slots | 7 (`1` through `7`) |
| Material assignments used by objects | 6 (`1` through `6`) |
| Physical nozzle vector | `0.4, 0.4` millimeters |
| Total vertices | 5,685,664 |
| Total triangles | 11,372,080 |
| Top-level observer diagnostics | 0 |
| Object-level observer diagnostics | 0 |
| Deterministic repeats | 2 of 2 JSON reports matched; 2 of 2 Markdown reports matched |

Report hashes:

| Output | SHA-256 |
| --- | --- |
| Observation JSON, run 1 | `d0487e55edbef1546e8efd470173ff8e1250e5e126a4f1bb8a748371366fbbda` |
| Observation JSON, run 2 | `d0487e55edbef1546e8efd470173ff8e1250e5e126a4f1bb8a748371366fbbda` |
| Observation Markdown, run 1 | `6f0ffe5a7efb663d03734538e028f204ce572be7c1375c553c9b23224546137e` |
| Observation Markdown, run 2 | `6f0ffe5a7efb663d03734538e028f204ce572be7c1375c553c9b23224546137e` |

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

Zero observer diagnostics means only that this observer emitted no top-level or object-level diagnostic for the package. It does not establish model validity, slicability, printability, quality, strength, or safety.

## Assignment Separation

The 27 object records use material assignments `1` through `6`. These values remain material/color metadata and are resolved separately from the project-level physical nozzle vector.

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
