"""Vues cotées de la plateforme HC16 recalée (profil, dessus, face), avec le modèle précédent en pointillé."""
import math, io, yaml, numpy as np, sys, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle, Circle
sys.path.insert(0, '/home/claude/cao')
plt.rcParams.update({'svg.fonttype': 'none', 'font.family': ['IBM Plex Sans', 'DejaVu Sans'], 'font.size': 9})
NEW = yaml.safe_load(open('/home/claude/cao/cotes.yaml')); OLD = yaml.safe_load(open('/home/claude/cao/cotes_avant_releves.yaml'))
PR = json.load(open('/home/claude/cao/profils_hc16.json'))
INK, ALU, OLDC, DIM, EAU, TRAMP = '#15232A', '#AEB8BD', '#D1495B', '#B8650E', '#4F9BC8', '#3B4348'
it = lambda t, x: float(np.interp(x, [p[0] for p in t], [p[1] for p in t]))
def geo(C):
    c, p = C['coques'], C['plateforme']
    g = dict(c=c, p=p, hy=c['entraxe'] / 2, fb=p['poutre_av_x'], rb=p['poutre_ar_x'], zav=p.get('poutre_av_z', p['poutre_z']), zar=p.get('poutre_ar_z', p['poutre_z']),
             ly=p.get('longeron_y', c['entraxe'] / 2), lp=p['poutre_longueur'] / 2, fl=p.get('poutre_av_fleche', 0), du=p.get('poutre_axe_u', 0.0))
    mg = p.get('martingale') or C.get('coffre', {}).get('martingale'); g['mg'] = mg
    g['yf'] = p.get('poutre_av_y_libre', g['lp']); g['pa'] = p.get('piece_angle')
    return g
N, O = geo(NEW), geo(OLD)
from shapely.geometry import box as sbox, Point
from shapely.ops import unary_union
PIECE = '#8E989E'
def zcam(g, y):
    a = abs(y); return g['zav'] + g['fl'] * (1 - (a / g['yf']) ** 2) if a <= g['yf'] else g['zav']
def ztige(g, y):
    mg = g['mg']; zb = g['zav'] - mg['pied_sous_axe_extremites']
    if 'jour_sous_poutre' in mg:
        yj = mg['y_jour']; zj = g['zav'] - 30.94 - mg['jour_sous_poutre'] - mg.get('tige_diam', 6) / 2
    else:
        yj = mg['y_cable']; zj = g['zav'] - mg['cable_sous_axe_extremites']
    return zb + (zj - zb) * abs(y) / yj
def rrect(x0, x1, y0, y1, r):
    r = max(0.1, min(r, (x1 - x0) / 2 - .1, (y1 - y0) / 2 - .1))
    return sbox(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, resolution=10)
def piece(g, vue, xb, zb, sens, sg=1):
    """Silhouette d'une pièce d'angle : vue 'profil' (x, z), 'dessus' (x, y), 'face' (y, z)."""
    pa = g['pa']; m, hm, nx, nf, hn = pa['manchon'], pa['manchon_demi_h'], pa['nez_x'], pa['nez_x_fin'], pa['nez_demi_h']
    xa, xz = sorted((xb - sens * nx, xb - sens * nf))
    if vue == 'profil':
        sh = [rrect(xb - m, xb + m, zb - hm, zb + hm, hm - 8), rrect(xa, xz, zb - hn, zb + hn, hn - 12),
              sbox(xb - pa['bossage_d'] / 2, zb - pa['bossage_bas'], xb + pa['bossage_d'] / 2, zb - hm + 12)]
    elif vue == 'dessus':
        sh = [sbox(xb - m, pa['y_int'], xb + m, pa['y_nez'] + 10), rrect(xa, xz, pa['y_nez'], pa['y_ext'], pa['nez_r'])]
    else:
        sh = [sbox(pa['y_int'], zb - hm, pa['y_nez'] + 10, zb + hm), rrect(pa['y_nez'], pa['y_ext'], zb - hn, zb + hn, hn - 12),
              sbox(pa['y_pylone'] - pa['bossage_d'] / 2, zb - pa['bossage_bas'], pa['y_pylone'] + pa['bossage_d'] / 2, zb - hm + 12)]
    u = unary_union(sh)
    pts = list(u.exterior.coords)
    if vue == 'dessus': pts = [(x, sg * y) for x, y in pts]
    if vue == 'face': pts = [(sg * y, z) for y, z in pts]
    return pts
