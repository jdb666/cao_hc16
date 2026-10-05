"""Développés des panneaux du coffre HC16 Rando (cousu-collé), d'après cotes.yaml."""
import math, json, yaml
import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity

C = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
k, m = C['coffre'], C['mats']
qa = math.radians(m['quete_deg'])
XCOL = m['x_pied'] + m['collier_hauteur'] * math.sin(qa)
W = k['largeur']; EF = k['ep_flasque']; WI = W / 2 - EF
XA, XF = k['face_ar_x'], k['avant_x']
ZBC, ZBS, ZT = k['fond_z'], k['fond_z_cotes'], k['dessus_z']
AF = XCOL - XF
E = k['ep_bordé']
b = k['bancs']; XR = XA + b['longueur']; XB0 = b.get('x_debut', XA)
zb = lambda y: ZBC + (ZBS - ZBC) * min(1.0, abs(y) / WI)
p = C['plateforme']
zpoutre = lambda y: p['poutre_z'] + p.get('poutre_av_fleche', 0) * (1 - (y / (p['poutre_longueur'] / 2)) ** 2)
RPOU = p['poutre_diam'] / 2 + 4

def ring(pts):
    return Polygon(pts).buffer(0)

parts = []
def add(ref, nom, ep, poly, qte=1, note=""):
    parts.append(dict(ref=ref, nom=nom, ep=ep, poly=poly, qte=qte, note=note))

# ---------- bordé (avant arrondi + dessus plat), développé par triangulation ----------
NT, NF = 90, 12
def surf(i, v):
    # i : indice le long du profil ; v : 0 = milieu (y=0), 1 = joue (|y| = WI)
    zb_ = ZBC + (ZBS - ZBC) * v
    if i <= NT:
        t = math.pi / 2 * i / NT
        return np.array([XCOL - AF * math.cos(t), WI * v, zb_ + (ZT - zb_) * math.sin(t)])
    s = (i - NT) / NF
    return np.array([XCOL + s * (XA - XCOL), WI * v, ZT])
NI = NT + NF
A3 = [surf(i, 0) for i in range(NI + 1)]; B3 = [surf(i, 1) for i in range(NI + 1)]
def place(p1, p2, d1, d2, side_ref):
    # point à d1 de p1 et d2 de p2, du côté opposé à side_ref
    dx = p2 - p1; L = np.linalg.norm(dx); ex = dx / L; ey = np.array([-ex[1], ex[0]])
    a = (d1 ** 2 - d2 ** 2 + L ** 2) / (2 * L); h = math.sqrt(max(0.0, d1 ** 2 - a ** 2))
    c1, c2 = p1 + a * ex + h * ey, p1 + a * ex - h * ey
    return c1 if np.dot(c1 - p1, ey) * np.dot(side_ref - p1, ey) <= 0 else c2
A2 = [np.array([0.0, 0.0])]; B2 = [np.array([np.linalg.norm(B3[0] - A3[0]), 0.0])]
err = 0.0
for i in range(NI):
    # triangle (A_i, B_i, A_i+1) puis (A_i+1, B_i, B_i+1)
    a1 = place(A2[i], B2[i], np.linalg.norm(A3[i + 1] - A3[i]), np.linalg.norm(A3[i + 1] - B3[i]), A2[i] + np.array([0, -1.0]) if i == 0 else A2[i - 1])
    b1 = place(a1, B2[i], np.linalg.norm(B3[i + 1] - A3[i + 1]), np.linalg.norm(B3[i + 1] - B3[i]), A2[i])
    A2.append(a1); B2.append(b1)
    err = max(err, abs(np.linalg.norm(b1 - A2[i]) - np.linalg.norm(B3[i + 1] - A3[i])))
DEV_ERR = err
bord_pts = [tuple(q) for q in A2] + [tuple(q) for q in reversed(B2)]
bordé = ring(bord_pts)
def dev_point(xp, v):
    # point du bordé à l'abscisse x (plan) et à la fraction v de la largeur -> coordonnées développées
    xs = [pt[0] for pt in A3]
    j = max(0, min(NI - 1, int(np.searchsorted(xs, xp) - 1)))
    f = (xp - xs[j]) / (xs[j + 1] - xs[j]) if xs[j + 1] != xs[j] else 0
    a = A2[j] + f * (A2[j + 1] - A2[j]); bb = B2[j] + f * (B2[j + 1] - B2[j])
    return tuple(a + v * (bb - a))
