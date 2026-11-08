# -*- coding: utf-8 -*-
"""
make_RevC_design_sheet_v2.py  --  EMCH 308 Team 6, one-page Rev C design sheet

Same layout as Design_Sheet_Stock1_Drilled_v2 (Rev B): side elevation with the
test rollers, top- and bottom-flange plans, sections, the Abaqus load-displacement
curve with its offset line, requirement check, cost and weight tables, feature
schedule and title block.  v2: numbers and curve from the warning-free rerun Stock1_RevC_v2 (Nov 8, 2026,
0 solver warnings).  Numbers come from the Stock1_RevC_v2 Abaqus job
(results/final_design/) and the course cost sheet.

Writes Design_Sheet_Stock1_RevC_v2.png / .pdf to cad/drawings/ (repo layout: this
script lives in cad/drawings/source/), or next to the script otherwise.
Needs numpy + matplotlib.
"""
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT_DIR = os.path.normpath(os.path.join(HERE, ".."))
if os.path.basename(OUT_DIR) != "drawings":
    OUT_DIR = HERE
NAME = "Design_Sheet_Stock1_RevC_v2"
CSV_C = os.path.join(REPO, "results", "final_design", "FOS_Stock1_RevC_v2_LoadDisp.csv")
CSV_B = os.path.join(REPO, "results", "iterations", "Stock1_Drilled_v2_RevB", "FOS_Stock1_Drilled_v2_LoadDisp.csv")

# ---------------------------------------------------------------- design + results
H, BF, TF, TW, RF = 3.00, 2.50, 0.26, 0.15, 0.25
L, HZ, SPAN = 8.40, 4.20, 8.00
DH = 1.03
HOLES = ((-3.0, -0.375), (-1.0, 0.375), (1.0, 0.375), (3.0, -0.375))
ND, RR, BN = 0.65, 0.25, 1.20
ZL, ZS = 0.75, 3.50
R_TOP, R_BOT = 0.492, 0.197
RES = dict(k=251019.0, d0=-0.00004, P_off=8850.3, d_off=0.0552, fos=1.770, P_max=9612.0,
           nodes=234665, elems=151673, seed=0.0757, w=0.9139, w_cad=0.9139, vol=9.3252,
           p1=5411.0, set6250=0.0009, d6250=0.0258)
COST = (("Material, Stock 1 (8.40 in raw)", 55.02), ("Saw: set-up + 14 cuts", 40.05),
        ("Drill: set-up + 12 holes", 36.71))
C_TOT = 131.78
RHO = 0.098
W_ROWS = (("Stock 1 blank, 8.40 in", 14.4955 * RHO), ("4 Ø 1.03 web holes", -0.4999 * RHO),
          ("4 top-flange notches", -2.3183 * RHO), ("2 bottom-flange notches", -2.3521 * RHO))

# ---------------------------------------------------------------- style
INK, MUTED, FAINT = "#1f2937", "#6b7280", "#9ca3af"
FILL, PAD = "#e1e6ee", "#c5cfdc"
RED, REDF, BLUE, GREEN, GREENF = "#c0392b", "#f6d5d3", "#1f5fa8", "#1e7a46", "#e3f2e8"
ORANGE, ORANGEF = "#d9962b", "#f3d9a6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "hatch.linewidth": 0.7, "hatch.color": RED})
fig = plt.figure(figsize=(17, 11), dpi=150)
fig.patch.set_facecolor("white")
fig.add_artist(Rectangle((0.15 / 17, 0.15 / 11), 16.7 / 17, 10.7 / 11, transform=fig.transFigure,
                         fill=False, ec=INK, lw=1.4))


def ft(x, y, s, **k):
    fig.text(x / 17, y / 11, s, **k)


def view(x, y, w, h, xl, yl):
    ax = fig.add_axes([x / 17, y / 11, w / 17, h / 11])
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")
    return ax


