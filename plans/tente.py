"""Tente igloo du HC16 Rando : toile (surface de Coons des bords + bosse), deux arceaux diagonaux croisés.
Renvoie la toile et les arceaux en maillage, les longueurs d'arceaux et la garde mini au-dessus du bateau."""
import math, json, numpy as np, yaml
C = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
k, m, t = C['coffre'], C['mats'], C['tente']
qa = math.radians(m['quete_deg'])
XCOL = m['x_pied'] + m['collier_hauteur'] * math.sin(qa); ZC = m['z_pied'] + m['collier_hauteur'] * math.cos(qa)
ZTS = ZC + k['dessus_cotes_au_dessus_collier']
ZB, ZBS, CPL = k['fond_z'], k['fond_z_cotes'], k['fond_plat_demi']
WI = k['largeur'] / 2 - k['ep_flasque']
AF = XCOL - k['avant_x']; XR = k['face_ar_x'] + k['bancs']['longueur']; AR = XR - XCOL; BJ = ZTS - ZBS
b = k['bancs']; ZS = b['plan_z'] + b['hauteur']; XB0 = b.get('x_debut', k['face_ar_x']); XB1 = XB0 + (XR - XB0)
X0, X1, HY, ZR = t['x0'], t['x1'], t['demi_y'], t['z_arriere']
zb = lambda y: ZB + (ZBS - ZB) * max(0.0, min(1.0, (abs(y) - CPL) / (WI - CPL)))
def joue(x):
    if x <= XCOL: c = (XCOL - x) / AF; return ZBS + BJ * math.sqrt(max(0.0, 1 - c * c))
    s = (x - XCOL) / AR; return ZBS + BJ * math.sqrt(max(0.0, 1 - s * s))
def z_bord(x):                      # bord latéral : dessus de joue, puis assise de banc, puis longeron jusqu'à la poutre AR
    z = joue(x) if x <= XR else 0.0
    if XB0 <= x <= XR + 74: z = max(z, ZS)
    if x > XR + 74: z = ZS + (ZR - ZS) * (x - XR - 74) / (X1 - XR - 74)
    return z
# bord latéral de la toile : enveloppe concave du profil joue / banc / longeron (la jupe latérale ferme le reste)
_xs = np.linspace(X0, X1, 400); _zs = np.array([z_bord(x) for x in _xs])
_h = []
for p_ in zip(_xs, _zs):
    while len(_h) >= 2 and (_h[-1][0] - _h[-2][0]) * (p_[1] - _h[-2][1]) - (_h[-1][1] - _h[-2][1]) * (p_[0] - _h[-2][0]) >= 0: _h.pop()
    _h.append(p_)
_hx, _hz = np.array([q[0] for q in _h]), np.array([q[1] for q in _h])
z_bord_brut = z_bord
z_bord = lambda x: float(np.interp(x, _hx, _hz))
jupe = lambda x: z_bord(x) - z_bord_brut(x)       # hauteur de la jupe latérale sous le bord de toile
ZT, CPT = k['dessus_z'], k.get('dessus_plat_demi', CPL)
zt = lambda y: ZT + (ZTS - ZT) * max(0.0, min(1.0, (abs(y) - CPT) / (WI - CPT)))
def zf(y):                          # bord avant : sur le dessus du coffre, section x = X0
    c = (XCOL - X0) / AF; yy = min(abs(y), WI)
    return zb(yy) + (zt(yy) - zb(yy)) * math.sqrt(max(0.0, 1 - c * c)) + 5
Z00 = z_bord(X0); Z10 = ZR
def z0(u, v):
    x, y = X0 + u * (X1 - X0), -HY + v * 2 * HY
    return z_bord(x) + (1 - u) * (zf(y) - Z00)
# arceaux : élastiques (elastica articulée aux deux pieds, sans moment) passant par le sommet -> longueur « naturelle »
from scipy.special import ellipk, ellipe
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
DIAG = math.hypot(X1 - X0, 2 * HY)
def _elastica():
    zA, zB = z0(0, 0), z0(1, 1); S = math.hypot(DIAG, zB - zA); H = t['sommet_z'] - (zA + zB) / 2
    f = lambda k: (k / ellipk(k * k)) / (2 * ellipe(k * k) / ellipk(k * k) - 1) - H / S
    k = brentq(f, 0.02, 0.6); K, E = ellipk(k * k), ellipe(k * k); L = S / (2 * E / K - 1)
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
A = t['sommet_z'] - z0(0.5, 0.5)
def bosse(u, v):
    a, b_ = u - 0.5, v - 0.5; r = min(1.0, 2 * max(abs(a), abs(b_)))
    if abs(a) >= abs(b_): return h_av(r) if a < 0 else h_ar(r)
    w = (a / abs(b_) + 1) / 2                                          # panneau latéral : entre diagonale avant et arrière
    return (1 - w) * h_av(r) + w * h_ar(r)
def z(u, v): return z0(u, v) + bosse(u, v)
def pt(u, v): return (X0 + u * (X1 - X0), -HY + v * 2 * HY, z(u, v))

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
def garde(meshes, n=90):
    """Garde verticale mini toile / bateau (maillages triangulés, lancer vertical)."""
    tris = []
    for o in meshes:
        if o['n'].startswith(('tente', 'mat_', 'collier_', 'voile', 'livarde', 'coque_', 'safran', 'pylone_a', 'barre')): continue
        v = np.array(o['v'], float).reshape(-1, 3); tr = np.array(o['t']).reshape(-1, 3)
        tris.append((o['n'], v[tr]))
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
if __name__ == '__main__':
    G = json.load(open('/home/claude/cao/plans/global.json'))
    L1 = arceau(1)[1]
    print('sommet', round(z(.5, .5)), 'arceau (diag toile)', round(L1), 'élastique', round(L_ARC), 'angle pied', round(ANGLE_PIED, 1))
    V, T, _ = maillage(80); V = np.array(V); T = np.array(T).reshape(-1, 3)
    aire = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1).sum() / 1e6
    aj = 2 * sum(jupe(x) for x in _xs) * (_xs[1] - _xs[0]) / 1e6
    g = garde(G)
    info = dict(long=X1 - X0, larg=2 * HY, sommet=round(z(.5, .5)), haut_tramp=round(z(.5, .5) - C['plateforme']['trampoline_z']),
                arceau=round(L_ARC), angle_pied=round(ANGLE_PIED), toile=round(aire, 2), jupe=round(aj, 2), jupe_max=round(max(jupe(x) for x in _xs)), garde=round(float(g[0])), garde_ou=g[1])
    json.dump(info, open('/home/claude/cao/plans/tente_info.json', 'w'), ensure_ascii=False)
    print(info)
