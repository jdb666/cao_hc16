"""HC16 + gréement Rando (mâts extérieurs), sans coffre.
Lit cotes.yaml, construit l'assemblage CadQuery, exporte STEP.
Usage : python hc16_rando.py [cotes.yaml] [sortie.step]
"""
import math, sys, yaml, json, os
import cadquery as cq
from cadquery import Vector as V

def interp(tab, x):
    for (x0, y0), (x1, y1) in zip(tab, tab[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return tab[-1][1]

def coque(c, yc):
    """Lissage de sections périodiques. Départ à x = 60 mm : en dessous, les sections trop
    fines rendent les booléens OCC instables (pointe d'étrave tronquée de 6 cm)."""
    L = c["longueur"]
    xs = [60, 120, 200, 300, 450, 600, 800, 1000, 1250, 1500, 1800, 2100, 2400,
          2800, 3200, 3600, 4000, 4400, 4700, L]
    wires = []
    for x in xs:
        k, b = interp(c["quille"], x), interp(c["demi_largeur"], x)
        d = interp(c["pont"], x) - c["bouge_pont"]       # livet ; le dessus du bombé = ligne de pont
        n = 12
        pts = [V(x, yc + b * math.cos(math.pi * j / n),
                 d - (d - k) * math.sin(math.pi * j / n) ** 0.55) for j in range(n + 1)]
        pts += [V(x, yc - b * math.cos(math.pi * j / n),
                  d + c["bouge_pont"] * math.sin(math.pi * j / n)) for j in range(1, n)]
        wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True)]))
    return cq.Solid.makeLoft(wires, ruled=False)

def aire_cdg(p):
    a = cx = cz = 0.0
    for (x0, z0), (x1, z1) in zip(p, p[1:] + p[:1]):
        k = x0 * z1 - x1 * z0
        a += k; cx += (x0 + x1) * k; cz += (z0 + z1) * k
    return abs(a) / 2, (cx / (3 * a), cz / (3 * a))

def voile_restante(contour, quete, frac):
    """Enroulement vertical autour du guindant : chaque tranche perd la même largeur d
    (repère du mât), la chute avance de d, le haut dont la corde < d disparaît.
    frac = part de surface enroulée (0 = pleine, 1 = roulée). Retourne (points dx,dz, d)."""
    ca, sa = math.cos(quete), math.sin(quete)
    loc = [tuple(q) for q in contour]            # (u perp. mât vers l'arrière, w le long du mât)
    monde = lambda pts: [(u * ca + w * sa, -u * sa + w * ca) for u, w in pts]
    if frac <= 0:
        return monde(loc), 0.0
    if frac >= 1:
        return [], None
    def clip(d):
        out = []
        for a_, b_ in zip(loc, loc[1:] + loc[:1]):
            ia, ib = a_[0] >= d, b_[0] >= d
            if ia: out.append(a_)
            if ia != ib:
                t = (d - a_[0]) / (b_[0] - a_[0])
                out.append((d, a_[1] + t * (b_[1] - a_[1])))
        return [(u - d, w) for u, w in out]
    a0 = aire_cdg(loc)[0]; lo, hi = 0.0, max(u for u, _ in loc)
    for _ in range(60):
        d = (lo + hi) / 2
        lo, hi = (d, hi) if aire_cdg(clip(d))[0] > (1 - frac) * a0 else (lo, d)
    return monde(clip(d)), d

def cyl(p0, p1, d):
    p0, p1 = V(*p0), V(*p1)
    v = p1 - p0
    return cq.Solid.makeCylinder(d / 2, v.Length, p0, v.normalized())

def ellipsoide(ax, ay, az, centre):
    """Ellipsoïde plein (sphère unité déformée), centré en `centre`."""
    from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
    from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
    g = gp_GTrsf(); g.SetVectorialPart(gp_Mat(ax, 0, 0, 0, ay, 0, 0, 0, az))
    g.SetTranslationPart(gp_XYZ(*centre))
    # sphère complète ; couture tournée de 33° pour l'écarter du plan de coupe y = 0
    sph = cq.Solid.makeSphere(1, V(0, 0, 0), V(0, 0, 1), -90, 90, 360).rotate(V(0, 0, 0), V(0, 0, 1), 33)
    return cq.Solid(BRepBuilderAPI_GTransform(sph.wrapped, g, True).Shape())

def section_coffre(xa, zb, zt, xp, ep_ar=0.0, ep_f=0.0, ep_t=0.0, ep_b=0.0, n=24, zcut=None):
    """Section (plan XZ) : face arrière verticale en xa, plateau horizontal en haut (zt) de xa
    jusqu'à xp, puis quart de rond de rayon R = zt - zb centré en (xp, zb) jusqu'au fond (zb).
    Les ep_* décalent vers l'intérieur (face AR, fond, plateau, bordé)."""
    R = zt - zb
    r = R - ep_b
    zh = zt if zcut is None else min(zt, zcut)                # coupe par un plan horizontal
    xr, zbi, zti = xa - ep_ar, zb + ep_f, zh - ep_t
    t0 = math.asin(min(1.0, (zti - zb) / r))                 # départ de l'arc sous le plateau
    t1 = math.asin(min(1.0, (zbi - zb) / r))                 # arrivée de l'arc au-dessus du fond
    arc = [(xp - r * math.cos(t), zb + r * math.sin(t)) for t in [t0 + (t1 - t0) * i / n for i in range(n + 1)]]
    return dict(pts=[(xr, zbi), (xr, zti)] + arc)

def solide_section(sec, y0, larg):
    """Extrude la section (polyligne dense) entre y0 et y0 - larg (vers -Y)."""
    return cq.Workplane("XZ", origin=(0, y0, 0)).polyline(sec["pts"]).close().extrude(larg).val()

def profil_coffre(xa, zb, zpl, xp, Rb, x_top, zcol, n=40):
    """Profil extérieur (plan XZ) : fond, quart de rond R=Rb centré (xp, zb) jusqu'au niveau du plateau,
    puis arc d'ellipse raccordé en tangence (C1) jusqu'à (x_top, zcol) à tangente horizontale,
    dessus plat jusqu'à la face arrière xa. Retourne (points, infos)."""
    dz = zpl - zb
    x1 = xp - math.sqrt(Rb * Rb - dz * dz)
    slope = (xp - x1) / dz
    dx, H = x_top - x1, zcol - zpl
    f = lambda B: (B * B * dx) / ((dx * dx / (1 - ((B - H) / B) ** 2)) * (B - H)) - slope
    lo, hi = H * 1.0001, 80 * H
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if f(lo) * f(mid) <= 0 else (mid, hi)
    B = (lo + hi) / 2
    A_ = math.sqrt(dx * dx / (1 - ((B - H) / B) ** 2))
    ze = zcol - B
    t0 = math.asin(max(-1.0, min(1.0, (zpl - ze) / B)))
    pts = [(xa, zb), (xp - Rb, zb)]
    tc = math.asin(dz / Rb)
    pts += [(xp - Rb * math.cos(t), zb + Rb * math.sin(t)) for t in [tc * i / n for i in range(1, n + 1)]]
    pts += [(x_top - A_ * math.cos(t), ze + B * math.sin(t)) for t in [t0 + (math.pi / 2 - t0) * i / n for i in range(1, n + 1)]]
    pts += [(xa, zcol)]
    return pts, dict(x1=x1, A=A_, B=B, ze=ze, avant=xp - Rb)