def hdim(ax, x0, x1, y, s, col=INK, fs=8.5, ext=None, above=True):
    if ext is not None:
        for x in (x0, x1):
            ax.plot([x, x], [ext, y + (0.05 if y > ext else -0.05)], color=col, lw=0.5)
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=col, lw=0.8,
                                                      shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + (0.04 if above else -0.04), s, ha="center",
            va="bottom" if above else "top", fontsize=fs, color=col,
            bbox=dict(fc="white", ec="none", pad=0.5))


def vdim(ax, x, y0, y1, s, col=INK, fs=8.5, ext=None, side="right"):
    if ext is not None:
        for yy in (y0, y1):
            ax.plot([ext, x + (0.05 if x > ext else -0.05)], [yy, yy], color=col, lw=0.5)
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=col, lw=0.8,
                                                      shrinkA=0, shrinkB=0))
    ax.text(x + (0.05 if side == "right" else -0.05), (y0 + y1) / 2, s,
            ha="left" if side == "right" else "right", va="center", fontsize=fs, color=col,
            bbox=dict(fc="white", ec="none", pad=0.5))


def arc(cz, cx, a0, a1, n=18):
    return [(cz + RR * math.cos(math.radians(a)), cx + RR * math.sin(math.radians(a)))
            for a in np.linspace(a0, a1, n)]


def top_flange():
    b, n, zl, e = BF / 2, BN / 2, ZL, HZ
    p = [(-e, -n)] + arc(-zl - RR, -n - RR, 90, 0) + [(-zl, -b), (zl, -b)]
    p += arc(zl + RR, -n - RR, 180, 90) + [(e, -n), (e, n)]
    p += arc(zl + RR, n + RR, 270, 180) + [(zl, b), (-zl, b)]
    p += arc(-zl - RR, n + RR, 0, -90) + [(-e, n)]
    return p


def bottom_flange():
    b, n, zs, e = BF / 2, BN / 2, ZS, HZ
    p = [(-e, -b), (-zs, -b)] + arc(-zs + RR, -n - RR, 180, 90)
    p += arc(zs - RR, -n - RR, 90, 0) + [(zs, -b), (e, -b), (e, b), (zs, b)]
    p += arc(zs - RR, n + RR, 0, -90) + arc(-zs + RR, n + RR, 270, 180) + [(-zs, b), (-e, b)]
    return p


def i_outline(bt, bb, n=16):
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


# ---------------------------------------------------------------- header + KPI cards
ft(0.45, 10.42, "STOCK 1 I-BEAM  ·  REV C  ·  FINAL DESIGN", fontsize=22, weight="bold",
   color=INK, va="center")
ft(0.45, 10.05, "EMCH 308 Team 6 · AA I 3 × 2.03, 6061-T6 · 8.40 in long · "
   "3-point bend, 8.00 in span",
   fontsize=11, color=MUTED, va="center")
ft(0.45, 9.80, "Full-width flange pads under every roller, tips notched elsewhere · inches from mid-span (CL) · "
   "Abaqus job Stock1_RevC_v2, Nov 8, 2026 (0 warnings)", fontsize=9, color=MUTED, va="center")
cards = (("WEIGHT", "%.3f lb" % RES["w"], "limit ≤ 1.00 lb  ·  margin 0.086 lb"),
         ("FACTOR OF SAFETY", "%.3f" % RES["fos"], "required ≥ 1.25  ·  Abaqus offset method"),
         ("COST", "$%.2f" % C_TOT, "limit ≤ $600  ·  course cost sheet"))
