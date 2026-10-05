"""Plan de découpe du coffre HC16 Rando (état du 30/09/2026).
Tout vient du modèle CAO (v_pleine_0.yaml) :
- bordé : les faces extérieures de coffre_coque (toutes planes : loft réglé entre stations) sont regroupées en panneaux
  (angle entre facettes voisines < SEUIL : la planche se cintre ; au-delà : bouchain, joint collé-stratifié),
  puis dépliées exactement, facette par facette, autour des arêtes communes ; découpes comprises ;
- pièces planes : plus grande face plane de chaque pièce, projetée dans son plan (trous compris) ;
- épaisseurs de plus de 12 : en plis de CP 9 ou CP 10 collés ;
imbrication par épaisseur sur panneaux 2 500 × 1 220 (imbrication.py), DXF par planche, JSON pour la page."""
import sys, math, json, os, re, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/cao'); sys.path.insert(0, '/home/claude/cao/plans')
import yaml, numpy as np, cadquery as cq, ezdxf
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from shapely import affinity
import hc16_rando as H, imbrication as I
from OCP.TopExp import TopExp
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape

V = cq.Vector
NON_IMBRIQUE = ('TR',)   # trappes de C4 : c'est la chute de C4 (même contour que le trou), pas de place à part
EP_BORDE = {'B': 4, 'F': 6, 'C4': 6, 'P': 6}   # « Bordé cintré : 4 mm ; fond 6 ; face AR 6 » (SYNTHESE, construction)
SEUIL = 8.0            # degrés : au-dessous, deux facettes voisines sont dans la même planche (cintrée)
OUT = os.environ.get('DECOUPE_OUT', '/home/claude/cao/plans')
cfg = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
A = H.build(cfg)
D = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children}
k = cfg['coffre']; e = k['ep_bordé']
INT = H.COFFRE_CACHE['int']

def npv(v): return np.array([v.x, v.y, v.z])

def poly2d(tris):
    g = unary_union([Polygon(t).buffer(0.02, join_style=2) for t in tris if Polygon(t).area > 1e-6])
    return g.buffer(-0.02, join_style=2)

def plus_grand(g):
    return max(getattr(g, 'geoms', [g]), key=lambda q: q.area)

# ---------------------------------------------------------------- bordé : faces extérieures
co = D['coffre_coque']
faces = co.Faces()
def normale(f):
    vs, ts = f.tessellate(0.5, 0.2)
    if ts:
        a, b, c3 = max(ts, key=lambda t: (vs[t[1]] - vs[t[0]]).cross(vs[t[2]] - vs[t[0]]).Length)
        c = (vs[a] + vs[b] + vs[c3]) * (1 / 3)
    else:
        c = f.Center()
    n = f.normalAt(c)
    return c, n
ext = []
for i, f in enumerate(faces):
    c, n = normale(f)
    if f.Area() < 1:
        continue
    if INT.isInside(c - n * (e + 1.0), 0.05):         # vers l'intérieur, on traverse le bordé et on tombe dans le coffre
        ext.append(i)
EXT = set(ext)
emap = TopTools_IndexedDataMapOfShapeListOfShape()
TopExp.MapShapesAndAncestors_s(co.wrapped, TopAbs_EDGE, TopAbs_FACE, emap)
wrapped = [f.wrapped for f in faces]
def idx(tf):
    for j, w in enumerate(wrapped):
        if w.IsSame(tf):
            return j
    return None
voisins = {i: [] for i in ext}                         # i -> [(j, P, Q)]
for ie in range(1, emap.Extent() + 1):
    ed = emap.FindKey(ie); lst = emap.FindFromIndex(ie)
    fs = []
    for tf in lst:
        j = idx(tf)
        if j is not None and j in EXT and j not in fs:
            fs.append(j)
    if len(fs) == 2:
        vs = cq.Shape.cast(ed).Vertices()
        if len(vs) < 2:
            continue
        P, Q = npv(vs[0].Center()), npv(vs[-1].Center())
        if np.linalg.norm(Q - P) < 1e-3:
            continue
        voisins[fs[0]].append((fs[1], P, Q)); voisins[fs[1]].append((fs[0], P, Q))
NRM = {i: npv(normale(faces[i])[1]) for i in ext}
CTR = {i: npv(normale(faces[i])[0]) for i in ext}
def angle(i, j):
    return math.degrees(math.acos(max(-1.0, min(1.0, float(NRM[i] @ NRM[j])))))