def coffre(A, k):
    """Coffre (CP cousu-collé) devant la poutre AV. Joues « ellipsoïdales » : deux quarts d'ellipse de même
    hauteur, tangents à l'horizontale au collier ; extrémités = pointe avant du coffre, collier, bout
    arrière du banc. Le coffre suit le quart d'ellipse avant jusqu'à la hauteur du collier puis reste plat
    jusqu'à la poutre ; plateau intérieur. Moteur : chaise centrée sous le coffre, bascule vers l'arrière
    dans l'axe du bateau, sous la martingale (arbre enfoncé à fond avant de basculer)."""
    from shapely.geometry import Polygon
    m = CFG_MAT
    qa = math.radians(m["quete_deg"])
    zc = m["z_pied"] + m["collier_hauteur"] * math.cos(qa)
    W, xa, zb = k["largeur"], k["face_ar_x"], k["fond_z"]
    ztop = k.get("dessus_z") or (zc + k["dessus_au_dessus_collier"])
    xcol = m["x_pied"] + m["collier_hauteur"] * math.sin(qa)
    xf = k["avant_x"]                        # pointe avant au droit des joues
    xf_mid = k.get("avant_x_milieu", xf)     # pointe du fond au milieu (plat C1) : peut avancer seule (JD 29/09)
    b = k["bancs"]
    xr = xa + b["longueur"]
    af, ar_, bj = xcol - xf, xr - xcol, ztop - zb
    e, ef, ec = k["ep_bordé"], k["ep_flasque"], k["ep_cloison"]
    bois = cq.Color(0.80, 0.58, 0.38)
    # fond en V transversal, parallèle aux câbles de martingale : zb au milieu, zb_s au droit des joues
    wi = W / 2 - ef
    zb_s = k.get("fond_z_cotes", zb)
    cpl = k.get("fond_plat_demi", 0.0)      # fond polygonal : plat sur |y| <= cpl, puis pente jusqu'aux joues
    zb_at = lambda y: zb + (zb_s - zb) * max(0.0, min(1.0, (abs(y) - cpl) / (wi - cpl)))
    # dessus polygonal : plat (ztop) sur |y| <= cpt, puis pente jusqu'au collier au droit des joues
    zt_s = zc + k["dessus_cotes_au_dessus_collier"] if "dessus_cotes_au_dessus_collier" in k else ztop
    cpt = k.get("dessus_plat_demi", cpl)
    zt_at = lambda y: ztop + (zt_s - ztop) * max(0.0, min(1.0, (abs(y) - cpt) / (wi - cpt)))
    cpa = k.get("avant_plat_demi", cpl)     # pointe du fond : x avant_x_milieu sur ±cpa, raccord linéaire jusqu'aux joues
    xf_at = lambda y: xf_mid + (xf - xf_mid) * max(0.0, min(1.0, (abs(y) - cpa) / (wi - cpa)))
    # fond en pente vers l'avant (JD 29/09) : plat sous la batterie et le moteur jusqu'à x0, puis remonte jusqu'à la pointe
    # avant pour repousser les vagues vers le bas ; chaque panneau de fond reste plan (développable)
    fp = k.get("fond_pente")
    tp = math.tan(math.radians(fp["deg"])) if fp else 0.0
    x0p = min(fp["x0"], xa) if fp else xa
    D_ = tp * (x0p - xf)                                         # montée du fond à la pointe avant, au droit des joues
    Dq = lambda xf_: tp * max(0.0, x0p - xf_)                    # montée à une pointe xf_ : même pente partout -> panneaux de fond plans
    zfond = lambda x_, y_: zb_at(y_) + tp * max(0.0, x0p - x_)
    jf_ = k.get("joues_forme") or {}
    nj_av, nj_ar = jf_.get("n_avant", 2.0), jf_.get("n_arriere", 2.0)     # exposants des superellipses des joues (2 = ellipse)
    def profil(zb_, zt_=None, off=0.0, n=48, xf_=None, nexp=2.0):
        zt_ = ztop if zt_ is None else zt_
        xf_ = xf if xf_ is None else xf_
        Dl = Dq(xf_)
        a_, h_ = xcol - xf_ - off, zt_ - zb_ - Dl - 2 * off
        pts_ = [(xa - off, zb_ + off)] + ([(x0p, zb_ + off)] if Dl > 0 else [])
        # paramétrage à pente égale (réf. HREF) : entre deux stations, les génératrices relient des points de même
        # tangente -> bordés latéraux développables (pas de torsion) malgré des hauteurs, des pointes et des formes
        # différentes ; courbe avant = superellipse d'exposant nexp (2 = ellipse), tangente verticale à la pointe, horizontale au collier
        sref = HREF / (af - off)
        for i in range(n + 1):
            u = math.pi / 2 * i / n
            if i == 0:
                p_, q_ = 1.0, 0.0
            elif i == n:
                p_, q_ = 0.0, 1.0
            else:
                r_ = (sref / math.tan(u) * a_ / h_) ** (1.0 / (nexp - 1.0))
                q_ = (1.0 + r_ ** nexp) ** (-1.0 / nexp); p_ = r_ * q_
            pts_.append((xcol - a_ * p_, zb_ + Dl + off + h_ * q_))
        return pts_ + [(xa - off, zt_ - off)]
    n_at = lambda y: nj_av if abs(y) >= wi - 1e-6 else 2.0             # superellipse seulement à la station des joues
    def profil_st(yy, off):
        yq = min(abs(yy), wi)
        return profil(zb_at(yq), zt_at(yq), off, xf_=xf_at(yq), nexp=n_at(yq))
    ST_ = sorted({0.0, cpl, cpt, cpa, wi})
    def profil_y(y, off=0.0):                                          # section du loft réglé à un y quelconque (interpolation des stations)
        ya_ = min(abs(y), wi)
        for y0_, y1_ in zip(ST_, ST_[1:]):
            if y0_ <= ya_ <= y1_:
                t_ = (ya_ - y0_) / (y1_ - y0_)
                P0, P1 = profil_st(y0_, off), profil_st(y1_, off)
                return [(a0 + t_ * (a1 - a0), b0 + t_ * (b1 - b0)) for (a0, b0), (a1, b1) in zip(P0, P1)]
        return profil_st(ya_, off)
    def loft(off, y_ext):
        solids = []
        for sg in (1, -1):
            ys_ = sorted({0.0, cpl, cpt, cpa, y_ext})
            ys_ = [yy for yy in ys_ if yy <= y_ext]
            wires = [cq.Wire.makePolygon([V(x, sg * yy, z) for x, z in profil_st(yy, off)], close=True) for yy in ys_]
            solids.append(cq.Solid.makeLoft(wires, True))
        return solids[0].fuse(solids[1]).clean()
    af_mid = xcol - xf_mid
    Dm_ = Dq(xf_mid)
    avant = [(xcol - af_mid * math.cos(t), zb + Dm_ + (bj - Dm_) * math.sin(t)) for t in [math.pi / 2 * i / 48 for i in range(49)]]
    pts = [(xa, zb)] + ([(x0p, zb)] if Dm_ > 0 else []) + avant + [(xa, ztop)]
    inner = Polygon(pts).buffer(-e, join_style=2)
    ipts = list(inner.exterior.coords)[:-1]
    ext_s = loft(0.0, wi)
    int_s = loft(e, wi + 1)
    _sous = {}
    def sous_fond(tol=0.3):                                      # tout ce qui est sous la face intérieure du fond (pente et V compris), + tol
        if "s" not in _sous:
            x_lo, x_hi = xf_mid - 400, xa + 400
            sol_ = []
            for sg in (1, -1):
                wires = []
                for yy in sorted({0.0, cpl, cpt, cpa, wi, wi + 60}):
                    yq = min(yy, wi)
                    zi_ = zb_at(yq) + e + tol                    # face intérieure : même tracé que profil(off=e) (pente de Dl sur x0p - xf - e)
                    Dl = Dq(xf_at(yq))
                    if Dl > 0:
                        pts_ = [(x_lo, zi_ + Dl * (x0p - x_lo) / (x0p - xf_at(yq) - e)), (x0p, zi_), (x_hi, zi_)]
                    else:
                        pts_ = [(x_lo, zi_), (x0p, zi_), (x_hi, zi_)]
                    pts_ = [(x_lo, zb - 2000)] + pts_ + [(x_hi, zb - 2000)]
                    wires.append(cq.Wire.makePolygon([V(x_, sg * yy, z_) for x_, z_ in pts_], close=True))
                sol_.append(cq.Solid.makeLoft(wires, True))
            _sous["s"] = sol_[0].fuse(sol_[1]).clean()
        return _sous["s"]
    ppa = k.get("poches_pieces_angle")
    if ppa and PLAT.get("pa"):                                   # C4 contre la poutre : coins arrière évidés autour des pièces d'angle AV
        pa_, j_ = PLAT["pa"], ppa["jeu"]
        x_n = PLAT["fb"] - pa_["nez_x"] - j_
        z0_, z1_ = PLAT["zav"] - pa_["manchon_demi_h"] - j_, PLAT["zav"] + pa_["manchon_demi_h"] + j_
        if ppa.get("ouverte_dessous"):                             # (JD 30/09, pose par-dessus) poche ouverte dessous : la pièce d'angle y entre d'en bas
            z0_ = zb - 200
        for sg_ in (1, -1):
            y0_, y1_ = sorted((sg_ * (pa_["y_int"] - j_), sg_ * (W / 2 + 50)))
            ext_s = ext_s.cut(cq.Solid.makeBox(xa + 10 - x_n, y1_ - y0_, z1_ - z0_, V(x_n, y0_, z0_)))
            int_s = int_s.cut(cq.Solid.makeBox(xa + 10 - x_n + e, y1_ - y0_ + 2 * e, z1_ - z0_ + 2 * e, V(x_n - e, y0_ - e, z0_ - e)))
    coque = ext_s.cut(int_s)
    COFFRE_CACHE.clear(); COFFRE_CACHE.update(ext=ext_s, int=int_s, e=e)
    zpl = k["plateau_z"]
    plat = None
    if zpl < ztop - 60:
        plat = cq.Solid.makeBox(xa - xf_mid, 2 * wi, k["ep_plateau"], V(xf_mid, -wi, zpl - k["ep_plateau"])).intersect(int_s)
    mo = k.get("moteur")
    niche_ext = None
    if mo and mo.get("mode") == "transversal":
        tv = mo["transversal"]; fe = tv["fente"]
        fente = cq.Solid.makeBox(fe["x1"] - fe["x0"], fe["y1"] - fe["y0"], zb_s - zb + 120, V(fe["x0"], fe["y0"], zb - 60))
        volet = coque.intersect(fente)
        coque = coque.cut(fente)
        if tv.get("volet", True):
            # volet fermé : le fond découpé, moins une encoche autour de l'arbre en marche
            enc = cq.Solid.makeBox(fe["x1"] - fe["x0"] + 20, tv["encoche_arbre"], 200, V(fe["x0"] - 10, fe["y0"] - 10, zb - 100))
            A.add(volet.cut(enc), name="fond_volet", color=cq.Color(0.86, 0.66, 0.44))
    elif mo and mo.get("mode") == "arriere":
        am = mo["arriere"]; nn = am["niche"]; ym = am["y"]; en = nn["ep"]
        # puits du moteur : ouvert en dessous, fermé par deux parois longitudinales et une paroi avant jusqu'au bordé
        niche_ext = cq.Solid.makeBox(nn["x1"] - nn["x0"] + 2 * en, 2 * nn["demi_y"] + 2 * en, nn["z_haut"] + en - zb + 20,
                                     V(nn["x0"] - en, ym - nn["demi_y"] - en, zb - 20))
        niche_int = cq.Solid.makeBox(nn["x1"] - nn["x0"], 2 * nn["demi_y"], nn["z_haut"] - zb + 40, V(nn["x0"], ym - nn["demi_y"], zb - 40))
        coque = coque.cut(cq.Solid.makeBox(nn["x1"] - nn["x0"], 2 * nn["demi_y"], zb_s - zb + 100, V(nn["x0"], ym - nn["demi_y"], zb - 40)))  # ouverture du fond seulement
        enc4 = am.get("encoche_c4")
        if enc4:                                   # passage de l'arbre basculé sous le bas de la face arrière
            coque = coque.cut(cq.Solid.makeBox(xa - nn["x1"] + 20, 2 * enc4["demi_y"], enc4["z"] - zb + 60,
                                               V(nn["x1"] - 10, ym - enc4["demi_y"], zb - 60)))
        plat = plat.cut(niche_ext) if plat is not None else None
        niche = niche_ext.cut(niche_int).cut(cq.Solid.makeBox(4000, 4000, 1000, V(-1000, -2000, zb - 1000 + e))).intersect(int_s)
        A.add(niche, name="moteur_niche", color=cq.Color(0.70, 0.49, 0.30))
    elif mo and mo.get("mode") == "vertical2":
        # relevage vertical dans l'axe (JD 29/09 soir) : l'arbre coulisse dans sa bride, le bas du moteur reste sous le coffre.
        # Puits minimal : trou de l'arbre dans le fond + cheminée autour de la planche, de la bride et de la tête, ouverte dessus ;
        # C4 échancrée au-dessus de la poutre pour l'arrière de la tête ; la paroi avant ferme aussi le compartiment batterie.
        v2 = mo["vertical2"]; pu2 = v2["puits"]; tb2 = v2["tableau"]
        xs2, ys2 = v2["x_arbre"], v2["y"]
        ep2, dy2 = pu2["ep"], pu2["demi_y"]
        xpi = pu2.get("x_av", xs2 - tb2["devant_arbre"] - tb2["ep"] - pu2.get("serrage", 48))   # face intérieure de la paroi avant
        brun2 = cq.Color(0.70, 0.49, 0.30)
        bt_, cb_ = k.get("batterie"), k.get("compartiment_batterie")
        dyc = dy2 + ep2
        if bt_ and cb_:
            dyc = max(dyc, max(abs(bt_["y_ext"]), abs(bt_["y_ext"] + bt_["bac"][0])) + cb_["jeu"] + cb_["ep"])
        cai_ = (cb_ or {}).get("caisse") if bt_ else None
        if cai_:                                      # caisse de la batterie prolongée au-dessus du coffre (JD 29/09) : sa face arrière
            pl_ = cq.Solid.makeBox(ep2, 2 * dyc, 2000, V(xpi - ep2, ys2 - dyc, zb - 500))       # du fond au dessus du coffre, et jusqu'à z_haut là où il est plus bas
            cl_av = pl_.intersect(ext_s).fuse(pl_.intersect(cq.Solid.makeBox(4000, 4000, cai_["z_haut"] - zb + 500, V(-1000, -2000, zb - 500)))).clean().cut(sous_fond())
        else:
            cl_av = cq.Solid.makeBox(ep2, 2 * dyc, 2000, V(xpi - ep2, ys2 - dyc, zb - 500)).intersect(int_s)
        parois = [cq.Solid.makeBox(xa - e - xpi, ep2, 2000, V(xpi, ys2 + sg_ * dy2 + (0 if sg_ > 0 else -ep2), zb - 500)) for sg_ in (1, -1)]
        puits_ = parois[0].fuse(parois[1]).intersect(int_s)
        ouv = cq.Solid.makeBox(xa + 10 - xpi, 2 * dy2, 2000, V(xpi, ys2 - dy2, ztop - 60))                  # dessus ouvert dans la cheminée
        dye = v2.get("encoche_c4_demi_y", dy2)
        enc = cq.Solid.makeBox(e + 20, 2 * dye, 2000, V(xa - e - 10, ys2 - dye, v2["encoche_c4_z"]))       # échancrure de C4 (tête)
        if pu2.get("fond_ouvert"):                   # la nacelle et l'hélice rentrent : fond ouvert sur toute la section du puits
            trou = cq.Solid.makeBox(xa - e - xpi, 2 * dy2, 250 + tp * max(0.0, x0p - xpi), V(xpi, ys2 - dy2, zb - 100))
        else:                                        # seul passage dans le fond : l'arbre
            trou = cq.Solid.makeCylinder(v2["trou_fond"] / 2, 200, V(xs2, ys2, zb - 100))
        coque = coque.cut(ouv).cut(enc).cut(trou)
        A.add(cl_av, name="coffre_cloison_moteur", color=bois)
        A.add(puits_, name="moteur_puits", color=brun2)
        niche_ext = cq.Solid.makeBox(xa - xpi + ep2 + 1, 2 * (dy2 + ep2), 2000, V(xpi - ep2, ys2 - dy2 - ep2, zb - 500))
        k["_puits"] = dict(x_av=xpi - ep2, x_int=xpi, demi_y=dy2, ep=ep2, largeur_cloison=2 * dyc)
    elif mo and mo.get("mode") == "avant2":
        av2 = mo["avant2"]; fe_, ca_ = av2["fente"], av2["canal"]; ym2 = av2["y"]
        xs2 = av2["pivot_x"] - av2["arbre_devant_pivot"]
        brun2 = cq.Color(0.70, 0.49, 0.30)
        wf, ef2, wc, ec2 = fe_["larg"] / 2, fe_["ep"], ca_["demi_larg"], ca_["ep"]
        # fente de l'arbre : fond et face avant, de la pointe jusque derrière l'arbre, jusqu'à la hauteur du coffrage
        fente = cq.Solid.makeBox(xs2 + 25 - (xf - 60), 2 * wf, fe_["haut"] - zb + 60, V(xf - 60, ym2 - wf, zb - 60))
        # canal de la tête : ouvert dessus, de x0 jusqu'à x_ouvert
        ouv = cq.Solid.makeBox(ca_["x_ouvert"] - ca_["x0"] - ec2, 2 * wc, 1500, V(ca_["x0"] + ec2, ym2 - wc, fe_["haut"]))
        coque = coque.cut(fente).cut(ouv)
        parois = []
        for sgw in (1, -1):                          # coffrage de la fente (joues + couvercle), jusqu'au canal
            parois.append(cq.Solid.makeBox(ca_["x0"] - (xf - 60), ef2, fe_["haut"] + ef2 - zb + 60, V(xf - 60, ym2 + sgw * wf + (0 if sgw > 0 else -ef2), zb - 60)))
        parois.append(cq.Solid.makeBox(ca_["x0"] - (xf - 60), 2 * (wf + ef2), ef2, V(xf - 60, ym2 - wf - ef2, fe_["haut"])))
        for sgw in (1, -1):                          # parois du canal de la tête, de x0 jusqu'à C4
            parois.append(cq.Solid.makeBox(xa - ca_["x0"], ec2, 2000, V(ca_["x0"], ym2 + sgw * wc + (0 if sgw > 0 else -ec2), zb - 500)))
        fav = cq.Solid.makeBox(ec2, 2 * (wc + ec2), 2000, V(ca_["x0"], ym2 - wc - ec2, zb - 500)).cut(
            cq.Solid.makeBox(ec2 + 2, 2 * wf, fe_["haut"] - zb + 500, V(ca_["x0"] - 1, ym2 - wf, zb - 500)))
        parois.append(fav)
        puits2 = parois[0]
        for q_ in parois[1:]:
            puits2 = puits2.fuse(q_)
        puits2 = puits2.cut(fente.cut(cq.Solid.makeBox(ca_["x0"] - xf + 100, 2 * wf, 2000, V(xf - 100, ym2 - wf, fe_["haut"])))).intersect(int_s).cut(ouv)
        A.add(puits2, name="moteur_puits", color=brun2)
        niche_ext = cq.Solid.makeBox(xa - ca_["x0"] + 1, 2 * (wc + ec2), 2000, V(ca_["x0"], ym2 - wc - ec2, zb - 500)).fuse(
            cq.Solid.makeBox(ca_["x0"] - xf + 100, 2 * (wf + ef2), fe_["haut"] + ef2 - zb + 100, V(xf - 100, ym2 - wf - ef2, zb - 100)))
    elif mo and mo.get("mode") == "avant" and "boite" in mo["avant"]:
        bo = mo["avant"]["boite"]
        ep_p = bo["ep"]
        # boîte étroite au milieu du coffre : fente ouverte en dessous et dans la face avant (jusqu'à z_fente)
        niche_ext = cq.Solid.makeBox(xa - xf + 50, 2 * bo["demi_y"] + 2 * ep_p, 1500, V(xf - 50, -bo["demi_y"] - ep_p, zb - 200))
        niche_ext = niche_ext.cut(cq.Solid.makeBox(xa - bo["x_ar"], 2 * bo["demi_y"] + 2 * ep_p, 1500, V(bo["x_ar"] + ep_p, -bo["demi_y"] - ep_p, zb - 200)))
        vide = cq.Solid.makeBox(bo["x_ar"] - xf + 50, 2 * bo["demi_y"], 1500, V(xf - 50, -bo["demi_y"], zb - 200))
        coque = coque.cut(vide)
        plat = plat.cut(niche_ext) if plat is not None else None
        parois = niche_ext.cut(vide).intersect(ext_s)
        # face avant de la boîte au-dessus de la fente (ferme la boîte devant, au-dessus de z_fente)
        av_pts = [(x, z) for x, z in avant if z >= bo["z_fente"]]
        if av_pts:
            fb = cq.Workplane("XZ", origin=(0, bo["demi_y"], 0)).polyline([(xa, bo["z_fente"])] + [(x, z) for x, z in avant if z >= bo["z_fente"]] + [(xa, ztop)]).close().extrude(2 * bo["demi_y"]).val()
            peau = fb.cut(cq.Workplane("XZ", origin=(0, bo["demi_y"] + 1, 0)).polyline(
                [(xa, bo["z_fente"])] + [(x, z) for x, z in list(inner.exterior.coords) if z >= bo["z_fente"] and x < xa - 1] + [(xa, ztop - e)]).close().extrude(2 * bo["demi_y"] + 2).val())
            if bo.get("face_fermee", False):
                A.add(peau, name="moteur_boite_face", color=cq.Color(0.70, 0.49, 0.30))
        A.add(parois, name="moteur_boite", color=cq.Color(0.70, 0.49, 0.30))
    elif mo and mo.get("mode", "vertical") == "vertical":
        pu = mo["puits"]
        ep_p = pu["ep"]
        # boîte verticale traversant le coffre : passage de l'arbre et de la tête au relevage
        niche_ext = cq.Solid.makeBox(pu["x1"] - pu["x0"] + 2 * ep_p, 2 * pu["demi_y"] + 2 * ep_p, 1500,
                                     V(pu["x0"] - ep_p, -pu["demi_y"] - ep_p, zb - 200))
        niche_int = cq.Solid.makeBox(pu["x1"] - pu["x0"], 2 * pu["demi_y"], 1500, V(pu["x0"], -pu["demi_y"], zb - 200))
        coque = coque.cut(niche_ext)
        plat = plat.cut(niche_ext) if plat is not None else None
        puits = niche_ext.cut(niche_int).intersect(ext_s)
        A.add(puits, name="moteur_puits", color=cq.Color(0.70, 0.49, 0.30))
    tr_ = k.get("trappe")
    if tr_:
        z0h = tr_.get("z_seuil", ztop - 250)          # hayon : dessus + haut de la face arrière au-dessus du seuil
        blk = cq.Solid.makeBox(tr_["x1"] - tr_["x0"], tr_["y1"] - tr_["y0"], zt_s + 400 - z0h, V(tr_["x0"], tr_["y0"], z0h))
        if not tr_.get("ouverte"):                  # ouverte : pas de couvercle, celui du bac suffit (JD 29/09)
            A.add(coque.intersect(blk), name="coffre_capot", color=cq.Color(0.86, 0.66, 0.44))
        coque = coque.cut(blk)
    for i, t4 in enumerate(k.get("trappes_c4") or [], 1):      # trappes de visite dans la face arrière
        blk = cq.Solid.makeBox(e + 10, t4["y1"] - t4["y0"], t4["z1"] - t4["z0"], V(xa - e - 5, t4["y0"], t4["z0"]))
        A.add(coque.intersect(blk), name=f"coffre_trappe_c4_{i}", color=cq.Color(0.86, 0.66, 0.44))
        coque = coque.cut(blk)
    A.add(coque, name="coffre_coque", color=bois)
    if plat is not None:
        A.add(plat, name="coffre_plateau", color=bois)
    if "cloisons_y" in k:                                        # liste explicite (vide = pas de cloison en plus)
        ycs = list(k["cloisons_y"] or [])
    else:
        n = max(0, math.ceil(2 * wi / k["pas_cloisons"]) - 1)
        ycs = [-wi + 2 * wi * i / (n + 1) for i in range(1, n + 1)]
    for i, yc in enumerate(ycs, 1):
        cl = cq.Workplane("XZ", origin=(0, yc + ec / 2, 0)).polyline(profil_y(yc, e)).close().extrude(ec).val()
        if niche_ext is not None:
            cl = cl.cut(niche_ext)
        if cl.Volume() > 1:
            A.add(cl, name=f"coffre_cloison_{i}", color=bois)
    def y_dep_(v_):                                          # départ d'un couple transversal : face extérieure de la caisse batterie ou du puits moteur
        if v_ == "caisse":
            bt0, cb0 = k.get("batterie"), k.get("compartiment_batterie")
            return max(abs(bt0["y_ext"]), abs(bt0["y_ext"] + bt0["bac"][0])) + cb0["jeu"] + cb0["ep"]
        if v_ == "puits":
            pq_ = k.get("_puits", {})
            return pq_.get("demi_y", 0) + pq_.get("ep", 0)
        return float(v_ or 0)
    trav_ = [(ct_["x"], ct_.get("ep", ec), y_dep_(ct_.get("y0"))) for ct_ in (k.get("couples_travers") or [])]
    for cc_ in k.get("couples_coffre") or []:              # couples dans le coffre, dans le plan des accroches de la poutre AV (JD 29/09)
        from shapely.geometry import Polygon as _Pg, box as _bx
        for nomc, sgc in (("babord", 1), ("tribord", -1)):
            yc = sgc * cc_["y"]; ecc = cc_.get("ep", ec)
            pg = _Pg(profil_y(yc, e))
            x0c = cc_.get("x0")
            if x0c == "puits":
                x0c = k.get("_puits", {}).get("x_int")
            if x0c:
                pg = pg.intersection(_bx(x0c, -1e4, 1e5, 1e4))
            if pg.is_empty or pg.area < 100:
                continue
            cl = cq.Workplane("XZ", origin=(0, yc + ecc / 2, 0)).polyline(list(pg.exterior.coords)[:-1]).close().extrude(ecc).val()
            ev = cc_.get("evidement")
            if ev:                                            # évidé : on garde un cadre de `marge` le long du bordé, de C4 et du fond
                ouv_ = pg.buffer(-ev["marge"], join_style=2)
                for xt_, et_, yt_ in trav_:                   # poteau plein au droit de chaque couple transversal qui le croise (collage + congés)
                    if yt_ < cc_["y"]:
                        ouv_ = ouv_.difference(_bx(xt_ + et_ / 2 - (et_ + ev["marge"]) / 2, -1e4, xt_ + et_ / 2 + (et_ + ev["marge"]) / 2, 1e4))
                tr_ = ouv_.buffer(-ev["rayon"], join_style=2).buffer(ev["rayon"])
                for tp_ in (getattr(tr_, "geoms", None) or [tr_]):
                    if not tp_.is_empty and tp_.area > 100:
                        cl = cl.cut(cq.Workplane("XZ", origin=(0, yc + ecc / 2 + 1, 0)).polyline(list(tp_.exterior.coords)[:-1]).close().extrude(ecc + 2).val())
            cl = cl.intersect(int_s)                          # suit la pente du dessus et du fond sur son épaisseur
            if niche_ext is not None:
                cl = cl.cut(niche_ext)
            if cl.Volume() > 1:
                A.add(cl, name=f"couple_coffre_{nomc}_{int(cc_['y'])}", color=bois)
    if trav_:                                                # couples transversaux des baies latérales (JD 29/09) : sur les pylônes, au droit des colliers
        from shapely.geometry import Polygon as _Pg, LineString as _Ls
        def sec_yz(x0q, x1q, ya, yb, n=32):                # section intérieure (y, z) commune aux deux faces du couple
            bas, haut = [], []
            for i in range(n + 1):
                yq = ya + (yb - ya) * i / n
                pq = _Pg(profil_y(yq, e))
                zz = [_Ls([(xq, -1e4), (xq, 1e4)]).intersection(pq).bounds for xq in (x0q, x1q)]
                if any(len(z_) < 4 for z_ in zz):
                    continue
                bas.append((yq, max(z_[1] for z_ in zz))); haut.append((yq, min(z_[3] for z_ in zz)))
            return _Pg(bas + haut[::-1]) if len(bas) > 2 else None
        # couples longitudinaux croisés : (|y|, épaisseur, x début, x fin)
        longs_ = []
        for cc_ in k.get("couples_coffre") or []:
            x0c = cc_.get("x0")
            x0c = k.get("_puits", {}).get("x_int") if x0c == "puits" else x0c
            longs_.append((cc_["y"], cc_.get("ep", ec), x0c or 0, xa))
        for it_, (ct_, (x0t, ect, y0t)) in enumerate(zip(k["couples_travers"], trav_)):
            bornes = [y0t]
            for yl, el, xl0, xl1 in sorted(longs_):
                if y0t < yl < wi and xl0 < x0t + ect and x0t < xl1:
                    bornes += [yl - el / 2, yl + el / 2]
            bornes.append(wi)
            troncons = [(bornes[i], bornes[i + 1]) for i in range(0, len(bornes) - 1, 2)]
            for nomc, sgc in (("babord", 1), ("tribord", -1)):
                for j_, (ya, yb) in enumerate(troncons):
                    y_lo, y_hi = sorted((sgc * ya, sgc * yb))
                    cl = cq.Solid.makeBox(ect, y_hi - y_lo, 2000, V(x0t, y_lo, zb - 500)).intersect(int_s)
                    ev = ct_.get("evidement")
                    sq = sec_yz(x0t, x0t + ect, y_lo, y_hi) if ev else None
                    if sq is not None:
                        tr_ = sq.buffer(-(ev["marge"] + ev["rayon"]), join_style=2).buffer(ev["rayon"])
                        if not tr_.is_empty and tr_.area > 100:
                            cl = cl.cut(cq.Workplane("YZ", origin=(x0t - 1, 0, 0)).polyline(list(tr_.exterior.coords)[:-1]).close().extrude(ect + 2).val())
                    if niche_ext is not None:
                        cl = cl.cut(niche_ext)
                    if cl.Volume() > 1:
                        A.add(cl, name=f"couple_coffre_travers_{nomc}_{int(round(x0t + ect / 2))}_{j_}", color=bois)
        k["_couples_travers"] = [dict(x=(x0t, x0t + ect), y0=y0t, ep=ect) for x0t, ect, y0t in trav_]
    bt = k.get("batterie")
    if bt:
        # batterie dans son bac, sur deux cales qui mettent le fond en pente de niveau
        x0b, y0b, y1b = bt["x_ar"] - bt["bac"][1], bt["y_ext"], bt["y_ext"] + bt["bac"][0]
        if bt.get("appui_direct"):
            zpl_b = zb + e
        elif isinstance(bt.get("cales"), dict):                   # fond en pente et en V sous le bac : deux cales transversales taillées au fond
            cl_ = bt["cales"]
            zpl_b = max(zfond(xq, yq) + e for xq in (x0b, bt["x_ar"]) for yq in (y0b, y1b, 0.0)) + cl_["jeu"]
            for nom, xc in (("av", x0b + 20), ("ar", bt["x_ar"] - 20 - cl_["ep"])):
                cale = cq.Solid.makeBox(cl_["ep"], y1b - y0b, zpl_b - zb + 500, V(xc, y0b, zb - 500)).cut(sous_fond())
                A.add(cale, name=f"batterie_cale_{nom}", color=cq.Color(0.13, 0.13, 0.14))
        elif bt.get("lisses"):
            li = bt["lisses"]; zpl_b = zb + e + li["h"]
            for j, yl in enumerate(li["y"], 1):
                A.add(cq.Solid.makeBox(bt["bac"][1], li["larg"], li["h"], V(x0b, yl - li["larg"] / 2, zb + e)), name=f"batterie_lisse_{j}", color=cq.Color(0.55, 0.36, 0.20))
        else:
            zpl_b = max(zb_at(y0b), zb_at(y1b)) + e + bt["jeu_cale"]
            for nom, xc in (("av", x0b + 20), ("ar", bt["x_ar"] - 20 - bt["cale_ep"])):
                ks_ = [yy for yy in (-cpl, cpl) if y0b < yy < y1b]            # cassures du fond sous le bac
                pts_c = [(y0b, zb_at(y0b) + e)] + [(yy, zb_at(yy) + e) for yy in ks_] + [(y1b, zb_at(y1b) + e), (y1b, zpl_b), (y0b, zpl_b)]
                cale = cq.Workplane("YZ", origin=(xc, 0, 0)).polyline(pts_c).close().extrude(bt["cale_ep"]).val()
                A.add(cale, name=f"batterie_cale_{nom}", color=cq.Color(0.66, 0.42, 0.22))
        bac = cq.Solid.makeBox(bt["bac"][1], bt["bac"][0], bt["bac"][2], V(x0b, y0b, zpl_b))
        A.add(bac.cut(cq.Solid.makeBox(bt["bac"][1] - 8, bt["bac"][0] - 8, bt["bac"][2] - 8, V(x0b + 4, y0b + 4, zpl_b + 4))), name="batterie_bac", color=cq.Color(0.2, 0.22, 0.25))   # bac fermé par son couvercle
        cx, cy = x0b + bt["bac"][1] / 2, (y0b + y1b) / 2
        A.add(cq.Solid.makeBox(bt["cellule"][1], bt["cellule"][0], bt["cellule"][2], V(cx - bt["cellule"][1] / 2, cy - bt["cellule"][0] / 2, zpl_b + 4)), name="batterie", color=cq.Color(0.12, 0.35, 0.55))
        k["_batterie"] = dict(x=(x0b, bt["x_ar"]), y=(y0b, y1b), z=(zpl_b, zpl_b + bt["bac"][2]), cg=(cx, cy, zpl_b + 4 + bt["cellule"][2] / 2))
        cb = k.get("compartiment_batterie")
        if cb:                                                    # compartiment juste à la taille du bac (JD 29/09) : 3 cloisons + C4, fermé par la trappe
            jb, eb_ = cb["jeu"], cb["ep"]
            xw, ya_, yb_ = x0b - jb - eb_, y0b - jb - eb_, y1b + jb
            x_fin = k.get("_puits", {}).get("x_av", xa)          # arrière : cloison du puits moteur (vertical2) ou C4
            parois = (("avant", cq.Solid.makeBox(eb_, yb_ + eb_ - ya_, 2000, V(xw, ya_, zb - 500))),
                      ("tribord", cq.Solid.makeBox(x_fin - xw - eb_, eb_, 2000, V(xw + eb_, ya_, zb - 500))),
                      ("babord", cq.Solid.makeBox(x_fin - xw - eb_, eb_, 2000, V(xw + eb_, yb_, zb - 500))))
            cai = cb.get("caisse")
            for nom_, pb_ in parois:
                if nom_ == "tribord" and ya_ < -wi or nom_ == "babord" and yb_ + eb_ > wi:
                    continue                              # contre la joue : c'est elle qui ferme le compartiment
                if cai:                                   # caisse : parallélépipède du fond jusqu'à z_haut, traverse le dessus
                    pb_ = pb_.intersect(ext_s).fuse(pb_.intersect(cq.Solid.makeBox(4000, 4000, cai["z_haut"] - zb + 500, V(-1000, -2000, zb - 500)))).clean().cut(sous_fond())
                else:
                    pb_ = pb_.intersect(int_s)
                if niche_ext is not None:
                    pb_ = pb_.cut(niche_ext)
                if pb_.Volume() > 1:
                    A.add(pb_, name=f"coffre_batterie_{nom_}", color=bois)
            k["_batterie"]["compartiment"] = dict(x=(xw + eb_, x_fin if x_fin < xa else xa - e), y=(ya_ + eb_, yb_))
            if cai:                                       # couvercle de la caisse (amovible) et ancre posée dessus, sanglée
                x1c = x_fin + (k.get("_puits", {}).get("ep", 0) if x_fin < xa else 0)
                ecv = cai.get("couvercle", 9) or 0
                if ecv:
                    A.add(cq.Solid.makeBox(x1c - xw, yb_ + eb_ - ya_, ecv, V(xw, ya_, cai["z_haut"])), name="coffre_caisse_couvercle", color=bois)
                k["_batterie"]["caisse"] = dict(x=(xw, x1c), y=(ya_, yb_ + eb_), z_haut=cai["z_haut"] + ecv)
                an = k.get("ancre")
                if an:
                    galva = cq.Color(0.55, 0.57, 0.58)
                    z_an = k["_batterie"]["z"][1] if an.get("sur") == "bac" else cai["z_haut"] + ecv     # sur le couvercle du bac (caisse ouverte) ou sur celui de la caisse
                    zc_a = z_an + an["faisceau"][1] / 2
                    xa_, ya0 = an.get("x", (xw + x1c) / 2), an.get("y0", -an["faisceau"][0] / 2)
                    A.add(cq.Solid.makeCylinder(an["faisceau"][1] / 2, an["faisceau"][0], V(xa_, ya0, zc_a), V(0, 1, 0)), name="ancre_faisceau", color=galva)
                    y1a = ya0 + an["faisceau"][0]
                    A.add(cq.Solid.makeCylinder(an["verge"][1] / 2, an["verge"][0], V(xa_, y1a, zc_a), V(0, 1, 0)), name="ancre_verge", color=galva)
                    ra = an["anneau"] / 2
                    A.add(cq.Solid.makeTorus(ra, 5, V(xa_, y1a + an["verge"][0] + ra - 5, zc_a), V(0, 0, 1)), name="ancre_anneau", color=galva)
                    k["_ancre"] = dict(x=xa_, y=(ya0, y1a + an["verge"][0] + 2 * ra), z=(z_an, zc_a + an["faisceau"][1] / 2))
    fl_ = k.get("fourreaux_livarde")
    if fl_:                                              # livarde rangée (JD 30/09) : verticale, trou dans le dessus + fourreau dans le coffre, collier ouvert sur le dessus
        xr_ = xcol - fl_["dx"]; rf_, ef_ = fl_["diam"] / 2, fl_["ep"]
        k["_fourreau"] = {}
        for nomf, sgf in (("babord", 1), ("tribord", -1)):
            yr_ = sgf * fl_["y"]
            co_ = next(ch.obj for ch in A.children if ch.name == "coffre_coque")
            co_ = co_.val() if isinstance(co_, cq.Workplane) else co_
            zt_f = co_.intersect(cq.Solid.makeBox(1, 1, 3000, V(xr_ - 0.5, yr_ - 0.5, 0))).BoundingBox().zmax
            z0f = zt_f - fl_["l"]
            gaine = cq.Solid.makeCylinder(rf_, fl_["l"] + 2, V(xr_, yr_, z0f - 2)).cut(cq.Solid.makeCylinder(rf_ - ef_, fl_["l"] + 2, V(xr_, yr_, z0f)))
            gaine = gaine.intersect(int_s.fuse(cq.Solid.makeBox(200, 200, 200, V(xr_ - 100, yr_ - 100, zt_f - 20))))   # dans le coffre, jusqu'au dessus
            for ch in A.children:                        # trou dans le dessus
                if ch.name == "coffre_coque":
                    ch.obj = (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj).cut(cq.Solid.makeCylinder(rf_, 300, V(xr_, yr_, zt_f - 150)))
            A.add(gaine, name=f"livarde_fourreau_{nomf}", color=cq.Color(0.13, 0.13, 0.14))
            cf_ = fl_.get("collier")
            if cf_:                                      # collier ouvert (clip) posé sur le dessus autour du trou
                ang_o = math.degrees(math.asin(min(0.99, cf_["ouverture"] / 2 / (rf_ + 6))))
                bague = cq.Solid.makeCylinder(rf_ + 6, cf_["h"], V(xr_, yr_, zt_f + 0.5)).cut(cq.Solid.makeCylinder(rf_ - ef_ + 0.5, cf_["h"], V(xr_, yr_, zt_f + 0.5)))
                fente = cq.Solid.makeBox(rf_ + 10, cf_["ouverture"], cf_["h"] + 2, V(xr_ - rf_ - 10, yr_ - cf_["ouverture"] / 2, zt_f - 0.5))   # ouverture vers l'avant
                co2_ = next(ch.obj for ch in A.children if ch.name == "coffre_coque")
                A.add(bague.cut(fente).cut(co2_.val() if isinstance(co2_, cq.Workplane) else co2_), name=f"livarde_collier_{nomf}", color=cq.Color(0.13, 0.13, 0.14))
            k["_fourreau"][nomf] = dict(x=xr_, y=yr_, z_bas=z0f, z_dessus=zt_f, r=rf_ - ef_)
    tb_ = k.get("table")
    if tb_:                                              # table (JD 30/09) : planche légère posée sur la caisse et le dessus plat, jusqu'au-dessus de la poutre AV
        zt0 = tb_.get("z", ztop)
        tab = cq.Solid.makeBox(tb_["x1"] - tb_["x0"], 2 * tb_["demi_y"], tb_["ep"], V(tb_["x0"], -tb_["demi_y"], zt0))
        dmo = tb_.get("decoupe_moteur")
        if dmo:                                          # passage de la tête et de la barre (en marche et au relevage)
            tab = tab.cut(cq.Solid.makeBox(dmo["x1"] - dmo["x0"], 2 * dmo["demi_y"], tb_["ep"] + 2, V(dmo["x0"], -dmo["demi_y"], zt0 - 1)))
        A.add(tab, name="coffre_table", color=bois)
        k["_table"] = dict(x=(tb_["x0"], tb_["x1"]), demi_y=tb_["demi_y"], z=(zt0, zt0 + tb_["ep"]))
    k["_geom"] = dict(zt=ztop, zt_s=zt_s, xcol=xcol, avant=xf, avant_milieu=xf_mid, af_milieu=af_mid, arriere=xr, af=af, ar=ar_, b=bj, volume_L=ext_s.Volume() / 1e6, fond_cotes=zb_s,
                      fond_pente=dict(x0=x0p, montee=D_, montee_milieu=Dm_, deg=fp["deg"] if fp else 0))
    # pattes verticales de collier : sur la face extérieure des joues, devant et derrière le mât, jusqu'au collier
    pc = k.get("pattes_collier")
    if pc and zt_s < zc:                   # inutiles quand la joue monte jusqu'au collier
        alu = cq.Color(0.72, 0.74, 0.77)
        z0p, z1p = ztop - pc["recouvrement"], zc + pc["au_dessus_axe_collier"]
        for nom, sg in (("babord", 1), ("tribord", -1)):
            y0p = W / 2 if sg > 0 else -W / 2 - pc["ep"]
            for cote, x0pc in (("av", xcol - pc["ecart"] - pc["larg"]), ("ar", xcol + pc["ecart"])):   # (x0p : début de la pente du fond, ne pas l'écraser)
                A.add(cq.Solid.makeBox(pc["larg"], pc["ep"], z1p - z0p, V(x0pc, y0p, z0p)), name=f"patte_collier_{nom}_{cote}", color=alu)
    # joues : quart d'ellipse avant + quart d'ellipse arrière (dossier jusqu'au bout du banc)
    bj_s = zt_s - zb_s
    PJ_ = profil_st(wi, 0.0)                                            # joue = profil extérieur du coffre à sa station (superellipse n_avant)
    avant_j = PJ_[(2 if D_ > 0 else 1):-1]                              # de la pointe (tangente verticale) au collier (tangente horizontale)
    x_dos = xa if jf_.get("plat_jusqu_a_c4") else xcol                  # dessus plat du collier à C4, comme le coffre, puis dossier
    ar2 = xr - x_dos
    arriere = ([(x_dos, zt_s)] if x_dos > xcol + 1 else []) + [(x_dos + ar2 * math.sin(t) ** (2 / nj_ar), zb_s + bj_s * math.cos(t) ** (2 / nj_ar))
                                                           for t in [math.pi / 2 * i / 48 for i in range(1, 49)]]
    prof = avant_j + arriere + ([(x0p, zb_s)] if D_ > 0 else [])        # bas de joue : suit le fond (pente à l'avant)
    yy_ = k.get("yinyang")
    if yy_ and yy_.get("joues"):                            # dessin du bateau (JD 29/09) : yin-yang sur la face extérieure des joues
        jy = yy_["joues"]
        poser_yinyang(A, "joue_babord", jy["r"], W / 2, jy.get("ep", 0.5), jy["x"], jy["z"])
        poser_yinyang(A, "joue_tribord", jy["r"], -W / 2, -jy.get("ep", 0.5), jy["x"], jy["z"], miroir=True)
    JOUES = {}
    for nom, y0 in (("babord", W / 2), ("tribord", -wi)):
        fl = cq.Workplane("XZ", origin=(0, y0, 0)).polyline(prof).close().extrude(ef).val()
        if PLAT:                                           # joue au-dessus du longeron : dégagée autour de la pièce d'angle AV et du longeron
            sgj = 1 if y0 > 0 else -1
            if b.get("joue_jusqu_au_longeron"):             # rangement sous l'assise : la joue descend jusqu'au longeron (JD 29/09)
                fl = fl.cut(degagement_joue(sgj, y0, ef, xr + 20, None, b.get("jeu_joue_longeron", 2), (k.get("accroches_poutre") or {}).get("pose")))
            else:
                fl = fl.cut(degagement_joue(sgj, y0, ef, xr + 20, b.get("plan_z")))
            JOUES[nom] = fl
        elif POUTRE_AV.get("degagement") is not None:
            pa = POUTRE_AV; ya = abs(y0) + ef / 2; zax = z_cambre(ya, pa["z_ext"], pa["fleche"], pa.get("y_libre", pa["y_ext"]))
            fl = fl.cut(POUTRE_AV["degagement"])            # encoche en U : la joue se pose sur la poutre par-dessus
            fl = fl.cut(cq.Solid.makeBox(pa["u1"] - pa["u0"], ef + 20, zax - zb_s + 20, V(pa["x"] + pa["u0"], y0 - 10, zb_s - 20)))
        else:
            fl = fl.cut(cq.Solid.makeCylinder(b["encoche_poutre_r"], ef + 20, V(b["poutre_x"], y0 + 10, b["poutre_z"]), V(0, -1, 0)))
        A.add(fl, name=f"joue_{nom}", color=cq.Color(0.74, 0.52, 0.34))
    rl_ = k.get("rangement_livarde")
    if rl_:                                              # livarde rangée (JD 30/09 soir) : debout contre la face extérieure de la joue, devant le mât ;
        from shapely.geometry import Polygon as _PJ, LineString as _LJ     # en bas un godet (trou), en haut un collier ouvert, tous deux collés sur la joue
        lvd_ = k.get("_livarde_diam", 30); rl2 = lvd_ / 2
        x_l = xcol - rl_["dx"]; y_l = W / 2 + rl_["jeu"] + rl2
        zz_ = _LJ([(x_l, -1e4), (x_l, 1e4)]).intersection(_PJ(prof)).bounds
        z_bot_, z_top_ = zz_[1], zz_[3]
        bl_ = rl_["bloc"]; lb_, sb_, eb_ = bl_["larg"], bl_["saillie"], bl_["ep"]
        z_g = z_bot_ + rl_["godet"]["au_dessus_bas"]
        z_c = z_top_ - rl_["collier"]["sous_haut"] - 2 * eb_
        k["_fourreau"] = {}
        noir_ = cq.Color(0.13, 0.13, 0.14)
        for nomf, sgf in (("babord", 1), ("tribord", -1)):
            y0b = W / 2 if sgf > 0 else -W / 2 - sb_
            blk = lambda z0_, h_: cq.Solid.makeBox(lb_, sb_, h_, V(x_l - lb_ / 2, y0b, z0_))
            trou_ = cq.Solid.makeCylinder(rl_["godet"]["diam"] / 2, 3 * eb_, V(x_l, sgf * y_l, z_g - eb_))
            A.add(blk(z_g, eb_), name=f"livarde_godet_fond_{nomf}", color=noir_)                       # pli du fond, plein : le pied y repose
            A.add(blk(z_g + eb_, eb_).cut(trou_), name=f"livarde_godet_{nomf}", color=noir_)           # pli percé : le trou
            ouv_ = cq.Solid.makeBox(rl_["collier"]["ouverture"], sb_ + 10, 2 * eb_ + 2,
                                    V(x_l - rl_["collier"]["ouverture"] / 2, sgf * y_l if sgf > 0 else sgf * y_l - sb_ - 10, z_c - 1))   # ouvert vers l'extérieur
            siege_ = cq.Solid.makeCylinder(rl_["collier"]["diam"] / 2, 2 * eb_ + 2, V(x_l, sgf * y_l, z_c - 1))
            A.add(blk(z_c, 2 * eb_).cut(siege_).cut(ouv_), name=f"livarde_collier_{nomf}", color=noir_)
            k["_fourreau"][nomf] = dict(x=x_l, y=sgf * y_l, z_bas=z_g + eb_, z_dessus=z_c + 2 * eb_, r=rl_["godet"]["diam"] / 2)
        k["_rangement_livarde"] = dict(x=round(x_l, 1), y=round(y_l, 1), joue_z=[round(z_bot_, 1), round(z_top_, 1)], godet_z=round(z_g, 1), collier_z=round(z_c, 1))
    zt0, L, hb = b["plan_z"], b["longueur"], b["hauteur"]
    zs = zt0 + hb
    # martingale (ancienne place, dans « coffre ») : pilier sous le milieu de la poutre AV + deux tiges inox vers les pylônes
    mg = k.get("martingale")
    if mg:
        gm = cq.Color(0.55, 0.55, 0.58)
        pa = POUTRE_AV or dict(x=mg["x"], z_ext=b["poutre_z"], fleche=0, r=38)
        xm_ = pa["x"]
        z_haut = pa["z_ext"] + pa["fleche"] - pa["r"]
        z_bas = pa["z_ext"] - mg["pied_sous_axe_extremites"]
        mg["_z_bas"] = z_bas
        top = V(xm_, 0, z_haut); bas = V(xm_, 0, z_bas)
        A.add(cq.Solid.makeCylinder(12, (top - bas).Length, bas, (top - bas).normalized()), name="martingale_pilier", color=gm)
        for nom, sg in (("babord", 1), ("tribord", -1)):
            ext_ = V(xm_, sg * mg["y_cable"], pa["z_ext"] - mg["cable_sous_axe_extremites"])
            A.add(cq.Solid.makeCylinder(mg.get("tige_diam", 6) / 2, (ext_ - bas).Length, bas, (ext_ - bas).normalized()), name=f"martingale_tige_{nom}", color=gm)
    # moteur, mode "arriere" : chaise pivotante fixée au fond du coffre (charnière transversale) ;
    # le moteur reste serré à 0° sur sa planche, c'est la chaise entière qui bascule vers l'arrière sous la martingale
    if mo and mo.get("mode") == "transversal":
        # moteur centré ; chaise pivotante : charnière longitudinale (axe x) dans le coffre, décalée côté tête ;
        # relevé : moteur couché en travers dans le coffre, au-dessus du fond (fente fermée par le volet)
        tv = mo["transversal"]
        brun = cq.Color(0.55, 0.36, 0.20); acier = cq.Color(0.6, 0.6, 0.62)
        xs_, e_h, zh = tv["x_arbre"], tv["charniere_decalage"], tv["charniere_z"]
        yh = -e_h
        ang = tv.get("bascule", 0)
        # fixe : deux paliers sur le fond, côté tête
        for nom, xp in (("av", tv["palier_av_x"]), ("ar", tv["palier_ar_x"])):
            zf = zb_at(yh) + e
            A.add(cq.Solid.makeBox(30, 40, zh + 15 - zf, V(xp - 15, yh - 20, zf)), name=f"charniere_palier_{nom}", color=acier)
        A.add(cq.Solid.makeCylinder(8, tv["palier_ar_x"] - tv["palier_av_x"] + 40, V(tv["palier_av_x"] - 20, yh, zh), V(1, 0, 0)), name="charniere_axe", color=acier)
        # mobile : planche de serrage, flasque porte-palier, moteur
        xpl1 = xs_ - mo["recul_arbre"]
        zpl1 = zh - tv["bride_sous_charniere"]
        zsb = zh + tv["arbre_au_dessus"] - mo["arbre_l"]
        zn = zsb - mo["nacelle_d"] / 2
        gris = cq.Color(0.25, 0.25, 0.27)
        parts = {
            "chaise_planche": cq.Solid.makeBox(tv["planche_ep"], 2 * tv["planche_demi_larg"], tv["planche_h"],
                                               V(xpl1 - tv["planche_ep"], -tv["planche_demi_larg"], zpl1 - tv["planche_h"])),
            "chaise_flasque": cq.Solid.makeBox(tv["flasque_ep"], tv["planche_demi_larg"] + e_h + 25, zh + 25 - (zpl1 - tv["planche_h"]),
                                               V(xpl1 - tv["planche_ep"] - tv["flasque_ep"], yh - 25, zpl1 - tv["planche_h"])),
            "chaise_bras": cq.Solid.makeBox(xpl1 - tv["planche_ep"] - tv["flasque_ep"] - tv["palier_av_x"] + 15, 30, 40,
                                            V(tv["palier_av_x"] + 15, yh - 15, zh - 20)),
            "moteur_arbre": cq.Solid.makeCylinder(mo["arbre_d"] / 2, mo["arbre_l"], V(xs_, 0, zsb)),
            "moteur_tete": cq.Solid.makeBox(mo["tete"][0], mo["tete"][1], mo["tete"][2], V(xs_ - mo["tete"][0] / 2, -mo["tete"][1] / 2, zsb + mo["arbre_l"])),
            "moteur_nacelle": cq.Solid.makeCylinder(mo["nacelle_d"] / 2, mo["nacelle_l"], V(xs_ - mo["nacelle_l"] / 2, 0, zn), V(1, 0, 0)),
            "moteur_helice": cq.Solid.makeCylinder(mo["helice_d"] / 2, 25, V(xs_ + mo["nacelle_l"] / 2 + 5, 0, zn), V(1, 0, 0)),
        }
        for nm, sh in parts.items():
            if ang:
                sh = sh.rotate(V(0, yh, zh), V(1, yh, zh), ang)
            col = (cq.Color(0.1, 0.1, 0.1) if nm == "moteur_helice" else gris) if nm.startswith("moteur") else brun
            A.add(sh, name=nm, color=col)
        k["_moteur"] = dict(helice_z=zn, bas_pale=zn - mo["helice_d"] / 2, tete_haut=zsb + mo["arbre_l"] + mo["tete"][2], x_arbre=xs_)
    elif mo and mo.get("mode") == "arriere" and mo["arriere"].get("type_chaise") == "fixe":
        # chaise fixe : planche de serrage suspendue sous le coffre ; le moteur bascule sur l'axe de sa propre bride
        ar = mo["arriere"]
        brun = cq.Color(0.55, 0.36, 0.20)
        xs_, ym = ar["x_arbre"], ar["y"]
        xp_, zp_ = xs_ - ar["bride_axe_devant_arbre"], ar["bride_axe_z"]
        xb1 = xp_ - ar["bride_axe_derriere_planche"]                    # face arrière de la planche
        zc_ = zp_ - ar["bride_axe_sur_planche"]                         # bord haut de la planche
        ang = ar.get("bascule", 0)
        A.add(cq.Solid.makeBox(ar["planche_ep"], 2 * ar["demi_larg"], ar["planche_h"], V(xb1 - ar["planche_ep"], ym - ar["demi_larg"], zc_ - ar["planche_h"])),
              name="chaise_planche", color=brun)
        zbas = zc_ - ar["planche_h"]
        car = ar.get("carter")
        x_av = car["x_av"] if car else xb1 - ar["long_joue"]
        for nom, sg in (("babord", 1), ("tribord", -1)):
            y0c = ym + ar["demi_passage"] if sg > 0 else ym - ar["demi_passage"] - ar["ep_joue"]
            zl_ = lambda x_: min(zfond(x_, y0c), zfond(x_, y0c + ar["ep_joue"]))
            xs_j = [x_av] + ([x0p] if x_av < x0p < xb1 else []) + [xb1]
            pj = [(x_av, zbas), (xb1, zbas)] + [(xx, zl_(xx)) for xx in reversed(xs_j)]
            A.add(cq.Workplane("XZ", origin=(0, y0c + ar["ep_joue"], 0)).polyline(pj).close().extrude(ar["ep_joue"]).val(),
                  name=f"chaise_joue_{nom}", color=brun)
        if car:
            # carter : fond et face avant entre les joues ; la tête relevée y est enfermée
            yl = ar["demi_passage"]
            zloc = min(zfond(x_av + car["ep"], ym - yl), zfond(x_av + car["ep"], ym + yl))   # côté arrière de la face : fond plus bas
            A.add(cq.Solid.makeBox(xb1 - ar["planche_ep"] - x_av, 2 * yl, car["ep"], V(x_av, ym - yl, zbas)), name="carter_fond", color=brun)
            A.add(cq.Solid.makeBox(car["ep"], 2 * yl, zloc - zbas - car["ep"], V(x_av, ym - yl, zbas + car["ep"])), name="carter_face_av", color=brun)
        zsb = zp_ + ar["arbre_au_dessus"] - mo["arbre_l"]
        zn = zsb - mo["nacelle_d"] / 2
        gris = cq.Color(0.25, 0.25, 0.27)
        parts = {
            "moteur_arbre": cq.Solid.makeCylinder(mo["arbre_d"] / 2, mo["arbre_l"], V(xs_, ym, zsb)),
            "moteur_tete": cq.Solid.makeBox(mo["tete"][0], mo["tete"][1], mo["tete"][2], V(xs_ - mo["tete"][0] / 2, ym - mo["tete"][1] / 2, zsb + mo["arbre_l"])),
            "moteur_nacelle": cq.Solid.makeCylinder(mo["nacelle_d"] / 2, mo["nacelle_l"], V(xs_ - mo["nacelle_l"] / 2, ym, zn), V(1, 0, 0)),
            "moteur_helice": cq.Solid.makeCylinder(mo["helice_d"] / 2, 25, V(xs_ + mo["nacelle_l"] / 2 + 5, ym, zn), V(1, 0, 0)),
            "moteur_bride": cq.Solid.makeBox(ar["bride_axe_derriere_planche"] + 30, 80, 90, V(xb1, ym - 40, zc_ - 50)),
        }
        for nm, sh in parts.items():
            if ang and nm != "moteur_bride":
                sh = sh.rotate(V(xs_, ym, 0), V(xs_, ym, 1), ar["rotation_tete_avant_bascule"])   # barre tournée : nacelle en travers
                sh = sh.rotate(V(xp_, ym, zp_), V(xp_, ym + 1, zp_), -ang)                      # bascule sur l'axe de la bride
            A.add(sh, name=nm, color=(cq.Color(0.1, 0.1, 0.1) if nm == "moteur_helice" else gris))
        k["_moteur"] = dict(helice_z=zn, bas_pale=zn - mo["helice_d"] / 2, tete_haut=zsb + mo["arbre_l"] + mo["tete"][2], x_arbre=xs_,
                            planche=(zc_ - ar["planche_h"], zc_))
    elif mo and mo.get("mode") == "arriere":
        ar = mo["arriere"]
        brun = cq.Color(0.55, 0.36, 0.20); acier = cq.Color(0.6, 0.6, 0.62)
        xs_, ym = ar["x_arbre"], ar["y"]
        xh, zh = xs_ + ar["charniere_derriere_arbre"], ar["charniere_z"]
        ang = ar.get("bascule", 0)
        # pièces fixes : deux ferrures de charnière sous le fond du coffre + axe
        for nom, sg in (("babord", 1), ("tribord", -1)):
            y0c = ym + ar["demi_passage"] if sg > 0 else ym - ar["demi_passage"] - ar["ep_ferrure"]
            A.add(cq.Solid.makeBox(ar["long_ferrure"], ar["ep_ferrure"], zb - (zh - 25), V(xh - ar["long_ferrure"] / 2, y0c, zh - 25)),
                  name=f"charniere_ferrure_{nom}", color=acier)
        A.add(cq.Solid.makeCylinder(8, 2 * ar["demi_passage"] + 2 * ar["ep_ferrure"], V(xh, ym - ar["demi_passage"] - ar["ep_ferrure"], zh), V(0, 1, 0)),
              name="charniere_axe", color=acier)
        # pièces mobiles : planche de serrage (bord haut au niveau du fond du coffre) + moteur
        xb1 = xs_ - mo["recul_arbre"]
        zc_ = ar["bride_z"]
        dessus = ar["arbre_au_dessus"] if ang == 0 else ar["arbre_au_dessus_bascule"]
        zsb = zc_ + dessus - mo["arbre_l"]
        zn = zsb - mo["nacelle_d"] / 2
        gris = cq.Color(0.25, 0.25, 0.27)
        parts = {
            "chaise_planche": cq.Solid.makeBox(ar["planche_ep"], 2 * ar["demi_larg"], ar["planche_h"],
                                               V(xb1 - ar["planche_ep"], ym - ar["demi_larg"], zc_ - ar["planche_h"])),
            "chaise_bras_babord": cq.Solid.makeBox(xh - (xb1 - ar["planche_ep"]) + 15, 12, 36, V(xb1 - ar["planche_ep"], ym + ar["demi_larg"] - 12, zh - 18)),
            "chaise_bras_tribord": cq.Solid.makeBox(xh - (xb1 - ar["planche_ep"]) + 15, 12, 36, V(xb1 - ar["planche_ep"], ym - ar["demi_larg"], zh - 18)),
            "moteur_arbre": cq.Solid.makeCylinder(mo["arbre_d"] / 2, mo["arbre_l"], V(xs_, ym, zsb)),
            "moteur_tete": cq.Solid.makeBox(mo["tete"][0], mo["tete"][1], mo["tete"][2], V(xs_ - mo["tete"][0] / 2, ym - mo["tete"][1] / 2, zsb + mo["arbre_l"])),
            "moteur_nacelle": cq.Solid.makeCylinder(mo["nacelle_d"] / 2, mo["nacelle_l"], V(xs_ - mo["nacelle_l"] / 2, ym, zn), V(1, 0, 0)),
            "moteur_helice": cq.Solid.makeCylinder(mo["helice_d"] / 2, 25, V(xs_ + mo["nacelle_l"] / 2 + 5, ym, zn), V(1, 0, 0)),
        }
        for nm, sh in parts.items():
            if ang:
                if nm.startswith("moteur"):
                    sh = sh.rotate(V(xs_, ym, 0), V(xs_, ym, 1), ar["rotation_tete_avant_bascule"])
                sh = sh.rotate(V(xh, ym, zh), V(xh, ym + 1, zh), -ang)
            col = (cq.Color(0.1, 0.1, 0.1) if nm == "moteur_helice" else gris) if nm.startswith("moteur") else brun
            A.add(sh, name=nm, color=col)
        k["_moteur"] = dict(helice_z=zn, bas_pale=zn - mo["helice_d"] / 2, tete_haut=zsb + mo["arbre_l"] + mo["tete"][2], x_arbre=xs_)
    # moteur, mode "avant" : moteur reculé et rehaussé dans une boîte du coffre, bascule vers l'avant par la fente
    elif mo and mo.get("mode") == "vertical2":
        # relevage vertical dans l'axe (JD 29/09 soir) : montage normal (planche devant l'arbre, nez de nacelle devant, hélice derrière,
        # poussée dans l'axe) ; bride fixe, l'arbre y coulisse (vis de serrage de la direction) ; `levee` monte arbre, tête, barre, nacelle, hélice.
        # Cotes relevées sur le schéma du manuel (p. 13), à l'échelle de l'arbre (900 entre tête et nacelle, Ø 30).
        v2 = mo["vertical2"]; tb2 = v2["tableau"]; br2 = v2["bride"]; te2 = v2["tete"]; na2 = v2["nacelle"]; he2 = v2["helice"]
        xs_, ym = v2["x_arbre"], v2["y"]
        lev = v2.get("levee", 0)
        brun = cq.Color(0.55, 0.36, 0.20); gris = cq.Color(0.25, 0.25, 0.27); alu = cq.Color(0.72, 0.74, 0.77)
        zhb = v2["tete_bas"]                                   # bas de la tête en marche (arbre au plus bas)
        zb1 = zhb - br2["dessous_tete"]; zb0 = zb1 - br2["h"]  # bride fixe (fourreau de direction)
        xt1 = xs_ - tb2["devant_arbre"]; xt0 = xt1 - tb2["ep"]
        zt1_ = zb1 - tb2["sous_bride"]                         # haut de la planche
        dyp = v2["puits"]["demi_y"]
        A.add(cq.Solid.makeBox(tb2["ep"], 2 * dyp, tb2["h"], V(xt0, ym - dyp, zt1_ - tb2["h"])), name="moteur_tableau", color=brun)   # collée entre les parois
        A.add(cq.Solid.makeBox(12, 100, tb2["h"] + 10, V(xt1, ym - 50, zt1_ - tb2["h"])), name="moteur_etrier", color=gris)
        A.add(cq.Solid.makeBox(xs_ + br2["derriere"] - (xt1 + 12), 2 * br2["demi_y"], br2["h"], V(xt1 + 12, ym - br2["demi_y"], zb0)), name="moteur_bride", color=gris)
        zsb = zhb - mo["arbre_l"]; zn = zsb - na2["d"] / 2
        ba2 = v2.get("barre"); ai2 = v2.get("aileron")
        parts = {
            "moteur_arbre": cq.Solid.makeCylinder(mo["arbre_d"] / 2, mo["arbre_l"], V(xs_, ym, zsb)),
            "moteur_tete": cq.Solid.makeBox(te2["avant"] + te2["arriere"], 2 * te2["demi_y"], te2["h"], V(xs_ - te2["avant"], ym - te2["demi_y"], zhb)),
            "moteur_nacelle": cq.Solid.makeCylinder(na2["d"] / 2, na2["avant"] + na2["arriere"], V(xs_ - na2["avant"], ym, zn), V(1, 0, 0)),
            "moteur_helice": cq.Solid.makeCylinder(he2["d"] / 2, he2["ep"], V(xs_ + he2["x"], ym, zn), V(1, 0, 0)),
        }
        if ba2:                                                # barre franche repliée vers le haut
            parts["moteur_barre"] = cq.Solid.makeCylinder(ba2["d"] / 2, ba2["l"], V(xs_ + ba2["x"], ym, zhb + te2["h"]))
        if ai2:                                                # aileron sous la nacelle
            parts["moteur_aileron"] = cq.Solid.makeBox(ai2["x1"] - ai2["x0"], ai2["ep"], ai2["h"] + 10, V(xs_ + ai2["x0"], ym - ai2["ep"] / 2, zn - na2["d"] / 2 - ai2["h"]))
        for nm, sh in parts.items():
            A.add(sh.translate(V(0, 0, lev)) if lev else sh, name=nm, color=(cq.Color(0.1, 0.1, 0.1) if nm == "moteur_helice" else gris))
        bt_ = v2.get("bras_tube")
        tc2 = (k.get("haubans") or {}).get("tube_colliers")
        if bt_ and tc2 and lev >= v2["levee_max"] - 0.5:      # position haute : bras rabattu du tube des colliers sur l'arbre
            rt = tc2["diam"] / 2; xtu, ztu = tc2.get("x", xcol), tc2.get("z", zc)
            man = cq.Solid.makeCylinder(rt + bt_["ep"], bt_["larg"] + 10, V(xtu, ym - (bt_["larg"] + 10) / 2, ztu), V(0, 1, 0)).cut(
                cq.Solid.makeCylinder(rt, bt_["larg"] + 10, V(xtu, ym - (bt_["larg"] + 10) / 2, ztu), V(0, 1, 0)))
            pla = cq.Solid.makeBox(xs_ + mo["arbre_d"] / 2 + 20 - xtu - rt, bt_["larg"], bt_["ep"], V(xtu + rt, ym - bt_["larg"] / 2, ztu - bt_["ep"] / 2))
            pla = pla.cut(cq.Solid.makeCylinder(mo["arbre_d"] / 2 + 1, 100, V(xs_, ym, ztu - 50)))
            A.add(man.fuse(pla), name="bras_tube_moteur", color=alu)
        k["_moteur"] = dict(helice_z=zn, bas_pale=zn - he2["d"] / 2, bas_aileron=zn - na2["d"] / 2 - (ai2["h"] if ai2 else 0),
                            tete_haut=zhb + te2["h"], x_arbre=xs_, y=ym, levee=lev, levee_max=v2["levee_max"], bride=(zb0, zb1), tete_bas=zhb,
                            planche=(xt0, xt1))
    elif mo and mo.get("mode") == "avant2":
        # moteur monté à l'envers au milieu (JD 29/09) : planche de serrage derrière l'arbre, nacelle tournée de `rotation`,
        # bascule vers l'avant autour de l'axe de la bride (la partie basse passe devant le coffre, la tête se couche dedans)
        av = mo["avant2"]; ym, xp_, zp_ = av["y"], av["pivot_x"], av["pivot_z"]
        xs_ = xp_ - av["arbre_devant_pivot"]; tb = av["tableau"]
        brun = cq.Color(0.55, 0.36, 0.20); gris = cq.Color(0.25, 0.25, 0.27)
        xt0 = xp_ + tb["derriere_pivot"]; zt1 = zp_ - tb["sous_pivot"]
        A.add(cq.Solid.makeBox(tb["ep"], 2 * tb["demi_larg"], tb["h"], V(xt0, ym - tb["demi_larg"], zt1 - tb["h"])), name="moteur_tableau", color=brun)
        A.add(cq.Solid.makeBox(12, 100, 90, V(xt0 - 12, ym - 50, zt1 - 80)), name="moteur_etrier", color=gris)          # étrier fixe, serré sur la planche
        dessus = av["arbre_au_dessus"]; zsb = zp_ + dessus - mo["arbre_l"]; zn = zsb - mo["nacelle_d"] / 2
        axe_arbre = (V(xs_, ym, 0), V(xs_, ym, 1))
        parts = {
            "moteur_arbre": cq.Solid.makeCylinder(mo["arbre_d"] / 2, mo["arbre_l"], V(xs_, ym, zsb)),
            "moteur_tete": cq.Solid.makeBox(mo["tete"][0], mo["tete"][1], mo["tete"][2], V(xs_ - mo["tete"][0] / 2, ym - mo["tete"][1] / 2, zsb + mo["arbre_l"])),
            "moteur_nacelle": cq.Solid.makeCylinder(mo["nacelle_d"] / 2, mo["nacelle_l"], V(xs_ - mo["nacelle_l"] / 2, ym, zn), V(1, 0, 0)),
            # monté à l'envers, direction au neutre : hélice côté avant ; la rotation de `rotation` la ramène derrière (poussée vers l'avant)
            "moteur_helice": cq.Solid.makeCylinder(mo["helice_d"] / 2, 25, V(xs_ - mo["nacelle_l"] / 2 - 30, ym, zn), V(1, 0, 0)),
            "moteur_bride": cq.Solid.makeBox(xt0 - 12 - (xs_ - 40), 80, 95, V(xs_ - 40, ym - 40, zp_ - 60)),         # support pivotant (suit la bascule)
        }
        ang = av.get("bascule", 0)
        for nm, sh in parts.items():
            if nm in ("moteur_nacelle", "moteur_helice", "moteur_tete"):
                sh = sh.rotate(axe_arbre[0], axe_arbre[1], av["rotation"])            # direction tournée : poussée vers l'avant
            if ang:
                sh = sh.rotate(V(xp_, ym, zp_), V(xp_, ym + 1, zp_), ang)             # bascule vers l'avant sur l'axe de la bride
            A.add(sh, name=nm, color=(cq.Color(0.1, 0.1, 0.1) if nm == "moteur_helice" else gris))
        k["_moteur"] = dict(helice_z=zn, bas_pale=zn - mo["helice_d"] / 2, tete_haut=zsb + mo["arbre_l"] + mo["tete"][2], x_arbre=xs_, pivot=(xp_, ym, zp_))
    elif mo and mo.get("mode") == "avant":
        av = mo["avant"]
        brun = cq.Color(0.55, 0.36, 0.20)
        xs_ = av["x_arbre"]
        zpv = av["pivot_z"]
        xb0 = xs_ + mo["recul_arbre"]
        A.add(cq.Solid.makeBox(av["tableau_ep"], 2 * av["demi_larg"], av["tableau_haut"] - av["tableau_bas"],
                               V(xb0, -av["demi_larg"], av["tableau_bas"])), name="chaise_tableau", color=brun)
        for nom, sg in (("babord", 1), ("tribord", -1)):
            y0c = av["demi_larg"] if sg > 0 else -av["demi_larg"] - av["ep_joue"]
            A.add(cq.Solid.makeBox(av["tableau_ep"] + av["long_joue"], av["ep_joue"], zb - av["tableau_bas"],
                                   V(xb0, y0c, av["tableau_bas"])), name=f"chaise_joue_{nom}", color=brun)
        zn = zpv - mo["bride_nacelle_max"]
        zsb = zn + mo["nacelle_d"] / 2
        gris = cq.Color(0.25, 0.25, 0.27)
        nac = cq.Solid.makeCylinder(mo["nacelle_d"] / 2, mo["nacelle_l"], V(xs_ - mo["nacelle_l"] / 2, 0, zn), V(1, 0, 0))
        hel = cq.Solid.makeCylinder(mo["helice_d"] / 2, 25, V(xs_ + mo["nacelle_l"] / 2 + 5, 0, zn), V(1, 0, 0))
        rot = av.get("rotation_tete", 180)
        nac = nac.rotate(V(xs_, 0, 0), V(xs_, 0, 1), rot); hel = hel.rotate(V(xs_, 0, 0), V(xs_, 0, 1), rot)
        dessus = av.get("arbre_au_dessus", 50)
        parts = {
            "moteur_arbre": cq.Solid.makeCylinder(mo["arbre_d"] / 2, mo["arbre_l"], V(xs_, 0, zsb)),
            "moteur_tete": cq.Solid.makeBox(mo["tete"][0], mo["tete"][1], mo["tete"][2], V(xs_ - mo["tete"][0] / 2, -mo["tete"][1] / 2, zsb + mo["arbre_l"])),
            "moteur_nacelle": nac, "moteur_helice": hel,
        }
        ang = av.get("bascule", 0)
        for nm, sh in parts.items():
            if ang:
                sh = sh.rotate(V(xs_, 0, zpv), V(xs_, 1, zpv), ang)
            A.add(sh, name=nm, color=(cq.Color(0.1, 0.1, 0.1) if nm == "moteur_helice" else gris))
        k["_moteur"] = dict(helice_z=zn, bas_pale=zn - mo["helice_d"] / 2, tete_haut=zsb + mo["arbre_l"] + mo["tete"][2], x_arbre=xs_)
    # moteur : chaise centrée fixe (tableau sous le fond du coffre), relevage vertical par coulissement de l'arbre
    elif mo:
        ch = mo["chaise"]
        brun = cq.Color(0.55, 0.36, 0.20)
        xs_ = ch["x_face_ar"] + mo["recul_arbre"]
        A.add(cq.Solid.makeBox(ch["ep"], 2 * ch["demi_larg"], ch["z_bride"] - ch["z_bas"],
                               V(ch["x_face_ar"] - ch["ep"], -ch["demi_larg"], ch["z_bas"])), name="chaise_moteur", color=brun)
        z_nac = ch["z_bride"] - mo["bride_nacelle_max"] + mo.get("levee", 0)       # axe de la nacelle
        zsb = z_nac + mo["nacelle_d"] / 2
        gris = cq.Color(0.25, 0.25, 0.27)
        A.add(cq.Solid.makeCylinder(mo["arbre_d"] / 2, mo["arbre_l"], V(xs_, 0, zsb)), name="moteur_arbre", color=gris)
        A.add(cq.Solid.makeBox(mo["tete"][0], mo["tete"][1], mo["tete"][2], V(xs_ - mo["tete"][0] / 2, -mo["tete"][1] / 2, zsb + mo["arbre_l"])),
              name="moteur_tete", color=gris)
        A.add(cq.Solid.makeCylinder(mo["nacelle_d"] / 2, mo["nacelle_l"], V(xs_ - mo["nacelle_l"] / 2, 0, z_nac), V(1, 0, 0)),
              name="moteur_nacelle", color=gris)
        A.add(cq.Solid.makeCylinder(mo["helice_d"] / 2, 25, V(xs_ + mo["nacelle_l"] / 2 + 5, 0, z_nac), V(1, 0, 0)),
              name="moteur_helice", color=cq.Color(0.1, 0.1, 0.1))
        A.add(cq.Solid.makeBox(60, 70, 60, V(xs_ - 30 - mo["recul_arbre"] + 10, -35, ch["z_bride"] - 20)), name="moteur_bride", color=gris)
        k["_moteur"] = dict(helice_z=z_nac, bas_pale=z_nac - mo["helice_d"] / 2,
                            tete_haut=zsb + mo["arbre_l"] + mo["tete"][2], x_arbre=xs_)
    # pylônes au bout du coffre, sous chaque joue, au droit du mât
    py = k["pylones"]
    if py.get("type") == "tube":                         # tubes carbone posés sur les semelles, seuls appuis sur le pont
        for nom, sg in (("babord", 1), ("tribord", -1)):
            yp = sg * (wi - py["y_int"])
            for j, dxp in enumerate(py["dx"]):
                xp = m["x_pied"] + dxp
                z0 = m["z_pied"] - math.tan(qa) * dxp if m.get("semelle") else interp_pont(xp, yp) + 1
                z1 = zfond(xp, abs(yp)) + e + 40
                tb = cq.Solid.makeCylinder(py["diam"] / 2, z1 - z0, V(xp, yp, z0)).cut(cq.Solid.makeCylinder(py["diam"] / 2 - py["ep"], z1 - z0, V(xp, yp, z0)))
                tb = tb.intersect(sous_fond())                   # haut coupé à la pente du fond (face intérieure), pente et V compris
                A.add(tb, name=f"pylone_coffre_{nom}_{j}", color=cq.Color(0.16, 0.16, 0.17))
            rf = py.get("renfort")
            if rf:                                               # semelle CP collée sur le fond contre la joue, sur les deux tubes : ils portent dessous (JD 30/09 : pas de couple en travers)
                ya_r, yb_r = sorted((sg * wi, sg * (wi - rf["dy"])))
                xr0, xr1 = m["x_pied"] + min(py["dx"]) - rf["dx"] / 2, m["x_pied"] + max(py["dx"]) + rf["dx"] / 2
                pad = sous_fond().translate(V(0, 0, rf["ep"])).cut(sous_fond()).intersect(
                    cq.Solid.makeBox(xr1 - xr0, yb_r - ya_r, 2000, V(xr0, ya_r, zb - 500)))
                A.add(pad, name=f"pylone_renfort_{nom}", color=cq.Color(0.13, 0.13, 0.14))
    for nom, sg in (("babord", 1), ("tribord", -1)) if py.get("type") != "tube" else ():
        z0 = m["z_pied"] if m.get("semelle") else interp_pont(m["x_pied"], sg * PONT_CFG["entraxe"] / 2) + 1   # sur la semelle
        x0, y0 = m["x_pied"] - py["dx"] / 2, (sg * (wi - py["dy"] / 2)) - py["dy"] / 2
        ztp = zb_at(abs(y0) if sg > 0 else abs(y0 + py["dy"])) 
        blk = cq.Solid.makeBox(py["dx"], py["dy"], ztp - z0, V(x0, y0, z0))
        t = py["ep"]
        blk = blk.cut(cq.Solid.makeBox(py["dx"] - 2 * t, py["dy"] - 2 * t, ztp - z0, V(x0 + t, y0 + t, z0)))
        A.add(blk, name=f"pylone_coffre_{nom}", color=bois)
    # accroches du coffre sur la poutre AV : demi-profil DWG + jeu, ouvertes vers le bas (posées par-dessus, tenues par les haubans)
    from shapely.geometry import Polygon as SPoly, box as sbox
    from shapely.ops import unary_union as sunion
    def demi_profil(nom, jeu):
        pb = SPoly(PROFILS[nom]).buffer(jeu, join_style=1)
        u0, _, u1, _ = pb.bounds
        return sunion([pb, sbox(u0, -400, u1, 0)])
    def machoire_uv(nom, jeu, mj):
        """Mâchoire (u, v) : du bord extérieur jusque sous le centre du nez (u = 0), lèvre d'épaisseur mj["levre"]
        sous le profil ; le quart inférieur intérieur (u > 0, v < 0) reste ouvert pour le trampoline."""
        pb = SPoly(PROFILS[nom]).buffer(jeu, join_style=1)
        r_ = -min(u for u, v in PROFILS[nom]) + jeu
        jm_ = sbox(mj["u_ext"], -(r_ + mj["levre"]), mj.get("u_fin", 0.0), mj["v_haut"]).difference(pb)
        if jm_.geom_type != "Polygon":
            jm_ = max(jm_.geoms, key=lambda g_: g_.area)
        return list(jm_.exterior.coords)[:-1]
    ac = k.get("accroches_poutre")
    if ac and POUTRE_AV:
        from shapely import affinity as _af
        pv = POUTRE_AV; ko_uv = demi_profil('poutre', ac["jeu"]); vmax = max(v for u, v in PROFILS['poutre'])
        pose_ = ac.get("pose"); integ_ = ac.get("integre")
        P0_ = SPoly(PROFILS['poutre']).buffer(ac["jeu"], join_style=1)
        def couloir(zc0):
            """Place balayée par la poutre (profil + jeu), vue de l'accroche, pendant la pose : descente verticale puis, si `pose`,
            fin en diagonale arrière-bas (angle, course) ; repère x, z. Sans `pose` : tout le dessous du profil (ouvert vers le bas)."""
            P_ = _af.translate(P0_, pv["x"], zc0)
            if not pose_:
                return sunion([P_, sbox(P_.bounds[0], zc0 - 1000, P_.bounds[2], zc0)])
            a_ = math.radians(pose_["angle"]); S_ = pose_["course"]
            P1_ = _af.translate(P_, S_ * math.cos(a_), -S_ * math.sin(a_))
            return sunion([P_, P1_]).convex_hull.union(sunion([P1_, _af.translate(P1_, 0, -1000)]).convex_hull)
        def cadre(yh_):
            """Couple du coffre (ou paroi du puits) dans le plan de l'accroche : (enfant, y0, y1) de sa face contre C4, sinon None."""
            slab_ = cq.Solid.makeBox(4, 60, 3000, V(xa - e - 5, yh_ - 30, -500))
            for ch_ in A.children:
                if ch_.obj is not None and ch_.name.startswith(("couple_coffre_", "moteur_puits")):
                    so_ = ch_.obj.val() if isinstance(ch_.obj, cq.Workplane) else ch_.obj
                    it_ = so_.intersect(slab_)
                    if it_.Volume() > 1:
                        bb_ = it_.BoundingBox()
                        return ch_, bb_.ymin, bb_.ymax
            return None
        k["_accroches"] = []
        for i, yh in enumerate(ac["y"]):
            zc_ = z_cambre(yh, pv["z_ext"], pv["fleche"], pv.get("y_libre", pv["y_ext"]))
            haut_ = zc_ + vmax + ac["au_dessus"]
            if yh in (ac.get("sous_assise") or []):      # sous les bancs : l'accroche monte jusqu'à l'assise (couple avant du banc)
                haut_ = b["plan_z"] + b["hauteur"] - b["ep_assise"]
            fr_ = cadre(yh) if integ_ else None
            y0f, y1f = (fr_[1], fr_[2]) if fr_ else (yh - ac["ep"] / 2, yh + ac["ep"] / 2)
            x0f = xa - e if fr_ else xa                      # intégrée : le couple traverse C4 (fente) et devient l'accroche
            cor_ = sunion([couloir(z_cambre(yy_, pv["z_ext"], pv["fleche"], pv.get("y_libre", pv["y_ext"]))) for yy_ in (y0f, y1f)])
            cor_ = cor_.intersection(sbox(xa, -1e4, 1e5, 1e4))     # ne mord pas dans C4, contre le nez
            pl = sbox(x0f, zc_ - ac["sous_axe"], ac["fin_x"], haut_).difference(cor_)
            if pl.geom_type != "Polygon":
                pl = max(pl.geoms, key=lambda g_: g_.area)
            sol = cq.Workplane("XZ", origin=(0, y1f, 0)).polyline(list(pl.exterior.coords)[:-1]).close().extrude(y1f - y0f).val()
            br_ = ac.get("brelage"); mg_ = PLAT.get("mg"); tb_ = (br_ or {}).get("trou")
            if tb_:                                          # trou du brêlage dans la lèvre, sous le nez
                sol = sol.cut(cq.Solid.makeCylinder(tb_["diam"] / 2, y1f - y0f + 20, V(pv["x"] + tb_["u"], y0f - 10, zc_ + tb_["v"]), V(0, 1, 0)))
            if fr_:
                so_ = fr_[0].obj.val() if isinstance(fr_[0].obj, cq.Workplane) else fr_[0].obj
                fr_[0].obj = so_.fuse(sol).clean()
                for ch_ in A.children:                       # fente dans C4
                    if ch_.name == "coffre_coque":
                        co_ = ch_.obj.val() if isinstance(ch_.obj, cq.Workplane) else ch_.obj
                        ch_.obj = co_.cut(sol)
            else:
                A.add(sol, name=f"accroche_poutre_{i}", color=cq.Color(0.66, 0.42, 0.22))
            k["_accroches"].append(dict(y=yh, y0=round(y0f, 1), y1=round(y1f, 1), cadre=fr_[0].name if fr_ else None, zc=round(zc_, 1)))
            if br_:                                          # brêlage en diagonale (JD 30/09) : du trou de la lèvre (ou d'un œil dans C4) au pied du pilier de martingale
                r_n = -u_min('poutre') + ac["jeu"]
                if tb_:
                    y_q0 = (y0f - br_["diam"] / 2 - 0.5) if yh > 0 else (y1f + br_["diam"] / 2 + 0.5)    # sort du trou côté axe
                    q0 = V(pv["x"] + tb_["u"], y_q0, zc_ + tb_["v"])
                else:
                    q0 = V(xa + br_["diam"] / 2 + 1, yh, zc_ - r_n - br_.get("sous_nez", 12))
                # passe sous le bord avant du pied (le brêlage tire vers le haut : il ne peut pas remonter le long du pilier), hors du plan des tiges
                q1 = V(PLAT["fb"] - 12 - br_["diam"] / 2 - 1, 0, PLAT["zav"] - (mg_ or {}).get("pied_sous_axe_extremites", 170) - br_["diam"] / 2 - 1)
                A.add(cq.Solid.makeCylinder(br_["diam"] / 2, (q1 - q0).Length, q0, (q1 - q0).normalized()), name=f"brelage_poutre_{i}", color=cq.Color(0.20, 0.36, 0.55))
            mj = ac.get("machoire")
            if mj and mj.get("type") == "corniere":      # C4 contre la poutre : cornière alu boulonnée sur C4, aile sous le nez
                r_n = -u_min('poutre'); yl_ = (yh - mj["larg"] / 2, yh + mj["larg"] / 2)
                zm_ = min(z_cambre(yy, pv["z_ext"], pv["fleche"], pv.get("y_libre", pv["y_ext"])) for yy in yl_)
                za_ = zm_ - r_n - mj["jeu"]; t_ = mj["ep"]
                lp = [(xa, za_), (xa + mj["aile_h"], za_), (xa + mj["aile_h"], za_ - t_), (xa + t_, za_ - t_), (xa + t_, za_ - mj["aile_v"]), (xa, za_ - mj["aile_v"])]
                solm = cq.Workplane("XZ", origin=(0, yl_[1], 0)).polyline(lp).close().extrude(mj["larg"]).val()
                A.add(solm, name=f"machoire_poutre_{i}", color=cq.Color(0.72, 0.74, 0.77))
            elif mj:                                     # mâchoire boulonnée contre l'accroche : ferme le quart inférieur extérieur (sous le nez)
                jm = machoire_uv('poutre', ac["jeu"], mj)
                sg_ = 1 if yh >= 0 else -1                # côté extérieur de l'accroche
                y0m = yh + sg_ * ac["ep"] / 2 + (mj["ep"] if sg_ > 0 else 0)
                zm_ = z_cambre(yh + sg_ * (ac["ep"] / 2 + mj["ep"]), pv["z_ext"], pv["fleche"], pv.get("y_libre", pv["y_ext"]))   # poutre cintrée : lèvre calée sur la face la plus basse
                solm = cq.Workplane("XZ", origin=(0, y0m, 0)).polyline([(pv["x"] + u, zm_ + v) for u, v in jm]).close().extrude(mj["ep"]).val()
                A.add(solm, name=f"machoire_poutre_{i}", color=cq.Color(0.42, 0.26, 0.13))
    # bancs latéraux sur les longerons, entre le trampoline et la joue
    es, eb, el, r = b["ep_assise"], b["ep_fond"], b["ep_cotes"], b["rayon_aretes"]
    xb0 = b.get("x_debut", xa)
    L = xa + b["longueur"] - xb0
    for nom, sg in (("babord", 1), ("tribord", -1)):
        yi, yo = sg * b["y_int"], sg * wi
        y0, larg = min(yi, yo), abs(yo - yi)
        outer = (cq.Workplane("XY").box(L, larg, hb, centered=False).translate((xb0, y0, zt0))
                 .edges("|X and >Z").fillet(r))
        inner = cq.Workplane("XY").box(L - 2 * el, larg - 2 * el, hb - es - eb, centered=False).translate(
            (xb0 + el, y0 + el, zt0 + eb))
        cas = outer.cut(inner).val()
        if POUTRE_AV.get("degagement") is not None:
            cas = cas.cut(POUTRE_AV["degagement"])
        else:
            cas = cas.cut(cq.Solid.makeCylinder(b["encoche_poutre_r"], larg + 20, V(b["poutre_x"], y0 + larg + 10, b["poutre_z"]), V(0, -1, 0)))
        Ul = V(0, -sg, 0)
        if PLAT:                                            # longeron en pente, de l'axe de la poutre AV à celui de la poutre AR
            zl = lambda x_: PLAT["zav"] + (PLAT["zar"] - PLAT["zav"]) * (x_ - PLAT["fb"]) / (PLAT["rb"] - PLAT["fb"])
            ly_, x0l = PLAT["ly"], xb0 - 10
            lg = cq.Solid.extrudeLinear(fil_section(profil_uv('longeron', 4), V(x0l, sg * ly_, zl(x0l)), Ul), [], V(L + 20, 0, zl(x0l + L + 20) - zl(x0l)))
            zlo = min(zl(x0l), zl(x0l + L + 20))
        else:
            ly_, zlo = b["longeron_y"], b["poutre_z"]
            lg = profil_droit('longeron', V(xb0 - 10, sg * ly_, zlo), V(1, 0, 0), L + 20, Ul, marge=4)
        cas = cas.cut(lg)                                   # encoche du longeron (profil en goutte), ouverte vers le bas
        yl0, yl1 = sorted((sg * (ly_ - u_max('longeron') - 4), sg * (ly_ - u_min('longeron') + 4)))
        if zlo - zt0 + 10 > 1:                               # caisson plus bas que le longeron (anciens bancs)
            cas = cas.cut(cq.Solid.makeBox(L + 20, yl1 - yl0, zlo - zt0 + 10, V(xb0 - 10, yl0, zt0 - 10)))
        cut = cq.Solid.makeBox(L + 10, larg + 10, es + 50, V(xb0 - 5, y0 - 5, zs - es))
        if b.get("caisson", True):
            A.add(cas.cut(cut), name=f"banc_{nom}_caisson", color=bois)
            A.add(cas.intersect(cut), name=f"banc_{nom}_assise", color=cq.Color(0.72, 0.50, 0.32))
        else:                                               # banc ouvert dessous (JD 29/09) : assise seule sur les couples
            ass = cq.Workplane("XY").box(L, larg, es, centered=False).translate((xb0, y0, zs - es)).edges("|X and >Z").fillet(b.get("rayon_assise", 4)).val()
            A.add(ass, name=f"banc_{nom}_assise", color=cq.Color(0.72, 0.50, 0.32))
        if PLAT and b.get("couples_x"):                     # couples transversaux accrochés au longeron (demi-profil DWG + jeu)
            ko_uv = demi_profil('longeron', 2)
            zl = lambda x_: PLAT["zav"] + (PLAT["zar"] - PLAT["zav"]) * (x_ - PLAT["fb"]) / (PLAT["rb"] - PLAT["fb"])
            ly_ = PLAT["ly"]; cep = b["couple_ep"]
            for j, xc_ in enumerate(b["couples_x"]):
                za_ = zl(xc_)
                ko = SPoly([(sg * (ly_ - u), za_ + v) for u, v in ko_uv.exterior.coords])
                yA, yB = sorted((sg * b["y_int"], sg * wi)); yC, yD = sorted((sg * (ly_ - u_max("longeron") - 2), sg * b["couple_ext"]))
                fr = sunion([sbox(yA, zt0, yB, zs - es), sbox(yC, za_ - b["couple_sous_axe"], yD, zt0 + b.get("couple_ext_haut", 0))]).difference(ko)   # joue du couple plus haute : cou plus large
                fr = fr.buffer(-0.2, join_style=2).buffer(0.2, join_style=2)   # retire la lame d'épaisseur nulle laissée au bord intérieur, sous la queue du longeron
                ev = b.get("evidement")
                if ev:                                   # couple évidé en dessous (JD 29/09) : les cases sous l'assise communiquent
                    y_i, y_o = sg * (b["y_int"] - 20), sg * (ly_ - u_max("longeron") - 2 - ev["marge"])
                    o_ = sbox(min(y_i, y_o), zt0 - 20, max(y_i, y_o), zs - es - ev["ame"]).buffer(-ev["rayon"], join_style=1).buffer(ev["rayon"], join_style=1)
                    fr = fr.difference(o_)
                if fr.geom_type != "Polygon":
                    fr = max(fr.geoms, key=lambda g_: g_.area)
                sol = cq.Workplane("YZ", origin=(xc_ - cep / 2, 0, 0)).polyline(list(fr.exterior.coords)[:-1]).close().extrude(cep).val()
                if b.get("joue_jusqu_au_longeron") and nom in JOUES:
                    if b.get("entaille_dans_joue"):          # (JD 30/09) la joue est entaillée par le bas, le couple reste entier
                        jo_ = JOUES[nom].cut(sol); JOUES[nom] = jo_
                        for ch_ in A.children:
                            if ch_.name == f"joue_{nom}":
                                ch_.obj = jo_
                    else:
                        sol = sol.cut(JOUES[nom])            # entaille du couple : la joue passe au travers (assemblage à mi-bois, collé)
                A.add(sol, name=f"banc_{nom}_couple_{j}", color=cq.Color(0.66, 0.42, 0.22))
                mj = b.get("machoire")
                if mj:                                   # mâchoire boulonnée contre la face arrière du couple, sous le nez du longeron
                    jm = machoire_uv('longeron', 2, mj)
                    solm = cq.Workplane("YZ", origin=(xc_ + cep / 2, 0, 0)).polyline([(sg * (ly_ - u), za_ + v) for u, v in jm]).close().extrude(mj["ep"]).val()
                    A.add(solm, name=f"banc_{nom}_machoire_{j}", color=cq.Color(0.42, 0.26, 0.13))
    lc = b.get("lacage")
    if PLAT and lc and b.get("couples_x"):                  # laçage d'un longeron à l'autre, sous la toile (JD 29/09) : ne traverse jamais le trampoline
        zl = lambda x_: PLAT["zav"] + (PLAT["zar"] - PLAT["zav"]) * (x_ - PLAT["fb"]) / (PLAT["rb"] - PLAT["fb"])
        ly_, rc = PLAT["ly"], lc["diam"] / 2; R_ = -u_min("longeron") + rc + 1   # rayon du nez + corde
        corde = cq.Color(0.20, 0.36, 0.55)
        for j, xc_ in enumerate(b["couples_x"]):
            if xc_ not in lc["x"]:
                continue
            xl_ = xc_ - b["couple_ep"] / 2 - rc - 1 if b.get("machoire") else xc_     # devant le couple : la mâchoire est derrière
            za_ = zl(xl_); ye = b["couple_ext"] + rc + 0.5
            if lc.get("droit"):                          # (JD 30/09) descend le long de la joue du couple, passe sous son bas et file tout droit sous la toile
                demi = [V(xl_, ye, za_ + lc["haut"]), V(xl_, ye, za_ - b["couple_sous_axe"] - rc - 1)]
            elif b.get("machoire"):                      # descend le long de la joue du couple, passe sous le nez puis file sous la toile
                demi = [V(xl_, ye, za_ + lc["haut"]), V(xl_, ye, za_ - R_), V(xl_, ly_, za_ - R_)]
            else:
                demi = [V(xl_, ye, za_ + lc["haut"]), V(xl_, ye, za_ - b["couple_sous_axe"] - rc - 1)]
                demi += [V(xl_, ly_ + R_ * math.cos(math.radians(t_)), za_ - R_ * math.sin(math.radians(t_))) for t_ in (30, 55, 75, 90)]
            pts = demi + [V(q.x, -q.y, q.z) for q in reversed(demi)]
            segs = [cq.Solid.makeCylinder(rc, (q1 - q0).Length, q0, (q1 - q0).normalized()) for q0, q1 in zip(pts, pts[1:])]
            segs += [cq.Solid.makeSphere(rc, q) for q in pts[1:-1]]
            A.add(cq.Compound.makeCompound(segs), name=f"lacage_banc_{j}", color=corde)