def goutte(nom, cx, cz, sens=1):            # section dans le plan (x, z) : u selon sens·x
    return [(cx + sens * u, cz + v) for u, v in PR[nom]]
def goutte_y(nom, cy, cz, sens):             # section dans le plan (y, z)
    return [(cy + sens * u, cz + v) for u, v in PR[nom]]
def cote_h(ax, x0, x1, y, txt, y_ext=None, col=DIM, dy=10):
    if y_ext is not None:
        for x, ye in zip((x0, x1), y_ext): ax.plot([x, x], [ye, y + (dy if y > ye else -dy)], color=col, lw=.6)
    ax.annotate('', xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle='<->', color=col, lw=.9, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + 12, txt, color=col, ha='center', va='bottom', fontsize=8.5, fontweight='bold')
def cote_v(ax, x, y0, y1, txt, col=DIM, side=1, x_ext=None):
    if x_ext is not None:
        for y, xe in zip((y0, y1), x_ext): ax.plot([xe, x + 10 * side], [y, y], color=col, lw=.6)
    ax.annotate('', xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle='<->', color=col, lw=.9, shrinkA=0, shrinkB=0))
    ax.text(x + 14 * side, (y0 + y1) / 2, txt, color=col, ha='left' if side > 0 else 'right', va='center', fontsize=8.5, fontweight='bold')
def svg(fig):
    b = io.StringIO(); fig.savefig(b, format='svg', bbox_inches='tight', pad_inches=0.05); plt.close(fig)
    s = b.getvalue(); return s[s.index('<svg'):]
def coque_profil(g):
    xs = np.linspace(0, g['c']['longueur'], 200)
    top = [(x, it(g['c']['pont'], x)) for x in xs]; bot = [(x, it(g['c']['quille'], x)) for x in xs]
    return top + bot[::-1]
