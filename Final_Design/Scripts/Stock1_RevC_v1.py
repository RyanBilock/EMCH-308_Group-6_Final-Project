# -*- coding: utf-8 -*-
"""
Stock1_RevC_v1.py  --  EMCH 308 Team 6, Rev C beam: build, finest mesh, job
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> abaqus/base_models/  (the folder that
                                        holds the original ProjectBeam.cae)
    2. File > Run Script...          -> abaqus/python/final/Stock1_RevC_v1.py
    The script opens the untouched ProjectBeam.cae, builds the Rev C beam,
    meshes it as finely as the licence allows, and submits the job.
    Inside the repo it saves straight into abaqus/final_design/:
        Stock1_RevC_v1.cae             model only
        job/Stock1_RevC_v1.cae         model with its job
        job/Stock1_RevC_v1.odb ...     job files (the solver writes them here)
        job/Stock1_RevC_v1_geometry.txt   CAD volumes, read by the FOS script
    Progress is in the message area and in Stock1_RevC_v1_log.txt (work dir).
    When the Job Monitor shows "Completed", run FOS_Stock1_RevC_v1.py.

    MESH CHECK (optional, for the accuracy report): set MESH_LEVEL = 'CHECK'
    below and run the script again.  It builds the same beam with the Rev B
    mesh density (0.10 in seed) as job Stock1_RevC_v1_MeshCheck in
    abaqus/final_design/mesh_check/.  FOS_Stock1_RevC_v1.py compares the two
    meshes when both have run: if FOS and stiffness barely change between
    them, the fine mesh is converged.

REV C GEOMETRY  (Stock 1 = AA I 3 x 2.03, 6061-T6; z measured from mid-span)
    * Length 8.40 in: the full raw stock length, no cross-cut.  Support span
      stays 8.00 in, so 0.20 in of beam extends past each support (Rev B 0.10).
    * Web: the four required Fig. 1 holes, dia 1.03 (1-1/32 drill), at
      z = +/-1.00 (y +0.375) and z = +/-3.00 (y -0.375).  Nothing else.
    * Flanges stay full width (2.50) wherever a roller touches:
        top flange    |z| <= 0.75   (load roller)
        bottom flange |z| >= 3.50   (support rollers)
      Elsewhere the flange tips are notched 0.65 deep (flange 1.20 wide):
        top flange:    4 notches, z = 0.75 to the end, both edges, both halves
        bottom flange: 2 notches, z = -3.50 to +3.50, both edges
      Every inside corner is R0.25 (a dia 0.50 relief hole is drilled there
      first and the saw cuts end on it).
    Hand calculation: 0.914 lb at 0.098 lb/in^3, $131.78.

MESH ("as detailed as possible")
    The Academic Teaching licence allows 250,000 nodes in the model.  The
    script searches for the smallest global element size that keeps the beam
    under NODE_TARGET (240,000) nodes, with tighter curvature control so the
    holes, fillets and notch corners are followed closely.  It then tries a
    few nearby settings and keeps the one with no distorted elements.
    Elements: C3D10, 10-node quadratic tetrahedra (curved edges).
    Meshing takes several tries at this size: allow 20-45 min before the job
    is submitted.  The fine job itself takes roughly 1-3 hours.

LOADING AND OUTPUT
    Top roller pushed down 0.080 in (displacement control, RF2 = load).
    Increments of at most 1 % of the step (>= 100 points on the
    load-displacement curve) so the offset-line crossing is well resolved.
    Field output (S, PE, PEEQ, U, RF, CSTRESS) at 10 frames keeps the .odb
    small enough for Git LFS; RF2/U2 history is written every increment.

Everything else (contact, rollers, boundary conditions, mesh-quality checks,
licence-limit check) is unchanged from Stock1_Drilled_v2.py (Rev B), which
holds the history of every fix (fix_ProjectBeam v1-v5).

UNITS: in, kip, ksi.  Works with the Python 3 (2024+) and Python 2.7 builds.
"""
from __future__ import print_function

import os
import math

from abaqus import *
from abaqusConstants import *
import mesh

# File > Run Script executes inside the CAE namespace, where Abaqus's
# XY-data operators (sum, abs, min, max, ...) replace the Python built-ins and
# reject ordinary numbers and generators.  Put the real built-ins back.
try:
    import builtins as _py_builtins          # Python 3 (Abaqus 2024+)
except ImportError:
    import __builtin__ as _py_builtins       # Python 2.7 (older Abaqus)
sum = _py_builtins.sum
abs = _py_builtins.abs
min = _py_builtins.min
max = _py_builtins.max
round = _py_builtins.round
pow = _py_builtins.pow


# ---------------------------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------------------------
MESH_LEVEL   = 'FINE'   # 'FINE' = finest mesh under the licence limit (the real job)
                        # 'CHECK' = Rev B mesh density, for the mesh-convergence check

CAE_NAME     = 'ProjectBeam.cae'   # opened from the work dir if nothing is open
MODEL_NAME   = 'Project'
BEAM_PART    = 'Beam'
TOP_PART     = 'TopRoller'
BOT_PART     = 'BotRoller'

R_TOP        = 0.492    # in  loading roller radius   (0.984 in diameter)
R_BOT        = 0.197    # in  support roller radius   (0.394 in diameter)
SPAN         = 8.0      # in  support centre-to-centre distance (test fixture)
BEAM_LENGTH  = 8.4      # in  overall beam length (full raw stock, no cross-cut)
S1_H, S1_BF, S1_TF, S1_TW, S1_RF = 3.00, 2.50, 0.26, 0.15, 0.25  # Stock 1, in

HOLE_R       = 0.515    # in  Fig. 1 access holes, dia 1.03 (1-1/32 drill = 1.031)
HOLES        = ((-3.0, -0.375), (-1.0, 0.375), (1.0, 0.375), (3.0, -0.375))
                        # (z from mid-span, y from mid-height) of each hole

NOTCH_DEPTH  = 0.65     # in  notch depth from each flange tip (flange left 1.20 wide)
NOTCH_R      = 0.25     # in  inside-corner radius (dia 0.50 relief drill)
TOP_PAD_Z    = 0.75     # in  top flange full width for |z| <= this (load roller)
BOT_PAD_Z    = 3.50     # in  bottom flange full width for |z| >= this (supports)

U_TARGET     = 0.08     # in  top-roller travel (RF2 vs U2 = load-deflection)
TOP_ADJUST_TOL = 1.0e-3 # in  strain-free gap closure, top roller only
MAX_INC      = 0.01     # largest increment, fraction of the step (0.02 in Rev B)
FIELD_FRAMES = 10       # field-output frames in the step (history: every inc)
FIELD_VARS   = ('S', 'PE', 'PEEQ', 'U', 'RF', 'CSTRESS')

