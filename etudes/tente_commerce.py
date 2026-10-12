"""(JD 12/10) Tente igloo du commerce sur le HC16 Rando : « trouver une tente du commerce dont la dimension correspondrait à des
arceaux un peu plus longs devant, on pourra recouvrir le coffre et les joues », puis « tente igloo du commerce en 200 × 250 à peu près ».
Dôme à 2 arceaux croisés de L × W × h (cm, au sol) : pieds AR sur la poutre AR (à ses bouts, comme la tente du 12/10), pieds AV posés
sur le bateau à la distance L (arceaux rallongés devant). Forme naturelle = la tente montée à plat (arceaux en élastique, toile en
membrane tendue), inclinée sur le rectangle de ses pieds ; forme drapée = la même toile soulevée à 25 au-dessus du bateau là où il la
traverse. Sorties : pieds, inclinaison, arceaux, sommet, ce qui traverse la toile naturelle (de combien), gréement dedans ou dehors,
hauteurs sous la toile, maillages pour la page 3D (TENTE_JSON=... PAGE_OUT=... python3 plateforme/page.py).
python3 etudes/tente_commerce.py L W h [nom]  -> etudes/tente_commerce/<nom>.json, <nom>_3d.json"""
import json, math, sys, numpy as np
from scipy.special import ellipk, ellipe
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
import scipy.sparse as sp, scipy.sparse.linalg as spl
import os
OUT = '/home/claude/cao/etudes/tente_commerce/'; os.makedirs(OUT, exist_ok=True)
L_, W_, h_ = (10 * float(a) for a in sys.argv[1:4]); NOM = sys.argv[4] if len(sys.argv) > 4 else f'{int(L_ / 10)}x{int(W_ / 10)}x{int(h_ / 10)}'   # cm -> mm
XR = 4145.0; RA = 5.5; GARDE = 25.0
P3 = json.load(open('/home/claude/cao/plateforme/p3d.json'))
M = {}
for g in ('full', 'new', 'roule', 'moteur', 'rig'):
    for o in P3.get(g, []):
        if isinstance(o, dict) and o.get('v') and o.get('t'):
            M.setdefault(o['n'], o)
V = {n: np.array(o['v'], float).reshape(-1, 3) for n, o in M.items()}
T = {n: np.array(o['t']).reshape(-1, 3) for n, o in M.items()}
EXCL = ('voile', 'mat_', 'livarde', 'safran', 'pylone_a', 'decor', 'repere', 'hauban', 'collier_', 'tente', 'eau', 'barre_accouplement', 'hc16')
# ---------- dessus du bateau (z-buffer vu de dessus, pas de 10), coques comprises
GX = np.arange(1300, 4400, 10.0); GY = np.arange(-1400, 1401, 10.0)
H = np.full((len(GX), len(GY)), -1e9)
def raster(tris, Hm):
    for A_, B_, C_ in tris:
        x0_, x1_ = min(A_[0], B_[0], C_[0]), max(A_[0], B_[0], C_[0]); y0_, y1_ = min(A_[1], B_[1], C_[1]), max(A_[1], B_[1], C_[1])
        i0, i1 = np.searchsorted(GX, x0_), np.searchsorted(GX, x1_, side='right'); j0, j1 = np.searchsorted(GY, y0_), np.searchsorted(GY, y1_, side='right')
        if i0 >= i1 or j0 >= j1: continue
        X_, Y_ = np.meshgrid(GX[i0:i1], GY[j0:j1], indexing='ij')
        d_ = (B_[1] - C_[1]) * (A_[0] - C_[0]) + (C_[0] - B_[0]) * (A_[1] - C_[1])
        if abs(d_) < 1e-9: continue
        l1 = ((B_[1] - C_[1]) * (X_ - C_[0]) + (C_[0] - B_[0]) * (Y_ - C_[1])) / d_
        l2 = ((C_[1] - A_[1]) * (X_ - C_[0]) + (A_[0] - C_[0]) * (Y_ - C_[1])) / d_
        l3 = 1 - l1 - l2; m_ = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if m_.any():
            Z_ = l1 * A_[2] + l2 * B_[2] + l3 * C_[2]; sub = Hm[i0:i1, j0:j1]; sub[m_] = np.maximum(sub[m_], Z_[m_])
