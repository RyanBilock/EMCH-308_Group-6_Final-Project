# -*- coding: utf-8 -*-
"""
make_RevC_concept_v1.py  --  EMCH 308 Team 6, Rev C proposal sheet (concept only)

Clean-sheet Stock 1 design: the flange tips are saw-trimmed full length
(2.50 -> 1.50 in wide), the beam keeps the full 8.40 in raw length, and the only
holes are the four required Fig. 1 web holes, opened to dia 1.03 in.
No flange holes, no inside corners.

Writes Proposal_RevC_Stock1_SawTrim_v1.png and .pdf next to this script
(or to OUT_DIR).  Needs numpy + matplotlib.  Hand calculations only:
confirm in Abaqus before releasing a Rev C drawing to MTC.
"""
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
NAME = "Proposal_RevC_Stock1_SawTrim_v1"

# ---------------------------------------------------------------- design data
H, BF0, TF, TW, RF = 3.00, 2.50, 0.26, 0.15, 0.25   # Stock 1, AA I 3 x 2.03
BF = 1.50            # trimmed flange width
TRIM = (BF0 - BF) / 2.0
L = 8.40             # full raw length (no cross-cut)
SPAN = 8.00
D_HOLE = 1.03
HOLES = ((-3.0, -0.375), (-1.0, 0.375), (1.0, 0.375), (3.0, -0.375))
R_TOP, R_BOT = 0.492, 0.197
RHO = 0.098          # lb/in^3 (basis of the 2.03 lb/ft catalogue weight)
P_TEST = 6250.0
SY = 40.0            # ksi, 6061-T6 (model value)


def i_outline(bf, n=24):
    h, yi = H / 2.0, H / 2.0 - TF

    def arc(cx, cy, a0, a1):
        return [(cx + RF * math.cos(a), cy + RF * math.sin(a))
                for a in np.linspace(a0, a1, n)][1:]
    p = [(-bf / 2, -h), (bf / 2, -h), (bf / 2, -yi), (TW / 2 + RF, -yi)]
    p += arc(TW / 2 + RF, -yi + RF, -math.pi / 2, -math.pi) + [(TW / 2, yi - RF)]
    p += arc(TW / 2 + RF, yi - RF, math.pi, math.pi / 2)
    p += [(bf / 2, yi), (bf / 2, h), (-bf / 2, h), (-bf / 2, yi), (-TW / 2 - RF, yi)]
    p += arc(-TW / 2 - RF, yi - RF, math.pi / 2, 0) + [(-TW / 2, -yi + RF)]
    p += arc(-TW / 2 - RF, -yi + RF, 0, -math.pi / 2) + [(-bf / 2, -yi)]
    return p


def area_ix(p):
    a = np.array(p + [p[0]])
    x, y = a[:, 0], a[:, 1]
    c = x[:-1] * y[1:] - x[1:] * y[:-1]
    return abs(c.sum() / 2), abs(((y[:-1] ** 2 + y[:-1] * y[1:] + y[1:] ** 2) * c).sum() / 12)


A0, _ = area_ix(i_outline(BF0))
A1, I1 = area_ix(i_outline(BF))
W_BLANK = A0 * L * RHO
W_TRIM = 4 * TRIM * TF * L * RHO
W_HOLES = 4 * math.pi * (D_HOLE / 2) ** 2 * TW * RHO
W_FIN = W_BLANK - W_TRIM - W_HOLES
W_TOL = 4 * 0.02 * TF * L * RHO
SIG_CL = P_TEST * SPAN / 4 * (H / 2) / I1 / 1000
HW = H - 2 * TF
TAU = P_TEST / 2 / (TW * (HW - D_HOLE)) / 1000
VM = math.sqrt(3) * TAU
LIG = (HW / 2 - RF) - (0.375 + D_HOLE / 2)
C_MAT = L * 2.03 / 12 * 38.72
C_SAW = (0.1667 + 4 * 0.0167) * 100
C_DRL = (0.1667 + 4 * 0.0167) * 100
C_TOT = C_MAT + C_SAW + C_DRL