REMESH       = True
NODE_LIMIT   = 250000   # Academic Teaching licence limit (nodes, whole model)
NODE_TARGET  = 240000   # FINE: largest beam mesh allowed (margin for the 3 roller nodes)
FILL_TARGET  = 0.93     # FINE: accept a size once the mesh fills this share of NODE_TARGET
SEED_START   = 0.080    # in  FINE: first element size tried (about 200,000 nodes expected)
CURV_DEV_FINE = 0.05    # FINE: curvature control (Rev B used 0.10; smaller follows curves closer)
MIN_SIZE_FINE = 0.10    # FINE: minimum size factor
SIZE_ITERS   = 6        # FINE: size-search tries
# CHECK level: the Rev B sweep (global seed, curvature deviation, min size factor)
MESH_SWEEP = ((0.100, 0.10, 0.10), (0.100, 0.10, 0.30), (0.105, 0.10, 0.10),
              (0.095, 0.10, 0.10), (0.100, 0.07, 0.10), (0.100, 0.15, 0.10))
IGNORE_TANGENT_SEAMS = True   # stage 2: ignore smooth seams if elements are still flagged
TANGENT_DEG  = 5.0      # faces meeting within this angle count as a smooth seam

JOB_BASE     = 'Stock1_RevC_v1'
SAVE_IN_REPO = True     # inside the repo: save to abaqus/final_design/ (else: work dir)
CREATE_JOB   = True
NUM_CPUS     = 4        # capped at the number of processors on the machine
SUBMIT_JOB   = True     # also submit the job (False = create only)

RHO          = 0.0975   # lb/in^3, 6061 (value used by the Rev B reports)
RHO_SHEET    = 0.098    # lb/in^3, basis of the 2.03 lb/ft cost-sheet weight
GEOM_TOL     = 1.0e-4   # in

if MESH_LEVEL not in ('FINE', 'CHECK'):
    raise RuntimeError("MESH_LEVEL must be 'FINE' or 'CHECK' (it is %r)." % (MESH_LEVEL,))
JOB_NAME   = JOB_BASE if MESH_LEVEL == 'FINE' else JOB_BASE + '_MeshCheck'
JOB_FOLDER = 'job' if MESH_LEVEL == 'FINE' else 'mesh_check'


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
LOG_PATH = os.path.join(os.getcwd(), JOB_NAME + '_log.txt')
try:
    open(LOG_PATH, 'w').close()
except Exception:
    LOG_PATH = None


def log(text):
    line = '[Stock1_RevC] ' + text
    print(line)
    if LOG_PATH:
        try:
            fh = open(LOG_PATH, 'a')
            fh.write(line + '\n')
            fh.close()
        except Exception:
            pass


def attempt(fn, what):
    """Run fn(); log and carry on if it fails (used for optional steps)."""
    try:
        return fn()
    except Exception as err:
        log('NOTE: %s skipped (%s)' % (what, err))
        return None


def first_rp(inst):
    rps = list(inst.referencePoints.values())
    if not rps:
        raise RuntimeError('Instance %s has no reference point.' % inst.name)
    return rps[0]


def dist(p, q):
    return math.sqrt(sum((float(a_) - float(b_)) ** 2 for a_, b_ in zip(p, q)))


def faces_through_plane(inst, y, x_lo, x_hi, z_lo, z_hi):
    """Beam faces that contain sample points on the plane y = const.
    Works even when partitions or virtual topology split or merge faces."""
    idx = set()
    w = x_hi - x_lo
    xs_ = [x_lo + f * w for f in (0.2, 0.35, 0.5, 0.65, 0.8)]
    n = 60
    zs_ = [z_lo + (z_hi - z_lo) * (k + 0.5) / n for k in range(n)]
    for x in xs_:
        for z in zs_:
            try:
                found = inst.faces.findAt(((x, y, z),))
                for f in found:
                    if f is not None:
                        idx.add(f.index)
            except Exception:
                pass
    seq = None
    for i in sorted(idx):
        s = inst.faces[i:i + 1]
        seq = s if seq is None else seq + s
    return seq, len(idx)


def faces_in_box(inst, y, x_lo, x_hi, z_lo, z_hi):
    big = 1.0
    seq = inst.faces.getByBoundingBox(
        xMin=x_lo - big, yMin=y - GEOM_TOL, zMin=z_lo - big,
        xMax=x_hi + big, yMax=y + GEOM_TOL, zMax=z_hi + big)
    return seq, len(seq)


def nearest_node(inst, pt, y_band=None):
    """Mesh node of inst closest to pt (optionally only nodes with
    |y - y_band| < 1e-3, i.e. on the flange face)."""
    best, dbest = None, 1.0e30
    for nd in inst.nodes:
        c = nd.coordinates
        if y_band is not None and abs(c[1] - y_band) > 1.0e-3:
            continue
        d = (c[0] - pt[0]) ** 2 + (c[1] - pt[1]) ** 2 + (c[2] - pt[2]) ** 2
        if d < dbest:
            best, dbest = nd, d
    if best is None:
        raise RuntimeError('No beam node found near (%.3f, %.3f, %.3f).' % pt)
    return best


def node_set(asm, name, inst, nodes):
    if name in asm.sets.keys():
        del asm.sets[name]
    labels = tuple(sorted(set(n.label for n in nodes)))
    asm.Set(name=name, nodes=inst.nodes.sequenceFromLabels(labels))
    return asm.sets[name]


# ---------------------------------------------------------------------------
# 0. model database and model
# ---------------------------------------------------------------------------
def find_model(db):
    if MODEL_NAME in db.models.keys():
        return MODEL_NAME
    for name in db.models.keys():
        if BEAM_PART in db.models[name].parts.keys():
            return name
    return None


log('Stock1_RevC_v1 starting (MESH_LEVEL = %s, job %s)' % (MESH_LEVEL, JOB_NAME))
# Always start from the untouched original so leftovers from an earlier run
# (old seeds, a bloated mesh in *_fixed.cae) can't carry over.
cae_path = os.path.join(os.getcwd(), CAE_NAME)
if os.path.exists(cae_path):
    log('Opening the original %s' % cae_path)
    mdb = openMdb(pathName=cae_path)
elif mdb.pathName.lower().endswith('_fixed.cae'):
    raise RuntimeError('%s is not in the work directory (%s).  Use File > Set Work '
                       'Directory to point at the folder with the original model.'
                       % (CAE_NAME, os.getcwd()))
model_name = find_model(mdb)
if model_name is None:
    raise RuntimeError('No model with a "%s" part found.  Set the work directory '
                       'to the folder holding %s and run again.' % (BEAM_PART, CAE_NAME))
if model_name != MODEL_NAME:
    log('Model "%s" not found; using "%s".' % (MODEL_NAME, model_name))
model = mdb.models[model_name]
a = model.rootAssembly
log('Model "%s", work directory %s' % (model_name, os.getcwd()))

# ---------------------------------------------------------------------------
# 1. instances: exactly 1 beam, 1 top roller, 2 bottom rollers
# ---------------------------------------------------------------------------
beam_insts = [i for i in a.instances.values() if i.partName == BEAM_PART]
if not beam_insts:
    raise RuntimeError('No instance of part "%s" in the assembly.' % BEAM_PART)
beam_insts.sort(key=lambda i: (i.name != 'Beam-1', i.name))
extra_beams = [i.name for i in beam_insts[1:]]     # deleted in section 2
beam_name = beam_insts[0].name

