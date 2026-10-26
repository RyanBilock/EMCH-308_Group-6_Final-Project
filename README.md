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
| `cost/` | Course cost sheet filled in for the final design |
| `Blackboard Files/` | Course reference documents: project statement, rubric, communication guide, and cost sheet |

### Current files

```
abaqus/
├── ProjectBeam.cae / .jnl          Original model (rollers, material); the scripts open it
├── Baseline_Stock1.cae / .jnl      Standard Stock 1 beam, 8.2 in, required holes only
├── Stock1_Drilled_v2.cae / .jnl    FINAL DESIGN model: Stock 1, 28 drilled flange holes
├── Stock1_Drilled_v2/              Final design job (.cae with job, .jnl, .inp)
├── Stock1_Drilled.cae / .jnl       Drilled v1 model (superseded)
├── Stock1_Drilled/                 Drilled v1 job (.cae, .jnl, .inp)
├── Stock1_Notched/                 Notched-flange job (.cae, .jnl, .inp)
└── python/
    ├── Stock1_Drilled_v2.py        Builds the final design and submits its job
    ├── FOS_Stock1_Drilled_v2.py    FoS, exact curved-element weight, first-yield location
    ├── Baseline_Stock1_v1.py       Rebuilds Baseline_Stock1.cae (no extra cutouts)
    ├── Stock1_Drilled_v1.py        Drilled v1 model (superseded)
    ├── Stock1_Drilled_Job_v1.py    Job script for drilled v1
    ├── FOS_Stock1_Drilled_v1.py    FoS for drilled v1 (straight-tet weight, superseded)
    ├── Stock1_Notched_v1.py        Notched Stock 1 design + job
    ├── Stock1_Plain_v1.py          Plain Stock 1 + job
    ├── FOS_ProjectBeam_v3.py       Offset-method FoS for every .odb in the work directory
    └── fix_history/                Every repair script, renumbered v1–v5, plus FOS v1–v2 (see its README)
results/
├── Stock1_Drilled_v2/              FINAL: FoS 1.625, 0.993 lb — plot, CSV, FoS report
├── Stock1_Drilled/                 Drilled v1: FoS 1.246 (fails) — plot, CSV, FoS report
├── Stock1_Notched/                 FoS 1.64, 0.957 lb — plot, CSV, FoS table
└── Stock3_Beam_8p2in/              FoS 3.55, over the weight limit — plot, CSV, FoS summary
cad/
└── concept_drawings/               Hole_Layout_Stock1_Drilled_v2.png (final layout); older
                                    material-removal and cost-plan drawings (superseded)
cost/
└── ProjectCostSheet_Stock1_Drilled_v2.xlsx   Course cost sheet filled in for the final design
```

**Running the scripts:** in Abaqus/CAE, set the work directory to the folder holding `ProjectBeam.cae` (`abaqus/`), then use **File → Run Script** on a file in `abaqus/python/`. `Stock1_Drilled_v2.py` writes its job into `Stock1_Drilled_v2/`; `FOS_Stock1_Drilled_v2.py` finds the `.odb` from anywhere in the project and writes to `results/Stock1_Drilled_v2/`.

**Not on GitHub:** the `.odb` result files (314–398 MB) are over GitHub's 100 MB file limit and stay on the team's project drive; each can be regenerated from the `.inp` in its job folder. Superseded scripts and models live in a local `archive/` folder.

### Final design: Stock 1 drilled v2

- **Stock:** Stock 1, AA I 3 × 2.03 (6061), cut to 8.20 in
- **Holes:** 4 × Ø1.00 Fig. 1 web holes (required) + 28 × Ø25/32 (0.78125) flange holes, drill thru, centred ±0.7875 from the web
  - Top flange: z = ±1.30, ±2.18, ±3.06 in from mid-span (12 holes)
  - Bottom flange: z = ±0.44, ±1.32, ±2.20, ±3.08 in from mid-span (16 holes)
- **No milling, no extra web holes.** Holes are kept clear of the load roller and the supports, where the web yields first.

| Requirement | Limit | Final design | |
|---|---|---|---|
| Weight | ≤ 1.00 lb | 0.993 lb (CAD and curved-element mesh agree) | Pass |
| FoS (offset method, 0.02 in) | ≥ 1.25 | 1.625 (P_offset = 8,123 lbf) | Pass |
| Cost (course cost sheet) | ≤ $600 | $143.47 | Pass |

**Cost breakdown** (from `ProjectCostSheet_F26_Deployable.xlsx` formulas):

| Item | Calculation | Cost |
|---|---|---|
| Material, Stock 1 | 8.4 in × 2.03/12 lb/in × $38.72/lb | $55.02 |
| Saw cut to 8.20 in (1 cut) | (0.1667 + 0.0167 × 1) h × $100/h | $18.34 |
| Drill (4 Fig. 1 + 28 flange = 32 holes) | (0.1667 + 0.0167 × 32) h × $100/h | $70.11 |
| **Total** | | **$143.47** |

If MTC needs the ends faced for length tolerance (saw ±0.02 in vs. face ±0.005 in), add facing both ends: (0.5 + 0.04 × 2) h × $250/h = $145.00, for a total of $288.47 — still under $600.

### Design history

| Design | Weight (lb) | FoS | Cost | Status |
|---|---|---|---|---|
| Stock 3, required holes only | 1.68 | 3.55 | — | Too heavy |
| Stock 1, notched flanges | 0.957 | 1.64 | over $600 (milling) | Meets weight and FoS, cost too high |
| Stock 1, drilled v1 (32 flange + 2 web holes, milled end reliefs) | 0.993 | 1.246 | $510 | Fails FoS (web yields around the extra web holes) |
| **Stock 1, drilled v2 (28 × Ø25/32 flange holes)** | **0.993** | **1.625** | **$143.47** | **Final: meets all three** |

## Tools

- Abaqus/CAE (finite element modeling and analysis)
- Python (scripting and post-processing)
