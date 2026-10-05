"""Développés des panneaux du coffre HC16 Rando — version moteur transversal, fond polygonal à 3 segments."""
import math, yaml, sys
import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
sys.path.insert(0, '/home/claude/cao')
import hc16_rando as H

C = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
k, m = C['coffre'], C['mats']
qa = math.radians(m['quete_deg'])
XCOL = m['x_pied'] + m['collier_hauteur'] * math.sin(qa)
W = k['largeur']; EF = k['ep_flasque']; WI = W / 2 - EF
XA, XF = k['face_ar_x'], k['avant_x']
ZBC, ZBS, ZT, CPL = k['fond_z'], k['fond_z_cotes'], k['dessus_z'], k['fond_plat_demi']
AF = XCOL - XF; E = k['ep_bordé']
b = k['bancs']; XR = XA + b['longueur']; XB0 = b.get('x_debut', XA)
zb = lambda y: ZBC + (ZBS - ZBC) * max(0.0, min(1.0, (abs(y) - CPL) / (WI - CPL)))
ZC = m['z_pied'] + m['collier_hauteur'] * math.cos(qa)
ZTS = ZC + k['dessus_cotes_au_dessus_collier'] if 'dessus_cotes_au_dessus_collier' in k else ZT
CPT = k.get('dessus_plat_demi', CPL)
assert CPT == CPL, "les développés supposent la même cassure au fond et au dessus"
zt = lambda y: ZT + (ZTS - ZT) * max(0.0, min(1.0, (abs(y) - CPT) / (WI - CPT)))
p = C['plateforme']
zpoutre = lambda y: p['poutre_z'] + p.get('poutre_av_fleche', 0) * (1 - (y / (p['poutre_longueur'] / 2)) ** 2)
RPOU = p['poutre_diam'] / 2 + 4
am = k['moteur']['arriere']; NN = am['niche']; YM = am['y']; ENC = am['encoche_c4']
ring = lambda pts: Polygon(pts).buffer(0)
plus_grand = lambda g: max(getattr(g, 'geoms', [g]), key=lambda q: q.area)   # élimine les éclats numériques
parts = []
def add(ref, nom, ep, poly, qte=1, note="", mat="CP okoumé"):
    parts.append(dict(ref=ref, nom=nom, ep=ep, poly=poly, qte=qte, note=note, mat=mat))

# ---------- profil du coffre ----------
NT, NF = 90, 12
def prof_pt(i, zb_, zt_=ZT):
    if i <= NT:
        u = math.pi / 2 * i / NT; h_ = zt_ - zb_
        t = math.atan2(h_ * math.sin(u), H.HREF * math.cos(u))      # pente égale entre stations : bordés développables
        return (XCOL - AF * math.cos(t), zb_ + h_ * math.sin(t))
    s = (i - NT) / NF
    return (XCOL + s * (XA - XCOL), zt_)
NI = NT + NF
def place(p1, p2, d1, d2, side_ref):
    dx = p2 - p1; L = np.linalg.norm(dx); ex = dx / L; ey = np.array([-ex[1], ex[0]])
    a = (d1 ** 2 - d2 ** 2 + L ** 2) / (2 * L); h = math.sqrt(max(0.0, d1 ** 2 - a ** 2))
    c1, c2 = p1 + a * ex + h * ey, p1 + a * ex - h * ey
    return c1 if np.dot(c1 - p1, ey) * np.dot(side_ref - p1, ey) <= 0 else c2
def develop(A3, B3):
    A2 = [np.array([0.0, 0.0])]; B2 = [np.array([np.linalg.norm(B3[0] - A3[0]), 0.0])]
    for i in range(len(A3) - 1):
        a1 = place(A2[i], B2[i], np.linalg.norm(A3[i + 1] - A3[i]), np.linalg.norm(A3[i + 1] - B3[i]), A2[i] + np.array([0, -1.0]) if i == 0 else A2[i - 1])
        b1 = place(a1, B2[i], np.linalg.norm(B3[i + 1] - A3[i + 1]), np.linalg.norm(B3[i + 1] - B3[i]), A2[i])
        A2.append(a1); B2.append(b1)
    return A2, B2
def P3(i, y):
    x, z = prof_pt(i, zb(y), zt(y)); return np.array([x, y, z])