top_insts = [i for i in a.instances.values() if i.partName == TOP_PART]
bot_insts = [i for i in a.instances.values() if i.partName == BOT_PART]
if len(top_insts) != 1 or len(bot_insts) != 2:
    raise RuntimeError('Expected 1 "%s" and 2 "%s" instances; found %d and %d.'
                       % (TOP_PART, BOT_PART, len(top_insts), len(bot_insts)))
top = top_insts[0]
for inst in [beam_insts[0], top] + bot_insts:
    if not inst.dependent:
        log('NOTE: instance %s is independent.' % inst.name)

# ---------------------------------------------------------------------------
# 2. clear old analysis set-up (steps, contact, loads, BCs, old surfaces)
# ---------------------------------------------------------------------------
for sname in reversed(list(model.steps.keys())):
    if sname != 'Initial':
        del model.steps[sname]
        log('Deleted step "%s" (with its loads, outputs and stabilization).' % sname)
for iname in list(model.interactions.keys()):
    del model.interactions[iname]
    log('Deleted interaction "%s".' % iname)
for lname in list(model.loads.keys()):
    del model.loads[lname]
for bname in list(model.boundaryConditions.keys()):
    del model.boundaryConditions[bname]
    log('Deleted BC "%s" (rebuilt below).' % bname)
for sname in list(a.surfaces.keys()):
    if sname.startswith('CS_') or sname in ('General_Contact_Faces',):
        del a.surfaces[sname]
if os.path.exists(os.path.join(os.getcwd(), JOB_NAME + '.lck')):
    log('NOTE: %s.lck exists (an earlier run was cut off); using job name %s_b.'
        % (JOB_NAME, JOB_NAME))
    JOB_NAME += '_b'
for jn in list(mdb.jobs.keys()):
    del mdb.jobs[jn]
    log('Removed old job definition "%s" from this model database.' % jn)
for name in extra_beams:
    del a.features[name]
    log('Deleted duplicate beam instance "%s" (was an unconnected region).' % name)
a.regenerate()
beam = a.instances[beam_name]

# ---------------------------------------------------------------------------
# 2a. Rev C beam: Stock 1 (AA I 3 x 2.03), Fig. 1 holes, flange notches
# ---------------------------------------------------------------------------
def arc(sk, c, p1, p2):
    """Quarter arc from p1 to p2 about c, direction worked out from geometry."""
    cross = (p1[0] - c[0]) * (p2[1] - c[1]) - (p1[1] - c[1]) * (p2[0] - c[0])
    sk.ArcByCenterEnds(center=c, point1=p1, point2=p2,
                       direction=COUNTERCLOCKWISE if cross > 0 else CLOCKWISE)