# panneaux : composantes connexes par arêtes à faible angle, sans traverser les stations du loft (±250, ±360) :
# chaque tronçon entre deux stations est développable, mais deux tronçons voisins ne le sont pas ensemble
# (le dépliage d'un seul tenant du bordé avant + dessus perdait 3 % de surface) ; y = 0 se traverse (même profil de part et d'autre)
cpl_ = k.get('fond_plat_demi', 0.0); cpt_ = k.get('dessus_plat_demi', cpl_); cpa_ = k.get('avant_plat_demi', cpl_)
BORNES = sorted({b for c_ in (cpl_, cpt_, cpa_) if c_ > 1 for b in (-c_, c_)})
def zone(i):
    return sum(CTR[i][1] > b for b in BORNES)
panneau_de, panneaux = {}, []
for i in sorted(ext, key=lambda i: -faces[i].Area()):
    if i in panneau_de:
        continue
    comp, pile = [i], [i]; panneau_de[i] = len(panneaux)
    while pile:
        a = pile.pop()
        for b, P, Q in voisins[a]:
            if b not in panneau_de and angle(a, b) < SEUIL and zone(a) == zone(b):
                panneau_de[b] = len(panneaux); comp.append(b); pile.append(b)
    panneaux.append(comp)
# dépliage de chaque panneau
def base(i):
    n = NRM[i]; t = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = t - n * (t @ n); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
    return e1, e2
def tris3d(i):
    vs, ts = faces[i].tessellate(0.1, 0.1)
    P = [npv(v) for v in vs]
    return [[P[a], P[b], P[c]] for a, b, c in ts]
DEV = []
for ip, comp in enumerate(panneaux):
    r = comp[0]; e1, e2 = base(r); o = CTR[r]
    T = {r: lambda X, o=o, e1=e1, e2=e2: np.array([(X - o) @ e1, (X - o) @ e2])}
    C2 = {r: T[r](CTR[r])}
    file_, vu = [r], {r}
    ecart = 0.0
    while file_:
        a = file_.pop(0)
        for b, P, Q in voisins[a]:
            if b in vu or panneau_de.get(b) != ip:
                continue
            p2, q2 = T[a](P), T[a](Q)
            ee = (Q - P) / np.linalg.norm(Q - P); nb = NRM[b]; bb = np.cross(nb, ee)
            if (CTR[b] - P) @ bb < 0:
                bb = -bb
            e2d = (q2 - p2) / np.linalg.norm(q2 - p2); b2d = np.array([-e2d[1], e2d[0]])
            if (C2[a] - p2) @ b2d > 0:
                b2d = -b2d
            T[b] = lambda X, P=P, ee=ee, bb=bb, p2=p2, e2d=e2d, b2d=b2d: p2 + ((X - P) @ ee) * e2d + ((X - P) @ bb) * b2d
            C2[b] = T[b](CTR[b]); vu.add(b); file_.append(b)
    tr2 = []
    a3 = 0.0
    for i in comp:
        for t in tris3d(i):
            tr2.append([tuple(T[i](X)) for X in t]); a3 += np.linalg.norm(np.cross(t[1] - t[0], t[2] - t[0])) / 2
    g = poly2d(tr2)
    xs = [CTR[i] for i in comp]; bb3 = np.array(xs)
    P3_ = np.array([X for i in comp for t in tris3d(i) for X in t])
    DEV.append(dict(comp=comp, poly=g, aire3d=a3, n=np.mean([NRM[i] for i in comp], axis=0), c=bb3.mean(axis=0),
                    xmin=P3_[:, 0].min(), xmax=P3_[:, 0].max(), ymin=P3_[:, 1].min(), ymax=P3_[:, 1].max(), zmin=P3_[:, 2].min(), zmax=P3_[:, 2].max()))

def dims(g):
    c = list(g.minimum_rotated_rectangle.exterior.coords)
    return tuple(sorted((round(math.dist(c[0], c[1])), round(math.dist(c[1], c[2])))))
def cote(y0, y1):
    if y0 > -1 and y1 < 1 or (y0 < -1 and y1 > 1):
        return 'milieu'
    return 'bâbord' if y0 >= -1 else 'tribord'
parts = []
def ajoute(ref, nom, ep, poly, qte=1, note='', plis=None):
    poly = plus_grand(poly) if isinstance(poly, MultiPolygon) else poly
    # orientation de moindre encombrement
    mrr = poly.minimum_rotated_rectangle; c = list(mrr.exterior.coords)
    ang = math.degrees(math.atan2(c[1][1] - c[0][1], c[1][0] - c[0][0]))
    poly = affinity.rotate(poly, -ang, origin='centroid')
    x0, y0, x1, y1 = poly.bounds
    if (y1 - y0) > (x1 - x0):
        poly = affinity.rotate(poly, 90, origin='centroid')
    x0, y0, _, _ = poly.bounds
    poly = affinity.translate(poly, -x0, -y0)
    parts.append(dict(ref=ref, nom=nom, ep=ep, poly=poly, qte=qte, note=note, plis=plis))