# bordé central (cylindre exact) et bordés latéraux (réglés)
A3c = [P3(i, -CPL) for i in range(NI + 1)]; B3c = [P3(i, CPL) for i in range(NI + 1)]
A2c, B2c = develop(A3c, B3c)
A3s = [P3(i, CPL) for i in range(NI + 1)]; B3s = [P3(i, WI) for i in range(NI + 1)]
A2s, B2s = develop(A3s, B3s)
poly_from = lambda A2, B2: ring([tuple(q) for q in A2] + [tuple(q) for q in reversed(B2)])
bord_c, bord_s = poly_from(A2c, B2c), poly_from(A2s, B2s)
def dev_point(A3, A2, B2, xp, v, B3=None):
    B3 = B3 if B3 is not None else A3
    xs = [a_[0] + v * (b_[0] - a_[0]) for a_, b_ in zip(A3, B3)]          # abscisse du point à la fraction v de la génératrice
    j = max(0, min(len(xs) - 2, int(np.searchsorted(xs, xp) - 1)))
    f = (xp - xs[j]) / (xs[j + 1] - xs[j]) if xs[j + 1] != xs[j] else 0
    a = A2[j] + f * (A2[j + 1] - A2[j]); bb = B2[j] + f * (B2[j + 1] - B2[j])
    return tuple(a + v * (bb - a))
tr = k['trappe']
v0, v1 = 0.0, (tr['y1'] - CPL) / (WI - CPL)          # trappe du dessus : bande côté milieu des bordés latéraux
hx = np.linspace(tr['x0'], min(tr['x1'], XA), 40)
capot = ring([dev_point(A3s, A2s, B2s, x, v0, B3s) for x in hx] + [dev_point(A3s, A2s, B2s, x, v1, B3s) for x in reversed(hx)])
# trappe de batterie dans C5 (cylindrique) : un rectangle du développé
hxc = np.linspace(tr['x0'], tr['x1'], 40)
u0, u1 = (tr['y0'] + CPL) / (2 * CPL), (tr['y1'] + CPL) / (2 * CPL)
t1 = ring([dev_point(A3c, A2c, B2c, x, u0, B3c) for x in hxc] + [dev_point(A3c, A2c, B2c, x, u1, B3c) for x in reversed(hxc)])
add('C5', 'Bordé central (avant arrondi + dessus)', 6, plus_grand(bord_c.difference(t1)), note="cylindrique : se cintre sans torsion ; ouverture de la trappe de batterie T1")
add('T1', 'Trappe de batterie (chute de C5)', 6, t1, note="découper après cintrage et stratification : le couvercle garde son cintre ; hiloire 25 mm, joint, charnière avant, 2 verrous")
add('C6', 'Bordé latéral bâbord', 6, bord_s, note="développable : génératrices obliques, se cintre sans torsion")
add('C7', 'Bordé latéral tribord', 6, bord_s, note="développable : génératrices obliques, se cintre sans torsion")

# ---------- fond : plat central + deux pans ----------
LF = XA - XF
WS = math.hypot(WI - CPL, ZBS - ZBC); ss = WS / (WI - CPL)
fx0, fx1 = NN['x0'] - XF, LF          # ouverture du puits jusqu'au chant arrière
add('C1', 'Fond central (plat)', 6, box(0, 0, LF, 2 * CPL))
add('C2', 'Fond latéral bâbord (pan), ouverture du puits', 6, box(0, 0, LF, WS).difference(box(fx0, (YM - NN['demi_y'] - CPL) * ss, fx1, (YM + NN['demi_y'] - CPL) * ss)), note="le moteur passe par l'ouverture ; la chaise se fixe dessous")
add('C3', 'Fond latéral tribord (pan)', 6, box(0, 0, LF, WS))

# ---------- face arrière ----------
dz = ZBS - ZBC
c4 = ring([(-WI, dz), (-CPL, 0), (CPL, 0), (WI, dz), (WI, ZTS - ZBC), (CPT, ZT - ZBC), (-CPT, ZT - ZBC), (-WI, ZTS - ZBC)])
TR4 = k.get('trappes_c4') or []
portes = [box(t['y0'], t['z0'] - ZBC, t['y1'], t['z1'] - ZBC) for t in TR4]
c4 = c4.difference(box(YM - ENC['demi_y'], -5, YM + ENC['demi_y'], ENC['z'] - ZBC))
for pt_ in portes: c4 = c4.difference(pt_)
add('C4.1', 'Face arrière', 6, plus_grand(c4), note="haut polygonal ; encoche de l'arbre basculé côté bâbord ; deux trappes de visite au-dessus de la poutre")
for i_, pt_ in enumerate(portes, 2):
    add(f'C4.{i_}', f"Porte de visite {'tribord' if TR4[i_ - 2]['y0'] < 0 else 'bâbord'} (chute de C4.1)", 6, pt_, note="sur cadre intérieur 25 mm, joint, deux verrous")

