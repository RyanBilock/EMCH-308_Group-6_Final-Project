# -*- coding: utf-8 -*-
"""
make_RevC_concept_v2.py  --  EMCH 308 Team 6, Rev C proposal sheet (concept only)

WHAT IS NEW IN v2
    * The flanges stay full width (2.50 in) wherever a test roller touches:
      top flange under the load roller (|z| <= 0.75 in) and bottom flange over
      both supports (|z| >= 3.50 in).  v1 saw-trimmed the tips full length,
      which also narrowed the flange under the rollers.
    * Everywhere else the flange tips are notched 0.65 in deep (flange 1.20 in
      wide).  Each inside corner is a dia 0.50 relief hole drilled first, so the
      saw cuts end on a R0.25 arc: no sharp inside corners.
    * Separate top- and bottom-flange views (the two flanges now differ) and
      three sections (mid-span, between, over a support).

Clean-sheet Stock 1 design, full 8.40 in raw length, the four required Fig. 1
web holes at dia 1.03.  Hand calculations only: confirm in Abaqus first.
Writes Proposal_RevC_Stock1_v2.png / .pdf to cad/concept_drawings/ (or next to
this script if that folder is not found).
"""
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch

_HERE = os.path.dirname(os.path.abspath(__file__))
# repo layout: cad/drawings/source/ -> write to cad/concept_drawings/
OUT_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "concept_drawings"))
if not os.path.isdir(OUT_DIR):
    OUT_DIR = _HERE
NAME = "Proposal_RevC_Stock1_v2"

# ---------------------------------------------------------------- design data
H, BF0, TF, TW, RF = 3.00, 2.50, 0.26, 0.15, 0.25   # Stock 1, AA I 3 x 2.03
DEPTH = 0.65                 # notch depth from each flange tip
BN = BF0 - 2 * DEPTH         # notched flange width (1.20)
RR = 0.25                    # relief-hole radius (dia 0.50 drill)
Z_LOAD = 0.75                # top-flange pad half-length (load roller)
Z_SUP = 3.50                 # bottom-flange pads from here to the ends
L = 8.40
HZ = L / 2
SPAN = 8.00
D_HOLE = 1.03
HOLES = ((-3.0, -0.375), (-1.0, 0.375), (1.0, 0.375), (3.0, -0.375))
R_TOP, R_BOT = 0.492, 0.197
RHO = 0.098
P_TEST = 6250.0
SY = 40.0
N_RELIEF, N_CUTS = 8, 14


def arc(cz, cx, a0, a1, n=20):
    return [(cz + RR * math.cos(math.radians(a)), cx + RR * math.sin(math.radians(a)))
            for a in np.linspace(a0, a1, n)]


def top_flange():
    """Kept outline of the top flange in plan, (z, x)."""
    b, n, zl, e = BF0 / 2, BN / 2, Z_LOAD, HZ
    p = [(-e, -n)] + arc(-zl - RR, -n - RR, 90, 0) + [(-zl, -b), (zl, -b)]
    p += arc(zl + RR, -n - RR, 180, 90) + [(e, -n), (e, n)]
    p += arc(zl + RR, n + RR, 270, 180) + [(zl, b), (-zl, b)]
    p += arc(-zl - RR, n + RR, 0, -90) + [(-e, n)]
    return p


def bottom_flange():
    b, n, zs, e = BF0 / 2, BN / 2, Z_SUP, HZ
    p = [(-e, -b), (-zs, -b)] + arc(-zs + RR, -n - RR, 180, 90)
    p += arc(zs - RR, -n - RR, 90, 0) + [(zs, -b), (e, -b), (e, b), (zs, b)]
    p += arc(zs - RR, n + RR, 0, -90) + arc(-zs + RR, n + RR, 270, 180)
    p += [(-zs, b), (-e, b)]
    return p


def poly_props(p):
    a = np.array(p + [p[0]])
    x, y = a[:, 0], a[:, 1]
    c = x[:-1] * y[1:] - x[1:] * y[:-1]
    A = c.sum() / 2
    sy = ((y[:-1] + y[1:]) * c).sum() / 6
    ixx = ((y[:-1] ** 2 + y[:-1] * y[1:] + y[1:] ** 2) * c).sum() / 12
    return abs(A), sy / A, abs(ixx)


