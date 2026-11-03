# -*- coding: utf-8 -*-
"""
FOS_Stock1_RevC_v3.py  --  EMCH 308 Team 6, Rev C: factor of safety, weight and accuracy
==============================================================================

WHAT IS NEW IN v3
    * Reads the warning-free rerun Stock1_RevC_v2 (fix_Stock1_RevC_v1.py,
      abaqus/final_design/job_v2/) when it exists, else Stock1_RevC_v1.
    * New SOLVER MESSAGES section: warnings and errors counted from the
      job's .msg/.dat, so you can confirm the rerun is clean.
    * When both v1 and v2 have run, it compares their FOS and stiffness
      (they should agree: the fixes do not change the physics).

WHAT WAS NEW IN v2
    * Plot fix: the offset line (and the mesh-check curve) now carry the same
      axis labels as the FEA curve, so Abaqus draws them on the same axes.
      In v1 the offset line got its own second x/y axes, so where it appeared
      to cross the curve on the PNG was wrong.  The numbers in the report and
      CSV were always correct (crossing found from the data, not the plot).

HOW TO RUN (Abaqus/CAE), after Stock1_RevC_v1.py's job reads "Completed"
    1. File > Set Work Directory... -> any folder inside the repo
                                       (e.g. abaqus/base_models/)
    2. File > Run Script...         -> abaqus/python/final/FOS_Stock1_RevC_v3.py
    It finds abaqus/final_design/job/Stock1_RevC_v1.odb (and, if it has been
    run, the mesh-check job in abaqus/final_design/mesh_check/), prints the
    report in the message area, plots the curves, and saves to
    results/final_design/:
        FOS_Stock1_RevC_v1.txt            report: requirements + accuracy checks
        FOS_Stock1_RevC_v1_LoadDisp.csv   travel, load, offset line (fine mesh)
        Stock1_RevC_v1_LoadDisp.png       plot (when the image export works)

WHAT IT REPORTS
    Requirements: weight <= 1.00 lb, FOS >= 1.25, cost <= $600.
    FOS (project spec, offset method):
        P = |RF2|, delta = |U2| at the top-roller reference point
        k = elastic slope, least-squares fit between 15 % and 45 % of peak load
        offset line P = k (delta - delta0 - 0.02 in); FOS = P_offset / 5000 lbf
    WEIGHT ACCURACY
        * Mesh volume with the curved 10-node elements integrated exactly
          (straight-sided tets are also shown: they overstate curved holes).
        * Compared with the exact CAD volume that Stock1_RevC_v1.py wrote to
          Stock1_RevC_v1_geometry.txt, and with the hand calculation (0.914 lb).
        * Given at 0.0975 lb/in^3 (Rev B reports) and 0.098 lb/in^3 (the
          2.03 lb/ft basis of the cost sheet).
    FOS ACCURACY
        * Sensitivity to the elastic-fit window (10-30 %, 15-45 %, 20-50 %).
        * Curve resolution at the offset-line crossing (points, step size).
        * Mesh convergence: fine mesh vs. the Rev B-density mesh-check job,
          when that job has been run (MESH_LEVEL = 'CHECK' in the build script).
    DEFORMATION AT THE TEST LOAD
        * Load where the curve first departs 1 % from its straight line.
        * At 6,250 lbf: departure from linear and the estimated permanent set
          after unloading.
        * Where plastic strain is largest at the offset-line load.
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

JOB_MAINS    = ('Stock1_RevC_v2', 'Stock1_RevC_v1')    # first one found is reported
JOB_CHECK    = 'Stock1_RevC_v1_MeshCheck'
REPO_ODB_DIR = {'Stock1_RevC_v2': ('abaqus', 'final_design', 'job_v2'),
                'Stock1_RevC_v1': ('abaqus', 'final_design', 'job'),
                JOB_CHECK: ('abaqus', 'final_design', 'mesh_check')}
RESULTS_DIR  = ('results', 'final_design')
STEP_NAME    = 'Load'
P_DESIGN     = 5000.0     # lbf
FOS_REQUIRED = 1.25
P_TEST       = FOS_REQUIRED * P_DESIGN   # 6,250 lbf
OFFSET       = 0.02       # in
LOAD_TO_LBF  = 1000.0     # model force unit is kip
RHO          = 0.0975     # lb/in^3, 6061 (Rev B reports)
RHO_SHEET    = 0.098      # lb/in^3, basis of the 2.03 lb/ft cost-sheet weight
W_LIMIT      = 1.0        # lb
W_HAND       = 0.914      # lb at 0.098 lb/in^3, Rev C hand calculation
COST         = 131.78     # $, course cost sheet (cost/ProjectCostSheet_RevC_Stock1_v2.xlsx)
COST_LIMIT   = 600.0      # $
FIT_WINDOWS  = ((0.10, 0.30), (0.15, 0.45), (0.20, 0.50))   # middle one is the reported FOS
FIT_MAIN     = (0.15, 0.45)
CONVERGED_FOS_PCT = 2.0   # mesh judged converged if FOS changes less than this ...
CONVERGED_K_PCT   = 3.0   # ... and the elastic slope less than this between meshes


def log(text):
    print('[FOS_Stock1_RevC] ' + text)


# --------------------------------------------------------------------------
# element volumes
# --------------------------------------------------------------------------
def tet_volume(c):
    a, b, d, e = c[0], c[1], c[2], c[3]
    u = [b[i] - a[i] for i in range(3)]
    v = [d[i] - a[i] for i in range(3)]
    w = [e[i] - a[i] for i in range(3)]
    det = (u[0] * (v[1] * w[2] - v[2] * w[1]) - u[1] * (v[0] * w[2] - v[2] * w[0])
           + u[2] * (v[0] * w[1] - v[1] * w[0]))
    return abs(det) / 6.0


# 5-point degree-3 rule on the unit tetrahedron (barycentric points, weights sum to 1)
_QP = [((0.25, 0.25, 0.25, 0.25), -0.8)] + \
      [(tuple(0.5 if i == j else 1.0 / 6.0 for i in range(4)), 0.45) for j in range(4)]
# C3D10 node order: corners 1-4, then mid-side 5(1-2) 6(2-3) 7(3-1) 8(1-4) 9(2-4) 10(3-4)
_EDGES = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))


def tet10_volume(c):
    """Exact volume of a curved 10-node tetrahedron (det J is cubic; the
    degree-3 rule integrates it exactly)."""
    vol = 0.0
    for L, w in _QP:
        dNdL = [[0.0] * 4 for _ in range(10)]
        for i in range(4):
            dNdL[i][i] = 4.0 * L[i] - 1.0
        for k, (i, j) in enumerate(_EDGES):
            dNdL[4 + k][i] = 4.0 * L[j]
            dNdL[4 + k][j] = 4.0 * L[i]
        J = [[0.0] * 3 for _ in range(3)]
        for n in range(10):
            g = [dNdL[n][m + 1] - dNdL[n][0] for m in range(3)]
            for a_ in range(3):
                for m in range(3):
                    J[a_][m] += c[n][a_] * g[m]
        det = (J[0][0] * (J[1][1] * J[2][2] - J[1][2] * J[2][1])
               - J[0][1] * (J[1][0] * J[2][2] - J[1][2] * J[2][0])
               + J[0][2] * (J[1][0] * J[2][1] - J[1][1] * J[2][0]))
        vol += w * abs(det)
    return vol / 6.0


# --------------------------------------------------------------------------
# curve analysis
# --------------------------------------------------------------------------
def where(c, length):
    """Plain-words location of a point (x, y, z) on the beam."""
    x, y, z = c
    zc = z - 0.5 * length
    part = 'top flange' if y > 1.24 else ('bottom flange' if y < -1.24 else
                                          ('web/fillet, upper half' if y > 0 else
                                           'web/fillet, lower half'))
    zone = ''
    if y > 0 and abs(zc) < 1.0:
        zone = ' (under the load roller)'
    elif y < 0 and abs(zc) > 3.3:
        zone = ' (over a support roller)'
    return '%s, %.2f in from mid-span%s' % (part, abs(zc), zone)


def offset_fos(D, P, window=FIT_MAIN):
    """Offset-method result from travel D (in) and load P (lbf) lists."""
    lo, hi = window
    n = len(P)
    P_max = max(P)
    i_pk = P.index(P_max)
    pts = [(D[i], P[i]) for i in range(i_pk + 1) if lo * P_max <= P[i] <= hi * P_max]
    if len(pts) < 3:
        pts = [(D[i], P[i]) for i in range(1, min(6, n))]
    mx = sum(d for d, _ in pts) / len(pts)
    my = sum(q for _, q in pts) / len(pts)
    k = sum((d - mx) * (q - my) for d, q in pts) / sum((d - mx) ** 2 for d, _ in pts)
    d0 = mx - my / k
    gap = lambda i: P[i] - k * (D[i] - d0 - OFFSET)
    P_off = d_off = None
    i_cross = None
    for i in range(1, n):
        if gap(i - 1) > 0.0 >= gap(i):
            f = gap(i - 1) / (gap(i - 1) - gap(i))
            P_off = P[i - 1] + f * (P[i] - P[i - 1])
            d_off = D[i - 1] + f * (D[i] - D[i - 1])
            i_cross = i
            break
    return dict(k=k, d0=d0, P_max=P_max, P_off=P_off, d_off=d_off, i_cross=i_cross,
                n_fit=len(pts), fos=(P_off if P_off is not None else P_max) / P_DESIGN,
                lower_bound=P_off is None)


def interp_at_load(D, P, P_target):
    """Travel where the curve first reaches P_target (None if it never does)."""
    for i in range(1, len(P)):
        if P[i - 1] < P_target <= P[i]:
            f = (P_target - P[i - 1]) / (P[i] - P[i - 1])
            return D[i - 1] + f * (D[i] - D[i - 1])
    return None


def linearity(D, P, r):
    """Departure of the curve from its straight elastic line."""
    k, d0, P_max = r['k'], r['d0'], r['P_max']
    first = {}
    for lim in (0.01, 0.02):
        for i in range(len(P)):
            if P[i] < FIT_MAIN[0] * P_max or D[i] <= d0:
                continue
            if 1.0 - P[i] / (k * (D[i] - d0)) >= lim:
                first[lim] = P[i]
                break
    d_test = interp_at_load(D, P, P_test_lbf())
    dev = set_ = None
    if d_test is not None:
        d_lin = P_test_lbf() / k + d0
        set_ = d_test - d_lin                      # plastic travel = permanent set on unloading
        dev = 1.0 - P_test_lbf() / (k * (d_test - d0))
    return dict(p_1pct=first.get(0.01), p_2pct=first.get(0.02), d_test=d_test,
                dev_test=dev, set_test=set_)


def P_test_lbf():
    return P_TEST


# --------------------------------------------------------------------------
# locating files
# --------------------------------------------------------------------------
def repo_root(start):
    """Walk up from start to the folder that holds both abaqus/ and results/."""
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, 'abaqus')) and os.path.isdir(os.path.join(d, 'results')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def find_odb(job, required):
    here = os.getcwd()
    up = os.path.dirname(here)
    root = repo_root(here)
    tries = [here, os.path.join(here, job), os.path.join(here, 'job'), os.path.join(here, 'job_v2'),
             os.path.join(here, 'mesh_check'), os.path.join(up, job)]
    if root:
        tries.insert(0, os.path.join(root, *REPO_ODB_DIR[job]))
    for d in tries:
        f = os.path.join(d, job + '.odb')
        if os.path.isfile(f):
            return f
    if required:
        raise RuntimeError('No %s.odb found (looked in %s first).  Run Stock1_RevC_v1.py, '
                           'wait for "Completed", and set the work directory to a folder '
                           'inside the repo.' % (job, tries[0]))
    return None


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


def solver_messages(odb_path):
    """Warning and error counts from the job's .msg summary (and .dat)."""
    import re
    out = dict(msg_warnings=None, msg_errors=None, neg_eig=None, dat_warnings=None)
    base = os.path.splitext(odb_path)[0]
    try:
        t = open(base + '.msg').read()
        m = re.findall(r'(\d+)\s+WARNING MESSAGES DURING ANALYSIS', t)
        e = re.findall(r'(\d+)\s+ERROR MESSAGES', t)
        n = re.findall(r'(\d+)\s+ANALYSIS WARNINGS ARE NEGATIVE EIGENVALUE', t)
        out['msg_warnings'] = int(m[-1]) if m else t.count('***WARNING')
        out['msg_errors'] = int(e[-1]) if e else t.count('***ERROR')
        out['neg_eig'] = int(n[-1]) if n else None
        kinds = {}
        for blk in re.findall(r'\*\*\*WARNING: ([^\n]+)', t):
            key = re.sub(r'\d+', '#', blk.strip())[:60]
            kinds[key] = kinds.get(key, 0) + 1
        out['kinds'] = kinds
    except Exception:
        pass
    try:
        t = open(base + '.dat').read()
        m = re.findall(r'(\d+)\s+WARNING MESSAGES DURING USER INPUT PROCESSING', t)
        out['dat_warnings'] = int(m[-1]) if m else None
    except Exception:
        pass
    return out


