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
S = 0.70                                      # main-view scale 7:10

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

# ======================= FRONT VIEW (web face) =======================
FX, FY = 1.70, 4.40                     # paper position of datum origin (end B, bottom A)
P = lambda z, y: (FX + S * z, FY + S * y)
x0, y0 = P(0, 0); x1, y1 = P(L, H)
rect(x0, y0, x1 - x0, y1 - y0, lw=LW_VIS)
for yy in (TF, H - TF):
    line(x0, P(0, yy)[1], x1, P(0, yy)[1], lw=LW_VIS * 0.8)
for yy in (TF + RF, H - TF - RF):                       # fillet tangent lines
    line(x0, P(0, yy)[1], x1, P(0, yy)[1], lw=0.3)
for z, y in FIG1:
    cx, cy = P(z, y)
    ax.add_patch(Circle((cx, cy), S * 0.5, fc='white', ec=K, lw=LW_VIS, zorder=4))
    centermark(cx, cy, S * 0.5)
line(P(ZM, 0)[0], y0 - 0.15, P(ZM, 0)[0], y1 + 0.15, ls=CHAIN, lw=0.3)   # CL (mid-span)
text(P(ZM, 0)[0] + 0.12, y1 + 0.12, '℄', fs=8)
# section cutting plane A-A at the top-flange hole station z = 5.40
zA = 5.40
cxA = P(zA, 0)[0]
line(cxA, y0 - 0.35, cxA, y1 + 0.35, lw=0.9, ls=(0, (14, 3, 3, 3, 3, 3)))
for yy, sg in ((y1 + 0.35, 1), (y0 - 0.35, -1)):
    line(cxA + 0.02, yy, cxA - 0.30, yy, lw=0.9)
    arrow(cxA - 0.05, yy, cxA - 0.32, yy)
    text(cxA - 0.43, yy, 'A', fs=10, bold=True)
# ordinates: horizontal (above), from end B
ordinate_h([(P(z, 0)[0], '%.3f' % z) for z, _ in sorted(FIG1)], y1, y1 + 0.38, x0, up=True)
# ordinates: vertical (left), from bottom A
ordinate_v([(P(0, y)[1], '%.3f' % y) for y in (H / 2 - 0.375, H / 2 + 0.375)], x0, x0 - 0.35,
           y0, left=True)
dim_lin(P(0, 0), P(0, H), x0 - 1.00, '3.00 REF', horiz=False)
dim_lin(P(0, 0), P(L, 0), y0 - 0.55, '8.20 ±.02', horiz=True, tpos=0.55)
# hole callout (web holes)
hx, hy = P(ZM + 1.0, H / 2 + 0.375)
leader((hx + S * 0.5 * 0.7, hy + S * 0.5 * 0.7), (x1 + 0.30, y1 - 0.05))
text(x1 + 0.33, y1 - 0.05, '4X ⌀1.000 THRU WEB', fs=FS, ha='left')
fcf(x1 + 0.33, y1 - 0.29, POS)
datum(x0 + 0.45, y0, 'A', 'down', 0.12)
datum(x0, y0 + S * 0.62, 'B', 'left', 0.30)
text((x0 + x1) / 2, y0 - 0.82, 'FRONT VIEW', fs=9, bold=True)

# ======================= TOP VIEW (top flange) =======================
TYc = 8.475                               # paper y of web centreline (datum C) in top view
T = lambda z, x: (FX + S * z, TYc + S * x)
tx0, ty0 = T(0, -BF / 2); tx1, ty1 = T(L, BF / 2)
rect(tx0, ty0, tx1 - tx0, ty1 - ty0, lw=LW_VIS)
for xx in (-TW / 2, TW / 2):
    line(tx0, T(0, xx)[1], tx1, T(0, xx)[1], lw=0.5, ls=HIDDEN)
line(tx0 - 0.25, TYc, tx1 + 0.25, TYc, ls=CHAIN, lw=0.3)
for z in TOP:
    for sx in (-1, 1):
        cx, cy = T(z, sx * HX)
        ax.add_patch(Circle((cx, cy), S * D / 2, fc='white', ec=K, lw=LW_VIS, zorder=4))
        centermark(cx, cy, S * D / 2)
