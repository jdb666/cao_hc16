"""Plan de découpe du coffre HC16 Rando (état du 08/10/2026 : coffre raccourci devant au ras des joues, coffre à ancre, deux batteries au fond du coffre de chaque côté du puits ; collier et emplanture en CP).
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
NON_IMBRIQUE = ('TR', 'TG')   # trappes de C4 et des caissons de rangement : chutes de C4 et du capot (même contour que le trou), pas de place à part
EP_BORDE = {'B': 4, 'F': 4, 'C4': 4, 'P': 4}   # (JD 09/10) tout le bordé en CP 4 + verre (avant : fond, C4 et poches en CP 6)
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
def normale(f):
    vs, ts = f.tessellate(0.5, 0.2)
    if ts:
        a, b, c3 = max(ts, key=lambda t: (vs[t[1]] - vs[t[0]]).cross(vs[t[2]] - vs[t[0]]).Length)
        c = (vs[a] + vs[b] + vs[c3]) * (1 / 3)
    else:
        c = f.Center()
    n = f.normalAt(c)
    return c, n

def deplier(co):
    """Panneaux du bordé d'un solide de peau (coque du coffre, couvercle du coffre à ancre) : facettes extérieures regroupées et dépliées."""
    faces = co.Faces()
    ext = []
    for i, f in enumerate(faces):
        c, n = normale(f)
        if f.Area() < 1:
            continue
        if any(INT.isInside(c - n * d_, 0.05) for d_ in (e + 1.0, 1.6 * e, 2.5 * e)):   # vers l'intérieur, on traverse le bordé et on tombe dans le coffre
            ext.append(i)                                  # (09/10) plusieurs profondeurs : avec le fond à 25°, la peau du fond avant fait plus de 7 mm d'épaisseur normale
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
    # (09/10) plus de borne au bord du plat du fond (±150) : le fond se sépare déjà à l'angle du V (10°), et la borne coupait
    # le bordé avant et le couvercle du coffre à ancre (±250) en trois morceaux
    BORNES = sorted({b for c_ in (cpt_, cpa_) if c_ > 1 for b in (-c_, c_)})
    def zone(i):
        return sum(CTR[i][1] > b for b in BORNES)
    def plane_(i):                                         # plane en fait (le loft réglé peut donner des surfaces B-spline planes)
        if faces[i].geomType() == 'PLANE':
            return True
        vs, _ = faces[i].tessellate(0.1, 0.1)
        return bool(vs) and max(abs(float((npv(v) - CTR[i]) @ NRM[i])) for v in vs) < 0.05
    PLAN = {i: plane_(i) for i in ext}
    def meme_panneau(a, b):
        return angle(a, b) < SEUIL and zone(a) == zone(b)
    panneau_de, panneaux = {}, []
    for i in sorted(ext, key=lambda i: -faces[i].Area()):
        if i in panneau_de:
            continue
        comp, pile = [i], [i]; panneau_de[i] = len(panneaux)
        while pile:
            a = pile.pop()
            for b, P, Q in voisins[a]:
                if b not in panneau_de and meme_panneau(a, b):
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
    # (08/10) panneaux plans et coplanaires qui se touchent (faces du loft séparées aux stations ±360, ±450) : un seul panneau ;
    # le fond en V de ±250 à la joue sortait en trois morceaux (F1, F5, F6). Les panneaux cintrés (facettes planes mais non
    # coplanaires entre elles) ne sont pas concernés : ils restent coupés aux stations
    def plan_comp(comp):
        if not all(PLAN[i] for i in comp) or any(angle(comp[0], j) > 0.3 for j in comp):
            return None
        return NRM[comp[0]], float(NRM[comp[0]] @ CTR[comp[0]])
    def proj2d(comp, o, e1, e2):
        return poly2d([[((X - o) @ e1, (X - o) @ e2) for X in t] for i in comp for t in tris3d(i)])
    PLC = [plan_comp(cp) for cp in panneaux]
    chef = list(range(len(panneaux)))
    def tete(a):
        while chef[a] != a:
            a = chef[a]
        return a
    for ia in range(len(panneaux)):
        for ib in range(ia + 1, len(panneaux)):
            if PLC[ia] is None or PLC[ib] is None or tete(ia) == tete(ib):
                continue
            (na, da), (nb, db) = PLC[ia], PLC[ib]
            if float(na @ nb) < math.cos(math.radians(0.3)) or abs(da - db) > 0.3:
                continue
            e1_, e2_ = base(panneaux[ia][0]); o_ = CTR[panneaux[ia][0]]
            if proj2d(panneaux[ia], o_, e1_, e2_).distance(proj2d(panneaux[ib], o_, e1_, e2_)) < 0.3:
                chef[tete(ib)] = tete(ia)
    if any(chef[i] != i for i in range(len(chef))):
        grp_ = {}
        for i_, cp in enumerate(panneaux):
            grp_.setdefault(tete(i_), []).extend(cp)
        panneaux = list(grp_.values())
        panneau_de = {f: ip for ip, cp in enumerate(panneaux) for f in cp}
    DEV = []
    for ip, comp in enumerate(panneaux):
        r = comp[0]; e1, e2 = base(r); o = CTR[r]
        T = {r: lambda X, o=o, e1=e1, e2=e2: np.array([(X - o) @ e1, (X - o) @ e2])}
        if plan_comp(comp) is not None:                    # panneau plan : le dépliage est la projection sur son plan
            T = {i: T[r] for i in comp}
        C2 = {r: T[r](CTR[r])}
        file_, vu = [r], set(T)
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

    return DEV

