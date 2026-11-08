# -*- coding: utf-8 -*-
"""
plot_FOS_RevC_v2.py  --  EMCH 308 Team 6, Rev C load-displacement / FOS plot

v2: plots the warning-free rerun Stock1_RevC_v2 (Nov 8, 2026) and overlays the
Stock1_RevC_v1 curve for comparison; replaces the plain Abaqus-exported PNG.

Plain Python (numpy + matplotlib), not Abaqus.  Reads the curve that
FOS_Stock1_RevC_v3.py saved and redraws it on its own: Rev C only, with the
0.02 in offset line, the crossing, the elastic line and the 5,000 / 6,250 lbf
levels.  The offset method is recomputed from the CSV (15-45 % of peak fit), so
the numbers on the plot always match the data.

    python abaqus/python/tools/plot_FOS_RevC_v2.py
writes results/final_design/Stock1_RevC_v2_LoadDisp.png (and a copy in
Final_Design/Results/ when that folder exists).
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
JOB = 'Stock1_RevC_v2'
CSV = os.path.join(ROOT, 'results', 'final_design', 'FOS_%s_LoadDisp.csv' % JOB)
CSV_V1 = os.path.join(ROOT, 'results', 'final_design', 'FOS_Stock1_RevC_v1_LoadDisp.csv')
OUTS = [os.path.join(ROOT, 'results', 'final_design', '%s_LoadDisp.png' % JOB),
        os.path.join(ROOT, 'Final_Design', 'Results', '%s_LoadDisp.png' % JOB)]
P_DESIGN, P_TEST, OFFSET = 5000.0, 6250.0, 0.02

d = np.loadtxt(CSV, delimiter=',', skiprows=1)
x, P = d[:, 0], d[:, 1]
Pm = P.max()
m = (P >= 0.15 * Pm) & (P <= 0.45 * Pm) & (np.arange(len(P)) <= P.argmax())
k, b = np.polyfit(x[m], P[m], 1)
d0 = -b / k
g = P - k * (x - d0 - OFFSET)
i = np.where((g[:-1] > 0) & (g[1:] <= 0))[0][0]
f = g[i] / (g[i] - g[i + 1])
P_off, d_off = P[i] + f * (P[i + 1] - P[i]), x[i] + f * (x[i + 1] - x[i])
fos = P_off / P_DESIGN
x_t = np.interp(P_TEST, P, x)
dev = 1 - P_TEST / (k * (x_t - d0))
pset = x_t - (P_TEST / k + d0)

INK, MUT, BLUE, RED, GREEN = '#1f2937', '#6b7280', '#1f5fa8', '#c0392b', '#1e7a46'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
fig, ax = plt.subplots(figsize=(10, 6.2), dpi=200)
if os.path.isfile(CSV_V1):
    v1 = np.loadtxt(CSV_V1, delimiter=',', skiprows=1)
    ax.plot(v1[:, 0], v1[:, 1] / 1000, color='#9ca3af', lw=1.4, ls='--',
            label='Stock1_RevC_v1 (Nov 3, 7 solver warnings), FOS 1.772')
ax.plot(x, P / 1000, color=BLUE, lw=2.6, label='Stock1_RevC_v2, clean run (C3D10, 234,665 nodes)')
xl = np.linspace(0, 0.034, 20)
ax.plot(xl, k * (xl - d0) / 1000, color=BLUE, lw=0.8, ls=':', alpha=0.85,
        label='elastic line, k = {:,.0f} lbf/in'.format(k))
xo = np.linspace(d0 + OFFSET, 0.08, 50)
ax.plot(xo, k * (xo - d0 - OFFSET) / 1000, color=RED, lw=1.4, ls=(0, (5, 3)),
        label='0.02 in offset line')
for y, t, c in ((P_DESIGN / 1000, '5,000 lbf design load', MUT),
                (P_TEST / 1000, '6,250 lbf test load (FOS 1.25)', GREEN)):
    ax.axhline(y, color=c, lw=0.8, ls=(0, (1, 2)))
    ax.text(0.0795, y + 0.12, t, ha='right', va='bottom', fontsize=8.5, color=c)
ax.plot([d_off], [P_off / 1000], 'o', ms=8, mfc='white', mec=RED, mew=2, zorder=5)
ax.annotate('Offset-line crossing\n{:,.0f} lbf at {:.4f} in\nFOS = {:,.0f} / 5,000 = {:.3f}'
            .format(P_off, d_off, P_off, fos), (d_off, P_off / 1000), (0.0625, 6.85),
            fontsize=9.5, color=INK, ha='left',
            arrowprops=dict(arrowstyle='-|>', color=INK, lw=0.8))
ax.annotate('At 6,250 lbf: {:.4f} in travel,\n{:.1f} % below linear, ~{:.4f} in set'
            .format(x_t, 100 * dev, pset), (x_t, P_TEST / 1000), (0.031, 3.0),
            fontsize=9.5, color=INK, arrowprops=dict(arrowstyle='-|>', color=INK, lw=0.8))
ax.set_xlim(0, 0.08); ax.set_ylim(0, 10.5)
ax.set_xlabel('Top-roller travel, δ (in)'); ax.set_ylabel('Load, P (kip)')
ax.set_title('Rev C load–displacement and factor of safety', loc='left', fontsize=13,
             weight='bold', color=INK, pad=22)
ax.text(0, 1.025, JOB + ' • 0 solver warnings • 3-point bend, 8.00 in span • offset method, 0.02 in '
        '• FOS {:.3f} (required ≥ 1.25)'.format(fos), transform=ax.transAxes,
        fontsize=9, color=MUT)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
ax.grid(alpha=0.25)
ax.legend(loc='lower right', frameon=False, fontsize=9)
fig.tight_layout()
for o in OUTS:
    if os.path.isdir(os.path.dirname(o)):
        fig.savefig(o, facecolor='white')
        print('saved', o)
print('k %.0f  P_off %.1f  d_off %.4f  FOS %.3f' % (k, P_off, d_off, fos))