def build_stock1_part():
    h2, b2, tf, t2, r = S1_H / 2.0, S1_BF / 2.0, S1_TF, S1_TW / 2.0, S1_RF
    yi, xf = h2 - tf, t2 + r          # flange inner face, fillet centre x
    yf = yi - r                       # fillet centre y
    sk = model.ConstrainedSketch(name='__s1profile__', sheetSize=10.0)
    L_ = lambda q1, q2: sk.Line(point1=q1, point2=q2)
    L_((-b2, h2), (b2, h2)); L_((b2, h2), (b2, yi)); L_((b2, yi), (xf, yi))
    arc(sk, (xf, yf), (xf, yi), (t2, yf))
    L_((t2, yf), (t2, -yf))
    arc(sk, (xf, -yf), (t2, -yf), (xf, -yi))
    L_((xf, -yi), (b2, -yi)); L_((b2, -yi), (b2, -h2)); L_((b2, -h2), (-b2, -h2))
    L_((-b2, -h2), (-b2, -yi)); L_((-b2, -yi), (-xf, -yi))
    arc(sk, (-xf, -yf), (-xf, -yi), (-t2, -yf))
    L_((-t2, -yf), (-t2, yf))
    arc(sk, (-xf, yf), (-t2, yf), (-xf, yi))
    L_((-xf, yi), (-b2, yi)); L_((-b2, yi), (-b2, h2))
    part = model.Part(name=BEAM_PART, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    part.BaseSolidExtrude(sketch=sk, depth=BEAM_LENGTH)
    del model.sketches['__s1profile__']
    return part


def sketch_cut(part, plane, offset, up, origin, draw, check, label, depth=None):
    """Through-all cut from a datum plane outside the beam.  The extrude
    direction and the sketch's vertical sense are not assumed: each of the
    four combinations is tried and kept only if check(removed volume) passes."""
    dp = part.datums[part.DatumPlaneByPrincipalPlane(principalPlane=plane,
                                                     offset=offset).id]
    ax = part.datums[part.DatumAxisByPrincipalAxis(principalAxis=up).id]
    for flip in (OFF, ON):
        for mv in (1.0, -1.0):
            v0 = part.getVolume()
            t = part.MakeSketchTransform(sketchPlane=dp, sketchUpEdge=ax,
                                         sketchPlaneSide=SIDE1,
                                         sketchOrientation=RIGHT, origin=origin)
            sk = model.ConstrainedSketch(name='__cut__', sheetSize=20.0, transform=t)
            draw(sk, mv)
            feat = None
            try:
                kw_d = {} if depth is None else {'depth': depth}
                feat = part.CutExtrude(sketchPlane=dp, sketchUpEdge=ax,
                                       sketchPlaneSide=SIDE1, sketchOrientation=RIGHT,
                                       sketch=sk, flipExtrudeDirection=flip, **kw_d)
            except Exception as err:
                log('  %s: try (flip %s, %+d) not made: %s' % (label, flip, mv, err))
            del model.sketches['__cut__']
            if feat is None:
                continue
            dv = v0 - part.getVolume()
            if check(dv):
                log('%s cut: %.4f in^3 removed (%.4f lb).' % (label, dv, dv * RHO))
                return dv
            part.deleteFeatures((feat.name,))
    raise RuntimeError('%s cut could not be made with the expected volume.' % label)


def hole_edges_ok(part):
    """True when all four Fig. 1 holes sit where they should (an edge on a
    0.5 in circle around each expected centre)."""
    lo_ = [min(v.pointOn[0][i] for v in part.vertices) for i in range(3)]
    hi_ = [max(v.pointOn[0][i] for v in part.vertices) for i in range(3)]
    cy, cz = 0.5 * (lo_[1] + hi_[1]), 0.5 * (lo_[2] + hi_[2])
    found = 0
    for dz, dy in HOLES:
        for e in part.edges:
            q = e.pointOn[0]
            if abs(math.hypot(q[2] - cz - dz, q[1] - cy - dy) - HOLE_R) < 2.0e-3:
                found += 1
                break
    return found == len(HOLES)


def draw_holes(sk, mv):
    for dz, dy in HOLES:
        sk.CircleByCenterPerimeter(center=(dz, mv * dy), point1=(dz + HOLE_R, mv * dy))


def draw_top_notches(sk, mv):
    """Top flange, plan view: 4 notches from z = TOP_PAD_Z out past the beam
    end, from x = flange half-width - NOTCH_DEPTH out past the tip, R corner at
    the inside corner.  Horizontal = x, vertical = z; symmetric in both."""
    hz = BEAM_LENGTH / 2.0
    xi, zi, R = S1_BF / 2.0 - NOTCH_DEPTH, TOP_PAD_Z, NOTCH_R
    xo, zo = S1_BF / 2.0 + 0.35, hz + 0.35
    for sx in (1.0, -1.0):
        for sz in (1.0, -1.0):
            P = lambda x, z: (sx * x, sz * z)
            sk.Line(point1=P(xo, zi), point2=P(xi + R, zi))
            arc(sk, P(xi + R, zi + R), P(xi + R, zi), P(xi, zi + R))
            sk.Line(point1=P(xi, zi + R), point2=P(xi, zo))
            sk.Line(point1=P(xi, zo), point2=P(xo, zo))
            sk.Line(point1=P(xo, zo), point2=P(xo, zi))


def draw_bottom_notches(sk, mv):
    """Bottom flange, plan view: 2 notches from z = -BOT_PAD_Z to +BOT_PAD_Z,
    one per flange edge, R corners at both ends.  Horizontal = x, vertical = z."""
    xi, z2, R = S1_BF / 2.0 - NOTCH_DEPTH, BOT_PAD_Z, NOTCH_R
    xo = S1_BF / 2.0 + 0.35
    for sx in (1.0, -1.0):
        P = lambda x, z: (sx * x, z)
        sk.Line(point1=P(xo, -z2), point2=P(xi + R, -z2))
        arc(sk, P(xi + R, -z2 + R), P(xi + R, -z2), P(xi, -z2 + R))
        sk.Line(point1=P(xi, -z2 + R), point2=P(xi, z2 - R))
        arc(sk, P(xi + R, z2 - R), P(xi, z2 - R), P(xi + R, z2))
        sk.Line(point1=P(xi + R, z2), point2=P(xo, z2))
        sk.Line(point1=P(xo, z2), point2=P(xo, -z2))


# layout sanity checks
_x_in = S1_BF / 2.0 - NOTCH_DEPTH
if _x_in - NOTCH_R < S1_TW / 2.0 + S1_RF:
    raise RuntimeError('Notch corner (x = %.3f) reaches the web fillet (x = %.3f).'
                       % (_x_in - NOTCH_R, S1_TW / 2.0 + S1_RF))
if TOP_PAD_Z + NOTCH_R >= BEAM_LENGTH / 2.0 or BOT_PAD_Z >= SPAN / 2.0:
    raise RuntimeError('Pad lengths do not fit the beam: check TOP_PAD_Z / BOT_PAD_Z.')
log('Rev C layout: notches %.2f deep (flange %.2f wide), R%.2f corners; top pad |z| <= %.2f, '
    'bottom pads |z| >= %.2f; web holes dia %.3f.'
    % (NOTCH_DEPTH, S1_BF - 2 * NOTCH_DEPTH, NOTCH_R, TOP_PAD_Z, BOT_PAD_Z, 2 * HOLE_R))

# replace the Stock 3 beam of ProjectBeam.cae: instances, assembly sets/surfaces, part
for nm in [i.name for i in a.instances.values() if i.partName == BEAM_PART]:
    del a.features[nm]
for nm in list(a.surfaces.keys()):
    del a.surfaces[nm]
for nm in list(a.sets.keys()):
    del a.sets[nm]
if BEAM_PART in model.parts.keys():
    del model.parts[BEAM_PART]
p = build_stock1_part()
v_blank = p.getVolume()
log('Stock 1 blank (AA I 3 x 2.03, %.2f in): %.4f in^3, %.3f lb.'
    % (BEAM_LENGTH, v_blank, v_blank * RHO))

v_holes_exp = len(HOLES) * math.pi * HOLE_R ** 2 * S1_TW
v_holes = sketch_cut(p, YZPLANE, S1_BF / 2.0 + 0.30, YAXIS,
                     (S1_BF / 2.0 + 0.30, 0.0, BEAM_LENGTH / 2.0), draw_holes,
                     lambda dv: abs(dv - v_holes_exp) < 0.05 * v_holes_exp and hole_edges_ok(p),
                     'Fig. 1 holes (4 x dia %.3f)' % (2 * HOLE_R))

_corner = (1.0 - math.pi / 4.0) * NOTCH_R ** 2            # material left in each R corner
a_top = NOTCH_DEPTH * (BEAM_LENGTH / 2.0 - TOP_PAD_Z) - _corner
a_bot = NOTCH_DEPTH * (2.0 * BOT_PAD_Z) - 2.0 * _corner
v_top_exp = 4.0 * a_top * S1_TF
v_bot_exp = 2.0 * a_bot * S1_TF
cut_depth = 0.20 + S1_TF + 0.10          # from a plane 0.20 outside the flange, that flange only
v_top = sketch_cut(p, XZPLANE, S1_H / 2.0 + 0.20, ZAXIS, (0.0, S1_H / 2.0 + 0.20, BEAM_LENGTH / 2.0),
                   draw_top_notches, lambda dv: abs(dv - v_top_exp) < 0.02 * v_top_exp,
                   'Top-flange notches (4 x %.2f deep, %.2f long)'
                   % (NOTCH_DEPTH, BEAM_LENGTH / 2.0 - TOP_PAD_Z), depth=cut_depth)
v_bot = sketch_cut(p, XZPLANE, -(S1_H / 2.0 + 0.20), ZAXIS,
                   (0.0, -(S1_H / 2.0 + 0.20), BEAM_LENGTH / 2.0),
                   draw_bottom_notches, lambda dv: abs(dv - v_bot_exp) < 0.02 * v_bot_exp,
                   'Bottom-flange notches (2 x %.2f deep, %.2f long)'
                   % (NOTCH_DEPTH, 2.0 * BOT_PAD_Z), depth=cut_depth)
v_final = p.getVolume()
log('Finished Rev C beam (CAD): %.4f in^3 -> %.4f lb at %.4f lb/in^3, %.4f lb at %.3f lb/in^3 '
    '(limit 1.000 lb) -> %s'
    % (v_final, v_final * RHO, RHO, v_final * RHO_SHEET, RHO_SHEET,
       'MEETS' if v_final * RHO_SHEET <= 1.0 else 'OVER'))
GEOMETRY = dict(beam_length_in=BEAM_LENGTH, cad_blank_in3=v_blank, cad_web_holes_in3=v_holes,
                cad_top_notches_in3=v_top, cad_bottom_notches_in3=v_bot,
                cad_volume_in3=v_final, hand_calc_lb_at_0p098=0.914,
                web_hole_dia_in=2 * HOLE_R, notch_depth_in=NOTCH_DEPTH)
a.Instance(name='Beam-1', part=p, dependent=ON)
beam_name = 'Beam-1'
a.regenerate()
beam = a.instances[beam_name]

# ---------------------------------------------------------------------------
# 2b. beam length: trim equally from both ends (holes stay centred)
# ---------------------------------------------------------------------------
p = model.parts[BEAM_PART]


def part_box():
    vs = [v.pointOn[0] for v in p.vertices]
    return ([min(v[i] for v in vs) for i in range(3)],
            [max(v[i] for v in vs) for i in range(3)])


def cut_end(z_plane, inward, depth, xc, yc):
    """Remove a slab 'depth' thick at the end face z = z_plane.  The cut
    direction is checked against the part box and flipped if needed."""
    dp = p.datums[p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE,
                                               offset=z_plane).id]
    ax = p.datums[p.DatumAxisByPrincipalAxis(principalAxis=YAXIS).id]
    target = z_plane + inward * depth
    for flip in (OFF, ON):
        t = p.MakeSketchTransform(sketchPlane=dp, sketchUpEdge=ax,
                                  sketchPlaneSide=SIDE1, sketchOrientation=RIGHT,
                                  origin=(xc, yc, z_plane))
        sk = model.ConstrainedSketch(name='__trim__', sheetSize=20.0, transform=t)
        sk.rectangle(point1=(-5.0, -5.0), point2=(5.0, 5.0))
        feat = None
        try:
            feat = p.CutExtrude(sketchPlane=dp, sketchUpEdge=ax, sketchPlaneSide=SIDE1,
                                sketchOrientation=RIGHT, sketch=sk, depth=depth,
                                flipExtrudeDirection=flip)
        except Exception as err:
            log('  end cut at z = %.3f (flip %s) not made: %s' % (z_plane, flip, err))
        del model.sketches['__trim__']
        if feat is None:
            continue
        lo, hi = part_box()
        end_now = lo[2] if inward > 0 else hi[2]
        if abs(end_now - target) < 1.0e-4:
            return
        p.deleteFeatures((feat.name,))           # cut went the wrong way
    raise RuntimeError('Could not trim the beam end at z = %.4f in.' % z_plane)


