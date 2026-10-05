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
    xf = k["avant_x"]
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
    def profil(zb_, zt_=None, off=0.0, n=48):
        zt_ = ztop if zt_ is None else zt_
        a_, h_ = af - off, zt_ - zb_ - 2 * off
        pts_ = [(xa - off, zb_ + off)]
        # paramétrage à pente égale (réf. HREF) : entre deux stations, les génératrices relient des points de même
        # tangente -> bordés latéraux développables (pas de torsion) malgré des hauteurs différentes
        ts_ = [math.atan2(h_ * math.sin(u), HREF * math.cos(u)) for u in [math.pi / 2 * i / n for i in range(n + 1)]]
        pts_ += [(xcol - a_ * math.cos(t), zb_ + off + h_ * math.sin(t)) for t in ts_]
        return pts_ + [(xa - off, zt_ - off)]
    def loft(off, y_ext):
        solids = []
        for sg in (1, -1):
            ys_ = sorted({0.0, cpl, cpt, y_ext})
            ys_ = [yy for yy in ys_ if yy <= y_ext]
            wires = [cq.Wire.makePolygon([V(x, sg * yy, z) for x, z in profil(zb_at(min(yy, wi)), zt_at(min(yy, wi)), off)], close=True) for yy in ys_]
            solids.append(cq.Solid.makeLoft(wires, True))
        return solids[0].fuse(solids[1]).clean()
    avant = [(xcol - af * math.cos(t), zb + bj * math.sin(t)) for t in [math.pi / 2 * i / 48 for i in range(49)]]
    pts = [(xa, zb)] + avant + [(xa, ztop)]
    inner = Polygon(pts).buffer(-e, join_style=2)
    ipts = list(inner.exterior.coords)[:-1]
    ext_s = loft(0.0, wi)
    int_s = loft(e, wi + 1)
    coque = ext_s.cut(int_s)
    zpl = k["plateau_z"]
    plat = None
    if zpl < ztop - 60:
        plat = cq.Solid.makeBox(xa - xf, 2 * wi, k["ep_plateau"], V(xf, -wi, zpl - k["ep_plateau"])).intersect(int_s)
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
        A.add(coque.intersect(blk), name="coffre_capot", color=cq.Color(0.86, 0.66, 0.44))
        coque = coque.cut(blk)
    for i, t4 in enumerate(k.get("trappes_c4") or [], 1):      # trappes de visite dans la face arrière
        blk = cq.Solid.makeBox(e + 10, t4["y1"] - t4["y0"], t4["z1"] - t4["z0"], V(xa - e - 5, t4["y0"], t4["z0"]))
        A.add(coque.intersect(blk), name=f"coffre_trappe_c4_{i}", color=cq.Color(0.86, 0.66, 0.44))
        coque = coque.cut(blk)
    A.add(coque, name="coffre_coque", color=bois)
    if plat is not None:
        A.add(plat, name="coffre_plateau", color=bois)
    if k.get("cloisons_y"):
        ycs = list(k["cloisons_y"])
    else:
        n = max(0, math.ceil(2 * wi / k["pas_cloisons"]) - 1)
        ycs = [-wi + 2 * wi * i / (n + 1) for i in range(1, n + 1)]
    for i, yc in enumerate(ycs, 1):
        cl = cq.Workplane("XZ", origin=(0, yc + ec / 2, 0)).polyline(profil(zb_at(yc), zt_at(yc), e)).close().extrude(ec).val()
        if niche_ext is not None:
            cl = cl.cut(niche_ext)
        if cl.Volume() > 1:
            A.add(cl, name=f"coffre_cloison_{i}", color=bois)
    bt = k.get("batterie")
    if bt:
        # batterie dans son bac, sur deux cales qui mettent le fond en pente de niveau
        x0b, y0b, y1b = bt["x_ar"] - bt["bac"][1], bt["y_ext"], bt["y_ext"] + bt["bac"][0]
        if bt.get("appui_direct"):
            zpl_b = zb + e
        elif bt.get("lisses"):
            li = bt["lisses"]; zpl_b = zb + e + li["h"]
            for j, yl in enumerate(li["y"], 1):
                A.add(cq.Solid.makeBox(bt["bac"][1], li["larg"], li["h"], V(x0b, yl - li["larg"] / 2, zb + e)), name=f"batterie_lisse_{j}", color=cq.Color(0.55, 0.36, 0.20))
        else:
            zpl_b = max(zb_at(y0b), zb_at(y1b)) + e + bt["jeu_cale"]
            for nom, xc in (("av", x0b + 20), ("ar", bt["x_ar"] - 20 - bt["cale_ep"])):
                pts_c = [(y0b, zb_at(y0b) + e), (y1b, zb_at(y1b) + e), (y1b, zpl_b), (y0b, zpl_b)]
                cale = cq.Workplane("YZ", origin=(xc, 0, 0)).polyline(pts_c).close().extrude(bt["cale_ep"]).val()
                A.add(cale, name=f"batterie_cale_{nom}", color=cq.Color(0.66, 0.42, 0.22))
        bac = cq.Solid.makeBox(bt["bac"][1], bt["bac"][0], bt["bac"][2], V(x0b, y0b, zpl_b))
        A.add(bac.cut(cq.Solid.makeBox(bt["bac"][1] - 8, bt["bac"][0] - 8, bt["bac"][2], V(x0b + 4, y0b + 4, zpl_b + 4))), name="batterie_bac", color=cq.Color(0.2, 0.22, 0.25))
        cx, cy = x0b + bt["bac"][1] / 2, (y0b + y1b) / 2
        A.add(cq.Solid.makeBox(bt["cellule"][1], bt["cellule"][0], bt["cellule"][2], V(cx - bt["cellule"][1] / 2, cy - bt["cellule"][0] / 2, zpl_b + 4)), name="batterie", color=cq.Color(0.12, 0.35, 0.55))
        k["_batterie"] = dict(x=(x0b, bt["x_ar"]), y=(y0b, y1b), z=(zpl_b, zpl_b + bt["bac"][2]), cg=(cx, cy, zpl_b + 4 + bt["cellule"][2] / 2))
    k["_geom"] = dict(zt=ztop, zt_s=zt_s, xcol=xcol, avant=xf, arriere=xr, af=af, ar=ar_, b=bj, volume_L=ext_s.Volume() / 1e6, fond_cotes=zb_s)
    # pattes verticales de collier : sur la face extérieure des joues, devant et derrière le mât, jusqu'au collier
    pc = k.get("pattes_collier")
    if pc and zt_s < zc:                   # inutiles quand la joue monte jusqu'au collier
        alu = cq.Color(0.72, 0.74, 0.77)
        z0p, z1p = ztop - pc["recouvrement"], zc + pc["au_dessus_axe_collier"]
        for nom, sg in (("babord", 1), ("tribord", -1)):
            y0p = W / 2 if sg > 0 else -W / 2 - pc["ep"]
            for cote, x0p in (("av", xcol - pc["ecart"] - pc["larg"]), ("ar", xcol + pc["ecart"])):
                A.add(cq.Solid.makeBox(pc["larg"], pc["ep"], z1p - z0p, V(x0p, y0p, z0p)), name=f"patte_collier_{nom}_{cote}", color=alu)
    # joues : quart d'ellipse avant + quart d'ellipse arrière (dossier jusqu'au bout du banc)
    bj_s = zt_s - zb_s
    avant_j = [(xcol - af * math.cos(t), zb_s + bj_s * math.sin(t)) for t in [math.pi / 2 * i / 48 for i in range(49)]]
    arriere = [(xcol + ar_ * math.sin(t), zb_s + bj_s * math.cos(t)) for t in [math.pi / 2 * i / 48 for i in range(1, 49)]]
    prof = avant_j + arriere
    for nom, y0 in (("babord", W / 2), ("tribord", -wi)):
        fl = cq.Workplane("XZ", origin=(0, y0, 0)).polyline(prof).close().extrude(ef).val()
        if PLAT:                                           # joue au-dessus du longeron : dégagée autour de la pièce d'angle AV et du longeron
            sgj = 1 if y0 > 0 else -1
            fl = fl.cut(degagement_joue(sgj, y0, ef, xr + 20, b.get("plan_z")))
        elif POUTRE_AV.get("degagement") is not None:
            pa = POUTRE_AV; ya = abs(y0) + ef / 2; zax = z_cambre(ya, pa["z_ext"], pa["fleche"], pa.get("y_libre", pa["y_ext"]))
            fl = fl.cut(POUTRE_AV["degagement"])            # encoche en U : la joue se pose sur la poutre par-dessus
            fl = fl.cut(cq.Solid.makeBox(pa["u1"] - pa["u0"], ef + 20, zax - zb_s + 20, V(pa["x"] + pa["u0"], y0 - 10, zb_s - 20)))
        else:
            fl = fl.cut(cq.Solid.makeCylinder(b["encoche_poutre_r"], ef + 20, V(b["poutre_x"], y0 + 10, b["poutre_z"]), V(0, -1, 0)))
        A.add(fl, name=f"joue_{nom}", color=cq.Color(0.74, 0.52, 0.34))
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
            zloc = min(zb_at(y0c), zb_at(y0c + ar["ep_joue"]))
            A.add(cq.Solid.makeBox(xb1 - x_av, ar["ep_joue"], zloc - zbas, V(x_av, y0c, zbas)),
                  name=f"chaise_joue_{nom}", color=brun)
        if car:
            # carter : fond et face avant entre les joues ; la tête relevée y est enfermée
            yl = ar["demi_passage"]
            zloc = min(zb_at(ym - yl), zb_at(ym + yl))
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
                z1 = zb_at(abs(yp)) + e
                tb = cq.Solid.makeCylinder(py["diam"] / 2, z1 - z0, V(xp, yp, z0)).cut(cq.Solid.makeCylinder(py["diam"] / 2 - py["ep"], z1 - z0, V(xp, yp, z0)))
                A.add(tb, name=f"pylone_coffre_{nom}_{j}", color=cq.Color(0.16, 0.16, 0.17))
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
    ac = k.get("accroches_poutre")
    if ac and POUTRE_AV:
        pv = POUTRE_AV; ko_uv = demi_profil('poutre', ac["jeu"]); vmax = max(v for u, v in PROFILS['poutre'])
        for i, yh in enumerate(ac["y"]):
            zc_ = z_cambre(yh, pv["z_ext"], pv["fleche"], pv.get("y_libre", pv["y_ext"]))
            ko = SPoly([(pv["x"] + u, zc_ + v) for u, v in ko_uv.exterior.coords])
            pl = sbox(xa, zc_ - ac["sous_axe"], ac["fin_x"], zc_ + vmax + ac["au_dessus"]).difference(ko)
            if pl.geom_type != "Polygon":
                pl = max(pl.geoms, key=lambda g_: g_.area)
            sol = cq.Workplane("XZ", origin=(0, yh + ac["ep"] / 2, 0)).polyline(list(pl.exterior.coords)[:-1]).close().extrude(ac["ep"]).val()
            A.add(sol, name=f"accroche_poutre_{i}", color=cq.Color(0.66, 0.42, 0.22))
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
        A.add(cas.cut(cut), name=f"banc_{nom}_caisson", color=bois)
        A.add(cas.intersect(cut), name=f"banc_{nom}_assise", color=cq.Color(0.72, 0.50, 0.32))
        if PLAT and b.get("couples_x"):                     # couples transversaux accrochés au longeron (demi-profil DWG + jeu)
            ko_uv = demi_profil('longeron', 2)
            zl = lambda x_: PLAT["zav"] + (PLAT["zar"] - PLAT["zav"]) * (x_ - PLAT["fb"]) / (PLAT["rb"] - PLAT["fb"])
            ly_ = PLAT["ly"]; cep = b["couple_ep"]
            for j, xc_ in enumerate(b["couples_x"]):
                za_ = zl(xc_)
                ko = SPoly([(sg * (ly_ - u), za_ + v) for u, v in ko_uv.exterior.coords])
                yA, yB = sorted((sg * b["y_int"], sg * wi)); yC, yD = sorted((sg * (ly_ - u_max("longeron") - 2), sg * b["couple_ext"]))
                fr = sunion([sbox(yA, zt0, yB, zs - es), sbox(yC, za_ - b["couple_sous_axe"], yD, zt0)]).difference(ko)
                if fr.geom_type != "Polygon":
                    fr = max(fr.geoms, key=lambda g_: g_.area)
                sol = cq.Workplane("YZ", origin=(xc_ - cep / 2, 0, 0)).polyline(list(fr.exterior.coords)[:-1]).close().extrude(cep).val()
                A.add(sol, name=f"banc_{nom}_couple_{j}", color=cq.Color(0.66, 0.42, 0.22))