for n in V:
    if n.startswith(EXCL): continue
    TR = V[n][T[n]]
    s_ = (TR[:, :, 0].max(1) >= GX[0]) & (TR[:, :, 0].min(1) <= GX[-1]) & (np.abs(TR[:, :, 1]).min(1) <= GY[-1])
    if s_.any(): raster(TR[s_], H)
def dessus(x, y, r=1):
    i = int(np.clip(round((x - GX[0]) / 10), 0, len(GX) - 1)); j = int(np.clip(round((y - GY[0]) / 10), 0, len(GY) - 1))
    return float(H[max(0, i - r):i + r + 1, max(0, j - r):j + r + 1].max())
# ---------- pieds : AR sur la poutre AR (ou le pont de la coque au-delà), AV à la distance L, posés sur le bateau
yc = W_ / 2
zr = dessus(XR, yc, 2) + RA
def pied_av():
    best = None
    for x in np.arange(XR - 400, 1300, -2.0):
        z = dessus(x, yc, 1) + RA
        d = math.hypot(XR - x, z - zr)
        if d >= L_:
            return x, z
    return None
xf, zf = pied_av()
R_mid = np.array([XR, 0.0, zr]); F_mid = np.array([xf, 0.0, zf])
es = (F_mid - R_mid) / np.linalg.norm(F_mid - R_mid); et = np.array([0, 1.0, 0]); en = np.cross(et, es)
if en[2] < 0: en = -en
th = math.degrees(math.atan2(zf - zr, XR - xf))
def boat(s, t, n): return R_mid + np.outer(s, es) + np.outer(t, et) + np.outer(n, en) if np.ndim(s) else R_mid + s * es + t * et + n * en
# ---------- arceaux (repère de la tente : s le long, t en travers, n normal) : élastiques articulées, sommet h
def elastica(A, B, sommet):
    D = math.hypot(B[0] - A[0], B[1] - A[1]); zA, zB = A[2], B[2]; S = math.hypot(D, zB - zA); Hh = sommet - (zA + zB) / 2
    f = lambda k: (k / ellipk(k * k)) / (2 * ellipe(k * k) / ellipk(k * k) - 1) - Hh / S
    k = brentq(f, 0.02, 0.9); K, E = ellipk(k * k), ellipe(k * k); Lp = S / (2 * E / K - 1)
    q = (2 * K / Lp) ** 2; al = 2 * math.asin(k)
    so = solve_ivp(lambda s_, y: [y[1], -q * math.sin(y[0]), math.cos(y[0]), math.sin(y[0])], [0, Lp], [al, 0, 0, 0], max_step=Lp / 400, rtol=1e-10, atol=1e-10, dense_output=True)
    Y = so.sol(np.linspace(0, Lp, 1601)); xc, ycc = Y[2], Y[3]
    ca, sa = D / S, (zB - zA) / S; d = xc * ca - ycc * sa; zz = zA + xc * sa + ycc * ca
    ux, uy = (B[0] - A[0]) / D, (B[1] - A[1]) / D
    return dict(L=Lp, pts=np.column_stack([A[0] + d * ux, A[1] + d * uy, zz]), ang=math.degrees(math.atan2(zz[1] - zz[0], d[1] - d[0])))
