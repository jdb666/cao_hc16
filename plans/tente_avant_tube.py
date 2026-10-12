"""Tente igloo du HC16 Rando (JD 09/10) : toile simple paroi sur deux arceaux diagonaux croisés au sommet.
(JD 09/10 17 h 40 : « tente inclut le coffre, ou derrière l'hiloire ») Elle couvre le dessus du coffre derrière l'hiloire, le tube
des colliers, les bancs et le trampoline : bord avant posé sur le dessus du coffre juste derrière l'hiloire (droite au milieu, en V
vers les joues), coins sur les joues juste devant les colliers ; bords latéraux sur le haut des joues (dossiers), des accoudoirs puis
le long des longerons ; bord arrière sur la poutre AR, porte dans le pan arrière. Des jupes ferment sous les bords latéraux, là où ils
passent au-dessus du bateau. Forme : surface de Coons des quatre bords, plus une bosse qui suit les arceaux (élastiques articulées aux
pieds), puis la toile est soulevée au-dessus du bateau là où elle le toucherait (coffre, tube, moteur : 25 au moins). Les colliers
traversent les flancs, juste au-dessus des joues (manchons). Profils du bateau lus dans plateforme/p3d.json (export de la maquette).
python3 plans/tente.py -> plans/tente_info.json, plans/tente_3d.json (maillages pour la page 3D)"""
import math, json, numpy as np, yaml
C = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
t = C['tente']
P3 = json.load(open('/home/claude/cao/plateforme/p3d.json'))
M_ = {}
for g_ in ('full', 'new'):
    for o in P3[g_]:
        M_.setdefault(o['n'], o)
VX = {n: np.array(o['v'], float).reshape(-1, 3) for n, o in M_.items()}
def haut(noms, x, dx=6.0, ymin=None, ymax=None):
    """Point le plus haut des pièces `noms` au droit de x (fenêtre ±dx, bande de y facultative)."""
    zs = []
    for n in noms:
        V = VX.get(n)
        if V is None:
            continue
        s = np.abs(V[:, 0] - x) <= dx
        if ymin is not None: s &= V[:, 1] >= ymin
        if ymax is not None: s &= V[:, 1] <= ymax
        if s.any(): zs.append(V[s, 2].max())
    return max(zs) if zs else None
X1, HY, ZR = t['x1'], t['demi_y'], t['z_arriere']
HIL = C['coffre']['hiloire']; WI = C['coffre']['largeur'] / 2 - C['coffre']['ep_flasque']
OFF = t.get('derriere_hiloire', 15)                  # bord avant : 15 derrière le pied de l'hiloire
_col = [VX[n] for n in VX if n.startswith('collier_pli') and n.endswith('_babord')]
XCOL = min(v[:, 0].min() for v in _col) if _col else 1942.0
X0 = min(HIL['x_joue'] + OFF, XCOL - t.get('devant_collier', 40))   # coins : sur les joues, devant les colliers (l'arceau passe en dedans)
def xf(y):                                           # bord avant en plan : droit au milieu, en V jusqu'aux coins
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
_xs = np.linspace(X0, X1, 220); _zb = np.array([z_bord_brut(x) for x in _xs])
_zb[-1] = ZR
# bord latéral de la toile : enveloppe concave supérieure du profil (la toile ne s'accroche pas dans les creux) ;
# entre ce bord et le bateau, la jupe latérale
_h = []
for p_ in zip(_xs, _zb):
    while len(_h) >= 2 and (_h[-1][0] - _h[-2][0]) * (p_[1] - _h[-2][1]) - (_h[-1][1] - _h[-2][1]) * (p_[0] - _h[-2][0]) >= 0:
        _h.pop()
    _h.append(p_)
_hx, _hz = np.array([q[0] for q in _h]), np.array([q[1] for q in _h])
z_bord = lambda x: float(np.interp(x, _hx, _hz))
z_bord_brut_i = lambda x: float(np.interp(x, _xs, _zb))
jupe = lambda x: z_bord(x) - z_bord_brut_i(x)
Z00 = z_bord(X0)
YJ = WI - 70                                          # bord avant : posé sur le dessus du coffre jusque-là, puis vers le coin, sur la joue (cosinus)
def zf(y):
    a = abs(y)
    zd = lambda yy: dessus(xf(yy), yy, 1) + 3
    if a <= YJ: return zd(a)
    s = min(1.0, (a - YJ) / (HY - YJ)); z1_ = zd(YJ)
    return z1_ + (Z00 - z1_) * (1 - math.cos(math.pi * s)) / 2
def xu(u, y): return xf(y) + u * (X1 - xf(y))
def z0(u, v):
    y = -HY + v * 2 * HY; x = xu(u, y)
    return z_bord(x) + (1 - u) * (zf(y) - z_bord(xf(y)))
