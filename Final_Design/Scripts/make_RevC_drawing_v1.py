"""make_RevC_drawing_v1.py  --  USC06_MTC06_IBeam_RevC manufacturing drawing for MTC.

Same style as make_RevB_drawing_v3.py (course example 'I-Beam Blank'): thin lines,
arrowed dimension lines, long dash-dot centerlines, leader callouts, EMCH 308 title
block.  All dimensions are baseline dimensions from the top-left corner (datum point)
of each view.  Three B-size sheets (17 x 11), all views 1:1:
    1/3  front view (web holes, notch ends) + end view (stock section)
    2/3  top flange, viewed from above (load-roller pad, 4 notches)
    3/3  bottom flange, viewed from below (support pads, 2 notches)
Writes USC06_MTC06_IBeam_RevC_Drawing.pdf and _sheet1..3.png to cad/ (repo layout:
this script lives in cad/drawings/source/), or next to the script otherwise.
"""
import math
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrowPatch
from matplotlib.lines import Line2D

plt.rcParams.update({'font.family': ['Liberation Sans', 'DejaVu Sans']})
K = 'black'
LW_OBJ, LW_THIN = 0.9, 0.45
FS_DIM, FS_NOTE, FS_VIEW = 11, 11, 12
CHAIN = (0, (16, 4, 3, 4))
HIDDEN = (0, (5, 3))
PHANTOM = (0, (10, 3, 2, 3, 2, 3))

# ---- Rev C geometry (inches, z from the left end, w down from the flange tip on top)
L, H, BF, TF, TW, RF = 8.40, 3.00, 2.50, 0.26, 0.15, 0.25
ZM = L / 2
DH = 1.03                         # Fig. 1 web holes (1-1/32 drill)
FIG1 = [(ZM - 3.0, H / 2 - 0.375), (ZM - 1.0, H / 2 + 0.375), (ZM + 1.0, H / 2 + 0.375),
        (ZM + 3.0, H / 2 - 0.375)]                    # (from left end, from bottom)
ND, RR = 0.65, 0.25               # notch depth, relief radius (dia .50 drill)
TP = (ZM - 0.75, ZM + 0.75)       # top-flange pad: 3.45 .. 4.95
BP = (ZM - 3.50, ZM + 3.50)       # bottom-flange notch: 0.70 .. 7.70 (pads outside)
WR = (ND - RR, BF - ND + RR)      # relief-hole rows: .40 and 2.10 from the top edge


def fmt(v):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return s[1:] if s.startswith('0.') else s