ARC = [elastica((0, yc, 0), (L_, -yc, 0), h_), elastica((0, -yc, 0), (L_, yc, 0), h_)]
# ---------- toile naturelle : membrane harmonique (bords à n = 0, accrochée sous les arceaux)
NU, NV = 160, 140
us = np.linspace(0, L_, NU + 1); vs = np.linspace(-yc, yc, NV + 1)
N = np.zeros((NU + 1, NV + 1)); FIX = np.zeros_like(N, bool); FIX[0, :] = FIX[-1, :] = FIX[:, 0] = FIX[:, -1] = True
for a in ARC:
    for s, t, n in a['pts']:
        i, j = int(round(s / L_ * NU)), int(round((t + yc) / W_ * NV))
        if 0 < i < NU and 0 < j < NV: N[i, j] = n - RA - 0.5; FIX[i, j] = True
hs, ht = L_ / NU, W_ / NV
def harmonique(N, FIX, LB=None, it_max=30000):
    if LB is None:                                    # résolution directe
        idx = -np.ones(N.shape, int); lib = np.argwhere(~FIX); idx[tuple(lib.T)] = np.arange(len(lib))
        rows, cols, vals = [], [], []; b = np.zeros(len(lib))
        cx, cy = 1 / hs ** 2, 1 / ht ** 2
        for k, (i, j) in enumerate(lib):
            rows.append(k); cols.append(k); vals.append(-2 * (cx + cy))
            for di, dj, c in ((1, 0, cx), (-1, 0, cx), (0, 1, cy), (0, -1, cy)):
                ii, jj = i + di, j + dj
                if idx[ii, jj] >= 0: rows.append(k); cols.append(idx[ii, jj]); vals.append(c)
                else: b[k] -= c * N[ii, jj]
        A = sp.csr_matrix((vals, (rows, cols)), shape=(len(lib), len(lib))); x = spl.spsolve(A, b)
        N2 = N.copy(); N2[tuple(lib.T)] = x; return N2
    Z = np.maximum(N.copy(), np.where(FIX, -1e9, LB)); WX, WY = 1 / hs ** 2, 1 / ht ** 2
    II, JJ = np.meshgrid(np.arange(NU + 1), np.arange(NV + 1), indexing='ij'); LIB = ~FIX[1:-1, 1:-1]
    for it in range(it_max):
        dmax = 0.0
        for col in (0, 1):
            m = LIB & (((II + JJ)[1:-1, 1:-1] % 2) == col)
            zn = (WX * (Z[:-2, 1:-1] + Z[2:, 1:-1]) + WY * (Z[1:-1, :-2] + Z[1:-1, 2:])) / (2 * WX + 2 * WY)
            zi = Z[1:-1, 1:-1]; nz = np.maximum(zi + 1.9 * (zn - zi), LB[1:-1, 1:-1]); dz = np.abs(nz - zi)[m]
            if dz.size: dmax = max(dmax, float(dz.max()))
            zi[m] = nz[m]
        if dmax < 0.005: break
    return Z
N0 = harmonique(N, FIX)
SS, TT = np.meshgrid(us, vs, indexing='ij')
def aire(Nm):
    P = boat(SS.ravel(), TT.ravel(), Nm.ravel()).reshape(NU + 1, NV + 1, 3)
    a = P[1:, :-1] - P[:-1, :-1]; b = P[:-1, 1:] - P[:-1, :-1]; c = P[1:, 1:] - P[1:, :-1]; d = P[1:, 1:] - P[:-1, 1:]
    return float((0.5 * np.linalg.norm(np.cross(a, b), axis=2) + 0.5 * np.linalg.norm(np.cross(c, d), axis=2)).sum() / 1e6)
# ---------- toile drapée : soulevée à GARDE au-dessus du bateau (obstacle exprimé en n)
LB = np.full(N.shape, -1e9)
for i in range(1, NU):
    for j in range(1, NV):
        if FIX[i, j]: continue
        n = N0[i, j]
        for _ in range(3):
            p = boat(us[i], vs[j], n); hb = dessus(p[0], p[1])
            if hb < -1e8: n = -1e9; break
            n = n + (hb + GARDE - p[2]) / en[2]
        LB[i, j] = n
