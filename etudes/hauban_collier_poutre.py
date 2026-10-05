"""Hauban du collier au milieu de la poutre AV (JD 05/10) : jeux contre toutes les pièces, moteur en marche et relevé,
et hauteur libre sous le hauban le long de son tracé.
python3 etudes/hauban_collier_poutre.py [cotes.yaml]"""
import sys, math, yaml, copy, json
sys.path.insert(0, '/home/claude/cao')
import cadquery as cq
import hc16_rando as H
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

def walk(a):
    for ch in a.children:
        yield ch
        yield from walk(ch)

def formes(A):
    return {ch.name: (ch.obj if not hasattr(ch.obj, 'val') else ch.obj.val()) for ch in walk(A) if ch.obj is not None}

def dist(a, b):
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value(), d.PointOnShape1(1), d.PointOnShape2(1)

def proche(bb1, bb2, m):
    return not (bb1.xmax + m < bb2.xmin or bb2.xmax + m < bb1.xmin or bb1.ymax + m < bb2.ymin or bb2.ymax + m < bb1.ymin or bb1.zmax + m < bb2.zmin or bb2.zmax + m < bb1.zmin)

def jeux(cfg, titre, seuil=60):
    A = H.build(cfg); D = formes(A)
    res = {}
    for nom in ('babord', 'tribord'):
        h = D[f'hauban_coffre_collier_poutre_{nom}']; bh = h.BoundingBox()
        lst = []
        for n, s in D.items():
            if n == f'hauban_coffre_collier_poutre_{nom}' or n.startswith(('voile', 'decor_yinyang_voile')):
                continue
            if not proche(bh, s.BoundingBox(), seuil):
                continue
            v, p1, p2 = dist(h, s)
            if v < seuil:
                lst.append((round(v, 1), n, (round(p1.X()), round(p1.Y()), round(p1.Z()))))
        lst.sort()
        res[nom] = lst
        print(titre, nom, 'longueur', round(h.BoundingBox().DiagonalLength), 'mm')
        for v, n, p in lst[:14]:
            print(f'   {v:7.1f}  {n:38s} au point {p}')
    return A, D, res

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/cao/cotes.yaml'
    c = yaml.safe_load(open(src))
    out = {}
    for titre, lv in (('en marche', 0), ('relevé', 'max')):
        cfg = copy.deepcopy(c)
        v2 = cfg['coffre']['moteur']['vertical2']; v2['levee'] = v2['levee_max'] if lv == 'max' else 0
        cfg['voile'].setdefault('enroulement', {}).update(babord=0, tribord=0)
        A, D, res = jeux(cfg, titre)
        out[titre] = res
        if lv == 0:
            g = cfg['coffre'].get('_collier_poutre')
            print('extrémités', json.dumps({k: {kk: [round(x, 1) for x in vv] for kk, vv in v.items()} for k, v in g.items()}))
            # hauteur libre sous le hauban (babord) : rayons verticaux vers le coffre et la table
            hb = g['babord']; a = cq.Vector(*hb['haut']); b = cq.Vector(*hb['bas'])
            cible = [D[n] for n in ('coffre_coque', 'coffre_table') if n in D] + [D[n] for n in D if n.startswith(('joue_', 'couple_coffre', 'moteur_puits'))]
            print('   y      x      z hauban   z dessous   jeu')
            for i in range(1, 20):
                t = i / 20; p = a + (b - a) * t
                ligne = cq.Edge.makeLine(cq.Vector(p.x, p.y, p.z - 2.5), cq.Vector(p.x, p.y, 0))
                zs = []
                for s in cible:
                    try:
                        it = s.intersect(ligne)
                        if it.Vertices() or it.Edges():
                            zs.append(it.BoundingBox().zmax)
                    except Exception:
                        pass
                zd = max(zs) if zs else None
                print(f'{p.y:6.0f} {p.x:6.0f} {p.z:8.1f} {"—" if zd is None else round(zd, 1):>10} {"—" if zd is None else round(p.z - 2 - zd, 1):>6}')
    json.dump(out, open('/home/claude/cao/etudes/hauban_collier_poutre.json', 'w'), ensure_ascii=False, indent=1)
