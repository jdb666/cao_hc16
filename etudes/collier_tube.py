"""Collier indépendant du coffre, tube au-dessus du coffre, emplanture sur rail (JD 06/10) : jeux entre le gréement
(mât, collier, tourillon, ferrures, tube, emplanture, haubans) et tout le reste, moteur en marche, moteur relevé,
voiles roulées (livardes rangées). python3 etudes/collier_tube.py [cotes.yaml] -> etudes/collier_tube.json"""
import sys, copy, json, yaml
sys.path.insert(0, '/home/claude/cao')
import cadquery as cq
import hc16_rando as H
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

GRE = ('mat_', 'collier', 'tube_colliers', 'emplanture_', 'hauban_coffre')
IGN = ('voile', 'decor', 'repere')

def walk(a):
    for ch in a.children:
        yield ch
        yield from walk(ch)

def dist(a, b):
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped); d.Perform()
    return d.Value(), d.PointOnShape2(1)

def proche(b1, b2, m):
    return not (b1.xmax + m < b2.xmin or b2.xmax + m < b1.xmin or b1.ymax + m < b2.ymin or b2.ymax + m < b1.ymin or b1.zmax + m < b2.zmin or b2.zmax + m < b1.zmin)

def jeux(cfg, seuil=60):
    A = H.build(cfg)
    D = {ch.name: (ch.obj.val() if hasattr(ch.obj, 'val') else ch.obj) for ch in walk(A) if ch.obj is not None}
    out = {}
    for g in D:
        if not g.startswith(GRE) or g.endswith('tribord'):
            continue
        for n, s in D.items():
            if n.startswith(GRE) or n.startswith(IGN):
                continue
            if not proche(D[g].BoundingBox(), s.BoundingBox(), seuil):
                continue
            v, p = dist(D[g], s)
            if v < seuil:
                out.setdefault(g, []).append((round(v, 1), n, [round(p.X()), round(p.Y()), round(p.Z())]))
    for g in out:
        out[g].sort()
    return out, cfg['mats'].get('_collier')

if __name__ == '__main__':
    c = yaml.safe_load(open(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/cao/cotes.yaml'))
    R = {}
    for titre, lev, enr in (('en marche', 0, 0), ('relevé', 'max', 0), ('voiles roulées', 0, 1)):
        cfg = copy.deepcopy(c)
        v2 = cfg['coffre']['moteur']['vertical2']; v2['levee'] = v2['levee_max'] if lev == 'max' else 0
        cfg['voile'].setdefault('enroulement', {}).update(babord=enr, tribord=enr)
        out, col = jeux(cfg)
        R[titre] = out
        print('==', titre, col)
        for g, L in sorted(out.items()):
            print(f'  {g:42s}', ' ; '.join(f'{v} {n}' for v, n, _ in L[:5]))
    R['quetes_crans'] = H.quetes_crans(c)
    json.dump(R, open('/home/claude/cao/etudes/collier_tube.json', 'w'), ensure_ascii=False, indent=1)
