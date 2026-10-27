# -*- coding: utf-8 -*-
"""
Stock1_Drilled_v2.py  --  EMCH 308 Team 6, redesigned Stock 1 drilled beam + job
==============================================================================

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> the folder holding ProjectBeam.cae
                                        (E:\\Semester Project\\abaqus once organized,
                                        or E:\\Semester Project before that)
    2. File > Run Script...          -> Stock1_Drilled_v2.py
    The script builds the redesigned beam, saves Stock1_Drilled_v2.cae, then
    creates the job "Stock1_Drilled_v2" in the folder Stock1_Drilled_v2\\ next to
    it and submits it (about 40 min).  When the Job Monitor shows "Completed",
    run FOS_Stock1_Drilled_v2.py.

WHY v1 FAILED (Stock1_Drilled.odb: FOS 1.246, mesh weight 1.002 lb)
    * Strength: the beam does not fail in bending.  It yields first in the thin
      web (0.15 in): around the two extra web holes and the Fig. 1 holes, over
      the supports, and under the load roller.  The extra web holes were the
      main cause; flange holes 0.58 in from the load roller and 0.40 in from
      the supports, and the milled top-flange ends, added to it by leaving the
      flanges less able to spread the roller loads into the web.
    * Weight: the part was 0.993 lb (CAD), under the limit.  The 1.002 lb came
      from the FOS script measuring straight-sided tetrahedra, which fill in
      part of every curved hole.  FOS_Stock1_Drilled_v2.py integrates the
      curved 10-node elements and reads the true weight.

WHAT v2 CHANGES (screened with a separate stress model calibrated on the v1
and notched Abaqus results before this script was written)
    * No flange holes within ~1 in of the load roller (top flange) or of the
      supports (bottom flange); full flanges at both beam ends.
    * Bottom-flange holes start at mid-span, where the flange carries only
      low bending stress and no roller load.
    * The two extra web holes are removed (the web is what yields).
    * The milled end reliefs (Option B) are gone: drilling only, so the cost
      drops from $510 to about $143 (32 drilled holes, one drill size
      besides the 1.00 in Fig. 1 holes).
    * Field output uses time marks OFF, which removes the warning
      "OUTPUT AT EXACT, PREDEFINED TIME POINTS WAS REQUESTED" (New_Errors_3).
    * The job is created and submitted in its own folder.
    Expected: about 0.994 lb (CAD), screened FOS about 1.5.

REMOVAL PLAN, dimensions from mid-span (CL):
    28 flange holes, dia 25/32 DRILL THRU, centred x = +/-0.7875
         top flange:    z = +/-1.30, 2.18, 3.06
         bottom flange: z = +/-0.44, 1.32, 2.20, 3.08
    plus the four required Fig. 1 holes (dia 1.00).
    Progress is in the message area and in Stock1_Drilled_v2_log.txt.

STOCK 1 = Aluminum Association I 3 x 2.03, 6061: height 3.00, flange width
    2.50, flange 0.26, web 0.15, R0.25 fillets, square flange tips.
    Length 8.20 in; four Fig. 1 holes (dia 1.00 at +/-1.00, y +0.375 and
    +/-3.00, y -0.375 from mid-span).
    Holes are cut on top of the baseline (Baseline_Stock1_v1.py).

EVERYTHING ELSE is fix_ProjectBeam_v5.py (fix_history folder):
    WHAT IT FIXES (errors in Erros.txt / ProjectBeam.jnl)
        1. "Zero pivot ... TOPROLLER-1.1 D.O.F. 2" (fatal): the top roller was
           force-loaded and free in U2, so it had no stiffness until contact
           closed.  -> The top roller is displacement-controlled; RF2 is the load.
        2. "148 facets facing the wrong direction": the bottom-roller contact
           surfaces used SIDE1, whose normal points into the beam.
           -> Every roller surface uses SIDE2 (outward); the contact is rebuilt as
              three surface-to-surface pairs; general contact is removed.
        3. "Unconnected regions": any duplicate beam instance (Beam-2) is deleted.
           The remaining warning is expected: the beam and the 3 rigid rollers
           only connect through contact.
        4. Roller positions came from ~30 hand translations.
           -> Placed from the beam geometry: 8.000 in span, exactly tangent.
        5. "51 elements are distorted" (warning only).
           -> The beam is remeshed with quadratic tets (C3D10) at the original
              0.1 in seed.  The node count is checked against the Academic
              Teaching licence limit (250,000 nodes) and the seed is coarsened
              automatically if needed.  Flagged elements are listed in the part
              set "MeshWarnElems"; they are warnings, not errors.
        6. Old step stabilization ("allsdtol") and BCs are cleared and rebuilt.
        The beam's rigid-body restraints are put on mesh nodes on the
        bottom-flange centre line (U1 at two nodes, U3 at the mid-span node).
        They add no stress.
    
    CHANGES IN v2
        7. Beam length 8.5 -> 8.2 in (BEAM_LENGTH).  0.15 in is trimmed from each
           end, so the four Fig. 1 access holes stay at +/-1 in and +/-3 in from
           mid-span and the 8 in support span is unchanged (0.1 in overhang).
        8. The 6 distorted tets at the top of the inner hole (where the hole edge
           nearly meets the web-flange fillet) are removed by seeding the hole
           edges finer.  Several seed combinations are tried; the first with no
           flagged elements (and under the node limit) is kept.
    CHANGES IN v5
       14. Beam contact surfaces are built from the mesh: only the element faces
           that lie on the flat top (y = top) and bottom (y = bottom) flange planes.
           In v4 the seam-ignore merged each flat face with the flange tips,
           underside and fillets, so the contact surfaces covered the whole
           flange skin (10,902 / 11,126 faces vs 3,936 in v3) and the solver
           carried ~200,000 open contact constraints.  The roller contact itself
           is unchanged.  If the mesh-face search is not available, the v4
           geometry-face method is used instead.
    
    CHANGES IN v4
       13. Distorted elements (15 in the v3 run: 9 where the hole edges come within
           ~0.08 in of the web-fillet seam, 6 at the top-flange tip rounds):
           - local hole-edge seeding is removed (every v3 try with it was worse:
             174-697 flagged vs 15 without);
           - stage 1 sweeps global mesh settings (size, curvature control,
             minimum size factor) and keeps the cleanest mesh;
           - stage 2 (only if elements are still flagged) tells the mesher to
             ignore the smooth tangent seams that run along the beam (web-fillet,
             flange-tip rounds) so it no longer squeezes elements into the thin
             strips beside them, then sweeps again.  The better stage is kept;
             the seam-ignore is undone if it does not help.
           The CAE mesh check matched the solver's list exactly in v3, so the
           count reported here is what the job will report.
    
    CHANGES IN v3
       10. New job name "Beam_8p2in" (an old Beam_Fixed.lck lock file blocks the
           old name); if a lock file exists for the name, a suffix is added.
       11. Every progress line is also written to Stock1_Drilled_v1_log.txt in
           the work directory, including where any flagged element sits.
       12. More mesh variations are tried (8) to clear the distorted elements in
           the 0.1 in strips between the holes and the web-flange fillets.
        9. Field output is written at 10 points in the step instead of every
           increment (the last ODB was 2.6 GB).  RF2/U2 history is still written
           every increment for the load-deflection curve.
    
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
CAE_NAME     = 'ProjectBeam.cae'   # opened from the work dir if nothing is open
MODEL_NAME   = 'Project'
BEAM_PART    = 'Beam'
TOP_PART     = 'TopRoller'
BOT_PART     = 'BotRoller'

R_TOP        = 0.492    # in  loading roller radius   (0.984 in diameter)
R_BOT        = 0.197    # in  support roller radius   (0.394 in diameter)
SPAN         = 8.0      # in  support centre-to-centre distance (test fixture)
BEAM_LENGTH  = 8.2      # in  overall beam length
S1_H, S1_BF, S1_TF, S1_TW, S1_RF = 3.00, 2.50, 0.26, 0.15, 0.25  # Stock 1, in
NOTCHES      = False    # (milled notch plan, superseded by the drilled plan)
FL_HOLE_D    = 0.78125   # in  flange hole dia (25/32 drill)
FL_HOLE_X    = 0.7875   # in  flange hole centre from the web centreline
TOP_Z        = (1.30, 2.18, 3.06)   # in  top-flange hole stations (from mid-span)
BOT_Z        = (0.44, 1.32, 2.20, 3.08)   # in  bottom-flange hole stations (from mid-span)
WEB_HOLES    = False    # extra web holes at +/-WEB_HOLE_Z (v1 had them; they weaken the web)
WEB_HOLE_D   = 0.875    # in  extra web hole dia
WEB_HOLE_Z   = 2.00     # in  at +/- this station, on mid-height
OPTION_B     = False    # milled top-flange end reliefs: OFF in v2 (they cut strength, cost $357)
RELIEF_L     = 0.25     # in  relief length from each beam end
RELIEF_R     = 0.25     # in  relief inside-corner radius (dia 0.50 end mill)
NOTCH_Z1, NOTCH_Z2 = 1.00, 3.65   # in  notch extent from mid-span
NOTCH_KEEP   = 1.00     # in  flange width left in the notch zone
NOTCH_R      = 0.50     # in  inside-corner radius
HOLE_R       = 0.5      # in  Fig. 1 access holes, diameter 1.0 in
HOLES        = ((-3.0, -0.375), (-1.0, 0.375), (1.0, 0.375), (3.0, -0.375))
                        # (z from mid-span, y from mid-height) of each hole

U_TARGET     = 0.08     # in  top-roller travel (RF2 vs U2 = load-deflection)
TOP_ADJUST_TOL = 1.0e-3 # in  strain-free gap closure, top roller only

REMESH       = True     # quadratic-tet remesh of the beam (recommended)
USE_VIRTUAL_TOPOLOGY = False   # off: it raised the distorted-element count
VT_SHORT_EDGE = 0.02    # in    edges shorter than this are merged
VT_SMALL_FACE = 4.0e-4  # in^2  faces smaller than this are merged
GLOBAL_SEED  = 0.1      # in    global element size (same as the original)
CURV_DEV     = 0.1      # curvature control (same as the original)
NODE_LIMIT   = 250000   # Academic Teaching licence limit (nodes, whole model)
NODE_TARGET  = 230000   # stay this far under it; seed grows until N <= this
# (global seed, hole-edge seed or None) tried in order until no element is
# flagged; the best one under NODE_TARGET is kept
# (global seed, curvature deviation factor, min size factor), tried in order
# until a mesh has no flagged elements; the first entry is the v3 mesh
MESH_SWEEP = ((0.100, 0.10, 0.10), (0.100, 0.10, 0.30), (0.105, 0.10, 0.10),
              (0.095, 0.10, 0.10), (0.100, 0.07, 0.10), (0.100, 0.15, 0.10),
              (0.105, 0.10, 0.30), (0.0975, 0.10, 0.20))
IGNORE_TANGENT_SEAMS = True   # stage 2 (see header)
TANGENT_DEG  = 5.0      # faces meeting within this angle count as a smooth seam
FIELD_FRAMES = 10       # field-output frames in the step (history: every inc)

JOB_NAME     = 'Stock1_Drilled_v2'
JOB_FOLDER   = 'Stock1_Drilled_v2'   # job files go here, next to the saved .cae
CREATE_JOB   = True     # add the job definition
NUM_CPUS     = 4        # capped at the number of processors on the machine
SUBMIT_JOB   = True     # also submit the job (False = create only)

GEOM_TOL     = 1.0e-4   # in


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
LOG_PATH = os.path.join(os.getcwd(), 'Stock1_Drilled_v2_log.txt')
try:
    open(LOG_PATH, 'w').close()
except Exception:
    LOG_PATH = None


def log(text):
    line = '[fix_ProjectBeam] ' + text
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


log('Stock1_Drilled_v2 starting')
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
# 2a. Stock 1 beam: AA I 3 x 2.03 (replaces the Stock 3 DXF beam)
# ---------------------------------------------------------------------------
RHO = 0.0975            # lb/in^3, 6061 aluminium


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


def draw_notches(sk, mv):
    """Four plan-view notch profiles (both edges, both sides of mid-span).
    Sketch axes: horizontal = across the flange (x), vertical = along the
    beam (z); the pattern is symmetric, so their signs do not matter."""
    xi, R, z1, z2, xo = NOTCH_KEEP / 2.0, NOTCH_R, NOTCH_Z1, NOTCH_Z2, S1_BF / 2.0 + 0.35
    for sx in (1.0, -1.0):
        for sz in (1.0, -1.0):
            P = lambda x, z: (sx * x, sz * z)
            sk.Line(point1=P(xo, z1), point2=P(xi + R, z1))
            arc(sk, P(xi + R, z1 + R), P(xi + R, z1), P(xi, z1 + R))
            sk.Line(point1=P(xi, z1 + R), point2=P(xi, z2 - R))
            arc(sk, P(xi + R, z2 - R), P(xi, z2 - R), P(xi + R, z2))
            sk.Line(point1=P(xi + R, z2), point2=P(xo, z2))
            sk.Line(point1=P(xo, z2), point2=P(xo, z1))


def draw_flange_holes(zs):
    """Plan-view circles: horizontal = x (across the flange), vertical = z.
    The pattern is symmetric in both, so the sketch axis signs do not matter."""
    def f(sk, mv):
        for z in zs:
            for sx in (1.0, -1.0):
                for sz in (1.0, -1.0):
                    c = (sx * FL_HOLE_X, sz * z)
                    sk.CircleByCenterPerimeter(center=c, point1=(c[0] + FL_HOLE_D / 2.0, c[1]))
    return f


def draw_web_holes(sk, mv):
    for sz in (1.0, -1.0):
        sk.CircleByCenterPerimeter(center=(sz * WEB_HOLE_Z, 0.0),
                                   point1=(sz * WEB_HOLE_Z + WEB_HOLE_D / 2.0, 0.0))


def draw_reliefs(sk, mv):
    """Top-flange end reliefs (plan view): from x = fillet end to past the tip,
    from z = HZ - RELIEF_L to past the beam end, R inside corner at the fillet
    side.  Horizontal = x, vertical = z."""
    hz = BEAM_LENGTH / 2.0
    xi, zi, R = S1_TW / 2.0 + S1_RF, hz - RELIEF_L, RELIEF_R
    xo, zo = S1_BF / 2.0 + 0.35, hz + 0.35
    for sx in (1.0, -1.0):
        for sz in (1.0, -1.0):
            P = lambda x, z: (sx * x, sz * z)
            sk.Line(point1=P(xo, zi), point2=P(xi + R, zi))
            arc(sk, P(xi + R, zi + R), P(xi + R, zi), P(xi, zi + R))
            sk.Line(point1=P(xi, zi + R), point2=P(xi, zo))
            sk.Line(point1=P(xi, zo), point2=P(xo, zo))
            sk.Line(point1=P(xo, zo), point2=P(xo, zi))


# hole-layout sanity checks (ligaments a drill can leave cleanly)
_fr = FL_HOLE_D / 2.0
_tip = S1_BF / 2.0 - (FL_HOLE_X + _fr)
_root = (FL_HOLE_X - _fr) - (S1_TW / 2.0 + S1_RF)
for _zs, _nm in ((TOP_Z, 'top'), (BOT_Z, 'bottom')):
    _zz = sorted(_zs)
    if _zz[0] - _fr < 0.04:
        raise RuntimeError('%s-flange hole at %.3f in is too close to mid-span.' % (_nm, _zz[0]))
    for _i in range(1, len(_zz)):
        if _zz[_i] - _zz[_i - 1] - FL_HOLE_D < 0.09:
            raise RuntimeError('%s-flange holes at %.3f and %.3f in leave less than 0.09 in '
                               'between them.' % (_nm, _zz[_i - 1], _zz[_i]))
    if BEAM_LENGTH / 2.0 - (_zz[-1] + _fr) < 0.1:
        raise RuntimeError('%s-flange hole at %.3f in is too close to the beam end.' % (_nm, _zz[-1]))
log('Hole layout: dia %.4f at x = +/-%.4f; flange-tip ligament %.3f in, fillet clearance %.3f in.'
    % (FL_HOLE_D, FL_HOLE_X, _tip, _root))
log('  top flange z = +/-%s; bottom flange z = +/-%s (from mid-span)'
    % (', '.join('%.2f' % z for z in TOP_Z), ', '.join('%.2f' % z for z in BOT_Z)))

# replace the Stock 3 beam: instances, assembly sets/surfaces, part
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
sketch_cut(p, YZPLANE, S1_BF / 2.0 + 0.30, YAXIS, (S1_BF / 2.0 + 0.30, 0.0, BEAM_LENGTH / 2.0),
           draw_holes,
           lambda dv: abs(dv - v_holes_exp) < 0.05 * v_holes_exp and hole_edges_ok(p),
           'Fig. 1 holes (4 x dia 1.00)')
if NOTCHES:
    a_notch = ((S1_BF - NOTCH_KEEP) / 2.0 * (NOTCH_Z2 - NOTCH_Z1)
               - 2.0 * (1.0 - math.pi / 4.0) * NOTCH_R ** 2)
    v_notch_exp = 8.0 * a_notch * S1_TF
    sketch_cut(p, XZPLANE, S1_H / 2.0 + 0.20, ZAXIS, (0.0, S1_H / 2.0 + 0.20, BEAM_LENGTH / 2.0),
               draw_notches,
               lambda dv: abs(dv - v_notch_exp) < 0.03 * v_notch_exp,
               'Flange notches (8 x %.2f x %.2f, R%.2f)'
               % (NOTCH_Z2 - NOTCH_Z1, (S1_BF - NOTCH_KEEP) / 2.0, NOTCH_R))
v_fl = math.pi * (FL_HOLE_D / 2.0) ** 2 * S1_TF
cut_depth = 0.20 + S1_TF + 0.10          # from a plane 0.20 above the flange, top flange only
for zs, y_pl, tag in ((TOP_Z, S1_H / 2.0 + 0.20, 'Top'), (BOT_Z, -(S1_H / 2.0 + 0.20), 'Bottom')):
    v_exp = 4 * len(zs) * v_fl
    sketch_cut(p, XZPLANE, y_pl, ZAXIS, (0.0, y_pl, BEAM_LENGTH / 2.0),
               draw_flange_holes(zs),
               lambda dv, v_exp=v_exp: abs(dv - v_exp) < 0.03 * v_exp,
               '%s-flange holes (%d x dia %.4f)' % (tag, 4 * len(zs), FL_HOLE_D),
               depth=cut_depth)
if WEB_HOLES:
    v_web = 2 * math.pi * (WEB_HOLE_D / 2.0) ** 2 * S1_TW
    sketch_cut(p, YZPLANE, S1_BF / 2.0 + 0.30, YAXIS, (S1_BF / 2.0 + 0.30, 0.0, BEAM_LENGTH / 2.0),
               draw_web_holes, lambda dv: abs(dv - v_web) < 0.05 * v_web,
               'Web holes (2 x dia %.3f)' % WEB_HOLE_D)
else:
    log('No extra web holes (v2): the web is the part that yields first.')
if OPTION_B:
    a_rel = ((S1_BF / 2.0 - (S1_TW / 2.0 + S1_RF)) * RELIEF_L
             - (1.0 - math.pi / 4.0) * RELIEF_R ** 2)
    v_rel = 4 * a_rel * S1_TF
    sketch_cut(p, XZPLANE, S1_H / 2.0 + 0.20, ZAXIS, (0.0, S1_H / 2.0 + 0.20, BEAM_LENGTH / 2.0),
               draw_reliefs, lambda dv: abs(dv - v_rel) < 0.05 * v_rel,
               'Option B top-flange end reliefs (4 x %.2f, R%.2f)' % (RELIEF_L, RELIEF_R),
               depth=cut_depth)
else:
    log('Option B (milled end reliefs) is off: drilled plan A only.')
v_final = p.getVolume()
log('Finished beam: %.4f in^3, %.3f lb (limit 1.000 lb) -> %s'
    % (v_final, v_final * RHO, 'MEETS' if v_final * RHO <= 1.0 else 'OVER'))
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
# 4. beam mesh: virtual topology + quadratic tets + local repair
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
    if USE_VIRTUAL_TOPOLOGY:
        attempt(lambda: p.createVirtualTopology(
            mergeShortEdges=True, shortEdgeThreshold=VT_SHORT_EDGE,
            mergeSmallFaces=True, smallFaceAreaThreshold=VT_SMALL_FACE,
            mergeSliverFaces=False, mergeSmallAngleFaces=False,
            mergeThinStairFaces=False, ignoreRedundantEntities=True,
            applyBlendControls=False),
            'virtual topology')
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

    def sweep(tag):
        best = None
        for g, dev, mf in MESH_SWEEP:
            nb = mesh_once(g, dev, mf)
            nn = len(p.nodes)
            log('Mesh try (%s): seed %.4f, curvature %.2f, min size %.2f -> %d elements, '
                '%d nodes, %s flagged%s' % (tag, g, dev, mf, len(p.elements), nn,
                                           '?' if nb >= 10 ** 9 else nb,
                                           '  (over node target, not used)'
                                           if nn > NODE_TARGET else ''))
            if nn > NODE_TARGET:
                continue
            if best is None or nb < best[0]:
                best = (nb, g, dev, mf)
            if nb == 0:
                break
        return best

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

    best = sweep('stage 1')
    chosen, stage = best, 1
    if best is not None and best[0] > 0 and IGNORE_TANGENT_SEAMS:
        feats_before = set(p.features.keys())
        n_ign = attempt(ignore_tangent_seams, 'seam ignore (virtual topology)')
        if n_ign:
            best2 = sweep('stage 2')
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
        seed = GLOBAL_SEED
        for k in range(8):
            mesh_once(seed, CURV_DEV, 0.1)
            if len(p.nodes) <= NODE_TARGET:
                break
            seed *= 1.15
    else:
        nb = mesh_once(chosen[1], chosen[2], chosen[3])
        log('Kept stage %d mesh: seed %.4f, curvature %.2f, min size %.2f (%d flagged).'
            % (stage, chosen[1], chosen[2], chosen[3], nb))
    log('Beam mesh: %d elements, %d nodes (C3D10).' % (len(p.elements), len(p.nodes)))
elif len(p.elements) == 0 or length_changed:
    p.generateMesh()

n_model_nodes = len(p.nodes) + 3          # + one reference node per roller
if n_model_nodes > NODE_LIMIT:
    raise RuntimeError('Mesh has %d nodes; the licence limit is %d. Raise '
                       'GLOBAL_SEED and run again.' % (n_model_nodes, NODE_LIMIT))

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
                 initialInc=0.01, maxNumInc=1000, minInc=1.0e-8, maxInc=0.02,
                 description='Top roller pushed down %.3f in' % U_TARGET)
model.boundaryConditions['TopRoller_Control'].setValuesInStep(
    stepName='Load', u2=-U_TARGET)
log('Loading: top roller U2 = -%.4f in (displacement control; RF2 = load).' % U_TARGET)

def _field_output():
    try:
        model.fieldOutputRequests['F-Output-1'].setValues(numIntervals=FIELD_FRAMES,
                                                          timeMarks=OFF)
        log('Field output: %d frames, time marks OFF (no exact-time-point warning).'
            % FIELD_FRAMES)
    except TypeError:
        model.fieldOutputRequests['F-Output-1'].setValues(numIntervals=FIELD_FRAMES)
        log('Field output: %d frames (this Abaqus has no timeMarks option).' % FIELD_FRAMES)


attempt(_field_output, 'field-output interval')

if 'H-LoadDisp' in model.historyOutputRequests.keys():
    del model.historyOutputRequests['H-LoadDisp']
model.HistoryOutputRequest(name='H-LoadDisp', createStepName='Load',
                           variables=('U2', 'RF2'),
                           region=a.sets['RP_TopRoller'],
                           sectionPoints=DEFAULT, rebar=EXCLUDE)

# ---------------------------------------------------------------------------
# 8. save, then job in its own folder, submit
# ---------------------------------------------------------------------------
base_dir = os.getcwd()
base = os.path.join(base_dir, JOB_NAME)
mdb.saveAs(pathName=base + '.cae')
log('Saved %s.cae (model only)' % base)

if CREATE_JOB:
    job_dir = os.path.join(base_dir, JOB_FOLDER)
    if not os.path.isdir(job_dir):
        os.makedirs(job_dir)
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
    try:
        mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, resultsFormat=ODB,
                numCpus=n_cpu, numDomains=n_cpu, memory=90, memoryUnits=PERCENTAGE,
                description='Stock 1 drilled plan v2 (Stock1_Drilled_v2)')
    except Exception:
        mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, numCpus=1,
                description='Stock 1 drilled plan v2 (Stock1_Drilled_v2)')
        n_cpu = 1
    log('Job "%s" defined (%d CPU%s).' % (JOB_NAME, n_cpu, '' if n_cpu == 1 else 's'))
    os.chdir(job_dir)                      # Abaqus writes job files to the work directory
    mdb.saveAs(pathName=os.path.join(job_dir, JOB_NAME + '.cae'))
    log('Saved the model with its job to %s' % os.path.join(job_dir, JOB_NAME + '.cae'))
    if SUBMIT_JOB:
        mdb.jobs[JOB_NAME].submit(consistencyChecking=OFF)
        log('Job "%s" submitted from %s.  Follow it in Job > Manager > Monitor '
            '(about 40 min).' % (JOB_NAME, job_dir))
        log('When it reads "Completed", run FOS_Stock1_Drilled_v2.py.')
    else:
        log('SUBMIT_JOB = False: job created, not submitted (Job > Manager > Submit).')
else:
    log('CREATE_JOB = False: model saved, no job.')
