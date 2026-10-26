# -*- coding: utf-8 -*-
"""
Stock1_Drilled_Job_v1.py  --  EMCH 308 Team 6, run the Stock 1 drilled-plan analysis
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> the folder holding Stock1_Drilled.cae
                                        (E:\\Semester Project\\abaqus after organizing;
                                        the project folder itself also works)
    2. File > Run Script...          -> Stock1_Drilled_Job_v1.py
    3. Watch progress in Job > Manager > Monitor.  When the job shows
       "Completed", run FOS_Stock1_Drilled_v1.py for the factor of safety.

WHAT IT DOES
    * Opens Stock1_Drilled.cae, the finished model from Stock1_Drilled_v1.py
      (Stock 1 AA I 3 x 2.03, 8.2 in, 32 flange holes + 2 web holes + top-flange
      end reliefs, 0.993 lb).  It does not change the geometry or the mesh.
    * Checks the model before submitting: beam meshed, node count under the
      Academic Teaching licence limit (250,000), no distorted elements, step
      "Load" with the top roller pushed down 0.08 in, load-displacement history
      output, three roller contact pairs.  Any failed check stops the script
      with a message saying what to fix.
    * Creates the folder  Stock1_Drilled\\  next to Stock1_Drilled.cae, saves a
      copy of the model there with the job definition, and submits the job from
      there, so every result file (.odb, .msg, .sta, ...) lands in that folder.
      The base Stock1_Drilled.cae is left untouched.
    * Progress goes to the message area and to
      Stock1_Drilled\\Stock1_Drilled_Job_v1_log.txt.
UNITS: model in kip, in (stress in ksi).
"""
from __future__ import print_function

import os

from abaqus import *
from abaqusConstants import *
from caeModules import *

try:
    import builtins as _py_builtins          # Python 3 (Abaqus 2024+)
except ImportError:
    import __builtin__ as _py_builtins       # Python 2.7 (older Abaqus)
sum = _py_builtins.sum
abs = _py_builtins.abs
min = _py_builtins.min
max = _py_builtins.max
round = _py_builtins.round

# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
CAE_NAME     = 'Stock1_Drilled.cae'
MODEL_NAME   = 'Project'
BEAM_PART    = 'Beam'
JOB_NAME     = 'Stock1_Drilled'
JOB_FOLDER   = 'Stock1_Drilled'      # created next to Stock1_Drilled.cae
STEP_NAME    = 'Load'
U_TARGET     = 0.08                  # in, expected top-roller travel
NODE_LIMIT   = 250000                # Academic Teaching licence limit
NUM_CPUS     = 4                     # capped at the processors on the machine
MEMORY_PCT   = 90
SUBMIT       = True                  # False = create the job but do not submit

LOG_LINES = []
LOG_PATH = None


def log(text):
    line = '[Stock1_Drilled_Job] ' + text
    print(line)
    LOG_LINES.append(line)
    if LOG_PATH:
        try:
            fh = open(LOG_PATH, 'a')
            fh.write(line + '\n')
            fh.close()
        except Exception:
            pass


def stop(text):
    log('STOPPED: ' + text)
    raise RuntimeError(text)


# --------------------------------------------------------------------------
# 1. find and open the model
# --------------------------------------------------------------------------
here = os.getcwd()
candidates = [os.path.join(here, CAE_NAME),
              os.path.join(here, 'abaqus', CAE_NAME)]
cae_path = None
for c in candidates:
    if os.path.isfile(c):
        cae_path = c
        break
if cae_path is None:
    stop('%s was not found in %s or its abaqus folder.  Run Stock1_Drilled_v1.py first, '
         'or set the work directory to the folder holding %s.' % (CAE_NAME, here, CAE_NAME))

base_dir = os.path.dirname(cae_path)
job_dir = os.path.join(base_dir, JOB_FOLDER)
if not os.path.isdir(job_dir):
    os.makedirs(job_dir)
LOG_PATH = os.path.join(job_dir, 'Stock1_Drilled_Job_v1_log.txt')
log('=' * 60)
log('Stock1_Drilled_Job_v1 starting')
log('Opening %s' % cae_path)
mdb = openMdb(pathName=cae_path)

model_name = MODEL_NAME if MODEL_NAME in mdb.models.keys() else None
if model_name is None:
    for nm in mdb.models.keys():
        if BEAM_PART in mdb.models[nm].parts.keys():
            model_name = nm
            break
if model_name is None:
    stop('No model with a "%s" part in %s.' % (BEAM_PART, CAE_NAME))
model = mdb.models[model_name]
a = model.rootAssembly
log('Model "%s"' % model_name)

# --------------------------------------------------------------------------
# 2. pre-submit checks
# --------------------------------------------------------------------------
problems = []

# mesh
p = model.parts[BEAM_PART]
n_el, n_nd = len(p.elements), len(p.nodes)
if n_el == 0:
    problems.append('the beam part has no mesh (rerun Stock1_Drilled_v1.py)')
