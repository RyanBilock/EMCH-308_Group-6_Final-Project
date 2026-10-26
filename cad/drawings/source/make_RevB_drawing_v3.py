"""USC06_MTC06_IBeam_RevB_Drawing (v3) -- styled after the course example 'I-Beam Blank':
thin lines, arrowed dimension lines, long dash-dot centerlines, leader callouts, large text,
EMCH 308 title block.  All dimensions are baseline dimensions from the top-left corner
(datum point) of each view.  Two B-size sheets (17 x 11)."""
import math
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

L, H, BF, TF, TW, RF = 8.20, 3.00, 2.50, 0.26, 0.15, 0.25
D, HX = 0.78125, 0.7875
ZM = L / 2
TOP = sorted(ZM + s * z for z in (1.30, 2.18, 3.06) for s in (-1, 1))
BOT = sorted(ZM + s * z for z in (0.44, 1.32, 2.20, 3.08) for s in (-1, 1))
FIG1 = [(ZM - 3.0, H / 2 - 0.375), (ZM - 1.0, H / 2 + 0.375), (ZM + 1.0, H / 2 + 0.375),
        (ZM + 3.0, H / 2 - 0.375)]                    # (from left end, from bottom)


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

    def title_block(self, title2, scale, sheet, weight='0.993 lb'):
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
        self.text(xl + 0.06, y0 + h - 1.35, 'I-Beam, Stock 1, Drilled', fs=22, ha='left', bg=False)
        self.text(xl + 0.06, y0 + h - 1.68, title2, fs=11, ha='left', bg=False)
        # bottom rows
        c = [xl, xl + 0.45, xl + 1.75, xl + 4.75, x0 + w - 0.55]
        for xx in c[1:]:
            self.line(xx, rows[0], xx, rows[2], lw=0.8)
        self.line(xl + 1.6, y0, xl + 1.6, rows[0], lw=0.8)
        self.line(xl + 3.55, y0, xl + 3.55, rows[0], lw=0.8)
        for (xa, xb, lab, val) in ((c[0], c[1], 'SIZE', 'B'), (c[1], c[2], 'CODE', ''),
                                   (c[2], c[3], 'DWG NO', 'USC06_MTC06_IBeam_RevB'),
                                   (c[3], c[4], '', ''), (c[4], x0 + w, 'REV', 'B')):
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


# =========================== SHEET 1: FRONT + END VIEW (1:1) ===========================
s1 = Sheet()
S = 1.0
X0, YT = 2.3, 7.25                     # paper: top-left corner (datum point) of the front view
P = lambda z, yb: (X0 + S * z, YT - S * (H - yb))       # yb measured from the bottom
s1.ax.add_patch(Rectangle(P(0, 0), S * L, S * H, fill=False, ec=K, lw=LW_OBJ, zorder=3))
for yy in (TF, H - TF):
    s1.line(P(0, yy)[0], P(0, yy)[1], P(L, yy)[0], P(L, yy)[1], lw=LW_OBJ * 0.8)
for z, yb in FIG1:
    s1.hole(*P(z, yb), S * 0.5)
s1.line(P(0, H / 2)[0] - 0.3, P(0, H / 2)[1], P(L, H / 2)[0] + 0.3, P(0, H / 2)[1], ls=CHAIN, lw=0.4)
s1.line(P(ZM, 0)[0], P(0, 0)[1] - 0.3, P(ZM, 0)[0], P(0, H)[1] + 0.3, ls=CHAIN, lw=0.4)
s1.datum_point(*P(0, H))
# horizontal baseline dimensions from the left end, stacked above
xs = sorted({z for z, _ in FIG1}) + [L]
for i, z in enumerate(xs):
    yd = YT + 0.45 + i * 0.36
    yb_h = dict(FIG1).get(z)
    yf = YT if yb_h is None else P(z, yb_h)[1] + S * 0.5
    s1.hdim(P(0, H)[0], P(z, H)[0], yd, YT, yf, fmt(z))
# vertical baseline dimensions from the top edge, stacked left
ys = [H - (H / 2 + 0.375), H - (H / 2 - 0.375), H]       # 1.125, 1.875, 3
for i, d in enumerate(ys):
    xd = X0 - 0.45 - i * 0.45
    s1.vdim(YT, YT - S * d, xd, X0, X0, fmt(d))
# callouts
s1.callout(P(ZM - 1.0, H / 2 + 0.375), S * 0.5, 145, 0.55, 'Ø1 THRU', side='left')
s1.callout(P(ZM + 1.0, H / 2 + 0.375), S * 0.5, 35, 0.55, 'Ø1 THRU', side='right')
s1.callout(P(ZM - 3.0, H / 2 - 0.375), S * 0.5, 215, 0.55, 'Ø1 THRU', side='left')
s1.callout(P(ZM + 3.0, H / 2 - 0.375), S * 0.5, 325, 0.55, 'Ø1 THRU', side='right')
s1.text(P(ZM, 0)[0], P(0, 0)[1] - 0.70, 'FRONT VIEW', fs=FS_VIEW, bold=True, bg=False)
s1.text(P(ZM, 0)[0], P(0, 0)[1] - 0.95, 'SCALE 1:1', fs=10, bg=False)