# ---------- cloisons ----------
def section_int(y):
    zi = zb(y) + E; a, h = AF - E, (zt(y) - E) - zi
    return ring([(XA - E, zi)] + [(XCOL - a * math.cos(t), zi + h * math.sin(t)) for t in np.linspace(0, math.pi / 2, 60)] + [(XA - E, zt(y) - E)])
for i, yc in enumerate(k['cloisons_y'], 1):
    sec = affinity.translate(section_int(yc), -(XCOL - AF + E), -(zb(yc) + E))
    add(f'C9.{i}', f'Cloison y = {yc:+d}', 6, sec, note=("sépare la soute moteur du compartiment de la caisse" if yc < 0 else "ferme la soute moteur côté bâbord"))

# ---------- puits du moteur ----------
def section_top(y, x):
    zi = zb(y) + E; a, h = AF - E, (zt(y) - E) - zi
    c_ = (XCOL - x) / a
    return zi + h * math.sqrt(max(0.0, 1 - c_ * c_)) if c_ > 0 else zt(y) - E
en = NN['ep']
for i, yw in enumerate((YM - NN['demi_y'] - en, YM + NN['demi_y']), 1):
    ymid = yw + en / 2
    sec = section_int(ymid).intersection(box(NN['x0'] - en, -1e4, XA - E, 1e4))
    add(f'N1.{i}', f'Paroi longitudinale du puits (y = {ymid:+.0f})', 6, affinity.translate(sec, -(NN['x0'] - en), -(zb(ymid) + E)), note="du fond jusqu'au bordé ; isole le puits du reste du coffre")
ys_ = np.linspace(YM - NN['demi_y'] - en, YM + NN['demi_y'] + en, 30)
xw = NN['x0'] - en / 2
n2 = ring([(y - ys_[0], zb(y) + E) for y in ys_] + [(y - ys_[0], section_top(y, xw)) for y in reversed(ys_)])
add('N2', 'Paroi avant du puits', 6, affinity.translate(n2, 0, -(zb(ys_[0]) + E)), note="bas en pente : suit le pan du fond")

# ---------- joues ----------
AR = XR - XCOL; BJ = ZTS - ZBS
jp = [(XCOL - AF * math.cos(t), ZBS + BJ * math.sin(t)) for t in np.linspace(0, math.pi / 2, 70)]
jp += [(XCOL + AR * math.sin(t), ZBS + BJ * math.cos(t)) for t in np.linspace(0, math.pi / 2, 90)[1:]]
zc_ = zpoutre(WI + EF / 2)
# encoche en U de la poutre avant : profil en goutte (queue vers l'arrière) + 4 mm, ouverte vers le bas
PPO = Polygon([(p['poutre_av_x'] + u, zc_ + v) for u, v in H.PROFILS['poutre']]).buffer(4, join_style=2)
encp = unary_union([PPO, box(PPO.bounds[0], ZBS - 5, PPO.bounds[2], zc_)])
add('J1', 'Joue (coffre + dossier)', 9, affinity.translate(ring(jp).difference(encp), -XF, -ZBS), qte=2, note="encoche en U au profil de la poutre (goutte, queue vers l'arrière) : se pose sur la poutre avant ; demi-collier boulonné en haut, au droit du mât")

# ---------- bancs ----------
Lb = XR - XB0
add('B1', 'Assise de banc (couvercle)', 9, box(0, 0, Lb, WI - b['y_int']), qte=2, note="arêtes longues arrondies R20 ; charnières côté joue")
add('B2', 'Côté intérieur de banc', 6, box(0, 0, Lb, b['hauteur'] - b['ep_assise']), qte=2)
yl_in = b['y_int'] + b['ep_cotes']
# longeron en goutte (queue vers l'intérieur) dans le plan (y, z), + 4 mm
PLO = Polygon([(b['longeron_y'] - u, b['poutre_z'] + v) for u, v in H.PROFILS['longeron']]).buffer(4, join_style=2)
_bande = PLO.intersection(box(0, b['plan_z'] - 1, 5000, b['plan_z'] + b['ep_fond'] + 1))
yl_lon = _bande.bounds[0] if not _bande.is_empty else b['longeron_y'] - b['encoche_longeron_r']      # le fond s'arrête au longeron
add('B3', 'Fond de banc (entre côté et longeron)', 6, box(0, 0, Lb - 2 * b['ep_cotes'], yl_lon - yl_in), qte=2)
ext = box(0, 0, WI - yl_in, b['hauteur'] - b['ep_assise'])
cy, cz = b['longeron_y'] - yl_in, b['poutre_z'] - b['plan_z']
plo = affinity.translate(PLO, -yl_in, -b['plan_z'])
ext = ext.difference(unary_union([plo, box(plo.bounds[0], -5, plo.bounds[2], cz)]))
add('B4', 'Extrémité de banc (encoche longeron)', 6, ext, qte=4)

