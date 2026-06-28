# U1 Adaptive Nozzle Profile Inventory

## Baseline Machine Profile

- File: `resources/profiles/Snapmaker/machine/Snapmaker U1.json`
- Model ID: `SM_U1`
- Declared nozzle diameters: `0.2;0.4;0.6;0.8`

## Process Families

### Base And Common

- `resources/profiles/Snapmaker/process/fdm_process_U1.json`
- `resources/profiles/Snapmaker/process/fdm_process_U1_common.json`

The base process defines the main 0.4-class role widths. The common profile currently sets `wall_generator` to `classic`.

### 0.2 Nozzle Process Bases

- `fdm_process_U1_0.06_nozzle_0.2.json`
- `fdm_process_U1_0.08_nozzle_0.2.json`
- `fdm_process_U1_0.10_nozzle_0.2.json`
- `fdm_process_U1_0.12_nozzle_0.2.json`
- `fdm_process_U1_0.14_nozzle_0.2.json`

Common observed line width: `0.22`, with initial layer width `0.25`.

### 0.4 Nozzle Process Bases

- `fdm_process_U1_0.08.json`
- `fdm_process_U1_0.12.json`
- `fdm_process_U1_0.16.json`
- `fdm_process_U1_0.20.json`
- `fdm_process_U1_0.24.json`
- `fdm_process_U1_0.28.json`

These inherit from the 0.4-class base/common U1 process.

### 0.6 Nozzle Process Bases

- `fdm_process_U1_0.18_nozzle_0.6.json`
- `fdm_process_U1_0.24_nozzle_0.6.json`
- `fdm_process_U1_0.30_nozzle_0.6.json`
- `fdm_process_U1_0.36_nozzle_0.6.json`
- `fdm_process_U1_0.42_nozzle_0.6.json`

Common observed line width: `0.62`.

### 0.8 Nozzle Process Bases

- `fdm_process_U1_0.24_nozzle_0.8.json`
- `fdm_process_U1_0.32_nozzle_0.8.json`
- `fdm_process_U1_0.40_nozzle_0.8.json`
- `fdm_process_U1_0.48_nozzle_0.8.json`
- `fdm_process_U1_0.56_nozzle_0.8.json`

Common observed line width: `0.82`.

## First Profile Experiment

Start from:

- `resources/profiles/Snapmaker/process/0.20 Standard @Snapmaker U1 (0.4 nozzle).json`
- `resources/profiles/Snapmaker/process/fdm_process_U1_0.20.json`
- `resources/profiles/Snapmaker/process/fdm_process_U1_common.json`

Experimental settings to test in a copied profile:

- `wall_generator`: `arachne`
- `outer_wall_line_width`: keep near `0.42`
- `top_surface_line_width`: keep near `0.42`
- `inner_wall_line_width`: test `0.50` to `0.54`
- `sparse_infill_line_width`: test `0.54` to `0.60`
- `internal_solid_infill_line_width`: test `0.50` to `0.54`

Do not ship these as defaults until preview, G-code, and real U1 print validation are complete.