# nommage des panneaux du bordé ; les panneaux symétriques (bâbord / tribord) sont regroupés
DEV.sort(key=lambda d: (-d['aire3d']))
n_b, grp_b = {}, []
for d in DEV:
    if d['aire3d'] < 2000:
        continue
    n = d['n']; n = n / np.linalg.norm(n)
    poche = d['xmin'] > 1950 and min(abs(d['ymin']), abs(d['ymax'])) > 900 and d['aire3d'] < 0.06e6
    if poche:
        typ, lettre = 'Paroi de poche (pièce d\'angle)', 'P'
    elif n[0] > 0.9:
        typ, lettre = 'Face arrière C4', 'C4'
    elif n[2] < -0.6:
        typ, lettre = 'Fond', 'F'
    else:
        typ, lettre = 'Bordé (avant cintré + dessus)', 'B'
    sig = (lettre, d['poly'].area, dims(d['poly']))
    for gr in grp_b:
        if gr['sig'][0] == lettre and abs(gr['sig'][1] - sig[1]) < 0.005 * sig[1] and all(abs(a - b) <= 2 for a, b in zip(gr['sig'][2], sig[2])):
            gr['d'].append(d); break
    else:
        grp_b.append(dict(sig=sig, typ=typ, lettre=lettre, d=[d]))
for gr in grp_b:
    lettre = gr['lettre']; n_b[lettre] = n_b.get(lettre, 0) + 1
    ref = (lettre if n_b[lettre] == 1 else f"C4{'abcdefgh'[n_b[lettre] - 1]}") if lettre == 'C4' else f"{lettre}{n_b[lettre]}"
    d0 = gr['d'][0]
    ou = ' et '.join(dict.fromkeys(cote(d['ymin'], d['ymax']) for d in gr['d']))
    pos = '; '.join(f"y {d['ymin']:+.0f} → {d['ymax']:+.0f}, x {d['xmin']:.0f} → {d['xmax']:.0f}, {len(d['comp'])} facettes" for d in gr['d'])
    ep_b = EP_BORDE.get(lettre, e)                     # construction : bordé cintré CP 4, fond et C4 CP 6 (SYNTHESE)
    ajoute(ref, f"{gr['typ']} ({ou})", ep_b, d0['poly'], qte=len(gr['d']), note=pos)
    for d in gr['d']:
        d['ref'] = ref

# ---------------------------------------------------------------- pièces planes
def plate(sh):
    fg = max(sh.Faces(), key=lambda f: f.Area())               # plus grande face (courbe pour une pièce cintrée : renfort de pont)
    fp = [f for f in sh.Faces() if f.geomType() == 'PLANE']
    f = max(fp, key=lambda f: f.Area()) if fp and max(q.Area() for q in fp) > 0.5 * fg.Area() else fg   # face plane si elle compte (collier du fourreau)
    c, n = normale(f); n = npv(n); c3 = npv(c)
    t = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 0, 1.0])
    e1 = t - n * (t @ n); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
    tri = []
    vs, ts = f.tessellate(0.1, 0.1)
    P = [npv(v) for v in vs]
    for a, b, cc in ts:
        tri.append([((P[q] - c3) @ e1, (P[q] - c3) @ e2) for q in (a, b, cc)])
    ep = max((npv(v.Center()) - c3) @ n for v in sh.Vertices()) - min((npv(v.Center()) - c3) @ n for v in sh.Vertices())
    return poly2d(tri), abs(ep)