ordinate_h([(T(z, 0)[0], '%.3f' % z) for z in TOP], ty1, ty1 + 0.38, tx0, up=True)
dim_lin(T(TOP[-1], -HX), T(TOP[-1], HX), tx1 + 0.45, '1.575', horiz=False, box=True)
line(T(TOP[-1], HX)[0] + S * D / 2 + 0.03, T(0, HX)[1], tx1 + 0.51, T(0, HX)[1])
line(T(TOP[-1], -HX)[0] + S * D / 2 + 0.03, T(0, -HX)[1], tx1 + 0.51, T(0, -HX)[1])
dim_lin(T(0, -BF / 2), T(0, BF / 2), tx0 - 0.40, '2.50 REF', horiz=False)
hx, hy = T(TOP[-1], HX)
leader((hx + S * D / 2 * 0.7, hy + S * D / 2 * 0.7), (tx1 + 0.30, ty1 + 0.62))
text(tx1 + 0.33, ty1 + 0.62, '12X ⌀.781 (25/32) THRU TOP FLANGE', fs=FS, ha='left')
fcf(tx1 + 0.33, ty1 + 0.38, POS)
text(tx1 + 0.75, TYc, 'C', fs=8, bold=True)
text((tx0 + tx1) / 2, ty0 - 0.16, 'TOP VIEW', fs=9, bold=True)

# ======================= BOTTOM VIEW (bottom flange) =======================
BYc = 2.225
B_ = lambda z, x: (FX + S * z, BYc - S * x)
bx0, by0 = B_(0, BF / 2); bx1, by1 = B_(L, -BF / 2)
rect(bx0, by0, bx1 - bx0, by1 - by0, lw=LW_VIS)
for xx in (-TW / 2, TW / 2):
    line(bx0, B_(0, xx)[1], bx1, B_(0, xx)[1], lw=0.5, ls=HIDDEN)
line(bx0 - 0.25, BYc, bx1 + 0.25, BYc, ls=CHAIN, lw=0.3)
for z in BOT:
    for sx in (-1, 1):
        cx, cy = B_(z, sx * HX)
        ax.add_patch(Circle((cx, cy), S * D / 2, fc='white', ec=K, lw=LW_VIS, zorder=4))
        centermark(cx, cy, S * D / 2)
ordinate_h([(B_(z, 0)[0], '%.3f' % z) for z in BOT], by0, by0 - 0.38, bx0, up=False)
dim_lin(B_(BOT[-1], HX), B_(BOT[-1], -HX), bx1 + 0.45, '1.575', horiz=False, box=True)
for sx in (-1, 1):
    line(B_(BOT[-1], sx * HX)[0] + S * D / 2 + 0.03, B_(0, sx * HX)[1], bx1 + 0.51, B_(0, sx * HX)[1])
hx, hy = B_(BOT[-1], -HX)
leader((hx + S * D / 2 * 0.7, hy + S * D / 2 * 0.7), (bx1 + 0.30, by1 + 0.10))
text(bx1 + 0.33, by1 + 0.10, '16X ⌀.781 (25/32) THRU BOTTOM FLANGE', fs=FS, ha='left')
fcf(bx1 + 0.33, by1 - 0.14, POS)
text(bx1 + 0.75, BYc, 'C', fs=8, bold=True)
text((bx0 + bx1) / 2, by1 + 0.15, 'BOTTOM VIEW', fs=9, bold=True)

# ======================= SECTION A-A (scale 1:1) =======================
SXc, SYb = 10.35, 4.40                    # paper: web centre x, bottom y
Q = lambda x, y: (SXc + x, SYb + y)


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