DEV = deplier(D['coffre_coque'])
DEV_CV = deplier(D['coffre_capot']) if 'coffre_capot' in D else []        # (07/10) couvercle du coffre à ancre : bordé central au-dessus de z 450

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
CAP_ = k.get('capot_arriere') or {}
def sous_capot(d):                                        # (09/10) capot horizontal à 810 : la peau qu'il remplace laisse des copeaux sans épaisseur
    return bool(CAP_) and len(d['comp']) == 1 and d['xmin'] >= CAP_['x0'] - 10 and max(abs(d['ymin']), abs(d['ymax'])) <= CAP_['demi_y'] + 5 \
        and d['zmin'] >= CAP_['z_c4'] - 12
for d in DEV:
    if d['aire3d'] < 2000:
        continue
    if sous_capot(d):
        print('copeau sous le capot écarté', round(d['xmin']), round(d['xmax']), round(d['ymin']), round(d['ymax']), round(d['aire3d']))
        continue
    if min(dims(d['poly'])) < 25 and len(d['comp']) == 1:  # (08/10) biseau de la peau coupée par le plan du capot (4 mm vus à 15° = 16 de large) : chant, pas un panneau
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
for d in DEV_CV:                                           # (07/10) couvercle du coffre à ancre, développé comme le bordé
    if d['aire3d'] < 2000 or sous_capot(d):
        continue
    d['ref'] = 'CV'
    ajoute('CV', "Couvercle du coffre à ancre : bordé central au-dessus de z 450, cintré, découpé pour le puits", EP_BORDE['B'], d['poly'], qte=1,
           note=f"y {d['ymin']:+.0f} → {d['ymax']:+.0f}, x {d['xmin']:.0f} → {d['xmax']:.0f}, {len(d['comp'])} facettes")