tr = k['trappe']
v0, v1 = abs(tr['y1']) / WI, abs(tr['y0']) / WI
hx = np.linspace(tr['x0'], tr['x1'], 40)
capot = ring([dev_point(x, v0) for x in hx] + [dev_point(x, v1) for x in reversed(hx)])
add('C4', 'Bordé bâbord (avant arrondi + dessus)', 6, bordé)
add('C5', 'Bordé tribord, découpe du capot', 6, bordé.difference(capot), note="la découpe donne le capot C6")
add('C6', 'Capot de chargement (chute de C5)', 6, capot, note="reprendre avec hiloire et joint")

# ---------- fond en V : deux demi-fonds plans ----------
LF, WF = XA - XF, math.hypot(WI, ZBS - ZBC)
fond = box(0, 0, LF, WF)
mo = k['moteur']['arriere']; nn = mo['niche']; ym = mo['y']
s = WF / WI
ouv = box(nn['x0'] - XF, (ym - nn['demi_y']) * s, nn['x1'] - XF, (ym + nn['demi_y']) * s)
add('C1', 'Demi-fond bâbord (ouverture niche moteur)', 6, fond.difference(ouv))
add('C2', 'Demi-fond tribord', 6, fond)

# ---------- face arrière (plan x = XA) ----------
add('C3', 'Face arrière', 6, ring([(-WI, ZBS - ZBC), (0, 0), (WI, ZBS - ZBC), (WI, ZT - ZBC), (-WI, ZT - ZBC)]), note="orifices de vidange en bas, de part et d'autre du milieu")

# ---------- cloisons (section intérieure à y) ----------
def section_int(y):
    zi = zb(y) + E; a, h = AF - E, (ZT - E) - zi
    pts = [(XA - E, zi)] + [(XCOL - a * math.cos(t), zi + h * math.sin(t)) for t in np.linspace(0, math.pi / 2, 60)] + [(XA - E, ZT - E)]
    return ring(pts)
for i, yc in enumerate(k['cloisons_y'], 1):
    sec = section_int(yc)
    sec = affinity.translate(sec, -(XCOL - AF + E), -(zb(yc) + E))
    add(f'C7.{i}', f'Cloison y = {yc:+d}', 6, sec, note=("dans la gouttière centrale du fond en V" if yc == 0 else "compartiment extérieur étanche : réserve de flottabilité"))

# ---------- niche moteur (boîte ouverte en dessous) ----------
en = nn['ep']
for nom, yw in (("côté axe", ym - nn['demi_y'] - en / 2), ("côté joue", ym + nn['demi_y'] + en / 2)):
    sec = section_int(yw).intersection(box(nn['x0'] - en, 0, XA - E, nn['z_haut'] + en))
    add(f'C8.{1 if nom=="côté axe" else 2}', f'Niche moteur, flanc {nom}', 6, affinity.translate(sec, -(nn['x0'] - en), -(zb(yw) + E)))
# face avant (plan x = x0 - en/2) : du fond jusqu'au bordé
xw = nn['x0'] - en / 2
def ztop_int(x, y):
    zi = zb(y) + E; a, h = AF - E, (ZT - E) - zi
    u = (XCOL - x) / a
    return ZT - E if u <= 0 else zi + h * math.sqrt(max(0, 1 - u * u))
ys = np.linspace(ym - nn['demi_y'], ym + nn['demi_y'], 20)
fa = ring([(y, zb(y) + E) for y in ys] + [(y, min(ztop_int(xw, y), nn['z_haut'])) for y in reversed(ys)])
add('C8.3', 'Niche moteur, face avant', 6, affinity.translate(fa, -(ym - nn['demi_y']), -min(zb(y) + E for y in ys)))
# dessus (z = z_haut + en/2) : de la rencontre avec le bordé à la face arrière
zd = nn['z_haut'] + en / 2
def x_at_z(z, y):
    zi = zb(y) + E; a, h = AF - E, (ZT - E) - zi
    return XCOL - a * math.sqrt(max(0, 1 - ((z - zi) / h) ** 2))
de = ring([(max(x_at_z(zd, y), nn['x0'] - en), y) for y in ys] + [(XA - E, y) for y in reversed(ys)])
add('C8.4', 'Niche moteur, dessus', 6, affinity.translate(de, -min(max(x_at_z(zd, y), nn['x0'] - en) for y in ys), -(ym - nn['demi_y'])))

# ---------- joues (CP 9) ----------
AR = XR - XCOL; BJ = ZT - ZBS
jp = [(XCOL - AF * math.cos(t), ZBS + BJ * math.sin(t)) for t in np.linspace(0, math.pi / 2, 70)]
jp += [(XCOL + AR * math.sin(t), ZBS + BJ * math.cos(t)) for t in np.linspace(0, math.pi / 2, 90)[1:]]
joue = ring(jp)
zc_ = zpoutre(WI + EF / 2)
enc = unary_union([Point(p['poutre_av_x'], zc_).buffer(RPOU, 48), box(p['poutre_av_x'] - RPOU, ZBS - 5, p['poutre_av_x'] + RPOU, zc_)])
joue = affinity.translate(joue.difference(enc), -XF, -ZBS)
add('J1', 'Joue (coffre + dossier)', 9, joue, qte=2, note="encoche en U : se pose sur la poutre avant ; perçages des pattes de collier à reporter")

