# -*- coding: utf-8 -*-
"""
fix_Stock1_RevC_v1.py  --  EMCH 308 Team 6, warning-free rerun of the Rev C job
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> any folder inside the repo
                                        (e.g. abaqus/base_models/)
    2. File > Run Script...          -> abaqus/python/final/fix_Stock1_RevC_v1.py
    It opens abaqus/final_design/Stock1_RevC_v1.cae (the finished Rev C model,
    with its 234,665-node mesh), applies the fixes below, and submits job
    Stock1_RevC_v2 from abaqus/final_design/job_v2/ (roughly 2 hours).
    When it reads "Completed", run FOS_Stock1_RevC_v3.py.
    Progress: message area and fix_Stock1_RevC_v1_log.txt in the work directory.

WHAT THE v1 JOB WARNED ABOUT (Stock1_RevC_v1.msg: 7 warnings, 0 errors)
    All 7 come from one rejected attempt, increment 2 attempt 1, before any real
    load: the beam settled onto the two support rollers and 83 contact points
    closed at once.  That jump caused
        * "EXCESSIVE DISTORTION AT ... 21 INTEGRATION POINTS" (2 warnings)
        * "STRAIN INCREMENT HAS EXCEEDED FIFTY TIMES THE STRAIN TO CAUSE FIRST
          YIELD" (3 warnings)
        * "THE SYSTEM MATRIX HAS 1 / 4 NEGATIVE EIGENVALUES" (2 warnings)
    Abaqus cut the increment to 1/4 and then 1/16 and carried on, so the v1
    results are valid.  This script removes the cause so the run is clean.

THE FIXES (physics unchanged; same mesh, material, rollers and loading)
    1. Bottom contact starts closed.  Only the top roller contact had a
       strain-free adjustment (0.001 in).  Both support-roller contacts now get
       the same adjustment, so the beam starts touching all three rollers
       instead of falling onto the supports in increment 2.
    2. Smaller first increment: 0.1 % of the step (0.00008 in of travel)
       instead of 1 %.  Abaqus grows the increment automatically up to the same
       1 % maximum, so the load-displacement curve keeps its resolution.
    3. A few more increments allowed (maxNumInc 3000) for the gentler start.
    The model is saved as abaqus/final_design/Stock1_RevC_v2.cae; the v1 model,
    job and results are not touched.

UNITS: in, kip, ksi.  Works with the Python 3 (2024+) and Python 2.7 builds.
"""
from __future__ import print_function

import os
import shutil

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

# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------
SRC_CAE      = 'Stock1_RevC_v1.cae'     # in abaqus/final_design/ (model only)
SRC_JOB      = 'Stock1_RevC_v1'
JOB_NAME     = 'Stock1_RevC_v2'
JOB_FOLDER   = 'job_v2'                 # abaqus/final_design/job_v2/
STEP_NAME    = 'Load'
ADJ_TOL      = 1.0e-3                   # in, strain-free closure for the support contacts
INITIAL_INC  = 0.001                    # fraction of the step (v1: 0.01)
MAX_INC      = 0.01                     # unchanged from v1
MAX_NUM_INC  = 3000
NUM_CPUS     = 4
SUBMIT_JOB   = True

LOG_PATH = os.path.join(os.getcwd(), 'fix_Stock1_RevC_v1_log.txt')
try:
    open(LOG_PATH, 'w').close()
except Exception:
    LOG_PATH = None


def log(text):
    line = '[fix_Stock1_RevC] ' + text
    print(line)
    if LOG_PATH:
        try:
            fh = open(LOG_PATH, 'a')
            fh.write(line + '\n')
            fh.close()
        except Exception:
            pass


