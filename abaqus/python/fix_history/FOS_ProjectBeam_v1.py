# -*- coding: utf-8 -*-
"""
FOS_ProjectBeam_v1.py  --  EMCH 308 Team 6, factor of safety from the FEA run
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> the folder holding Beam_Fixed.odb
    2. File > Run Script...          -> FOS_ProjectBeam_v1.py
    Results print in the message area (lines start with [FOS]) and are saved
    to FOS_Results.txt and FOS_LoadDisp.csv in the same folder.

METHOD (project spec, offset method)
    P     = |RF2| at the top-roller reference point (load, lbf)
    delta = |U2|  at the top-roller reference point (roller travel, in)
    k     = elastic slope, least-squares fit of P vs delta between 15 % and
            45 % of the peak load (past the contact seating, before yield)
    Offset line: P_line = k (delta - 0.02 in)
    P_offset = load where the FEA curve meets the offset line
    FOS = P_offset / 5000 lbf      (requirement: FOS >= 1.25, P_offset >= 6250 lbf)
    If the curve never reaches the line, FOS > P_max / 5000 lbf (lower bound).

UNITS: the model is in kip and in; results are reported in lbf and in.
"""
from __future__ import print_function

import os

from abaqus import *
from abaqusConstants import *
from odbAccess import openOdb

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
# SETTINGS
# ---------------------------------------------------------------------------
ODB_NAME     = 'Beam_Fixed.odb'
STEP_NAME    = 'Load'
P_DESIGN     = 5000.0   # lbf  design load (spec)
FOS_REQUIRED = 1.25     #      required factor of safety (spec)
OFFSET       = 0.02     # in   offset displacement (spec)
LOAD_TO_LBF  = 1000.0   # model force unit is kip
FIT_LO, FIT_HI = 0.15, 0.45   # fit window as fractions of peak load


def log(text):
    print('[FOS] ' + text)


# ---------------------------------------------------------------------------
# 1. read RF2 and U2 history at the top roller
# ---------------------------------------------------------------------------
path = os.path.join(os.getcwd(), ODB_NAME)
if not os.path.exists(path):
    raise RuntimeError('%s not found in %s.  Set the work directory to the folder '
                       'holding the job results.' % (ODB_NAME, os.getcwd()))
for key in list(session.odbs.keys()):
    if os.path.normcase(os.path.abspath(key)) == os.path.normcase(path):
        session.odbs[key].close()
odb = openOdb(path=path, readOnly=True)
step = odb.steps[STEP_NAME]

rf2 = u2 = None
for name, region in step.historyRegions.items():
    outs = region.historyOutputs
    if 'RF2' in outs.keys() and 'U2' in outs.keys():
        cand_rf, cand_u = outs['RF2'].data, outs['U2'].data
        # top roller: the region whose U2 actually moves
        if max(abs(v) for _, v in cand_u) > 1.0e-6:
            rf2, u2 = cand_rf, cand_u
            log('History region: %s' % name)
            break
if rf2 is None:
    raise RuntimeError('No RF2/U2 history for the top roller in step "%s".' % STEP_NAME)

P = [abs(v) * LOAD_TO_LBF for _, v in rf2]
D = [abs(v) for _, v in u2]
odb.close()
n = len(P)
P_max = max(P)
log('%d points; peak load %.0f lbf at %.4f in travel.' % (n, P_max, D[P.index(P_max)]))

# ---------------------------------------------------------------------------
# 2. elastic slope (least squares in the fit window)
# ---------------------------------------------------------------------------
i_peak = P.index(P_max)
pts = [(D[i], P[i]) for i in range(i_peak + 1)
       if FIT_LO * P_max <= P[i] <= FIT_HI * P_max]
if len(pts) < 3:
    pts = [(D[i], P[i]) for i in range(1, min(6, n))]