N1 = harmonique(N, FIX, LB)
pen = LB - N0                                          # > 0 : le bateau traverse la toile naturelle (de tant)
P0 = boat(SS.ravel(), TT.ravel(), N0.ravel()).reshape(NU + 1, NV + 1, 3)
P1 = boat(SS.ravel(), TT.ravel(), N1.ravel()).reshape(NU + 1, NV + 1, 3)
def zones(mask, pen):
    out = []
    pts = np.argwhere(mask)
    if not len(pts): return out
    for nom, cond in (('coffre et capot (x < 2022)', lambda p: p[0] < 2022 and abs(p[1]) < 1100), ('joues (dossiers)', lambda p: abs(p[1]) >= 1100 and p[0] < 3230),
                      ('tube et potences', lambda p: 2040 <= p[0] <= 2130 and abs(p[1]) < 1100), ('bancs et accoudoirs', lambda p: 2022 <= p[0] <= 3230 and 790 <= abs(p[1]) < 1100),
                      ('arrière (longerons, poutre AR)', lambda p: p[0] > 3230)):
        sel = [(i, j) for i, j in pts if cond(P0[i, j])]
        if sel:
            pv = [pen[i, j] for i, j in sel]; k = int(np.argmax(pv)); i, j = sel[k]
            out.append(dict(zone=nom, maxi=round(float(pv[k])), x=round(float(P0[i, j][0])), y=round(float(P0[i, j][1])), z=round(float(P0[i, j][2]))))
    return out
# ---------- gréement : mâts, colliers, livardes rangées, haubans : à l'intérieur de la toile (traverse) ou dehors
def hauteur_toile(P, x, y):                            # toile au-dessus de (x, y) : interpolation sur le maillage (plus haut point dans 20 mm)
    d = np.hypot(P[:, :, 0] - x, P[:, :, 1] - y); m = d < 25
    return float(P[:, :, 2][m].max()) if m.any() else None
def traverse(pts, P):
    dedans = []
    for x, y, z in pts:
        zt = hauteur_toile(P, x, y)
        if zt is not None and z < zt: dedans.append((round(x), round(y), round(z)))
    return dedans
RIG = {}
for n in V:
    if n.endswith('_babord') and n.startswith(('mat_', 'collier_pli', 'collier_chemise')) or n == 'livarde_babord_rangee':
        v = V[n]; RIG[n] = v[np.random.default_rng(0).choice(len(v), min(len(v), 600), replace=False)]
HAUB = {'hauban_coffre_av_babord': ((1920, 1202, 1175), (49, 1002, 458)), 'hauban_coffre_ar_babord': ((2074, 1217, 1168), (2688, 1187, 297)),
        'hauban_coffre_collier_poutre_babord': ((2000, 1058, 1194), (2087, 1, 675))}
for n, (a, b) in HAUB.items():
    RIG[n] = np.array([np.array(a) + (np.array(b) - np.array(a)) * s for s in np.linspace(0, 1, 120)])
RIG['tube_colliers'] = np.array([(2085, y, 1194) for y in np.linspace(0, 1078, 60)])
rig = {}
for n, pts in RIG.items():
    d0, d1 = traverse(pts, P0), traverse(pts, P1)
    rig[n] = dict(dans_naturelle=len(d0), dans_drapee=len(d1), exemple=(d1 or d0)[:1])
# ---------- hauteur : têtes assises au milieu du trampoline et sur les bancs
def haut(x, y, z0):
    zt = hauteur_toile(P1, x, y); return None if zt is None else round(zt - z0)
heads = {f'au-dessus du trampoline x {x}': haut(x, 0, 580.0) for x in (2600, 2900, 3100, 3400)}
heads['au-dessus de l\'assise x 2450, y 961 (tete assise : H 936, F 832)'] = haut(2450, 961, 685.0)
couvre = {}
for nom, (x, y) in {'coffre milieu x 1650': (1650, 0), 'coffre milieu x 1800': (1800, 0), 'capot x 1900': (1900, 300), 'joue x 1800': (1800, 1115), 'joue x 2400': (2400, 1115),
                    'joue x 3000': (3000, 1115), 'accoudoir x 3100': (3100, 1000), 'pointe joue x 1620': (1620, 1115)}.items():
    zt = hauteur_toile(P1, x, y); couvre[nom] = None if zt is None else round(zt - dessus(x, y))