def profil():
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.axhline(0, color=EAU, lw=1); ax.text(-140, -12, 'flottaison', color=EAU, fontsize=7.5, va='top')
    ax.add_patch(MPoly(coque_profil(O), closed=True, fill=False, ec=OLDC, lw=1, ls=(0, (4, 3))))
    ax.add_patch(MPoly(coque_profil(N), closed=True, fc='#F4F6F6', ec=INK, lw=1.2))
    g = N
    for xb, zb, s in ((g['fb'], g['zav'], 1), (g['rb'], g['zar'], -1)):
        dk = it(g['c']['pont'], xb)
        ax.add_patch(Rectangle((xb - 35, dk), 70, zb - dk, fc=ALU, ec=INK, lw=.6))
        ax.add_patch(MPoly(goutte('poutre', xb - s * g['du'], zb, s), closed=True, fc=ALU, ec=INK, lw=.8))
        ax.add_patch(MPoly(piece(g, 'profil', xb, zb, s), closed=True, fc=PIECE, alpha=.55, ec=INK, lw=.7, zorder=4))
    ax.add_patch(MPoly(goutte('poutre', g['fb'] - g['du'], g['zav'] + g['fl'], 1), closed=True, fill=False, ec=INK, lw=.7, ls=(0, (1.5, 1.5))))
    ax.text(g['fb'] - 60, g['zav'] + g['fl'] - 10, 'poutre AV\nau milieu (+100)', ha='right', va='top', fontsize=7.5, color=INK)
    xl = np.array([g['fb'], g['rb']]); zl = np.array([g['zav'], g['zar']])
    ax.fill_between(xl, zl - 22, zl + 22.5, color=ALU, lw=0, alpha=.9); ax.plot(xl, zl + 22.5, color=INK, lw=.7); ax.plot(xl, zl - 22, color=INK, lw=.7)
    ax.plot([g['fb'] - g['du'] + 64.5, g['rb'] + g['du'] - 64.5], [g['zav'] + g['fl'], g['zar']], color=TRAMP, lw=1.6)
    ax.text((g['fb'] + g['rb']) / 2, (g['zav'] + g['fl'] + g['zar']) / 2 + 12, 'trampoline (axe)', ha='center', fontsize=7.5, color=TRAMP)
    mg = g['mg']; zbm = g['zav'] - mg['pied_sous_axe_extremites']
    ax.plot([g['fb'], g['fb']], [zbm, g['zav'] + g['fl'] - 31], color='#6E7A80', lw=2)
    sf = NEW['safrans']; ax.add_patch(Rectangle((sf['x'] - sf['corde'] / 2, sf['z_centre'] - sf['hauteur'] / 2), sf['corde'], sf['hauteur'], fc='#8C979C', ec=INK, lw=.5, alpha=.45))
    for xb, zb in ((O['fb'], O['zav']), (O['rb'], O['zar'])):
        ax.add_patch(MPoly(goutte('poutre', xb, zb, 1 if xb < 3000 else -1), closed=True, fill=False, ec=OLDC, lw=.9, ls=(0, (3, 2))))
    # pied de mât prévu et pente du pont
    xm = NEW['mats']['x_pied']; zm = it(g['c']['pont'], xm); ax.plot([xm], [zm], 'o', color=DIM, ms=4)
    ax.annotate(f'pied de mât (x {xm:,.0f}) :\npente du pont / longerons\nP4 relevé +1,7°, modèle +0,9°'.replace(',', ' '), xy=(xm, zm), xytext=(130, 500), fontsize=7.5, color=DIM, va='bottom', ha='left', arrowprops=dict(arrowstyle='-', color=DIM, lw=.6))
    cote_h(ax, 0, g['fb'], 790, 'P2  2 070', y_ext=(450, g['zav'] + 40))
    cote_h(ax, 0, g['rb'], 900, 'P3  4 145 (relevé 4 140)', y_ext=(450, g['zar'] + 40))
    cote_h(ax, g['fb'], g['rb'], 700, 'D1  2 075 (relevé 2 080)', y_ext=(g['zav'] + 110, g['zar'] + 40))
    cote_h(ax, 0, 5050, -640, 'P1  5 050', y_ext=(420, 60))
    dk = it(g['c']['pont'], g['fb']); cote_v(ax, g['fb'] + 190, dk, g['zav'] + 22.5, 'P5  250', x_ext=(g['fb'] + 40, g['fb'] + 140))
    cote_v(ax, g['fb'] - 170, it(g['c']['quille'], g['fb']), dk, 'P6  500', side=-1, x_ext=(g['fb'] - 10, g['fb'] - 10))
    dk2 = it(g['c']['pont'], g['rb']); cote_v(ax, g['rb'] - 170, dk2, g['zar'] + 31, 'A3  210', side=-1, x_ext=(g['rb'] - 40, g['rb'] - 40))
    ax.set_aspect('equal'); ax.set_xlim(-150, 5500); ax.set_ylim(-700, 990); ax.axis('off')
    return svg(fig)
