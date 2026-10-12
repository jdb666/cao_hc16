"""Tente igloo du HC16 Rando, refaite le 12/10 (JD : « tente avec arceaux reposant sur la poutre arrière et le tube avant au niveau
du collier, avec une avancée qui couvre l'avant sous le tube » ; arceaux croisés, igloo).
Deux arceaux alu croisés, posés sur le dessus du tube des colliers, à ses bouts, contre les joues (au niveau des colliers), et sur la
poutre AR, à ses bouts, contre les pièces d'angle : rectangle d'appui de 2 060 × 2 100, l'avant 640 plus haut que l'arrière.
Devant le tube, la toile continue en avancée jusqu'au bord avant et ferme l'avant sous le tube : dessus du coffre, 15 derrière
l'hiloire (variante « hiloire », par défaut), ou haut de C4, juste sous le tube (variante « c4 »). Bords latéraux sur le haut des
joues (dossiers) et des accoudoirs, puis le long des longerons ; bord arrière sur la poutre AR, porte dans le pan arrière ; jupes
sous les bords latéraux. Forme : membrane tendue (surface harmonique) accrochée aux deux arceaux (élastiques articulées aux pieds)
et à ses bords, soulevée à 25 au moins au-dessus du bateau là où elle le toucherait (coffre, tube, moteur). Les colliers traversent
les flancs (manchons). Profils du bateau lus dans plateforme/p3d.json (export de la maquette).
(09/10 : arceaux aux coins du bord avant, sur les joues devant les colliers : plans/tente_avant_tube.py)
python3 plans/tente.py [hiloire|c4] -> plans/tente_info.json, plans/tente_3d.json (maillages pour la page 3D)"""
import math, json, sys, numpy as np, yaml
from scipy.special import ellipk, ellipe
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
C = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
t = C['tente']
AVANCEE = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ('hiloire', 'c4') else t.get('avancee', 'hiloire')
P3 = json.load(open('/home/claude/cao/plateforme/p3d.json'))
M_ = {}
for g_ in ('full', 'new'):
    for o in P3[g_]:
        M_.setdefault(o['n'], o)
VX = {n: np.array(o['v'], float).reshape(-1, 3) for n, o in M_.items()}
X1, HY, ZR = t['x1'], t['demi_y'], t['z_arriere']
HIL = C['coffre']['hiloire']; WI = C['coffre']['largeur'] / 2 - C['coffre']['ep_flasque']
OFF = t.get('derriere_hiloire', 15)                  # bord avant (variante hiloire) : 15 derrière le pied de l'hiloire
_col = [VX[n] for n in VX if n.startswith('collier_pli') and n.endswith('_babord')]
XCOL = min(v[:, 0].min() for v in _col) if _col else 1942.0
XC4 = C['coffre'].get('face_ar_x', 2022.5)
# pieds des arceaux : dessus du tube des colliers, à ses bouts ; dessus de la poutre AR, à ses bouts
_tu = VX['tube_colliers']; XT, ZT = float((_tu[:, 0].min() + _tu[:, 0].max()) / 2), float(_tu[:, 2].max())
YT, YR = t['pieds_av']['y'], t['pieds_ar']['y']
if AVANCEE == 'c4':
    X0 = XC4 - 3                                     # bord avant sur le haut de C4, juste sous le tube
    xf = lambda y: X0
else:
    X0 = min(HIL['x_joue'] + OFF, XCOL - t.get('devant_collier', 40))   # coins : sur les joues, devant les colliers
    def xf(y):                                       # bord avant en plan : droit au milieu, en V jusqu'aux coins
        a = abs(y)
        if a <= HIL['y_plat']: return HIL['x_milieu'] + OFF
        return HIL['x_milieu'] + OFF + (X0 - HIL['x_milieu'] - OFF) * min(1.0, (a - HIL['y_plat']) / (HY - HIL['y_plat']))
# dessus du bateau sous la tente (toutes les pièces sauf gréement, coques, colliers, haubans) : tableau de hauteurs, pas de 10
_EXCL = ('voile', 'mat_', 'livarde', 'coque_', 'safran', 'pylone_a', 'decor', 'repere', 'hauban', 'collier_', 'tente', 'eau', 'barre_accouplement')
_T = []
for g_ in ('full', 'moteur'):
    for o in P3.get(g_, []):
        if not isinstance(o, dict) or o['n'].startswith(_EXCL) or not o.get('t'):
            continue
        v_ = np.array(o['v'], float).reshape(-1, 3); tr_ = np.array(o['t']).reshape(-1, 3); T3_ = v_[tr_]
        s_ = (T3_[:, :, 0].max(1) >= 1650) & (T3_[:, :, 0].min(1) <= X1 + 20) & (np.abs(T3_[:, :, 1]).min(1) <= HY + 20)
        if s_.any(): _T.append(T3_[s_])