CFG_MAT = {}
PLAT = {}               # plateforme vue par le coffre (poutres, longerons, pièces d'angle)
COFFRE_CACHE = {}       # solides extérieur / intérieur du dernier coffre construit (développés du plan de découpe)
def degagement_joue(sg, y0, ef, x_fin, z_bas_banc=None, jeu_longeron=None, pose=None):
    """Volume à retirer d'une joue posée sur le longeron : nez de la pièce d'angle AV (ouvert vers le bas) puis
    longeron jusqu'au bout du banc (dessus du longeron + 4), en suivant sa pente. jeu_longeron : la joue descend
    jusqu'au dessus local du longeron sous son épaisseur (+ jeu) au lieu du dessus du profil + 4."""
    pa, fb, zav, zar, rb = PLAT["pa"], PLAT["fb"], PLAT["zav"], PLAT["zar"], PLAT["rb"]
    ya, yb = sorted((y0 - 10, y0 + ef + 10))
    xa_, xb_ = fb - pa["nez_x"] - 4, fb - pa["nez_x_fin"] + 4
    nez = cq.Solid.makeBox(xb_ - xa_, yb - ya, zav + pa["nez_demi_h"] + 4 + 200, V(xa_, ya, -200))
    if pose:                                              # fin de pose en diagonale arrière-bas : la pièce d'angle, vue de la joue, vient d'en arrière-bas
        a_ = math.radians(pose["angle"]); S_ = pose["course"] + 3
        dx_, dz_ = S_ * math.cos(a_), S_ * math.sin(a_); z1n = zav + pa["nez_demi_h"] + 4
        hexa = [(xa_, z1n), (xb_, z1n), (xb_ + dx_, z1n - dz_), (xb_ + dx_, -200 - dz_), (xa_ + dx_, -200 - dz_), (xa_, -200)]
        nez = cq.Workplane("XZ", origin=(0, yb, 0)).polyline(hexa).close().extrude(yb - ya).val()
    pente = (zar - zav) / (rb - fb); v_top = max(v for u, v in PROFILS['longeron']) + 4
    if jeu_longeron is not None:                          # dessus du longeron sous la joue seulement (côté nez)
        from shapely.geometry import Polygon as SP_, box as sb_
        ly_ = PLAT["ly"]; ja, jb_ = (y0 - ef, y0) if y0 > 0 else (-y0, -y0 + ef)      # |y| occupés par la joue
        ua, ub = sorted((ly_ - ja, ly_ - jb_))
        loc = SP_(PROFILS['longeron']).intersection(sb_(ua - jeu_longeron, -100, ub + jeu_longeron, 100))
        v_top = (loc.bounds[3] if not loc.is_empty else -100) + jeu_longeron
    zl = lambda x_: zav + pente * (x_ - fb)
    x0 = xb_ - 10
    sec = cq.Wire.makePolygon([V(x0, ya, -200), V(x0, yb, -200), V(x0, yb, zl(x0) + v_top), V(x0, ya, zl(x0) + v_top)], close=True)
    lon = cq.Solid.extrudeLinear(sec, [], V(x_fin - x0, 0, pente * (x_fin - x0)))
    ko = nez.fuse(lon)
    if z_bas_banc is not None:                            # le long du banc, la joue s'arrête au fond du banc : les couples passent dessous
        ko = ko.fuse(cq.Solid.makeBox(x_fin - x0, yb - ya, z_bas_banc + 200, V(x0, ya, -200)))
    return ko
