# -*- coding: utf-8 -*-
"""
Organize_Project_v5.py  --  EMCH 308 Team 6, bring a local copy into the Rev C layout
==============================================================================

HOW TO RUN (plain Python, not Abaqus: it calls git)
    Close Abaqus/CAE first (open .cae/.odb files are locked on Windows), then in
    PowerShell or Command Prompt:
        python D:\\EMCH308_repo\\Organize_Project_v5.py
    (use the drive letter where the repo is, e.g. E:\\EMCH308_repo).  It shows
    the plan and asks "Go ahead? [y/N]" before changing anything; add --yes to
    skip the question.  A record goes to archive/logs/Organize_Project_v5_log.txt.

WHAT IT DOES
    1. git fetch origin, then back up anything git is about to overwrite:
       * tracked files you changed locally (Abaqus re-saves a .cae when it is
         opened), and
       * untracked files sitting where GitHub has a different file,
       copied to archive/pre_sync_backup/<date-time>/ with their folders.
    2. git reset --hard origin/main: every tracked file moves to the GitHub
       layout (Rev C = Final_Design/, Rev B = Old_Designs/ and the
       ..._RevB folders).  Untracked and ignored files are not deleted.
    3. Moves the local-only (git-ignored) files git leaves behind:
       * Rev B job leftovers (.dat .log .msg .sta ...) from
         abaqus/final_design/job/ -> abaqus/iterations/Stock1_Drilled_v2_RevB/job/
       * the interrupted Stock1_RevC_v2 rerun (job_v2/ and Stock1_RevC_v2.cae
         /.jnl) -> archive/old_results/Stock1_RevC_v2_interrupted/
         (fix_Stock1_RevC_v1.py makes them again when you rerun it)
       * Abaqus replay files (abaqus.rpy*) and *_log.txt files -> archive/logs/
       * "RevC Warnings.txt" -> archive/error_notes/
       * the superseded Rev C v1 concept sheet -> archive/old_drawings/
    4. Removes folders left empty, then prints git status (should be clean).
    archive/ is local-only (git-ignored), so nothing here is lost or uploaded.
"""
from __future__ import print_function

import datetime
import filecmp
import os
import shutil
import subprocess
import sys

YES = '--yes' in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith('--')]
here = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(args[0]) if args else here
if not (os.path.isdir(os.path.join(ROOT, '.git')) and os.path.isdir(os.path.join(ROOT, 'abaqus'))):
    sys.exit('%s is not the repo folder (no .git and abaqus inside).  Run:  python '
             '<repo folder>\\Organize_Project_v5.py' % ROOT)
STAMP = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
LOG = []


def log(t):
    LOG.append(t)
    print('[ORGANIZE v5] ' + t)


def git(*a, **kw):
    r = subprocess.run(('git',) + a, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True)
    if kw.get('check', True) and r.returncode != 0:
        log('git %s failed:\n%s' % (' '.join(a), r.stderr.strip()))
        save_log()
        sys.exit(1)
    return r.stdout


def save_log():
    d = os.path.join(ROOT, 'archive', 'logs')
    try:
        if not os.path.isdir(d):
            os.makedirs(d)
        with open(os.path.join(d, 'Organize_Project_v5_log.txt'), 'a') as fh:
            fh.write('\n'.join(['', '=== %s ===' % STAMP] + LOG) + '\n')
    except Exception:
        pass


