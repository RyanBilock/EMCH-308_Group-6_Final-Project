# EMCH 308 Semester Project: Lightweight I-Beam Design

Finite element design and validation of an 8" × 3" I-beam for EMCH 308 (Introduction to Finite Element Stress Analysis) at the University of South Carolina (USC), Fall 2026. The beam was designed by a USC team and manufactured in partnership with Midlands Technical College (MTC).

## Design requirements

- **Weight:** ≤ 1 lbf
- **Strength:** factor of safety (FoS) ≥ 1.25 for a 5,000 lbf load in 3-point bending
- **Cost:** total manufacturing cost ≤ $600, using one of three approved stock options
- **Fixed geometry:** 8" span, 3" height, four Ø1" through holes (additional material removal allowed)

## Test setup

- Central steel load roller, Ø0.984"
- Two steel support rollers, Ø0.394", 8" center-to-center
- Loaded to 6,250 lbf; FoS checked against a 0.02" offset line from the linear-elastic load–displacement response

## Repository contents

| Folder | Contents |
|---|---|
| `abaqus/` | `.cae` model and `.odb` results for the final simulation |
| `scripts/` | Python scripts for model setup and post-processing |
| `cad/` | `.step` model and PDF manufacturing drawing (revision-controlled) |
| `results/` | Load–displacement plots comparing simulation and experiment |
| `report/` | Final report: modeling approach, element selection, mesh study, and test comparison |

## Tools

- Abaqus/CAE (finite element modeling and analysis)
- Python (scripting and post-processing)
