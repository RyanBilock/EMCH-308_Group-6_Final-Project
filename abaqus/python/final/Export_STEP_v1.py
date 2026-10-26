# -*- coding: utf-8 -*-
"""
Export_STEP_v1.py  --  EMCH 308 Team 6, export the final beam as a STEP file
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> the project folder (or any folder in it,
                                        e.g. abaqus\\final_design)
    2. File > Run Script...          -> Export_STEP_v1.py
    The script opens abaqus\\final_design\\Stock1_Drilled_v2.cae read-only (it
    never saves the .cae), checks the beam, and writes

        cad\\USC06_MTC06_IBeam_RevA.step      (the Beam part only, solid geometry)

    plus cad\\USC06_MTC06_IBeam_RevA_export_log.txt with the checks below.

WHAT IT EXPORTS
    Only the part "Beam": Stock 1 (AA I 3 x 2.03), 8.20 in, 4 x dia 1.00 web
    holes and 28 x dia 25/32 flange holes.  The rollers (rigid surfaces), mesh,
    contact and loads are not part of a STEP file.

CHECKS BEFORE AND AFTER EXPORT
    * bounding box 8.20 x 2.50 x 3.00 in
    * volume 10.19 in^3 (0.993 lb at 0.0975 lb/in^3)
    * 4 holes of dia 1.00 and 28 of dia 0.78125 (counted from circular edges;
      a mismatch here is only a note, the box and volume checks stop the export)
    * the written file starts with the STEP header "ISO-10303-21"
    If this Abaqus build cannot write STEP, the script writes ACIS (.sat) and
    IGES (.igs) copies instead and says so; SolidWorks and most CAD programs
    open both.

UNITS
    The model is in inches.  STEP files from Abaqus carry no unit, so choose
    INCHES when importing the file into SolidWorks or another CAD program.
"""
from __future__ import print_function

import os
import math

from abaqus import *
from abaqusConstants import *

try:
    import builtins as _py_builtins          # Python 3 (Abaqus 2024+)
except ImportError:
    import __builtin__ as _py_builtins       # Python 2.7 (older Abaqus)
sum = _py_builtins.sum
abs = _py_builtins.abs
min = _py_builtins.min
max = _py_builtins.max
round = _py_builtins.round

# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------
CAE_NAME   = 'Stock1_Drilled_v2.cae'
PART_NAME  = 'Beam'
OUT_NAME   = 'USC06_MTC06_IBeam_RevA'      # README revision scheme
RHO        = 0.0975                        # lb/in^3, 6061
EXPECT_BOX = (2.50, 3.00, 8.20)            # in, x (flange width), y (height), z (length)
EXPECT_VOL = 10.189                        # in^3 (Stock1_Drilled_v2 log: 10.1893)
EXPECT_HOLES = {1.00: 4, 0.78125: 28}      # diameter (in): count
TOL_BOX, TOL_VOL = 0.01, 0.05              # in, in^3

LOG = []


def log(text):
    line = '[Export_STEP] ' + text
    print(line)
    LOG.append(line)


# ---------------------------------------------------------------------------
# 1. find the project folder and the final model
# ---------------------------------------------------------------------------
def find_root(start):
    d = start
    for _ in range(6):
        if os.path.isdir(os.path.join(d, 'abaqus')) and os.path.isdir(os.path.join(d, 'cad')):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    return None


here = os.getcwd()
root = find_root(here)
candidates = [os.path.join(here, CAE_NAME), os.path.join(here, 'final_design', CAE_NAME)]
if root:
    candidates.insert(0, os.path.join(root, 'abaqus', 'final_design', CAE_NAME))
cae_path = None
for c in candidates:
    if os.path.isfile(c):
        cae_path = c
        break
if cae_path is None:
    raise RuntimeError('%s not found.  Set the work directory to the project folder '
                       '(the one holding abaqus\\ and cad\\) and run again.' % CAE_NAME)
cad_dir = os.path.join(root, 'cad') if root else os.path.dirname(cae_path)
if not os.path.isdir(cad_dir):
    os.makedirs(cad_dir)

log('=' * 60)
log('Opening %s (read-only; the .cae is not saved)' % cae_path)
try:
    mdb = openMdb(pathName=cae_path, readOnly=True)
except TypeError:
    mdb = openMdb(pathName=cae_path)

model = None
for mname in mdb.models.keys():
    if PART_NAME in mdb.models[mname].parts.keys():
        model = mdb.models[mname]
        break
if model is None:
    raise RuntimeError('No part named "%s" in %s.' % (PART_NAME, CAE_NAME))