HREF = 500.0            # hauteur de référence du paramétrage à pente égale des profils du coffre
CFG_COFFRE_Y = {}
POUTRE_AV = {}

def poutre_cintree(x, z_ext, fleche, y_ext, r, n=24, y_lim=None):
    """Tube cintré (flèche parabolique vers le haut au milieu), axe à z_ext en y=±y_ext ; tracé de -y_lim à +y_lim."""
    yl = y_lim or y_ext
    pts = [V(x, y, z_ext + fleche * (1 - (y / y_ext) ** 2)) for y in [-yl + 2 * yl * i / n for i in range(n + 1)]]
    e = cq.Edge.makeSpline(pts)
    path = cq.Wire.assembleEdges([e])
    prof = cq.Wire.makeCircle(r, pts[0], e.tangentAt(0))
    return cq.Solid.sweep(prof, [], path, True, False)
# profils extrudés des poutres et longerons (relevés sur les DWG « pince » : u vers le trampoline, v vers le haut)
PROFILS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profils_hc16.json')))
def profil_uv(nom, marge=0.0):
    pts = PROFILS[nom]
    if marge:
        from shapely.geometry import Polygon
        pts = list(Polygon(pts).buffer(marge, join_style=2).simplify(0.2).exterior.coords)[:-1]
    return pts