def dessus():
    fig, ax = plt.subplots(figsize=(11, 5.4))
    for g, st in ((O, dict(fill=False, ec=OLDC, lw=1, ls=(0, (4, 3)))), (N, dict(fc='#F4F6F6', ec=INK, lw=1.2))):
        xs = np.linspace(0, g['c']['longueur'], 160)
        for sg in (1, -1):
            yc = sg * g['hy']; b = [it(g['c']['demi_largeur'], x) for x in xs]
            ax.add_patch(MPoly([(x, yc + bb) for x, bb in zip(xs, b)] + [(x, yc - bb) for x, bb in zip(xs[::-1], b[::-1])], closed=True, **st))
    g = N
    ax.add_patch(Rectangle((g['fb'] - g['du'] + 64.5, -(g['ly'] - 51)), g['rb'] - g['fb'] + 2 * g['du'] - 129, 2 * (g['ly'] - 51), fc=TRAMP, alpha=.18, ec=TRAMP, lw=.8))
    for xb, s in ((g['fb'], 1), (g['rb'], -1)):
        x0 = xb - g['du'] - 31 if s > 0 else xb + g['du'] - 64.5
        ax.add_patch(Rectangle((x0, -g['lp']), 95.5, 2 * g['lp'], fc=ALU, ec=INK, lw=.7))
    for sg in (1, -1):
        y0 = sg * g['ly'] - (51 if sg > 0 else -51); y1 = sg * g['ly'] + 22 * sg
        ax.add_patch(Rectangle((g['fb'] - 60, min(y0, y1)), g['rb'] - g['fb'] + 120, abs(y1 - y0), fc=ALU, ec=INK, lw=.7))
        for xb, zb, s in ((g['fb'], g['zav'], 1), (g['rb'], g['zar'], -1)):
            ax.add_patch(MPoly(piece(g, 'dessus', xb, zb, s, sg), closed=True, fc=PIECE, ec=INK, lw=.7, zorder=4))
            ax.add_patch(Circle((xb, sg * g['hy']), 35, fill=False, ec=INK, lw=.6, ls=(0, (2, 2)), zorder=5))
    for sg in (1, -1):
        ax.plot([O['fb'], O['rb']], [sg * O['ly']] * 2, color=OLDC, lw=.9, ls=(0, (3, 2)))
    for xb in (O['fb'], O['rb']): ax.plot([xb, xb], [-O['lp'], O['lp']], color=OLDC, lw=.9, ls=(0, (3, 2)))
    cote_v(ax, 5300, -g['hy'], g['hy'], 'V1 = A1\n2 000\naxes des\ncoques', x_ext=(4200, 4200))
    cote_v(ax, 3520, -(g['ly'] + 21.9), g['ly'] + 21.9, 'D2  2 230\nfaces ext.\nlongerons')
    ax.text(2720, 0, 'trampoline\n1 979 × 2 084\n(D4 relevé 2 000 × 2 100)', ha='center', va='center', fontsize=9, color=DIM, fontweight='bold')
    pa = g['pa']
    cote_h(ax, g['fb'] - pa['nez_x'], g['rb'] + pa['nez_x'], 1405, 'D6  ≈ 2 269 nez des pièces d’angle (à relever)', y_ext=(1130, 1130))
    cote_h(ax, g['fb'], g['rb'], -1470, 'D1  2 075 entre axes des poutres', y_ext=(-1140, -1140))
    cote_h(ax, g['fb'] - g['du'] - 31, g['rb'] + g['du'] + 31, 1265, 'D5  2 170 faces extérieures des poutres', y_ext=(1110, 1110))
    ax.annotate('', xy=(g['rb'] + 190, -925), xytext=(g['rb'] + 190, 925), arrowprops=dict(arrowstyle='<->', color=DIM, lw=.9))
    ax.text(g['rb'] + 215, 520, 'A2  1 850\nentre pièces\nd’angle', color=DIM, fontsize=8.5, fontweight='bold', va='center')
    ym = 1000 + 190; ax.annotate('', xy=(1766, 1000), xytext=(1766, ym), arrowprops=dict(arrowstyle='<->', color=DIM, lw=.9))
    ax.text(1740, 1095, 'D3  190', color=DIM, fontsize=8.5, fontweight='bold', ha='right', va='center')
    ax.set_aspect('equal'); ax.set_xlim(-150, 5750); ax.set_ylim(-1580, 1480); ax.axis('off')
    return svg(fig)
def section_coque(g, x, yc):
    c = g['c']; k, b = it(c['quille'], x), it(c['demi_largeur'], x); d = it(c['pont'], x) - c['bouge_pont']; n = 24
    pts = [(yc + b * math.cos(math.pi * j / n), d - (d - k) * math.sin(math.pi * j / n) ** 0.55) for j in range(n + 1)]
    pts += [(yc - b * math.cos(math.pi * j / n), d + c['bouge_pont'] * math.sin(math.pi * j / n)) for j in range(1, n)]
    return pts