# end view at 1:1, to the right
ECX, EBY = 13.6, YT - H
s1.ax.add_patch(Polygon(ipoly(ECX, EBY), closed=True, fill=False, ec=K, lw=LW_OBJ, zorder=3))
s1.line(ECX, EBY - 0.3, ECX, EBY + H + 0.3, ls=CHAIN, lw=0.4)
s1.datum_point(ECX - BF / 2, EBY + H)
s1.hdim(ECX - BF / 2, ECX + BF / 2, EBY + H + 0.45, EBY + H, EBY + H, '2.5')
s1.vdim(EBY + H, EBY, ECX + BF / 2 + 0.55, ECX + BF / 2, ECX + BF / 2, '3')
s1.vdim(EBY + H, EBY + H - TF, ECX - BF / 2 - 0.45, ECX - BF / 2, ECX - BF / 2, '')
s1.text(ECX - BF / 2 - 0.55, EBY + H - TF / 2, '.26', ha='right')
s1.callout((ECX + TW / 2, EBY + 2.0), 0.0, 25, 0.55, '.15 WEB', side='right')
s1.callout((ECX + TW / 2 + RF * 0.293, EBY + TF + RF * 0.293), 0.0, 40, 0.55, 'R.25 4X', side='right')
s1.text(ECX, EBY - 0.70, 'END VIEW (STOCK)', fs=FS_VIEW, bold=True, bg=False)
s1.text(ECX, EBY - 0.95, 'SCALE 1:1', fs=10, bg=False)

# notes (left of title block)
notes = ['NOTES:', '1. ALL DIMENSIONS FROM THE DATUM POINT AT THE TOP-LEFT CORNER.',
         '2. SAW TO LENGTH 8.2. NO MILLING.', '3. DEBURR ALL HOLES.',
         '4. FLANGE HOLES: SEE SHEET 2.']
for i, n in enumerate(notes):
    s1.text(0.75, 2.75 - i * 0.30, n, fs=11, ha='left', bold=(i == 0), bg=False)
s1.title_block('Rev B  –  web holes and stock section', '1:1', '1/2')

# =========================== SHEET 2: TOP + BOTTOM FLANGE VIEWS (3:4) ===========================
s2 = Sheet()
S = 0.75


def flange_view(sh, x0, yt, zs, label, n):
    T = lambda z, w: (x0 + S * z, yt - S * w)          # w measured down from the top edge
    sh.ax.add_patch(Rectangle(T(0, BF), S * L, S * BF, fill=False, ec=K, lw=LW_OBJ, zorder=3))
    for xx in (BF / 2 - TW / 2, BF / 2 + TW / 2):
        sh.line(T(0, xx)[0], T(0, xx)[1], T(L, xx)[0], T(L, xx)[1], ls=(0, (5, 3)), lw=0.5)
    rows = (BF / 2 - HX, BF / 2 + HX)                   # .4625 and 2.0375 from the top edge
    for z in zs:
        for w in rows:
            sh.hole(*T(z, w), S * D / 2, ext=0.12)
    for w in rows:
        sh.line(T(0, w)[0] - 0.25, T(0, w)[1], T(L, w)[0] + 0.25, T(0, w)[1], ls=CHAIN, lw=0.4)
    sh.datum_point(*T(0, 0))
    for i, z in enumerate(list(zs) + [L]):
        yd = yt + 0.40 + i * 0.33
        yf = yt if z == L else T(z, rows[0])[1] + S * D / 2
        sh.hdim(T(0, 0)[0], T(z, 0)[0], yd, yt, yf, fmt(z))
    for i, w in enumerate(list(rows) + [BF]):
        xd = x0 - 0.42 - i * 0.45
        sh.vdim(yt, T(0, w)[1], xd, x0, x0, fmt(round(w, 3)))
    sh.callout(T(zs[1], rows[1]), S * D / 2, -55, 0.42,
               '%dX \u00d8.781 (25/32) THRU' % n, side='right')
    sh.text(T(L / 2, 0)[0], T(0, BF)[1] - 1.00, label + ' FLANGE  (VIEWED FROM %s)'
            % ('ABOVE' if label.startswith('TOP') else 'BELOW'), fs=FS_VIEW, bold=True, bg=False)
    sh.text(T(L / 2, 0)[0], T(0, BF)[1] - 1.25, 'SCALE 3:4', fs=10, bg=False)


flange_view(s2, 1.95, 6.70, TOP, 'TOP', 12)
flange_view(s2, 10.0, 6.70, BOT, 'BOTTOM', 16)
notes2 = ['NOTES:', '1. DRILL FLANGE HOLES THROUGH ONE FLANGE ONLY.',
          '2. DO NOT CUT INTO THE WEB OR FILLETS.', '3. HOLE ROWS .4625 FROM EACH',
          '    FLANGE EDGE (1.575 APART).']
for i, n in enumerate(notes2):
    s2.text(0.75, 2.75 - i * 0.30, n, fs=11, ha='left', bold=(i == 0), bg=False)
s2.title_block('Rev B  –  28 flange holes', '3:4', '2/2')

out = '/home/claude/dwg/v3/USC06_MTC06_IBeam_RevB_Drawing'
with PdfPages(out + '.pdf') as pdf:
    pdf.savefig(s1.fig); pdf.savefig(s2.fig)
s1.fig.savefig(out + '_sheet1.png', dpi=110); s2.fig.savefig(out + '_sheet2.png', dpi=110)
print('saved')
