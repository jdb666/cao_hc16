"""Maillages three.js de la plateforme HC16 : modèle recalé (cotes.yaml) + modèle précédent (cotes_avant_releves.yaml),
bateau complet (v_pleine_0.yaml), voiles roulées, et relevage du moteur (pièces mobiles à 0°, coupe dans le plan de l'arbre)."""
import sys, json, copy, time, math, yaml
sys.path.insert(0, '/home/claude/cao')
import cadquery as cq
import hc16_rando as H
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

def walk(a):
    for ch in a.children:
        yield ch
        yield from walk(ch)

def forme(ch):
    return ch.obj if not hasattr(ch.obj, 'val') else ch.obj.val()

def maillages(A, tol=2.0):
    out = []
    for ch in walk(A):
        if ch.obj is None:
            continue
        sh = forme(ch)
        V, T = [], []
        for s in (sh if isinstance(sh, list) else [sh]):
            vs, ts = s.tessellate(tol, 0.35)
            o = len(V)
            V += [(round(v.x, 1), round(v.y, 1), round(v.z, 1)) for v in vs]
            T += [(a + o, b + o, c + o) for a, b, c in ts]
        bb = sh.BoundingBox()
        out.append(dict(n=ch.name, v=[c for p in V for c in p], t=[i for tr in T for i in tr],
                        bb=[round(x, 1) for x in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)]))
    return out

def projection_xz(sh, tol=1.0):
    """Silhouette d'un solide vu de côté (projection sur xz), en polygones shapely."""
    vs, ts = sh.tessellate(tol, 0.3)
    tri = [Polygon([(vs[i].x, vs[i].z) for i in t]) for t in ts]
    return unary_union([p.buffer(0.05) for p in tri if p.area > 1e-3])

def coupe_y(sh, y0, tol=0.5):
    """Coupe d'un solide par le plan y = y0 (tranche de 0,5 mm projetée sur xz)."""
    bb = sh.BoundingBox()
    if not (bb.ymin < y0 < bb.ymax):
        return None
    tr = sh.intersect(cq.Solid.makeBox(bb.xlen + 20, 0.5, bb.zlen + 20, cq.Vector(bb.xmin - 10, y0 - 0.25, bb.zmin - 10)))
    if tr.Volume() < 1e-3:
        return None
    return projection_xz(tr, tol)

def polys(g, simp=0.4):
    if g is None or g.is_empty:
        return []
    g = g.simplify(simp)
    return [p for p in (g.geoms if isinstance(g, MultiPolygon) else [g]) if p.area > 1]

def chemin(g, simp=0.4):
    """Polygones -> attribut d SVG (y SVG = -z), trous compris (règle evenodd)."""
    d = []
    for p in polys(g, simp):
        for r in [p.exterior] + list(p.interiors):
            c = list(r.coords)[:-1]
            d.append('M' + ' '.join(f"{x:.1f},{-z:.1f}" for x, z in c) + 'Z')
    return ''.join(d)

t0 = time.time()
new = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
old = yaml.safe_load(open('/home/claude/cao/cotes_avant_releves.yaml'))
old = copy.deepcopy(old)
mg = dict(old['coffre']['martingale']); mg.pop('x', None)
old['plateforme']['martingale'] = mg            # l'ancien modèle portait la martingale dans « coffre »
N = maillages(H.build(new, plateforme_seule=True))
O = maillages(H.build(old, plateforme_seule=True), tol=3.0)
# bateau complet (coffre recalé, gréement, haubans), moteur en marche : on ne garde que ce qui n'est pas déjà dans la plateforme
full = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
mo_ = full['coffre']['moteur']; v2 = mo_['vertical2']; v2['levee'] = 0
AF = H.build(full)
PLATE = ('coque_', 'poutre_', 'longeron_', 'piece_angle', 'trampoline', 'martingale', 'safran_', 'barre_', 'pylone_av', 'pylone_ar', 'repere_')
MOB = ('moteur_arbre', 'moteur_tete', 'moteur_barre', 'moteur_nacelle', 'moteur_helice', 'moteur_aileron')   # montent avec l'arbre
FA = maillages(AF, tol=2.5)
F = [o for o in FA if not o['n'].startswith(PLATE) and o['n'] not in MOB]
M = [o for o in FA if o['n'] in MOB]
# bras du tube des colliers : n'existe qu'en position haute
rel = copy.deepcopy(full); rel['coffre']['moteur']['vertical2']['levee'] = v2['levee_max']
BR = [o for o in maillages(H.build(rel), tol=2.0) if o['n'] == 'bras_tube_moteur']
# relevage : coupe dans le plan de l'arbre (y du moteur), silhouettes des pièces mobiles en marche
D = {ch.name: forme(ch) for ch in walk(AF) if ch.obj is not None}
km = full['coffre']['_moteur']; xs, ym = km['x_arbre'], km['y']
fixes = {'coffre': ['coffre_coque'], 'cloisons': ['coffre_cloison_moteur', 'coffre_batterie_avant', 'coffre_caisse_couvercle', 'coffre_table'], 'bac': ['batterie_bac'], 'cellule': ['batterie'],
         'ancre': ['ancre_faisceau', 'ancre_verge', 'ancre_anneau'],
         'tableau': ['moteur_tableau'], 'bride': ['moteur_etrier', 'moteur_bride'], 'poutre': ['poutre_av'], 'trampoline': ['trampoline'], 'tube': ['tube_colliers']}
