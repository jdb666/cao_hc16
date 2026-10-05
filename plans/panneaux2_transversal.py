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
tv = k['moteur']['transversal']; fe = tv['fente']
ring = lambda pts: Polygon(pts).buffer(0)
parts = []
def add(ref, nom, ep, poly, qte=1, note="", mat="CP okoumé"):
    parts.append(dict(ref=ref, nom=nom, ep=ep, poly=poly, qte=qte, note=note, mat=mat))

# ---------- profil du coffre ----------
NT, NF = 90, 12
def prof_pt(i, zb_, zt_=ZT):
    if i <= NT:
        t = math.pi / 2 * i / NT
        return (XCOL - AF * math.cos(t), zb_ + (zt_ - zb_) * math.sin(t))
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
def dev_point(A3, A2, B2, xp, v):
    xs = [pt[0] for pt in A3]
    j = max(0, min(len(xs) - 2, int(np.searchsorted(xs, xp) - 1)))
    f = (xp - xs[j]) / (xs[j + 1] - xs[j]) if xs[j + 1] != xs[j] else 0
    a = A2[j] + f * (A2[j + 1] - A2[j]); bb = B2[j] + f * (B2[j + 1] - B2[j])
    return tuple(a + v * (bb - a))
tr = k['trappe']
v0, v1 = (abs(tr['y1']) - CPL) / (WI - CPL), (abs(tr['y0']) - CPL) / (WI - CPL)
hx = np.linspace(tr['x0'], tr['x1'], 40)
capot = ring([dev_point(A3s, A2s, B2s, x, v0) for x in hx] + [dev_point(A3s, A2s, B2s, x, v1) for x in reversed(hx)])
add('C5', 'Bordé central (avant arrondi + dessus)', 6, bord_c, note="cylindrique : se cintre sans torsion")
add('C6', 'Bordé latéral bâbord', 6, bord_s, note="légère torsion (≈ 5°) : 10 mm de surcote au chant bas")
add('C7', 'Bordé latéral tribord, découpe du capot', 6, bord_s.difference(capot), note="la découpe donne le capot C8")
add('C8', 'Capot de chargement (chute de C7)', 6, capot, note="hiloire et joint ; ouverture sur toute la largeur du compartiment")

# ---------- fond : plat central + deux pans ----------
LF = XA - XF
WS = math.hypot(WI - CPL, ZBS - ZBC); ss = WS / (WI - CPL)
fx0, fx1 = fe['x0'] - XF, LF          # la découpe va jusqu'au chant arrière (le volet vient contre la face arrière)
enc = tv['encoche_arbre']; ye = fe['y0'] - 10 + enc          # bord du volet côté arbre
add('C1', 'Fond central (plat)', 6, box(0, 0, LF, 2 * CPL).difference(box(fx0, fe['y0'] + CPL, fx1, 2 * CPL)), note="fente de bascule : le volet V1 la ferme")
add('C2', 'Fond latéral bâbord (pan)', 6, box(0, 0, LF, WS).difference(box(fx0, 0, fx1, (fe['y1'] - CPL) * ss)))
add('C3', 'Fond latéral tribord (pan)', 6, box(0, 0, LF, WS))
add('V1.1', 'Volet de fond, partie plate', 6, box(0, 0, fx1 - fx0, CPL - ye), note="charnière sur le chant arrière ; fente de l'arbre laissée ouverte")
add('V1.2', 'Volet de fond, partie en pente', 6, box(0, 0, fx1 - fx0, (fe['y1'] - CPL) * ss), note="collée à V1.1 à l'angle du fond, bande de verre")

# ---------- face arrière ----------
dz = ZBS - ZBC
add('C4', 'Face arrière', 6, ring([(-WI, dz), (-CPL, 0), (CPL, 0), (WI, dz), (WI, ZTS - ZBC), (CPT, ZT - ZBC), (-CPT, ZT - ZBC), (-WI, ZTS - ZBC)]), note="haut polygonal : plat au milieu, pentes jusqu'aux colliers ; vidanges en bas")

# ---------- cloisons ----------
def section_int(y):
    zi = zb(y) + E; a, h = AF - E, (zt(y) - E) - zi
    return ring([(XA - E, zi)] + [(XCOL - a * math.cos(t), zi + h * math.sin(t)) for t in np.linspace(0, math.pi / 2, 60)] + [(XA - E, zt(y) - E)])
for i, yc in enumerate(k['cloisons_y'], 1):
    sec = affinity.translate(section_int(yc), -(XCOL - AF + E), -(zb(yc) + E))
    add(f'C9.{i}', f'Cloison y = {yc:+d}', 6, sec, note=("sépare la soute moteur du compartiment de la caisse" if yc < 0 else "ferme la soute moteur côté bâbord"))

