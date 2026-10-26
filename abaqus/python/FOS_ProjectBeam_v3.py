# -*- coding: utf-8 -*-
"""
FOS_ProjectBeam_v3.py  --  EMCH 308 Team 6, factor of safety for every job
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> the folder holding the job results
    2. File > Run Script...          -> FOS_ProjectBeam_v3.py
    Every .odb in the folder with an RF2/U2 history at the top roller is read
    (e.g. Stock1_Plain.odb, Stock1_Notched.odb, Beam_8p2in.odb).  A comparison
    table prints in the message area and is saved to FOS_Results_v3.txt; each
    job's load-displacement data goes to FOS_<job>_LoadDisp.csv.

METHOD (project spec, offset method)
    P     = |RF2| at the top-roller reference point (lbf)
    delta = |U2|  at the top-roller reference point (in)
    k     = elastic slope, least-squares fit between 15 % and 45 % of peak load
    Offset line: P = k (delta - delta0 - 0.02 in), delta0 = contact seating
    FOS = P_offset / 5000 lbf      (requirement: FOS >= 1.25)
    Weight is computed from the analysed mesh (tet volumes x 0.0975 lb/in^3).
UNITS: model in kip, in; results reported in lbf, in, lb.
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

STEP_NAME    = 'Load'
P_DESIGN     = 5000.0   # lbf
FOS_REQUIRED = 1.25
OFFSET       = 0.02     # in
LOAD_TO_LBF  = 1000.0   # model force unit is kip
RHO          = 0.0975   # lb/in^3, 6061 aluminium
W_LIMIT      = 1.0      # lb
FIT_LO, FIT_HI = 0.15, 0.45


def log(text):
    print('[FOS] ' + text)


def tet_volume(c):
    a, b, d, e = c[0], c[1], c[2], c[3]
    u = [b[i] - a[i] for i in range(3)]
    v = [d[i] - a[i] for i in range(3)]
    w = [e[i] - a[i] for i in range(3)]
    det = (u[0] * (v[1] * w[2] - v[2] * w[1]) - u[1] * (v[0] * w[2] - v[2] * w[0])
           + u[2] * (v[0] * w[1] - v[1] * w[0]))
    return abs(det) / 6.0


def analyse(path):
    name = os.path.splitext(os.path.basename(path))[0]
    for key in list(session.odbs.keys()):
        if os.path.normcase(os.path.abspath(key)) == os.path.normcase(path):
            session.odbs[key].close()
    odb = openOdb(path=path, readOnly=True)
    try:
        if STEP_NAME not in odb.steps.keys():
            return None
        step = odb.steps[STEP_NAME]
        rf2 = u2 = None
        for region in step.historyRegions.values():
            outs = region.historyOutputs
            if 'RF2' in outs.keys() and 'U2' in outs.keys():
                if max(abs(v) for _, v in outs['U2'].data) > 1.0e-6:
                    rf2, u2 = outs['RF2'].data, outs['U2'].data
                    break
        if rf2 is None:
            return None
        done = step.frames[-1].frameValue if len(step.frames) else 0.0
        length = vol = None
        for iname, inst in odb.rootAssembly.instances.items():
            if iname.upper().startswith('BEAM'):
                xyz = dict((n.label, n.coordinates) for n in inst.nodes)
                zs = [c[2] for c in xyz.values()]
                length = max(zs) - min(zs)
                vol = 0.0
                for el in inst.elements:
                    con = el.connectivity
                    if len(con) >= 4:
                        vol += tet_volume([xyz[con[i]] for i in range(4)])
    finally:
        odb.close()

    P = [abs(v) * LOAD_TO_LBF for _, v in rf2]
    D = [abs(v) for _, v in u2]
    n = len(P)
    P_max = max(P)
    i_pk = P.index(P_max)
    pts = [(D[i], P[i]) for i in range(i_pk + 1) if FIT_LO * P_max <= P[i] <= FIT_HI * P_max]
    if len(pts) < 3:
        pts = [(D[i], P[i]) for i in range(1, min(6, n))]
    mx = sum(d for d, _ in pts) / len(pts)
    my = sum(p for _, p in pts) / len(pts)
    k = sum((d - mx) * (p - my) for d, p in pts) / sum((d - mx) ** 2 for d, _ in pts)
    d0 = mx - my / k
    gap = lambda i: P[i] - k * (D[i] - d0 - OFFSET)
    P_off = d_off = None
    for i in range(1, n):
        if gap(i - 1) > 0.0 >= gap(i):
            f = gap(i - 1) / (gap(i - 1) - gap(i))
            P_off = P[i - 1] + f * (P[i] - P[i - 1])
            d_off = D[i - 1] + f * (D[i] - D[i - 1])
            break
    fos = (P_off if P_off is not None else P_max) / P_DESIGN
    fh = open(os.path.join(os.path.dirname(path), 'FOS_%s_LoadDisp.csv' % name), 'w')
    fh.write('travel_in,load_lbf,offset_line_lbf\n')
    for i in range(n):
        fh.write('%.6f,%.2f,%.2f\n' % (D[i], P[i], max(0.0, k * (D[i] - d0 - OFFSET))))
    fh.close()
    return dict(name=name, length=length, weight=(vol * RHO if vol else None), done=done,
                k=k, P_max=P_max, P_off=P_off, d_off=d_off, fos=fos,
                lower_bound=(P_off is None), D=D, P=P, d0=d0)


folder = os.getcwd()
odbs = sorted(f for f in os.listdir(folder) if f.lower().endswith('.odb'))
if not odbs:
    raise RuntimeError('No .odb files in %s.  Set the work directory to the results folder.'
                       % folder)
rows = []
for f in odbs:
    try:
        r = analyse(os.path.join(folder, f))
    except Exception as err:
        log('%s skipped (%s)' % (f, err))
        continue
    if r is None:
        log('%s skipped (no load/displacement history in step "%s").' % (f, STEP_NAME))
        continue
    rows.append(r)
if not rows:
    raise RuntimeError('No job results with RF2/U2 history were found.')

lines = ['FACTOR OF SAFETY COMPARISON  (offset method, %.2f in offset; design load %.0f lbf)'
         % (OFFSET, P_DESIGN),
         'Folder: %s' % folder, '',
         '%-18s %8s %9s %9s %12s %9s %8s  %s' % ('Job', 'Length', 'Weight', 'Complete',
                                                  'P_offset', 'FOS', 'Weight', 'FOS'),
         '%-18s %8s %9s %9s %12s %9s %8s  %s' % ('', '(in)', '(lb)', '', '(lbf)', '',
                                                  '<=1 lb', '>=1.25'),
         '-' * 92]
for r in rows:
    w_ok = r['weight'] is not None and r['weight'] <= W_LIMIT
    f_ok = r['fos'] >= FOS_REQUIRED
    lines.append('%-18s %8s %9s %8.0f%% %12s %9s %8s  %s' % (
        r['name'][:18],
        '%.3f' % r['length'] if r['length'] else '?',
        '%.3f' % r['weight'] if r['weight'] else '?',
        100.0 * r['done'],
        ('%.0f' % r['P_off']) if r['P_off'] is not None else '> %.0f' % r['P_max'],
        ('%.2f' % r['fos']) if not r['lower_bound'] else '> %.2f' % r['fos'],
        'PASS' if w_ok else 'FAIL',
        'PASS' if f_ok else 'FAIL'))
lines += ['', 'Notes:',
          '  "> value": the curve never reached the offset line, so the value is a lower bound.',
          '  Jobs below 100 % complete stopped early; rerun them before using the numbers.',
          '  Weight is from the analysed mesh, so it reflects the modelled geometry.']
for l in lines:
    log(l)
fh = open(os.path.join(folder, 'FOS_Results_v3.txt'), 'w')
fh.write('\n'.join(lines) + '\n')
fh.close()
log('Saved FOS_Results_v3.txt and FOS_<job>_LoadDisp.csv files in %s' % folder)

# plot every curve with its offset line
try:
    curves = []
    for r in rows:
        for nm in ('LD_' + r['name'], 'OFF_' + r['name']):
            if nm in session.xyDataObjects.keys():
                del session.xyDataObjects[nm]
        c1 = session.XYData(name='LD_' + r['name'], data=tuple(zip(r['D'], r['P'])))
        d_end = max(r['D'])
        c2 = session.XYData(name='OFF_' + r['name'],
                            data=((r['d0'] + OFFSET, 0.0),
                                  (d_end, r['k'] * (d_end - r['d0'] - OFFSET))))
        curves += [session.Curve(xyData=c1), session.Curve(xyData=c2)]
    if 'FOS_Compare' in session.xyPlots.keys():
        del session.xyPlots['FOS_Compare']
    xyp = session.XYPlot(name='FOS_Compare')
    chart = xyp.charts[list(xyp.charts.keys())[0]]
    chart.setValues(curvesToPlot=tuple(curves))
    session.viewports[session.currentViewportName].setValues(displayedObject=xyp)
    log('Plot "FOS_Compare": load (lbf) vs top-roller travel (in) with offset lines.')
except Exception as err:
    log('Plot skipped (%s); use the CSV files instead.' % err)