# ---------------------------------------------------------------- style
INK, MUTED, FAINT = "#1f2937", "#6b7280", "#9ca3af"
KEEP, RED, REDF, BLUE, GREEN = "#d5dae1", "#c0392b", "#f6d5d3", "#1f5fa8", "#1e7a46"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "hatch.linewidth": 0.8, "hatch.color": RED})

fig = plt.figure(figsize=(11, 8.5), dpi=200)
fig.patch.set_facecolor("white")


def ftext(x, y, s, **k):
    fig.text(x / 11, y / 8.5, s, **k)


def dim_h(ax, x0, x1, y, label, ext0=None, ext1=None, color=INK, fs=9, above=True):
    for x, e in ((x0, ext0), (x1, ext1)):
        if e is not None:
            ax.plot([x, x], [e, y + (0.05 if y > e else -0.05)], color=color, lw=0.5)
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=color,
                lw=0.8, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + (0.04 if above else -0.04), label, ha="center",
            va="bottom" if above else "top", fontsize=fs, color=color,
            bbox=dict(fc="white", ec="none", pad=0.6))


def dim_v(ax, x, y0, y1, label, ext0=None, ext1=None, color=INK, fs=9, side="left"):
    for y, e in ((y0, ext0), (y1, ext1)):
        if e is not None:
            ax.plot([e, x + (0.05 if x > e else -0.05)], [y, y], color=color, lw=0.5)
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=color,
                lw=0.8, shrinkA=0, shrinkB=0))
    ax.text(x + (-0.05 if side == "left" else 0.05), (y0 + y1) / 2, label,
            ha="right" if side == "left" else "left", va="center", fontsize=fs,
            color=color, bbox=dict(fc="white", ec="none", pad=0.6))


def view_axes(x, y, w, h, xlim, ylim):
    ax = fig.add_axes([x / 11, y / 8.5, w / 11, h / 8.5])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


# ---------------------------------------------------------------- header
ftext(0.40, 8.05, "PROPOSED DESIGN  —  REV C CONCEPT", fontsize=20,
      weight="bold", color=INK, va="center")
ftext(0.40, 7.70, "Stock 1  ·  AA I 3 × 2.03, 6061-T6  ·  clean sheet: "
      "saw-trimmed flanges + 4 required holes", fontsize=11.5,
      color=INK, va="center")
ftext(0.40, 7.47, "EMCH 308 Team 6  ·  8.40 in long  ·  3-point bend, 8.00 in span  ·  inches, from mid-span (CL)",
      fontsize=8.5, color=MUTED, va="center")
badge = FancyBboxPatch((7.55 / 11, 7.83 / 8.5), 3.05 / 11, 0.42 / 8.5,
                       boxstyle="round,pad=0.004,rounding_size=0.008",
                       transform=fig.transFigure, fc=GREEN, ec="none")
fig.patches.append(badge)
ftext(9.075, 8.04, "%.3f lb  MEETS ≤ 1.00 lb" % W_FIN, fontsize=14.5,
      weight="bold", color="white", ha="center", va="center")
ftext(9.075, 7.50, "%.3f lb under the limit  (Rev B: 0.001 lb)" % (1 - W_FIN),
      fontsize=8.5, color=GREEN, ha="center", va="center", weight="bold")
fig.add_artist(plt.Line2D([0.40 / 11, 10.60 / 11], [7.30 / 8.5] * 2, color=INK, lw=1.2))

# ---------------------------------------------------------------- top view
ftext(0.55, 7.08, "TOP VIEW", fontsize=11, weight="bold", color=INK, va="center")
ftext(1.55, 7.08, "— top and bottom flanges identical", fontsize=9.5,
      color=MUTED, va="center")
ax = view_axes(0.35, 4.55, 6.75, 2.45, (-4.75, 4.85), (-1.85, 1.65))
hz = L / 2
for s in (1, -1):
    ax.add_patch(Rectangle((-hz, s * BF / 2 if s > 0 else -BF0 / 2), L, TRIM,
                           fc=REDF, ec=RED, lw=0.9, hatch="////"))