lo, hi = part_box()
length0 = hi[2] - lo[2]
trim = 0.5 * (length0 - BEAM_LENGTH)
length_changed = False
if trim < -1.0e-4:
    raise RuntimeError('The model beam (%.3f in) is shorter than BEAM_LENGTH = %.3f in; '
                       'this script only shortens it.' % (length0, BEAM_LENGTH))
if trim > 1.0e-4:
    p.deleteMesh()
    xc, yc = 0.5 * (lo[0] + hi[0]), 0.5 * (lo[1] + hi[1])
    cut_end(lo[2], +1.0, trim, xc, yc)
    cut_end(hi[2], -1.0, trim, xc, yc)
    lo, hi = part_box()
    length_changed = True
    log('Beam length %.3f -> %.3f in (%.3f in trimmed from each end; holes stay '
        'centred).' % (length0, hi[2] - lo[2], trim))
else:
    log('Beam length already %.3f in.' % length0)

# make sure every cell carries the aluminium section after the geometry edit
sec_name = None
for sa in p.sectionAssignments:
    sec_name = sa.sectionName
if sec_name is None:
    if 'Al6061' not in model.materials.keys():
        mat = model.Material(name='Al6061')
        mat.Elastic(table=((10000.0, 0.33),))
        mat.Plastic(table=((40.0, 0.0), (45.0, 0.05)))
    if 'Alum' not in model.sections.keys():
        model.HomogeneousSolidSection(name='Alum', material='Al6061', thickness=None)
    sec_name = 'Alum'
while len(p.sectionAssignments):
    del p.sectionAssignments[0]
if 'BeamAll' in p.sets.keys():
    del p.sets['BeamAll']
p.Set(name='BeamAll', cells=p.cells)
p.SectionAssignment(region=p.sets['BeamAll'], sectionName=sec_name, offset=0.0,
                    offsetType=MIDDLE_SURFACE, offsetField='',
                    thicknessAssignment=FROM_SECTION)
a.regenerate()
beam = a.instances[beam_name]

# ---------------------------------------------------------------------------
# 3. beam extents and roller placement
# ---------------------------------------------------------------------------
pts = [v.pointOn[0] for v in beam.vertices]
x_min, x_max = min(p[0] for p in pts), max(p[0] for p in pts)
y_bot, y_top = min(p[1] for p in pts), max(p[1] for p in pts)
z_min, z_max = min(p[2] for p in pts), max(p[2] for p in pts)
x_mid, z_mid = 0.5 * (x_min + x_max), 0.5 * (z_min + z_max)
log('Beam box: x[%.4f, %.4f]  y[%.4f, %.4f]  z[%.4f, %.4f]  (length %.3f in)'
    % (x_min, x_max, y_bot, y_top, z_min, z_max, z_max - z_min))
if z_max - z_min < SPAN:
    raise RuntimeError('Beam (%.3f in) is shorter than the %.1f in span.'
                       % (z_max - z_min, SPAN))


