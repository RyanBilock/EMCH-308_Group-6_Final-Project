"""USC06_MTC06_IBeam_RevB_Drawing  --  manufacturing drawing in the MTC format
(third-angle projection, ASME Y14.5, inches, B-size 17 x 11)."""
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Ellipse, FancyArrowPatch
from matplotlib.lines import Line2D

plt.rcParams.update({'font.family': ['Liberation Sans', 'DejaVu Sans'], 'font.size': 7,
                     'hatch.linewidth': 0.35, 'hatch.color': 'black'})
K = 'black'
LW_VIS, LW_THIN, LW_BORDER = 1.0, 0.35, 1.4
FS, FS_DIM, FS_SM = 7.5, 7.0, 6.0

# ---------------- part ----------------
L, H, BF, TF, TW, RF = 8.20, 3.00, 2.50, 0.26, 0.15, 0.25
D, HX = 0.78125, 0.7875
ZM = L / 2
TOP = [ZM + s * z for z in (1.30, 2.18, 3.06) for s in (-1, 1)]
BOT = [ZM + s * z for z in (0.44, 1.32, 2.20, 3.08) for s in (-1, 1)]
TOP.sort(); BOT.sort()
FIG1 = [(ZM - 3.0, H / 2 - 0.375), (ZM - 1.0, H / 2 + 0.375), (ZM + 1.0, H / 2 + 0.375),
        (ZM + 3.0, H / 2 - 0.375)]          # (from end B, from bottom A)
S = 0.75                                      # scale 3:4

fig = plt.figure(figsize=(17, 11), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 17); ax.set_ylim(0, 11); ax.axis('off')
ax.set_aspect('equal')


def line(x1, y1, x2, y2, lw=LW_THIN, ls='-', z=3, c=K):
    ax.add_line(Line2D([x1, x2], [y1, y2], lw=lw, ls=ls, color=c, zorder=z, solid_capstyle='butt'))


def rect(x, y, w, h, lw=LW_VIS, fc='none', z=3, hatch=None):
    ax.add_patch(Rectangle((x, y), w, h, lw=lw, ec=K, fc=fc, zorder=z, hatch=hatch))


def text(x, y, s, fs=FS, ha='center', va='center', rot=0, bold=False, box=False, z=6, fam=None):
    kw = dict(fontsize=fs, ha=ha, va=va, rotation=rot, zorder=z, color=K,
              weight='bold' if bold else 'normal')
    if fam: kw['family'] = fam
    if box:
        kw['bbox'] = dict(boxstyle='square,pad=0.18', fc='white', ec=K, lw=0.5)
    else:
        kw['bbox'] = dict(boxstyle='square,pad=0.05', fc='white', ec='none')
    return ax.text(x, y, s, **kw)


CHAIN = (0, (12, 3, 2, 3))
HIDDEN = (0, (4, 2))


def arrow(x1, y1, x2, y2):            # arrowhead at (x2, y2)
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=7,
                                 lw=LW_THIN, color=K, shrinkA=0, shrinkB=0, zorder=5))


def dim_lin(p1, p2, off, label, horiz=True, fs=FS_DIM, box=False, ext=True, tpos=0.5):
    """Linear dimension between paper points p1, p2; 'off' = signed offset of the dim line."""
    if horiz:
        y = off
        if ext:
            for (x, yy) in (p1, p2):
                line(x, yy + (0.04 if y > yy else -0.04), x, y + (0.06 if y > yy else -0.06))
        xm = p1[0] + (p2[0] - p1[0]) * tpos
        arrow(xm, y, p1[0], y); arrow(xm, y, p2[0], y)
        text(xm, y, label, fs=fs, box=box)
    else:
        x = off
        if ext:
            for (xx, y) in (p1, p2):
                line(xx + (0.04 if x > xx else -0.04), y, x + (0.06 if x > xx else -0.06), y)
        ym = p1[1] + (p2[1] - p1[1]) * tpos
        arrow(x, ym, x, p1[1]); arrow(x, ym, x, p2[1])
        text(x, ym, label, fs=fs, rot=90, box=box)