def fil_section(pts, O, U, W=V(0, 0, 1)):
    return cq.Wire.makePolygon([O + U * u + W * v for u, v in pts], close=True)
def profil_droit(nom, O, axe, L, U, marge=0.0):
    """Profilé droit : section (u, v) posée en O, u selon U (vers le trampoline), extrudé de L selon axe."""
    return cq.Solid.extrudeLinear(fil_section(profil_uv(nom, marge), O, U), [], axe * L)
def z_cambre(y, z_ext, fleche, y_libre):
    """Axe de la poutre AV : parabole entre les pièces d'angle (z_ext en y = ±y_libre, +fleche au milieu),
    horizontale dans les pièces d'angle (hauteur relative poutre / longeron non relevée : V9)."""
    a = abs(y)
    if a <= y_libre:
        return z_ext + fleche * (1 - (a / y_libre) ** 2)
    return z_ext
def profil_cintre(nom, x, z_ext, fleche, y_ext, U, marge=0.0, y_lim=None, n=32, y_libre=None, y_de=None):
    """Poutre cintrée : sections empilées le long de y (de -y_lim à +y_lim, ou de y_de[0] à y_de[1])."""
    yl = y_lim or y_ext; yf = y_libre or y_ext; pts = profil_uv(nom, marge)
    y0, y1 = y_de if y_de else (-yl, yl)
    ys = sorted({y0 + (y1 - y0) * i / n for i in range(n + 1)} | {yy for yy in (-yf, yf) if y0 < yy < y1})
    fils = [fil_section(pts, V(x, y, z_cambre(y, z_ext, fleche, yf)), U, V(0, 0, 1)) for y in ys]
    return cq.Solid.makeLoft(fils, True)