def checked_radius(inst, nominal):
    """Roller radius measured from the reference point to the surface,
    perpendicular to the roller axis (global x after the 90 deg rotation)."""
    c = a.getCoordinates(first_rp(inst))
    p = inst.faces[0].pointOn[0]
    r = math.sqrt((p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2)
    if abs(r - nominal) <= 0.02 * nominal:
        return r
    log('NOTE: %s measured radius %.4f in differs from %.4f in; using %.4f in.'
        % (inst.name, r, nominal, nominal))
    return nominal


r_top = checked_radius(top, R_TOP)
r_bot = max(checked_radius(bot_insts[0], R_BOT), checked_radius(bot_insts[1], R_BOT))


def move_center_to(inst, target):
    cur = a.getCoordinates(first_rp(inst))
    vec = tuple(t - c for t, c in zip(target, cur))
    if any(abs(c) > 1.0e-9 for c in vec):
        a.translate(instanceList=(inst.name,), vector=vec)
    log('%-12s centre -> (%.4f, %.4f, %.4f)' % ((inst.name,) + tuple(target)))


bot_insts.sort(key=lambda i: a.getCoordinates(first_rp(i))[2])
move_center_to(bot_insts[0], (x_mid, y_bot - r_bot, z_mid - SPAN / 2.0))
move_center_to(bot_insts[1], (x_mid, y_bot - r_bot, z_mid + SPAN / 2.0))
move_center_to(top, (x_mid, y_top + r_top, z_mid))
a.regenerate()
c0 = a.getCoordinates(first_rp(bot_insts[0]))
c1 = a.getCoordinates(first_rp(bot_insts[1]))
log('Support span = %.4f in' % dist(c0, c1))

# ---------------------------------------------------------------------------
# 4. beam mesh: quadratic tets, finest under the licence limit
# ---------------------------------------------------------------------------
p = model.parts[BEAM_PART]


def bad_elements():
    q = p.verifyMeshQuality(criterion=ANALYSIS_CHECKS)
    return list(q['failedElements']) + list(q['warningElements'])


def centroid(el):
    cs = [n.coordinates for n in el.getNodes()]
    return tuple(sum(c[i] for c in cs) / len(cs) for i in range(3))


if REMESH:
    p.deleteMesh()
    p.setMeshControls(regions=p.cells, elemShape=TET, technique=FREE)
    p.setElementType(regions=(p.cells,), elemTypes=(
        mesh.ElemType(elemCode=C3D20R, elemLibrary=STANDARD),
        mesh.ElemType(elemCode=C3D15, elemLibrary=STANDARD),
        mesh.ElemType(elemCode=C3D10, elemLibrary=STANDARD)))

    def mesh_once(g, dev, mf):
        p.deleteMesh()
        attempt(lambda: p.deleteSeeds(regions=p.edges), 'clearing old edge seeds')
        p.seedPart(size=g, deviationFactor=dev, minSizeFactor=mf)
        p.generateMesh()
        nb = attempt(lambda: len(bad_elements()), 'mesh quality check')
        return 10 ** 9 if nb is None else nb

    def report(tag, g, dev, mf, nb, nn):
        log('Mesh try (%s): seed %.4f, curvature %.2f, min size %.2f -> %d elements, '
            '%d nodes, %s flagged%s' % (tag, g, dev, mf, len(p.elements), nn,
                                       '?' if nb >= 10 ** 9 else nb,
                                       '  (over node target, not used)'
                                       if nn > NODE_TARGET else ''))

    def try_list(cands, tag):
        """Mesh each (seed, curvature, min size); best = fewest flagged
        elements, then most nodes, among meshes under NODE_TARGET."""
        best = None
        for g, dev, mf in cands:
            nb = mesh_once(g, dev, mf)
            nn = len(p.nodes)
            report(tag, g, dev, mf, nb, nn)
            if nn > NODE_TARGET:
                continue
            key = (nb, -nn)
            if best is None or key < (best[0], -best[4]):
                best = (nb, g, dev, mf, nn)
            if nb == 0:
                break          # candidates run from finest to coarsest
        return best

    def finest_size():
        """Smallest global size with the beam under NODE_TARGET nodes.
        Node count scales about as (1/size)^3, so each try rescales the size."""
        g, under, tries = SEED_START, [], []
        for k in range(SIZE_ITERS):
            mesh_once(g, CURV_DEV_FINE, MIN_SIZE_FINE)
            nn = len(p.nodes)
            log('Size search %d: seed %.4f -> %d nodes (target %d)' % (k + 1, g, nn, NODE_TARGET))
            tries.append((g, nn))
            if nn <= NODE_TARGET:
                under.append((g, nn))
                if nn >= FILL_TARGET * NODE_TARGET:
                    break
            ratio = float(nn) / NODE_TARGET
            g = g * ratio ** (1.0 / 3.0) * (1.01 if ratio > 1.0 else 0.995)
        while not under:                      # every try was over: keep growing
            g = max(t[0] for t in tries) * 1.08
            mesh_once(g, CURV_DEV_FINE, MIN_SIZE_FINE)
            nn = len(p.nodes)
            log('Size search: seed %.4f -> %d nodes' % (g, nn))
            tries.append((g, nn))
            if nn <= NODE_TARGET:
                under.append((g, nn))
        g_best, n_best = max(under, key=lambda t: t[1])
        log('Finest size under the licence target: %.4f in (%d nodes).' % (g_best, n_best))
        return g_best

    def fine_candidates(g0):
        return ((g0, CURV_DEV_FINE, MIN_SIZE_FINE), (g0 * 1.01, CURV_DEV_FINE, MIN_SIZE_FINE),
                (g0, 0.07, MIN_SIZE_FINE), (g0 * 1.02, CURV_DEV_FINE, 0.20),
                (g0 * 1.03, 0.07, MIN_SIZE_FINE))

    def face_normal(f, pt):
        try:
            return f.getNormal(point=pt)
        except TypeError:
            return f.getNormal()

    def ignore_tangent_seams():
        """Ignore straight seams running along the beam where the two faces
        meet tangentially (web-fillet, fillet-flange, flange-tip rounds)."""
        cos_lim = math.cos(math.radians(TANGENT_DEG))
        seams = []
        for e in p.edges:
            try:
                vs = e.getVertices()
                if len(vs) != 2:
                    continue
                va, vb = p.vertices[vs[0]].pointOn[0], p.vertices[vs[1]].pointOn[0]
                if (abs(va[0] - vb[0]) > 1e-4 or abs(va[1] - vb[1]) > 1e-4
                        or abs(va[2] - vb[2]) < 1.0):
                    continue                          # not a long seam along z
                fids = e.getFaces()
                if len(fids) != 2:
                    continue
                m = e.pointOn[0]
                n1 = face_normal(p.faces[fids[0]], m)
                n2 = face_normal(p.faces[fids[1]], m)
                dot = abs(sum(a_ * b_ for a_, b_ in zip(n1, n2)))
                l1 = math.sqrt(sum(a_ * a_ for a_ in n1))
                l2 = math.sqrt(sum(a_ * a_ for a_ in n2))
                if l1 > 0 and l2 > 0 and dot / (l1 * l2) >= cos_lim:
                    seams.append(e)
            except Exception:
                continue
        if not seams:
            log('Stage 2: no smooth seams found to ignore.')
            return 0
        p.ignoreEntity(entities=tuple(seams))
        log('Stage 2: ignoring %d smooth seams along the beam.' % len(seams))
        return len(seams)

    if MESH_LEVEL == 'FINE':
        log('MESH_LEVEL FINE: searching for the finest mesh under %d nodes '
            '(several tries; this can take 20-45 min).' % NODE_TARGET)
        cands = fine_candidates(finest_size())
    else:
        log('MESH_LEVEL CHECK: Rev B mesh density (0.10 in seed) for the convergence check.')
        cands = MESH_SWEEP
    best = try_list(cands, 'stage 1')
    chosen, stage = best, 1
    if best is not None and best[0] > 0 and IGNORE_TANGENT_SEAMS:
        feats_before = set(p.features.keys())
        n_ign = attempt(ignore_tangent_seams, 'seam ignore (virtual topology)')
        if n_ign:
            best2 = try_list(cands, 'stage 2')
            if best2 is not None and best2[0] < best[0]:
                chosen, stage = best2, 2
            else:
                new_feats = [f for f in p.features.keys() if f not in feats_before]
                if attempt(lambda: p.deleteFeatures(tuple(new_feats)) or True,
                           'undoing the seam ignore') and new_feats:
                    log('Stage 2 did not help; seam ignore undone.')
                else:
                    log('Stage 2 did not help and could not be undone; keeping its best mesh.')
                    chosen, stage = best2 or best, 2
    if chosen is None:
        seed = 0.10
        for k in range(8):
            mesh_once(seed, 0.10, 0.10)
            if len(p.nodes) <= NODE_TARGET:
                break
            seed *= 1.15
        MESH_INFO = dict(seed_in=seed, curvature=0.10, min_size=0.10)
    else:
        nb = mesh_once(chosen[1], chosen[2], chosen[3])
        log('Kept stage %d mesh: seed %.4f, curvature %.2f, min size %.2f (%d flagged).'
            % (stage, chosen[1], chosen[2], chosen[3], nb))
        MESH_INFO = dict(seed_in=chosen[1], curvature=chosen[2], min_size=chosen[3])
    log('Beam mesh: %d elements, %d nodes (C3D10), %.1f %% of the %d-node licence limit.'
        % (len(p.elements), len(p.nodes), 100.0 * (len(p.nodes) + 3) / NODE_LIMIT, NODE_LIMIT))
else:
    p.generateMesh()
    MESH_INFO = dict(seed_in=0.0, curvature=0.0, min_size=0.0)
MESH_INFO.update(level=MESH_LEVEL, elements=len(p.elements), nodes=len(p.nodes))

n_model_nodes = len(p.nodes) + 3          # + one reference node per roller
if n_model_nodes > NODE_LIMIT:
    raise RuntimeError('Mesh has %d nodes; the licence limit is %d. Lower '
                       'NODE_TARGET (or raise SEED_START) and run again.' % (n_model_nodes, NODE_LIMIT))

bad = attempt(bad_elements, 'final mesh quality check')
if bad:
    if 'MeshWarnElems' in p.sets.keys():
        del p.sets['MeshWarnElems']
    p.Set(name='MeshWarnElems',
          elements=p.elements.sequenceFromLabels(tuple(e.label for e in bad)))
    log('Mesh check: %d of %d elements flagged (part set "MeshWarnElems"). '
        'These are warnings only; the job still runs.' % (len(bad), len(p.elements)))
    lo_, hi_ = part_box()
    cx, cy, cz = [0.5 * (lo_[i] + hi_[i]) for i in range(3)]
    for el in bad[:30]:
        c = centroid(el)
        dh = min(math.hypot(c[2] - cz - dz, c[1] - cy - dy) for dz, dy in HOLES)
        log('  element %d at (x%+.3f, y%+.3f, z%+.3f) from beam centre; %.3f in '
            'from the nearest hole centre' % (el.label, c[0] - cx, c[1] - cy,
                                               c[2] - cz, dh))
elif bad is not None:
    log('Mesh check: no distorted elements.')
a.regenerate()
beam = a.instances[beam.name]

# ---------------------------------------------------------------------------
# 5. contact: rigid rollers (SIDE2 = outward) on the flange faces
# ---------------------------------------------------------------------------
def meshed_only(seq):
    """Keep faces that actually carry element faces (an empty contact surface
    gives 'THE SECONDARY SURFACE ... DOES NOT EXIST' in the job)."""
    out, n = None, 0
    for f in (seq or []):
        try:
            if len(f.getElementFaces()) == 0:
                continue
        except Exception:
            pass
        s = beam.faces[f.index:f.index + 1]
        out = s if out is None else out + s
        n += 1
    return out, n


def flange_faces(y):
    for finder in (faces_in_box, faces_through_plane):
        seq, n = finder(beam, y, x_min, x_max, z_min, z_max)
        if n:
            seq, n = meshed_only(seq)
            if n:
                return seq, n
    raise RuntimeError('No meshed flange face found at y = %.4f in.' % y)


FACE_KEYS = {'FACE1': 'face1Elements', 'FACE2': 'face2Elements',
             'FACE3': 'face3Elements', 'FACE4': 'face4Elements',
             'FACE5': 'face5Elements', 'FACE6': 'face6Elements'}


def flat_mesh_surface(name, y):
    """Element-based surface made only of the element faces lying on the
    flat plane y = const (the face a roller touches)."""
    tol = 1.0e-4
    try:
        mfs = beam.elementFaces.getByBoundingBox(
            xMin=x_min - 0.01, yMin=y - tol, zMin=z_min - 0.01,
            xMax=x_max + 0.01, yMax=y + tol, zMax=z_max + 0.01)
    except Exception as err:
        log('NOTE: mesh-face box search unavailable (%s); scanning faces.' % err)
        mfs = [f for f in beam.elementFaces
               if all(abs(nd.coordinates[1] - y) < tol for nd in f.getNodes())]
    groups = {}
    for f in mfs:
        side = str(f.face).upper()
        key = FACE_KEYS.get(side)
        if key is None:
            raise RuntimeError('Unexpected element face id %s.' % side)
        for el in f.getElements():
            groups.setdefault(key, set()).add(el.label)
    if not groups:
        return 0
    kw = dict((k, beam.elements.sequenceFromLabels(tuple(sorted(v))))
              for k, v in groups.items())
    if name in a.surfaces.keys():
        del a.surfaces[name]
    a.Surface(name=name, **kw)
    return len(mfs)


n_top = attempt(lambda: flat_mesh_surface('CS_BeamTop', y_top), 'mesh-face top surface')
n_bot = attempt(lambda: flat_mesh_surface('CS_BeamBot', y_bot), 'mesh-face bottom surface')
if n_top and n_bot:
    log('Beam contact surfaces from the mesh: top %d, bottom %d element faces '
        '(flat flange planes only).' % (n_top, n_bot))
else:
    log('Mesh-face surfaces not available; using geometry faces (v4 method).')
    top_faces, n_top = flange_faces(y_top)
    bot_faces, n_bot = flange_faces(y_bot)
    log('Beam contact faces (meshed): top = %d, bottom = %d' % (n_top, n_bot))
    for sname in ('CS_BeamTop', 'CS_BeamBot'):
        if sname in a.surfaces.keys():
            del a.surfaces[sname]
    a.Surface(name='CS_BeamTop', side1Faces=top_faces)
    a.Surface(name='CS_BeamBot', side1Faces=bot_faces)
a.Surface(name='CS_' + top.name, side2Faces=top.faces[0:1])
for inst in bot_insts:
    a.Surface(name='CS_' + inst.name, side2Faces=inst.faces[0:1])

if 'CP_Frictionless' in model.interactionProperties.keys():
    del model.interactionProperties['CP_Frictionless']
cp = model.ContactProperty('CP_Frictionless')
cp.NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON,
                  constraintEnforcementMethod=DEFAULT)