def rel(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


def free_name(dst):
    if not os.path.exists(dst):
        return dst
    b, e = os.path.splitext(dst)
    k = 1
    while os.path.exists('%s_%d%s' % (b, k, e)):
        k += 1
    return '%s_%d%s' % (b, k, e)


def move(src, dst_dir, plan_only, why):
    dst = os.path.join(dst_dir, os.path.basename(src))
    if os.path.isfile(dst) and os.path.isfile(src) and filecmp.cmp(src, dst, shallow=False):
        if not plan_only:
            os.remove(src)
        log('%s %s  (identical copy already in %s/)' % ('would remove' if plan_only else 'removed',
                                                       rel(src), rel(dst_dir)))
        return
    dst = free_name(dst)
    if plan_only:
        log('move %s -> %s   [%s]' % (rel(src), rel(dst), why))
        return
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    shutil.move(src, dst)
    log('moved %s -> %s' % (rel(src), rel(dst)))


# ---------------------------------------------------------------------------
# 0. pre-flight
# ---------------------------------------------------------------------------
locks = []
for d, dirs, files in os.walk(ROOT):
    dirs[:] = [x for x in dirs if x not in ('.git', 'archive')]
    locks += [os.path.join(d, f) for f in files if f.endswith('.lck')]
if locks:
    sys.exit('A job is running or was cut off (%s).  Wait for it / close Abaqus, delete the '
             '.lck if no job runs, and try again.' % ', '.join(rel(x) for x in locks))
log('Repo: %s' % ROOT)
log('Local HEAD %s; fetching origin ...' % git('rev-parse', '--short', 'HEAD').strip())
git('fetch', 'origin')
target = git('rev-parse', '--short', 'origin/main').strip()
log('GitHub main is %s.' % target)
tree = set(git('ls-tree', '-r', '--name-only', 'origin/main').splitlines())

# files git would overwrite: modified tracked + untracked-in-the-way that differ
backup = []
for line in git('status', '--porcelain', '--untracked-files=no').splitlines():
    path = line[3:].strip().strip('"')
    if ' -> ' in path:
        path = path.split(' -> ')[-1]
    if os.path.isfile(os.path.join(ROOT, path)):
        backup.append((path, 'changed locally'))
for path in git('ls-files', '--others', '--exclude-standard').splitlines():
    path = path.strip().strip('"')
    if path in tree:
        h_local = git('hash-object', path).strip()
        h_tree = git('rev-parse', 'origin/main:' + path).strip()
        if h_local != h_tree:
            backup.append((path, 'untracked, differs from GitHub'))


# local-only files to tidy after the reset
def leftovers():
    """Untracked/ignored files only: tracked files are moved by the reset itself."""
    out = []
    j = os.path.join(ROOT, 'abaqus', 'final_design', 'job')
    revb_job = os.path.join(ROOT, 'abaqus', 'iterations', 'Stock1_Drilled_v2_RevB', 'job')
    if os.path.isdir(j):
        for f in sorted(os.listdir(j)):
            if f.startswith('Stock1_Drilled_v2.') and os.path.isfile(os.path.join(j, f)):
                out.append((os.path.join(j, f), revb_job, 'Rev B job file'))
    fd = os.path.join(ROOT, 'abaqus', 'final_design')
    v2 = os.path.join(ROOT, 'archive', 'old_results', 'Stock1_RevC_v2_interrupted')
    jv2 = os.path.join(fd, 'job_v2')
    if os.path.isdir(jv2):
        sta = os.path.join(jv2, 'Stock1_RevC_v2.sta')
        done = os.path.isfile(sta) and 'COMPLETED SUCCESSFULLY' in open(sta).read()
        if not done:
            for f in sorted(os.listdir(jv2)):
                out.append((os.path.join(jv2, f), v2, 'interrupted v2 rerun'))
            for f in ('Stock1_RevC_v2.cae', 'Stock1_RevC_v2.jnl'):
                if os.path.isfile(os.path.join(fd, f)):
                    out.append((os.path.join(fd, f), v2, 'interrupted v2 rerun'))
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in ('.git', 'archive', 'job_v2')]
        for f in files:
            p = os.path.join(d, f)
            if f.startswith('abaqus.rpy'):
                out.append((p, os.path.join(ROOT, 'archive', 'logs', 'abaqus_rpy',
                                            rel(d).replace('/', '__')), 'Abaqus replay file'))
            elif f.endswith('_log.txt'):
                out.append((p, os.path.join(ROOT, 'archive', 'logs'), 'log file'))
            elif f == 'RevC Warnings.txt':
                out.append((p, os.path.join(ROOT, 'archive', 'error_notes'), 'warning notes'))
            elif f.startswith('Proposal_RevC_Stock1_SawTrim_v1'):
                out.append((p, os.path.join(ROOT, 'archive', 'old_drawings'), 'superseded concept'))
    tracked = set(git('ls-files').splitlines())
    return [o for o in out if rel(o[0]) not in tracked]


# ---------------------------------------------------------------------------
# 1. plan + confirmation
# ---------------------------------------------------------------------------
log('PLAN')
for path, why in backup:
    log('back up %s -> archive/pre_sync_backup/%s/  [%s]' % (path, STAMP, why))
log('git reset --hard origin/main  (%s)' % target)
for src, dst, why in leftovers():
    move(src, dst, True, why)
log('then remove empty folders and show git status')
if not YES:
    try:
        ans = input('Go ahead? [y/N] ').strip().lower()
    except EOFError:
        ans = ''
    if ans not in ('y', 'yes'):
        log('Stopped; nothing changed.')
        save_log()
        sys.exit(0)

# ---------------------------------------------------------------------------
# 2. back up, reset, tidy
# ---------------------------------------------------------------------------
bdir = os.path.join(ROOT, 'archive', 'pre_sync_backup', STAMP)
for path, why in backup:
    dst = os.path.join(bdir, path)
    if not os.path.isdir(os.path.dirname(dst)):
        os.makedirs(os.path.dirname(dst))
    shutil.copy2(os.path.join(ROOT, path), dst)
    log('backed up %s' % path)
log(git('reset', '--hard', 'origin/main').strip())
for src, dst, why in leftovers():
    if os.path.exists(src):
        move(src, dst, False, why)

removed = 0
for d, dirs, files in os.walk(ROOT, topdown=False):
    if '.git' in d.split(os.sep) or rel(d).startswith('archive'):
        continue
    if d != ROOT and not os.listdir(d):
        os.rmdir(d)
        removed += 1
log('Removed %d empty folder%s.' % (removed, '' if removed == 1 else 's'))
st = git('status', '--short').strip()
log('git status: %s' % ('clean' if not st else '\n' + st))
log('Done.  The folder now matches GitHub %s; local-only files are in archive/.' % target)
save_log()
