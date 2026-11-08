# -*- coding: utf-8 -*-
"""
Stock1_RevC_Job_v1.py  --  EMCH 308 Team 6, run the Rev C final-design job and push it to GitHub
==============================================================================

ONE SCRIPT, START TO FINISH (lab PC with Abaqus/CAE)
    1. Builds the warning-free Rev C rerun, job Stock1_RevC_v2
       (runs abaqus/python/final/fix_Stock1_RevC_v1.py: same mesh, material,
       rollers and loading as v1; only the contact start and first increment
       change).
    2. Submits it and WAITS until Abaqus finishes (roughly 2 hours).  If the
       run is cut off (the Nov 3 try was stopped by the license server), it
       resubmits once by itself.
    3. Runs abaqus/python/final/FOS_Stock1_RevC_v3.py on the new .odb:
       FoS, weight, cost, solver-warning count, v1 vs v2 comparison.
    4. Refreshes the copies in Final_Design/ (Results/ and Abaqus/job_v2/).
    5. Commits the new files and pushes them to
       github.com/RyanBilock/EMCH-308_Group-6_Final-Project (branch main).
       The 500+ MB .odb stays local only (.gitignore; too big for GitHub).

HOW TO RUN
    Option A, Abaqus/CAE window (the FoS plot PNG is exported only this way):
        1. File > Set Work Directory... -> any folder inside the repo
                                           (e.g. abaqus/final_design/)
        2. File > Run Script...         -> abaqus/python/final/Stock1_RevC_Job_v1.py
        The CAE window is busy until the job ends (~2 h); that is normal.
    Option B, Abaqus Command prompt (no window; report + CSV, no PNG):
        cd /d E:\\EMCH308_repo\\abaqus\\final_design
        abaqus cae noGUI=..\\python\\final\\Stock1_RevC_Job_v1.py
    Progress: message area / prompt, and archive/logs/Stock1_RevC_Job_v1_log.txt.

    Already ran the job?  Run this script again: it sees the finished
    Stock1_RevC_v2 job, skips the 2-hour run, and does steps 3-5 only.

GIT ON THE LAB PC
    The script looks for git on PATH, then in Git for Windows and GitHub
    Desktop.  The first push from a new PC opens a GitHub sign-in window
    (Git Credential Manager): sign in once.  If there is no git, or the push
    fails, nothing is lost: the results are saved in the repo folder and the
    message says to push from your own PC (GitHub Desktop or `git push`).

UNITS: model in kip, in (stress in ksi); reports in lbf, in, lb, ksi.
Works with the Python 3 (Abaqus 2024+) and Python 2.7 builds.
"""
from __future__ import print_function

import os
import re
import shutil
import subprocess
import sys
import time

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
JOB_NAME      = 'Stock1_RevC_v2'
BUILD_SCRIPT  = ('abaqus', 'python', 'final', 'fix_Stock1_RevC_v1.py')
FOS_SCRIPT    = ('abaqus', 'python', 'final', 'FOS_Stock1_RevC_v3.py')
FINAL_DIR     = ('abaqus', 'final_design')
JOB_DIR       = ('abaqus', 'final_design', 'job_v2')
RESULTS_DIR   = ('results', 'final_design')
LOG_DIR       = ('archive', 'logs')            # local only (.gitignore)
MAX_TRIES     = 2                              # 1 run + 1 automatic resubmit
RETRY_WAIT_S  = 300                            # wait before resubmitting (license server)

DO_GIT_PUSH   = True
GIT_BRANCH    = 'main'
GIT_NAME      = 'Ryan Bilock'                  # used only if the lab PC has no git identity
GIT_EMAIL     = 'rbilock@gmail.com'
GIT_TIMEOUT_S = 600

# files and folders committed (anything .gitignore excludes is skipped by git)
GIT_PATHS = [
    'abaqus/final_design/Stock1_RevC_v2.cae',
    'abaqus/final_design/Stock1_RevC_v2.jnl',
    'abaqus/final_design/job_v2',
    'results/final_design',
    'Final_Design/Results',
    'Final_Design/Abaqus/job_v2',
    'Final_Design/Scripts/Stock1_RevC_Job_v1.py',
    'abaqus/python/final/Stock1_RevC_Job_v1.py',
]