def face():
    fig, ax = plt.subplots(figsize=(11, 4.4))
    for g, st in ((O, dict(fill=False, ec=OLDC, lw=1, ls=(0, (4, 3)))), (N, dict(fc='#F4F6F6', ec=INK, lw=1.2))):
        for sg in (1, -1): ax.add_patch(MPoly(section_coque(g, g['fb'], sg * g['hy']), closed=True, **st))
    for g, col, ls, lw in ((O, OLDC, (0, (3, 2)), .9), (N, INK, '-', .8)):
        ys = np.linspace(-g['lp'], g['lp'], 161); za = np.array([zcam(g, y) for y in ys])
        if g is N: ax.fill_between(ys, za - 31, za + 31, color=ALU, lw=0)
        ax.plot(ys, za + 31, color=col, lw=lw, ls=ls); ax.plot(ys, za - 31, color=col, lw=lw, ls=ls)
        mg = g['mg']; zb = g['zav'] - mg['pied_sous_axe_extremites']
        ax.plot([0, 0], [zb, g['zav'] + g['fl'] - 31], color=col if g is O else '#6E7A80', lw=2 if g is N else .9, ls=ls)
        for sg in (1, -1): ax.plot([0, sg * mg['y_cable']], [zb, ztige(g, mg['y_cable'])], color=col if g is O else '#6E7A80', lw=1.8 if g is N else .8, ls=ls)
    g = N
    for sg in (1, -1):
        dk = it(g['c']['pont'], g['fb'])
        ax.add_patch(Rectangle((sg * g['hy'] - 35, dk), 70, g['zav'] - dk, fc=ALU, ec=INK, lw=.6))
        ax.add_patch(MPoly(goutte_y('longeron', sg * g['ly'], g['zav'], -sg), closed=True, fc=ALU, ec=INK, lw=.8))
        ax.add_patch(MPoly(piece(g, 'face', g['fb'], g['zav'], 1, sg), closed=True, fc=PIECE, alpha=.55, ec=INK, lw=.7, zorder=4))
    zb = g['zav'] - g['mg']['pied_sous_axe_extremites']
    cote_v(ax, -150, zb, g['zav'], '', side=-1, x_ext=(-20, -915))
    ax.text(-150, 345, 'V4  170', color=DIM, ha='center', va='top', fontsize=8.5, fontweight='bold')
    cote_v(ax, -1330, g['zav'], g['zav'] + g['fl'], 'V2  100', side=-1, x_ext=(-935, -40))
    cote_h(ax, -g['hy'], g['hy'], -330, 'V1  2 000', y_ext=(-190, -190))
    cote_h(ax, 0, g['mg']['y_cable'], 230, 'V5  1 000', y_ext=(zb - 10, ztige(g, g['mg']['y_cable']) - 10))
    ax.text(1180, g['zav'] - 150, 'tiges inox : jour de 15\nsous la poutre (V5)', fontsize=7.5, color=DIM, ha='left', va='top')
    ax.set_aspect('equal'); ax.set_xlim(-1650, 1900); ax.set_ylim(-420, 760); ax.axis('off')
    return svg(fig)

# ---- semelle de pied de mât (plat CP sur bourrage époxy, perpendiculaire au mât) ----
MATS = NEW['mats']; SM = MATS['semelle']; CQ = NEW['coques']
def pont_modele(x, y):
    yc = CQ['entraxe'] / 2; b = it(CQ['demi_largeur'], x); d = it(CQ['pont'], x); t = min(1.0, abs(y - yc) / b)
    return d - CQ['bouge_pont'] + CQ['bouge_pont'] * math.sqrt(max(0.0, 1 - t * t))
XM, YM = MATS['x_pied'], SM['y_mat']
PENTE_MOD = math.atan(-(pont_modele(XM + 5, YM) - pont_modele(XM - 5, YM)) / 10)
def pont_p4(x, y):          # pente locale du pont corrigée sur P4 autour du pied de mât
    return pont_modele(x, y) - (math.tan(math.radians(SM['pente_pont_p4'])) - math.tan(PENTE_MOD)) * (x - XM)
QU, LA = math.radians(MATS['quete_deg']), math.radians(SM['inclinaison_laterale'])
NX, NY, NZ = math.sin(QU), -math.sin(LA), math.cos(QU)
X0, X1 = XM + SM['dx'][0], XM + SM['dx'][1]; Y0, Y1 = YM + SM['dy'][0], YM + SM['dy'][1]
RP = SM.get('renfort', {}); EPR = RP.get('ep', 0.0)
def sup(x, y):              # dessus du renfort de pont cintré (support du bourrage)
    return pont_p4(x, y) + EPR
def semelle_geo():
    xs, ys = np.linspace(X0, X1, 45), np.linspace(Y0, Y1, 39)
    z0 = max(sup(x, y) + (NX * (x - XM) + NY * (y - YM)) / NZ for x in xs for y in ys) + SM['bourrage_min']
    zu = lambda x, y: z0 - (NX * (x - XM) + NY * (y - YM)) / NZ
    J = np.array([[zu(x, y) - sup(x, y) for x in xs] for y in ys])
    vol = J.sum() * (xs[1] - xs[0]) * (ys[1] - ys[0]) / 1000
    coins = dict(av_int=zu(X0, Y0) - sup(X0, Y0), av_ext=zu(X0, Y1) - sup(X0, Y1), ar_int=zu(X1, Y0) - sup(X1, Y0), ar_ext=zu(X1, Y1) - sup(X1, Y1))
    return dict(z0=z0, zu=zu, jmin=J.min(), jmax=J.max(), vol=vol, coins=coins, dessus=z0 + SM['ep'] / NZ)