def ordinate_h(xs_labels, y_feat, y_text, zero_x, basic=True, up=True):
    """Horizontal ordinate dims: extension lines from features up/down to y_text."""
    sgn = 1 if up else -1
    allp = [(zero_x, '0.000', False)] + [(x, l, basic) for x, l in xs_labels]
    for x, lab, b in allp:
        line(x, y_feat + 0.05 * sgn, x, y_text - 0.03 * sgn)
        text(x, y_text + 0.20 * sgn, lab, fs=FS_DIM, rot=90, box=b,
             va='center')


def ordinate_v(ys_labels, x_feat, x_text, zero_y, basic=True, left=True):
    sgn = -1 if left else 1
    allp = [(zero_y, '0.000', False)] + [(y, l, basic) for y, l in ys_labels]
    for y, lab, b in allp:
        line(x_feat + 0.05 * sgn, y, x_text - 0.03 * sgn, y)
        text(x_text + 0.24 * sgn, y, lab, fs=FS_DIM, box=b)


def datum(x, y, letter, direction='down', length=0.28):
    """Datum feature symbol: filled triangle on the feature at (x, y), leader, boxed letter."""
    dx, dy = {'down': (0, -1), 'up': (0, 1), 'left': (-1, 0), 'right': (1, 0)}[direction]
    t = 0.07
    if dy:
        tri = [(x - t, y), (x + t, y), (x, y + dy * t * 1.4)]
    else:
        tri = [(x, y - t), (x, y + t), (x + dx * t * 1.4, y)]
    ax.add_patch(Polygon(tri, closed=True, fc=K, ec=K, lw=0.4, zorder=6))
    x2, y2 = x + dx * length, y + dy * length
    line(x, y, x2, y2, lw=0.5, z=6)
    bs = 0.20
    bx, by = x2 + dx * bs / 2, y2 + dy * bs / 2
    ax.add_patch(Rectangle((bx - bs / 2, by - bs / 2), bs, bs, fc='white', ec=K, lw=0.6, zorder=6))
    text(bx, by, letter, fs=8, bold=True, z=7)


def fcf(x, y, cells, h=0.20):
    """Feature control frame, left edge at x, vertical centre y. cells = list of (text, width)."""
    cx = x
    for t, w in cells:
        ax.add_patch(Rectangle((cx, y - h / 2), w, h, fc='white', ec=K, lw=0.6, zorder=6))
        if t == '\u2316':
            pcx = cx + w / 2
            ax.add_patch(Circle((pcx, y), 0.052, fc='white', ec=K, lw=0.6, zorder=7))
            line(pcx - 0.078, y, pcx + 0.078, y, lw=0.6, z=8); line(pcx, y - 0.078, pcx, y + 0.078, lw=0.6, z=8)
        elif '\u24C2' in t:
            base = t.replace('\u24C2', '').strip()
            text(cx + w * 0.40, y, base, fs=7.2, z=7)
            mx = cx + w * 0.80
            ax.add_patch(Circle((mx, y), 0.068, fc='white', ec=K, lw=0.6, zorder=7))
            ax.text(mx, y - 0.002, 'M', fontsize=5.6, ha='center', va='center', zorder=8, color=K)
        else:
            text(cx + w / 2, y, t, fs=7.2, z=7)
        cx += w
    return cx


POS = [('⌖', 0.22), ('⌀.040 Ⓜ', 0.62), ('A', 0.2), ('B', 0.2), ('C', 0.2)]


def leader(p_from, p_to, z=5):
    ax.add_patch(FancyArrowPatch(p_to, p_from, arrowstyle='-|>', mutation_scale=7, lw=0.45,
                                 color=K, shrinkA=0, shrinkB=0, zorder=z))


def centermark(x, y, r):
    e = r + 0.07
    line(x - e, y, x + e, y, ls=CHAIN, lw=0.3); line(x, y - e, x, y + e, ls=CHAIN, lw=0.3)


# ======================= BORDER, ZONES =======================
rect(0.25, 0.25, 16.5, 10.5, lw=LW_BORDER)
rect(0.5, 0.5, 16.0, 10.0, lw=LW_BORDER)
for i in range(1, 6):
    x = 0.5 + 16.0 * i / 6
    for y0, y1 in ((0.25, 0.5), (10.5, 10.75)):
        line(x, y0, x, y1, lw=0.6)