mx = sum(d for d, _ in pts) / len(pts)
my = sum(p for _, p in pts) / len(pts)
sxx = sum((d - mx) ** 2 for d, _ in pts)
k = sum((d - mx) * (p - my) for d, p in pts) / sxx
d0 = mx - my / k                  # where the elastic line crosses P = 0
log('Elastic slope k = %.0f lbf/in from %d points (seating offset %.4f in).'
    % (k, len(pts), d0))

# ---------------------------------------------------------------------------
# 3. intersection with the offset line  P_line = k (delta - d0 - OFFSET)
# ---------------------------------------------------------------------------
def gap(i):
    return P[i] - k * (D[i] - d0 - OFFSET)


P_off = None
for i in range(1, n):
    if gap(i - 1) > 0.0 >= gap(i):
        f = gap(i - 1) / (gap(i - 1) - gap(i))
        P_off = P[i - 1] + f * (P[i] - P[i - 1])
        d_off = D[i - 1] + f * (D[i] - D[i - 1])
        break

lines = ['FACTOR OF SAFETY - %s (offset method, %.3f in offset)' % (ODB_NAME, OFFSET),
         '  elastic slope k        = %.0f lbf/in' % k,
         '  peak load reached      = %.0f lbf' % P_max]
if P_off is not None:
    fos = P_off / P_DESIGN
    lines += ['  offset-line load       = %.0f lbf at %.4f in travel' % (P_off, d_off),
              '  FOS = %.0f / %.0f     = %.3f' % (P_off, P_DESIGN, fos)]
else:
    fos = P_max / P_DESIGN
    lines += ['  curve did not reach the offset line within the run;',
              '  FOS > %.0f / %.0f     = %.3f  (lower bound; raise U_TARGET to find it)'
              % (P_max, P_DESIGN, fos)]
verdict = 'PASS' if fos >= FOS_REQUIRED else 'FAIL'
lines.append('  required FOS >= %.2f (load >= %.0f lbf)  ->  %s'
             % (FOS_REQUIRED, FOS_REQUIRED * P_DESIGN, verdict))
for l in lines:
    log(l)

out_dir = os.path.dirname(path)
fh = open(os.path.join(out_dir, 'FOS_Results.txt'), 'w')
fh.write('\n'.join(lines) + '\n')
fh.close()
fh = open(os.path.join(out_dir, 'FOS_LoadDisp.csv'), 'w')
fh.write('travel_in,load_lbf,offset_line_lbf\n')
for i in range(n):
    fh.write('%.6f,%.2f,%.2f\n' % (D[i], P[i], max(0.0, k * (D[i] - d0 - OFFSET))))
fh.close()
log('Saved FOS_Results.txt and FOS_LoadDisp.csv in %s' % out_dir)

# ---------------------------------------------------------------------------
# 4. plot in CAE (curve + offset line)
# ---------------------------------------------------------------------------
try:
    for nm in ('FOS_LoadDisp', 'FOS_OffsetLine'):
        if nm in session.xyDataObjects.keys():
            del session.xyDataObjects[nm]
    c1 = session.XYData(name='FOS_LoadDisp', data=tuple(zip(D, P)))
    d_end = max(D)
    c2 = session.XYData(name='FOS_OffsetLine',
                        data=((d0 + OFFSET, 0.0), (d_end, k * (d_end - d0 - OFFSET))))
    if 'FOS_Plot' in session.xyPlots.keys():
        del session.xyPlots['FOS_Plot']
    xyp = session.XYPlot(name='FOS_Plot')
    chart = xyp.charts[list(xyp.charts.keys())[0]]
    chart.setValues(curvesToPlot=(session.Curve(xyData=c1), session.Curve(xyData=c2)))
    session.viewports[session.currentViewportName].setValues(displayedObject=xyp)
    log('Plot "FOS_Plot" shown: load (lbf) vs top-roller travel (in) with the offset line.')
except Exception as err:
    log('Plot skipped (%s); use FOS_LoadDisp.csv instead.' % err)
