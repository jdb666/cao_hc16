from shapely.geometry import box
from shapely.prepared import prep
from shapely.ops import unary_union
from shapely import affinity
SW, SH, MARGE, JEU = 2500, 1220, 10, 8
def norm(poly, rot=0):
    g = affinity.rotate(poly, rot, origin=(0, 0)) if rot else poly
    x0, y0, _, _ = g.bounds
    return affinity.translate(g, -x0, -y0)
def imbriquer(items, step=10, rots=(0, 90, 180, 270)):
    """items : liste (ref, n, poly). Bas-gauche glouton, par surface décroissante. Renvoie liste de planches."""
    items = sorted(items, key=lambda t: -t[2].area)
    planches = []
    for ref, n, poly in items:
        done = False
        for pl in planches + [None]:
            if pl is None:
                pl = dict(placed=[], union=None); planches.append(pl)
            pu = prep(pl['union'].buffer(JEU / 2)) if pl['union'] is not None else None
            best = None
            for rot in rots:
                g0 = norm(poly, rot); w, h = g0.bounds[2], g0.bounds[3]
                if w > SW - 2 * MARGE or h > SH - 2 * MARGE: continue
                gb = g0.buffer(JEU / 2)
                found = None
                y = MARGE
                while y + h <= SH - MARGE and found is None:
                    x = MARGE
                    while x + w <= SW - MARGE:
                        if best is not None and (y, x) >= best[0]: break
                        cand = affinity.translate(gb, x, y)
                        if pu is None or not pu.intersects(cand):
                            found = (y, x); break
                        x += step
                    y += step
                if found and (best is None or found < best[0]):
                    best = (found, rot, g0)
            if best:
                (y, x), rot, g0 = best
                g = affinity.translate(g0, x, y)
                pl['placed'].append((ref, n, g, rot))
                pl['union'] = g if pl['union'] is None else unary_union([pl['union'], g])
                done = True; break
        assert done, ref
    for pl in planches:
        pl['taux'] = sum(g.area for *_, g, _ in [(a, b, c, d) for a, b, c, d in pl['placed']]) / (SW * SH)
    return planches