for i in range(6):
    xc = 0.5 + 16.0 * (i + 0.5) / 6
    for yc in (0.375, 10.625):
        text(xc, yc, str(6 - i), fs=8, bold=True)
for j in range(1, 5):
    y = 0.5 + 10.0 * j / 5
    for x0, x1 in ((0.25, 0.5), (16.5, 16.75)):
        line(x0, y, x1, y, lw=0.6)
for j, letter in enumerate('ABCDE'):
    yc = 0.5 + 10.0 * (j + 0.5) / 5
    for xc in (0.375, 16.625):
        text(xc, yc, letter, fs=8, bold=True)


def origin(x, y, sx=1, sy=1):
    """MTC-style X/Y datum origin marker at a view's lower-left corner."""
    ax.add_patch(Circle((x, y), 0.055, fc='white', ec=K, lw=0.7, zorder=7))
    ax.add_patch(Polygon([(x, y), (x + 0.055, y), (x, y + 0.055)], closed=True, fc=K, ec=K, lw=0, zorder=8))


def ord_x(xs, y_edge, y_line, x0, up=True):
    """Ordinate dims along X: '0.000' at x0, then each value; text vertical."""
    sg = 1 if up else -1
    for x, lab in [(x0, '0.000')] + xs:
        line(x, y_edge + 0.06 * sg, x, y_line, lw=LW_THIN)
        text(x, y_line + 0.24 * sg, lab, fs=7.2, rot=90)


def ord_y(ys, x_edge, x_line, y0):
    for y, lab in [(y0, '0.000')] + ys:
        line(x_edge - 0.06, y, x_line, y, lw=LW_THIN)
        text(x_line - 0.26, y, lab, fs=7.2)


def note_leader(p, q, lines_):
    leader(p, q)
    for i, t in enumerate(lines_):
        text(q[0] + 0.04, q[1] - i * 0.17, t, fs=7.4, ha='left')


def holes(cx_list, r):
    for cx, cy in cx_list:
        ax.add_patch(Circle((cx, cy), r, fc='white', ec=K, lw=LW_VIS, zorder=4))
        centermark(cx, cy, r)


f3 = lambda v: '%.3f' % v
Y1, Y2 = BF / 2 - HX, BF / 2 + HX          # hole rows from the flange edge: 0.4625, 2.0375

# ---------------- TOP VIEW ----------------
TX0, TY0 = 1.75, 7.55
T = lambda z, x: (TX0 + S * z, TY0 + S * x)        # x measured from the near flange edge
rect(*T(0, 0), S * L, S * BF)
holes([T(z, y) for z in TOP for y in (Y1, Y2)], S * D / 2)
ord_x([(T(z, 0)[0], f3(z)) for z in TOP] + [(T(L, 0)[0], f3(L))], T(0, BF)[1], T(0, BF)[1] + 0.32, T(0, 0)[0])
ord_y([(T(0, y)[1], f3(round(y, 3))) for y in (Y1, Y2, BF)], T(0, 0)[0], T(0, 0)[0] - 0.30, T(0, 0)[1])
origin(*T(0, 0))
hx, hy = T(TOP[-1], Y2)
note_leader((hx + S * D / 2 * 0.7, hy + S * D / 2 * 0.7), (T(L, BF)[0] + 0.35, T(L, BF)[1] + 0.05),
            ['⌀0.781 (25/32) THRU', '12 PLACES', 'TOP FLANGE'])
text(T(L / 2, 0)[0], T(0, 0)[1] - 0.22, 'TOP VIEW', fs=9, bold=True)

# ---------------- FRONT VIEW ----------------
FX0, FY0 = 1.75, 4.05
P = lambda z, y: (FX0 + S * z, FY0 + S * y)
rect(*P(0, 0), S * L, S * H)
for yy in (TF, H - TF):
    line(P(0, yy)[0], P(0, yy)[1], P(L, yy)[0], P(L, yy)[1], lw=LW_VIS * 0.8)