cp.TangentialBehavior(formulation=FRICTIONLESS)


def contact_pair(name, main_name, sec_name, adjust_tol):
    kw = dict(name=name, createStepName='Initial',
              sliding=FINITE, thickness=ON, interactionProperty='CP_Frictionless',
              initialClearance=OMIT, datumAxis=None, clearanceRegion=None)
    if adjust_tol:
        kw.update(adjustMethod=TOLERANCE, adjustTolerance=adjust_tol)
    else:
        kw.update(adjustMethod=NONE)
    for roles in (('main', 'secondary'), ('master', 'slave')):
        kw2 = dict(kw)
        kw2[roles[0]] = a.surfaces[main_name]
        kw2[roles[1]] = a.surfaces[sec_name]
        try:
            model.SurfaceToSurfaceContactStd(contactTracking=ONE_CONFIG, **kw2)
            return
        except TypeError:
            try:
                model.SurfaceToSurfaceContactStd(**kw2)
                return
            except TypeError:
                continue
    raise RuntimeError('Could not create contact pair %s.' % name)


for sname in ('CS_BeamTop', 'CS_BeamBot'):
    try:
        n_el = len(a.surfaces[sname].elements)
    except Exception:
        n_el = None
    if n_el == 0:
        raise RuntimeError('Contact surface %s has no element faces.' % sname)
    if n_el:
        log('%s: %d element faces.' % (sname, n_el))

contact_pair('C_' + top.name, 'CS_' + top.name, 'CS_BeamTop', TOP_ADJUST_TOL)
for inst in bot_insts:
    contact_pair('C_' + inst.name, 'CS_' + inst.name, 'CS_BeamBot', None)
log('Contact: 3 surface-to-surface pairs, frictionless, roller SIDE2 surfaces.')

# ---------------------------------------------------------------------------
# 6. boundary conditions
# ---------------------------------------------------------------------------
for sname in ('RP_BotRollers', 'RP_TopRoller'):
    if sname in a.sets.keys():
        del a.sets[sname]
a.Set(name='RP_BotRollers', referencePoints=(
    (first_rp(bot_insts[0]),), (first_rp(bot_insts[1]),)))
a.Set(name='RP_TopRoller', referencePoints=((first_rp(top),),))

