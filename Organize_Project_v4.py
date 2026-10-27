# -*- coding: utf-8 -*-
"""
Organize_Project_v4.py  --  EMCH 308 Team 6, finish matching the GitHub layout
==============================================================================

HOW TO RUN (either way works)
    Abaqus/CAE:  File > Set Work Directory -> E:\\Semester_Project_GitHub
                 File > Run Script         -> Organize_Project_v4.py
    Python:      python Organize_Project_v4.py "E:\\Semester_Project_GitHub"
    A confirmation box (in Abaqus) lists every change before anything happens.
    A record is written to archive\\logs\\Organize_Project_v4_log.txt.

WHAT IT DOES (only the files named below are touched)
    cad\\
      * deletes Creo session files: trail.txt.1, .2, .3
      * deletes the Creo part copies usc06_mtc06_ibeam_revb_.prt.1/.2/.3 from cad\\
        -- the latest version (.prt.3) is already saved in cad\\creo\\
      * moves the STEP export log and the Creo import log (.xml) to archive\\logs\\
    abaqus\\python\\final\\
      * removes Export_STEP_v1.py and Export_STEP_v2.py; identical copies are in
        abaqus\\python\\iterations\\ (Export_STEP_v3.py is the current one).
        A file is only deleted if its copy matches byte for byte; otherwise it
        is moved to archive\\old_scripts\\ instead.
"""
from __future__ import print_function

import os
import shutil
import sys

IN_CAE = False
try:
    from abaqus import getWarningReply
    from abaqusConstants import YES
    IN_CAE = True
except Exception:
    pass

if not IN_CAE and len(sys.argv) > 1 and os.path.isdir(sys.argv[-1]):
    ROOT = os.path.abspath(sys.argv[-1])
else:
    ROOT = os.getcwd()

if not (os.path.isdir(os.path.join(ROOT, 'abaqus')) and os.path.isdir(os.path.join(ROOT, 'cad'))):
    raise RuntimeError('%s is not the project folder (no abaqus\\ and cad\\ inside).  Set the '
                       'work directory to E:\\Semester_Project_GitHub and run again.' % ROOT)

LOG = []


def log(t):
    LOG.append(t)
    print('[ORGANIZE v4] ' + t)


def same(a, b):
    try:
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        fa, fb = open(a, 'rb'), open(b, 'rb')
        r = fa.read() == fb.read()
        fa.close(); fb.close()
        return r
    except Exception:
        return False


j = lambda *p: os.path.join(ROOT, *p)
deletes, moves = [], []
for n in ('trail.txt.1', 'trail.txt.2', 'trail.txt.3'):
    if os.path.isfile(j('cad', n)):
        deletes.append(j('cad', n))
creo_latest = j('cad', 'creo', 'usc06_mtc06_ibeam_revb_.prt.3')
for n in ('usc06_mtc06_ibeam_revb_.prt.1', 'usc06_mtc06_ibeam_revb_.prt.2',
          'usc06_mtc06_ibeam_revb_.prt.3'):
    p = j('cad', n)
    if os.path.isfile(p):
        if n.endswith('.3') and not same(p, creo_latest):
            moves.append((p, creo_latest if not os.path.exists(creo_latest)
                          else j('archive', 'old_models', n)))
        else:
            deletes.append(p)
for n in ('USC06_MTC06_IBeam_RevB_export_log.txt', 'USC06_MTC06_IBeam_RevB_log.xml'):
    if os.path.isfile(j('cad', n)):
        moves.append((j('cad', n), j('archive', 'logs', n)))
for n in ('Export_STEP_v1.py', 'Export_STEP_v2.py'):
    p = j('abaqus', 'python', 'final', n)
    if os.path.isfile(p):
        if same(p, j('abaqus', 'python', 'iterations', n)):
            deletes.append(p)
        else:
            moves.append((p, j('archive', 'old_scripts', n)))

if not deletes and not moves:
    log('Nothing to do: the folder already matches the GitHub layout.')
else:
    summary = 'Folder: %s\n\nDelete %d files:\n  %s\n\nMove %d files:\n  %s\n\nContinue?' % (
        ROOT, len(deletes), '\n  '.join(os.path.relpath(p, ROOT) for p in deletes) or '-',
        len(moves), '\n  '.join('%s -> %s' % (os.path.relpath(a, ROOT), os.path.relpath(b, ROOT))
                                for a, b in moves) or '-')
    log(summary.replace('\n\nContinue?', ''))
    go = True
    if IN_CAE:
        try:
            from abaqusConstants import NO
            go = getWarningReply(message=summary, buttons=(YES, NO)) == YES
        except Exception:
            go = True
    if not go:
        log('Cancelled; nothing changed.')
    else:
        for a, b in moves:
            try:
                if not os.path.isdir(os.path.dirname(b)):
                    os.makedirs(os.path.dirname(b))
                if os.path.exists(b):
                    log('SKIP (exists): ' + os.path.relpath(b, ROOT))
                    continue
                shutil.move(a, b)
                log('moved   ' + os.path.relpath(a, ROOT) + ' -> ' + os.path.relpath(b, ROOT))
            except Exception as err:
                log('could not move %s (%s)' % (a, err))
        for p in deletes:
            try:
                os.remove(p)
                log('deleted ' + os.path.relpath(p, ROOT))
            except Exception as err:
                log('could not delete %s (%s)' % (p, err))
        log('Done.')

try:
    d = j('archive', 'logs')
    if not os.path.isdir(d):
        os.makedirs(d)
    fh = open(os.path.join(d, 'Organize_Project_v4_log.txt'), 'a')
    fh.write('\n'.join(LOG) + '\n')
    fh.close()
except Exception:
    pass
