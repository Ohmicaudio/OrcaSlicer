# Snapmaker Support Ticket Record

## Submission

- Submitted: 2026-06-29 07:44:46 -04:00
- Status: submitted / awaiting response
- Support/contact route used: Snapmaker General Inquiry Form
- Issue type selected: Complaints and Feature request
- Subcategory selected: Hardware request

## Subject

U1 engineering guidance request: mixed-nozzle validation constraints for Adaptive Manufacturing Planner

## Public Project Link

- AMP branch: <https://github.com/Ohmicaudio/OrcaSlicer/tree/u1-adaptive-nozzle-strategy>
- Forum discussion: <https://forum.snapmaker.com/t/adaptive-manufacturing-planner-for-u1-bead-widths-first-mixed-nozzles-later/42359>

## Questions Asked

The ticket asked Snapmaker Support / Engineering for U1-specific guidance on:

- Whether U1 supports, rejects, or leaves undefined different physical nozzle diameters across toolheads in one print job.
- How U1 validates nozzle state against slicer jobs.
- Whether nozzle diameter is checked per printer, per toolhead, or per selected process/profile.
- Whether there is a documented path for matching slicer-side nozzle declarations to the printer's remembered/current nozzle state.
- Whether toolhead offsets, Z offsets, or nozzle-size calibration values are stored independently per toolhead/nozzle combination.
- Known limitations around purge, wipe tower behavior, or toolchange reliability when nozzle diameters differ between toolheads.
- Recommended first validation tests before mixed-nozzle toolpath logic is allowed to affect G-code.

## Safety Status

Stage 2 mixed physical nozzle behavior remains blocked until U1 hardware behavior, nozzle-state validation, calibration assumptions, toolchange cost, purge/wipe behavior, and bonding risks are understood.