TAG = '[RevC_Job] '


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def repo_root(start):
    """Walk up from start to the folder that holds abaqus/, results/ and Final_Design/."""
    d = os.path.abspath(start)
    while True:
        if all(os.path.isdir(os.path.join(d, s)) for s in ('abaqus', 'results', 'Final_Design')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def find_root():
    starts = [os.getcwd()]
    try:
        starts.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:                           # File > Run Script may not set __file__
        pass
    for s in starts:
        r = repo_root(s)
        if r:
            return r
    raise RuntimeError('Repo folder not found from %s.  Set the work directory to a folder '
                       'inside EMCH308_repo (e.g. abaqus/final_design) and run again.' % starts[0])


ROOT = find_root()
P = lambda parts: os.path.join(ROOT, *parts)

_log_dir = P(LOG_DIR)
try:
    if not os.path.isdir(_log_dir):
        os.makedirs(_log_dir)
    LOG_PATH = os.path.join(_log_dir, 'Stock1_RevC_Job_v1_log.txt')
    open(LOG_PATH, 'w').close()
except Exception:
    LOG_PATH = None


def log(text):
    line = TAG + text
    print(line)
    try:
        milestone(line)                         # CAE status bar (no-op in noGUI)
    except Exception:
        pass
    if LOG_PATH:
        try:
            fh = open(LOG_PATH, 'a')
            fh.write(time.strftime('%Y-%m-%d %H:%M:%S  ') + text + '\n')
            fh.close()
        except Exception:
            pass


def read(path):
    try:
        fh = open(path)
        t = fh.read()
        fh.close()
        return t
    except Exception:
        return ''


def job_files(ext):
    return os.path.join(P(JOB_DIR), JOB_NAME + ext)


def job_completed():
    return ('COMPLETED SUCCESSFULLY' in read(job_files('.sta'))
            and 'COMPLETED' in read(job_files('.log'))
            and os.path.isfile(job_files('.odb')))


def run_script(parts, workdir):
    """Run one of the team's Abaqus scripts in its own namespace; return that namespace."""
    path = P(parts)
    if not os.path.isfile(path):
        raise RuntimeError('%s is missing.' % path)
    os.chdir(workdir)
    ns = {'__name__': '__main__', '__file__': path}
    code = compile(read(path), path, 'exec')
    exec(code, ns)
    return ns


def copy_into(src, dst_dir):
    if not os.path.isfile(src):
        return False
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    shutil.copy2(src, os.path.join(dst_dir, os.path.basename(src)))
    return True


# ---------------------------------------------------------------------------
# 1-2. build, submit and wait for the job
# ---------------------------------------------------------------------------
def run_job():
    if job_completed():
        log('%s already finished (%s): skipping the run, going to the FoS report.'
            % (JOB_NAME, P(JOB_DIR)))
        return True

    log('Repo: %s' % ROOT)
    log('Step 1/5: building %s with %s' % (JOB_NAME, BUILD_SCRIPT[-1]))
    lck = job_files('.lck')
    if os.path.exists(lck):
        try:
            os.remove(lck)
            log('Removed a leftover %s.lck from an earlier cut-off run.' % JOB_NAME)
        except Exception:
            raise RuntimeError('%s exists and could not be removed.  If no job is running, '
                               'delete it and run again.' % lck)

    ns = run_script(BUILD_SCRIPT, P(LOG_DIR))    # it submits the job from job_v2/
    db = ns.get('mdb')
    if db is None or JOB_NAME not in db.jobs.keys():
        raise RuntimeError('%s did not define job %s.' % (BUILD_SCRIPT[-1], JOB_NAME))
    job = db.jobs[JOB_NAME]

    for attempt in range(1, MAX_TRIES + 1):
        if attempt > 1:
            log('Waiting %d s, then resubmitting (try %d of %d).' % (RETRY_WAIT_S, attempt, MAX_TRIES))
            time.sleep(RETRY_WAIT_S)
            if os.path.exists(lck):
                try:
                    os.remove(lck)
                except Exception:
                    pass
            os.chdir(P(JOB_DIR))
            job.submit(consistencyChecking=OFF)
        log('Step 2/5: %s running (try %d of %d), roughly 2 hours.  Started %s.'
            % (JOB_NAME, attempt, MAX_TRIES, time.strftime('%H:%M')))
        t0 = time.time()
        job.waitForCompletion()
        mins = (time.time() - t0) / 60.0
        if job_completed():
            log('%s COMPLETED in %.0f min.' % (JOB_NAME, mins))
            return True
        tail = read(job_files('.log')).strip().splitlines()[-4:]
        log('%s did not complete (%.0f min).  End of .log: %s' % (JOB_NAME, mins, ' | '.join(tail)))
    raise RuntimeError('%s failed %d times.  Check %s and %s; nothing was pushed.'
                       % (JOB_NAME, MAX_TRIES, job_files('.msg'), job_files('.log')))


# ---------------------------------------------------------------------------
# 3. FoS report
# ---------------------------------------------------------------------------
def run_fos():
    log('Step 3/5: FoS, weight and warning report with %s' % FOS_SCRIPT[-1])
    run_script(FOS_SCRIPT, P(FINAL_DIR))
    rpt = os.path.join(P(RESULTS_DIR), 'FOS_%s.txt' % JOB_NAME)
    txt = read(rpt)
    if not txt:
        raise RuntimeError('%s was not written; see the messages above.' % rpt)
    summary = {}
    m = re.search(r'FOS = P_offset / 5000 = ([\d.]+).*?->\s*(\w+)', txt)
    if m:
        summary['fos'] = '%s (%s)' % (m.group(1), m.group(2))
    m = re.search(r'Weight \(curved C3D10, 0\.098 lb/in\^3\) = ([\d.]+) lb.*?->\s*(\w+)', txt)
    if m:
        summary['weight'] = '%s lb (%s)' % (m.group(1), m.group(2))
    m = re.search(r'OVERALL: ([^\n]+)', txt)
    if m:
        summary['overall'] = m.group(1).strip()
    m = re.search(r'Analysis warnings: (\d+)\s+errors: (\d+)', txt)
    if m:
        summary['warnings'] = '%s warnings, %s errors' % (m.group(1), m.group(2))
    for k in ('fos', 'weight', 'warnings', 'overall'):
        if k in summary:
            log('  %-8s %s' % (k + ':', summary[k]))
    return summary


# ---------------------------------------------------------------------------
# 4. refresh the Final_Design/ copies
# ---------------------------------------------------------------------------
def refresh_final_design():
    log('Step 4/5: refreshing the copies in Final_Design/')
    n = 0
    res_dst = os.path.join(ROOT, 'Final_Design', 'Results')
    for f in ('FOS_%s.txt' % JOB_NAME, 'FOS_%s_LoadDisp.csv' % JOB_NAME, '%s_LoadDisp.png' % JOB_NAME):
        n += copy_into(os.path.join(P(RESULTS_DIR), f), res_dst)
    job_dst = os.path.join(ROOT, 'Final_Design', 'Abaqus', 'job_v2')
    for ext in ('.cae', '.inp', '.jnl', '_geometry.txt'):
        n += copy_into(job_files(ext), job_dst)
    me = os.path.join(ROOT, 'abaqus', 'python', 'final', 'Stock1_RevC_Job_v1.py')
    n += copy_into(me, os.path.join(ROOT, 'Final_Design', 'Scripts'))
    log('  %d files copied (the .odb stays in abaqus/final_design/job_v2/ only).' % n)


# ---------------------------------------------------------------------------
# 5. git commit + push
# ---------------------------------------------------------------------------
def find_git():
    cands = ['git']
    pf = [os.environ.get(v) for v in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)')]
    for base in [b for b in pf if b]:
        cands.append(os.path.join(base, 'Git', 'cmd', 'git.exe'))
    local = os.environ.get('LOCALAPPDATA')
    if local:
        cands.append(os.path.join(local, 'Programs', 'Git', 'cmd', 'git.exe'))
        gd = os.path.join(local, 'GitHubDesktop')
        if os.path.isdir(gd):
            apps = sorted([d for d in os.listdir(gd) if d.startswith('app-')], reverse=True)
            for a in apps:
                cands.append(os.path.join(gd, a, 'resources', 'app', 'git', 'cmd', 'git.exe'))
    for g in cands:
        try:
            out = subprocess.check_output([g, '--version'], stderr=subprocess.STDOUT)
            return g, out.decode('utf-8', 'replace').strip()
        except Exception:
            continue
    return None, None


def git(g, args, check=True):
    cmd = [g, '-C', ROOT] + args
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            out = p.communicate(timeout=GIT_TIMEOUT_S)[0]
        except TypeError:                      # Python 2.7: no timeout
            out = p.communicate()[0]
        out = out.decode('utf-8', 'replace').strip()
        code = p.returncode
    except Exception as e:
        out, code = str(e), 1
    if check and code != 0:
        raise RuntimeError('git %s failed:\n%s' % (' '.join(args), out))
    return code, out


def push_to_github(summary):
    if not DO_GIT_PUSH:
        log('Step 5/5: DO_GIT_PUSH = False, skipping GitHub.')
        return
    log('Step 5/5: committing and pushing to GitHub')
    g, ver = find_git()
    if not g:
        log('  No git on this PC.  Results are saved in the repo folder; push them from your own PC '
            '(GitHub Desktop: commit + Push origin).')
        return
    log('  Using %s' % ver)
    if not os.path.isdir(os.path.join(ROOT, '.git')):
        log('  %s is not a git clone; push from your own PC.' % ROOT)
        return

    ident = []
    if not git(g, ['config', 'user.email'], check=False)[1]:
        ident = ['-c', 'user.name=%s' % GIT_NAME, '-c', 'user.email=%s' % GIT_EMAIL]

    paths = [p for p in GIT_PATHS if os.path.exists(os.path.join(ROOT, *p.split('/')))]
    git(g, ['add', '--'] + paths)
    if git(g, ['diff', '--cached', '--quiet'], check=False)[0] == 0:
        log('  Nothing new to commit (already on GitHub).')
    else:
        title = 'Rev C warning-free rerun (%s): FoS %s' % (JOB_NAME, summary.get('fos', 'see report'))
        body = ['Ran by Stock1_RevC_Job_v1.py on %s.' % time.strftime('%Y-%m-%d %H:%M'),
                '',
                'Weight: %s' % summary.get('weight', 'see report'),
                'Solver: %s' % summary.get('warnings', 'see report'),
                'Overall: %s' % summary.get('overall', 'see report'),
                'Report: results/final_design/FOS_%s.txt' % JOB_NAME,
                'The .odb is local only (over the GitHub size limit); regenerate from job_v2/%s.inp.'
                % JOB_NAME]
        git(g, ident + ['commit', '-m', title, '-m', '\n'.join(body)])
        log('  Committed: %s' % title)

    code, out = git(g, ident + ['pull', '--rebase', '--autostash', 'origin', GIT_BRANCH], check=False)
    if code != 0:
        git(g, ['rebase', '--abort'], check=False)
        log('  Pull from GitHub failed, so nothing was pushed (your commit is safe locally):\n%s\n'
            '  Fix it in GitHub Desktop (Fetch, then Push).' % out)
        return
    code, out = git(g, ['push', 'origin', 'HEAD:%s' % GIT_BRANCH], check=False)
    if code != 0:
        log('  Push failed (sign-in or network?):\n%s\n  The commit is saved locally; push it '
            'later from GitHub Desktop or with "git push".' % out)
        return
    log('  Pushed to github.com/RyanBilock/EMCH-308_Group-6_Final-Project (%s).' % GIT_BRANCH)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
_start_dir = os.getcwd()
try:
    log('Stock1_RevC_Job_v1 starting: %s -> FoS report -> GitHub' % JOB_NAME)
    run_job()
    summary = run_fos()
    refresh_final_design()
    push_to_github(summary)
    log('Done.  Next: update the Status line in Final_Design/README.md with the v2 numbers.')
except Exception as err:
    log('STOPPED: %s' % err)
    raise
finally:
    try:
        os.chdir(_start_dir)
    except Exception:
        pass