def read_geometry(odb_path, job):
    """key = value lines written by Stock1_RevC_v1.py next to the job."""
    f = os.path.join(os.path.dirname(odb_path), job + '_geometry.txt')
    out = {}
    try:
        for line in open(f):
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k_, v_ = [t.strip() for t in line.split('=', 1)]
            try:
                out[k_] = float(v_)
            except ValueError:
                out[k_] = v_
    except Exception:
        log('NOTE: %s not found; the CAD comparison is skipped.' % os.path.basename(f))
    return out


# --------------------------------------------------------------------------
# read one ODB
# --------------------------------------------------------------------------
def analyse(odb_path, job, detail=True):
    log('Reading %s' % odb_path)
    res = dict(job=job, odb=odb_path, status=job_status(odb_path), mises=None,
               yield_spots=[], vol=None, vol4=None, length=None, n_el=0, n_nodes=0)
    if os.path.exists(os.path.splitext(odb_path)[0] + '.lck'):
        log('WARNING: %s.lck exists, so the job may still be running; the numbers cover '
            'only the increments finished so far.' % job)
    for key in list(session.odbs.keys()):
        if os.path.normcase(os.path.abspath(key)) == os.path.normcase(odb_path):
            session.odbs[key].close()
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        if STEP_NAME not in odb.steps.keys():
            raise RuntimeError('Step "%s" is not in %s.' % (STEP_NAME, odb_path))
        step = odb.steps[STEP_NAME]
        rf2 = u2 = None
        for region in step.historyRegions.values():
            outs = region.historyOutputs
            if 'RF2' in outs.keys() and 'U2' in outs.keys():
                if max(abs(v) for _, v in outs['U2'].data) > 1.0e-6:
                    rf2, u2 = outs['RF2'].data, outs['U2'].data
                    break
        if rf2 is None:
            raise RuntimeError('No RF2/U2 history at the top roller in %s.' % odb_path)
        res['done'] = step.frames[-1].frameValue if len(step.frames) else 0.0
        res['D'] = [abs(v) for _, v in u2]
        res['P'] = [abs(v) * LOAD_TO_LBF for _, v in rf2]
        res['r'] = offset_fos(res['D'], res['P'])

        beam_inst, xyz = None, {}
        for iname, inst in odb.rootAssembly.instances.items():
            if iname.upper().startswith('BEAM'):
                beam_inst = inst
                xyz = dict((n.label, n.coordinates) for n in inst.nodes)
                zs = [c[2] for c in xyz.values()]
                res['length'] = max(zs) - min(zs)
                res['n_nodes'] = len(xyz)
                vol = vol4 = 0.0
                n_el = 0
                for el in inst.elements:
                    con = el.connectivity
                    n_el += 1
                    if len(con) == 10:
                        vol += tet10_volume([xyz[con[i]] for i in range(10)])
                        vol4 += tet_volume([xyz[con[i]] for i in range(4)])
                    elif len(con) >= 4:
                        v4 = tet_volume([xyz[con[i]] for i in range(4)])
                        vol += v4
                        vol4 += v4
                res['vol'], res['vol4'], res['n_el'] = vol, vol4, n_el
                break
        if not detail or beam_inst is None:
            return res

        # peak von Mises at the saved frame closest to the design load
        try:
            hist = [(t, abs(v) * LOAD_TO_LBF) for t, v in rf2]
            best = None
            for fr in step.frames:
                if fr.frameValue <= 0.0 or 'S' not in fr.fieldOutputs.keys():
                    continue
                Pf = min(hist, key=lambda h: abs(h[0] - fr.frameValue))[1]
                if best is None or abs(Pf - P_DESIGN) < best[0]:
                    best = (abs(Pf - P_DESIGN), fr, Pf)
            if best is not None:
                S = best[1].fieldOutputs['S'].getSubset(region=beam_inst)
                res['mises'] = (max(v.mises for v in S.values), best[2], best[1].frameValue)
        except Exception as err:
            log('NOTE: stress check skipped (%s).' % err)

        # where plastic strain is largest at the saved frame nearest the offset load
        try:
            r = res['r']
            P_ref = r['P_off'] if r['P_off'] is not None else r['P_max']
            hist = [(t, abs(v) * LOAD_TO_LBF) for t, v in rf2]
            fr_best = None
            for fr in step.frames:
                if 'PEEQ' not in fr.fieldOutputs.keys() or fr.frameValue <= 0.0:
                    continue
                Pf = min(hist, key=lambda h: abs(h[0] - fr.frameValue))[1]
                if fr_best is None or abs(Pf - P_ref) < fr_best[0]:
                    fr_best = (abs(Pf - P_ref), fr, Pf)
            if fr_best is not None:
                pe = fr_best[1].fieldOutputs['PEEQ'].getSubset(region=beam_inst)
                per_el = {}
                for v in pe.values:
                    if v.data > per_el.get(v.elementLabel, 0.0):
                        per_el[v.elementLabel] = v.data
                ranked = sorted(per_el.items(), key=lambda kv: -kv[1])
                el_by_label = dict((e.label, e) for e in beam_inst.elements)
                seen, spots = [], []
                for lab, val in ranked:
                    if val <= 0.0 or len(spots) >= 5:
                        break
                    con = el_by_label[lab].connectivity[:4]
                    c = [sum(xyz[n][i] for n in con) / 4.0 for i in range(3)]
                    txt = where(c, res['length'])
                    key = txt.split(',')[0] + '%.1f' % round(abs(c[2] - 0.5 * res['length']) * 2)
                    if key in seen:
                        continue
                    seen.append(key)
                    spots.append((val, txt))
                res['yield_spots'] = [('frame', fr_best[2])] + spots
        except Exception as err:
            log('NOTE: yield-location check skipped (%s).' % err)
    finally:
        odb.close()
    return res