def semelle():
    G = semelle_geo(); zu, ep = G['zu'], SM['ep']; ztop = G['dessus']
    AMB, AMBL, CP, CPL = '#D69B64', '#8F5A2C', '#E8C79A', '#8F5A2C'
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.9), gridspec_kw=dict(width_ratios=[1.25, 1]))
    # coupe en travers à x = XM, vue de l'avant (bâbord à droite)
    a1.add_patch(MPoly(section_coque(N, XM, N['hy']), closed=True, fc='#F4F6F6', ec=INK, lw=1.1))
    ysd = np.linspace(Y0, Y1, 80)
    yr = np.linspace(N['hy'] - RP.get('demi_y', 0), N['hy'] + RP.get('demi_y', 0), 90)
    if EPR: a1.add_patch(MPoly([(y, pont_p4(XM, y)) for y in yr] + [(y, sup(XM, y)) for y in yr[::-1]], closed=True, fc='#E8C79A', ec=CPL, lw=.6))
    a1.add_patch(MPoly([(y, sup(XM, y)) for y in ysd] + [(Y1, zu(XM, Y1)), (Y0, zu(XM, Y0))], closed=True, fc=AMB, ec=AMBL, lw=.7))
    a1.add_patch(MPoly([(Y0, zu(XM, Y0)), (Y1, zu(XM, Y1)), (Y1, zu(XM, Y1) + ep), (Y0, zu(XM, Y0) + ep)], closed=True, fc=CP, ec=CPL, lw=.8))
    EMP = MATS.get('emplanture')                       # (JD 06/10) rail U, cale triangulaire boulonnée, ergot
    ALU_, ALUL_, ANO_, INX_ = '#C9CED2', '#6E7A80', '#3A3F44', '#E3E7EA'
    if EMP:
        r_, ca_, eg_ = EMP['rail'], EMP['cale'], EMP['ergot']; W_, H_, e_ = r_['larg'], r_['h'], r_['ep']
        import hc16_rando as HR_
        nb_, nh_ = HR_.pivot_emplanture(EMP), HR_.hauteur_emplanture(EMP)        # axe du boulon, dessus de la cale
        n0c = ca_.get('pointe_z', e_)                                             # bas de la cale (pointe en bas, JD 06/10)
        zc0, zc1 = ztop + n0c, ztop + nh_; zbo = ztop + nb_; zm0 = zc1
    else:
        zm0 = ztop
    a1.add_patch(Rectangle((YM - 30, zm0), 60, 520 - zm0, fc='#2B2F33', ec=INK, lw=.6))
    if EMP:
        a1.add_patch(MPoly([(YM - W_ / 2, ztop), (YM + W_ / 2, ztop), (YM + W_ / 2, ztop + H_), (YM + W_ / 2 - e_, ztop + H_), (YM + W_ / 2 - e_, ztop + e_),
                            (YM - W_ / 2 + e_, ztop + e_), (YM - W_ / 2 + e_, ztop + H_), (YM - W_ / 2, ztop + H_)], closed=True, fc=ALU_, ec=ALUL_, lw=.6))
        a1.add_patch(Rectangle((YM - ca_['larg'] / 2, zc0), ca_['larg'], zc1 - zc0, fc=ANO_, ec=INK, lw=.6))
        a1.add_patch(Rectangle((YM - W_ / 2 - 8, zbo - r_['trou'] / 2), W_ + 16, r_['trou'], fc=INX_, ec=INK, lw=.5))
        a1.add_patch(Rectangle((YM - eg_['d'] / 2, zc1), eg_['d'], eg_['h'], fc=INX_, ec=INK, lw=.5, ls=(0, (2, 1.5))))
        a1.annotate(f"rail U {W_:.0f} × {H_:.0f} × {e_:.0f}", xy=(YM + W_ / 2, ztop + H_ - 4), xytext=(YM + 44, ztop + 36), fontsize=7, color=INK, va='center',
                    arrowprops=dict(arrowstyle='-', color=DIM, lw=.5))
        a1.annotate(f"cale alu, boulon Ø {r_['trou']:.0f}", xy=(YM + ca_['larg'] / 2, zc1 - 6), xytext=(YM + 44, ztop + 58), fontsize=7, color=INK, va='center',
                    arrowprops=dict(arrowstyle='-', color=DIM, lw=.5))
        a1.annotate(f"ergot Ø {eg_['d']:.0f}", xy=(YM + eg_['d'] / 2, zc1 + eg_['h'] / 2), xytext=(YM + 44, ztop + 80), fontsize=7, color=INK, va='center',
                    arrowprops=dict(arrowstyle='-', color=DIM, lw=.5))
    PY = NEW['coffre']['pylones']; yp = NEW['coffre']['largeur'] / 2 - NEW['coffre']['ep_flasque'] - PY['y_int']
    a1.add_patch(Rectangle((yp - PY['diam'] / 2, ztop), PY['diam'], 520 - ztop, fc='#26292C', ec=INK, lw=.6))
    a1.text(yp - PY['diam'] / 2 - 8, 470, 'tubes carbone\ndu coffre', ha='right', va='center', fontsize=7, color=INK)
    a1.text(YM, 505, 'mât Ø 60', ha='center', va='center', fontsize=7, color='white')
    a1.plot([N['hy'], N['hy']], [150, 520], color='#6E7A80', lw=.6, ls=(0, (6, 2, 1, 2)))
    a1.text(N['hy'] - 6, 205, 'axe de coque', ha='right', va='bottom', fontsize=7, color='#6E7A80', rotation=90)
    cote_h(a1, N['hy'], YM, 395, f'{YM - N["hy"]:.0f}', dy=6)
    cote_h(a1, Y0, Y1, 258, f'semelle {Y1 - Y0:.0f}', dy=6)
    for y, ha in ((Y0, 'right'), (Y1, 'left')):
        j = zu(XM, y) - sup(XM, y)
        a1.annotate(f'{j:.0f}'.replace('.', ','), xy=(y, sup(XM, y) + j / 2), xytext=(y + (-28 if ha == 'right' else 28), sup(XM, y) + j / 2 - 30),
                    ha=ha, va='center', fontsize=8, color=AMBL, fontweight='bold', arrowprops=dict(arrowstyle='-', color=AMBL, lw=.6))
    a1.text(Y1 + 12, ztop + 4, f'CP {ep:.0f}', fontsize=7.5, color=CPL, va='bottom')
    a1.set_title(f'En travers au pied de mât (x {XM:,.0f}), vue de l’avant'.replace(',', ' '), fontsize=9, color=INK, loc='left')
    a1.set_aspect('equal'); a1.set_xlim(790, 1250); a1.set_ylim(190, 520); a1.axis('off')
    # coupe en long dans l'axe du mât (y = YM), vue de bâbord (étrave à gauche)
    XL0, XL1 = XM - 206, XM + 214
    xsd = np.linspace(XL0, XL1, 120)
    a2.add_patch(MPoly([(x, pont_p4(x, YM)) for x in xsd] + [(XL1, 190), (XL0, 190)], closed=True, fc='#F4F6F6', ec='none'))
    a2.plot(xsd, [pont_p4(x, YM) for x in xsd], color=INK, lw=1.1)
    xss = np.linspace(X0, X1, 60)
    xr_ = np.linspace(XM + RP.get('dx', [0, 0])[0], XM + RP.get('dx', [0, 0])[1], 60)
    if EPR: a2.add_patch(MPoly([(x, pont_p4(x, YM)) for x in xr_] + [(x, sup(x, YM)) for x in xr_[::-1]], closed=True, fc='#E8C79A', ec=CPL, lw=.6))
    a2.add_patch(MPoly([(x, sup(x, YM)) for x in xss] + [(X1, zu(X1, YM)), (X0, zu(X0, YM))], closed=True, fc=AMB, ec=AMBL, lw=.7))
    a2.add_patch(MPoly([(X0, zu(X0, YM)), (X1, zu(X1, YM)), (X1, zu(X1, YM) + ep), (X0, zu(X0, YM) + ep)], closed=True, fc=CP, ec=CPL, lw=.8))
    ux, uz = NX, NZ
    P_ = lambda s_, n_: (XM + s_ * uz + n_ * ux, ztop - s_ * ux + n_ * uz)      # s le long de la semelle (vers l'arrière), n le long du mât
    n0 = nh_ if EMP else 0.0
    L = (520 - ztop) / uz
    a2.add_patch(MPoly([P_(-30, n0), P_(30, n0), P_(30, L), P_(-30, L)], closed=True, fc='#2B2F33', ec=INK, lw=.6))
    if EMP:
        if 'pointe_z' in ca_:                                                     # triangle pointe en bas, il pivote sur le boulon
            prof_ = [(-ca_['pointe'] / 2, ca_['pointe_z']), (ca_['pointe'] / 2, ca_['pointe_z']), (ca_['haut'] / 2, n0), (-ca_['haut'] / 2, n0)]
        else:
            prof_ = [(-ca_['base'] / 2, e_), (ca_['base'] / 2, e_), (ca_['haut'] / 2, n0), (-ca_['haut'] / 2, n0)]
        a2.add_patch(MPoly([P_(*q_) for q_ in prof_], closed=True, fc=ANO_, ec=INK, lw=.6))
        a2.add_patch(MPoly([P_(-r_['l'] / 2, 0), P_(r_['l'] / 2, 0), P_(r_['l'] / 2, H_), P_(-r_['l'] / 2, H_)], closed=True, fc=ALU_, ec=ALUL_, lw=.6, alpha=.92))
        for kk in r_['crans']:
            a2.add_patch(Circle(P_(kk * r_['pas'], nb_), r_['trou'] / 2, fc=INX_ if kk == 0 else 'white', ec=INK if kk == 0 else ALUL_, lw=.5))
        a2.add_patch(MPoly([P_(-eg_['d'] / 2, n0), P_(eg_['d'] / 2, n0), P_(eg_['d'] / 2, n0 + eg_['h']), P_(-eg_['d'] / 2, n0 + eg_['h'])], closed=True, fc=INX_, ec=INK, lw=.5, ls=(0, (2, 1.5))))
        qc_ = HR_.quetes_crans(NEW)
        qq = (' · '.join(f'{v:.1f}' for _, v in qc_).replace('.', ',') + '°') if qc_ else None
        a2.annotate(f"trous Ø {r_['trou']:.0f} tous les {r_['pas']:.0f}" + (f"\nquête {qq}" if qq else ''), xy=P_(r_['l'] / 2 - 10, nb_),
                    xytext=(XM + 106, 440), fontsize=7, color=INK, ha='left', va='center', arrowprops=dict(arrowstyle='-', color=DIM, lw=.5))
        a2.annotate('cale triangulaire pointe en bas :\nelle pivote sur le boulon', xy=P_(-24, n0 - 4), xytext=(XM - 181, 440), fontsize=7, color=INK, ha='left', va='center',
                    arrowprops=dict(arrowstyle='-', color=DIM, lw=.5))
    a2.plot([XM, XM], [ztop, 515], color=DIM, lw=.6, ls=(0, (3, 2)))
    a2.text(XM + 10, 492, f'quête {MATS["quete_deg"]:.0f}°', fontsize=8, color=DIM, fontweight='bold')
    a2.text(XM - 191, 212, f'pont +{SM["pente_pont_p4"]:.1f}° vers l’étrave (P4)'.replace('.', ','), fontsize=7.5, color=INK)
    for x, ha in ((X0, 'right'), (X1, 'left')):
        j = zu(x, YM) - sup(x, YM)
        a2.annotate(f'{j:.0f}', xy=(x, sup(x, YM) + j / 2), xytext=(x + (-24 if ha == 'right' else 24), pont_p4(x, YM) - 30),
                    ha=ha, va='center', fontsize=8, color=AMBL, fontweight='bold', arrowprops=dict(arrowstyle='-', color=AMBL, lw=.6))
    cote_h(a2, X0, X1, 258, f'semelle {X1 - X0:.0f}', dy=6)
    a2.set_title(f'En long dans l’axe du mât (y {YM:,.0f}), vue de bâbord'.replace(',', ' '), fontsize=9, color=INK, loc='left')
    a2.set_aspect('equal'); a2.set_xlim(XL0, XL1); a2.set_ylim(190, 520); a2.axis('off')
    fig.tight_layout(w_pad=2)
    return svg(fig), G
if __name__ == '__main__':
    sv, G = semelle()
    out = dict(profil=profil(), dessus=dessus(), face=face(), semelle=sv)
    print('semelle', {k: (round(v, 1) if isinstance(v, float) else v) for k, v in G.items() if k != 'zu'})
    json.dump(out, open('/home/claude/cao/plateforme/dessins.json', 'w'))
    for k_, v in out.items(): open(f'/home/claude/cao/plateforme/{k_}.svg', 'w').write(v)
    print({k_: len(v) for k_, v in out.items()})
