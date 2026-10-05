"""Patron de la toile de tente (simple paroi) : 4 pans bornés par les arceaux (diagonales), chacun en fuseaux
rayonnant du sommet ; développement par triangulation ; jupes latérales ; imbrication sur rouleau."""
import math, json, numpy as np, ezdxf, os, sys
from shapely.geometry import Polygon, LineString
from shapely import affinity
sys.path.insert(0, '/home/claude/cao/plans')
import tente as TE, imbrication as I
COUT, OURLET = 15, 30                    # valeur de couture, ourlet du bord bas
NS = 70
def carte(pan, s, t):
    if pan == 'AV': return 0.5 * s, 0.5 + (1 - s) * t / 2
    if pan == 'AR': return 1 - 0.5 * s, 0.5 - (1 - s) * t / 2
    if pan == 'L':  return 0.5 - (1 - s) * t / 2, 1 - 0.5 * s        # côté bâbord (tribord en miroir)
def P3(pan, s, t): return np.array(TE.pt(*carte(pan, s, t)))
def place(p1, p2, d1, d2, ref):
    """Point à d1 de p1 et d2 de p2, du côté opposé à ref par rapport à (p1, p2)."""
    dx = p2 - p1; L = np.linalg.norm(dx)
    if L < 1e-9: return p1.copy()
    ex = dx / L; ey = np.array([-ex[1], ex[0]])
    a = (d1 ** 2 - d2 ** 2 + L ** 2) / (2 * L); h = math.sqrt(max(0.0, d1 ** 2 - a ** 2))
    c1, c2 = p1 + a * ex + h * ey, p1 + a * ex - h * ey
    return c1 if np.dot(c1 - p1, ey) * np.dot(ref - p1, ey) <= 0 else c2
def develop_chaine(lignes):
    """lignes : polylignes 3D côte à côte (même nb de points, du bord au sommet). Bande 0-1 par triangulation,
    puis chaque ligne suivante placée par distances à la précédente, du côté opposé à l'avant-dernière."""
    L0, B3 = lignes[0], lignes[1]; n = len(L0)
    A2 = [np.array([0.0, 0.0])]; B2 = [np.array([np.linalg.norm(B3[0] - L0[0]), 0.0])]
    for i in range(n - 1):
        a1 = place(A2[i], B2[i], np.linalg.norm(L0[i + 1] - L0[i]), np.linalg.norm(L0[i + 1] - B3[i]), A2[i] + np.array([0, -1.0]) if i == 0 else A2[i - 1])
        b1 = place(a1, B2[i], np.linalg.norm(B3[i + 1] - L0[i + 1]), np.linalg.norm(B3[i + 1] - B3[i]), A2[i])
        A2.append(a1); B2.append(b1)
    out = [A2, B2]
    for j in range(2, len(lignes)):
        M3, M2, N3, R2 = lignes[j - 1], out[j - 1], lignes[j], out[j - 2]
        N2 = []
        for i in range(n):
            i2 = i + 1 if i < n - 1 else i - 1
            N2.append(place(M2[i], M2[i2], np.linalg.norm(N3[i] - M3[i]), np.linalg.norm(N3[i] - M3[i2]), R2[i]))
        out.append(N2)
    return out
def erreur(lignes, dev):
    """Allongement relatif max et moyen de toutes les arêtes (bords, génératrices, diagonales) après aplatissement."""
    es = []
    for j in range(len(lignes)):
        for i in range(len(lignes[0]) - 1):
            pairs = [((j, i), (j, i + 1))]
            if j < len(lignes) - 1: pairs += [((j, i), (j + 1, i + 1)), ((j + 1, i), (j, i + 1)), ((j, i), (j + 1, i))]
            for (a, b_), (c, d) in pairs:
                d3 = np.linalg.norm(lignes[a][b_] - lignes[c][d]); d2 = np.linalg.norm(dev[a][b_] - dev[c][d])
                if d3 > 30: es.append(abs(d2 - d3) / d3)
    return (max(es), float(np.mean(es)))