ax.add_patch(Rectangle((-hz, -BF / 2), L, BF, fc=KEEP, ec=INK, lw=1.3))
ax.plot([-hz, hz, hz, -hz, -hz], [BF0 / 2, BF0 / 2, -BF0 / 2, -BF0 / 2, BF0 / 2],
        color=RED, lw=0.6, ls=(0, (4, 2)))
for yy in (TW / 2, -TW / 2):
    ax.plot([-hz, hz], [yy, yy], color=FAINT, lw=0.7, ls="--")
ax.text(-hz - 0.08, 0, "web", ha="right", va="center", fontsize=7.5, color=MUTED)
for zs in (-SPAN / 2, SPAN / 2):
    ax.plot([zs, zs], [-1.40, 1.30], color=BLUE, lw=0.8, ls=(0, (2, 2)))
ax.plot([0, 0], [-1.40, 1.30], color=MUTED, lw=0.7, ls="-.")
ax.text(0.06, -1.36, "CL", ha="left", va="center", fontsize=8, color=MUTED)
dim_h(ax, -hz, hz, 1.40, "8.40 beam length (raw stock length, no cross-cut)", ext0=1.25, ext1=1.25)
dim_h(ax, -SPAN / 2, SPAN / 2, -1.55, "8.00 support span", color=BLUE, above=False)
dim_v(ax, hz + 0.30, -BF / 2, BF / 2, "1.50", ext0=hz, ext1=hz, side="right")
dim_v(ax, hz + 0.30, BF / 2, BF0 / 2, "0.50", ext0=hz, ext1=hz, side="right", color=RED)
ax.text(-1.0, 1.0, "trim 0.50 off each flange tip — full-length saw cut, 4 places",
        ha="center", va="center", fontsize=8, color=RED, weight="bold",
        bbox=dict(fc="white", ec="none", pad=1.0))
ax.text(2.1, 0.38, "no flange holes — flanges stay solid\nunder the load roller and over both supports",
        ha="center", va="center", fontsize=8, color=INK, linespacing=1.3,
        bbox=dict(fc=KEEP, ec="none", pad=0.5))

# ---------------------------------------------------------------- side view
ftext(0.55, 4.43, "SIDE VIEW (web)", fontsize=11, weight="bold", color=INK, va="center")
ftext(2.25, 4.43, "— web unchanged", fontsize=9.5, color=MUTED, va="center")
ax = view_axes(0.35, 1.72, 6.75, 2.70, (-4.75, 4.85), (-2.65, 2.75))
h = H / 2
ax.add_patch(Rectangle((-hz, -h), L, H, fc=KEEP, ec=INK, lw=1.3))
for yy in (h - TF, -(h - TF)):
    ax.plot([-hz, hz], [yy, yy], color=MUTED, lw=0.7)
for yy in (h - TF - RF, -(h - TF - RF)):
    ax.plot([-hz, hz], [yy, yy], color=FAINT, lw=0.5, ls=":")
for zc, yc in HOLES:
    ax.add_patch(Circle((zc, yc), D_HOLE / 2, fc="white", ec=BLUE, lw=1.4))
    ax.plot([zc - 0.12, zc + 0.12], [yc, yc], color=BLUE, lw=0.6)
    ax.plot([zc, zc], [yc - 0.12, yc + 0.12], color=BLUE, lw=0.6)
ax.add_patch(Circle((0, h + R_TOP), R_TOP, fc="white", ec=INK, lw=1.2))
for zs in (-SPAN / 2, SPAN / 2):
    ax.add_patch(Circle((zs, -h - R_BOT), R_BOT, fc="white", ec=INK, lw=1.2))
    ax.plot([zs, zs], [-h - 0.5, h + 0.1], color=BLUE, lw=0.7, ls=(0, (2, 2)))
ax.annotate("", (0, h + 2 * R_TOP + 0.02), (0, h + 2 * R_TOP + 0.45),
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2))
ax.text(0.62, h + 2 * R_TOP - 0.15, "P = 6,250 lbf test\n(5,000 design)",
        fontsize=8.5, color=INK, va="center", linespacing=1.2)