def i_outline(bt, bb, n=20):
    """I-section (x, y) with top width bt, bottom width bb, R0.25 fillets."""
    h, yi = H / 2, H / 2 - TF

    def fa(cx, cy, a0, a1):
        return [(cx + RF * math.cos(math.radians(a)), cy + RF * math.sin(math.radians(a)))
                for a in np.linspace(a0, a1, n)][1:]
    p = [(-bb / 2, -h), (bb / 2, -h), (bb / 2, -yi), (TW / 2 + RF, -yi)]
    p += fa(TW / 2 + RF, -yi + RF, 270, 180) + [(TW / 2, yi - RF)]
    p += fa(TW / 2 + RF, yi - RF, 180, 90)
    p += [(bt / 2, yi), (bt / 2, h), (-bt / 2, h), (-bt / 2, yi), (-TW / 2 - RF, yi)]
    p += fa(-TW / 2 - RF, yi - RF, 90, 0) + [(-TW / 2, -yi + RF)]
    p += fa(-TW / 2 - RF, -yi + RF, 0, -90) + [(-bb / 2, -yi)]
    return p


# weight
A_full, _, _ = poly_props(i_outline(BF0, BF0))
A_core = A_full - 2 * BF0 * TF                       # web + fillets
A_top, _, _ = poly_props(top_flange())
A_bot, _, _ = poly_props(bottom_flange())
W_BLANK = A_full * L * RHO
W_NOTCH = (2 * BF0 * L - A_top - A_bot) * TF * RHO
W_HOLES = 4 * math.pi * (D_HOLE / 2) ** 2 * TW * RHO
W_FIN = W_BLANK - W_NOTCH - W_HOLES
NOTCH_LEN = 4 * (HZ - Z_LOAD) + 2 * (2 * Z_SUP)
W_TOL = NOTCH_LEN * 0.02 * TF * RHO

# strength at the test load
M_CL = P_TEST * SPAN / 4
_, yc, Ic = poly_props(i_outline(BF0, BN))            # mid-span: top pad, bottom notched
I_CL = Ic - poly_props(i_outline(BF0, BN))[0] * yc ** 2
SIG_CL = M_CL * (H / 2 + yc) / I_CL / 1000            # bottom fibre, tension
A1, _, I1 = poly_props(i_outline(BN, BN))             # z = 1: both notched, minus hole
yh = 0.375
Ah, Ih = TW * D_HOLE, TW * D_HOLE ** 3 / 12 + TW * D_HOLE * yh ** 2
yb = -Ah * yh / (A1 - Ah)
In = I1 - Ih - (A1 - Ah) * yb ** 2
SIG_Z1 = P_TEST / 2 * (SPAN / 2 - 1.0) * (H / 2 + abs(yb)) / In / 1000
HW = H - 2 * TF
TAU = P_TEST / 2 / (TW * (HW - D_HOLE)) / 1000
VM = math.sqrt(3) * TAU
LIG = (HW / 2 - RF) - (0.375 + D_HOLE / 2)

C_MAT = L * 2.03 / 12 * 38.72
C_SAW = (0.1667 + N_CUTS * 0.0167) * 100
C_DRL = (0.1667 + (4 + N_RELIEF) * 0.0167) * 100
C_TOT = C_MAT + C_SAW + C_DRL

# ---------------------------------------------------------------- style
INK, MUTED, FAINT = "#1f2937", "#6b7280", "#9ca3af"
KEEP, PAD = "#d5dae1", "#b9c3d0"
RED, REDF, BLUE, GREEN = "#c0392b", "#f6d5d3", "#1f5fa8", "#1e7a46"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "hatch.linewidth": 0.8, "hatch.color": RED})
fig = plt.figure(figsize=(11, 8.5), dpi=200)
fig.patch.set_facecolor("white")


def ftext(x, y, s, **k):
    fig.text(x / 11, y / 8.5, s, **k)


def dim_h(ax, x0, x1, y, label, ext=None, color=INK, fs=8.5, above=True):
    if ext is not None:
        for x in (x0, x1):
            ax.plot([x, x], [ext, y + (0.06 if y > ext else -0.06)], color=color, lw=0.5)
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=color,
                lw=0.8, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + (0.05 if above else -0.05), label, ha="center",
            va="bottom" if above else "top", fontsize=fs, color=color,
            bbox=dict(fc="white", ec="none", pad=0.5))