ax.add_patch(Polygon(ipoly(), closed=True, fc='white', ec=K, lw=LW_VIS, hatch='//////', zorder=3))
for sx in (-1, 1):
    for yb in (0, H - TF):                # holes cut by the section: open gaps in both flanges
        px, py = Q(sx * HX - D / 2, yb)
        ax.add_patch(Rectangle((px, py - 0.004), D, TF + 0.008, fc='white', ec='none', zorder=4))
        line(px, py, px, py + TF, lw=LW_VIS, z=5); line(px + D, py, px + D, py + TF, lw=LW_VIS, z=5)
        line(px, py, px + D, py, lw=LW_VIS * 0.8, z=5); line(px, py + TF, px + D, py + TF, lw=LW_VIS * 0.8, z=5)
    line(Q(sx * HX, 0)[0], Q(0, -0.12)[1], Q(sx * HX, 0)[0], Q(0, H + 0.12)[1], ls=CHAIN, lw=0.3)
line(Q(0, 0)[0], Q(0, -0.2)[1], Q(0, 0)[0], Q(0, H + 0.2)[1], ls=CHAIN, lw=0.3)
dim_lin(Q(-BF / 2, H), Q(BF / 2, H), Q(0, H + 0.62)[1], '2.50 REF', horiz=True)
dim_lin(Q(-HX, H), Q(HX, H), Q(0, H + 0.30)[1], '1.575', horiz=True, box=True)
dim_lin(Q(BF / 2, 0), Q(BF / 2, H), Q(BF / 2 + 0.38, 0)[0], '3.00 REF', horiz=False)
# flange thickness and web
dim_lin(Q(-BF / 2, H - TF), Q(-BF / 2, H), Q(-BF / 2 - 0.22, 0)[0], '', horiz=False, fs=6.4)
text(Q(-BF / 2 - 0.30, 0)[0], Q(0, H - TF / 2)[1], '.26 REF', fs=6.6, ha='right')
wx = Q(TW / 2, H / 2)
leader((wx[0], wx[1] - 0.25), (wx[0] + 0.55, wx[1] - 0.55))
text(wx[0] + 0.58, wx[1] - 0.55, '.15 REF', fs=6.6, ha='left')
fx_ = Q(TW / 2 + RF * (1 - 0.707), TF + RF * (1 - 0.707))
leader(fx_, (fx_[0] + 0.55, fx_[1] + 0.35))
text(fx_[0] + 0.58, fx_[1] + 0.35, 'R.25 REF (4X)', fs=6.6, ha='left')
# datum C on the web (centre plane): symbol attached to the web thickness
datum(Q(-TW / 2, H / 2)[0], Q(0, H / 2 + 0.35)[1], 'C', 'left', 0.42)
text(Q(0, 0)[0], Q(0, -0.40)[1], 'SECTION A-A', fs=9, bold=True)
text(Q(0, 0)[0], Q(0, -0.57)[1], 'SCALE 1:1', fs=FS_SM)

# ======================= ISOMETRIC (reference) =======================
IOX, IOY, IS = 12.55, 7.05, 0.40
c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def iso(x, y, z):        # x across (+ toward viewer), y up, z along length
    return (IOX + IS * (z - x) * c30, IOY + IS * (y - (z + x) * s30 * 0.0 - x * s30 + z * s30 * 0.0) + IS * z * s30 * 0.0 - IS * x * 0.0)


def iso(x, y, z):
    return (IOX + IS * (z * c30 - x * c30), IOY + IS * (y + z * s30 + x * s30) - IS * 2.3)


def face(pts3, fc='white', z=3, lw=0.7):
    ax.add_patch(Polygon([iso(*p) for p in pts3], closed=True, fc=fc, ec=K, lw=lw, zorder=z))


hw, yt, yb_ = BF / 2, H, 0
# draw back-to-front (viewer at +x, +y, -z end visible? use +x front, top, and z=0 end)
# bottom flange top surface (front outstand), web front face, top flange front edge, top face, end face
face([(TW / 2, TF, 0), (hw, TF, 0), (hw, TF, L), (TW / 2, TF, L)], fc='#f2f2f2', z=3)
face([(TW / 2, TF, 0), (TW / 2, H - TF, 0), (TW / 2, H - TF, L), (TW / 2, TF, L)], fc='#e6e6e6', z=3)
for z, y in FIG1:
    pts = [iso(TW / 2, y + 0.5 * math.sin(t), z + 0.5 * math.cos(t)) for t in
           [k * 2 * math.pi / 40 for k in range(41)]]
    ax.add_patch(Polygon(pts, closed=True, fc='white', ec=K, lw=0.6, zorder=3.5))
