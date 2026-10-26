# -*- coding: utf-8 -*-
"""
fix_ProjectBeam_v2.py  --  EMCH 308 Team 6, three-point-bend I-beam repair
==============================================================================
(Renumbered in the fix history; originally delivered as fix_ProjectBeam_v8.py.)

HOW TO RUN (Abaqus/CAE)
    1. File > Set Work Directory...  -> the folder holding ProjectBeam.cae
    2. (Nothing to open: the script opens ProjectBeam.cae from the work
       directory itself.)
    3. File > Run Script...  -> fix_ProjectBeam_v2.py
    The repaired model is saved as ProjectBeam_fixed.cae (the original file is
    not changed) and job "Beam_Fixed" is submitted.  Progress lines start with
    [fix_ProjectBeam] in the message area at the bottom of the window.
    The script always reopens the original ProjectBeam.cae from the work
    directory, so it can be re-run safely; it never builds on a _fixed file.

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
BEAM_LENGTH  = 8.2      # in  overall beam length (trimmed equally at both ends)
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
MESH_CANDIDATES = ((0.10, 0.05), (0.10, 0.035), (0.09, 0.05), (0.11, 0.04),
                   (0.10, 0.025), (0.10, None))
FIELD_FRAMES = 10       # field-output frames in the step (history: every inc)

JOB_NAME     = 'Beam_Fixed'
NUM_CPUS     = 4        # capped at the number of processors on the machine
SUBMIT_JOB   = True     # False = build and save only; submit from Job Manager

GEOM_TOL     = 1.0e-4   # in


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def log(text):
    print('[fix_ProjectBeam] ' + text)


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


log('fix_ProjectBeam v2 starting')
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
if JOB_NAME in mdb.jobs.keys():
    del mdb.jobs[JOB_NAME]
for name in extra_beams:
    del a.features[name]
    log('Deleted duplicate beam instance "%s" (was an unconnected region).' % name)
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
    raise RuntimeError('Part "%s" has no section assignment.' % BEAM_PART)
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
    # hole edges (both web faces of all four Fig. 1 holes), part coordinates
    lo, hi = part_box()
    pym, pzm = 0.5 * (lo[1] + hi[1]), 0.5 * (lo[2] + hi[2])
    centres = [(pzm + dz, pym + dy) for dz, dy in HOLES]
    hole_idx = []
    for e in p.edges:
        q = e.pointOn[0]
        if any(abs(math.hypot(q[2] - zc, q[1] - yc) - HOLE_R) < 2.0e-3
               for zc, yc in centres):
            hole_idx.append(e.index)
    hole_edges = None
    for i in hole_idx:
        s1 = p.edges[i:i + 1]
        hole_edges = s1 if hole_edges is None else hole_edges + s1
    log('Hole edges found for local seeding: %d (expected 8).' % len(hole_idx))

    def mesh_with(g, loc):
        p.deleteMesh()
        attempt(lambda: p.deleteSeeds(regions=p.edges), 'clearing old edge seeds')
        p.seedPart(size=g, deviationFactor=CURV_DEV, minSizeFactor=0.1)
        if loc and hole_edges is not None:
            p.seedEdgeBySize(edges=hole_edges, size=loc, deviationFactor=CURV_DEV,
                             minSizeFactor=0.1, constraint=FINER)
        p.generateMesh()

    best, current = None, None
    for g, loc in MESH_CANDIDATES:
        if loc and hole_edges is None:
            continue
        mesh_with(g, loc)
        current = (g, loc)
        nb = attempt(lambda: len(bad_elements()), 'mesh quality check')
        log('Mesh try: seed %.3f in, hole edges %s -> %d elements, %d nodes, '
            '%s flagged.' % (g, ('%.3f in' % loc) if loc else 'global',
                             len(p.elements), len(p.nodes),
                             '?' if nb is None else nb))
        if len(p.nodes) > NODE_TARGET:
            continue
        score = 10 ** 9 if nb is None else nb
        if best is None or score < best[0]:
            best = (score, g, loc)
        if score == 0:
            break
    if best is not None and current != best[1:]:
        mesh_with(best[1], best[2])
        log('Kept: seed %.3f in, hole edges %s.' % (best[1], best[2]))
    if best is None:
        seed = GLOBAL_SEED
        for k in range(8):
            mesh_with(seed, None)
            log('Beam meshed (C3D10), seed %.4f in: %d elements, %d nodes.'
                % (seed, len(p.elements), len(p.nodes)))
            if len(p.nodes) <= NODE_TARGET:
                break
            seed *= 1.15
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


top_faces, n_top = flange_faces(y_top)
bot_faces, n_bot = flange_faces(y_bot)
log('Beam contact faces (meshed): top = %d, bottom = %d' % (n_top, n_bot))

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

attempt(lambda: model.fieldOutputRequests['F-Output-1'].setValues(
    numIntervals=FIELD_FRAMES), 'field-output interval')

if 'H-LoadDisp' in model.historyOutputRequests.keys():
    del model.historyOutputRequests['H-LoadDisp']
model.HistoryOutputRequest(name='H-LoadDisp', createStepName='Load',
                           variables=('U2', 'RF2'),
                           region=a.sets['RP_TopRoller'],
                           sectionPoints=DEFAULT, rebar=EXCLUDE)

# ---------------------------------------------------------------------------
# 8. job, save, submit
# ---------------------------------------------------------------------------
try:
    n_cpu = os.cpu_count() or 1
except AttributeError:
    n_cpu = 1
n_cpu = max(1, min(NUM_CPUS, n_cpu))
try:
    mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, resultsFormat=ODB,
            numCpus=n_cpu, numDomains=n_cpu, memory=90, memoryUnits=PERCENTAGE,
            description='Repaired 3-point bend model (fix_ProjectBeam v2)')
except Exception:
    mdb.Job(name=JOB_NAME, model=model_name, type=ANALYSIS, numCpus=1,
            description='Repaired 3-point bend model (fix_ProjectBeam v2)')
    n_cpu = 1
log('Job "%s" created (%d CPU%s).' % (JOB_NAME, n_cpu, '' if n_cpu == 1 else 's'))

base = mdb.pathName[:-4] if mdb.pathName.lower().endswith('.cae') else ''
if not base:
    base = os.path.join(os.getcwd(), CAE_NAME[:-4])
if not base.endswith('_fixed'):
    base += '_fixed'
mdb.saveAs(pathName=base + '.cae')
log('Saved %s.cae' % base)

if SUBMIT_JOB:
    mdb.jobs[JOB_NAME].submit(consistencyChecking=OFF)
    log('Job "%s" submitted; watch it in Job Manager > Monitor.' % JOB_NAME)
else:
    log('Submit job "%s" from Job Manager when ready.' % JOB_NAME)
log('Done.  After the run: open Beam_Fixed.odb, Plot > Contours > On Deformed '
    'Shape (Options > Common: deformation scale factor 10 to see the bending); '
    'plot history RF2 vs U2 at RP_TopRoller for the load-deflection curve.')