ax.plot([0, 0], [-h - 0.05, h + 0.05], color=MUTED, lw=0.6, ls="-.")
ax.annotate("Ø1.03 THRU, 4 required (Fig. 1)\n1-1/32 drill (1.031)", (-1.0 - 0.37, 0.375 + 0.36),
            (-4.65, 2.15), fontsize=8.5, color=BLUE, ha="left", va="center",
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=0.8))
dim_h(ax, 0, 1.0, -2.05, "1.00", ext0=0.375 - 0.6, ext1=-0.0, color=BLUE, above=False)
dim_h(ax, 0, 3.0, -2.45, "3.00", ext0=-0.375 - 0.6, color=BLUE, above=False)
ax.plot([3.0, 3.0], [-0.375 - 0.55, -2.40], color=BLUE, lw=0.5)
ax.plot([1.0, 1.0], [0.375 - 0.55, -2.00], color=BLUE, lw=0.5)
dim_h(ax, SPAN / 2, hz, -2.05, "0.20", ext0=-h - 0.45, ext1=-h - 0.05, above=False)
ax.text(hz + 0.08, -2.48, "end overhang\n(Rev B: 0.10)", fontsize=7.5, color=MUTED,
        ha="center", va="top", linespacing=1.2)
dim_v(ax, -hz - 0.30, 0, 0.375, ".375", ext0=-hz, side="left", fs=8)
ax.plot([-1.0, -hz - 0.35], [0.375, 0.375], color=INK, lw=0.4, ls=":")
ax.plot([-hz - 0.35, hz], [0, 0], color=INK, lw=0.4, ls="-.", alpha=0.6)

# ---------------------------------------------------------------- section A-A
ftext(0.55, 1.62, "A–A  (any section)", fontsize=10, weight="bold", color=INK, va="center")
ax = view_axes(0.30, 0.05, 2.45, 1.36, (-1.75, 1.95), (-1.85, 1.75))
for sy in (1, -1):
    for sx in (1, -1):
        x0 = BF / 2 if sx > 0 else -BF0 / 2
        y0 = H / 2 - TF if sy > 0 else -H / 2
        ax.add_patch(Rectangle((x0, y0), TRIM, TF, fc=REDF, ec=RED, lw=0.8, hatch="////"))
ax.add_patch(Polygon(i_outline(BF), closed=True, fc=KEEP, ec=INK, lw=1.2))
dim_h(ax, -BF / 2, BF / 2, 1.58, "1.50", ext0=1.5, ext1=1.5, fs=8)
dim_h(ax, -BF0 / 2, BF0 / 2, -1.72, "2.50 stock", ext0=-1.5, ext1=-1.5, color=RED, fs=8, above=False)
dim_v(ax, 1.60, -1.5, 1.5, "3", ext0=1.25, ext1=1.25, side="right", fs=8)
ax.text(0.28, 0.35, ".15 web", fontsize=7.5, color=INK, va="center")
ax.text(0.28, -0.85, "R.25 4X", fontsize=7.5, color=INK, va="center")
ax.text(-1.55, 1.30, ".26", fontsize=7.5, color=INK, ha="center")

# ---------------------------------------------------------------- legend
lx, ly = 3.05, 1.30
for i, (fc, ec, hatch, lab) in enumerate(
        [(KEEP, INK, None, "Material kept"),
         (REDF, RED, "////", "Saw-trimmed off (this plan)"),
         ("white", BLUE, None, "Required holes, Ø1.03 (Fig. 1)")]):
    yy = ly - i * 0.40
    r = Rectangle((lx / 11, yy / 8.5), 0.36 / 11, 0.24 / 8.5, transform=fig.transFigure,
                  fc=fc, ec=ec, lw=1.2, hatch=hatch)
    fig.patches.append(r)
    ftext(lx + 0.50, yy + 0.12, lab, fontsize=9.5, color=INK, va="center")
ftext(3.05, 0.20, "Concept for team review — hand calculations only.\nConfirm in Abaqus before a Rev C drawing goes to MTC.",
      fontsize=7.5, linespacing=1.3, color=MUTED, va="center")