def relaxer(lignes, dev):
    """Aplatissement par moindres carrés sur les longueurs d'arêtes (bords, génératrices, deux diagonales)."""
    from scipy.optimize import least_squares
    J, n = len(lignes), len(lignes[0])
    idx = lambda j, i: j * n + i
    X3 = np.array([p for l in lignes for p in l]); X0 = np.array([p for l in dev for p in l])
    E = []
    for j in range(J):
        for i in range(n - 1): E.append((idx(j, i), idx(j, i + 1)))
    for j in range(J - 1):
        for i in range(n):
            E.append((idx(j, i), idx(j + 1, i)))
            if i < n - 1: E += [(idx(j, i), idx(j + 1, i + 1)), (idx(j + 1, i), idx(j, i + 1))]
    E = np.array([e for e in E if np.linalg.norm(X3[e[0]] - X3[e[1]]) > 1e-6]); L3 = np.linalg.norm(X3[E[:, 0]] - X3[E[:, 1]], axis=1)
    w = 1 / np.sqrt(L3)
    def res(x):
        P = x.reshape(-1, 2); return w * (np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) - L3)
    r = least_squares(res, X0.ravel(), method='trf', x_scale='jac', max_nfev=300)
    P = r.x.reshape(-1, 2); P -= P[0]
    return [[P[idx(j, i)] for i in range(n)] for j in range(J)]
def fuseau(pan, t0, t1, sous=4):
    ss = [1 - (1 - i / NS) for i in range(NS + 1)]
    ts = np.linspace(t0, t1, sous + 1)
    lignes = [[P3(pan, s, t) for s in ss] for t in ts]
    dev = relaxer(lignes, develop_chaine(lignes))
    poly = Polygon([tuple(p) for p in dev[0]] + [tuple(p) for p in reversed(dev[-1][:-1])] + [tuple(dev[j][0]) for j in range(len(dev) - 1, 0, -1)]).buffer(0)
    bas = LineString([tuple(dev[j][0]) for j in range(len(dev))])                  # bord bas (ourlet)
    return poly, bas, erreur(lignes, dev), lignes
def avec_marges(poly, bas):
    g = poly.buffer(COUT, join_style=2)
    return g.union(bas.buffer(OURLET, cap_style=2).intersection(poly.buffer(OURLET, join_style=2))).buffer(0)
def pieces(K=4):
    P = []
    for pan, lab, q in (('AV', 'AV', 1), ('AR', 'AR', 1), ('L', 'L', 2)):
        tt = np.linspace(-1, 1, K + 1)
        for k in range(K):
            poly, bas, err, _ = fuseau(pan, tt[k], tt[k + 1])
            P.append(dict(ref=f'{lab}{k + 1}', pan=pan, poly=poly, coupe=avec_marges(poly, bas), bas=bas, err=err, qte=q,
                          note=('à couper 2 fois, en miroir (bâbord / tribord)' if q == 2 else '')))
    # jupes latérales (plan vertical y = ±demi-largeur) : entre le bord de toile et la joue / le banc
    xs = np.linspace(TE.X0, TE.X1, 300); js = [TE.jupe(x) for x in xs]
    haut = [(x - TE.X0, TE.z_bord(x) - 0) for x in xs]; bas_ = [(x - TE.X0, TE.z_bord(x) - max(0.0, j)) for x, j in zip(xs, js)]
    idx = [i for i, j in enumerate(js) if j > 3]
    if idx:
        i0, i1 = max(0, idx[0] - 1), min(len(xs) - 1, idx[-1] + 1)
        pj = Polygon(haut[i0:i1 + 1] + list(reversed(bas_[i0:i1 + 1]))).buffer(0)
        pj = affinity.translate(pj, -pj.bounds[0], -pj.bounds[1])
        P.append(dict(ref='J', pan='J', poly=pj, coupe=pj.buffer(COUT, join_style=2), bas=None, err=(0.0, 0.0), qte=2,
                      note='jupe latérale, cousue sous le bord de toile ; à couper 2 fois en miroir'))
    return P