DEV = DEV + [d for d in DEV_CV if d.get('ref')]

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
    (r'^couple_coffre_(babord|tribord)_331$', 'K331', 'Couple ±331, de la cloison du puits à C4, et son accroche au travers de C4', 6, 1),
    (r'^couple_coffre_(babord|tribord)_420$', 'K420', 'Couple plein ±420 (côté du caisson de rangement), de la cloison du puits à C4, et son accroche au travers de C4', 6, 1),
    (r'^couple_coffre_(babord|tribord)_850$', 'K850', 'Couple ±850 et son accroche, au travers de C4', 9, 1),
    (r'^coffre_batterie_avant$', 'CA', 'Caisse batterie : cloison avant', 6, 1),
    (r'^coffre_batterie_(babord|tribord)$', 'CB', 'Caisse batterie : côté', 6, 1),
    (r'^coffre_cloison_moteur$', 'CM', 'Cloison avant du puits, jusqu\'aux couples ±420 (ferme le coffre à ancre et l\'avant des caissons de rangement)', 6, 1),
    (r'^coffre_ancre_(babord|tribord)$', 'AN', 'Cloison du coffre à ancre (±250), de l\'avant à la cloison du puits', 6, 1),
    (r'^accoudoir_(babord|tribord)_(avant|arriere)$', 'AF', 'Accoudoir : face avant ou arrière, collée sur l\'assise et contre la joue', 6, 1),
    (r'^accoudoir_(babord|tribord)_interieur$', 'AI', 'Accoudoir : côté intérieur, collé sur l\'assise', 6, 1),
    (r'^accoudoir_(babord|tribord)_couvercle$', 'AV', 'Accoudoir : couvercle amovible sur joint, deux grenouillères', 6, 1),
    (r'^banc_(babord|tribord)_lisse_\d$', 'BL', 'Lisse sous la rive intérieure de l\'assise, entre deux couples', 9, 1),
    (r'^banc_(babord|tribord)_jambe_\d_(av|ar)$', 'BJ', 'Joue de jambe de couple de banc (une de chaque côté de la jambe)', 9, 1),
    (r'^glissiere_sabot_(babord|tribord)$', 'GS', 'Sabot de la glissière du tube des colliers (70 × 121 × 60, 6 × CP 10)', 10, 6),
    (r'^glissiere_berceau_(babord|tribord)$', 'GB', 'Berceau en U du tube, sur le sabot : 4 × CP 9 collés, gorge creusée, garniture PEHD 3', 9, 4),
    (r'^glissiere_poteau_(haut|bas)_(babord|tribord)_(av|ar|int)$', 'GP', 'Poteau caisson de la glissière : paroi CP 9 (trois parois collées contre la joue, au-dessus et au-dessous de l\'assise)', 9, 1),
    (r'^coffre_hiloire$', 'HI', 'Hiloire (brise-lames) en haut de l\'arrondi avant : bande CP 9 de 30, penchée à 45° vers l\'avant, collée sur le dessus (congé époxy) ; pied biseauté et bouts coupés d\'onglet en place', 9, 1),   # (09/10 après-midi : plus de couvercle du coffre à ancre, la bande droite n'est plus coupée à ±250)
    (r'^glissiere_potence_(babord|tribord)$', 'GQ', 'Potence de la glissière, sur le poteau, au-dessus de C4 jusqu\'au berceau PEHD (40 = 4 × CP 10)', 10, 4),
    (r'^glissiere_bague_(babord|tribord)$', 'GA', 'Bague du poteau de la glissière, collée sous le dessus du coffre (18 = 2 × CP 9)', 9, 2),
    (r'^tape_piece_angle_(babord|tribord)$', 'TP', 'Tape de fermeture contre la joue, au-dessus de la pièce d\'angle AV, découpée à son profil (posée après le coffre)', 6, 1),
    (r'^moteur_puits$', 'PM', 'Paroi du puits moteur et son accroche (±131), au travers de C4', 6, 1),
    (r'^coffre_table$', 'TA', 'Table (sur la caisse)', 10, 1),
    (r'^coffre_capot_arriere$', 'CR', 'Capot arrière horizontal (dessus des caissons de rangement), découpé pour la tête du moteur, CP 4 + verre', 4, 1),
    (r'^coffre_capot_joue_(babord|tribord)$', 'CJ', 'Joue triangulaire du capot arrière', 4, 1),
    (r'^coffre_trappe_c4_\d$', 'TR', 'Trappe du compartiment extérieur, dans C4 (dans la chute de C4), CP 4 + verre', 4, 1),
    (r'^coffre_trappe_rangement_(babord|tribord)$', 'TG', 'Trappe du caisson de rangement (dans la chute du capot), CP 4 + verre', 4, 1),
    (r'^accroche_poutre_\d$', 'AC', 'Accroche sur la poutre AV', 9, 1),
    (r'^banc_(babord|tribord)_assise$', 'AS', 'Assise du banc', 9, 1),
    (r'^banc_(babord|tribord)_couple_\d$', 'BC', 'Couple de banc', 9, 1),
    (r'^banc_(babord|tribord)_machoire_\d$', 'MA', 'Mâchoire de banc', 9, 1),
    (r'^batterie_cale_(av|ar)(_babord|_tribord)?$', 'CL', 'Cale de batterie, taillée au fond en pente et en V (40 = 4 × CP 10)', 10, 4),
    (r'^moteur_tableau$', 'PL', 'Planche de la pince moteur (40 = 4 × CP 10)', 10, 4),
    (r'^pylone_renfort_(babord|tribord)$', 'SR', 'Semelle sur les tubes carbone (18 = 2 × CP 9)', 9, 2),
    (r'^semelle_(babord|tribord)$', 'SM', 'Semelle de pied de mât, sous l\'emplanture (18 = 2 × CP 9)', 9, 2),
    (r'^emplanture_joue_(int|ext)_(babord|tribord)$', 'JE', 'Joue de l\'emplanture, percée Ø 8 tous les 20, collée sur la semelle et stratifiée', 10, 1),
    (r'^emplanture_cale_(babord|tribord)$', 'CE', 'Cale de l\'emplanture, triangle pointe en bas (30 = 3 × CP 10), percée Ø 8', 10, 3),
    (r'^collier_pli\d_(babord|tribord)$', 'CO', 'Collier du mât, pli de CP 10 (7 plis collés et stratifiés par collier)', 10, 1),
    (r'^semelle_tubes_(babord|tribord)$', 'ST', 'Semelle des tubes carbone du coffre, sur le pont (18 = 2 × CP 9)', 9, 2),
    (r'^renfort_pont_(babord|tribord)$', 'RP', 'Renfort de pont (8 = 2 × CP 4, cintré en place)', 4, 2),
    (r'^livarde_collier_(babord|tribord)$', 'LC', 'Collier ouvert de la livarde, collé sur la joue (20 = 2 × CP 10)', 10, 2),
    (r'^livarde_godet_(babord|tribord)$', 'LG', 'Godet de la livarde, pli percé Ø 34, collé sur la joue', 10, 1),
    (r'^livarde_godet_fond_(babord|tribord)$', 'LF', 'Godet de la livarde, pli du fond', 10, 1),
]
def bande(sh, h):
    """(09/10) Hiloire : le loft (une face par section) n'a pas de grande face plane ; bande droite de la longueur du
    segment (axe principal des sommets) et de la hauteur de l'hiloire ; le pied est biseauté et ajusté en place."""
    V = np.array([npv(v.Center()) for v in sh.Vertices()]); c = V.mean(axis=0)
    ax = np.linalg.svd(V - c, full_matrices=False)[2][0]; t = (V - c) @ ax
    L = float(t.max() - t.min())
    return Polygon([(0, 0), (L, 0), (L, h), (0, h)]), 9.0
vus = {}
for nom in sorted(D):
    for motif, ref, lib, ep, plis in REGLES:
        if re.match(motif, nom):
            sh = D[nom]
            sols = sh.Solids() if hasattr(sh, 'Solids') else [sh]
            for j, so in enumerate(sols):
                if so.Volume() < 100:
                    continue
                g, ep_m = bande(so, k['hiloire']['h'] / math.cos(math.radians(k['hiloire'].get('inclinaison_deg', 0)))) if ref == 'HI' else plate(so)   # largeur de la bande penchée
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