total_nodes = 0
for inst in a.instances.values():
    try:
        total_nodes += len(inst.nodes)
    except Exception:
        pass
log('Beam mesh: %d elements, %d nodes; whole model %d nodes (limit %d).'
    % (n_el, n_nd, total_nodes, NODE_LIMIT))
if total_nodes > NODE_LIMIT:
    problems.append('%d nodes is over the %d-node licence limit' % (total_nodes, NODE_LIMIT))

try:
    q = p.verifyMeshQuality(criterion=ANALYSIS_CHECKS)
    n_bad = len(q.get('failedElements', ()))
    n_warn = len(q.get('warningElements', ()))
    log('Mesh check: %d failed, %d warning elements.' % (n_bad, n_warn))
    if n_bad:
        problems.append('%d distorted elements (the solver would stop on them)' % n_bad)
except Exception as err:
    log('NOTE: mesh check skipped (%s).' % err)

# step and loading
if STEP_NAME not in model.steps.keys():
    problems.append('step "%s" is missing' % STEP_NAME)
else:
    try:
        st = model.steps[STEP_NAME]
        log('Step "%s": nlgeom %s, initial increment %s, max increments %s.'
            % (STEP_NAME, st.nlgeom, st.initialInc, st.maxNumInc))
    except Exception:
        pass
if 'TopRoller_Control' not in model.boundaryConditions.keys():
    problems.append('boundary condition "TopRoller_Control" is missing')
else:
    try:
        bcs = model.steps[STEP_NAME].boundaryConditionStates['TopRoller_Control']
        u2 = bcs.u2
        log('Top roller U2 in step "%s" = %s in.' % (STEP_NAME, u2))
        if abs(abs(float(u2)) - U_TARGET) > 1.0e-6:
            log('NOTE: top-roller travel is %s in (expected -%.3f in).' % (u2, U_TARGET))
    except Exception as err:
        log('NOTE: could not read the top-roller travel (%s).' % err)

# output
if 'H-LoadDisp' not in model.historyOutputRequests.keys():
    problems.append('history output "H-LoadDisp" (RF2/U2 at the top roller) is missing')
else:
    log('History output "H-LoadDisp" present (RF2, U2 at the top roller).')

# contact
n_pairs = len(model.interactions.keys())
log('Interactions: %d (%s).' % (n_pairs, ', '.join(sorted(model.interactions.keys()))))
if n_pairs < 3:
    problems.append('only %d contact interactions (expected 3 roller pairs)' % n_pairs)
for sname in ('CS_BeamTop', 'CS_BeamBot'):
    if sname not in a.surfaces.keys():
        problems.append('contact surface "%s" is missing' % sname)

if problems:
    stop('The model is not ready:\n  - ' + '\n  - '.join(problems))
log('All pre-submit checks passed.')

# --------------------------------------------------------------------------
# 3. job definition in its own folder
# --------------------------------------------------------------------------
if os.path.exists(os.path.join(job_dir, JOB_NAME + '.lck')):
    stop('%s.lck exists in %s: a run is active or was killed.  If no job is running, '
         'delete the .lck file and run again.' % (JOB_NAME, job_dir))

for jn in list(mdb.jobs.keys()):
    del mdb.jobs[jn]

try:
    n_cpu = os.cpu_count() or 1
except AttributeError:
    n_cpu = 1
n_cpu = max(1, min(NUM_CPUS, n_cpu))
try:
    mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, resultsFormat=ODB,
            numCpus=n_cpu, numDomains=n_cpu, memory=MEMORY_PCT, memoryUnits=PERCENTAGE,
            description='Stock 1 drilled plan A+B, 8.2 in, 3-point bend to 0.08 in')
except Exception as err:
    log('NOTE: %d-CPU job not accepted (%s); using 1 CPU.' % (n_cpu, err))
    n_cpu = 1
    mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, numCpus=1,
            description='Stock 1 drilled plan A+B, 8.2 in, 3-point bend to 0.08 in')
log('Job "%s" defined (%d CPU%s, %d%% memory).'
    % (JOB_NAME, n_cpu, '' if n_cpu == 1 else 's', MEMORY_PCT))

# Abaqus writes the job files into the current work directory
os.chdir(job_dir)
mdb.saveAs(pathName=os.path.join(job_dir, JOB_NAME + '.cae'))
log('Saved the model with its job to %s' % os.path.join(job_dir, JOB_NAME + '.cae'))
log('Work directory is now %s' % job_dir)

# --------------------------------------------------------------------------
# 4. submit
# --------------------------------------------------------------------------
if SUBMIT:
    mdb.jobs[JOB_NAME].submit(consistencyChecking=OFF)
    log('Job "%s" submitted.  Follow it in Job > Manager > Monitor.' % JOB_NAME)
    log('When it reads "Completed", run FOS_Stock1_Drilled_v1.py (any work directory '
        'inside the project folder works).')
else:
    log('SUBMIT = False: job created but not submitted.  Use Job > Manager > Submit.')