for i, (lab, val, sub) in enumerate(cards):
    x0 = 10.05 + i * 2.25
    fig.add_artist(FancyBboxPatch((x0 / 17, 9.62 / 11), 2.10 / 17, 1.02 / 11,
                                  boxstyle="round,pad=0.002,rounding_size=0.006",
                                  transform=fig.transFigure, fc=GREENF, ec=GREEN, lw=1.3))
    ft(x0 + 0.14, 10.47, lab, fontsize=8.5, weight="bold", color=GREEN, va="center")
    fig.add_artist(FancyBboxPatch(((x0 + 1.50) / 17, 10.38 / 11), 0.48 / 17, 0.18 / 11,
                                  boxstyle="round,pad=0.002,rounding_size=0.004",
                                  transform=fig.transFigure, fc=GREEN, ec="none"))
    ft(x0 + 1.74, 10.47, "PASS", fontsize=7.5, weight="bold", color="white", ha="center", va="center")
    ft(x0 + 0.14, 10.08, val, fontsize=19, weight="bold", color=INK, va="center")
    ft(x0 + 0.14, 9.76, sub, fontsize=6.8, color=MUTED, va="center")

# ---------------------------------------------------------------- side elevation
ft(1.70, 9.50, "SIDE ELEVATION", fontsize=11, weight="bold", color=INK, va="center")
ft(1.70, 9.30, "web holes, notch ends and test rollers", fontsize=8.5, color=MUTED, va="center")
ax = view(0.30, 6.05, 9.40, 3.20, (-5.6, 5.6), (-2.75, 3.05))
h = H / 2
ax.add_patch(Rectangle((-HZ, -h), L, H, fc=FILL, ec=INK, lw=1.3))
ax.add_patch(Rectangle((-ZL, h - TF), 2 * ZL, TF, fc=PAD, ec="none"))
for z0 in (-HZ, ZS):
    ax.add_patch(Rectangle((z0, -h), HZ - ZS, TF, fc=PAD, ec="none"))
ax.add_patch(Rectangle((-HZ, -h), L, H, fc="none", ec=INK, lw=1.3))
for yy in (h - TF, -(h - TF)):
    ax.plot([-HZ, HZ], [yy, yy], color=MUTED, lw=0.7)
for z in (-ZL, ZL):
    ax.plot([z, z], [h - TF, h], color=INK, lw=0.8)
for z in (-ZS, ZS):
    ax.plot([z, z], [-h, -h + TF], color=INK, lw=0.8)
for zc, yc in HOLES:
    ax.add_patch(Circle((zc, yc), DH / 2, fc="white", ec=BLUE, lw=1.4))
    ax.plot([zc - 0.65, zc + 0.65], [yc, yc], color=FAINT, lw=0.5, ls="-.")
    ax.plot([zc, zc], [yc - 0.65, yc + 0.65], color=FAINT, lw=0.5, ls="-.")
ax.add_patch(Circle((0, h + R_TOP), R_TOP, fc=ORANGEF, ec=ORANGE, lw=1.2))
for zs in (-SPAN / 2, SPAN / 2):
    ax.add_patch(Circle((zs, -h - R_BOT), R_BOT, fc=ORANGEF, ec=ORANGE, lw=1.2))
    ax.text(zs, -h - 2 * R_BOT - 0.08, "support Ø0.394", fontsize=7.5, color=ORANGE,
            ha="center", va="top")
ax.annotate("", (0, h + 2 * R_TOP + 0.02), (0, h + 2 * R_TOP + 0.45),
            arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.4))
ax.text(-0.15, h + 2 * R_TOP + 0.25, "P  (load roller Ø0.984)", fontsize=8, color=ORANGE,
        ha="right", va="center")
ax.plot([0, 0], [-h - 0.2, h + 0.1], color=MUTED, lw=0.6, ls="-.")
ax.text(0, -h - 0.30, "CL", fontsize=7.5, color=MUTED, ha="center", va="top")
ax.annotate("4× Ø1.03 THRU WEB (Fig. 1)", (1.0 + 0.36, 0.375 + 0.36), (1.55, 2.15),
            fontsize=8.5, color=BLUE, ha="left", va="center",
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=0.8))
ax.annotate("full-width pad (shaded)", (-ZS - 0.35, -h + TF / 2), (-1.75, -1.02), fontsize=7.5,
            color=INK, ha="center", va="center", arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.6),
            bbox=dict(fc="white", ec="none", pad=0.4))