def u_max(nom): return max(u for u, v in PROFILS[nom])
def u_min(nom): return min(u for u, v in PROFILS[nom])

PONT_CFG = {}
def interp_pont(x, y):
    """Dessus du pont (bombé) à (x, y), d'après les tables de coque."""
    c = PONT_CFG
    yc = c["entraxe"] / 2 * (1 if y > 0 else -1)
    b = interp(c["demi_largeur"], x); d = interp(c["pont"], x)
    t = min(1.0, abs(y - yc) / b)
    return d - c["bouge_pont"] + c["bouge_pont"] * math.sqrt(max(0.0, 1 - t * t))

def z_tige_martingale(mg, z_ext, r_nez, y):
    """Hauteur de l'axe d'une tige de martingale à la distance y de l'axe du bateau."""
    z_bas = z_ext - mg["pied_sous_axe_extremites"]
    if "jour_sous_poutre" in mg:                  # jour relevé entre le dessous de la poutre et la tige, au ras de la pièce d'angle
        yj = mg["y_jour"]; zj = z_ext - r_nez - mg["jour_sous_poutre"] - mg.get("tige_diam", 6) / 2
    else:
        yj = mg["y_cable"]; zj = z_ext - mg["cable_sous_axe_extremites"]
    return z_bas + (zj - z_bas) * abs(y) / yj