# ---------- bancs ----------
Lb = XR - XB0
add('B1', 'Assise de banc (couvercle)', 9, box(0, 0, Lb, WI - b['y_int']), qte=2, note="arêtes longues arrondies R20 ; charnières côté joue")
add('B2', 'Côté intérieur de banc', 6, box(0, 0, Lb, b['hauteur'] - b['ep_assise']), qte=2)
yl_in = b['y_int'] + b['ep_cotes']; yl_lon = b['longeron_y'] - b['encoche_longeron_r']
add('B3', 'Fond de banc (entre côté et longeron)', 6, box(0, 0, Lb - 2 * b['ep_cotes'], yl_lon - yl_in), qte=2)
ext = box(0, 0, WI - yl_in, b['hauteur'] - b['ep_assise'])
cy = b['longeron_y'] - yl_in; cz = b['poutre_z'] - b['plan_z']
ext = ext.difference(unary_union([Point(cy, cz).buffer(b['encoche_longeron_r'], 32), box(cy - b['encoche_longeron_r'], -5, cy + b['encoche_longeron_r'], cz)]))
add('B4', 'Extrémité de banc (encoche longeron)', 6, ext, qte=4)

# ---------- pylônes sous les joues (CP 9) ----------
import sys; sys.path.insert(0, '/home/claude/cao')
import hc16_rando as H
H.PONT_CFG.update(C['coques']); H.CFG_MAT.update(C['mats'])
py = k['pylones']; ep9 = py['ep']
z0 = H.interp_pont(m['x_pied'], C['coques']['entraxe'] / 2) + 1
y_ext, y_int = WI, WI - py['dy']
h_ext, h_int = zb(y_ext) - z0, zb(y_int) - z0
add('P1', 'Pylône, face longitudinale', 9, box(0, 0, py['dx'], (h_ext + h_int) / 2), qte=4, note=f"pied à ajuster au bombé du pont ; hauteur {h_int:.0f} côté axe, {h_ext:.0f} côté joue")
add('P2', 'Pylône, face transversale', 9, ring([(0, 0), (py['dy'] - 2 * ep9, 0), (py['dy'] - 2 * ep9, h_ext), (0, h_int)]), qte=4, note="tête biaise : suit la pente du fond en V")

# ---------- chaise et carter moteur ----------
car = mo['carter']
zc_pl = mo['bride_axe_z'] - mo['bride_axe_sur_planche']; zbas = zc_pl - mo['planche_h']
xb1 = mo['x_arbre'] - mo['bride_axe_devant_arbre'] - mo['bride_axe_derriere_planche']
Lj = xb1 - car['x_av']
for nom, y0c in (("bâbord", ym + mo['demi_passage']), ("tribord", ym - mo['demi_passage'] - mo['ep_joue'])):
    hj = min(zb(y0c), zb(y0c + mo['ep_joue'])) - zbas
    add(f'M2.{1 if nom=="bâbord" else 2}', f'Joue de chaise {nom}', mo['ep_joue'], box(0, 0, Lj, hj), note="CP 25 (ou 2 × 12) ou massif, sous le fond du coffre")
yl = mo['demi_passage']
add('M3', 'Fond de carter', 9, box(0, 0, xb1 - mo['planche_ep'] - car['x_av'], 2 * yl), note="trous d'évacuation")
add('M4', 'Face avant de carter', 9, box(0, 0, 2 * yl, min(zb(ym - yl), zb(ym + yl)) - zbas - car['ep']))
add('M1', 'Planche de serrage de la bride', mo['planche_ep'], box(0, 0, 2 * mo['demi_larg'], mo['planche_h']), note="massif dur (chêne, iroko)")

INFO = dict(dev_err=DEV_ERR, xcol=XCOL, af=AF, wi=WI, lb=Lb, h_pyl=(h_int, h_ext))
if __name__ == '__main__':
    print(f"écart max du développé du bordé (non-développabilité) : {DEV_ERR:.2f} mm")
    tot = {}
    for q in parts:
        x0, y0_, x1, y1 = q['poly'].bounds
        a = q['poly'].area / 1e6 * q['qte']; tot[q['ep']] = tot.get(q['ep'], 0) + a
        print(f"{q['ref']:5s} {q['nom']:44s} ép {q['ep']:>2} × {q['qte']}  {x1-x0:7.0f} × {y1-y0_:5.0f}   {a:5.2f} m²")
    print({e: round(v, 2) for e, v in tot.items()})