CFG_MAT = {}
PLAT = {}               # plateforme vue par le coffre (poutres, longerons, pièces d'angle)
def degagement_joue(sg, y0, ef, x_fin, z_bas_banc=None):
    """Volume à retirer d'une joue posée sur le longeron : nez de la pièce d'angle AV (ouvert vers le bas) puis
    longeron jusqu'au bout du banc (dessus du longeron + 4), en suivant sa pente."""
    pa, fb, zav, zar, rb = PLAT["pa"], PLAT["fb"], PLAT["zav"], PLAT["zar"], PLAT["rb"]
    ya, yb = sorted((y0 - 10, y0 + ef + 10))
    xa_, xb_ = fb - pa["nez_x"] - 4, fb - pa["nez_x_fin"] + 4
    nez = cq.Solid.makeBox(xb_ - xa_, yb - ya, zav + pa["nez_demi_h"] + 4 + 200, V(xa_, ya, -200))
    pente = (zar - zav) / (rb - fb); v_top = max(v for u, v in PROFILS['longeron']) + 4
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
    A.add(cq.Solid.makeLoft(sections, False), name="trampoline", color=cq.Color(0.17, 0.17, 0.17))
    mg = p.get("martingale")
    if mg:
        martingale(A, mg, fb, zav, fl_, -u_min('poutre'))

    PLAT.clear()
    PLAT.update(fb=fb, rb=rb, zav=zav, zar=zar, ly=ly, pa=p.get("piece_angle"), du=p.get("poutre_axe_u", 0.0))
    if "coffre" in cfg and not plateforme_seule:
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
            liens = [("av", p_av, pts_etrave(sgm)), ("ar", p_ar, pts_cadene(sgm))]
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
                if hb_.get("croises_avant"):
                    liens.append(("semelle_av_croise", s_av, pts_etrave(-sgm)))
                if hs_.get("croises_arriere"):              # variante : croisés AR dans le plan des semelles, vers la cadène opposée
                    liens.append(("semelle_ar_croise", s_ar, pts_cadene(-sgm)))
                if hs_.get("vers_martingale"):              # variante : de la semelle au pied du pilier de martingale
                    mg_ = p.get("martingale", {})
                    liens.append(("semelle_ar_martingale", s_ar, V(fb, 0, zav - mg_.get("pied_sous_axe_extremites", 170))))
            for tag, q0, q1 in liens:
                A.add(cq.Solid.makeCylinder(hb_["diam"] / 2, (q1 - q0).Length, q0, (q1 - q0).normalized()), name=f"hauban_coffre_{tag}_{nom}", color=inox)
            tc_ = hb_.get("tube_colliers")
            if tc_ and sgm > 0:                              # tube alu entre les colliers, à hauteur de leur centre, d'une joue à l'autre
                yj_ = cfg["coffre"]["largeur"] / 2; c0_ = V(cc.x, -yj_, cc.z)
                tube = cq.Solid.makeCylinder(tc_["diam"] / 2, 2 * yj_, c0_, V(0, 1, 0)).cut(cq.Solid.makeCylinder(tc_["diam"] / 2 - tc_["ep"], 2 * yj_, c0_, V(0, 1, 0)))
                A.add(tube, name="tube_colliers", color=cq.Color(0.70, 0.72, 0.75))
        rest, d = voile_restante(vo["contour"], a, enr.get(nom, 0))
        if rest:
            pts = [(m["x_pied"] + dx, m["z_pied"] + dz) for dx, dz in rest]
            voile = cq.Workplane("XZ", origin=(0, y, 0)).polyline(pts).close().extrude(0.5, both=True)
            A.add(voile, name=f"voile_{nom}", color=cq.Color(0.95, 0.93, 0.88))
        lv = vo["livarde"]
        s0 = f + u * lv["w_mat"]
        cu, cw = vo["contour"][1]                                    # point d'écoute voile pleine
        s1 = f + V(cu * math.cos(a) + cw * math.sin(a), 0, -cu * math.sin(a) + cw * math.cos(a))
        for sg, cote in ((1, "a"), (-1, "b")):
            mid = s0 + (s1 - s0) * 0.45 + V(0, sg * lv["ecart"], 0)
            bez = [s0 * (1 - t) ** 2 + mid * (2 * t * (1 - t)) + s1 * t ** 2
                   for t in [i / 10 for i in range(11)]]
            seg = cq.Compound.makeCompound([cyl(q0.toTuple(), q1.toTuple(), lv["diam"])
                                            for q0, q1 in zip(bez, bez[1:])])
            A.add(seg, name=f"livarde_{nom}_{cote}", color=cq.Color(0.45, 0.45, 0.45))
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
