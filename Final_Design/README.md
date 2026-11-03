# Final Design: Rev C (Stock 1, roller pads + sawn notches)

> **Status: Abaqus run complete (Nov 3, 2026): meets weight, FoS and cost.** FoS 1.772, weight 0.914 lb, cost $131.78. Mesh-convergence check still optional. The last fully analysed design, Rev B, is in [`Old_Designs/RevB_Stock1_Drilled_v2/`](../Old_Designs/RevB_Stock1_Drilled_v2/).

These are **copies**: each file also stays in its original location (listed below). Change the original, then refresh the copy here.

![Rev C design sheet](Drawings/Design_Sheet_Stock1_RevC_v1.png)

## Summary

- **Stock:** Stock 1, AA I 3 × 2.03 (6061-T6), full 8.40 in raw length (no cross-cut; 0.20 in overhang past each support, Rev B had 0.10 in)
- **Flanges:** full 2.50 in width wherever a test roller touches:
  - top flange, |z| ≤ 0.75 in from mid-span (load roller)
  - bottom flange, |z| ≥ 3.50 in (both supports)
  - everywhere else the tips are notched 0.65 in deep, leaving the flange 1.20 in wide
- **Corners:** 8 × Ø0.50 relief holes drilled first; the saw cuts end tangent to them, so every inside corner is R0.25 (MTC cannot make sharp corners)
- **Web:** unchanged except the 4 required Fig. 1 holes, opened to Ø1.03 (1-1/32 drill)

| Requirement | Limit | Rev C | |
|---|---|---|---|
| Weight (0.098 lb/in³) | ≤ 1.00 lb | 0.914 lb (Abaqus mesh 0.9139 lb, matches CAD to 0.001 %; 0.928 lb if every notch is 0.02 in shallow) | Pass |
| Factor of safety (FoS), 0.02 in offset method | ≥ 1.25 | **1.772** (P_offset = 8,858 lbf, Abaqus, 234,665-node mesh) | Pass |
| Cost (course cost sheet) | ≤ $600 | $131.78 | Pass |

| Item | Calculation | Cost |
|---|---|---|
| Material, Stock 1 | 8.4 in × 2.03/12 lb/in × $38.72/lb | $55.02 |
| Saw (14 cuts) | (0.1667 + 0.0167 × 14) h × $100/h | $40.05 |
| Drill (4 web + 8 relief = 12 holes) | (0.1667 + 0.0167 × 12) h × $100/h | $36.71 |
| **Total** | | **$131.78** |

With setups the sheet does not model (second drill size, flipping between flanges, a cross-cut) the total is $183.46. If MTC has to mill the notches instead of sawing them, the cost rises to about $1,860–$3,890 and fails the limit.

## Open items before release to MTC

1. ~~Run the Rev C Abaqus model~~ Done Nov 3, 2026: FoS 1.772, mesh weight 0.9139 lb (see `Results/`). Optional: run the mesh-convergence job (`MESH_LEVEL = 'CHECK'`), then `FOS_Stock1_RevC_v2.py`.
2. Confirm with David Wilson (MTC) that the notches can be sawn out to the relief holes.
3. Fig. 1 allows Ø1.00 ± 0.02 (0.98–1.02); the Ø1.03 holes are a deliberate team choice.
4. ~~Make the Rev C manufacturing drawing~~ Done: `Drawings/USC06_MTC06_IBeam_RevC_Drawing.pdf` (3 sheets). STEP file: run `Export_STEP_v4.py`.

## What's here

| Folder | File | What it is | Original location |
|---|---|---|---|
| `Drawings/` | `Design_Sheet_Stock1_RevC_v1.pdf` / `.png` | One-page design sheet: views, dimensions, Abaqus FoS curve, cost, weight, feature schedule | `cad/drawings/` |
| | `USC06_MTC06_IBeam_RevC_Drawing.pdf` + `_sheet1–3.png` | Manufacturing drawing for MTC (3 sheets, 1:1) | `cad/` |
| | `Proposal_RevC_Stock1_v2.pdf` / `.png` | Concept sheet: flange plans, side view, sections, weight, cost, strength | `cad/concept_drawings/` |
| `Cost/` | `ProjectCostSheet_RevC_Stock1_v2.xlsx` | Course cost sheet, filled in ($131.78) | `cost/` |
| `Scripts/` | `Stock1_RevC_v1.py` | Builds the Rev C beam, finest mesh under the 250,000-node limit, submits the job | `abaqus/python/final/` |
| | `FOS_Stock1_RevC_v1.py` → `_v3.py` | Reads the `.odb`: FoS, weight, cost, solver warnings, accuracy checks, mesh convergence (use v3) | `abaqus/python/final/` |
| | `fix_Stock1_RevC_v1.py` | Warning-free rerun of the v1 model as job `Stock1_RevC_v2` | `abaqus/python/final/` |
| | `Export_STEP_v4.py` | Writes `cad/USC06_MTC06_IBeam_RevC.step` (inches) after geometry checks | `abaqus/python/final/` |
| | `make_RevC_drawing_v1.py` · `make_RevC_design_sheet_v1.py` | Generate the manufacturing drawing and the design sheet | `cad/drawings/source/` |
| | `make_RevC_concept_v2.py` | Draws the concept sheet and recomputes weight, cost, stresses | `cad/drawings/source/` |
| `Results/` | `Design_Comparison.png` | Abaqus curves of the earlier designs (Rev C to be added) | `results/` |
| `Abaqus/` | *(after the run)* | Rev C model, job and `.odb` | `abaqus/final_design/` |
| `Results/` | *(after the run)* | `FOS_Stock1_RevC_v1.txt` / `_LoadDisp.csv` / `.png` | `results/final_design/` |
| `CAD/` | *(to come)* | Rev C STEP file | `cad/` |