hdim(ax, 0, 1.0, h + 1.15, "1.00", ext=0.375 + 0.55)
hdim(ax, 0, 3.0, h + 1.45, "3.00", ext=-0.375 + 0.55)
vdim(ax, -1.0 - 0.75, 0, 0.375, "0.375", side="left", ext=-1.0)
vdim(ax, -3.0 - 0.75, -0.375, 0.0, "0.375", side="left", ext=-3.0)
vdim(ax, HZ + 0.35, -h, h, "3.00", ext=HZ)
hdim(ax, -SPAN / 2, SPAN / 2, -h - 0.85, "8.00 span", above=False)
hdim(ax, -HZ, HZ, -h - 1.20, "8.40 overall (raw length, no cross-cut; 0.20 past each support)", above=False,
     ext=-h - 0.05)


# ---------------------------------------------------------------- flange plans
def plan(y_axes, title, sub, outline, pads, reliefs, notes):
    ft(1.70, y_axes + 2.55, title, fontsize=11, weight="bold", color=INK, va="center")
    ft(1.70, y_axes + 2.35, sub, fontsize=8.5, color=MUTED, va="center")
    ax = view(0.30, y_axes, 9.40, 2.25, (-5.6, 5.6), (-1.95, 1.75))
    ax.add_patch(Rectangle((-HZ, -BF / 2), L, BF, fc=REDF, ec=RED, lw=0.8, hatch="////"))
    ax.add_patch(Polygon(outline, closed=True, fc=FILL, ec="none"))
    for z0, z1 in pads:
        ax.add_patch(Rectangle((z0, -BF / 2), z1 - z0, BF, fc=PAD, ec="none"))
    ax.add_patch(Polygon(outline, closed=True, fc="none", ec=INK, lw=1.2))
    for zc, xc in reliefs:
        ax.add_patch(Circle((zc, xc), RR, fc="none", ec=RED, lw=0.7, ls=(0, (2, 1.5))))
    for yy in (TW / 2, -TW / 2):
        ax.plot([-HZ, HZ], [yy, yy], color=FAINT, lw=0.5, ls="--")
    ax.plot([0, 0], [-1.45, 1.45], color=MUTED, lw=0.6, ls="-.")
    for zs in (-SPAN / 2, SPAN / 2):
        ax.plot([zs, zs], [-1.45, 1.45], color=ORANGE, lw=0.8, ls=(0, (2, 2)))
    vdim(ax, -HZ - 0.35, -BF / 2, BF / 2, "2.50", side="left", ext=-HZ)
    vdim(ax, HZ + 0.30, -BN / 2, BN / 2, "1.20", ext=HZ)
    vdim(ax, HZ + 0.30, BN / 2, BF / 2, ".65", ext=HZ, col=RED)
    for n in notes:
        n(ax)
    return ax


rel_t = [(s * (ZL + RR), t * (BN / 2 + RR)) for s in (1, -1) for t in (1, -1)]
rel_b = [(s * (ZS - RR), t * (BN / 2 + RR)) for s in (1, -1) for t in (1, -1)]
plan(3.30, "TOP FLANGE  ·  PLAN", "load-roller pad 1.50 long at CL · 4 notches 0.65 deep, "
     "3.45 long, run out the ends · 4 ×0.50 relief drills (R0.25 corners)",
     top_flange(), [(-ZL, ZL)], rel_t,
     [lambda ax: hdim(ax, -ZL, ZL, 1.40, "1.50 pad", ext=1.25),
      lambda ax: hdim(ax, ZL, HZ, 1.40, "3.45 notch", ext=1.25, col=RED),
      lambda ax: ax.text(0, -1.62, "load roller line", fontsize=7.5, color=ORANGE, ha="center",
                         va="top")])