_T = np.concatenate(_T)
_GX = np.arange(1650, X1 + 21, 10.0); _GY = np.arange(-HY - 10, HY + 11, 10.0)
_H = np.full((len(_GX), len(_GY)), -1e9)
for A_, B_, C_ in _T:                                # z-buffer vu de dessus : hauteur de chaque triangle aux nœuds qu'il couvre
    x0_, x1_ = min(A_[0], B_[0], C_[0]), max(A_[0], B_[0], C_[0]); y0_, y1_ = min(A_[1], B_[1], C_[1]), max(A_[1], B_[1], C_[1])
    i0, i1 = np.searchsorted(_GX, x0_), np.searchsorted(_GX, x1_, side='right'); j0, j1 = np.searchsorted(_GY, y0_), np.searchsorted(_GY, y1_, side='right')
    if i0 >= i1 or j0 >= j1:
        continue
    X_, Y_ = np.meshgrid(_GX[i0:i1], _GY[j0:j1], indexing='ij')
    d_ = (B_[1] - C_[1]) * (A_[0] - C_[0]) + (C_[0] - B_[0]) * (A_[1] - C_[1])
    if abs(d_) < 1e-9:
        continue
    l1 = ((B_[1] - C_[1]) * (X_ - C_[0]) + (C_[0] - B_[0]) * (Y_ - C_[1])) / d_
    l2 = ((C_[1] - A_[1]) * (X_ - C_[0]) + (A_[0] - C_[0]) * (Y_ - C_[1])) / d_
    l3 = 1 - l1 - l2; m_ = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
    if m_.any():
        Z_ = l1 * A_[2] + l2 * B_[2] + l3 * C_[2]
        sub = _H[i0:i1, j0:j1]; sub[m_] = np.maximum(sub[m_], Z_[m_])
