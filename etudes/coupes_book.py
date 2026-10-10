"""Coupes planes du modèle pour les figures du book (JD 08/10) : glissière du tube des colliers et banc renforcé.
Chaque coupe : plan x = cte (vue y-z) ou y = cte (vue x-z), pièces choisies, contours (extérieur + trous) en mm.
python3 etudes/coupes_book.py -> etudes/coupes_book.json"""
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import yaml, cadquery as cq, hc16_rando as H
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
c = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
A = H.build(c)
D = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children if ch.obj is not None}
V = cq.Vector

def coupe(nom, axe, val, fen):
    """Contours de la section de la pièce `nom` par le plan axe = val ; fen = (u0, u1, v0, v1) fenêtre de tri."""
    s = D[nom]
    bb = s.BoundingBox()
    lo, hi = (bb.xmin, bb.xmax) if axe == 'x' else (bb.ymin, bb.ymax)
    if not (lo - 1e-6 <= val <= hi + 1e-6):
        return []
    n = gp_Dir(1, 0, 0) if axe == 'x' else gp_Dir(0, 1, 0)
    p = gp_Pnt(val, 0, 0) if axe == 'x' else gp_Pnt(0, val, 0)
    sec = BRepAlgoAPI_Section(s.wrapped, gp_Pln(p, n)); sec.Build()
    sh = cq.Shape.cast(sec.Shape())
    edges = sh.Edges()
    if not edges:
        return []
    uv = (lambda q: (round(q.y, 3), round(q.z, 3))) if axe == 'x' else (lambda q: (round(q.x, 3), round(q.z, 3)))
    segs = []                                          # chaque arête échantillonnée, puis chaînage bout à bout en boucles
    for e in edges:
        L = e.Length(); nseg = max(2, int(L / 1.5))
        segs.append([uv(e.positionAt(i / nseg)) for i in range(nseg + 1)])
    d2 = lambda a, b: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    out = []
    while segs:
        boucle = segs.pop(0)
        while segs and d2(boucle[0], boucle[-1]) > 1e-4:
            j, inv = min(((j, inv) for j in range(len(segs)) for inv in (False, True)),
                         key=lambda t: d2(boucle[-1], segs[t[0]][-1] if t[1] else segs[t[0]][0]))
            s_ = segs.pop(j)
            boucle += (s_[::-1] if inv else s_)[1:]
        if len(boucle) > 3:
            out.append([(round(a, 2), round(b, 2)) for a, b in boucle])
    return out

COUPES = {
    # (JD 09/10) poteau de la glissière dans le coffre, potence au-dessus de C4
    'gl2_y1045': ('y', 1045.0, ('coffre_coque', 'glissiere_poteau_babord', 'glissiere_potence_babord', 'glissiere_bloc_babord', 'glissiere_bague_babord',
                                'glissiere_cale_babord', 'piece_angle_av_babord', 'poutre_av', 'banc_babord_assise', 'tube_colliers',
                                'collier_tourillon_babord', 'longeron_babord', 'coque_babord', 'coffre_hiloire')),
    'gl2_x2085': ('x', 2085.0, ('joue_babord', 'glissiere_potence_babord', 'glissiere_bloc_babord', 'banc_babord_assise', 'banc_babord_lisse_0',
                                'tube_colliers', 'collier_tourillon_babord', 'collier_pli1_babord', 'collier_pli2_babord', 'collier_pli3_babord',
                                'collier_pli4_babord', 'collier_pli5_babord', 'collier_pli6_babord', 'collier_pli7_babord', 'tape_piece_angle_babord',
                                'piece_angle_av_babord', 'poutre_av', 'longeron_babord', 'coque_babord', 'mat_babord')),
    'gl2_x1988': ('x', 1988.5, ('coffre_coque', 'joue_babord', 'glissiere_poteau_babord', 'glissiere_potence_babord', 'glissiere_bague_babord',
                                'glissiere_cale_babord', 'piece_angle_av_babord', 'coque_babord', 'mat_babord', 'semelle_babord')),
    'banc2_x2545': ('x', 2545.0, ('banc_babord_assise', 'banc_babord_lisse_2', 'joue_babord', 'longeron_babord', 'trampoline', 'joint_longeron_babord', 'coque_babord')),
    'glissiere_x2085': ('x', 2085.0, ('joue_babord', 'glissiere_sabot_babord', 'glissiere_berceau_babord', 'glissiere_pehd_babord',
                                      'glissiere_poteau_haut_babord_int', 'glissiere_poteau_bas_babord_int', 'glissiere_cale_babord',
                                      'banc_babord_assise', 'banc_babord_lisse_0', 'tube_colliers', 'collier_tourillon_babord',
                                      'collier_pli1_babord', 'collier_pli2_babord', 'collier_pli3_babord', 'collier_pli4_babord',
                                      'collier_pli5_babord', 'collier_pli6_babord', 'collier_pli7_babord',
                                      'piece_angle_av_babord', 'poutre_av', 'longeron_babord', 'coque_babord')),
    'glissiere_x2059': ('x', 2059.5, ('glissiere_poteau_haut_babord_av', 'glissiere_poteau_bas_babord_av')),
    'glissiere_y1040': ('y', 1040.0, ('glissiere_sabot_babord', 'glissiere_berceau_babord', 'glissiere_pehd_babord', 'tube_colliers',
                                      'collier_tourillon_babord', 'glissiere_poteau_haut_babord_av', 'glissiere_poteau_haut_babord_ar',
                                      'glissiere_poteau_bas_babord_av', 'glissiere_poteau_bas_babord_ar', 'glissiere_cale_babord',
                                      'banc_babord_assise', 'coffre_coque', 'piece_angle_av_babord', 'poutre_av', 'coffre_trappe_c4_2')),
    'banc_x2680': ('x', 2680.0, ('banc_babord_couple_2', 'banc_babord_assise', 'joue_babord', 'longeron_babord', 'lacage_banc_2', 'trampoline', 'coque_babord')),
    'banc_x2689': ('x', 2689.0, ('banc_babord_jambe_2_ar',)),
    'banc_x2545': ('x', 2545.0, ('banc_babord_assise', 'banc_babord_lisse_2', 'joue_babord', 'longeron_babord', 'trampoline')),
}
res = {}
for cle, (axe, val, noms) in COUPES.items():
    res[cle] = dict(axe=axe, val=val, pieces={})
    for n in noms:
        if n in D:
            cs = coupe(n, axe, val, None)
            if cs:
                res[cle]['pieces'][n] = cs
    print(cle, {n: len(v) for n, v in res[cle]['pieces'].items()}, flush=True)
json.dump(res, open('/home/claude/cao/etudes/coupes_book.json', 'w'))