# ---------------------------------------------------------------- right panel
fig.add_artist(plt.Line2D([7.25 / 11] * 2, [0.35 / 8.5, 7.15 / 8.5], color="#e5e7eb", lw=1.0))
X0, X1 = 7.45, 10.60
y = [7.05]


def head(t):
    ftext(X0, y[0], t, fontsize=11, weight="bold", color=INK, va="center")
    fig.add_artist(plt.Line2D([X0 / 11, X1 / 11], [(y[0] - 0.15) / 8.5] * 2, color=INK, lw=0.8))
    y[0] -= 0.36


def row(l, r, col=INK, bold=False, fs=8.8, step=0.235):
    ftext(X0, y[0], l, fontsize=fs, color=col, va="center", weight="bold" if bold else "normal")
    ftext(X1, y[0], r, fontsize=fs, color=col, va="center", ha="right",
          weight="bold" if bold else "normal")
    y[0] -= step


def rule():
    fig.add_artist(plt.Line2D([X0 / 11, X1 / 11], [(y[0] + 0.12) / 8.5] * 2, color=FAINT, lw=0.6))
    y[0] -= 0.04


head("WEIGHT  (0.098 lb/in³)")
row("Blank, 8.40 in × 0.1692 lb/in", "%.3f lb" % W_BLANK)
row("– 4 flange-tip strips, 0.50 × 0.26 × 8.40", "–%.3f lb" % W_TRIM)
row("– 4 required Ø1.03 holes", "–%.3f lb" % W_HOLES)
rule()
row("Finished weight", "%.3f lb" % W_FIN, col=GREEN, bold=True)
row("Worst case, all 4 cuts 0.02 narrow", "%.3f lb" % (W_FIN + W_TOL), col=MUTED, fs=8.2)
y[0] -= 0.10

head("COST  (course cost sheet)")
row("Material, Stock 1, 8.40 in raw", "\\$%.2f" % C_MAT)
row("Saw: set-up + 4 lengthwise cuts", "\\$%.2f" % C_SAW)
row("Drill: set-up + 4 holes", "\\$%.2f" % C_DRL)
rule()
row("Total   (limit \\$600; Rev B \\$143.47)", "\\$%.2f" % C_TOT, col=GREEN, bold=True)
y[0] -= 0.10

head("STRENGTH  (hand calc at 6,250 lbf)")
row("Bending at CL, I = %.2f in⁴" % I1, "%.1f ksi → FOS %.1f" % (SIG_CL, SY / SIG_CL))
row("Avg web shear at Ø1.03 holes", "%.1f ksi (VM %.1f)" % (TAU, VM))
row("Hole edge to fillet strip", "%.3f in (Rev B 0.115)" % LIG)
ftext(X0, y[0] - 0.05,
      "The 0.15 in web sets first yield (about 4,500 lbf in every\n"
      "Stock 1 FE run), not the flanges. This plan leaves the web\n"
      "whole, doubles the end overhang over the supports, and\n"
      "removes every flange hole. Expect equal or later yield;\n"
      "the larger holes work slightly against it. FE must confirm.",
      fontsize=8.0, color=INK, va="top", linespacing=1.35)
y[0] -= 1.08

head("MANUFACTURING  (MTC)")
ftext(X0, y[0] + 0.08,
      "• 4 lengthwise saw cuts, one fence setting; cuts run\n"
      "   end to end, so there are no inside corners anywhere.\n"
      "• One drill size (1-1/32) for all 4 holes.\n"
      "• No cross-cut: uses the 8.40 raw length as supplied.\n"
      "• Break all edges 0.02 max.\n"
      "• Confirm with David Wilson that MTC can make the rip\n"
      "   cuts, and with the instructor that a rip is priced as a\n"
      "   saw cut.",
      fontsize=8.2, color=INK, va="top", linespacing=1.35)

for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT_DIR, "%s.%s" % (NAME, ext)), facecolor="white")
print("weight %.4f  cost %.2f  sigma %.2f  tau %.2f  lig %.3f" % (W_FIN, C_TOT, SIG_CL, TAU, LIG))
