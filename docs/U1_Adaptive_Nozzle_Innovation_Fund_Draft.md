# Snapmaker U1 Innovation Fund Draft

## Project Name

Adaptive Nozzle Strategy for U1

## Project URL

Add the public GitHub repository URL here after the fork/repo is published.

## Category

Slicer / software

Secondary category if Snapmaker supports multiple categories: Hardware modification.

## Short Description

An open-source Snapmaker Orca prototype and workflow for detail-aware extrusion widths and multi-nozzle U1 printing. The project aims to preserve fine exterior detail while using larger effective line widths or larger nozzle toolheads for shells, inner walls, and bulk regions, improving the print speed/detail tradeoff for U1 users.

## Support Request

I can begin with slicer research, public documentation, and a profile-only proof of concept. Full validation requires U1 hardware access. I am requesting access to a U1 and, if possible, multiple nozzle sizes or toolhead configuration guidance so the project can test mixed-nozzle workflows responsibly.

## Technical Summary

Most FDM slicing treats nozzle diameter as a static profile choice. A small nozzle gives detail but slows the print; a large nozzle prints faster and stronger but loses fine exterior resolution. U1 makes this tradeoff especially interesting because its multi-toolhead design creates the possibility of role-specific nozzle behavior.

The first milestone treats "adaptive nozzle diameter" as adaptive effective extrusion width using existing Orca/Snapmaker Orca settings. The second milestone evaluates physical mixed-nozzle U1 workflows where a small nozzle handles visible detail and larger nozzles handle inner shells, infill, or supports.

## Deliverables

- Public fork or companion repository.
- U1 adaptive nozzle strategy documentation.
- U1 profile inventory for 0.2, 0.4, 0.6, and 0.8 nozzle families.
- Experimental profile-only proof of concept.
- G-code comparison notes.
- Hardware validation report if U1 access is granted.

## Submission Notes

Submit through:

- https://www.snapmaker.com/innovation-fund

Phase 1 submissions close September 7, 2026.

Additional contact route:

- community@snapmaker.com