face([(hw, 0, 0), (hw, TF, 0), (hw, TF, L), (hw, 0, L)], fc='#d9d9d9', z=3.6)
face([(hw, H - TF, 0), (hw, H, 0), (hw, H, L), (hw, H - TF, L)], fc='#d9d9d9', z=3.7)
face([(-hw, H, 0), (hw, H, 0), (hw, H, L), (-hw, H, L)], fc='#f7f7f7', z=3.8)
for z in TOP:
    for sx in (-1, 1):
        pts = [iso(sx * HX + D / 2 * math.cos(t), H, z + D / 2 * math.sin(t)) for t in
               [k * 2 * math.pi / 36 for k in range(37)]]
        ax.add_patch(Polygon(pts, closed=True, fc='white', ec=K, lw=0.55, zorder=3.9))
# end face (z = 0) I-profile
prof = [(p[0] - SXc, p[1] - SYb) for p in ipoly()]
face([(px, py, 0) for px, py in prof], fc='#cfcfcf', z=4)
text(iso(0, 0, L / 2)[0] + 0.3, iso(0, 0, L / 2)[1] - 0.55, 'ISOMETRIC VIEW (REF)', fs=9, bold=True)
text(iso(0, 0, L / 2)[0] + 0.3, iso(0, 0, L / 2)[1] - 0.72, 'NOT TO SCALE', fs=FS_SM)

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

# ======================= NOTES =======================
NX, NY = 12.05, 5.78
notes = ['NOTES:',
         '1.  MATERIAL: 6061-T6 ALUMINUM, STOCK 1 =',
         '     AA I 3 X 2.03 EXTRUSION. DIMENSIONS MARKED',
         '     REF ARE AS-EXTRUDED (ALUMINUM ASSOC. STD).',
         '2.  SAW TO LENGTH 8.20 ±.02. NO MILLING.',
         '3.  DRILL FLANGE HOLES THROUGH ONE FLANGE ONLY.',
         '     DO NOT CUT INTO THE WEB OR FILLETS.',
         '4.  HOLE LOCATIONS ARE BASIC FROM DATUM B (END)',
         '     AND DATUM C (WEB CENTER PLANE); PATTERNS',
         '     ARE SYMMETRIC ABOUT DATUM C AND MID-SPAN ℄.',
         '5.  DEBURR ALL HOLES. BREAK SHARP EDGES .005-.015.',
         '6.  FINISHED WEIGHT 0.993 LB (REF); 32 HOLES TOTAL.',
         '7.  HIDDEN LINES OMITTED FOR CLARITY.']
for i, n in enumerate(notes):
    text(NX, NY - i * 0.19, n, fs=7.4 if i else 8.5, ha='left', bold=(i == 0))

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
                                (c2, c3, 'SCALE', '7:10', 8.5), (c3, c4, 'SIZE', 'B', 8.5),
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
sx_, sy_ = TX + 1.30, TY + THT + 0.30
text(sx_ + 1.45, sy_, 'THIRD ANGLE PROJECTION', fs=6.4, ha='left', bold=True)
ax.add_patch(Polygon([(sx_, sy_ - 0.10), (sx_, sy_ + 0.10), (sx_ + 0.42, sy_ + 0.16),
                      (sx_ + 0.42, sy_ - 0.16)], closed=True, fc='none', ec=K, lw=0.6, zorder=5))
line(sx_ - 0.05, sy_, sx_ + 0.47, sy_, ls=CHAIN, lw=0.3)
ax.add_patch(Circle((sx_ + 0.95, sy_), 0.16, fc='none', ec=K, lw=0.6, zorder=5))
ax.add_patch(Circle((sx_ + 0.95, sy_), 0.10, fc='none', ec=K, lw=0.6, zorder=5))
line(sx_ + 0.70, sy_, sx_ + 1.20, sy_, ls=CHAIN, lw=0.3)

out = '/home/claude/dwg/USC06_MTC06_IBeam_RevB_Drawing'
fig.savefig(out + '.pdf'); fig.savefig(out + '.png', dpi=150)
print('saved')