model.EncastreBC(name='BotRollers_Fixed', createStepName='Initial',
                 region=a.sets['RP_BotRollers'], localCsys=None)
model.DisplacementBC(name='TopRoller_Control', createStepName='Initial',
                     region=a.sets['RP_TopRoller'],
                     u1=SET, u2=SET, u3=SET, ur1=SET, ur2=SET, ur3=SET,
                     amplitude=UNSET, distributionType=UNIFORM,
                     fieldName='', localCsys=None)

# beam rigid-body modes the frictionless rollers do not hold: x-translation,
# z-translation and rotation about y.  Nodes on the bottom-flange centre line.
nA = nearest_node(beam, (x_mid, y_bot, z_mid), y_band=y_bot)
nB = nearest_node(beam, (x_mid, y_bot, z_mid + 0.25 * SPAN), y_band=y_bot)
node_set(a, 'Beam_U1_Pts', beam, [nA, nB])
node_set(a, 'Beam_U3_Pt', beam, [nA])
log('Beam restraints: U1 at nodes %d and %d, U3 at node %d (mid-span, bottom).'
    % (nA.label, nB.label, nA.label))
model.DisplacementBC(name='Beam_U1_Restraint', createStepName='Initial',
                     region=a.sets['Beam_U1_Pts'], u1=SET, u2=UNSET, u3=UNSET,
                     ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET,
                     distributionType=UNIFORM, fieldName='', localCsys=None)
model.DisplacementBC(name='Beam_U3_Restraint', createStepName='Initial',
                     region=a.sets['Beam_U3_Pt'], u1=UNSET, u2=UNSET, u3=SET,
                     ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET,
                     distributionType=UNIFORM, fieldName='', localCsys=None)

# ---------------------------------------------------------------------------
# 7. step, loading and output
# ---------------------------------------------------------------------------
model.StaticStep(name='Load', previous='Initial', nlgeom=ON,
                 initialInc=0.01, maxNumInc=2000, minInc=1.0e-8, maxInc=MAX_INC,
                 description='Top roller pushed down %.3f in' % U_TARGET)
model.boundaryConditions['TopRoller_Control'].setValuesInStep(
    stepName='Load', u2=-U_TARGET)
log('Loading: top roller U2 = -%.4f in (displacement control; RF2 = load); '
    'increments <= %.1f %% of the step.' % (U_TARGET, 100.0 * MAX_INC))


def _field_output():
    fo = model.fieldOutputRequests['F-Output-1']
    attempt(lambda: fo.setValues(variables=FIELD_VARS),
            'field-output variable list (default list kept)')
    try:
        fo.setValues(numIntervals=FIELD_FRAMES, timeMarks=OFF)
        log('Field output: %s at %d frames, time marks OFF.' % (', '.join(FIELD_VARS), FIELD_FRAMES))
    except TypeError:
        fo.setValues(numIntervals=FIELD_FRAMES)
        log('Field output: %d frames (this Abaqus has no timeMarks option).' % FIELD_FRAMES)


attempt(_field_output, 'field-output settings')

if 'H-LoadDisp' in model.historyOutputRequests.keys():
    del model.historyOutputRequests['H-LoadDisp']
model.HistoryOutputRequest(name='H-LoadDisp', createStepName='Load',
                           variables=('U2', 'RF2'),
                           region=a.sets['RP_TopRoller'],
                           sectionPoints=DEFAULT, rebar=EXCLUDE)

# ---------------------------------------------------------------------------
# 8. save, then job in its own folder, submit
# ---------------------------------------------------------------------------
def repo_root(start):
    """Walk up to the folder that holds both abaqus/ and results/ (the repo)."""
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, 'abaqus')) and os.path.isdir(os.path.join(d, 'results')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


root = repo_root(os.getcwd()) if SAVE_IN_REPO else None
base_dir = os.path.join(root, 'abaqus', 'final_design') if root else os.getcwd()
if not os.path.isdir(base_dir):
    os.makedirs(base_dir)
job_dir = os.path.join(base_dir, JOB_FOLDER)
if not os.path.isdir(job_dir):
    os.makedirs(job_dir)
mdb.saveAs(pathName=os.path.join(base_dir, JOB_NAME + '.cae'))
log('Saved %s (model only)' % os.path.join(base_dir, JOB_NAME + '.cae'))

# CAD volumes and mesh settings for FOS_Stock1_RevC_v1.py (weight-accuracy check)
try:
    fh = open(os.path.join(job_dir, JOB_NAME + '_geometry.txt'), 'w')
    fh.write('# Written by Stock1_RevC_v1.py; read by FOS_Stock1_RevC_v1.py\n')
    for k_ in sorted(GEOMETRY.keys()):
        fh.write('%s = %.6f\n' % (k_, GEOMETRY[k_]))
    for k_ in sorted(MESH_INFO.keys()):
        v_ = MESH_INFO[k_]
        fh.write('mesh_%s = %s\n' % (k_, ('%.6f' % v_) if isinstance(v_, float) else v_))
    fh.close()
    log('Saved %s_geometry.txt (CAD volume %.4f in^3).' % (JOB_NAME, GEOMETRY['cad_volume_in3']))
except Exception as err:
    log('NOTE: geometry file not written (%s).' % err)

if CREATE_JOB:
    if os.path.exists(os.path.join(job_dir, JOB_NAME + '.lck')):
        raise RuntimeError('%s.lck exists in %s: a run is active or was cut off.  If no job '
                           'is running, delete the .lck file and run again.' % (JOB_NAME, job_dir))
    for jn in list(mdb.jobs.keys()):
        del mdb.jobs[jn]
    try:
        n_cpu = os.cpu_count() or 1
    except AttributeError:
        n_cpu = 1
    n_cpu = max(1, min(NUM_CPUS, n_cpu))
    desc = 'Rev C, Stock 1 roller pads + notches (%s mesh)' % MESH_LEVEL
    try:
        mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, resultsFormat=ODB,
                numCpus=n_cpu, numDomains=n_cpu, memory=90, memoryUnits=PERCENTAGE,
                description=desc)
    except Exception:
        mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, numCpus=1, description=desc)
        n_cpu = 1
    log('Job "%s" defined (%d CPU%s).' % (JOB_NAME, n_cpu, '' if n_cpu == 1 else 's'))
    os.chdir(job_dir)                      # Abaqus writes job files to the work directory
    mdb.saveAs(pathName=os.path.join(job_dir, JOB_NAME + '.cae'))
    log('Saved the model with its job to %s' % os.path.join(job_dir, JOB_NAME + '.cae'))
    if SUBMIT_JOB:
        mdb.jobs[JOB_NAME].submit(consistencyChecking=OFF)
        log('Job "%s" submitted from %s.  Follow it in Job > Manager > Monitor '
            '(%s).' % (JOB_NAME, job_dir,
                       'roughly 1-3 hours' if MESH_LEVEL == 'FINE' else 'about 30-40 min'))
        log('When it reads "Completed", run FOS_Stock1_RevC_v1.py.')
    else:
        log('SUBMIT_JOB = False: job created, not submitted (Job > Manager > Submit).')
else:
    log('CREATE_JOB = False: model saved, no job.')