def pct(a_, b_):
    return 100.0 * (a_ - b_) / b_ if b_ else 0.0


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------
odb_main = JOB_MAIN = None
for _job in JOB_MAINS:
    odb_main = find_odb(_job, required=False)
    if odb_main:
        JOB_MAIN = _job
        break
if odb_main is None:
    find_odb(JOB_MAINS[-1], required=True)          # raises with the search path
M = analyse(odb_main, JOB_MAIN, detail=True)
SOLVER = solver_messages(odb_main)
PREV = None
if JOB_MAIN == 'Stock1_RevC_v2':
    _odb_v1 = find_odb('Stock1_RevC_v1', required=False)
    if _odb_v1:
        PREV = analyse(_odb_v1, 'Stock1_RevC_v1', detail=False)
        PREV['solver'] = solver_messages(_odb_v1)
geo = read_geometry(odb_main, JOB_MAIN)
odb_chk = find_odb(JOB_CHECK, required=False)
C = analyse(odb_chk, JOB_CHECK, detail=False) if odb_chk else None

D, P, r = M['D'], M['P'], M['r']
lin = linearity(D, P, r)
w = M['vol'] * RHO if M['vol'] else None
w_sheet = M['vol'] * RHO_SHEET if M['vol'] else None
w_ok = w_sheet is not None and w_sheet <= W_LIMIT
f_ok = r['fos'] >= FOS_REQUIRED
c_ok = 0.0 < COST <= COST_LIMIT