# ---------- pylônes ----------
H.PONT_CFG.update(C['coques']); H.CFG_MAT.update(C['mats'])
py = k['pylones']; ep9 = py['ep']
z0 = H.interp_pont(m['x_pied'], C['coques']['entraxe'] / 2) + 1
y_in, y_out = WI - py['dy'], WI
h_in, h_out = zb(y_in) - z0, zb(y_out) - z0
add('P1', 'Pylône, face longitudinale côté axe', 9, box(0, 0, py['dx'], zb(y_in + ep9) - z0), qte=2, note="pied à ajuster au bombé du pont")
add('P2', 'Pylône, face longitudinale côté joue', 9, box(0, 0, py['dx'], h_out), qte=2, note="pied à ajuster au bombé du pont")
add('P3', 'Pylône, face transversale', 9, ring([(0, 0), (py['dy'] - 2 * ep9, 0), (py['dy'] - 2 * ep9, zb(y_out - ep9) - z0), (0, zb(y_in + ep9) - z0)]), qte=4, note="tête biaise : suit la pente du fond")

# ---------- cales de la batterie ----------
bt = k['batterie']
y0b, y1b = bt['y_ext'], bt['y_ext'] + bt['bac'][0]
LI = bt.get('lisses'); zpl_b = ZBC + E + (0 if bt.get('appui_direct') else LI['h'])
if not bt.get('appui_direct'):
    add('S1', "Lisse d'appui du bac", LI['h'], box(0, 0, bt['bac'][1], LI['larg']), qte=2, mat="massif", note="collées sur C1 à y ±150 : le bac déborde sur les pans")

# ---------- chaise fixe et carter (sous le fond) ----------
XP = am['x_arbre'] - am['bride_axe_devant_arbre']; ZP = am['bride_axe_z']
XB1 = XP - am['bride_axe_derriere_planche']; ZC_ = ZP - am['bride_axe_sur_planche']; ZBAS = ZC_ - am['planche_h']
XAV = am['carter']['x_av']; YL = am['demi_passage']
add('M1', 'Planche de serrage de la bride', am['planche_ep'], box(0, 0, 2 * am['demi_larg'], am['planche_h']), note="massif dur (chêne, iroko) ; entre les joues de chaise", mat="massif")
for i, (nom, y0c) in enumerate((("bâbord", YM + YL), ("tribord", YM - YL - am['ep_joue'])), 1):
    zloc = min(zb(y0c), zb(y0c + am['ep_joue']))
    add(f'M2.{i}', f'Joue de chaise {nom}', am['ep_joue'], box(0, 0, XB1 - XAV, zloc - ZBAS), note="collée-boulonnée sous le fond, de part et d'autre de l'ouverture du puits", mat="massif dur")
zloc_c = min(zb(YM - YL), zb(YM + YL))
add('M3', 'Fond du carter', am['carter']['ep'], box(0, 0, XB1 - am['planche_ep'] - XAV, 2 * YL), note="ferme le dessous devant la planche : la tête basculée y repose")
add('M4', 'Face avant du carter', am['carter']['ep'], box(0, 0, 2 * YL, zloc_c - ZBAS - am['carter']['ep']))

INFO = dict(zts=ZTS, cpt=CPT, xcol=XCOL, af=AF, wi=WI, lb=Lb, zb=zb, prof_pt=prof_pt, NI=NI, A3c=A3c, B3c=B3c, A3s=A3s, B3s=B3s, A2c=A2c, B2c=B2c, A2s=A2s, B2s=B2s, v0=v0, v1=v1)
if __name__ == '__main__':
    tot = {}
    for q in parts:
        x0, y0_, x1, y1 = q['poly'].bounds
        a = q['poly'].area / 1e6 * q['qte']; tot[(q['mat'], q['ep'])] = tot.get((q['mat'], q['ep']), 0) + a
        print(f"{q['ref']:5s} {q['nom']:44s} {q['mat']:14s} ép {q['ep']:>2} × {q['qte']}  {x1-x0:7.0f} × {y1-y0_:5.0f}   {a:5.2f} m²")
    print({f"{m_} {e}": round(v, 2) for (m_, e), v in tot.items()})