def zone_box(x0, x1, y0, y1):
    m = (np.abs(P0[:, :, 1]) >= y0) & (np.abs(P0[:, :, 1]) <= y1) & (P0[:, :, 0] >= x0) & (P0[:, :, 0] <= x1) & (pen > 0)
    if not m.any(): return 0
    k = np.unravel_index(np.argmax(np.where(m, pen, -1e9)), pen.shape)
    return dict(maxi=round(float(pen[k])), pt=[round(float(v)) for v in P0[k]])
detail = {'barre du moteur': zone_box(1780, 1840, 0, 30), 'potence et bout du tube': zone_box(1950, 2125, 980, 1080),
          'dessus du coffre contre la joue': zone_box(1765, 1950, 900, 1110), 'accoudoirs': zone_box(3025, 3225, 790, 1110),
          'assise et dossier': zone_box(2125, 3025, 790, 1110), 'longeron et poutre AR': zone_box(3225, 4150, 0, 1130)}
info = dict(detail_traverse=detail, tente=dict(L=L_, W=W_, h=h_), pieds=dict(ar=[XR, yc, round(zr)], av=[round(xf), yc, round(zf)], inclinaison_deg=round(th, 1),
            plan=round(XR - xf), arceau=round(ARC[0]['L']), angle_pied=round(ARC[0]['ang'])),
            sommet=round(float(P1[:, :, 2].max())), sommet_naturel=round(float(P0[:, :, 2].max())), aire_naturelle=round(aire(N0), 2), aire_drapee=round(aire(N1), 2),
            traverse_naturelle=zones(pen > 0, pen), gréement=rig, tetes=heads, garde_dessus=couvre)
json.dump(info, open(OUT + NOM + '.json', 'w'), ensure_ascii=False, indent=1)
# maillages pour la page (toile drapée, arceaux)
def maillage(P, pas=2):
    I_ = list(range(0, NU + 1, pas)); J_ = list(range(0, NV + 1, pas))
    Vv = [P[i, j] for i in I_ for j in J_]; Tt = []; n = len(J_)
    for a_ in range(len(I_) - 1):
        for b_ in range(n - 1):
            p = a_ * n + b_; Tt += [p, p + n + 1, p + n, p, p + 1, p + n + 1]   # sens : normales vers l'extérieur (s de l'arrière vers l'avant)
    return np.array(Vv), Tt
def tube(pts, r, nc=8):
    P = np.array(pts, float); Vv, Tt = [], []
    for i, p in enumerate(P):
        d = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]; d /= np.linalg.norm(d)
        a = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
        e1 = np.cross(d, a); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
        for k in range(nc):
            t_ = 2 * math.pi * k / nc; Vv.append(p + r * (math.cos(t_) * e1 + math.sin(t_) * e2))
    for i in range(len(P) - 1):
        for k in range(nc):
            a, b = i * nc + k, i * nc + (k + 1) % nc; Tt += [a, b, b + nc, a, b + nc, a + nc]
    return np.array(Vv), Tt
Vt, Tt = maillage(P1)
meshes = [dict(n='tente_toile', v=np.round(Vt.ravel(), 1).tolist(), t=Tt)]
for k, a in enumerate(ARC):
    pts = boat(a['pts'][::8, 0], a['pts'][::8, 1], a['pts'][::8, 2])
    Va, Ta = tube(pts, RA); meshes.append(dict(n=f'tente_arceau_{k + 1}', v=np.round(Va.ravel(), 1).tolist(), t=Ta))
json.dump(meshes, open(OUT + NOM + '_3d.json', 'w'), separators=(',', ':'))
print(json.dumps(info, ensure_ascii=False))