L = []
L += ['FACTOR OF SAFETY, WEIGHT AND ACCURACY - %s (Rev C)' % JOB_MAIN,
      'ODB: %s' % odb_main,
      'Job status: %s; step %.0f %% complete' % (M['status'], 100.0 * M['done']),
      'Mesh: %d C3D10 elements, %d nodes%s'
      % (M['n_el'], M['n_nodes'],
         (', seed %.4f in' % geo['mesh_seed_in']) if isinstance(geo.get('mesh_seed_in'), float) else ''),
      '',
      'REQUIREMENTS',
      '  Weight (curved C3D10, 0.098 lb/in^3) = %s lb   limit %.2f lb   -> %s'
      % ('%.4f' % w_sheet if w_sheet else '?', W_LIMIT, 'PASS' if w_ok else 'FAIL'),
      '  FOS = P_offset / %.0f = %s%.3f   required >= %.2f (P >= %.0f lbf)   -> %s'
      % (P_DESIGN, '> ' if r['lower_bound'] else '', r['fos'], FOS_REQUIRED, P_TEST,
         'PASS' if f_ok else 'FAIL'),
      '  Cost (course cost sheet) = $%.2f   limit $%.0f   -> %s'
      % (COST, COST_LIMIT, 'PASS' if c_ok else 'FAIL'),
      '  OVERALL: %s' % ('MEETS weight, strength and cost' if (w_ok and f_ok and c_ok)
                         else 'does NOT meet every requirement (see FAIL lines)'),
      '',
      'LOAD-DISPLACEMENT',
      '  Beam length analysed  = %s in' % ('%.3f' % M['length'] if M['length'] else '?'),
      '  Elastic slope k       = %.0f lbf/in (fit %d points, %.0f-%.0f %% of peak)'
      % (r['k'], r['n_fit'], 100 * FIT_MAIN[0], 100 * FIT_MAIN[1]),
      '  Peak load reached     = %.0f lbf' % r['P_max'],
      ('  Offset-line load      = %.0f lbf at %.4f in travel' % (r['P_off'], r['d_off'])
       if r['P_off'] is not None else
       '  Offset-line load      > %.0f lbf (curve never reached the offset line)' % r['P_max'])]
