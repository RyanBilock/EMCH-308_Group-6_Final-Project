# EMCH 308 Semester Project: Lightweight I-Beam Design

Finite element design and validation of an 8" × 3" I-beam for EMCH 308 (Introduction to Finite Element Stress Analysis) at the University of South Carolina (USC), Fall 2026. The beam was designed by a USC team and manufactured in partnership with Midlands Technical College (MTC).

## Team 6

| Name | Institution | Contact |
|---|---|---|
| Chase Gregg | USC | cgregg@email.sc.edu |
| Sam McKool | USC | smckool@email.sc.edu |
| James Dierdorf | USC | dierdorf@email.sc.edu |
| Ryan Bilock | USC | rbilock@email.sc.edu |
| David Wilson | MTC | davidwilson358@student.midlandstech.edu |

**Instructors:** 
| Name | Institution | Contact |
|---|---|---|
| Andrew Gross | USC | andrewgross@sc.edu |
| Gary Shannon | MTC | shannong@midlandstech.edu |

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
| `abaqus/` | `.cae` model, `.jnl` journal, and `.odb` results for the final simulation |
| `abaqus/python/` | Python scripts for model setup and post-processing |
| `cad/` | `.step` model and PDF manufacturing drawing (revision-controlled, e.g. `USC06_MTC06_IBeam_RevA.step`) |
| `results/` | Load–displacement plots comparing simulation and experiment |
| `report/` | Final report: modeling approach, element selection, mesh study, and test comparison |
| `Blackboard Files/` | Course reference documents: project statement, rubric, communication guide, and cost sheet |

### Current files

```
abaqus/
├── ProjectBeam.cae / .jnl          Original model (rollers, material); the scripts open it
├── Baseline_Stock1.cae / .jnl      Standard Stock 1 beam, 8.2 in, required holes only
├── Stock1_Drilled.cae / .jnl       Stock 1 + recommended drilled holes (cost-compliant plan)
├── Stock1_Notched/                 Completed notched-flange analysis (.cae, .jnl, .inp)
└── python/
    ├── Baseline_Stock1_v1.py       Rebuilds Baseline_Stock1.cae (no extra cutouts)
    ├── Stock1_Drilled_v1.py        Rebuilds Stock1_Drilled.cae (recommended cutouts)
    ├── Stock1_Drilled_Job_v1.py    Checks Stock1_Drilled.cae and submits its job into abaqus/Stock1_Drilled/
    ├── FOS_Stock1_Drilled_v1.py    FoS, weight and peak stress of the drilled beam → results/Stock1_Drilled/
    ├── Stock1_Notched_v1.py        Notched Stock 1 design + job
    ├── Stock1_Plain_v1.py          Plain Stock 1 + job
    ├── FOS_ProjectBeam_v3.py       Offset-method FoS for every .odb in the work directory
    └── fix_history/                Every repair script, renumbered v1–v5, plus FOS v1–v2 (see its README)
results/
├── Stock1_Notched/                 FoS 1.64, 0.957 lb: load–displacement plot, CSV, FoS table
└── Stock3_Beam_8p2in/              FoS 3.55, over the weight limit: plot, CSV, FoS summary
cad/
└── concept_drawings/               Material-removal and cost-plan drawings
```

**Running the scripts:** in Abaqus/CAE, set the work directory to `abaqus/` (the folder holding `ProjectBeam.cae`), then use **File → Run Script** on a file in `abaqus/python/`. To recompute FoS, set the work directory to the folder holding the `.odb` and run `FOS_ProjectBeam_v3.py`.

**Not on GitHub:** `Stock1_Notched.odb` (354 MB) is over GitHub's 100 MB file limit and stays on the team's project drive; it can be regenerated from `abaqus/Stock1_Notched/Stock1_Notched.inp`. Superseded scripts and models live in a local `archive/` folder.

### Design status

| Design | Weight (lb) | FoS | Est. cost | Status |
|---|---|---|---|---|
| Stock 3, required holes only | 1.68 | 3.55 | — | Too heavy |
| Stock 1, notched flanges | 0.957 | 1.64 | over $600 (milling) | Meets weight and FoS, cost too high |
| Stock 1, drilled holes (Option A + B) | 0.993 | pending | $510 | Recommended; run `Stock1_Drilled_Job_v1.py`, then `FOS_Stock1_Drilled_v1.py` |

## Tools

- Abaqus/CAE (finite element modeling and analysis)
- Python (scripting and post-processing)
