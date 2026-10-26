# Fix history: Abaqus repair scripts

Every version of the scripts that repaired the original `ProjectBeam.cae` model (Stock 3 I-beam) and computed its factor of safety (FoS). The scripts were renumbered into a clean sequence. Each file's header gives the name it was first delivered under.

The current scripts are one folder up in `abaqus/python/`. The Stock 1 scripts there are built on `fix_ProjectBeam_v5.py`.

## Model repair: `fix_ProjectBeam_v1` → `v5`

| File | Originally | Job | What changed |
|---|---|---|---|
| `fix_ProjectBeam_v1.py` | `fix_ProjectBeam.py` / `_v7.py` | `Beam_Fixed` | First working repair. Displacement-controlled top roller (fixes the zero-pivot error); roller contact uses SIDE2 normals (fixes 148 wrong-way facets); duplicate beam instance removed; rollers placed from the beam geometry (8.000 in span); quadratic tet (C3D10) remesh with a 250,000-node licence guard; always reopens the original `ProjectBeam.cae` |
| `fix_ProjectBeam_v2.py` | `fix_ProjectBeam_v8.py` | `Beam_Fixed` | Beam length 8.5 → 8.2 in (0.15 in trimmed from each end, holes stay at ±1 in and ±3 in); finer hole-edge seeding to clear the distorted elements; field output at 10 points instead of every increment (the ODB had reached 2.6 GB) |
| `fix_ProjectBeam_v3.py` | `fix_ProjectBeam_v9.py` | `Beam_8p2in` | New job name (an old lock file blocked `Beam_Fixed`); progress log file; 8 mesh variations tried |
| `fix_ProjectBeam_v4.py` | `fix_ProjectBeam_v10.py` | `Beam_8p2in` | Two-stage mesh fix: a global seed sweep, then ignoring tangent seams, which brought the distorted elements from 15 to 0; local hole-edge seeding removed because it made the mesh worse |
| `fix_ProjectBeam_v5.py` | `fix_ProjectBeam_v11.py` | `Beam_8p2in` | Contact surfaces built from mesh faces, so they cover only the roller contact strips; v4's seam merge had spread them over the whole flange skin |

## Post-processing: `FOS_ProjectBeam_v1` → `v3`

| File | Reads | What it does |
|---|---|---|
| `FOS_ProjectBeam_v1.py` | `Beam_Fixed.odb` | Offset-method FoS (0.02 in offset) for the first repaired model |
| `FOS_ProjectBeam_v2.py` | `Beam_8p2in.odb` | Same method for the 8.2 in beam, with a length check |
| `FOS_ProjectBeam_v3.py` | every `.odb` in the work directory | Comparison table, weight from the mesh, CSV per job, overlay plot. Current version: lives in `abaqus/python/` |

Versions before `v1` were overwritten during development and no longer exist.
