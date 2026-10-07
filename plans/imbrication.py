import math
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
    if not getattr(imbriquer, 'ordre_libre', False):
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


def imbriquer_mieux(items, essais=8, graine=1, step=10):
    """Plusieurs ordres (surface décroissante perturbée) ; garde le moins de panneaux, la dernière planche
    comptant pour ½ si elle tient sur un demi-panneau (1 250). Renvoie (planches, demi)."""
    import random
    global SW
    rnd = random.Random(graine); base = sorted(items, key=lambda t: -t[2].area); best = None
    for k in range(essais):
        ordre = base if k == 0 else sorted(base, key=lambda t: -t[2].area * rnd.uniform(0.6, 1.4))
        imbriquer.ordre_libre = True
        SW = 2500; pls = imbriquer(ordre, step=step)
        demi = None
        if len(pls) >= 2:
            last = [q for q in ordre if (q[0], q[1]) in [(x[0], x[1]) for x in pls[-1]['placed']]]
            SW = 1250
            try:
                h = imbriquer(last, step=step)
                if len(h) == 1: demi = h
            except AssertionError:                     # une pièce ne tient pas sur un demi-panneau
                pass
        SW = 2500; imbriquer.ordre_libre = False
        score = len(pls) - (0.5 if demi else 0)
        if best is None or score < best[0]: best = (score, pls, demi)
        if score <= math.ceil(sum(q[2].area for q in items) / (2500 * 1220) * 2) / 2: break
    return best[1], best[2]


# ---------------------------------------------------------------- imbrication par grille (rapide) : même règle bas-gauche, collisions par corrélation FFT
def _masque(g, res, d):
    """Masque booléen (lignes = y) du polygone g (bornes à 0,0) grossi de d, pixels de res mm ; origine en (-d, -d)."""
    from PIL import Image, ImageDraw
    import numpy as np
    gb = g.buffer(d, join_style=2)
    w = int(math.ceil((g.bounds[2] + 2 * d) / res)) + 1; h = int(math.ceil((g.bounds[3] + 2 * d) / res)) + 1
    im = Image.new('1', (w, h), 0); dr = ImageDraw.Draw(im)
    for p in getattr(gb, 'geoms', [gb]):
        dr.polygon([((x + d) / res, (y + d) / res) for x, y in p.exterior.coords], fill=1, outline=1)
        for r_ in p.interiors:                    # trous (évidements) libres : on peut y loger de petites pièces
            dr.polygon([((x + d) / res, (y + d) / res) for x, y in r_.coords], fill=0, outline=1)
    return np.array(im, dtype=np.float32)