def dessus(x, y, r=3):                               # plus haut point du bateau autour de (x, y) (±30 : la toile ne passe pas entre les nœuds du maillage)
    i = int(np.clip((x - _GX[0]) // 10, 0, len(_GX) - 2)); j = int(np.clip((y - _GY[0]) // 10, 0, len(_GY) - 2))
    return float(_H[max(0, i - r + 1):i + r + 1, max(0, j - r + 1):j + r + 1].max())
GARDE_MIN = t.get('garde', 25)
# profil du bateau le long du bord latéral (côté bâbord, symétrique) : joue (dossier), accoudoir, longeron, poutre AR
XA1 = max(VX['accoudoir_babord_couvercle'][:, 0]) if 'accoudoir_babord_couvercle' in VX else 3218.0
_V = np.vstack([VX[n] for n in ('joue_babord', 'accoudoir_babord_couvercle') if n in VX]); _V = _V[_V[:, 1] >= 1000]
_bins = {}
for x_, z_ in zip(np.round(_V[:, 0] / 10) * 10, _V[:, 2]):          # haut de la joue et de l'accoudoir : enveloppe par tranches de 10
    _bins[x_] = max(_bins.get(x_, -1e9), z_)
_bx = np.array(sorted(_bins)); _bz = np.array([_bins[q] for q in _bx])
def z_bord_brut(x):
    if x <= XA1 + 0.5:
        return float(np.interp(x, _bx, _bz))
    return ZR                                                          # derrière les bancs : le long du longeron, jusqu'à la poutre AR
X0F = xf(HY)                                                           # coins avant de la toile (sur les joues)
_xs = np.linspace(X0F, X1, 220); _zb = np.array([z_bord_brut(x) for x in _xs])
_zb[-1] = ZR
_h = []                                                                # bord latéral : enveloppe concave supérieure du profil ; dessous, la jupe
for p_ in zip(_xs, _zb):
    while len(_h) >= 2 and (_h[-1][0] - _h[-2][0]) * (p_[1] - _h[-2][1]) - (_h[-1][1] - _h[-2][1]) * (p_[0] - _h[-2][0]) >= 0:
        _h.pop()
    _h.append(p_)
_hx, _hz = np.array([q[0] for q in _h]), np.array([q[1] for q in _h])
z_bord = lambda x: float(np.interp(x, _hx, _hz))
z_bord_brut_i = lambda x: float(np.interp(x, _xs, _zb))
jupe = lambda x: z_bord(x) - z_bord_brut_i(x)
Z00 = z_bord(X0F)
YJ = WI - 70                                          # bord avant : posé sur le coffre (ou sur C4) jusque-là, puis vers le coin, sur la joue (cosinus)
def zf(y):
    a = abs(y)
    zd = lambda yy: dessus(xf(yy), yy, 1) + 3
    if a <= YJ: return zd(a)
    s = min(1.0, (a - YJ) / (HY - YJ)); z1_ = zd(YJ)
    return z1_ + (Z00 - z1_) * (1 - math.cos(math.pi * s)) / 2
z_ar = lambda y: ZR + 9 * min(1.0, max(0.0, (abs(y) - 1040) / max(1.0, HY - 1040)))   # bord arrière : poutre AR, puis pièce d'angle
# ---------- arceaux : élastiques articulées aux deux pieds, passant à la hauteur demandée au milieu de la corde ----------
RA = t['arceau_diam'] / 2
def elastica(A, B, sommet):
    D = math.hypot(B[0] - A[0], B[1] - A[1]); zA, zB = A[2], B[2]; S = math.hypot(D, zB - zA); H = sommet - (zA + zB) / 2
    f = lambda k: (k / ellipk(k * k)) / (2 * ellipe(k * k) / ellipk(k * k) - 1) - H / S
    k = brentq(f, 0.02, 0.9); K, E = ellipk(k * k), ellipe(k * k); L = S / (2 * E / K - 1)
    q = (2 * K / L) ** 2; al = 2 * math.asin(k)
    so = solve_ivp(lambda s_, y: [y[1], -q * math.sin(y[0]), math.cos(y[0]), math.sin(y[0])], [0, L], [al, 0, 0, 0],
                   max_step=L / 400, rtol=1e-10, atol=1e-10, dense_output=True)
    Y = so.sol(np.linspace(0, L, 1601)); xc, yc = Y[2], Y[3]
    ca, sa = D / S, (zB - zA) / S
    d = xc * ca - yc * sa; zz = zA + xc * sa + yc * ca               # repère de la corde -> (distance horizontale depuis A, z)
    ux, uy = (B[0] - A[0]) / D, (B[1] - A[1]) / D
    pts = np.column_stack([A[0] + d * ux, A[1] + d * uy, zz])
    ang_A = math.degrees(math.atan2(zz[1] - zz[0], d[1] - d[0])); ang_B = math.degrees(math.atan2(zz[-2] - zz[-1], d[-1] - d[-2]))
    return dict(L=L, pts=pts, angle_av=ang_A, angle_ar=ang_B)
FA = [(XT, YT, ZT + RA), (XT, -YT, ZT + RA)]                         # pieds avant : sur le tube (centre de l'arceau à son rayon au-dessus)
RB = [(X1, YR, ZR + RA), (X1, -YR, ZR + RA)]                         # pieds arrière : sur la poutre AR
ARC = [elastica(FA[0], RB[1], t['sommet_z']), elastica(FA[1], RB[0], t['sommet_z'])]   # croisés : bâbord avant -> tribord arrière, et l'inverse
# ---------- toile : membrane tendue entre ses bords et les arceaux, au-dessus du bateau (obstacle) ----------
NU, NV = 200, 160
us = np.linspace(0, 1, NU + 1); vs = np.linspace(0, 1, NV + 1)
YV = -HY + vs * 2 * HY
XFV = np.array([xf(y) for y in YV])
GX = XFV[None, :] + us[:, None] * (X1 - XFV)[None, :]; GY = np.broadcast_to(YV[None, :], GX.shape).copy()
Z = np.zeros(GX.shape); FIX = np.zeros(GX.shape, bool)
Z[0, :] = [zf(y) for y in YV]; Z[-1, :] = [z_ar(y) for y in YV]
Z[:, 0] = [z_bord(x) for x in GX[:, 0]]; Z[:, -1] = [z_bord(x) for x in GX[:, -1]]
FIX[0, :] = FIX[-1, :] = FIX[:, 0] = FIX[:, -1] = True
def uv(x, y):
    return (x - xf(y)) / (X1 - xf(y)), (y + HY) / (2 * HY)
for a in ARC:                                         # la toile est accrochée sous les arceaux
    for x, y, za in a['pts']:
        u_, v_ = uv(x, y); i, j = int(round(u_ * NU)), int(round(v_ * NV))
        if 0 < i < NU and 0 < j < NV:
            Z[i, j] = za - RA - 0.5; FIX[i, j] = True
LB = np.full(GX.shape, -1e9)
for i in range(1, NU):
    for j in range(1, NV):
        if not FIX[i, j]: LB[i, j] = dessus(GX[i, j], GY[i, j]) + GARDE_MIN
for i in range(1, NU):                                # départ : interpolation de Coons des bords
    for j in range(1, NV):
        if FIX[i, j]: continue
        u_, v_ = us[i], vs[j]
        Z[i, j] = ((1 - u_) * Z[0, j] + u_ * Z[-1, j] + (1 - v_) * Z[i, 0] + v_ * Z[i, -1]
                   - ((1 - u_) * (1 - v_) * Z[0, 0] + u_ * (1 - v_) * Z[-1, 0] + (1 - u_) * v_ * Z[0, -1] + u_ * v_ * Z[-1, -1]))
Z = np.maximum(Z, LB)
HXc = (X1 - XFV) / NU; HYc = 2 * HY / NV
WX = np.broadcast_to((1 / HXc ** 2)[None, :], Z.shape)[1:-1, 1:-1]; WYc = 1 / HYc ** 2
II, JJ = np.meshgrid(np.arange(NU + 1), np.arange(NV + 1), indexing='ij')
LIB = ~FIX[1:-1, 1:-1]
for it in range(40000):                               # SOR rouge-noir projetée (problème d'obstacle)
    dmax = 0.0
    for col in (0, 1):
        m = LIB & (((II + JJ)[1:-1, 1:-1] % 2) == col)
        zn = (WX * (Z[:-2, 1:-1] + Z[2:, 1:-1]) + WYc * (Z[1:-1, :-2] + Z[1:-1, 2:])) / (2 * WX + 2 * WYc)
        zi = Z[1:-1, 1:-1]
        nz = np.maximum(zi + 1.9 * (zn - zi), LB[1:-1, 1:-1])
        dz = np.abs(nz - zi)[m]
        if dz.size: dmax = max(dmax, float(dz.max()))
        zi[m] = nz[m]
    if dmax < 0.002: break
ITER = it
def z_uv(u_, v_):                                     # interpolation bilinéaire de la toile
    fu, fv = u_ * NU, v_ * NV; i = int(np.clip(fu, 0, NU - 1)); j = int(np.clip(fv, 0, NV - 1)); a, b = fu - i, fv - j
    return (1 - a) * (1 - b) * Z[i, j] + a * (1 - b) * Z[i + 1, j] + (1 - a) * b * Z[i, j + 1] + a * b * Z[i + 1, j + 1]
def z_xy(x, y):
    u_, v_ = uv(x, y); return z_uv(min(1, max(0, u_)), min(1, max(0, v_)))
# ---------- sorties ----------
def maillage(pas=2):
    I_ = list(range(0, NU + 1, pas)); J_ = list(range(0, NV + 1, pas))
    if I_[-1] != NU: I_.append(NU)
    if J_[-1] != NV: J_.append(NV)
    V = [(GX[i, j], GY[i, j], Z[i, j]) for i in I_ for j in J_]; T = []; n = len(J_)
    for a_ in range(len(I_) - 1):
        for b_ in range(n - 1):
            p = a_ * n + b_; T += [p, p + n, p + n + 1, p, p + n + 1, p + 1]
    return V, T
def tube(pts, r, nc=8):
    """Tube de rayon r le long d'une polyligne (maillage pour la page)."""
    P = np.array(pts, float); V, T = [], []
    for i, p in enumerate(P):
        d = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]; d /= np.linalg.norm(d)
        a = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        e1 = np.cross(d, a); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
        for k in range(nc):
            th = 2 * math.pi * k / nc; V.append(p + r * (math.cos(th) * e1 + math.sin(th) * e2))
    for i in range(len(P) - 1):
        for k in range(nc):
            a, b = i * nc + k, i * nc + (k + 1) % nc; T += [a, b, b + nc, a, b + nc, a + nc]
    return np.array(V), T
def nappe(L1, L2):
    """Surface réglée entre deux polylignes de même nombre de points."""
    V = list(L1) + list(L2); n = len(L1); T = []
    for i in range(n - 1):
        T += [i, i + 1, n + i + 1, i, n + i + 1, n + i]
    return np.array(V, float), T
def jupes(n=120):
    xs = [X0F + (X1 - X0F) * i / n for i in range(n + 1)]
    out = {}
    for nom, sg in (('babord', 1), ('tribord', -1)):
        out[nom] = nappe([(x, sg * HY, z_bord(x)) for x in xs], [(x, sg * HY, min(z_bord(x), z_bord_brut_i(x))) for x in xs])
    return out
def aire(V, T):
    V = np.array(V, float); T = np.array(T).reshape(-1, 3)
    return float(0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1).sum() / 1e6)