def martingale(A, mg, fb, z_ext, fleche, r_nez):
    """Martingale : pilier sous le milieu de la poutre AV + deux tiges inox rigides vers les attaches (y = ±y_cable)."""
    gm = cq.Color(0.55, 0.55, 0.58)
    z_haut = z_ext + fleche - r_nez
    z_bas = z_ext - mg["pied_sous_axe_extremites"]
    mg["_z_bas"] = z_bas
    top = V(fb, 0, z_haut); bas = V(fb, 0, z_bas)
    A.add(cq.Solid.makeCylinder(12, (top - bas).Length, bas, (top - bas).normalized()), name="martingale_pilier", color=gm)
    for nom, sg in (("babord", 1), ("tribord", -1)):
        ext_ = V(fb, sg * mg["y_cable"], z_tige_martingale(mg, z_ext, r_nez, mg["y_cable"]))
        A.add(cq.Solid.makeCylinder(mg.get("tige_diam", 6) / 2, (ext_ - bas).Length, bas, (ext_ - bas).normalized()), name=f"martingale_tige_{nom}", color=gm)

def piece_angle(pa, xb, zb, sg, sens, du=0.0):
    """Pièce d'angle poutre / longeron (fonderie), d'après photos : manchon autour de la poutre, nez arrondi autour du bout
    du longeron qui dépasse devant la poutre AV (sens = 1) ou derrière la poutre AR (sens = -1), emboîture sur le pylône."""
    yi, ye = pa["y_int"], pa["y_ext"]
    m, hm = pa["manchon"], pa["manchon_demi_h"]
    man = cq.Workplane().box(2 * m, pa["y_nez"] - yi + 10, 2 * hm).edges("|Y").fillet(hm - 8).val() \
        .translate(V(xb, sg * (yi + (pa["y_nez"] - yi + 10) / 2), zb))
    nx, hn, r = pa["nez_x"], pa["nez_demi_h"], pa["nez_r"]
    lx = nx - pa["nez_x_fin"]
    nez = cq.Workplane().box(lx, ye - pa["y_nez"], 2 * hn).edges("|Z").fillet(min(r, (ye - pa["y_nez"]) / 2 - 1)).edges().fillet(hn - 12).val() \
        .translate(V(xb - sens * (pa["nez_x_fin"] + lx / 2), sg * (pa["y_nez"] + ye) / 2, zb))
    bos = cq.Solid.makeCylinder(pa["bossage_d"] / 2, pa["bossage_bas"] - hm + 12, V(xb, sg * pa["y_pylone"], zb - pa["bossage_bas"]))
    return man.fuse(nez).fuse(bos).clean()

def yinyang(R, anneau=None):
    """Taijitu de rayon R centré en (0, 0) dans le plan (u, v) : (blanc, noir) en polygones shapely.
    Moitié blanche à gauche (tête en haut), moitié noire à droite (tête en bas), un point de chaque couleur, anneau noir."""
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    disque = Point(0, 0).buffer(R, 128)
    haut, bas = Point(0, R / 2).buffer(R / 2, 96), Point(0, -R / 2).buffer(R / 2, 96)
    blanc = unary_union([disque.intersection(box(-R, -R, 0, R)), haut]).difference(bas)
    p_haut, p_bas = Point(0, R / 2).buffer(R / 6, 64), Point(0, -R / 2).buffer(R / 6, 64)
    blanc = unary_union([blanc.difference(p_haut), p_bas])
    ep_a = R / 30 if anneau is None else anneau
    blanc = blanc.intersection(Point(0, 0).buffer(R - ep_a, 128))
    noir = disque.difference(blanc)
    return blanc, noir


def decalque(geom, y0, ep, cx, cz, miroir=False, clip=None):
    """Polygones shapely (u, v) posés à (cx, cz) dans le plan xz, épaisseur ep à partir de y0 (vers +y si ep > 0)."""
    from shapely import affinity
    from shapely.geometry import MultiPolygon
    g = affinity.scale(geom, xfact=-1 if miroir else 1, origin=(0, 0))
    g = affinity.translate(g, cx, cz)
    if clip is not None:
        g = g.intersection(clip)
    if g.is_empty:
        return None
    sols = []
    for pg in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        if pg.geom_type != "Polygon" or pg.area < 1:
            continue
        pg = pg.simplify(0.3)
        w = cq.Workplane("XZ", origin=(0, y0 + (ep if ep > 0 else 0), 0)).polyline(list(pg.exterior.coords)[:-1]).close()
        sol = w.extrude(abs(ep)).val()
        for tr in pg.interiors:
            tw = cq.Workplane("XZ", origin=(0, y0 + (ep if ep > 0 else 0) + 1, 0)).polyline(list(tr.coords)[:-1]).close()
            sol = sol.cut(tw.extrude(abs(ep) + 2).val())
        sols.append(sol)
    if not sols:
        return None
    out = sols[0]
    for so in sols[1:]:
        out = out.fuse(so)
    return out


def poser_yinyang(A, nom, R, y0, ep, cx, cz, miroir=False, clip=None, groupe="decor"):
    blanc, noir = yinyang(R)
    for coul, g, rgb in (("blanc", blanc, (0.97, 0.97, 0.95)), ("noir", noir, (0.07, 0.07, 0.08))):
        so = decalque(g, y0, ep, cx, cz, miroir, clip)
        if so is not None:
            A.add(so, name=f"{groupe}_yinyang_{nom}_{coul}", color=cq.Color(*rgb))


def peindre(A, pe):
    """Finition (JD 29/09) : coffre et bancs peints en blanc, couples et pièces de maintien en noir."""
    if not pe:
        return
    import re
    for ch in A.children:
        for motif, rgb in pe:
            if re.search(motif, ch.name):
                ch.color = cq.Color(*rgb)
                break