# arceaux : élastiques (elastica articulée aux deux pieds, sans moment) passant par le sommet -> longueur « naturelle »
from scipy.special import ellipk, ellipe
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
DIAG = math.hypot(X1 - X0, 2 * HY)
def _elastica():
    zA, zB = z0(0, 0), z0(1, 1); S = math.hypot(DIAG, zB - zA); H = t['sommet_z'] - (zA + zB) / 2
    f = lambda k: (k / ellipk(k * k)) / (2 * ellipe(k * k) / ellipk(k * k) - 1) - H / S
    k = brentq(f, 0.02, 0.9); K, E = ellipk(k * k), ellipe(k * k); L = S / (2 * E / K - 1)
    q = (2 * K / L) ** 2; al = 2 * math.asin(k)
    so = solve_ivp(lambda s_, y: [y[1], -q * math.sin(y[0]), math.cos(y[0]), math.sin(y[0])], [0, L], [al, 0, 0, 0],
                   max_step=L / 400, rtol=1e-10, atol=1e-10, dense_output=True)
    Y = so.sol(np.linspace(0, L, 1601)); xc, yc = Y[2], Y[3]
    ca, sa = DIAG / S, (zB - zA) / S
    d = xc * ca - yc * sa; zz = zA + xc * sa + yc * ca               # repère corde -> (distance horizontale, z)
    return L, math.degrees(al), d, zz
L_ARC, ANGLE_PIED, _de, _ze = _elastica()
z_el = lambda u: float(np.interp(u * DIAG, _de, _ze))              # arceau le long de la diagonale, u = abscisse réduite
h_av = lambda r: z_el(0.5 - r / 2) - z0(0.5 - r / 2, 0.5 - r / 2)     # bosse le long de la demi-diagonale avant
h_ar = lambda r: z_el(0.5 + r / 2) - z0(0.5 + r / 2, 0.5 + r / 2)
def bosse(u, v):
    a, b_ = u - 0.5, v - 0.5; r = min(1.0, 2 * max(abs(a), abs(b_)))
    if abs(a) >= abs(b_): return h_av(r) if a < 0 else h_ar(r)
    w = (a / abs(b_) + 1) / 2                                          # panneau latéral : entre diagonale avant et arrière
    return (1 - w) * h_av(r) + w * h_ar(r)
def z_brut(u, v): return z0(u, v) + bosse(u, v)
def z(u, v):                                          # la toile passe au-dessus du bateau (25 au moins), sauf sur ses bords
    zb_ = z_brut(u, v)
    if u <= 0 or u >= 1 or v <= 0 or v >= 1:
        return zb_
    y = -HY + v * 2 * HY
    return max(zb_, dessus(xu(u, y), y) + GARDE_MIN)
def pt(u, v):
    y = -HY + v * 2 * HY
    return (xu(u, y), y, z(u, v))

def maillage(n=64):
    us = [0.5 - 0.5 * math.cos(math.pi * i / n) for i in range(n + 1)]      # resserré près des bords (parois raides)
    V, T = [], []
    for u in us:
        for v in us: V.append(pt(u, v))
    for i in range(n):
        for j in range(n):
            a = i * (n + 1) + j; T += [a, a + n + 1, a + n + 2, a, a + n + 2, a + 1]
    return V, T, us
def arceau(sens, n=200):
    pts = [pt(s, s if sens > 0 else 1 - s) for s in [i / n for i in range(n + 1)]]
    L = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
    return pts, L
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
def porte(n=60):
    """Porte sous le bord avant : du bord (sur le tube) jusqu'au trampoline et aux assises, plan x = X0."""
    ys = [-HY + 2 * HY * i / n for i in range(n + 1)]
    haut_ = [(X0, y, zf(y)) for y in ys]
    pl = C['plateforme']; za_ = max(VX['banc_babord_assise'][:, 2]) if 'banc_babord_assise' in VX else 685.0
    y_as = min(VX['banc_babord_assise'][:, 1]) if 'banc_babord_assise' in VX else 800.0
    z_tr = lambda y: pl['poutre_av_z'] + pl.get('poutre_av_fleche', 0) * max(0.0, 1 - (y / pl.get('poutre_av_y_libre', 925)) ** 2) + 3
    bas_ = [(X0, y, min(zf(y) - 5, za_ if abs(y) >= y_as else z_tr(y))) for y in ys]   # sur les assises, sinon sur le trampoline
    return nappe(haut_, bas_), haut_, bas_
def jupes(n=120):
    xs = [X0 + (X1 - X0) * i / n for i in range(n + 1)]
    out = {}
    for nom, sg in (('babord', 1), ('tribord', -1)):
        out[nom] = nappe([(x, sg * HY, z_bord(x)) for x in xs], [(x, sg * HY, min(z_bord(x), z_bord_brut_i(x))) for x in xs])
    return out