holes([P(z, y) for z, y in FIG1], S * 0.5)
ord_x([(P(z, 0)[0], f3(z)) for z, _ in sorted(FIG1)] + [(P(L, 0)[0], f3(L))], P(0, H)[1], P(0, H)[1] + 0.32, P(0, 0)[0])
ord_y([(P(0, y)[1], f3(y)) for y in (H / 2 - 0.375, H / 2 + 0.375, H)], P(0, 0)[0], P(0, 0)[0] - 0.30, P(0, 0)[1])
origin(*P(0, 0))
hx, hy = P(ZM + 3.0, H / 2 - 0.375)
note_leader((hx + S * 0.5 * 0.7, hy - S * 0.5 * 0.7), (P(L, 0)[0] + 0.35, P(L, 0)[1] - 0.05),
            ['⌀1.000 THRU WEB', '4 PLACES'])
text(P(L / 2, 0)[0], P(0, 0)[1] - 0.22, 'FRONT VIEW', fs=9, bold=True)

# ---------------- BOTTOM VIEW ----------------
BX0, BY0 = 1.75, 0.95
B_ = lambda z, x: (BX0 + S * z, BY0 + S * x)
rect(*B_(0, 0), S * L, S * BF)
holes([B_(z, y) for z in BOT for y in (Y1, Y2)], S * D / 2)
ord_x([(B_(z, 0)[0], f3(z)) for z in BOT] + [(B_(L, 0)[0], f3(L))], B_(0, BF)[1], B_(0, BF)[1] + 0.32, B_(0, 0)[0])
ord_y([(B_(0, y)[1], f3(round(y, 3))) for y in (Y1, Y2, BF)], B_(0, 0)[0], B_(0, 0)[0] - 0.30, B_(0, 0)[1])
origin(*B_(0, 0))
hx, hy = B_(BOT[-1], Y1)
note_leader((hx + S * D / 2 * 0.7, hy - S * D / 2 * 0.7), (B_(L, 0)[0] + 0.35, B_(L, 0)[1] + 0.30),
            ['⌀0.781 (25/32) THRU', '16 PLACES', 'BOTTOM FLANGE'])
text(B_(L / 2, 0)[0], B_(0, 0)[1] - 0.22, 'BOTTOM VIEW', fs=9, bold=True)

# ---------------- END VIEW (stock section, reference) ----------------
EXc, EY0 = 10.6, 4.05
Q = lambda x, y: (EXc + S * x, EY0 + S * y)