def dim_v(ax, x, y0, y1, label, ext=None, color=INK, fs=8.5, side="right"):
    if ext is not None:
        for y in (y0, y1):
            ax.plot([ext, x + (0.06 if x > ext else -0.06)], [y, y], color=color, lw=0.5)
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=color,
                lw=0.8, shrinkA=0, shrinkB=0))
    ax.text(x + (0.06 if side == "right" else -0.06), (y0 + y1) / 2, label,
            ha="left" if side == "right" else "right", va="center", fontsize=fs,
            color=color, bbox=dict(fc="white", ec="none", pad=0.5))


def view_axes(x, y, w, h, xlim, ylim):
    ax = fig.add_axes([x / 11, y / 8.5, w / 11, h / 8.5])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


# ---------------------------------------------------------------- header
ftext(0.40, 8.05, "PROPOSED DESIGN  —  REV C CONCEPT (v2)", fontsize=19,
      weight="bold", color=INK, va="center")
ftext(0.40, 7.70, "Stock 1  ·  AA I 3 × 2.03, 6061-T6  ·  full-width pads at the 3 rollers, "
      "flange tips notched elsewhere", fontsize=11, color=INK, va="center")
ftext(0.40, 7.47, "EMCH 308 Team 6  ·  8.40 in long  ·  3-point bend, 8.00 in span  ·  "
      "inches, from mid-span (CL)", fontsize=8.5, color=MUTED, va="center")
fig.patches.append(FancyBboxPatch((7.70 / 11, 7.83 / 8.5), 2.90 / 11, 0.42 / 8.5,
                   boxstyle="round,pad=0.004,rounding_size=0.008",
                   transform=fig.transFigure, fc=GREEN, ec="none"))
ftext(9.15, 8.04, "%.3f lb  MEETS ≤ 1.00 lb" % W_FIN, fontsize=14,
      weight="bold", color="white", ha="center", va="center")
ftext(9.15, 7.50, "%.3f lb under the limit  (Rev B: 0.001 lb)" % (1 - W_FIN),
      fontsize=8.5, color=GREEN, ha="center", va="center", weight="bold")
fig.add_artist(plt.Line2D([0.40 / 11, 10.60 / 11], [7.30 / 8.5] * 2, color=INK, lw=1.2))


# ---------------------------------------------------------------- flange plans
def flange_view(x0, title, sub, outline, pads, holes, load_side):
    ftext(x0 + 0.15, 7.08, title, fontsize=10, weight="bold", color=INK, va="center")
    ftext(x0 + 0.15, 6.88, sub, fontsize=8, color=MUTED, va="center")
    ax = view_axes(x0, 5.05, 3.40, 1.75, (-4.65, 4.65), (-2.25, 2.30))
    ax.add_patch(Rectangle((-HZ, -BF0 / 2), L, BF0, fc=REDF, ec=RED, lw=0.8, hatch="////"))
    ax.add_patch(Polygon(outline, closed=True, fc=KEEP, ec=INK, lw=1.1))
    for z0, z1 in pads:
        ax.add_patch(Rectangle((z0, -BF0 / 2), z1 - z0, BF0, fc=PAD, ec="none"))
    ax.add_patch(Polygon(outline, closed=True, fc="none", ec=INK, lw=1.1))
    for zc, xc in holes:
        ax.add_patch(Circle((zc, xc), RR, fc="none", ec=RED, lw=0.7, ls=(0, (2, 1.5))))
        ax.plot([zc - 0.08, zc + 0.08], [xc, xc], color=RED, lw=0.5)
        ax.plot([zc, zc], [xc - 0.08, xc + 0.08], color=RED, lw=0.5)
    for yy in (TW / 2, -TW / 2):
        ax.plot([-HZ, HZ], [yy, yy], color=FAINT, lw=0.5, ls="--")
    for zs in (-SPAN / 2, SPAN / 2):
        ax.plot([zs, zs], [-1.55, 1.55], color=BLUE, lw=0.7, ls=(0, (2, 2)))
    ax.plot([0, 0], [-1.55, 1.55], color=MUTED, lw=0.6, ls="-.")
    return ax


ax = flange_view(0.30, "TOP FLANGE", "viewed from above  ·  load-roller pad at CL",
                 top_flange(), [(-Z_LOAD, Z_LOAD)],
                 [(s * (Z_LOAD + RR), t * (BN / 2 + RR)) for s in (1, -1) for t in (1, -1)], True)