def garde(n=80):
    """Garde verticale mini toile / bateau sous la toile (maillages de la maquette)."""
    tris = []
    for nom, o in M_.items():
        if nom.startswith(('mat_', 'collier_', 'voile', 'livarde', 'coque_', 'safran', 'pylone_a', 'barre_acc', 'hauban', 'decor')) or not o['t']:
            continue
        v = np.array(o['v'], float).reshape(-1, 3); tr = np.array(o['t']).reshape(-1, 3)
        tris.append((nom, v[tr]))
    best = (1e9, None, None)
    for i in range(1, n):
        for j in range(1, n):
            u, v = i / n, j / n; x, y, zt = pt(u, v)
            for nom, T3 in tris:
                a, b_, c = T3[:, 0], T3[:, 1], T3[:, 2]
                sel = (np.minimum(np.minimum(a[:, 0], b_[:, 0]), c[:, 0]) <= x) & (np.maximum(np.maximum(a[:, 0], b_[:, 0]), c[:, 0]) >= x) & \
                      (np.minimum(np.minimum(a[:, 1], b_[:, 1]), c[:, 1]) <= y) & (np.maximum(np.maximum(a[:, 1], b_[:, 1]), c[:, 1]) >= y)
                if not sel.any(): continue
                A3, B3, C3 = a[sel], b_[sel], c[sel]
                d = (B3[:, 1] - C3[:, 1]) * (A3[:, 0] - C3[:, 0]) + (C3[:, 0] - B3[:, 0]) * (A3[:, 1] - C3[:, 1])
                ok = np.abs(d) > 1e-9
                l1 = np.where(ok, ((B3[:, 1] - C3[:, 1]) * (x - C3[:, 0]) + (C3[:, 0] - B3[:, 0]) * (y - C3[:, 1])) / np.where(ok, d, 1), -1)
                l2 = np.where(ok, ((C3[:, 1] - A3[:, 1]) * (x - C3[:, 0]) + (A3[:, 0] - C3[:, 0]) * (y - C3[:, 1])) / np.where(ok, d, 1), -1)
                l3 = 1 - l1 - l2
                inn = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
                if not inn.any(): continue
                zz = (l1 * A3[:, 2] + l2 * B3[:, 2] + l3 * C3[:, 2])[inn].max()
                if zt - zz < best[0]: best = (zt - zz, nom, (round(x), round(y), round(zt)))
    return best
def aire(V, T):
    V = np.array(V, float); T = np.array(T).reshape(-1, 3)
    return float(0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1).sum() / 1e6)
if __name__ == '__main__':
    ra = t['arceau_diam'] / 2
    V, T, _ = maillage(72)
    J = jupes()
    meshes = [dict(n='tente_toile', v=np.round(np.array(V).ravel(), 1).tolist(), t=T)]
    for nom, (Vj, Tj) in J.items():
        meshes.append(dict(n=f'tente_jupe_{nom}', v=np.round(Vj.ravel(), 1).tolist(), t=Tj))
    for sens, nom in ((1, 'tente_arceau_1'), (-1, 'tente_arceau_2')):
        pts, _ = arceau(sens)
        Va, Ta = tube([(x, y, z_ + ra + 0.5) for x, y, z_ in pts], ra)
        meshes.append(dict(n=nom, v=np.round(Va.ravel(), 1).tolist(), t=Ta))
    json.dump(meshes, open('/home/claude/cao/plans/tente_3d.json', 'w'), separators=(',', ':'))
    g = garde()
    la = [arceau(s_)[1] for s_ in (1, -1)]
    zt_ = max(z(i / 40, j / 40) for i in range(41) for j in range(41))
    info = dict(long=round(X1 - xf(0)), long_coins=round(X1 - X0), larg=2 * HY, x=[round(xf(0)), X1], x_coins=round(X0), sommet=round(zt_), haut_tramp=round(zt_ - C['plateforme']['trampoline_z']),
                arceau=round(max(la)), angle_pied=round(ANGLE_PIED), toile=round(aire(V, T), 2), porte='pan arrière',
                jupe=round(sum(aire(*J[k]) for k in J), 2), jupe_max=round(max(jupe(x) for x in _xs)),
                bord_avant=dict(x_milieu=round(xf(0)), z_milieu=round(zf(0)), x_coins=round(X0), coins=round(Z00), derriere_hiloire=OFF),
                garde=round(float(g[0])), garde_ou=g[1], garde_pt=g[2])
    json.dump(info, open('/home/claude/cao/plans/tente_info.json', 'w'), ensure_ascii=False, indent=1)
    print(info)