if M['mises']:
    L.append('  Peak von Mises at %.0f lbf = %.1f ksi (saved frame at step time %.2f)'
             % (M['mises'][1], M['mises'][0], M['mises'][2]))

L += ['', 'DEFORMATION AT THE TEST LOAD (%.0f lbf)' % P_TEST]
L.append('  Curve departs 1 %% from linear at  %s' % ('%.0f lbf' % lin['p_1pct'] if lin['p_1pct'] else 'not reached'))
L.append('  Curve departs 2 %% from linear at  %s' % ('%.0f lbf' % lin['p_2pct'] if lin['p_2pct'] else 'not reached'))
if lin['d_test'] is not None:
    L.append('  At %.0f lbf: travel %.4f in, %.1f %% below the straight line'
             % (P_TEST, lin['d_test'], 100.0 * lin['dev_test']))
    L.append('  Estimated permanent set after unloading from %.0f lbf = %.4f in '
             '(the offset test allows %.3f in)' % (P_TEST, max(0.0, lin['set_test']), OFFSET))
else:
    L.append('  The run never reached %.0f lbf.' % P_TEST)
if len(M['yield_spots']) > 1:
    L.append('  Largest plastic strain at %.0f lbf (saved frame nearest the offset load):'
             % M['yield_spots'][0][1])
    for val, txt in M['yield_spots'][1:]:
        L.append('     PEEQ %.4f  %s' % (val, txt))