def garde():
    """Garde verticale mini toile / bateau sous la toile (hors bords), sur le tableau de hauteurs du bateau."""
    best = (1e9, None)
    for i in range(2, NU - 1):
        for j in range(2, NV - 1):
            g = Z[i, j] - dessus(GX[i, j], GY[i, j], 1)
            if g < best[0]: best = (g, (round(GX[i, j]), round(GY[i, j]), round(Z[i, j])))
    return best
def tetes(x=2450):
    """Assis sur les bancs à x (comme l'équipage de la page 3D) : garde verticale entre la toile et le dessus de chaque tête."""
    out = {}
    za = max(VX['banc_babord_assise'][:, 2]); yd = max(VX['banc_babord_assise'][:, 1])
    for nom, H in (('H 1,80', 1800), ('F 1,60', 1600)):
        yc, zc, rx, ry, rz = yd - (10 + .078 * H), za + .455 * H, .043 * H, .055 * H, .065 * H
        g = 1e9
        for a_ in np.linspace(-0.95, 0.95, 9):
            for b_ in np.linspace(-0.95, 0.95, 9):
                if a_ * a_ + b_ * b_ > 0.95: continue
                xx, yy = x + a_ * rx, yc + b_ * ry
                g = min(g, z_xy(xx, yy) - (zc + rz * math.sqrt(max(0.0, 1 - a_ * a_ - b_ * b_))))
        out[nom] = round(g)
    return out