def imbriquer_grille(items, sw, res=5.0, rots=(0, 90, 180, 270)):
    """items : (ref, n, poly) dans l'ordre voulu. Renvoie les planches (placed, union) comme imbriquer()."""
    import numpy as np
    from scipy.signal import fftconvolve
    d = JEU / 2 + 0.8 * res                        # grossissement : jeu + marge de pixellisation
    nx, ny = int((sw - 2 * MARGE) // res), int((SH - 2 * MARGE) // res)
    planches = []
    cache = {}
    for ref, n, poly in items:
        cands = []
        for rot in rots:
            g0 = norm(poly, rot)
            if g0.bounds[2] + 2 * d > sw - 2 * MARGE or g0.bounds[3] + 2 * d > SH - 2 * MARGE:
                continue
            key = (id(poly), rot)
            if key not in cache:
                cache[key] = _masque(g0, res, d)
            cands.append((rot, g0, cache[key]))
        assert cands, ref
        done = False
        for pl in planches + [None]:
            if pl is None:
                pl = dict(placed=[], union=None, occ=np.zeros((ny, nx), dtype=np.float32)); planches.append(pl)
            best = None
            for rot, g0, M in cands:
                if M.shape[0] > ny or M.shape[1] > nx:
                    continue
                C = fftconvolve(pl['occ'], M[::-1, ::-1], mode='valid')
                ok = np.argwhere(C < 0.5)
                if not len(ok):
                    continue
                i, j = ok[np.lexsort((ok[:, 1], ok[:, 0]))[0]]      # bas d'abord, puis gauche
                if best is None or (i, j) < best[0]:
                    best = ((int(i), int(j)), rot, g0, M)
            if best:
                (i, j), rot, g0, M = best
                g = affinity.translate(g0, MARGE + j * res + d, MARGE + i * res + d)
                pl['occ'][i:i + M.shape[0], j:j + M.shape[1]] += M
                pl['placed'].append((ref, n, g, rot))
                pl['union'] = g if pl['union'] is None else unary_union([pl['union'], g])
                done = True; break
        assert done, ref
    for pl in planches:
        pl.pop('occ', None)
        pl['taux'] = sum(g.area for _, _, g, _ in pl['placed']) / (sw * SH)
    return planches

def controle_planche(pl, sw):
    """Vrai si toutes les pièces sont dans la plaque (marge) et à JEU - 0,5 les unes des autres."""
    cadre = box(MARGE - 0.01, MARGE - 0.01, sw - MARGE + 0.01, SH - MARGE + 0.01)
    gs = [g for _, _, g, _ in pl['placed']]
    if not all(cadre.contains(g) for g in gs):
        return False
    for a in range(len(gs)):
        for b in range(a + 1, len(gs)):
            if gs[a].distance(gs[b]) < JEU - 0.5:
                return False
    return True

def imbriquer_grille_mieux(items, essais=12, graine=1, res=5.0):
    """Comme imbriquer_mieux, par grille : plusieurs ordres, dernière plaque sur un demi-panneau si possible."""
    import random
    rnd = random.Random(graine); base = sorted(items, key=lambda t: -t[2].area); best = None
    for k in range(essais):
        ordre = base if k == 0 else sorted(base, key=lambda t: -t[2].area * rnd.uniform(0.6, 1.4))
        pls = imbriquer_grille(ordre, 2500, res)
        demi = None
        if len(pls) >= 1:                                  # (07/10) aussi quand une épaisseur tient sur une seule plaque (CP 10)
            last = [q for q in ordre if (q[0], q[1]) in [(x[0], x[1]) for x in pls[-1]['placed']]]
            try:
                h = imbriquer_grille(last, 1250, res)
                if len(h) == 1: demi = h
            except AssertionError:
                pass
        score = (len(pls) - (0.5 if demi else 0), -max(p['taux'] for p in pls))
        if best is None or score < best[0]: best = (score, pls, demi)
    pls, demi = best[1], best[2]
    for pl in pls:
        assert controle_planche(pl, 2500), 'chevauchement'
    if demi:
        assert controle_planche(demi[0], 1250), 'chevauchement (demi)'
    return pls, demi


def _grille_occupee(pl, sw, res, d):
    """Occupation d'une plaque déjà remplie (pièces placées grossies de d), pixels de res mm, origine en (MARGE, MARGE)."""
    from PIL import Image, ImageDraw
    import numpy as np
    nx, ny = int((sw - 2 * MARGE) // res), int((SH - 2 * MARGE) // res)
    im = Image.new('1', (nx, ny), 0); dr = ImageDraw.Draw(im)
    for _, _, g, _ in pl['placed']:
        gb = g.buffer(d, join_style=2)
        for p in getattr(gb, 'geoms', [gb]):
            dr.polygon([((x - MARGE) / res, (y - MARGE) / res) for x, y in p.exterior.coords], fill=1, outline=1)
            for r_ in p.interiors:
                dr.polygon([((x - MARGE) / res, (y - MARGE) / res) for x, y in r_.coords], fill=0, outline=1)
    return np.array(im, dtype=np.float32)

def reloger(pls, largeurs, res=2.5):
    """Essaie de vider la dernière plaque en logeant ses pièces dans les précédentes (grille plus fine).
    pls : plaques (placed) ; largeurs : largeur de chacune. Renvoie la liste des plaques (dernière retirée si vidée)."""
    import numpy as np
    from scipy.signal import fftconvolve
    if len(pls) < 2:
        return pls, largeurs
    dp = JEU / 2 + 0.6 * res                        # pièces déjà placées : grossies de la moitié du jeu (+ pixellisation)
    dn = JEU / 2 + 0.6 * res                        # pièce à loger : l'autre moitié
    occ = [_grille_occupee(pl, sw, res, dp) for pl, sw in zip(pls[:-1], largeurs[:-1])]
    reste = []
    for ref, n, g, rot0 in pls[-1]['placed']:
        g_ = norm(g, 0); loge = False
        for k, (pl, sw) in enumerate(zip(pls[:-1], largeurs[:-1])):
            best = None
            for rot in (0, 90, 180, 270):
                g0 = norm(g_, rot); M = _masque(g0, res, dn)
                if M.shape[0] > occ[k].shape[0] or M.shape[1] > occ[k].shape[1]:
                    continue
                C = fftconvolve(occ[k], M[::-1, ::-1], mode='valid')
                ok = np.argwhere(C < 0.5)
                if len(ok):
                    i, j = ok[np.lexsort((ok[:, 1], ok[:, 0]))[0]]
                    if best is None or (i, j) < best[0]:
                        best = ((int(i), int(j)), rot, g0, M)
            if best:
                (i, j), rot, g0, M = best
                gp = affinity.translate(g0, MARGE + j * res + dn, MARGE + i * res + dn)
                essai = dict(placed=pl['placed'] + [(ref, n, gp, rot)])
                if controle_planche(essai, sw):
                    pl['placed'].append((ref, n, gp, rot)); occ[k][i:i + M.shape[0], j:j + M.shape[1]] += M
                    pl['union'] = unary_union([pl['union'], gp]); loge = True; break
        if not loge:
            reste.append((ref, n, g, rot0))
    for pl, sw in zip(pls[:-1], largeurs[:-1]):
        pl['taux'] = sum(g.area for _, _, g, _ in pl['placed']) / (sw * SH)
    if reste:
        pls[-1]['placed'] = reste
        pls[-1]['taux'] = sum(g.area for _, _, g, _ in reste) / (largeurs[-1] * SH)
        return pls, largeurs
    return pls[:-1], largeurs[:-1]