# ---- solver messages
L += ['', 'SOLVER MESSAGES (%s.msg / .dat)' % JOB_MAIN]
if SOLVER['msg_warnings'] is not None:
    L.append('  Analysis warnings: %d   errors: %d   (negative-eigenvalue warnings: %s)'
             % (SOLVER['msg_warnings'], SOLVER['msg_errors'],
                '?' if SOLVER['neg_eig'] is None else SOLVER['neg_eig']))
    for k_, n_ in sorted(SOLVER.get('kinds', {}).items(), key=lambda kv: -kv[1]):
        L.append('     %dx  %s' % (n_, k_))
    if SOLVER['msg_warnings'] == 0 and SOLVER['msg_errors'] == 0:
        L.append('  -> CLEAN RUN: no warnings or errors.')
else:
    L.append('  .msg file not found next to the .odb; warnings not counted.')
if SOLVER['dat_warnings'] is not None:
    L.append('  Input-processing warnings (.dat): %d' % SOLVER['dat_warnings'])
if PREV is not None and PREV.get('r'):
    rp = PREV['r']
    L.append('  Compared with Stock1_RevC_v1 (%s warnings): FOS %.3f vs %.3f (%+.2f %%), '
             'k %+.2f %%' % ('?' if PREV['solver']['msg_warnings'] is None else PREV['solver']['msg_warnings'],
                            r['fos'], rp['fos'], pct(r['fos'], rp['fos']), pct(r['k'], rp['k'])))