if __name__ == '__main__':
    V, T = maillage(2)
    J = jupes()
    meshes = [dict(n='tente_toile', v=np.round(np.array(V).ravel(), 1).tolist(), t=T)]
    for nom, (Vj, Tj) in J.items():
        meshes.append(dict(n=f'tente_jupe_{nom}', v=np.round(Vj.ravel(), 1).tolist(), t=Tj))
    for k, a in enumerate(ARC):
        Va, Ta = tube(a['pts'][::8], RA)
        meshes.append(dict(n=f'tente_arceau_{k + 1}', v=np.round(Va.ravel(), 1).tolist(), t=Ta))
    json.dump(meshes, open('/home/claude/cao/plans/tente_3d.json', 'w'), separators=(',', ':'))
    g = garde()
    zt_ = float(Z.max()); ia, ja = np.unravel_index(int(Z.argmax()), Z.shape)
    zarc = max(float(a['pts'][:, 2].max()) for a in ARC)
    croise = float(np.interp(0.0, ARC[0]['pts'][::-1, 1], ARC[0]['pts'][::-1, 2]))   # hauteur des arceaux au croisement (y 0)
    xcroise = float(np.interp(0.0, ARC[0]['pts'][::-1, 1], ARC[0]['pts'][::-1, 0]))
    tz_ = C['plateforme']['trampoline_z']
    info = dict(variante=AVANCEE, long=round(X1 - xf(0)), long_coins=round(X1 - X0F), larg=2 * HY, x=[round(xf(0)), X1], x_coins=round(X0F),
                rectangle=dict(x=[round(XT), X1], long=round(X1 - XT), larg_av=2 * YT, larg_ar=2 * YR, z_av=round(ZT), z_ar=ZR, denivele=round(ZT - ZR)),
                avancee=dict(x_bord=round(xf(0)), long=round(XT - xf(0)), z_bord=round(zf(0))),
                sommet=round(zt_), sommet_xy=[round(GX[ia, ja]), round(GY[ia, ja])], haut_tramp=round(zt_ - tz_), croisement=dict(x=round(xcroise), z=round(croise)),
                arceau=round(max(a['L'] for a in ARC)), angle_pied=round(ARC[0]['angle_av']), angle_pied_ar=round(ARC[0]['angle_ar']),
                arceau_z_max=round(zarc), toile=round(aire(V, T), 2), porte='pan arrière',
                jupe=round(sum(aire(*J[k]) for k in J), 2), jupe_max=round(max(jupe(x) for x in _xs)),
                bord_avant=dict(x_milieu=round(xf(0)), z_milieu=round(zf(0)), x_coins=round(X0F), coins=round(Z00), derriere_hiloire=OFF if AVANCEE == 'hiloire' else None),
                garde=round(float(g[0])), garde_pt=g[1], tetes_x2450=tetes(2450), tetes_x2700=tetes(2700), iterations=ITER)
    json.dump(info, open('/home/claude/cao/plans/tente_info.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(info, ensure_ascii=False))
