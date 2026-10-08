"""Chiffres du modèle pour les textes (page 3D, book, synthèse) : boîtes des pièces, longueurs du brêlage, du laçage
et des haubans, géométries rangées par le modèle (k['_...']). python3 etudes/infos_texte.py -> etudes/infos_texte.json"""
import sys, json, math, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import yaml, cadquery as cq, hc16_rando as H
c = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
A = H.build(c)
D = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children if ch.obj is not None}
k = c['coffre']
def bb(n):
    b = D[n].BoundingBox()
    return [round(b.xmin, 1), round(b.xmax, 1), round(b.ymin, 1), round(b.ymax, 1), round(b.zmin, 1), round(b.zmax, 1)]
def longueur_cyl(n):                                # longueur d'un cylindre ou d'une suite de cylindres (cordage, hauban)
    s = D[n]; tot = 0.0
    for so in (s.Solids() if hasattr(s, 'Solids') else [s]):
        cs = [e for e in so.Edges() if e.geomType() == 'CIRCLE']
        if len(cs) >= 2:
            p = sorted({(round(e.Center().x, 2), round(e.Center().y, 2), round(e.Center().z, 2)) for e in cs})
            if len(p) >= 2:
                tot += math.dist(p[0], p[-1])
    return round(tot)
out = dict(boites={}, longueurs={}, geom={})
for n in sorted(D):
    if n.endswith('tribord') or '_tribord_' in n:
        continue
    if n.startswith(('couple_coffre', 'coffre_', 'glissiere_', 'banc_babord', 'accoudoir_babord', 'batterie', 'joue_babord', 'moteur_puits',
                     'moteur_tableau', 'coffre_ancre', 'tube_colliers', 'collier_', 'pylone', 'semelle', 'emplanture', 'livarde_')):
        out['boites'][n] = bb(n)
for n in sorted(D):
    if n.startswith(('brelage_poutre', 'lacage_banc', 'hauban_')):
        out['longueurs'][n] = longueur_cyl(n)
        out['boites'][n] = bb(n)
for key in ('_accroches', '_capot_arriere', '_rangements', '_glissiere', '_accoudoirs', '_collier_geom', '_puits', '_geom', '_trappe'):
    if key in k:
        v = k[key]
        try:
            json.dumps(v); out['geom'][key] = v
        except TypeError:
            out['geom'][key] = {a: b for a, b in v.items() if isinstance(b, (int, float, str, list, tuple, dict))} if isinstance(v, dict) else str(v)
out['geom']['_collier'] = c['mats'].get('_collier')
json.dump(out, open('/home/claude/cao/etudes/infos_texte.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out['longueurs'], indent=0))
print(json.dumps(out['geom'], ensure_ascii=False, default=str)[:3000])