# ---- weight accuracy
L += ['', 'WEIGHT ACCURACY']
if M['vol']:
    L.append('  Mesh volume, curved C3D10 (exact)    = %.4f in^3' % M['vol'])
    L.append('  Mesh volume, straight-sided tets     = %.4f in^3  (%+.2f %%; fills in curved holes)'
             % (M['vol4'], pct(M['vol4'], M['vol'])))
    cad = geo.get('cad_volume_in3')
    if isinstance(cad, float):
        L.append('  CAD volume (Abaqus part)             = %.4f in^3  -> mesh differs by %+.3f %%'
                 % (cad, pct(M['vol'], cad)))
    L.append('  Weight at %.4f lb/in^3 (Rev B basis) = %.4f lb' % (RHO, w))
    L.append('  Weight at %.3f lb/in^3 (cost sheet)  = %.4f lb   hand calc %.3f lb -> %+.2f %%'
             % (RHO_SHEET, w_sheet, W_HAND, pct(w_sheet, W_HAND)))
    L.append('  Margin under the 1.00 lb limit       = %.3f lb (%.1f %%)'
             % (W_LIMIT - w_sheet, 100.0 * (W_LIMIT - w_sheet)))
    if isinstance(geo.get('beam_length_in'), float) and M['length']:
        L.append('  Length check: mesh %.4f in vs design %.4f in'
                 % (M['length'], geo['beam_length_in']))

# ---- FOS accuracy
L += ['', 'FOS ACCURACY']
fits = []
for win in FIT_WINDOWS:
    rr = offset_fos(D, P, win)
    fits.append(rr['fos'])
    L.append('  Elastic fit %2.0f-%2.0f %% of peak: k = %6.0f lbf/in, FOS = %s%.3f'
             % (100 * win[0], 100 * win[1], rr['k'], '> ' if rr['lower_bound'] else '', rr['fos']))
L.append('  Spread from the fit window          = %.3f (%.1f %% of the reported FOS)'
         % (max(fits) - min(fits), 100.0 * (max(fits) - min(fits)) / r['fos']))
if r['i_cross'] is not None:
    i = r['i_cross']
    L.append('  Curve points: %d in the step; at the crossing they are %.4f in / %.0f lbf apart'
             % (len(P), D[i] - D[i - 1], P[i] - P[i - 1]))
if C is not None and C.get('r'):
    rc = C['r']
    dF, dk = pct(r['fos'], rc['fos']), pct(r['k'], rc['k'])
    L.append('  Mesh convergence (fine vs. Rev B-density mesh check, %s):' % C['status'])
    L.append('     nodes      %7d  vs %7d' % (M['n_nodes'], C['n_nodes']))
    L.append('     k (lbf/in) %7.0f  vs %7.0f   (%+.2f %%)' % (r['k'], rc['k'], dk))
    L.append('     FOS        %7.3f  vs %7.3f   (%+.2f %%)' % (r['fos'], rc['fos'], dF))
    if C['vol'] and M['vol']:
        L.append('     weight     %7.4f  vs %7.4f lb (%+.3f %%)'
                 % (w_sheet, C['vol'] * RHO_SHEET, pct(M['vol'], C['vol'])))
    conv = abs(dF) < CONVERGED_FOS_PCT and abs(dk) < CONVERGED_K_PCT
    L.append('     -> %s' % ('CONVERGED: refining the mesh changes FOS by less than %.0f %% and k by '
                              'less than %.0f %%.' % (CONVERGED_FOS_PCT, CONVERGED_K_PCT) if conv else
                              'NOT CONVERGED: the two meshes disagree; treat the FOS with caution.'))