plan(0.85, "BOTTOM FLANGE  ·  PLAN", "support pads 0.70 long at both ends · 2 notches 0.65 deep, "
     "7.00 long · 4 ×0.50 relief drills (R0.25 corners)",
     bottom_flange(), [(-HZ, -ZS), (ZS, HZ)], rel_b,
     [lambda ax: hdim(ax, ZS, HZ, 1.40, ".70 pad", ext=1.25),
      lambda ax: hdim(ax, -ZS, ZS, 1.40, "7.00 notch", ext=1.25, col=RED),
      lambda ax: ax.text(-SPAN / 2, -1.62, "support", fontsize=7.5, color=ORANGE, ha="center", va="top"),
      lambda ax: ax.text(SPAN / 2, -1.62, "support", fontsize=7.5, color=ORANGE, ha="center", va="top")])

# ---------------------------------------------------------------- sections
ft(10.10, 9.28, "SECTIONS", fontsize=11, weight="bold", color=INK, va="center")
ft(10.10, 9.08, "B–B at CL  ·  A–A between pads  ·  C–C over a support",
   fontsize=7.8, color=MUTED, va="center")
for i, (lab, bt, bb) in enumerate((("B–B", BF, BN), ("A–A", BN, BN), ("C–C", BN, BF))):
    ax = view(10.00 + i * 1.05, 6.60, 1.05, 2.30, (-1.40, 1.40), (-2.05, 2.05))
    for sy, bw in ((1, bt), (-1, bb)):
        y0 = H / 2 - TF if sy > 0 else -H / 2
        if bw < BF:
            for sx in (1, -1):
                ax.add_patch(Rectangle((bw / 2 if sx > 0 else -BF / 2, y0), ND, TF, fc=REDF,
                                       ec=RED, lw=0.5, hatch="////"))
    ax.add_patch(Polygon(i_outline(bt, bb), closed=True, fc=FILL, ec=INK, lw=0.9, hatch="////"))
    ax.text(0, 1.70, lab, ha="center", va="bottom", fontsize=8.5, weight="bold", color=INK)
    ax.text(0, -1.68, "top %.2f\nbottom %.2f" % (bt, bb), ha="center", va="top", fontsize=6.8,
            color=MUTED, linespacing=1.15)
ft(10.10, 6.45, "flange 0.26 · web 0.15 · R0.25 fillets · height 3.00", fontsize=7.5,
   color=MUTED, va="center")

# ---------------------------------------------------------------- FoS plot
ft(13.35, 9.28, "FOS  ·  ABAQUS LOAD–DISPLACEMENT", fontsize=11, weight="bold", color=INK,
   va="center")
ft(13.35, 9.08, "0.02 in offset · C3D10, %s nodes · 105 increments"
   % format(RES["nodes"], ","), fontsize=7.8, color=MUTED, va="center")
axp = fig.add_axes([13.75 / 17, 6.70 / 11, 2.95 / 17, 2.20 / 11])
try:
    c = np.loadtxt(CSV_C, delimiter=",", skiprows=1)
    xc, pc = c[:, 0], c[:, 1] / 1000
except Exception:
    xc = pc = None
try:
    b = np.loadtxt(CSV_B, delimiter=",", skiprows=1)
    axp.plot(b[:, 0], b[:, 1] / 1000, color=FAINT, lw=1.1, ls="--", label="Rev B, FOS 1.625")
except Exception:
    pass
if xc is not None:
    axp.plot(xc, pc, color=BLUE, lw=2.0, label="Rev C, FOS 1.770")
xo = np.linspace(RES["d0"] + 0.02, 0.064, 30)
axp.plot(xo, RES["k"] * (xo - RES["d0"] - 0.02) / 1000, color=RED, lw=1.1, ls=(0, (4, 2)),
         label="0.02 in offset line")