# ---------- joues ----------
AR = XR - XCOL; BJ = ZTS - ZBS
jp = [(XCOL - AF * math.cos(t), ZBS + BJ * math.sin(t)) for t in np.linspace(0, math.pi / 2, 70)]
jp += [(XCOL + AR * math.sin(t), ZBS + BJ * math.cos(t)) for t in np.linspace(0, math.pi / 2, 90)[1:]]
zc_ = zpoutre(WI + EF / 2)
encp = unary_union([Point(p['poutre_av_x'], zc_).buffer(RPOU, 48), box(p['poutre_av_x'] - RPOU, ZBS - 5, p['poutre_av_x'] + RPOU, zc_)])
add('J1', 'Joue (coffre + dossier)', 9, affinity.translate(ring(jp).difference(encp), -XF, -ZBS), qte=2, note="encoche en U : se pose sur la poutre avant ; demi-collier boulonné en haut, au droit du mât")

# ---------- bancs ----------
Lb = XR - XB0
add('B1', 'Assise de banc (couvercle)', 9, box(0, 0, Lb, WI - b['y_int']), qte=2, note="arêtes longues arrondies R20 ; charnières côté joue")
add('B2', 'Côté intérieur de banc', 6, box(0, 0, Lb, b['hauteur'] - b['ep_assise']), qte=2)
yl_in = b['y_int'] + b['ep_cotes']; yl_lon = b['longeron_y'] - b['encoche_longeron_r']
add('B3', 'Fond de banc (entre côté et longeron)', 6, box(0, 0, Lb - 2 * b['ep_cotes'], yl_lon - yl_in), qte=2)
ext = box(0, 0, WI - yl_in, b['hauteur'] - b['ep_assise'])
cy, cz = b['longeron_y'] - yl_in, b['poutre_z'] - b['plan_z']
ext = ext.difference(unary_union([Point(cy, cz).buffer(b['encoche_longeron_r'], 32), box(cy - b['encoche_longeron_r'], -5, cy + b['encoche_longeron_r'], cz)]))
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
zpl_b = max(zb(y0b), zb(y1b)) + E + bt['jeu_cale']
h0, h1 = zpl_b - (zb(y0b) + E), zpl_b - (zb(y1b) + E)
add('S1', 'Cale de batterie (2 épaisseurs collées)', 9, ring([(0, 0), (bt['bac'][0], 0), (bt['bac'][0], h1), (0, h0)]), qte=4, note=f"met le bac de niveau sur le pan du fond : {h0:.0f} côté joue, {h1:.0f} côté axe")

# ---------- chaise pivotante ----------
xpl1 = tv['x_arbre'] - k['moteur']['recul_arbre']
zpl1 = tv['charniere_z'] - tv['bride_sous_charniere']
fl_w, fl_h = tv['planche_demi_larg'] + tv['charniere_decalage'] + 25, tv['charniere_z'] + 25 - (zpl1 - tv['planche_h'])
add('M1', 'Planche de serrage de la bride', tv['planche_ep'], box(0, 0, 2 * tv['planche_demi_larg'], tv['planche_h']), note="massif dur (chêne, iroko)", mat="massif")
fl = box(0, 0, fl_w, fl_h).difference(Point(25, fl_h - 25).buffer(8.5, 24))
add('M2', 'Flasque porte-palier de la chaise', tv['flasque_ep'], fl, note="collée-vissée devant la planche ; trou de l'axe Ø 17", mat="CP 21 ou massif")
lb = xpl1 - tv['planche_ep'] - tv['flasque_ep'] - tv['palier_av_x'] + 15
add('M3', 'Bras de charnière', 30, box(0, 0, lb, 40), note="relie la flasque au palier avant ; alésage Ø 17 à l'avant", mat="massif dur")

INFO = dict(zts=ZTS, cpt=CPT, xcol=XCOL, af=AF, wi=WI, lb=Lb, zb=zb, prof_pt=prof_pt, NI=NI, A3c=A3c, B3c=B3c, A3s=A3s, B3s=B3s, A2c=A2c, B2c=B2c, A2s=A2s, B2s=B2s, v0=v0, v1=v1)
if __name__ == '__main__':
    tot = {}
    for q in parts:
        x0, y0_, x1, y1 = q['poly'].bounds
        a = q['poly'].area / 1e6 * q['qte']; tot[(q['mat'], q['ep'])] = tot.get((q['mat'], q['ep']), 0) + a
        print(f"{q['ref']:5s} {q['nom']:44s} {q['mat']:14s} ép {q['ep']:>2} × {q['qte']}  {x1-x0:7.0f} × {y1-y0_:5.0f}   {a:5.2f} m²")
    print({f"{m_} {e}": round(v, 2) for (m_, e), v in tot.items()})