def ipoly():
    yi, xf, yf = H - TF, TW / 2 + RF, H - TF - RF
    def arc(c, a0, a1, n=14):
        return [(c[0] + RF * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                 c[1] + RF * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    pts = ([(-BF / 2, H), (BF / 2, H), (BF / 2, yi), (xf, yi)] + arc((xf, yf), 90, 180)[1:] +
           [(TW / 2, TF + RF)] + arc((xf, TF + RF), 180, 270)[1:] +
           [(BF / 2, TF), (BF / 2, 0), (-BF / 2, 0), (-BF / 2, TF), (-xf, TF)] +
           arc((-xf, TF + RF), 270, 360)[1:] + [(-TW / 2, yf)] + arc((-xf, yf), 0, 90)[1:] +
           [(-BF / 2, yi)])
    return [Q(*p) for p in pts]


ax.add_patch(Polygon(ipoly(), closed=True, fc='white', ec=K, lw=LW_VIS, zorder=3))
dim_lin(Q(-BF / 2, H), Q(BF / 2, H), Q(0, H)[1] + 0.35, '2.500', horiz=True)
dim_lin(Q(BF / 2, 0), Q(BF / 2, H), Q(BF / 2, 0)[0] + 0.40, '3.000', horiz=False)
dim_lin(Q(-BF / 2, H - TF), Q(-BF / 2, H), Q(-BF / 2, 0)[0] - 0.25, '', horiz=False)
text(Q(-BF / 2, 0)[0] - 0.32, Q(0, H - TF / 2)[1], '0.260', fs=7.2, ha='right')
wx = Q(TW / 2, H / 2)
leader((wx[0], wx[1]), (wx[0] + 0.55, wx[1] + 0.25))
text(wx[0] + 0.58, wx[1] + 0.25, '0.150', fs=7.2, ha='left')
fx_ = Q(TW / 2 + RF * 0.293, TF + RF * 0.293)
leader(fx_, (fx_[0] + 0.55, fx_[1] + 0.30))
text(fx_[0] + 0.58, fx_[1] + 0.30, 'R0.250 4 PLACES', fs=7.2, ha='left')
text(Q(0, 0)[0], Q(0, 0)[1] - 0.22, 'END VIEW (STOCK)', fs=9, bold=True)

# ---------------- NOTES ----------------
NX, NY = 11.55, 8.95
notes = ['NOTES:',
         '1. MATERIAL: 6061-T6 ALUMINUM, STOCK 1 (AA I 3 X 2.03).',
         '2. END VIEW DIMENSIONS ARE AS-EXTRUDED STOCK.',
         '3. DRILL FLANGE HOLES THROUGH ONE FLANGE ONLY.',
         '4. DEBURR ALL HOLES.',
         '5. X/Y DATUM (0.000, 0.000) IS THE LOWER-LEFT CORNER OF EACH VIEW.']
for i, n in enumerate(notes):
    text(NX, NY - i * 0.20, n, fs=7.6 if i else 8.5, ha='left', bold=(i == 0))
# ======================= REVISION BLOCK =======================
RX, RY, RW = 11.0, 9.50, 5.5
rect(RX, RY, RW, 1.0, lw=0.8)
for yy in (RY + 0.25, RY + 0.5, RY + 0.75):
    line(RX, yy, RX + RW, yy, lw=0.6)
for xx in (RX + 0.45, RX + 4.55):
    line(xx, RY, xx, RY + 0.75, lw=0.6)
text(RX + RW / 2, RY + 0.875, 'REVISIONS', fs=8, bold=True)
text(RX + 0.225, RY + 0.625, 'REV', fs=6.5, bold=True)
text(RX + 2.5, RY + 0.625, 'DESCRIPTION', fs=6.5, bold=True)
text(RX + 5.025, RY + 0.625, 'DATE', fs=6.5, bold=True)
text(RX + 0.225, RY + 0.375, 'A', fs=7.5, bold=True)
text(RX + 0.55, RY + 0.375, 'NEW RELEASE (STOCK 3 DESIGN)', fs=6.0, ha='left')
text(RX + 5.025, RY + 0.375, '—', fs=6.5)
text(RX + 0.225, RY + 0.125, 'B', fs=7.5, bold=True)
text(RX + 0.55, RY + 0.125, 'STOCK 3 → STOCK 1; ADDED 28X ⌀.781 FLANGE HOLES', fs=6.0, ha='left')
text(RX + 5.025, RY + 0.125, '10/26/26', fs=6.5)

# ======================= TITLE BLOCK (MTC format) =======================
TX, TY, TWD, THT = 9.6, 0.5, 6.9, 2.35
rect(TX, TY, TWD, THT, lw=1.0)
# left column: tolerance block
lx = TX + 2.55
line(lx, TY, lx, TY + THT, lw=0.8)
tol = ['UNLESS OTHERWISE SPECIFIED', 'DIMENSIONS ARE IN INCHES.', 'INTERPRET DIMENSIONS AND',
       'TOLERANCES PER ASME Y14.5M-1984.', '', 'TOLERANCES:', 'FRACTIONS:  ± 1/64',
       'ANGLES:  ± 1 DEGREE', 'DECIMALS:  .X ± .020    .XX ± .010', '                  .XXX ± .005   .XXXX ± .0005']
for i, t in enumerate(tol):
    text(TX + 0.08, TY + THT - 0.16 - i * 0.205, t, fs=6.6, ha='left', bold=(i in (0, 5)))
# right part rows
rows = [TY + THT - 0.55, TY + THT - 1.05, TY + THT - 1.55]
for yy in rows:
    line(lx, yy, TX + TWD, yy, lw=0.8)
text((lx + TX + TWD) / 2, TY + THT - 0.20, 'MIDLANDS TECHNICAL COLLEGE', fs=11, bold=True)
text((lx + TX + TWD) / 2, TY + THT - 0.42, 'USC TEAM 6  /  MTC TEAM 6', fs=7)
text(lx + 0.06, rows[0] - 0.12, 'TITLE:', fs=6, ha='left', bold=True)
text((lx + TX + TWD) / 2, rows[0] - 0.24, 'MTC AND USC I BEAM PROJECT', fs=10, bold=True)
text((lx + TX + TWD) / 2, rows[0] - 0.41, 'I-BEAM, STOCK 1, DRILLED (FINAL DESIGN)', fs=7.5)
# row 3: dwg no / rev / scale / size / sheet
c1, c2, c3, c4 = lx + 2.05, lx + 2.65, lx + 3.35, lx + 3.8
for xx in (c1, c2, c3, c4):
    line(xx, rows[2], xx, rows[1], lw=0.6)
for (xa, xb, lab, val, fsv) in ((lx, c1, 'DWG NO.', 'USC06_MTC06_IBeam_RevB', 7.2), (c1, c2, 'REV', 'B', 11),
                                (c2, c3, 'SCALE', '3:4', 8.5), (c3, c4, 'SIZE', 'B', 8.5),
                                (c4, TX + TWD, 'SHEET', '1 OF 1', 7.5)):
    text(xa + 0.05, rows[1] - 0.10, lab, fs=5.6, ha='left', bold=True)
    text((xa + xb) / 2, rows[1] - 0.32, val, fs=fsv, bold=(lab in ('REV', 'DWG NO.')))
# row 4: people/dates + material / heat treatment
names = [('DESIGNER:', 'USC TEAM 6'), ('DRAWN BY:', 'R. BILOCK'), ('DWG CHK BY:', ''), ('DWG APP BY:', '')]
cw = (TX + TWD - lx)
q1, q2 = lx + cw * 0.36, lx + cw * 0.56
line(q1, TY, q1, rows[2], lw=0.6); line(q2, TY, q2, rows[2], lw=0.6)
for i, (k, v) in enumerate(names):
    yy = rows[2] - 0.10 - i * 0.205
    text(lx + 0.05, yy, k, fs=5.8, ha='left', bold=True)
    text(lx + 0.80, yy, v, fs=6.6, ha='left')
    text(q1 + 0.05, yy, 'DATE:', fs=5.8, ha='left', bold=True)
    text(q1 + 0.43, yy, '10/26/26' if v else '', fs=6.6, ha='left')
text(q2 + 0.05, rows[2] - 0.10, 'MATERIAL:', fs=5.8, ha='left', bold=True)
text(q2 + 0.05, rows[2] - 0.30, '6061-T6 ALUMINUM', fs=7, ha='left')
text(q2 + 0.05, rows[2] - 0.50, 'HEAT TREATMENT:', fs=5.8, ha='left', bold=True)
text(q2 + 0.05, rows[2] - 0.70, 'T6 (AS SUPPLIED)', fs=7, ha='left')
# third-angle projection symbol + note above title block
sx_, sy_ = TX + 3.55, TY + THT + 0.30
text(sx_ + 1.45, sy_, 'THIRD ANGLE PROJECTION', fs=6.4, ha='left', bold=True)
ax.add_patch(Polygon([(sx_, sy_ - 0.10), (sx_, sy_ + 0.10), (sx_ + 0.42, sy_ + 0.16),
                      (sx_ + 0.42, sy_ - 0.16)], closed=True, fc='none', ec=K, lw=0.6, zorder=5))
line(sx_ - 0.05, sy_, sx_ + 0.47, sy_, ls=CHAIN, lw=0.3)
ax.add_patch(Circle((sx_ + 0.95, sy_), 0.16, fc='none', ec=K, lw=0.6, zorder=5))
ax.add_patch(Circle((sx_ + 0.95, sy_), 0.10, fc='none', ec=K, lw=0.6, zorder=5))
line(sx_ + 0.70, sy_, sx_ + 1.20, sy_, ls=CHAIN, lw=0.3)

out = '/home/claude/dwg/v2/USC06_MTC06_IBeam_RevB_Drawing'
fig.savefig(out + '.pdf'); fig.savefig(out + '.png', dpi=150)
print('saved')