coupe = {k: chemin(unary_union([g for g in (coupe_y(D[n], ym) for n in ns if n in D) if g is not None])) for k, ns in fixes.items()}
coupe['martingale'] = chemin(unary_union([projection_xz(D[n]) for n in D if n.startswith('martingale')]))
coupe['cheminee'] = chemin(projection_xz(D['moteur_puits']))           # parois de la cheminée, derrière le plan de coupe
coupe['bras'] = chemin(unary_union([projection_xz(forme(ch)) for ch in walk(H.build(rel)) if ch.name == 'bras_tube_moteur']))
sil = {}
for n in MOB:
    if n in D:
        g = projection_xz(D[n], 0.8).simplify(0.6)
        sil[n] = [[[round(x, 1), round(z, 1)] for x, z in list(p.exterior.coords)[:-1]] for p in polys(g, 0.6)]
kc = full['coffre']; g_ = kc['_geom']; bt_ = kc['_batterie']; pu_ = kc['_puits']
BAL = json.load(open('/home/claude/cao/plateforme/balayage_levee.json'))
REL = dict(mode='vertical', levee_max=v2['levee_max'], x_arbre=xs, coupe=coupe, sil=sil,
           geom=dict(xf=g_['avant_milieu'], xf_joue=g_['avant'], xa=kc['face_ar_x'], zb=kc['fond_z'], zt=g_['zt'], xcol=round(g_['xcol'], 1),
                     x0p=g_['fond_pente']['x0'], dm=round(g_['fond_pente'].get('montee_milieu', 0), 1),
                     planche=[round(v, 1) for v in (lambda b: (b.xmin, b.xmax, b.zmin, b.zmax))(D['moteur_tableau'].BoundingBox())] if 'moteur_tableau' in D else None,
                     table=[kc['_table']['x'][0], kc['_table']['x'][1], kc['_table']['z'][1]] if kc.get('_table') else None,
                     bas_pale=km['bas_pale'], bas_aileron=km['bas_aileron'], tete_bas=km['tete_bas'], bride=km['bride'],
                     bac=[bt_['x'][0], bt_['x'][1], round(bt_['z'][0], 1), round(bt_['z'][1], 1)], puits=[pu_['x_int'], kc['face_ar_x'] - kc['ep_bordé']],
                     caisse=[bt_['caisse']['x'][0], bt_['caisse']['x'][1], bt_['caisse']['z_haut']] if bt_.get('caisse') else None,
                     ancre=[kc['_ancre']['x'], kc['_ancre']['z'][1]] if kc.get('_ancre') else None,
                     encoche=v2['encoche_c4_z'], tube=[kc['haubans']['tube_colliers'].get('x', round(g_['xcol'], 1)), kc['haubans']['tube_colliers'].get('z', 1097), kc['haubans']['tube_colliers']['diam'] / 2]),
           balayage=[dict(l=r['l'], zmin=r['zmin'], zmax=r['zmax'], contacts=len(r['hits']),
                          jeux={k: v[0] for k, v in r['jeux'].items()}, qui={k: [v[1], v[2]] for k, v in r['jeux'].items()}) for r in BAL['levees']],
           sortie_bac=BAL['sortie_bac'])
# voiles roulées : rouleau autour du mât et livardes rangées debout devant les mâts
rou = copy.deepcopy(full); rou['voile']['enroulement'] = {'babord': 1, 'tribord': 1}
R = [o for o in maillages(H.build(rou), tol=2.5) if o['n'].startswith(('livarde_', 'voile_roulee'))]
for o in N + O + F + R + M + BR:
    print(f"{o['n']:28s} {len(o['t'])//3:7d} tri  bb {o['bb']}")
print('coupe', {k: len(v) for k, v in coupe.items()}, 'sil', {k: len(v) for k, v in sil.items()})
# gréement réglable (page) : voiles, livardes et écoutes générées en JS à partir des cotes
m_, vo_ = full['mats'], full['voile']; lv_ = vo_['livarde']
a_ = math.radians(m_['quete_deg'])
yyv = (kc.get('yinyang') or {}).get('voiles')
dec = dict(u=round(yyv['dx'] * math.cos(a_) - yyv['dz'] * math.sin(a_), 1), w=round(yyv['dx'] * math.sin(a_) + yyv['dz'] * math.cos(a_), 1), r=yyv['r']) if yyv else None
xpa = full['plateforme']['poutre_ar_x']; top_pa = []
for yq in range(0, 1041, 80):
    s_ = D['poutre_ar'].intersect(cq.Solid.makeBox(60, 1, 500, cq.Vector(xpa - 30, yq - 0.5, 200)))
    if s_.Volume() > 0:
        top_pa.append([yq, round(s_.BoundingBox().zmax, 1)])
RIG = dict(mat=dict(x=m_['x_pied'], z=m_['z_pied'], y=m_['y_axe'], quete=m_['quete_deg'], diam=m_['diam'], L=m_['longueur']),
           voile=dict(contour=vo_['contour'], toile=vo_.get('toile_ep', 0.35), decor=dec),
           livarde=dict(w=lv_['w_mat'], diam=lv_['diam'], jeu=lv_.get('jeu_mat', 5), L=round(vo_['_livarde_longueur'], 1),
                        fourreau={k_: {kk: round(vv, 1) for kk, vv in v_.items()} for k_, v_ in (kc.get('_fourreau') or {}).items()}),
           poutre_ar=dict(x=xpa, top=top_pa), flotteur=dict(y=full['coques']['entraxe'] / 2, pont=full['coques']['pont'], x=[4300, 5000]),
           hc16_ratio=1.37)
print('rig', {k_: (v_ if k_ != 'voile' else '...') for k_, v_ in RIG.items()})
json.dump(dict(new=N, old=O, full=F, roule=R, moteur=M, bras=BR, relevage=REL, rig=RIG), open('/home/claude/cao/plateforme/p3d.json', 'w'), separators=(',', ':'))
print('t', round(time.time() - t0, 1), 's')