dim_h(ax, -Z_LOAD, Z_LOAD, 1.55, "1.50 pad", ext=1.25, fs=7.5)
dim_h(ax, -HZ, HZ, 1.95, "8.40", ext=1.25, fs=7.5)
dim_v(ax, HZ + 0.12, -BN / 2, BN / 2, "1.20", ext=HZ, fs=7.5)
dim_v(ax, HZ + 0.12, BN / 2, BF0 / 2, ".65", ext=HZ, fs=7.5, color=RED)
ax.text(-2.45, -1.62, "notch 0.65 deep, runs out the end", fontsize=7, color=RED,
        ha="center", va="top")

ax = flange_view(3.75, "BOTTOM FLANGE", "viewed from below  ·  support pads at both ends",
                 bottom_flange(), [(-HZ, -Z_SUP), (Z_SUP, HZ)],
                 [(s * (Z_SUP - RR), t * (BN / 2 + RR)) for s in (1, -1) for t in (1, -1)], False)
dim_h(ax, Z_SUP, HZ, 1.55, ".70", ext=1.25, fs=7.5)
dim_h(ax, -Z_SUP, Z_SUP, 1.95, "7.00 notch", ext=1.25, fs=7.5, color=RED)
dim_h(ax, -SPAN / 2, SPAN / 2, -1.70, "8.00 support span", color=BLUE, fs=7.5, above=False)
ax.annotate("Ø.50 relief drill (R.25 corner)\n8X total, 4 per flange",
            (-Z_SUP + RR - 0.05, BN / 2 + RR - 0.20), (-1.30, 0.0),
            fontsize=7, color=RED, ha="center", va="center", linespacing=1.15,
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.7),
            bbox=dict(fc="white", ec="none", pad=0.6))

# ---------------------------------------------------------------- side view
ftext(0.45, 4.95, "SIDE VIEW (web)", fontsize=10.5, weight="bold", color=INK, va="center")
ftext(2.10, 4.95, "— web unchanged", fontsize=9, color=MUTED, va="center")
ax = view_axes(0.30, 1.85, 6.85, 3.05, (-4.75, 4.85), (-2.70, 2.70))
h = H / 2
ax.add_patch(Rectangle((-HZ, -h), L, H, fc=KEEP, ec=INK, lw=1.2))
ax.add_patch(Rectangle((-Z_LOAD, h - TF), 2 * Z_LOAD, TF, fc=PAD, ec="none"))
for z0 in (-HZ, Z_SUP):
    ax.add_patch(Rectangle((z0, -h), HZ - Z_SUP, TF, fc=PAD, ec="none"))
ax.add_patch(Rectangle((-HZ, -h), L, H, fc="none", ec=INK, lw=1.2))
for yy in (h - TF, -(h - TF)):
    ax.plot([-HZ, HZ], [yy, yy], color=MUTED, lw=0.7)
for zc, yc_ in HOLES:
    ax.add_patch(Circle((zc, yc_), D_HOLE / 2, fc="white", ec=BLUE, lw=1.3))
    ax.plot([zc - 0.11, zc + 0.11], [yc_, yc_], color=BLUE, lw=0.6)
    ax.plot([zc, zc], [yc_ - 0.11, yc_ + 0.11], color=BLUE, lw=0.6)
ax.add_patch(Circle((0, h + R_TOP), R_TOP, fc="white", ec=INK, lw=1.1))
for zs in (-SPAN / 2, SPAN / 2):
    ax.add_patch(Circle((zs, -h - R_BOT), R_BOT, fc="white", ec=INK, lw=1.1))
    ax.plot([zs, zs], [-h - 0.45, h + 0.05], color=BLUE, lw=0.6, ls=(0, (2, 2)))
ax.annotate("", (0, h + 2 * R_TOP + 0.02), (0, h + 2 * R_TOP + 0.40),
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.1))
ax.text(0.60, h + 2 * R_TOP - 0.15, "P = 6,250 lbf test\n(5,000 design)", fontsize=8,
        color=INK, va="center", linespacing=1.2)
ax.plot([0, 0], [-h - 0.05, h + 0.05], color=MUTED, lw=0.6, ls="-.")
ax.annotate("Ø1.03 THRU, 4 required (Fig. 1)\n1-1/32 drill (1.031)", (-1.37, 0.73),
            (-4.65, 2.20), fontsize=8, color=BLUE, ha="left", va="center",
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=0.8))
ax.text(-2.55, -2.15, "shaded = full-width flange pad\nunder each roller", fontsize=7.5,
        color=INK, ha="center", va="center", linespacing=1.2)