class Sheet:
    def __init__(self):
        self.fig = plt.figure(figsize=(17, 11), dpi=150)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        ax = self.ax
        ax.set_xlim(0, 17); ax.set_ylim(0, 11); ax.set_aspect('equal'); ax.axis('off')
        ax.add_patch(Rectangle((0.4, 0.4), 16.2, 10.2, fill=False, ec=K, lw=1.2))
        for (x, y, r) in ((8.5, 10.6, 270), (0.4, 5.5, 0), (16.6, 5.5, 180)):
            self.centering(x, y, r)

    def centering(self, x, y, rot):
        t = 0.10
        pts = {0: [(x, y), (x + t * 1.4, y + t), (x + t * 1.4, y - t)],
               180: [(x, y), (x - t * 1.4, y + t), (x - t * 1.4, y - t)],
               90: [(x, y), (x - t, y + t * 1.4), (x + t, y + t * 1.4)],
               270: [(x, y), (x - t, y - t * 1.4), (x + t, y - t * 1.4)]}[rot]
        self.ax.add_patch(Polygon(pts, closed=True, fill=False, ec=K, lw=0.7))

    # primitives
    def line(self, x1, y1, x2, y2, lw=LW_THIN, ls='-', z=3):
        self.ax.add_line(Line2D([x1, x2], [y1, y2], lw=lw, ls=ls, color=K, zorder=z,
                                solid_capstyle='butt'))

    def text(self, x, y, s, fs=FS_DIM, ha='center', va='center', rot=0, bold=False, z=6, bg=True):
        kw = dict(fontsize=fs, ha=ha, va=va, rotation=rot, zorder=z, color=K,
                  weight='bold' if bold else 'normal')
        if bg:
            kw['bbox'] = dict(boxstyle='square,pad=0.08', fc='white', ec='none')
        self.ax.text(x, y, s, **kw)

    def arrow(self, x1, y1, x2, y2):
        self.ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=11,
                                          lw=LW_THIN, color=K, shrinkA=0, shrinkB=0, zorder=5))

    def hdim(self, xa, xb, y, y_feat_a, y_feat_b, label):
        """Horizontal dimension (arrows both ends, text in a break) with extension lines."""
        g = 0.06
        for x, yf in ((xa, y_feat_a), (xb, y_feat_b)):
            sg = 1 if y > yf else -1
            self.line(x, yf + g * sg, x, y + 0.08 * sg)
        xm = (xa + xb) / 2
        self.arrow(xm, y, xa, y); self.arrow(xm, y, xb, y)
        self.text(xm, y, label)

    def vdim(self, ya, yb, x, x_feat_a, x_feat_b, label):
        g = 0.06
        for y, xf in ((ya, x_feat_a), (yb, x_feat_b)):
            sg = 1 if x > xf else -1
            self.line(xf + g * sg, y, x + 0.08 * sg, y)
        ym = (ya + yb) / 2
        self.arrow(x, ym, x, ya); self.arrow(x, ym, x, yb)
        self.text(x, ym, label, rot=90)

    def hole(self, cx, cy, r, ext=0.18):
        self.ax.add_patch(Circle((cx, cy), r, fill=False, ec=K, lw=LW_OBJ, zorder=4))
        e = r + ext
        self.line(cx - e, cy, cx + e, cy, ls=CHAIN, lw=0.4)
        self.line(cx, cy - e, cx, cy + e, ls=CHAIN, lw=0.4)
        self.line(cx - 0.04, cy, cx + 0.04, cy, lw=0.5); self.line(cx, cy - 0.04, cx, cy + 0.04, lw=0.5)

    def callout(self, p_hole, r, ang, length, label, side='right'):
        a = math.radians(ang)
        px, py = p_hole[0] + r * math.cos(a), p_hole[1] + r * math.sin(a)
        ex, ey = px + length * math.cos(a), py + length * math.sin(a)
        self.ax.add_patch(FancyArrowPatch((ex, ey), (px, py), arrowstyle='-|>', mutation_scale=11,
                                          lw=LW_THIN, color=K, shrinkA=0, shrinkB=0, zorder=5))
        sh = 0.25 if side == 'right' else -0.25
        self.line(ex, ey, ex + sh, ey)
        self.text(ex + sh + (0.05 if side == 'right' else -0.05), ey, label,
                  ha='left' if side == 'right' else 'right', fs=FS_NOTE)

    def datum_point(self, x, y):
        self.ax.add_patch(Circle((x, y), 0.07, fc='white', ec=K, lw=0.8, zorder=7))
        self.ax.add_patch(Polygon([(x, y), (x + 0.07, y), (x, y + 0.07)], closed=True, fc=K, lw=0,
                                  zorder=8))
        self.ax.add_patch(Polygon([(x, y), (x - 0.07, y), (x, y - 0.07)], closed=True, fc=K, lw=0,
                                  zorder=8))

    def title_block(self, title2, scale, sheet, weight='0.914 lb'):
        x0, y0, w, h = 6.9, 0.4, 9.7, 2.65
        ax = self.ax
        ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=K, lw=1.0))
        xl = x0 + 3.2                                      # left column | right part
        self.line(xl, y0, xl, y0 + h, lw=0.8)
        rows = [y0 + 0.30, y0 + 0.60, y0 + 0.90]
        for yy in rows:
            self.line(x0, yy, x0 + w, yy, lw=0.8)
        self.line(xl, y0 + h - 0.85, x0 + w, y0 + h - 0.85, lw=0.8)
        # left: general notes
        self.text(x0 + 1.6, y0 + 2.05, 'ALL UNITS IN INCHES', fs=12, bg=False)
        self.text(x0 + 1.6, y0 + 1.78, 'ALL TOLERANCES ± 0.02', fs=12, bg=False)
        self.text(x0 + 1.6, y0 + 1.36, 'MATERIAL: 6061-T6 ALUMINUM', fs=10, bg=False)
        self.text(x0 + 1.6, y0 + 1.13, 'STOCK 1: AA I 3 × 2.03', fs=10, bg=False)
        for yy, lab, val in ((rows[2] - 0.15, 'APPROVED', ''), (rows[1] - 0.15, 'CHECKED', ''),
                             (rows[0] - 0.15, 'DRAWN', 'Ryan Bilock')):
            self.text(x0 + 0.08, yy, lab, fs=10, ha='left', bg=False)
            self.text(x0 + 1.15, yy, val, fs=10, ha='left', bg=False)
        # right: project / title
        self.text(xl + 0.06, y0 + h - 0.10, 'PROJECT', fs=8.5, ha='left', va='top', bg=False)
        self.text(xl + 0.06, y0 + h - 0.52, 'EMCH 308 Semester Project', fs=22, ha='left', bg=False)
        self.text(xl + 0.06, y0 + h - 0.95, 'TITLE', fs=8.5, ha='left', va='top', bg=False)
        self.text(xl + 0.06, y0 + h - 1.35, 'I-Beam, Stock 1, Rev C', fs=22, ha='left', bg=False)
        self.text(xl + 0.06, y0 + h - 1.68, title2, fs=11, ha='left', bg=False)
        # bottom rows
        c = [xl, xl + 0.45, xl + 1.75, xl + 4.75, x0 + w - 0.55]
        for xx in c[1:]:
            self.line(xx, rows[0], xx, rows[2], lw=0.8)
        self.line(xl + 1.6, y0, xl + 1.6, rows[0], lw=0.8)
        self.line(xl + 3.55, y0, xl + 3.55, rows[0], lw=0.8)
        for (xa, xb, lab, val) in ((c[0], c[1], 'SIZE', 'B'), (c[1], c[2], 'CODE', ''),
                                   (c[2], c[3], 'DWG NO', 'USC06_MTC06_IBeam_RevC'),
                                   (c[3], c[4], '', ''), (c[4], x0 + w, 'REV', 'C')):
            if lab:
                self.text((xa + xb) / 2, rows[2] - 0.11, lab, fs=8.5, bg=False)
                self.text((xa + xb) / 2, rows[1] - 0.15, val, fs=11, bg=False)
        self.text(xl + 0.06, y0 + 0.15, 'SCALE  ' + scale, fs=10, ha='left', bg=False)
        self.text(xl + 1.66, y0 + 0.15, 'WEIGHT  ' + weight, fs=10, ha='left', bg=False)
        self.text(xl + 3.61, y0 + 0.15, 'SHEET  ' + sheet, fs=10, ha='left', bg=False)