def orienter(p):
    """Tourne la pièce pour que son grand axe suive le rouleau (droit fil le long du fuseau)."""
    r = p['coupe'].minimum_rotated_rectangle; c = list(r.exterior.coords)
    e = max(((c[k], c[k + 1]) for k in range(4)), key=lambda q: math.dist(*q))
    ang = math.degrees(math.atan2(e[1][1] - e[0][1], e[1][0] - e[0][0]))
    for key in ('poly', 'coupe'):
        p[key] = affinity.rotate(p[key], -ang, origin=(0, 0))
    x0, y0 = p['coupe'].bounds[:2]
    for key in ('poly', 'coupe'):
        p[key] = affinity.translate(p[key], -x0, -y0)
    return p
LAIZE = 1500
def construire(K=4, sortie='/home/claude/cao/plans'):
    P = [orienter(p) for p in pieces(K)]
    items, par = [], {}
    for p in P:
        par[p['ref']] = p
        for n in range(p['qte']):
            g = p['coupe'] if n == 0 else affinity.scale(p['coupe'], xfact=-1, origin=(0, 0))   # 2e exemplaire en miroir
            g = affinity.rotate(g, 90, origin=(0, 0))                       # grand axe le long du rouleau (axe y ici)
            items.append((p['ref'], n + 1, affinity.translate(g, -g.bounds[0], -g.bounds[1])))
    I.SW, I.SH, I.MARGE, I.JEU = LAIZE, 14000, 25, 12                     # on remplit la laize d'abord, puis la longueur
    pl = I.imbriquer(items, step=15, rots=(0, 180))
    assert len(pl) == 1, 'ne tient pas sur la longueur de rouleau prévue'
    placed = pl[0]['placed']; Lr = max(g.bounds[3] for _, _, g, _ in placed) + 25
    # correspondance pièce coupée -> ligne de couture (même transformation)
    out = []
    for ref, n, g, rot in placed:
        base = par[ref]['coupe'] if n == 1 else affinity.scale(par[ref]['coupe'], xfact=-1, origin=(0, 0))
        cou = par[ref]['poly'] if n == 1 else affinity.scale(par[ref]['poly'], xfact=-1, origin=(0, 0))
        base, cou = affinity.rotate(base, 90, origin=(0, 0)), affinity.rotate(cou, 90, origin=(0, 0))
        dx, dy = -base.bounds[0], -base.bounds[1]
        b0 = affinity.translate(base, dx, dy); c0 = affinity.translate(cou, dx, dy)
        if rot: b0, c0 = affinity.rotate(b0, rot, origin=(0, 0)), affinity.rotate(c0, rot, origin=(0, 0))
        ox, oy = g.bounds[0] - b0.bounds[0], g.bounds[1] - b0.bounds[1]
        tr_ = lambda q: affinity.translate(affinity.rotate(q, -90, origin=(0, 0)), 0, LAIZE)   # rouleau à l'horizontale
        out.append((ref, n, tr_(g), tr_(affinity.translate(c0, ox, oy))))
    # DXF 1:1
    doc = ezdxf.new('R2010', setup=True); doc.units = ezdxf.units.MM
    for lay, col in (('LAIZE', 8), ('DECOUPE', 1), ('COUTURE', 5), ('REPERES', 3)): doc.layers.add(lay, color=col)
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (Lr, 0), (Lr, LAIZE), (0, LAIZE)], close=True, dxfattribs={'layer': 'LAIZE'})
    rings = lambda g: [list(g.exterior.coords)] + [list(r.coords) for r in g.interiors]
    for ref, n, g, c in out:
        for r in rings(g): msp.add_lwpolyline([(round(x, 1), round(y, 1)) for x, y in r[:-1]], close=True, dxfattribs={'layer': 'DECOUPE'})
        for r in rings(c): msp.add_lwpolyline([(round(x, 1), round(y, 1)) for x, y in r[:-1]], close=True, dxfattribs={'layer': 'COUTURE'})
        pt = g.representative_point()
        msp.add_text(ref + ('' if par[ref]['qte'] == 1 else (' bâbord' if n == 1 else ' tribord')), height=40, dxfattribs={'layer': 'REPERES'}).set_placement((pt.x, pt.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    os.makedirs(f'{sortie}/dxf_tente', exist_ok=True)
    doc.saveas(f'{sortie}/dxf_tente/patron_tente_laize1500.dxf')
    # SVG pour la page
    pd = lambda g: ''.join('M' + ' L'.join(f'{x:.0f},{LAIZE - y:.0f}' for x, y in r[:-1]) + ' Z ' for r in rings(g))
    nseg = 3; Ls = math.ceil(Lr / nseg / 100) * 100
    segs = []
    for k in range(nseg):
        x0 = k * Ls
        svg = [f'<svg class="planche" viewBox="{x0 - 30} -110 {Ls + 60} {LAIZE + 150}" role="img" aria-label="Toile, tronçon {k + 1}">',
               f'<rect x="{x0}" y="0" width="{min(Ls, Lr - x0):.0f}" height="{LAIZE}" class="feuille"/>']
        for gx in range(int(x0) + 500, int(min(x0 + Ls, Lr)), 500): svg.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{LAIZE}" class="grille"/>')
        for ref, n, g, c in out:
            if g.bounds[2] < x0 or g.bounds[0] > x0 + Ls: continue
            svg.append(f'<path d="{pd(g)}" class="piece pT" fill-rule="evenodd"><title>{ref}</title></path><path d="{pd(c)}" class="couture"/>')
            pt = g.representative_point()
            svg.append(f'<text x="{pt.x:.0f}" y="{LAIZE - pt.y:.0f}" class="rep" font-size="95" text-anchor="middle" dominant-baseline="central">{ref}{"" if par[ref]["qte"] == 1 else (" b" if n == 1 else " t")}</text>')
        svg.append(f'<text x="{x0}" y="-35" class="cote" font-size="70">{x0 / 1000:.1f} → {min(x0 + Ls, Lr) / 1000:.2f} m</text></svg>')
        segs.append(''.join(svg))
    table = []
    for p in P:
        r = p['coupe'].bounds
        table.append(dict(ref=p['ref'], pan={'AV': 'avant', 'AR': 'arrière', 'L': 'latéral', 'J': 'jupe'}[p['pan']], qte=p['qte'],
                          L=round(r[2] - r[0]), H=round(r[3] - r[1]), surf=round(p['coupe'].area * p['qte'] / 1e6, 2),
                          allong=round(100 * p['err'][0], 2), note=p['note']))
    info = dict(svg=segs, table=table, rouleau=round(Lr), K=K, couture=COUT, ourlet=OURLET,
                arceau=round(TE.L_ARC), angle=round(TE.ANGLE_PIED), long=TE.X1 - TE.X0, larg=2 * TE.HY,
                sommet=round(TE.z(.5, .5)), haut=round(TE.z(.5, .5) - TE.C['plateforme']['trampoline_z']),
                toile=round(sum(t_['surf'] for t_ in table), 2), allong=round(max(t_['allong'] for t_ in table), 2))
    json.dump(info, open(f'{sortie}/patron.json', 'w'), ensure_ascii=False)
    return info
if __name__ == '__main__':
    import time; t0 = time.time()
    inf = construire(4)
    print({k: v for k, v in inf.items() if k not in ('svg', 'table')}, round(time.time() - t0))
    for r in inf['table']: print(r)