dim_h(ax, 0, 1.0, -2.05, "1.00", color=BLUE, above=False, fs=8)
dim_h(ax, 0, 3.0, -2.42, "3.00", color=BLUE, above=False, fs=8)
ax.plot([3.0, 3.0], [-0.375 - 0.55, -2.38], color=BLUE, lw=0.5)
ax.plot([1.0, 1.0], [0.375 - 0.55, -2.00], color=BLUE, lw=0.5)
ax.plot([0, 0], [-h - 0.05, -2.45], color=BLUE, lw=0.5)
dim_h(ax, SPAN / 2, HZ, -2.05, ".20", ext=-h - 0.42, above=False, fs=8)
ax.text(HZ + 0.12, -2.40, "overhang\n(Rev B .10)", fontsize=7, color=MUTED,
        ha="center", va="top", linespacing=1.15)
dim_v(ax, -HZ - 0.28, 0, 0.375, ".375", side="left", fs=7.5)
ax.plot([-1.0, -HZ - 0.33], [0.375, 0.375], color=INK, lw=0.4, ls=":")
ax.plot([-HZ - 0.33, HZ], [0, 0], color=INK, lw=0.4, ls="-.", alpha=0.5)

# ---------------------------------------------------------------- sections
ftext(0.45, 1.72, "SECTIONS", fontsize=10, weight="bold", color=INK, va="center")
ftext(1.45, 1.72, "— flange .26, web .15, R.25 fillets (stock)", fontsize=8, color=MUTED, va="center")
secs = [("B–B  z = 0", BF0, BN, "load-roller pad"),
        ("A–A  z = ±2", BN, BN, "between pads"),
        ("C–C  z = ±4", BN, BF0, "support pad")]
for i, (lab, bt, bb, note) in enumerate(secs):
    x0 = 0.30 + i * 1.35
    ax = view_axes(x0, 0.10, 1.30, 1.40, (-1.45, 1.45), (-1.95, 1.75))
    for sy, bw in ((1, bt), (-1, bb)):
        y0 = H / 2 - TF if sy > 0 else -H / 2
        if bw < BF0:
            for sx in (1, -1):
                xx = bw / 2 if sx > 0 else -BF0 / 2
                ax.add_patch(Rectangle((xx, y0), DEPTH, TF, fc=REDF, ec=RED, lw=0.6, hatch="////"))
    ax.add_patch(Polygon(i_outline(bt, bb), closed=True, fc=KEEP, ec=INK, lw=1.0))
    for sy, bw in ((1, bt), (-1, bb)):
        if bw == BF0:
            y0 = H / 2 - TF if sy > 0 else -H / 2
            ax.add_patch(Rectangle((-BF0 / 2, y0), BF0, TF, fc=PAD, ec=INK, lw=1.0))
    ax.text(0, 1.62, lab, ha="center", va="bottom", fontsize=7.5, weight="bold", color=INK)
    ax.text(0, -1.62, note, ha="center", va="top", fontsize=7, color=MUTED)

# legend
lx, ly = 4.55, 1.45
for i, (fc, ec, hatch, lab) in enumerate(
        [(KEEP, INK, None, "Material kept"),
         (PAD, INK, None, "Full-width pad (roller contact)"),
         (REDF, RED, "////", "Notched off (saw, after relief drill)"),
         ("white", BLUE, None, "Required holes, Ø1.03")]):
    yy = ly - i * 0.31
    fig.patches.append(Rectangle((lx / 11, yy / 8.5), 0.30 / 11, 0.20 / 8.5,
                                 transform=fig.transFigure, fc=fc, ec=ec, lw=1.0, hatch=hatch))
    ftext(lx + 0.40, yy + 0.10, lab, fontsize=8.3, color=INK, va="center")
ftext(4.55, 0.18, "Concept for team review — hand calculations only.\n"
      "Confirm in Abaqus before a Rev C drawing goes to MTC.",
      fontsize=7, color=MUTED, va="center", linespacing=1.3)

# ---------------------------------------------------------------- right panel
fig.add_artist(plt.Line2D([7.35 / 11] * 2, [0.30 / 8.5, 7.15 / 8.5], color="#e5e7eb", lw=1.0))
X0, X1 = 7.55, 10.60
y = [7.05]


