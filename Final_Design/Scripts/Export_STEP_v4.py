# -*- coding: utf-8 -*-
"""
Export_STEP_v4.py  --  EMCH 308 Team 6, export the Rev C beam as a STEP file
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> any folder inside the repo
                                        (e.g. abaqus/base_models/)
    2. File > Run Script...          -> abaqus/python/final/Export_STEP_v4.py
    The script opens abaqus/final_design/Stock1_RevC_v1.cae read-only (it never
    saves the .cae), checks the beam, and writes

        cad/USC06_MTC06_IBeam_RevC.step      (the Beam part only, solid geometry)

    plus cad/USC06_MTC06_IBeam_RevC_export_log.txt with the checks below.
    If Stock1_RevC_v1.cae is not there it uses Stock1_RevC_v2.cae (same beam).

CHANGE FROM v3 (Rev B)
    * Exports Rev C: 8.40 in, 4 x dia 1.03 web holes, 0.65 in flange notches
      with R0.25 inside corners, full-width pads under the three rollers.
    * File name Rev C (Rev A = Stock 3 and Rev B = drilled Stock 1 already exist).
    * Checks updated: box 8.40 x 2.50 x 3.00, volume 9.3252 in^3, 4 web holes,
      and the R0.25 notch corners counted.
    Unchanged from v3: Abaqus labels STEP files MILLIMETRE although the model
    is in inches, so the unit is rewritten to INCH (1 in = 25.4 mm) and the file
    is re-read to confirm it.  The geometry numbers are not changed.

WHAT IT EXPORTS
    Only the part "Beam".  The rollers (rigid surfaces), mesh, contact and loads
    are not part of a STEP file.

CHECKS BEFORE EXPORT (box and volume stop the export; edge counts are notes)
    * bounding box 2.50 x 3.00 x 8.40 in
    * volume 9.3252 in^3 (0.914 lb at 0.098 lb/in^3)
    * 4 web holes of dia 1.03 (8-16 circular edges)
    * R0.25 arcs: 8 notch corners x 2 flange faces = 16, plus the stock's
      4 web fillets seen at both beam ends = 8, so about 24 (split edges can
      change this; it is a note only)
    * the written file starts with the STEP header "ISO-10303-21"
    If this Abaqus build cannot write STEP, the script writes ACIS (.sat) and
    IGES (.igs) copies instead and says so.

UNITS
    The STEP file is labelled INCH, so SolidWorks/Creo/Fusion import it at the
    right size (8.40 x 2.50 x 3.00 in).  Still check one dimension after import.
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
CAE_NAMES  = ('Stock1_RevC_v1.cae', 'Stock1_RevC_v2.cae')   # first one found is used
PART_NAME  = 'Beam'
OUT_NAME   = 'USC06_MTC06_IBeam_RevC'      # Rev A = Stock 3, Rev B = drilled Stock 1, Rev C = this
RHO        = 0.098                         # lb/in^3, 6061 (cost-sheet basis)
EXPECT_BOX = (2.50, 3.00, 8.40)            # in, x (flange width), y (height), z (length)
EXPECT_VOL = 9.3252                        # in^3 (Stock1_RevC_v1 log: 9.3252)
EXPECT_HOLES = {1.03: 4}                   # diameter (in): count (web holes)
EXPECT_R025_ARCS = 24                      # notch corners (16) + stock fillet ends (8); note only
TOL_BOX, TOL_VOL = 0.01, 0.03              # in, in^3

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
candidates = []
for nm in CAE_NAMES:
    if root:
        candidates.append(os.path.join(root, 'abaqus', 'final_design', nm))
    candidates += [os.path.join(here, nm), os.path.join(here, 'final_design', nm)]
cae_path = None
for c in candidates:
    if os.path.isfile(c):
        cae_path = c
        break
if cae_path is None:
    raise RuntimeError('%s not found.  Set the work directory to a folder inside the repo '
                       '(the one holding abaqus/ and cad/) and run again.' % ' or '.join(CAE_NAMES))
CAE_NAME = os.path.basename(cae_path)
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
if n_circ:
    n_r = sum(n for d, n in holes.items() if abs(d - 0.50) < 1.0e-3)
    log('R0.25 arcs (notch corners + stock fillet ends): %d  (about %d expected)'
        % (n_r, EXPECT_R025_ARCS))
    if n_r < 16:
        log('NOTE: fewer R0.25 arcs than the 16 notch corners; check the notches after import.')
else:
    log('NOTE: this Abaqus build gives no edge radii; hole count not checked.')

if problems:
    for pr in problems:
        log('CHECK FAILED: ' + pr)
    raise RuntimeError('The beam in %s does not match Rev C:\n  - %s\n'
                       'Nothing was exported.' % (CAE_NAME, '\n  - '.join(problems)))
log('Geometry checks passed.')

# ---------------------------------------------------------------------------
# 3. export
# ---------------------------------------------------------------------------
def fix_step_units(path):
    """Relabel the STEP length unit from MILLIMETRE to INCH (values unchanged)."""
    import re
    fh = open(path, 'r')
    t = fh.read()
    fh.close()
    if "CONVERSION_BASED_UNIT('INCH'" in t:
        return 'already INCH'
    m = re.search(r"CONVERSION_BASED_UNIT\('MILLIMETRE',#(\d+)\)", t)
    if m:
        n = m.group(1)
        t = t.replace(m.group(0), "CONVERSION_BASED_UNIT('INCH',#%s)" % n)
        t, k = re.subn(r"(#%s=LENGTH_MEASURE_WITH_UNIT\(LENGTH_MEASURE\()1\.0*(?:E\+?0+)?(\),#\d+\);)" % n,
                       r"\g<1>25.4\g<2>", t)
        if k != 1:
            return 'NOT FIXED (unexpected unit block)'
    else:
        return 'NOT FIXED (no MILLIMETRE unit found)'
    t = re.sub(r"FILE_NAME\('[^']*'", "FILE_NAME('%s'" % os.path.basename(path), t, count=1)
    fh = open(path, 'w')
    fh.write(t)
    fh.close()
    fh = open(path, 'r')
    ok = "CONVERSION_BASED_UNIT('INCH'" in fh.read()
    fh.close()
    return 'INCH' if ok else 'NOT FIXED (re-read failed)'


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
        res = fix_step_units(step_path)
        log('STEP length unit: %s' % res)
        if not res.startswith(('INCH', 'already')):
            log('WARNING: set units to INCHES (Interpret, not Convert) when importing.')
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

log('Done.  The beam should import at 8.40 x 2.50 x 3.00 in with 4 web holes '
    'and 6 flange notches (R0.25 corners).')
try:
    fh = open(os.path.join(cad_dir, OUT_NAME + '_export_log.txt'), 'w')
    fh.write('\n'.join(LOG) + '\n')
    fh.close()
except Exception:
    pass