REGLES = [   # (motif, ref, nom, épaisseur de CP, plis)
    (r'^joue_(babord|tribord)$', 'J', 'Joue (dossier du banc)', 9, 1),
    (r'^couple_coffre_(babord|tribord)_331$', 'K331', 'Couple ±331 (côté caisse prolongé) et son accroche, au travers de C4', 6, 1),
    (r'^couple_coffre_(babord|tribord)_850$', 'K850', 'Couple ±850 et son accroche, au travers de C4', 9, 1),
    (r'^coffre_batterie_avant$', 'CA', 'Caisse batterie : cloison avant', 6, 1),
    (r'^coffre_batterie_(babord|tribord)$', 'CB', 'Caisse batterie : côté', 6, 1),
    (r'^coffre_cloison_moteur$', 'CM', 'Cloison du puits (arrière de la caisse)', 6, 1),
    (r'^moteur_puits$', 'PM', 'Paroi du puits moteur et son accroche (±131), au travers de C4', 6, 1),
    (r'^coffre_table$', 'TA', 'Table', 10, 1),
    (r'^coffre_trappe_c4_\d$', 'TR', 'Trappe de visite C4 (dans la chute de C4)', 6, 1),
    (r'^accroche_poutre_\d$', 'AC', 'Accroche sur la poutre AV', 9, 1),
    (r'^banc_(babord|tribord)_assise$', 'AS', 'Assise du banc', 9, 1),
    (r'^banc_(babord|tribord)_couple_\d$', 'BC', 'Couple de banc', 9, 1),
    (r'^banc_(babord|tribord)_machoire_\d$', 'MA', 'Mâchoire de banc', 9, 1),
    (r'^batterie_cale_(av|ar)$', 'CL', 'Cale du bac de batterie (40 = 4 × CP 10)', 10, 4),
    (r'^moteur_tableau$', 'PL', 'Planche de la pince moteur (40 = 4 × CP 10)', 10, 4),
    (r'^pylone_renfort_(babord|tribord)$', 'SR', 'Semelle sur les tubes carbone (18 = 2 × CP 9)', 9, 2),
    (r'^semelle_(babord|tribord)$', 'SM', 'Semelle de pied de mât (18 = 2 × CP 9)', 9, 2),
    (r'^renfort_pont_(babord|tribord)$', 'RP', 'Renfort de pont (8 = 2 × CP 4, cintré en place)', 4, 2),
    (r'^livarde_collier_(babord|tribord)$', 'LC', 'Collier ouvert de la livarde, collé sur la joue (20 = 2 × CP 10)', 10, 2),
    (r'^livarde_godet_(babord|tribord)$', 'LG', 'Godet de la livarde, pli percé Ø 34, collé sur la joue', 10, 1),
    (r'^livarde_godet_fond_(babord|tribord)$', 'LF', 'Godet de la livarde, pli du fond', 10, 1),
]
vus = {}
for nom in sorted(D):
    for motif, ref, lib, ep, plis in REGLES:
        if re.match(motif, nom):
            sh = D[nom]
            sols = sh.Solids() if hasattr(sh, 'Solids') else [sh]
            for j, so in enumerate(sols):
                if so.Volume() < 100:
                    continue
                g, ep_m = plate(so)
                vus.setdefault(ref, []).append((nom, g, ep_m, lib, ep, plis))
            break
hors = sorted(n for n in D if not any(re.match(m, n) for m, *_ in REGLES))
print('hors plan (achetées, alu, carbone, cordage, gréement, plateforme) :', hors)
# regroupe les pièces identiques (symétriques) : même aire et même encombrement à 1 mm près
for ref, lst in vus.items():
    groupes = []
    for nom, g, ep_m, lib, ep, plis in lst:
        sig = (g.area, dims(g))
        for gr in groupes:
            if abs(gr['sig'][0] - sig[0]) < 0.005 * sig[0] and all(abs(a - b) <= 2 for a, b in zip(gr['sig'][1], sig[1])):
                gr['noms'].append(nom); break
        else:
            groupes.append(dict(sig=sig, g=g, noms=[nom], ep_m=ep_m, lib=lib, ep=ep, plis=plis))
    for n_, gr in enumerate(groupes, 1):
        r_ = ref if len(groupes) == 1 else f"{ref}{n_}"
        ajoute(r_, gr['lib'], gr['ep'], gr['g'], qte=len(gr['noms']) * gr['plis'],
               note=f"épaisseur modèle {gr['ep_m']:.0f} ; " + ', '.join(gr['noms']), plis=gr['plis'])

# ---------------------------------------------------------------- pièces -> pickle, puis imbrication (imbrique3.py)
import pickle
CONTROLE = [dict(ref=d.get('ref'), aire3d=round(d['aire3d'] / 1e6, 4), aire2d=round(d['poly'].area / 1e6, 4)) for d in DEV if d.get('ref')]
for d in DEV:
    if d.get('ref') and abs(d['poly'].area / d['aire3d'] - 1) > 0.002:
        print('ATTENTION dépliage', d['ref'], round(d['aire3d'] / 1e6, 4), round(d['poly'].area / 1e6, 4))
print('panneaux du bordé', [(c['ref'], c['aire3d'], c['aire2d']) for c in CONTROLE])
pickle.dump(dict(parts=parts, controle=CONTROLE, seuil=SEUIL), open(f"{OUT}/pieces.pkl", 'wb'))   # contours exacts : réimbriquer sans reconstruire le modèle
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imbrique3.py')).read())