def head(t):
    ftext(X0, y[0], t, fontsize=10.5, weight="bold", color=INK, va="center")
    fig.add_artist(plt.Line2D([X0 / 11, X1 / 11], [(y[0] - 0.15) / 8.5] * 2, color=INK, lw=0.8))
    y[0] -= 0.35


def row(l, r, col=INK, bold=False, fs=8.4, step=0.225):
    ftext(X0, y[0], l, fontsize=fs, color=col, va="center", weight="bold" if bold else "normal")
    ftext(X1, y[0], r, fontsize=fs, color=col, va="center", ha="right",
          weight="bold" if bold else "normal")
    y[0] -= step


def rule():
    fig.add_artist(plt.Line2D([X0 / 11, X1 / 11], [(y[0] + 0.11) / 8.5] * 2, color=FAINT, lw=0.6))
    y[0] -= 0.04


head("WEIGHT  (0.098 lb/in³)")
row("Blank, 8.40 in × 0.1692 lb/in", "%.3f lb" % W_BLANK)
row("– flange notches, %.1f in × 0.65 × 0.26" % NOTCH_LEN, "–%.3f lb" % W_NOTCH)
row("– 4 required Ø1.03 holes", "–%.3f lb" % W_HOLES)
rule()
row("Finished weight", "%.3f lb" % W_FIN, col=GREEN, bold=True)
row("Worst case, every notch 0.02 shallow", "%.3f lb" % (W_FIN + W_TOL), col=MUTED, fs=8.0)
y[0] -= 0.08

head("COST  (course cost sheet)")
row("Material, Stock 1, 8.40 in raw", "\\$%.2f" % C_MAT)
row("Saw: set-up + %d cuts" % N_CUTS, "\\$%.2f" % C_SAW)
row("Drill: set-up + %d holes (4 web, 8 relief)" % (4 + N_RELIEF), "\\$%.2f" % C_DRL)
rule()
row("Total   (limit \\$600; Rev B \\$143.47)", "\\$%.2f" % C_TOT, col=GREEN, bold=True)
y[0] -= 0.08

head("STRENGTH  (hand calc at 6,250 lbf)")
row("Bending at CL, bottom fibre", "%.1f ksi → FOS %.1f" % (SIG_CL, SY / SIG_CL))
row("Bending at z = 1 hole section", "%.1f ksi → FOS %.1f" % (SIG_Z1, SY / SIG_Z1))
row("Avg web shear at Ø1.03 holes", "%.1f ksi (VM %.1f)" % (TAU, VM))
row("Hole edge to fillet strip", "%.3f in (Rev B .115)" % LIG)
ftext(X0, y[0] - 0.02,
      "The 0.15 in web sets first yield (about 4,500 lbf in\n"
      "every Stock 1 FE run). Flange tips away from the\n"
      "rollers do not: the notched FE run (0.75 deep, pads\n"
      "kept) matched Rev B's curve. This plan keeps the web\n"
      "whole, keeps every roller zone full width, and doubles\n"
      "the support overhang. FE must confirm.",
      fontsize=7.8, color=INK, va="top", linespacing=1.32)
y[0] -= 1.22

head("MANUFACTURING  (MTC)")
ftext(X0, y[0] + 0.08,
      "• Drill the 8 Ø.50 relief holes first; each saw cut\n"
      "   ends tangent to one, so every inside corner is R.25.\n"
      "• Top flange: 2 cuts per notch (runs out the end).\n"
      "   Bottom flange: 3 cuts per notch.  14 cuts total.\n"
      "• Two drill sizes: 1-1/32 (web), 1/2 (relief).\n"
      "• No cross-cut: uses the 8.40 raw length as supplied.\n"
      "• Break all edges 0.02 max.\n"
      "• Confirm with David Wilson that MTC can saw to a\n"
      "   relief hole this way.",
      fontsize=7.8, color=INK, va="top", linespacing=1.32)

for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT_DIR, "%s.%s" % (NAME, ext)), facecolor="white")
print("W %.4f notch %.4f tol %.4f  cost %.2f  sigCL %.2f sigZ1 %.2f tau %.2f  I_CL %.3f yc %.3f"
      % (W_FIN, W_NOTCH, W_TOL, C_TOT, SIG_CL, SIG_Z1, TAU, I_CL, yc))