def ipoly(cx, by, s=1.0):
    yi, xf, yf = H - TF, TW / 2 + RF, H - TF - RF
    def arc(c, a0, a1, n=16):
        return [(c[0] + RF * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                 c[1] + RF * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    pts = ([(-BF / 2, H), (BF / 2, H), (BF / 2, yi), (xf, yi)] + arc((xf, yf), 90, 180)[1:] +
           [(TW / 2, TF + RF)] + arc((xf, TF + RF), 180, 270)[1:] +
           [(BF / 2, TF), (BF / 2, 0), (-BF / 2, 0), (-BF / 2, TF), (-xf, TF)] +
           arc((-xf, TF + RF), 270, 360)[1:] + [(-TW / 2, yf)] + arc((-xf, yf), 0, 90)[1:] +
           [(-BF / 2, yi)])
    return [(cx + s * x, by + s * y) for x, y in pts]




def arc_pts(c, a0, a1, n=14):
    return [(c[0] + RR * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             c[1] + RR * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def top_outline():
    """Kept top flange in (z, w): pad full width at TP, 1.20 wide elsewhere.
    Arcs are R.25 inside corners centred on the relief holes."""
    a, b = TP
    w1, w2 = ND, BF - ND
    p = [(0, w1), (a - RR, w1)] + arc_pts((a - RR, w1 - RR), 90, 0)[1:] + [(a, 0), (b, 0)]
    p += arc_pts((b + RR, w1 - RR), 180, 90)[1:] + [(L, w1), (L, w2), (b + RR, w2)]
    p += arc_pts((b + RR, w2 + RR), 270, 180)[1:] + [(b, BF), (a, BF)]
    p += arc_pts((a - RR, w2 + RR), 0, -90)[1:] + [(0, w2)]
    return p


def bottom_outline():
    a, b = BP
    w1, w2 = ND, BF - ND
    p = [(0, 0), (a, 0)] + arc_pts((a + RR, w1 - RR), 180, 90)[1:]
    p += [(b - RR, w1)] + arc_pts((b - RR, w1 - RR), 90, 0)[1:] + [(b, 0), (L, 0), (L, BF), (b, BF)]
    p += arc_pts((b - RR, w2 + RR), 0, -90)[1:] + [(a + RR, w2)]
    p += arc_pts((a + RR, w2 + RR), 270, 180)[1:] + [(a, BF), (0, BF)]
    return p


def notes_block(sh, lines, x=0.75, y=2.95):
    sh.text(x, y, 'NOTES', fs=11, ha='left', bold=True, bg=False)
    for i, t in enumerate(lines):
        sh.text(x, y - 0.32 - i * 0.27, t, fs=9.5, ha='left', bg=False)


NOTES = ['1.  STOCK 1, AA I 3 × 2.03, 6061-T6.  USE THE 8.40 RAW LENGTH AS SUPPLIED.',
         '2.  DRILL THE 8X Ø.50 RELIEF HOLES BEFORE ANY SAW CUT.',
         '3.  SAW EACH NOTCH TANGENT TO ITS RELIEF HOLE(S): ALL INSIDE',
         '     CORNERS R.25 (NO SHARP CORNERS).  CUT THE FLANGE ONLY.',
         '4.  Ø1.03 WEB HOLES: 1-1/32 DRILL, 4X.',
         '5.  BREAK ALL EDGES .02 MAX.  DEBURR ALL HOLES AND CUTS.',
         '6.  FULL-WIDTH PADS (NO CUTS) UNDER THE TEST ROLLERS:',
         '     TOP 3.45–4.95; BOTTOM 0–.70 AND 7.70–8.40.']

# =========================== SHEET 1: FRONT + END VIEW (1:1) ===========================
s1 = Sheet()
S = 1.0
X0, YT = 2.3, 7.25
P = lambda z, yb: (X0 + S * z, YT - S * (H - yb))
s1.ax.add_patch(Rectangle(P(0, 0), S * L, S * H, fill=False, ec=K, lw=LW_OBJ, zorder=3))
for yy in (TF, H - TF):
    s1.line(P(0, yy)[0], P(0, yy)[1], P(L, yy)[0], P(L, yy)[1], lw=LW_OBJ * 0.8)
# notch end faces seen in the flange bands
for z in TP:
    s1.line(P(z, H - TF)[0], P(z, H - TF)[1], P(z, H)[0], P(z, H)[1], lw=LW_OBJ * 0.8)
for z in BP:
    s1.line(P(z, 0)[0], P(z, 0)[1], P(z, TF)[0], P(z, TF)[1], lw=LW_OBJ * 0.8)
for z, yb in FIG1:
    s1.hole(*P(z, yb), S * DH / 2)
s1.line(P(0, H / 2)[0] - 0.3, P(0, H / 2)[1], P(L, H / 2)[0] + 0.3, P(0, H / 2)[1], ls=CHAIN, lw=0.4)
s1.line(P(ZM, 0)[0], P(0, 0)[1] - 0.3, P(ZM, 0)[0], P(0, H)[1] + 0.3, ls=CHAIN, lw=0.4)
s1.datum_point(*P(0, H))
xs = sorted({z for z, _ in FIG1}) + [L]
for i, z in enumerate(xs):
    yd = YT + 0.45 + i * 0.36
    yb_h = dict(FIG1).get(z)
    yf = YT if yb_h is None else P(z, yb_h)[1] + S * DH / 2
    s1.hdim(P(0, H)[0], P(z, H)[0], yd, YT, yf, fmt(z))
ys = [H - (H / 2 + 0.375), H - (H / 2 - 0.375), H]
for i, d in enumerate(ys):
    xd = X0 - 0.45 - i * 0.45
    s1.vdim(YT, YT - S * d, xd, X0, X0, fmt(d))
s1.callout(P(ZM - 1.0, H / 2 + 0.375), S * DH / 2, 145, 0.55, 'Ø1.03 THRU', side='left')
s1.callout(P(ZM + 1.0, H / 2 + 0.375), S * DH / 2, 35, 0.55, 'Ø1.03 THRU', side='right')
s1.callout(P(ZM - 3.0, H / 2 - 0.375), S * DH / 2, 215, 0.55, 'Ø1.03 THRU', side='left')
s1.callout(P(ZM + 3.0, H / 2 - 0.375), S * DH / 2, 325, 0.55, 'Ø1.03 THRU', side='right')
s1.callout(P(TP[1], H - TF / 2), 0.0, 20, 0.9, 'NOTCH ENDS, SEE SHEETS 2–3', side='right')
s1.text(P(ZM, 0)[0], P(0, 0)[1] - 0.70, 'FRONT VIEW', fs=FS_VIEW, bold=True, bg=False)
s1.text(P(ZM, 0)[0], P(0, 0)[1] - 0.95, 'SCALE 1:1', fs=10, bg=False)

ECX, EBY = 13.9, YT - H
s1.ax.add_patch(Polygon(ipoly(ECX, EBY), closed=True, fill=False, ec=K, lw=LW_OBJ, zorder=3))
for yb in (EBY + H - TF, EBY):               # notched flange width, phantom
    for sx in (-1, 1):
        xx = ECX + sx * (BF / 2 - ND)
        s1.line(xx, yb, xx, yb + TF, ls=PHANTOM, lw=0.5)
s1.line(ECX, EBY - 0.3, ECX, EBY + H + 0.3, ls=CHAIN, lw=0.4)
s1.datum_point(ECX - BF / 2, EBY + H)
s1.hdim(ECX - BF / 2, ECX + BF / 2, EBY + H + 0.45, EBY + H, EBY + H, '2.5')
s1.hdim(ECX - BF / 2 + ND, ECX + BF / 2 - ND, EBY - 0.40, EBY, EBY, '1.2')
s1.vdim(EBY + H, EBY, ECX + BF / 2 + 0.55, ECX + BF / 2, ECX + BF / 2, '3')
s1.vdim(EBY + H, EBY + H - TF, ECX - BF / 2 - 0.45, ECX - BF / 2, ECX - BF / 2, '')
s1.text(ECX - BF / 2 - 0.55, EBY + H - TF / 2, '.26', ha='right')
s1.callout((ECX + TW / 2, EBY + 2.0), 0.0, 25, 0.55, '.15 WEB', side='right')
s1.callout((ECX + TW / 2 + RF * 0.293, EBY + TF + RF * 0.293), 0.0, 40, 0.55, 'R.25 4X', side='right')
s1.text(ECX, EBY - 0.85, 'END VIEW (STOCK)', fs=FS_VIEW, bold=True, bg=False)
s1.text(ECX, EBY - 1.10, 'SCALE 1:1   ·   PHANTOM: NOTCHED WIDTH 1.2', fs=10, bg=False)
notes_block(s1, NOTES)
s1.title_block('Rev C  –  web holes and stock section', '1:1', '1/3')


# =========================== SHEETS 2-3: FLANGE VIEWS (1:1) ===========================
def flange_sheet(outline, zs_relief, zs_dims, label, title2, sheet, hidden_side, callouts):
    sh = Sheet()
    x0, yt = 3.55, 7.70
    T = lambda z, w: (x0 + z, yt - w)
    sh.ax.add_patch(Polygon([T(z, w) for z, w in outline], closed=True, fill=False,
                            ec=K, lw=LW_OBJ, zorder=3))
    # stock outline (phantom) where material is removed
    sh.ax.add_patch(Rectangle(T(0, BF), L, BF, fill=False, ec=K, lw=0.4, ls=PHANTOM, zorder=2))
    for ww in (BF / 2 - TW / 2, BF / 2 + TW / 2):
        sh.line(T(0, ww)[0], T(0, ww)[1], T(L, ww)[0], T(L, ww)[1], ls=HIDDEN, lw=0.5)
    sh.line(T(ZM, 0)[0], T(0, 0)[1] + 0.25, T(ZM, 0)[0], T(0, BF)[1] - 0.25, ls=CHAIN, lw=0.4)
    for z in zs_relief:
        for w in WR:
            cx, cy = T(z, w)
            sh.ax.add_patch(Circle((cx, cy), RR, fill=False, ec=K, lw=0.5, ls=PHANTOM, zorder=4))
            for d in ((-0.36, 0, 0.36, 0), (0, -0.36, 0, 0.36)):
                sh.line(cx + d[0], cy + d[1], cx + d[2], cy + d[3], ls=CHAIN, lw=0.35)
    sh.datum_point(*T(0, 0))
    sh.text(T(0, 0)[0] - 0.12, T(0, 0)[1] + 0.20, 'DATUM: STOCK CORNER', fs=8.5, ha='right', bg=False)
    for i, z in enumerate(list(zs_dims) + [L]):
        yd = yt + 0.40 + i * 0.36
        sh.hdim(T(0, 0)[0], T(z, 0)[0], yd, yt, yt, fmt(z))
    for i, w in enumerate((WR[0], ND, BF - ND, WR[1], BF)):
        xd = x0 - 0.45 - i * 0.45
        sh.vdim(yt, T(0, w)[1], xd, x0, x0, fmt(round(w, 3)))
    for (p, ang, length, txt, side) in callouts:
        sh.callout(T(*p), 0.0, ang, length, txt, side=side)
    sh.text(T(ZM, 0)[0], T(0, BF)[1] - 0.85, label, fs=FS_VIEW, bold=True, bg=False)
    sh.text(T(ZM, 0)[0], T(0, BF)[1] - 1.10,
            'SCALE 1:1   ·   PHANTOM: STOCK OUTLINE AND Ø.50 RELIEF DRILLS   ·   '
            'HIDDEN: WEB', fs=10, bg=False)
    notes_block(sh, NOTES)
    sh.title_block(title2, '1:1', sheet)
    return sh


a, b = TP
s2 = flange_sheet(top_outline(), (a - RR, b + RR), (a - RR, a, b, b + RR),
                  'TOP FLANGE  (VIEWED FROM ABOVE)', 'Rev C  –  top flange, load-roller pad',
                  '2/3', 'top',
                  [((a - RR - 0.18, WR[0] + 0.18), 150, 0.75, '4X Ø.50 RELIEF DRILL', 'left'),
                   ((a - RR + RR * 0.71, ND - RR + RR * 0.71), 60, 0.95, 'R.25 4X (FROM RELIEF DRILL)', 'right'),
                   ((1.6, BF - ND * 0.5), -115, 0.85, 'NOTCH .65 DEEP, 4X, RUNS OUT THE END', 'left'),
                   ((ZM, BF - 0.2), -60, 0.80, 'FULL-WIDTH PAD, NO CUTS (LOAD ROLLER)', 'right')])
a, b = BP
s3 = flange_sheet(bottom_outline(), (a + RR, b - RR), (a, a + RR, b - RR, b),
                  'BOTTOM FLANGE  (VIEWED FROM BELOW)', 'Rev C  –  bottom flange, support pads',
                  '3/3', 'bottom',
                  [((a + RR + 0.18, WR[0] + 0.18), 30, 0.75, '4X Ø.50 RELIEF DRILL', 'right'),
                   ((a + RR - RR * 0.71, BF - ND + RR - RR * 0.71), -150, 0.70, 'R.25 4X', 'left'),
                   ((ZM, ND * 0.5), 70, 0.75, 'NOTCH .65 DEEP, 2X', 'right'),
                   ((L - 0.35, BF - 0.2), -60, 0.80, 'FULL-WIDTH PADS, NO CUTS (SUPPORTS)', 'right')])

_here = os.path.dirname(os.path.abspath(__file__))
_cad = os.path.normpath(os.path.join(_here, '..', '..'))
out_dir = _cad if os.path.basename(_cad) == 'cad' else _here
out = os.path.join(out_dir, 'USC06_MTC06_IBeam_RevC_Drawing')
with PdfPages(out + '.pdf') as pdf:
    for s in (s1, s2, s3):
        pdf.savefig(s.fig)
for k, s in enumerate((s1, s2, s3), 1):
    s.fig.savefig(out + '_sheet%d.png' % k, dpi=110)
print('saved', out)