p = model.parts[PART_NAME]
log('Model "%s", part "%s"' % (model.name, PART_NAME))

# ---------------------------------------------------------------------------
# 2. checks on the geometry
# ---------------------------------------------------------------------------
problems = []
vs = [v.pointOn[0] for v in p.vertices]
lo = [min(v[i] for v in vs) for i in range(3)]
hi = [max(v[i] for v in vs) for i in range(3)]
box = [hi[i] - lo[i] for i in range(3)]
log('Bounding box: %.4f x %.4f x %.4f in (x width, y height, z length)' % tuple(box))
for got, want, nm in zip(box, EXPECT_BOX, ('width', 'height', 'length')):
    if abs(got - want) > TOL_BOX:
        problems.append('%s is %.4f in, expected %.2f in' % (nm, got, want))

vol = p.getVolume()
log('Volume: %.4f in^3  ->  %.3f lb at %.4f lb/in^3' % (vol, vol * RHO, RHO))
if abs(vol - EXPECT_VOL) > TOL_VOL:
    problems.append('volume is %.4f in^3, expected about %.3f in^3' % (vol, EXPECT_VOL))

# holes: each through-hole is bounded by circles (possibly split into arcs);
# group circular edges by centre and radius
holes = {}
n_circ = 0
for e in p.edges:
    try:
        r = e.getRadius()
    except Exception:
        continue
    if r is None or r <= 0:
        continue
    n_circ += 1
    d = round(2.0 * r, 4)
    holes.setdefault(d, 0)
    holes[d] += 1
found = {}
for d_exp, n_exp in EXPECT_HOLES.items():
    # each through hole has two rims; a rim may be split into 2 arcs
    n_edges = sum(n for d, n in holes.items() if abs(d - d_exp) < 1.0e-3)
    found[d_exp] = n_edges
    log('Circular edges of dia %.5f: %d  (%d holes expected -> %d-%d edges)'
        % (d_exp, n_edges, n_exp, 2 * n_exp, 4 * n_exp))
    if n_circ and not (2 * n_exp <= n_edges <= 4 * n_exp):
        log('NOTE: unexpected edge count for dia %.5f (edges can be split differently '
            'in some builds); check the hole count after import.' % d_exp)
if not n_circ:
    log('NOTE: this Abaqus build gives no edge radii; hole count not checked.')

if problems:
    for pr in problems:
        log('CHECK FAILED: ' + pr)
    raise RuntimeError('The beam in %s does not match the final design:\n  - %s\n'
                       'Nothing was exported.' % (CAE_NAME, '\n  - '.join(problems)))
log('Geometry checks passed.')

# ---------------------------------------------------------------------------
# 3. export
# ---------------------------------------------------------------------------
def is_step(path):
    try:
        fh = open(path, 'r')
        head = fh.read(200)
        fh.close()
        return 'ISO-10303-21' in head
    except Exception:
        return False


step_path = os.path.join(cad_dir, OUT_NAME + '.step')
written = []
try:
    if os.path.exists(step_path):
        os.remove(step_path)
    p.writeStepFile(fileName=step_path)
    if os.path.isfile(step_path) and is_step(step_path):
        written.append(step_path)
        log('STEP written: %s (%.0f kB)' % (step_path, os.path.getsize(step_path) / 1024.0))
    else:
        log('NOTE: writeStepFile ran but no valid STEP file appeared.')
except Exception as err:
    log('NOTE: STEP export not available in this Abaqus build (%s).' % err)

if not written:
    sat = os.path.join(cad_dir, OUT_NAME + '.sat')
    igs = os.path.join(cad_dir, OUT_NAME + '.igs')
    try:
        p.writeAcisFile(fileName=sat)
        written.append(sat)
        log('ACIS written instead: %s' % sat)
    except Exception as err:
        log('NOTE: ACIS export failed (%s).' % err)
    try:
        p.writeIgesFile(fileName=igs, flavor=STANDARD)
        written.append(igs)
        log('IGES written instead: %s' % igs)
    except Exception as err:
        log('NOTE: IGES export failed (%s).' % err)
    if not written:
        raise RuntimeError('No CAD file could be written.  Use File > Export > Part and '
                           'choose STEP with the Beam part selected.')
    log('Open the .sat or .igs in SolidWorks/Fusion and save it as STEP (units: inches).')

log('Done.  Import with units = INCHES; the beam should measure 8.20 x 2.50 x 3.00 in '
    'and show 32 holes.')
try:
    fh = open(os.path.join(cad_dir, OUT_NAME + '_export_log.txt'), 'w')
    fh.write('\n'.join(LOG) + '\n')
    fh.close()
except Exception:
    pass