axp.plot([RES["d_off"]], [RES["P_off"] / 1000], "o", ms=6, mfc="white", mec=RED, mew=1.6, zorder=5)
axp.annotate("P_offset %.2f kip\nFOS %.3f" % (RES["P_off"] / 1000, RES["fos"]),
             (RES["d_off"], RES["P_off"] / 1000), (0.006, 8.3), fontsize=7.5,
             bbox=dict(fc="white", ec=FAINT, lw=0.6, pad=2),
             arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
for yy, t, col in ((6.25, "6.25 kip (FOS 1.25)", GREEN), (5.0, "5.0 kip design", MUTED)):
    axp.axhline(yy, color=col, lw=0.7, ls=":")
    axp.text(0.079, yy - 0.12, t, fontsize=6.5, color=col, ha="right", va="top")
axp.set_xlim(0, 0.08); axp.set_ylim(0, 10.5)
axp.set_xlabel("top-roller travel (in)", fontsize=7.5); axp.set_ylabel("load (kip)", fontsize=7.5)
axp.tick_params(labelsize=6.8)
for sp in ("top", "right"):
    axp.spines[sp].set_visible(False)
axp.grid(alpha=0.25)
axp.legend(loc="lower right", fontsize=6.2, frameon=False)

# ---------------------------------------------------------------- tables (right column)
X0, X1 = 10.10, 16.60


def head(y, t, x0=X0, x1=X1):
    ft(x0, y, t, fontsize=10.5, weight="bold", color=INK, va="center")
    return y - 0.30


def rows(y, cols, data, fs=8.2, step=0.215, bold_last=False, hdr=None):
    if hdr:
        for x, t, ha in hdr:
            ft(x, y, t, fontsize=7.6, color=MUTED, weight="bold", va="center", ha=ha)
        fig.add_artist(plt.Line2D([cols[0][0] / 17, X1 / 17], [(y - 0.11) / 11] * 2,
                                  color=FAINT, lw=0.6))
        y -= step
    for j, r in enumerate(data):
        last = bold_last and j == len(data) - 1
        for (x, ha), t in zip(cols, r):
            ft(x, y, t, fontsize=fs, color=GREEN if t == "PASS" else INK, va="center", ha=ha,
               weight="bold" if (last or t == "PASS") else "normal")
        y -= step
    return y


y = head(6.10, "REQUIREMENTS CHECK")
y = rows(y, ((X0, "left"), (12.20, "left"), (13.35, "left"), (X1, "right")),
         (("Weight", "≤ 1.00 lb", "0.914 lb (mesh = CAD to 0.003 %)", "PASS"),
          ("Factor of safety", "≥ 1.25", "1.770  (P_offset 8,850 lbf)", "PASS"),
          ("Cost", "≤ $600", "$131.78", "PASS"),
          ("Span / height", "fixed", "8.00 / 3.00 in", "PASS"),
          ("Fig. 1 holes", "4 × Ø1 ±.02", "4 × Ø1.03 (team choice, +.01 over)", "NOTE")),
         hdr=((X0, "Requirement", "left"), (12.20, "Limit", "left"), (13.35, "Rev C", "left")))
ft(X0, y + 0.02, "At 6,250 lbf: curve 3.6 %% below linear, est. permanent set %.4f in (offset allows 0.020)  ·  "
   "linear to about %s lbf" % (RES["set6250"], format(int(RES["p1"]), ",")), fontsize=7.2,
   color=MUTED, va="center")

ycost = head(4.25, "COST  ·  course cost sheet", X0, 13.10)
yy = rows(ycost, ((X0, "left"), (13.10, "right")), [(a_, "$%.2f" % b_) for a_, b_ in COST])
fig.add_artist(plt.Line2D([X0 / 17, 13.10 / 17], [(yy + 0.11) / 11] * 2, color=INK, lw=0.8))
yy = rows(yy - 0.02, ((X0, "left"), (13.10, "right")), (("Total", "$%.2f" % C_TOT),), bold_last=True)
ft(X0, yy + 0.02, "(0.1667 + 0.0167·n) h × \\$100/h · material 8.4 × 2.03/12 × \\$38.72\n"
   "with setups the sheet omits: \\$183.46 max", fontsize=6.9, color=MUTED, va="top", linespacing=1.4)

yw = head(4.25, "WEIGHT  ·  6061, 0.098 lb/in³", 13.45, X1)
yy = rows(yw, ((13.45, "left"), (X1, "right")), [(a_, "%.3f" % b_) for a_, b_ in W_ROWS])
fig.add_artist(plt.Line2D([13.45 / 17, X1 / 17], [(yy + 0.11) / 11] * 2, color=INK, lw=0.8))
yy = rows(yy - 0.02, ((13.45, "left"), (X1, "right")), (("Finished beam (lb)", "%.3f" % RES["w"]),),
          bold_last=True)
ft(13.45, yy + 0.02, "CAD 9.3252 in³; Abaqus mesh agrees to 0.003 %\n"
   "margin 0.086 lb (0.928 lb if notches 0.02 shallow)",
   fontsize=6.9, color=MUTED, va="top", linespacing=1.4)

y = head(2.62, "FEATURE SCHEDULE")
rows(y, ((X0, "left"), (10.45, "left"), (11.85, "left"), (12.35, "left"), (X1, "right")),
     (("A", "Ø1.03 (1-1/32)", "4", "web, z ±1.00 (y +0.375), ±3.00 (y −0.375)", "drill"),
      ("B", "Ø0.50 relief", "8", "top z ±1.00, bottom z ±3.25; x ±0.85", "drill first"),
      ("C", "notch 0.65 deep", "4", "top flange, |z| 0.75 → end, both tips, R0.25", "saw"),
      ("D", "notch 0.65 deep", "2", "bottom flange, z −3.50 → +3.50, both tips, R0.25", "saw")),
     fs=7.6, step=0.205,
     hdr=((X0, "Tag", "left"), (10.45, "Size", "left"), (11.85, "Qty", "left"),
          (12.35, "Location (from CL, web centreline)", "left")))

# title block
tb = (X0, 0.30, X1 - X0, 1.00)
fig.add_artist(Rectangle((tb[0] / 17, tb[1] / 11), tb[2] / 17, tb[3] / 11, transform=fig.transFigure,
                         fill=False, ec=INK, lw=1.1))
fig.add_artist(plt.Line2D([X0 / 17, X1 / 17], [0.80 / 11] * 2, color=INK, lw=0.8))
for xx in (13.85, 14.95):
    fig.add_artist(plt.Line2D([xx / 17] * 2, [0.30 / 11, 1.30 / 11], color=INK, lw=0.8))
for (x, ytop, lab, val) in ((X0, 1.30, "TITLE", "Stock 1 I-Beam, Rev C, Final Design"),
                            (13.85, 1.30, "REV", "C"), (14.95, 1.30, "MATERIAL", "6061-T6 Al"),
                            (X0, 0.80, "PROJECT", "EMCH 308 · USC Team 6 / MTC"),
                            (13.85, 0.80, "DATE", "2026-11-08"),
                            (14.95, 0.80, "UNITS / TOL", "in · ±0.02")):
    ft(x + 0.10, ytop - 0.13, lab, fontsize=6.8, color=MUTED, weight="bold", va="center")
    ft(x + 0.10, ytop - 0.34, val, fontsize=10 if lab == "TITLE" else 9.5, color=INK,
       weight="bold" if lab == "TITLE" else "normal", va="center")

ft(0.45, 0.48, "Notes: drill relief holes before any saw cut · saw tangent to the relief holes (no sharp inside "
   "corners) · cut the flange only, never the web or fillets · break edges 0.02 max", fontsize=7.6, color=MUTED, va="center")
ft(0.45, 0.28, "Manufacturing drawing: USC06_MTC06_IBeam_RevC (3 sheets) · model: abaqus/python/final/Stock1_RevC_v1.py "
   "· FoS: FOS_Stock1_RevC_v3.py (job Stock1_RevC_v2)", fontsize=7.6, color=MUTED, va="center")

for ext in ("png", "pdf"):
    fig.savefig(os.path.join(OUT_DIR, "%s.%s" % (NAME, ext)), facecolor="white",
                dpi=160 if ext == "png" else None)
print("saved", os.path.join(OUT_DIR, NAME))
