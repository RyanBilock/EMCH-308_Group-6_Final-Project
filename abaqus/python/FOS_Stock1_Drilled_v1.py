# -*- coding: utf-8 -*-
"""
FOS_Stock1_Drilled_v1.py  --  EMCH 308 Team 6, factor of safety of the Stock 1 drilled beam
==============================================================================

HOW TO RUN (Abaqus/CAE), after Stock1_Drilled_Job_v1.py has finished
    1. File > Set Work Directory... -> anywhere in the project folder
                                       (the project folder, abaqus\\ or
                                       abaqus\\Stock1_Drilled\\ all work)
    2. File > Run Script...         -> FOS_Stock1_Drilled_v1.py
    The script finds Stock1_Drilled.odb, prints the result in the message
    area, draws the load-displacement curve with its offset line, and saves
    to  results\\Stock1_Drilled\\ :
        FOS_Stock1_Drilled.txt            summary and pass/fail
        FOS_Stock1_Drilled_LoadDisp.csv   travel, load, offset line
        Stock1_Drilled_LoadDisp.png       the plot (when the image export works)

METHOD (project spec, offset method)
    P     = |RF2| at the top-roller reference point (lbf)
    delta = |U2|  at the top-roller reference point (in)
    k     = elastic slope, least-squares fit between 15 % and 45 % of peak load
    Offset line: P = k (delta - delta0 - 0.02 in), delta0 = contact seating
    FOS = P_offset / 5000 lbf        requirement: FOS >= 1.25 (P_offset >= 6250 lbf)
    Weight from the analysed mesh: tet volumes x 0.0975 lb/in^3 (6061).
    Peak von Mises stress is reported at the saved frame closest to 5000 lbf.
UNITS: model in kip, in (stress in ksi); results in lbf, in, lb, ksi.
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

ODB_NAME     = 'Stock1_Drilled.odb'
JOB_LABEL    = 'Stock1_Drilled'
STEP_NAME    = 'Load'
P_DESIGN     = 5000.0     # lbf
FOS_REQUIRED = 1.25
OFFSET       = 0.02       # in
LOAD_TO_LBF  = 1000.0     # model force unit is kip
RHO          = 0.0975     # lb/in^3, 6061 aluminium
W_LIMIT      = 1.0        # lb
COST_PLAN    = 510.0      # $, cost sheet estimate for plan A+B (Cost_Plan_Stock1_v2.png)
COST_LIMIT   = 600.0      # $
FIT_LO, FIT_HI = 0.15, 0.45


def log(text):
    print('[FOS_Stock1_Drilled] ' + text)


def tet_volume(c):
    a, b, d, e = c[0], c[1], c[2], c[3]
    u = [b[i] - a[i] for i in range(3)]
    v = [d[i] - a[i] for i in range(3)]
    w = [e[i] - a[i] for i in range(3)]
    det = (u[0] * (v[1] * w[2] - v[2] * w[1]) - u[1] * (v[0] * w[2] - v[2] * w[0])
           + u[2] * (v[0] * w[1] - v[1] * w[0]))
    return abs(det) / 6.0


def offset_fos(D, P):
    """Offset-method result from travel D (in) and load P (lbf) lists."""
    n = len(P)
    P_max = max(P)
    i_pk = P.index(P_max)
    pts = [(D[i], P[i]) for i in range(i_pk + 1) if FIT_LO * P_max <= P[i] <= FIT_HI * P_max]
    if len(pts) < 3:
        pts = [(D[i], P[i]) for i in range(1, min(6, n))]
    mx = sum(d for d, _ in pts) / len(pts)
    my = sum(q for _, q in pts) / len(pts)
    k = sum((d - mx) * (q - my) for d, q in pts) / sum((d - mx) ** 2 for d, _ in pts)
    d0 = mx - my / k
    gap = lambda i: P[i] - k * (D[i] - d0 - OFFSET)
    P_off = d_off = None
    for i in range(1, n):
        if gap(i - 1) > 0.0 >= gap(i):
            f = gap(i - 1) / (gap(i - 1) - gap(i))
            P_off = P[i - 1] + f * (P[i] - P[i - 1])
            d_off = D[i - 1] + f * (D[i] - D[i - 1])
            break
    return dict(k=k, d0=d0, P_max=P_max, P_off=P_off, d_off=d_off,
                fos=(P_off if P_off is not None else P_max) / P_DESIGN,
                lower_bound=P_off is None)


def find_odb():
    here = os.getcwd()
    tries = [here, os.path.join(here, 'Stock1_Drilled'),
             os.path.join(here, 'abaqus', 'Stock1_Drilled'), os.path.join(here, 'abaqus')]
    up = os.path.dirname(here)
    tries += [os.path.join(up, 'Stock1_Drilled'), os.path.join(up, 'abaqus', 'Stock1_Drilled')]
    for d in tries:
        f = os.path.join(d, ODB_NAME)
        if os.path.isfile(f):
            return f
    raise RuntimeError('%s not found near %s.  Run Stock1_Drilled_Job_v1.py and wait for '
                       '"Completed", or set the work directory to the project folder.'
                       % (ODB_NAME, here))


def project_root(start):
    """Walk up from the .odb to the folder that holds abaqus\\ (the project root)."""
    d = start
    for _ in range(4):
        if os.path.isdir(os.path.join(d, 'abaqus')) or os.path.isdir(os.path.join(d, 'results')):
            return d
        d = os.path.dirname(d)
    return os.path.dirname(start)


def job_status(odb_path):
    sta = os.path.splitext(odb_path)[0] + '.sta'
    try:
        txt = open(sta).read()
    except Exception:
        return 'unknown (no .sta file)'
    if 'COMPLETED SUCCESSFULLY' in txt:
        return 'completed successfully'
    if 'NOT BEEN COMPLETED' in txt:
        return 'stopped early'
    return 'still running or stopped'


# --------------------------------------------------------------------------
# read the ODB
# --------------------------------------------------------------------------
odb_path = find_odb()
log('Reading %s' % odb_path)
status = job_status(odb_path)
if os.path.exists(os.path.splitext(odb_path)[0] + '.lck'):
    log('WARNING: %s.lck exists, so the job may still be running; the numbers below '
        'cover only the increments finished so far.' % JOB_LABEL)

for key in list(session.odbs.keys()):
    if os.path.normcase(os.path.abspath(key)) == os.path.normcase(odb_path):
        session.odbs[key].close()
odb = openOdb(path=odb_path, readOnly=True)
mises = None
try:
    if STEP_NAME not in odb.steps.keys():
        raise RuntimeError('Step "%s" is not in the ODB.' % STEP_NAME)
    step = odb.steps[STEP_NAME]
    rf2 = u2 = None
    for region in step.historyRegions.values():
        outs = region.historyOutputs
        if 'RF2' in outs.keys() and 'U2' in outs.keys():
            if max(abs(v) for _, v in outs['U2'].data) > 1.0e-6:
                rf2, u2 = outs['RF2'].data, outs['U2'].data
                break
    if rf2 is None:
        raise RuntimeError('No RF2/U2 history at the top roller in the ODB.')
    done = step.frames[-1].frameValue if len(step.frames) else 0.0

    length = vol = None
    beam_inst = None
    for iname, inst in odb.rootAssembly.instances.items():
        if iname.upper().startswith('BEAM'):
            beam_inst = inst
            xyz = dict((n.label, n.coordinates) for n in inst.nodes)
            zs = [c[2] for c in xyz.values()]
            length = max(zs) - min(zs)
            vol = 0.0
            for el in inst.elements:
                con = el.connectivity
                if len(con) >= 4:
                    vol += tet_volume([xyz[con[i]] for i in range(4)])
            break

    # peak von Mises at the saved frame closest to the design load
    try:
        hist = dict((round(t, 6), abs(v) * LOAD_TO_LBF) for t, v in rf2)
        times = sorted(hist.keys())
        best = None
        for fr in step.frames:
            if fr.frameValue <= 0.0 or 'S' not in fr.fieldOutputs.keys():
                continue
            t = min(times, key=lambda x: abs(x - fr.frameValue))
            dP = abs(hist[t] - P_DESIGN)
            if best is None or dP < best[0]:
                best = (dP, fr, hist[t])
        if best is not None:
            S = best[1].fieldOutputs['S']
            if beam_inst is not None:
                S = S.getSubset(region=beam_inst)
            smax = max(v.mises for v in S.values)
            mises = (smax, best[2], best[1].frameValue)
    except Exception as err:
        log('NOTE: stress check skipped (%s).' % err)
finally:
    odb.close()

D = [abs(v) for _, v in u2]
P = [abs(v) * LOAD_TO_LBF for _, v in rf2]
r = offset_fos(D, P)
weight = vol * RHO if vol else None

# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------
w_ok = weight is not None and weight <= W_LIMIT
f_ok = r['fos'] >= FOS_REQUIRED
c_ok = COST_PLAN <= COST_LIMIT
lines = [
    'FACTOR OF SAFETY - Stock 1 drilled plan (A+B)',
    'ODB: %s' % odb_path,
    'Job status: %s; step %.0f %% complete' % (status, 100.0 * done),
    '',
    'Beam length analysed      = %s in' % ('%.3f' % length if length else '?'),
    'Weight (from mesh)        = %s lb    limit %.2f lb   -> %s'
    % ('%.3f' % weight if weight else '?', W_LIMIT, 'PASS' if w_ok else 'FAIL'),
    'Elastic slope k           = %.0f lbf/in' % r['k'],
    'Peak load reached         = %.0f lbf' % r['P_max'],
    ('Offset-line load          = %.0f lbf at %.4f in travel' % (r['P_off'], r['d_off'])
     if r['P_off'] is not None else
     'Offset-line load          > %.0f lbf (curve never reached the offset line)' % r['P_max']),
    'FOS = P_offset / %.0f     = %s%.3f    required >= %.2f (P >= %.0f lbf)   -> %s'
    % (P_DESIGN, '> ' if r['lower_bound'] else '', r['fos'], FOS_REQUIRED,
       FOS_REQUIRED * P_DESIGN, 'PASS' if f_ok else 'FAIL'),
]
if mises:
    lines.append('Peak von Mises at %.0f lbf = %.1f ksi (saved frame at step time %.2f)'
                 % (mises[1], mises[0], mises[2]))
lines += [
    'Cost (cost-sheet estimate) = $%.0f    limit $%.0f   -> %s'
    % (COST_PLAN, COST_LIMIT, 'PASS' if c_ok else 'FAIL'),
    '',
    'OVERALL: %s' % ('MEETS weight, strength and cost' if (w_ok and f_ok and c_ok)
                     else 'does NOT meet every requirement (see FAIL lines)'),
]
if done < 1.0:
    lines.append('NOTE: the step did not finish; rerun the job before using these numbers.')
if r['lower_bound']:
    lines.append('NOTE: "> value" is a lower bound: the load never crossed the offset line '
                 'within the 0.08 in travel.')
for l in lines:
    log(l)

root = project_root(os.path.dirname(odb_path))
out_dir = os.path.join(root, 'results', JOB_LABEL)
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
fh = open(os.path.join(out_dir, 'FOS_%s.txt' % JOB_LABEL), 'w')
fh.write('\n'.join(lines) + '\n')
fh.close()
fh = open(os.path.join(out_dir, 'FOS_%s_LoadDisp.csv' % JOB_LABEL), 'w')
fh.write('travel_in,load_lbf,offset_line_lbf\n')
for i in range(len(D)):
    fh.write('%.6f,%.2f,%.2f\n' % (D[i], P[i], max(0.0, r['k'] * (D[i] - r['d0'] - OFFSET))))
fh.close()
log('Saved FOS_%s.txt and FOS_%s_LoadDisp.csv in %s' % (JOB_LABEL, JOB_LABEL, out_dir))

# --------------------------------------------------------------------------
# plot in the viewport, then export it as a PNG
# --------------------------------------------------------------------------
try:
    for nm in ('LD_' + JOB_LABEL, 'OFF_' + JOB_LABEL):
        if nm in session.xyDataObjects.keys():
            del session.xyDataObjects[nm]
    c1 = session.XYData(name='LD_' + JOB_LABEL, data=tuple(zip(D, P)),
                        xValuesLabel='Top-roller travel (in)', yValuesLabel='Load (lbf)',
                        legendLabel='FEA load-displacement')
    d_end = max(D)
    c2 = session.XYData(name='OFF_' + JOB_LABEL,
                        data=((r['d0'] + OFFSET, 0.0),
                              (d_end, r['k'] * (d_end - r['d0'] - OFFSET))),
                        legendLabel='0.02 in offset line')
    plot_name = 'FOS_' + JOB_LABEL
    if plot_name in session.xyPlots.keys():
        del session.xyPlots[plot_name]
    xyp = session.XYPlot(name=plot_name)
    xyp.title.setValues(text='Stock 1 drilled beam: FOS %s%.2f'
                        % ('> ' if r['lower_bound'] else '', r['fos']))
    chart = xyp.charts[list(xyp.charts.keys())[0]]
    cu1, cu2 = session.Curve(xyData=c1), session.Curve(xyData=c2)
    try:
        cu2.lineStyle.setValues(style=DASHED)
    except Exception:
        pass
    chart.setValues(curvesToPlot=(cu1, cu2))
    vp = session.viewports[session.currentViewportName]
    vp.setValues(displayedObject=xyp)
    log('Plot "%s" shown in the viewport.' % plot_name)
    try:
        png = os.path.join(out_dir, '%s_LoadDisp' % JOB_LABEL)
        session.printOptions.setValues(vpDecorations=OFF, reduceColors=False)
        session.printToFile(fileName=png, format=PNG, canvasObjects=(vp,))
        log('Saved %s.png' % png)
    except Exception as err:
        log('NOTE: PNG export skipped (%s); the CSV has the data.' % err)
except Exception as err:
    log('NOTE: plot skipped (%s); use the CSV file instead.' % err)