else:
    L.append('  Mesh convergence: not checked.  Set MESH_LEVEL = \'CHECK\' in Stock1_RevC_v1.py,')
    L.append('     run it, and run this script again to compare the two meshes.')

if M['done'] < 1.0:
    L.append('NOTE: the step did not finish; rerun the job before using these numbers.')
if r['lower_bound']:
    L.append('NOTE: "> value" is a lower bound: the load never crossed the offset line '
             'within the step travel.')
for l in L:
    log(l)

# --------------------------------------------------------------------------
# save
# --------------------------------------------------------------------------
root = repo_root(os.path.dirname(odb_main)) or os.path.dirname(odb_main)
out_dir = os.path.join(root, *RESULTS_DIR)
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
fh = open(os.path.join(out_dir, 'FOS_%s.txt' % JOB_MAIN), 'w')
fh.write('\n'.join(L) + '\n')
fh.close()
fh = open(os.path.join(out_dir, 'FOS_%s_LoadDisp.csv' % JOB_MAIN), 'w')
fh.write('travel_in,load_lbf,offset_line_lbf\n')
for i in range(len(D)):
    fh.write('%.6f,%.2f,%.2f\n' % (D[i], P[i], max(0.0, r['k'] * (D[i] - r['d0'] - OFFSET))))
fh.close()
log('Saved FOS_%s.txt and FOS_%s_LoadDisp.csv in %s' % (JOB_MAIN, JOB_MAIN, out_dir))

# --------------------------------------------------------------------------
# plot in the viewport, then export it as a PNG
# --------------------------------------------------------------------------
try:
    names = ['LD_' + JOB_MAIN, 'OFF_' + JOB_MAIN, 'LD_' + JOB_CHECK]
    for nm in names:
        if nm in session.xyDataObjects.keys():
            del session.xyDataObjects[nm]
    c1 = session.XYData(name=names[0], data=tuple(zip(D, P)),
                        xValuesLabel='Top-roller travel (in)', yValuesLabel='Load (lbf)',
                        legendLabel='Rev C, fine mesh')
    d_end = max(D)
    c2 = session.XYData(name=names[1],
                        data=((r['d0'] + OFFSET, 0.0),
                              (d_end, r['k'] * (d_end - r['d0'] - OFFSET))),
                        xValuesLabel='Top-roller travel (in)', yValuesLabel='Load (lbf)',
                        legendLabel='0.02 in offset line')
    curves = [session.Curve(xyData=c1), session.Curve(xyData=c2)]
    try:
        curves[1].lineStyle.setValues(style=DASHED)
    except Exception:
        pass
    if C is not None and C.get('D'):
        c3 = session.XYData(name=names[2], data=tuple(zip(C['D'], C['P'])),
                            xValuesLabel='Top-roller travel (in)', yValuesLabel='Load (lbf)',
                            legendLabel='Rev C, mesh check (Rev B density)')
        curves.append(session.Curve(xyData=c3))
        try:
            curves[2].lineStyle.setValues(style=DOTTED)
        except Exception:
            pass
    plot_name = 'FOS_' + JOB_MAIN
    if plot_name in session.xyPlots.keys():
        del session.xyPlots[plot_name]
    xyp = session.XYPlot(name=plot_name)
    xyp.title.setValues(text='Rev C: FOS %s%.2f' % ('> ' if r['lower_bound'] else '', r['fos']))
    chart = xyp.charts[list(xyp.charts.keys())[0]]
    chart.setValues(curvesToPlot=tuple(curves))
    vp = session.viewports[session.currentViewportName]
    vp.setValues(displayedObject=xyp)
    log('Plot "%s" shown in the viewport.' % plot_name)
    try:
        png = os.path.join(out_dir, '%s_LoadDisp' % JOB_MAIN)
        session.printOptions.setValues(vpDecorations=OFF, reduceColors=False)
        session.printToFile(fileName=png, format=PNG, canvasObjects=(vp,))
        log('Saved %s.png' % png)
    except Exception as err:
        log('NOTE: PNG export skipped (%s); the CSV has the data.' % err)
except Exception as err:
    log('NOTE: plot skipped (%s); use the CSV file instead.' % err)