def repo_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, 'abaqus')) and os.path.isdir(os.path.join(d, 'results')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


# ---------------------------------------------------------------------------
# 1. open the finished v1 model
# ---------------------------------------------------------------------------
root = repo_root(os.getcwd())
tries = [os.path.join(os.getcwd(), SRC_CAE)]
if root:
    tries.insert(0, os.path.join(root, 'abaqus', 'final_design', SRC_CAE))
src = None
for f in tries:
    if os.path.isfile(f):
        src = f
        break
if src is None:
    raise RuntimeError('%s not found (looked in %s).  Set the work directory to a folder '
                       'inside the repo and run again.' % (SRC_CAE, tries[0]))
base_dir = os.path.dirname(src)
log('Opening %s' % src)
mdb = openMdb(pathName=src)
model = None
for mname in mdb.models.keys():
    if STEP_NAME in mdb.models[mname].steps.keys():
        model = mdb.models[mname]
        break
if model is None:
    raise RuntimeError('No model with a "%s" step in %s.' % (STEP_NAME, SRC_CAE))
a = model.rootAssembly
p = model.parts['Beam']
log('Model "%s": beam mesh %d elements, %d nodes (unchanged).'
    % (model.name, len(p.elements), len(p.nodes)))

# ---------------------------------------------------------------------------
# 2. fix 1: support-roller contacts start closed (strain-free adjustment)
# ---------------------------------------------------------------------------
def make_pair(name, main_s, sec_s, adjust_tol):
    """Same definition as the build script, with an adjustment zone."""
    kw = dict(name=name, createStepName='Initial', sliding=FINITE, thickness=ON,
              interactionProperty='CP_Frictionless', initialClearance=OMIT,
              datumAxis=None, clearanceRegion=None,
              adjustMethod=TOLERANCE, adjustTolerance=adjust_tol)
    for roles in (('main', 'secondary'), ('master', 'slave')):
        kw2 = dict(kw)
        kw2[roles[0]] = a.surfaces[main_s]
        kw2[roles[1]] = a.surfaces[sec_s]
        for extra in ({'contactTracking': ONE_CONFIG}, {}):
            try:
                kw3 = dict(kw2)
                kw3.update(extra)
                model.SurfaceToSurfaceContactStd(**kw3)
                return
            except TypeError:
                continue
    raise RuntimeError('Could not rebuild contact pair %s.' % name)


bot_pairs = [n for n in model.interactions.keys() if n.upper().startswith('C_BOTROLLER')]
if len(bot_pairs) != 2:
    raise RuntimeError('Expected 2 support-roller contact pairs (C_BotRoller-*); found %s.'
                       % bot_pairs)
for name in bot_pairs:
    ia = model.interactions[name]
    try:
        ia.setValues(adjustMethod=TOLERANCE, adjustTolerance=ADJ_TOL)
        log('Contact %s: strain-free adjustment %.4f in (was none).' % (name, ADJ_TOL))
    except Exception as err:
        log('NOTE: %s could not be edited in place (%s); rebuilding it.' % (name, err))
        inst_name = name[2:]                       # C_BotRoller-1 -> BotRoller-1
        del model.interactions[name]
        make_pair(name, 'CS_' + inst_name, 'CS_BeamBot', ADJ_TOL)
        log('Contact %s rebuilt with a %.4f in adjustment.' % (name, ADJ_TOL))
top_pairs = [n for n in model.interactions.keys() if n.upper().startswith('C_TOPROLLER')]
log('Top-roller contact %s keeps its existing adjustment.' % (', '.join(top_pairs) or '(none found)'))

# ---------------------------------------------------------------------------
# 3. fix 2 and 3: gentler first increment, same maximum
# ---------------------------------------------------------------------------
st = model.steps[STEP_NAME]
st.setValues(initialInc=INITIAL_INC, maxInc=MAX_INC, maxNumInc=MAX_NUM_INC)
log('Step "%s": first increment %.3f (was 0.010), max %.3f, up to %d increments.'
    % (STEP_NAME, INITIAL_INC, MAX_INC, MAX_NUM_INC))

# ---------------------------------------------------------------------------
# 4. save, job in its own folder, submit
# ---------------------------------------------------------------------------
job_dir = os.path.join(base_dir, JOB_FOLDER)
if not os.path.isdir(job_dir):
    os.makedirs(job_dir)
if os.path.exists(os.path.join(job_dir, JOB_NAME + '.lck')):
    raise RuntimeError('%s.lck exists in %s: a run is active or was cut off.  If no job is '
                       'running, delete the .lck file and run again.' % (JOB_NAME, job_dir))
for jn in list(mdb.jobs.keys()):
    del mdb.jobs[jn]
mdb.saveAs(pathName=os.path.join(base_dir, JOB_NAME + '.cae'))
log('Saved %s (model only)' % os.path.join(base_dir, JOB_NAME + '.cae'))

# the FOS script reads the CAD volume from <job>_geometry.txt next to the job
g_src = os.path.join(base_dir, 'job', SRC_JOB + '_geometry.txt')
if os.path.isfile(g_src):
    shutil.copyfile(g_src, os.path.join(job_dir, JOB_NAME + '_geometry.txt'))
    log('Copied %s_geometry.txt -> %s_geometry.txt (same geometry).' % (SRC_JOB, JOB_NAME))
else:
    log('NOTE: %s not found; the FOS report will skip the CAD-volume comparison.' % g_src)

try:
    n_cpu = os.cpu_count() or 1
except AttributeError:
    n_cpu = 1
n_cpu = max(1, min(NUM_CPUS, n_cpu))
desc = 'Rev C, warning fixes on the v1 model (support contacts adjusted, initial inc %.3f)' % INITIAL_INC
try:
    mdb.Job(name=JOB_NAME, model=model.name, type=ANALYSIS, resultsFormat=ODB,
            numCpus=n_cpu, numDomains=n_cpu, memory=90, memoryUnits=PERCENTAGE,
            description=desc)
except Exception:
    mdb.Job(name=JOB_NAME, model=model.name, type=ANALYSIS, numCpus=1, description=desc)
    n_cpu = 1
log('Job "%s" defined (%d CPU%s).' % (JOB_NAME, n_cpu, '' if n_cpu == 1 else 's'))
os.chdir(job_dir)                          # Abaqus writes job files to the work directory
mdb.saveAs(pathName=os.path.join(job_dir, JOB_NAME + '.cae'))
log('Saved the model with its job to %s' % os.path.join(job_dir, JOB_NAME + '.cae'))
if SUBMIT_JOB:
    mdb.jobs[JOB_NAME].submit(consistencyChecking=OFF)
    log('Job "%s" submitted from %s (roughly 2 hours).  Follow it in Job > Manager > Monitor.'
        % (JOB_NAME, job_dir))
    log('When it reads "Completed", run FOS_Stock1_RevC_v3.py: it reports the solver warning count.')
else:
    log('SUBMIT_JOB = False: job created, not submitted (Job > Manager > Submit).')