def build(cfg, plateforme_seule=False):
    """Assemblage complet ; plateforme_seule=True : coques, poutres, longerons, trampoline, martingale, safrans (HC16 d'origine)."""
    PONT_CFG.clear(); PONT_CFG.update(cfg["coques"])
    CFG_MAT.clear(); CFG_MAT.update(cfg["mats"])
    CFG_COFFRE_Y.clear()
    if "coffre" in cfg:
        CFG_COFFRE_Y["y_joue"] = cfg["coffre"]["largeur"] / 2
    c, p, m, vo, s = cfg["coques"], cfg["plateforme"], cfg["mats"], cfg["voile"], cfg["safrans"]
    hy = c["entraxe"] / 2
    fb, rb, bz = p["poutre_av_x"], p["poutre_ar_x"], p["poutre_z"]
    zav, zar = p.get("poutre_av_z", bz), p.get("poutre_ar_z", bz)        # axes des poutres aux extrémités
    ly = p.get("longeron_y", hy)                                          # axe des longerons
    A = cq.Assembly(name="HC16_plateforme" if plateforme_seule else "HC16_Rando")
    gris, alu, noir = cq.Color(0.89, 0.88, 0.86), cq.Color(0.62, 0.64, 0.66), cq.Color(0.12, 0.12, 0.12)

    COQUES = {}
    for nom, y in (("babord", hy), ("tribord", -hy)):
        COQUES[nom] = coque(c, y)
        A.add(COQUES[nom], name=f"coque_{nom}", color=gris)
        sg = 1 if y > 0 else -1
        for xb, zb_, tag in ((fb, zav, "av"), (rb, zar, "ar")):
            A.add(cyl((xb, y, interp(c["pont"], xb)), (xb, y, zb_), p["pylone_diam"]),
                  name=f"pylone_{tag}_{nom}", color=alu)
        # longeron : profil en goutte, queue vers le trampoline, de l'axe de la poutre AV à celui de la poutre AR
        pl_ = (zar - zav) / (rb - fb); e_ = p.get("longeron_dans_pieces", 0.0)
        A.add(cq.Solid.extrudeLinear(fil_section(profil_uv('longeron'), V(fb - e_, sg * ly, zav - pl_ * e_), V(0, -sg, 0)), [], V(rb - fb + 2 * e_, 0, (zar - zav) + 2 * pl_ * e_)),
              name=f"longeron_{nom}", color=alu)
        pa_ = p.get("piece_angle")
        if pa_:                                           # pièces d'angle d'après les photos (face intérieure d'après A2)
            for xb, zb_, tag, sens in ((fb, zav, "av", 1), (rb, zar, "ar", -1)):
                A.add(piece_angle(pa_, xb, zb_, sg, sens, p.get("poutre_axe_u", 0.0)),
                      name=f"piece_angle_{tag}_{nom}", color=cq.Color(0.50, 0.52, 0.55))
        A.add(cq.Solid.makeBox(s["corde"], s["epaisseur"], s["hauteur"],
              V(s["x"] - s["corde"] / 2, y - s["epaisseur"] / 2, s["z_centre"] - s["hauteur"] / 2)),
              name=f"safran_{nom}", color=noir)
    lp = p["poutre_longueur"] / 2
    # axe relevé des poutres (axe des pièces d'angle, P2/P3/D1) : milieu de la section, à du derrière le centre du nez (D5)
    du = p.get("poutre_axe_u", 0.0)
    xav0, xar0 = fb - du, rb + du                     # centres des nez = origines des profils DWG
    POUTRE_AV.clear()
    if p.get("poutre_av_fleche"):
        yf_ = p.get("poutre_av_y_libre", lp)
        pav = profil_cintre('poutre', xav0, zav, p["poutre_av_fleche"], lp, V(1, 0, 0), y_libre=yf_)
        POUTRE_AV.update(x=xav0, z_ext=zav, fleche=p["poutre_av_fleche"], y_ext=lp, y_libre=yf_, r=-u_min('poutre'), u0=u_min('poutre') - 4, u1=u_max('poutre') + 4,
                         degagement=profil_cintre('poutre', xav0, zav, p["poutre_av_fleche"], lp, V(1, 0, 0), marge=4, y_lim=lp + 60, y_libre=yf_))
        A.add(pav, name="poutre_av", color=alu)
    else:
        A.add(cyl((fb, -lp, zav), (fb, lp, zav), p["poutre_diam"]), name="poutre_av", color=alu)
    A.add(profil_droit('poutre', V(xar0, -lp, zar), V(0, 1, 0), 2 * lp, V(-1, 0, 0)), name="poutre_ar", color=alu)
    A.add(cyl((s["barre_x"], -hy, s["barre_z"]), (s["barre_x"], hy, s["barre_z"]), 30),
          name="barre_accouplement", color=alu)
    # trampoline lacé dans les fentes, au bout des queues : bord avant sur la poutre cintrée, bord arrière droit
    ut, ul = u_max('poutre'), u_max('longeron'); yt = ly - ul; fl_ = p.get("poutre_av_fleche", 0)
    zf_ = lambda y: z_cambre(y, zav, fl_, p.get("poutre_av_y_libre", lp))
    sections = [cq.Wire.makePolygon([V(xav0 + ut, y, zf_(y)), V(xar0 - ut, y, zar), V(xar0 - ut, y, zar - 3), V(xav0 + ut, y, zf_(y) - 3)], close=True)
                for y in [-yt + 2 * yt * i / 16 for i in range(17)]]
    A.add(cq.Solid.makeLoft(sections, False), name="trampoline", color=cq.Color(0.96, 0.96, 0.94))   # mesh blanc (JD 29/09)
    mg = p.get("martingale")
    if mg:
        martingale(A, mg, fb, zav, fl_, -u_min('poutre'))

    PLAT.clear()
    PLAT.update(fb=fb, rb=rb, zav=zav, zar=zar, ly=ly, pa=p.get("piece_angle"), du=p.get("poutre_axe_u", 0.0), mg=p.get("martingale"))
    if "coffre" in cfg and not plateforme_seule:
        cfg["coffre"]["_livarde_diam"] = ((cfg.get("voile") or {}).get("livarde") or {}).get("diam", 30)
        coffre(A, cfg["coffre"])
    if plateforme_seule:
        return A

    a = math.radians(m["quete_deg"])
    u = V(math.sin(a), 0, math.cos(a))
    enr = vo.get("enroulement", {})
    for nom, y in (("babord", m["y_axe"]), ("tribord", -m["y_axe"])):
        f = V(m["x_pied"], y, m["z_pied"])
        A.add(cq.Solid.makeCylinder(m["diam"] / 2, m["longueur"], f, u), name=f"mat_{nom}", color=noir)
        if "collier_hauteur" in m:
            tc = m["collier_hauteur"]; c0 = f + u * (tc - 25)
            col = cq.Solid.makeCylinder(46, 50, c0, u).cut(cq.Solid.makeCylinder(31, 50, c0, u))
            yj = CFG_COFFRE_Y.get("y_joue")                  # demi-collier (étrier) boulonné sur la joue
            if yj:
                sgn = 1 if y > 0 else -1
                col = col.cut(cq.Solid.makeBox(400, 400, 400, V(c0.x - 200, sgn * yj - (400 if sgn > 0 else 0), c0.z - 200)))
            A.add(col, name=f"collier_{nom}", color=cq.Color(0.55, 0.55, 0.58))
        h = f + u * m["haubanage"]
        A.add(cq.Solid.makeSphere(25, h, angleDegrees1=-90, angleDegrees2=90),
              name=f"repere_haubanage_{nom}", color=cq.Color(0.33, 0.29, 0.72))
        sm = m.get("semelle")
        if sm:                                              # renfort de pont cintré + semelle CP + bourrage époxy
            sgm = 1 if y > 0 else -1; hull = COQUES["babord" if sgm > 0 else "tribord"]
            rp = sm.get("renfort", {})
            if rp:
                ep_r = rp["ep"]; yc_ = sgm * hy
                zone = cq.Solid.makeBox(rp["dx"][1] - rp["dx"][0], 2 * rp["demi_y"], 160, V(f.x + rp["dx"][0], yc_ - rp["demi_y"], f.z - 120))
                ren = hull.translate(V(0, 0, ep_r)).cut(hull).intersect(zone)
                A.add(ren, name=f"renfort_pont_{nom}", color=cq.Color(0.86, 0.66, 0.44))
            else:
                ep_r = 0.0
            dy0, dy1 = (sm["dy"][0], sm["dy"][1]) if sgm > 0 else (-sm["dy"][1], -sm["dy"][0])
            pl = cq.Solid.makeBox(sm["dx"][1] - sm["dx"][0], dy1 - dy0, sm["ep"], V(f.x + sm["dx"][0], f.y + dy0, f.z - sm["ep"]))
            pl = pl.rotate(f, f + V(0, 1, 0), m["quete_deg"])
            A.add(pl, name=f"semelle_{nom}", color=cq.Color(0.91, 0.72, 0.51))
            pr = cq.Solid.makeBox(sm["dx"][1] - sm["dx"][0] + 20, dy1 - dy0, 140, V(f.x + sm["dx"][0] - 10, f.y + dy0, f.z - sm["ep"] - 120))
            cutp = cq.Solid.makeBox(sm["dx"][1] - sm["dx"][0] + 60, dy1 - dy0 + 20, 200, V(f.x + sm["dx"][0] - 30, f.y + dy0 - 10, f.z - sm["ep"])).rotate(f, f + V(0, 1, 0), m["quete_deg"])
            bou = pr.cut(cutp).cut(hull.translate(V(0, 0, ep_r))).intersect(
                cq.Solid.makeBox(sm["dx"][1] - sm["dx"][0], dy1 - dy0, 200, V(f.x + sm["dx"][0], f.y + dy0, f.z - 200)).rotate(f, f + V(0, 1, 0), m["quete_deg"]))
            A.add(bou, name=f"bourrage_{nom}", color=cq.Color(0.78, 0.55, 0.30))
        hb_ = cfg.get("coffre", {}).get("haubans") if not plateforme_seule else None
        if hb_ and "collier_hauteur" in m:                 # haubans du coffre : attaches sur le collier, devant et derrière le mât
            sgm = 1 if y > 0 else -1
            cc = f + u * m["collier_hauteur"]; ax_ = V(math.cos(a), 0, -math.sin(a))
            p_av, p_ar = cc - ax_ * hb_["attache_dx"], cc + ax_ * hb_["attache_dx"]
            def pts_etrave(s_):
                return V(hb_["etrave"]["x"], s_ * hy, interp(c["pont"], hb_["etrave"]["x"]) + hb_["etrave"]["dz"])
            def pts_cadene(s_):
                yc2 = s_ * (hy + hb_["cadene"]["dy"])
                return V(hb_["cadene"]["x"], yc2, interp_pont(hb_["cadene"]["x"], yc2) + hb_["cadene"]["dz"])
            inox = cq.Color(0.80, 0.82, 0.84)
            dyav_ = hb_.get("attache_dy_av", 0)            # (JD 30/09 soir) direct AV attaché plus à l'extérieur : il passe dehors de la livarde rangée contre la joue
            liens = [("av", p_av + V(0, sgm * dyav_, 0), pts_etrave(sgm)), ("ar", p_ar, pts_cadene(sgm))]
            if hb_.get("croises_avant"):                  # croisés : œil sur le dessus du collier, pour passer au-dessus de la joue
                liens.append(("av_croise", p_av + V(0, 0, hb_.get("croise_dz", 35)), pts_etrave(-sgm)))
            if hb_.get("croises_arriere") and PLAT.get("pa"):
                g_ = cfg["coffre"].get("_geom", {})
                xk = hb_["x_croise_ar"]; st = min(1.0, max(-1.0, (xk - g_["xcol"]) / g_["ar"]))
                zj = g_["fond_cotes"] + (g_["zt_s"] - g_["fond_cotes"]) * math.cos(math.asin(st)) - 30
                pa_ = PLAT["pa"]
                haut = V(xk, sgm * (cfg["coffre"]["largeur"] / 2 + 3), zj)
                bas = V(xk, -sgm * (pa_["y_nez"] + pa_["y_ext"]) / 2, PLAT["zav"] + pa_["nez_demi_h"])
                liens.append(("ar_croise", haut, bas))
            hs_ = hb_.get("semelle")
            if hs_ and m.get("semelle"):                  # même configuration dans le plan horizontal des semelles
                zs_ = lambda dx_: f.z - math.tan(a) * dx_ + hs_["dz"]
                s_av = V(f.x - hs_["attache_dx"], f.y, zs_(-hs_["attache_dx"]))
                s_ar = V(f.x + hs_["attache_dx"], f.y, zs_(hs_["attache_dx"]))
                liens += [("semelle_av", s_av, pts_etrave(sgm)), ("semelle_ar", s_ar, pts_cadene(sgm))]
                if hs_.get("croises_avant", hb_.get("croises_avant")):
                    liens.append(("semelle_av_croise", s_av, pts_etrave(-sgm)))
                if hs_.get("croises_arriere"):              # croisés AR dans le plan des semelles
                    pbi = hs_.get("pontet_interieur")
                    if pbi:                                  # vers un pontet au bord intérieur du pont opposé (la cadène est derrière le bombé)
                        ybi = -sgm * (hy - pbi["dy"])
                        liens.append(("semelle_ar_croise", s_ar, V(pbi["x"], ybi, interp_pont(pbi["x"], ybi) + pbi["dz"])))
                    else:
                        liens.append(("semelle_ar_croise", s_ar, pts_cadene(-sgm)))
                if hs_.get("vers_martingale"):              # variante : de la semelle au pied du pilier de martingale
                    mg_ = p.get("martingale", {})
                    liens.append(("semelle_ar_martingale", s_ar, V(fb, 0, zav - mg_.get("pied_sous_axe_extremites", 170))))
            for tag, q0, q1 in liens:
                A.add(cq.Solid.makeCylinder(hb_["diam"] / 2, (q1 - q0).Length, q0, (q1 - q0).normalized()), name=f"hauban_coffre_{tag}_{nom}", color=inox)
            tc_ = hb_.get("tube_colliers")
            if tc_ and sgm > 0:                              # tube alu entre les colliers, à hauteur de leur centre, d'une joue à l'autre
                yj_ = cfg["coffre"]["largeur"] / 2; c0_ = V(tc_.get("x", cc.x), -yj_, tc_.get("z", cc.z))
                tube = cq.Solid.makeCylinder(tc_["diam"] / 2, 2 * yj_, c0_, V(0, 1, 0)).cut(cq.Solid.makeCylinder(tc_["diam"] / 2 - tc_["ep"], 2 * yj_, c0_, V(0, 1, 0)))
                A.add(tube, name="tube_colliers", color=cq.Color(0.70, 0.72, 0.75))
        rest, d = voile_restante(vo["contour"], a, enr.get(nom, 0))
        if rest:
            pts = [(m["x_pied"] + dx, m["z_pied"] + dz) for dx, dz in rest]
            voile = cq.Workplane("XZ", origin=(0, y, 0)).polyline(pts).close().extrude(0.5, both=True)
            A.add(voile, name=f"voile_{nom}", color=cq.Color(0.95, 0.93, 0.88))
            yyv = (cfg["coffre"].get("yinyang") or {}).get("voiles") if "coffre" in cfg else None
            if yyv:                                               # dessin du bateau (JD 29/09) : yin-yang sur chaque face de la voile
                from shapely.geometry import Polygon as _Pg
                rest0, _ = voile_restante(vo["contour"], a, 0)
                pg0 = _Pg([(m["x_pied"] + dx, m["z_pied"] + dz) for dx, dz in rest0])
                cxy, czy = m["x_pied"] + yyv["dx"], m["z_pied"] + yyv["dz"]      # position sur la voile pleine (repère du pied de mât)
                if d:                                                 # voile en partie roulée : la toile, et le dessin, avancent de d avec la chute
                    cxy, czy = cxy - d * math.cos(a), czy + d * math.sin(a)
                clip = _Pg(pts).buffer(-yyv.get("marge", 30))
                sgv = 1 if y > 0 else -1
                poser_yinyang(A, f"voile_{nom}_ext", yyv["r"], y + sgv * 0.5, sgv * 0.4, cxy, czy, miroir=(sgv < 0), clip=clip, groupe="decor")
                poser_yinyang(A, f"voile_{nom}_int", yyv["r"], y - sgv * 0.5, -sgv * 0.4, cxy, czy, miroir=(sgv > 0), clip=clip, groupe="decor")
        frac_ = enr.get(nom, 0)
        if frac_ > 0:                                               # partie roulée autour du guindant (repère visuel : toile de 0,35)
            t_, r_m = vo.get("toile_ep", 0.35), m["diam"] / 2
            w_t, w_h = vo["contour"][0][1], vo["contour"][-1][1]
            l_r = max(u_ for u_, _ in vo["contour"]) if frac_ >= 1 else d
            r_b = math.sqrt(r_m ** 2 + l_r * t_ / math.pi)
            r_h = r_m + 1 if frac_ >= 1 else r_b
            ext_r = (cq.Solid.makeCone(r_b, r_h, w_h - w_t, f + u * w_t, u) if abs(r_b - r_h) > 1e-6
                     else cq.Solid.makeCylinder(r_b, w_h - w_t, f + u * w_t, u))      # en partie roulée : rouleau cylindrique
            rou = ext_r.cut(cq.Solid.makeCylinder(r_m, w_h - w_t, f + u * w_t, u))
            A.add(rou, name=f"voile_roulee_{nom}", color=cq.Color(0.95, 0.93, 0.88))
        lv = vo["livarde"]
        s0 = f + u * lv["w_mat"]
        cu, cw = vo["contour"][1]                                    # point d'écoute voile pleine
        s1 = f + V(cu * math.cos(a) + cw * math.sin(a), 0, -cu * math.sin(a) + cw * math.cos(a))
        sgl = 1 if y > 0 else -1
        if lv.get("type") == "wishbone":                             # ancienne variante : deux bras cintrés de part et d'autre de la voile
            for sg, cote in ((1, "a"), (-1, "b")):
                mid = s0 + (s1 - s0) * 0.45 + V(0, sg * lv["ecart"], 0)
                bez = [s0 * (1 - t) ** 2 + mid * (2 * t * (1 - t)) + s1 * t ** 2
                       for t in [i / 10 for i in range(11)]]
                seg = cq.Compound.makeCompound([cyl(q0.toTuple(), q1.toTuple(), lv["diam"])
                                                for q0, q1 in zip(bez, bez[1:])])
                A.add(seg, name=f"livarde_{nom}_{cote}", color=cq.Color(0.45, 0.45, 0.45))
        else:                                                        # tube carbone droit, d'un seul côté de la voile (JD 29/09)
            carb = cq.Color(0.16, 0.16, 0.17)
            dv = (s1 - s0).normalized()
            q0 = s0 + dv * (m["diam"] / 2 + lv.get("jeu_mat", 5))    # bout côté mât : mâchoire contre le mât
            Lt = (s1 - q0).Length
            vo["_livarde_longueur"] = Lt
            rangee = lv.get("rangee", "auto")
            if rangee == "auto":
                rangee = frac_ > 0                                   # voile roulée, même en partie : livarde démontée et rangée
            tube_ = lambda p_, ax, L_: cq.Solid.makeCylinder(lv["diam"] / 2, L_, p_, ax).cut(
                cq.Solid.makeCylinder(lv["diam"] / 2 - lv.get("ep", 1.5), L_, p_, ax))
            if rangee:                                               # rangée debout devant le mât
                rg = lv.get("rangement", {})
                fo_ = (cfg.get("coffre", {}).get("_fourreau") or {}).get(nom)
                if rg.get("vertical") and fo_:                       # verticale, pied au fond du fourreau du coffre (JD 30/09)
                    A.add(tube_(V(fo_["x"], fo_["y"], fo_["z_bas"]), V(0, 0, 1), Lt), name=f"livarde_{nom}_rangee", color=carb)
                else:                                                # ancienne place : parallèle au mât, pied sur l'avant du collier
                    ax_ = V(math.cos(a), 0, -math.sin(a))
                    p0 = f - ax_ * rg.get("dx", 75) + V(0, sgl * rg.get("dy", 0), 0) + u * rg.get("dw", 0)
                    A.add(tube_(p0, u, Lt), name=f"livarde_{nom}_rangee", color=carb)
            else:
                off = V(0, sgl * (lv["diam"] / 2 + 1), 0)            # contre la voile, côté extérieur
                A.add(tube_(q0 + off, dv, Lt), name=f"livarde_{nom}", color=carb)
    peindre(A, cfg.get("peinture"))
    return A

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "cotes.yaml"
    out = sys.argv[2] if len(sys.argv) > 2 else "hc16_rando_sans_coffre.step"
    cfg = yaml.safe_load(open(src))
    A = build(cfg)
    m, vo = cfg["mats"], cfg["voile"]
    a = math.radians(m["quete_deg"])
    for nom in ("babord", "tribord"):
        f = vo.get("enroulement", {}).get(nom, 0)
        rest, d = voile_restante(vo["contour"], a, f)
        if rest:
            S, (cx, cz) = aire_cdg(rest)
            print(f"voile {nom} : enroulée {f:.0%} (largeur {d:.0f} mm), {S/1e6:.2f} m², "
                  f"CV {m['x_pied']+cx:.0f} mm de l'étrave, {m['z_pied']+cz:.0f} mm / flottaison")
        else:
            print(f"voile {nom} : entièrement roulée")
    A.export(out)
    print("OK", out)
