import json, math, numpy as np, ezdxf
from shapely.geometry import box, Polygon
from shapely import affinity
import panneaux as P

SW, SH, MARGE, JEU = 2500, 1220, 10, 8
PARTS = {q['ref']: q for q in P.parts}

def norm(poly, rot=0):
    g = affinity.rotate(poly, rot, origin=(0, 0)) if rot else poly
    x0, y0, _, _ = g.bounds
    return affinity.translate(g, -x0, -y0)

# (réf, n° d'exemplaire, x, y, rotation)
PLANCHES = [
  dict(id="6-A", ep=6, titre="CP okoumé 6 mm — planche A", items=[
    ("C4", 1, 10, 10, 0), ("C5", 1, 1192, 10, 0),
    ("B3", 1, 10, 858, 0), ("B3", 2, 1139, 858, 0),
    ("B4", 1, 10, 1089, 0), ("B4", 2, 330, 1089, 0), ("B4", 3, 650, 1089, 0), ("B4", 4, 970, 1089, 0),
    ("B2", 1, 1290, 1089, 0)]),
  dict(id="6-B", ep=6, titre="CP okoumé 6 mm — planche B", items=[
    ("C3", 1, 10, 10, 0), ("C1", 1, 10, 470, 90), ("C2", 1, 1145, 470, 90), ("B2", 2, 10, 1057, 0)]),
  dict(id="6-C", ep=6, titre="CP okoumé 6 mm — planche C", items=[
    ("C7.2", 1, 10, 10, 0), ("C7.1", 1, 585, 10, 0), ("C7.3", 1, 1160, 10, 0), ("C8.1", 1, 1735, 10, 0),
    ("C8.2", 1, 10, 458, 0), ("C8.3", 1, 558, 458, 0), ("C8.4", 1, 793, 458, 0)]),
  dict(id="9-A", ep=9, titre="CP okoumé 9 mm — planche A", items=[
    ("J1", 1, 10, 10, 0), ("J1", 2, 10, 380, 0), ("B1", 1, 10, 750, 0), ("B1", 2, 1151, 750, 0),
    ("P1", 1, 10, 1076, 90), ("P1", 2, 234, 1076, 90), ("P1", 3, 458, 1076, 90), ("P1", 4, 682, 1076, 90),
    ("P2", 1, 906, 1076, 90), ("P2", 2, 1133, 1076, 90), ("P2", 3, 1360, 1076, 90), ("P2", 4, 1587, 1076, 90),
    ("M3", 1, 1797, 10, 0), ("M4", 1, 1797, 245, 0)]),
]

# ---------- placement et contrôles ----------
problemes = []
for pl in PLANCHES:
    placed = []
    for ref, n, x, y, rot in pl["items"]:
        g = affinity.translate(norm(PARTS[ref]['poly'], rot), x, y)
        placed.append((ref, n, g, rot))
        if not box(MARGE - 0.5, MARGE - 0.5, SW - MARGE + 0.5, SH - MARGE + 0.5).contains(g):
            problemes.append(f"{pl['id']} {ref}#{n} sort de la planche {tuple(round(v) for v in g.bounds)}")
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            if placed[i][2].distance(placed[j][2]) < JEU:
                problemes.append(f"{pl['id']} {placed[i][0]} / {placed[j][0]} trop proches ({placed[i][2].distance(placed[j][2]):.1f})")
    pl["placed"] = placed
    pl["taux"] = sum(g.area for _, _, g, _ in placed) / (SW * SH)
# contrôle des quantités
cnt = {}
for pl in PLANCHES:
    for ref, n, *_ in pl["items"]:
        cnt[ref] = cnt.get(ref, 0) + 1
for q in P.parts:
    if q['ep'] in (6, 9) and q['ref'] != 'C6' and cnt.get(q['ref'], 0) != q['qte']:
        problemes.append(f"quantité {q['ref']} : {cnt.get(q['ref'],0)} placées / {q['qte']} demandées")
print("problèmes :", problemes or "aucun")
for pl in PLANCHES:
    print(pl["id"], f"utilisation {pl['taux']*100:.0f} %")

# ---------- DXF par planche ----------
def rings(g):
    return [list(g.exterior.coords)] + [list(r.coords) for r in g.interiors]
for pl in PLANCHES:
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM
    for lay, col in (("PANNEAU", 8), ("DECOUPE", 1), ("REPERES", 5)):
        doc.layers.add(lay, color=col)
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (SW, 0), (SW, SH), (0, SH)], close=True, dxfattribs={"layer": "PANNEAU"})
    for ref, n, g, rot in pl["placed"]:
        for r in rings(g):
            msp.add_lwpolyline([(round(x, 2), round(y, 2)) for x, y in r[:-1]], close=True, dxfattribs={"layer": "DECOUPE"})
        c = g.representative_point()
        msp.add_text(f"{ref}", height=30, dxfattribs={"layer": "REPERES"}).set_placement((c.x, c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(f"dxf/planche_{pl['id']}.dxf")
# pièces épaisses : un DXF à part
doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM; msp = doc.modelspace(); x = 0
for ref in ("M2.1", "M2.2", "M1"):
    g = affinity.translate(norm(PARTS[ref]['poly']), x, 0)
    for r in rings(g): msp.add_lwpolyline(r[:-1], close=True)
    msp.add_text(ref, height=25).set_placement((g.centroid.x, g.centroid.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    x += g.bounds[2] - g.bounds[0] + 30
doc.saveas("dxf/pieces_massif_CP25.dxf")

# ---------- SVG des planches ----------
def path_d(g):
    d = ""
    for r in rings(g):
        d += "M" + " L".join(f"{x:.1f},{SH - y:.1f}" for x, y in r[:-1]) + " Z "
    return d
def svg_planche(pl):
    out = [f'<svg viewBox="-60 -70 {SW + 120} {SH + 140}" class="planche" role="img" aria-label="{pl["titre"]}">']
    out.append(f'<rect x="0" y="0" width="{SW}" height="{SH}" class="feuille"/>')
    for gx in range(500, SW, 500):
        out.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{SH}" class="grille"/>')
    for gy in range(500, SH, 500):
        out.append(f'<line x1="0" y1="{SH-gy}" x2="{SW}" y2="{SH-gy}" class="grille"/>')
    for ref, n, g, rot in pl["placed"]:
        grp = ref.split('.')[0][0]
        out.append(f'<path d="{path_d(g)}" class="piece p{grp}" fill-rule="evenodd"><title>{ref} — {PARTS[ref]["nom"]}</title></path>')
        x0, y0, x1, y1 = g.bounds
        c = g.representative_point()
        fs = 44 if min(x1 - x0, y1 - y0) > 150 else 30
        out.append(f'<text x="{c.x:.0f}" y="{SH - c.y:.0f}" class="rep" font-size="{fs}" text-anchor="middle" dominant-baseline="central">{ref}</text>')
        if min(x1 - x0, y1 - y0) > 160:
            out.append(f'<text x="{c.x:.0f}" y="{SH - c.y + fs * 0.95:.0f}" class="dim" font-size="24" text-anchor="middle" dominant-baseline="central">{x1-x0:.0f} × {y1-y0:.0f}</text>')
    out.append(f'<text x="0" y="-22" class="cote" font-size="30">2 500 mm</text>')
    out.append(f'<text x="{SW + 20}" y="{SH/2:.0f}" class="cote" font-size="30" writing-mode="vertical-rl" text-anchor="middle">1 220</text>')
    out.append('</svg>')
    return "".join(out)

# ---------- ordonnées des pièces courbes ----------
def ordonnees_joue():
    g = PARTS['J1']['poly']; rows = []
    for x in range(0, int(g.bounds[2]) + 1, 100):
        xs = min(x, g.bounds[2] - 0.5) if x > 0 else 0.5
        sec = g.intersection(box(xs - 0.1, -1, xs + 0.1, 1000))
        rows.append((x, round(sec.bounds[3]) if not sec.is_empty else 0))
    rows.append((round(g.bounds[2]), 0))
    return rows
def ordonnees_cloison(ref):
    g = PARTS[ref]['poly']; x1 = g.bounds[2]; rows = []
    for z in list(range(0, int(g.bounds[3]), 50)) + [int(g.bounds[3])]:
        zz = min(max(z, 0.5), g.bounds[3] - 0.5)
        sec = g.intersection(box(-1, zz - 0.1, 2000, zz + 0.1))
        rows.append((z, round(x1 - sec.bounds[0])))
    return rows
def ordonnees_borde():
    A2, B2 = P.A2, P.B2; rows = []
    # abscisse curviligne le long du bord milieu, tous les 50 mm
    s = [0.0]
    for i in range(1, len(A2)): s.append(s[-1] + np.linalg.norm(A2[i] - A2[i - 1]))
    for sv in list(np.arange(0, s[-1], 50)) + [s[-1]]:
        i = max(0, min(len(A2) - 2, int(np.searchsorted(s, sv) - 1)))
        f = (sv - s[i]) / (s[i + 1] - s[i])
        a = A2[i] + f * (A2[i + 1] - A2[i]); b_ = B2[i] + f * (B2[i + 1] - B2[i])
        rows.append((round(a[0]), round(a[1]), round(b_[0]), round(b_[1])))
    return rows

# ---------- données 3D (pièces planes extrudées + bordés maillés) ----------
WI, XA, XF, E = P.WI, P.XA, P.XF, P.E
mo = P.k['moteur']['arriere']; nn = mo['niche']; ym = mo['y']
def inst(O, U, V, N): return dict(O=list(map(float, O)), U=list(map(float, U)), V=list(map(float, V)), N=list(map(float, N)))
def mir(i): return {k: [v[0], -v[1], v[2]] for k, v in i.items()}
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
def polyjs(g): return [[[round(x, 1), round(y, 1)] for x, y in r[:-1]] for r in rings(g)]
objs = []
def obj(ref, poly, ep, instances, grp, explode):
    objs.append(dict(ref=ref, poly=polyjs(poly), ep=ep, inst=instances, grp=grp, ex=explode))
sl = math.hypot(WI, P.ZBS - P.ZBC); vy, vz = WI / sl, (P.ZBS - P.ZBC) / sl
fb = inst((XF, 0, P.ZBC), X, (0, vy, vz), (0, -vz, vy))
obj("C1", PARTS['C1']['poly'], 6, [fb], "6", (0, 0.35, -1))
obj("C2", PARTS['C2']['poly'], 6, [mir(fb)], "6", (0, -0.35, -1))
obj("C3", PARTS['C3']['poly'], 6, [inst((XA - E, 0, P.ZBC), Y, Z, X)], "6", (1, 0, 0))
for ref, yc in zip(("C7.1", "C7.2", "C7.3"), P.k['cloisons_y']):
    obj(ref, PARTS[ref]['poly'], 6, [inst((P.XCOL - P.AF + E, yc - 3, P.zb(yc) + E), X, Z, Y)], "6", (0, yc / 1400, 0.15))
yw1, yw2 = ym - nn['demi_y'] - nn['ep'] / 2, ym + nn['demi_y'] + nn['ep'] / 2
obj("C8.1", PARTS['C8.1']['poly'], 6, [inst((nn['x0'] - nn['ep'], yw1 - 3, P.zb(yw1) + E), X, Z, Y)], "6", (0, 0, 0.4))
obj("C8.2", PARTS['C8.2']['poly'], 6, [inst((nn['x0'] - nn['ep'], yw2 - 3, P.zb(yw2) + E), X, Z, Y)], "6", (0, 0, 0.4))
ysn = np.linspace(ym - nn['demi_y'], ym + nn['demi_y'], 20)
obj("C8.3", PARTS['C8.3']['poly'], 6, [inst((nn['x0'] - nn['ep'], ym - nn['demi_y'], min(P.zb(y) + E for y in ysn)), Y, Z, X)], "6", (0, 0, 0.4))
zd = nn['z_haut'] + nn['ep'] / 2
xmin_d = min(max(P.x_at_z(zd, y), nn['x0'] - nn['ep']) for y in ysn)
obj("C8.4", PARTS['C8.4']['poly'], 6, [inst((xmin_d, ym - nn['demi_y'], zd - 3), X, Y, Z)], "6", (0, 0, 0.55))
jo = inst((XF, WI, P.ZBS), X, Z, Y)
obj("J1", PARTS['J1']['poly'], 9, [jo, mir(jo)], "9", (0, 1, 0))
b = P.b; XB0 = P.XB0
obj("B1", PARTS['B1']['poly'], 9, [inst((XB0, b['y_int'], b['plan_z'] + b['hauteur'] - b['ep_assise']), X, Y, Z)] + [mir(inst((XB0, b['y_int'], b['plan_z'] + b['hauteur'] - b['ep_assise']), X, Y, Z))], "9", (0, 0.35, 1.1))
ci = inst((XB0, b['y_int'], b['plan_z']), X, Z, Y)
obj("B2", PARTS['B2']['poly'], 6, [ci, mir(ci)], "6", (0, 0.2, 0.5))
fi = inst((XB0 + 6, b['y_int'] + 6, b['plan_z']), X, Y, Z)
obj("B3", PARTS['B3']['poly'], 6, [fi, mir(fi)], "6", (0, 0.35, 0.3))
e1, e2 = inst((XB0, b['y_int'] + 6, b['plan_z']), Y, Z, X), inst((P.XR - 6, b['y_int'] + 6, b['plan_z']), Y, Z, X)
obj("B4", PARTS['B4']['poly'], 6, [e1, e2, mir(e1), mir(e2)], "6", (0, 0.35, 0.5))
py = P.k['pylones']; z0 = P.INFO['h_pyl']
zp0 = P.zb(WI) - P.INFO['h_pyl'][1]
x0p = P.m['x_pied'] - py['dx'] / 2; y0p = WI - py['dy']
p1a, p1b = inst((x0p, y0p, zp0), X, Z, Y), inst((x0p, WI - 9, zp0), X, Z, Y)
obj("P1", PARTS['P1']['poly'], 9, [p1a, p1b, mir(p1a), mir(p1b)], "9", (0, 0.3, -1))
p2a, p2b = inst((x0p, y0p + 9, zp0), Y, Z, X), inst((x0p + py['dx'] - 9, y0p + 9, zp0), Y, Z, X)
obj("P2", PARTS['P2']['poly'], 9, [p2a, p2b, mir(p2a), mir(p2b)], "9", (0, 0.3, -1))
car = mo['carter']; zbas = mo['bride_axe_z'] - mo['bride_axe_sur_planche'] - mo['planche_h']
xb1 = mo['x_arbre'] - mo['bride_axe_devant_arbre'] - mo['bride_axe_derriere_planche']
obj("M2.1", PARTS['M2.1']['poly'], 25, [inst((car['x_av'], ym + mo['demi_passage'], zbas), X, Z, Y)], "m", (0, 0, -1.2))
obj("M2.2", PARTS['M2.2']['poly'], 25, [inst((car['x_av'], ym - mo['demi_passage'] - mo['ep_joue'], zbas), X, Z, Y)], "m", (0, 0, -1.2))
obj("M3", PARTS['M3']['poly'], 9, [inst((car['x_av'], ym - mo['demi_passage'], zbas), X, Y, Z)], "9", (0, 0, -1.5))
obj("M4", PARTS['M4']['poly'], 9, [inst((car['x_av'], ym - mo['demi_passage'], zbas + 9), Y, Z, X)], "9", (0, 0, -1.2))
obj("M1", PARTS['M1']['poly'], 40, [inst((xb1 - mo['planche_ep'], ym - mo['demi_larg'], zbas), Y, Z, X)], "m", (0, 0, -1.2))
# bordés : maillage paramétrique (ligne i du profil × fraction v de la largeur)
tr = P.k['trappe']; v0, v1 = abs(tr['y1']) / WI, abs(tr['y0']) / WI
def bord_mesh(sg, trou):
    xs = [P.A3[i][0] for i in range(len(P.A3))]
    vs = sorted(set(list(np.linspace(0, 1, 23)) + ([v0, v1] if trou else [])))
    verts, tris, capv, capt = [], [], [], []
    for i in range(len(P.A3)):
        for v in vs:
            p = P.A3[i] + v * (P.B3[i] - P.A3[i]); verts.append([round(p[0], 1), round(sg * p[1], 1), round(p[2], 1)])
    nv = len(vs)
    for i in range(len(P.A3) - 1):
        xm = (xs[i] + xs[i + 1]) / 2
        for j in range(nv - 1):
            vm = (vs[j] + vs[j + 1]) / 2
            q = [i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1]
            inside = trou and tr['x0'] <= xm <= tr['x1'] and v0 <= vm <= v1
            (capt if inside else tris).extend([q[0], q[1], q[2], q[0], q[2], q[3]])
    return verts, tris, capt
vb, tb, _ = bord_mesh(1, False)
vt, tt, tc = bord_mesh(-1, True)
meshes = [dict(ref="C4", v=vb, t=tb, grp="6", ex=(-0.5, 0.35, 0.9)), dict(ref="C5", v=vt, t=tt, grp="6", ex=(-0.5, -0.35, 0.9)),
          dict(ref="C6", v=vt, t=tc, grp="c", ex=(-0.5, -0.35, 1.7))]
# contexte (non découpé)
ctx = dict(poutre=dict(x=P.p['poutre_av_x'], z=P.p['poutre_z'], f=P.p['poutre_av_fleche'], r=P.p['poutre_diam'] / 2, L=P.p['poutre_longueur'] / 2),
           longerons=dict(y=P.b['longeron_y'], z=P.p['poutre_z'], x0=P.p['poutre_av_x'], x1=P.p['poutre_ar_x'], r=P.p['longeron_diam'] / 2),
           mats=dict(x=P.m['x_pied'], y=P.m['y_axe'], z=P.m['z_pied'], q=P.m['quete_deg'], r=P.m['diam'] / 2, L=1300),
           pattes=dict(xc=P.XCOL, ecart=P.k['pattes_collier']['ecart'], larg=P.k['pattes_collier']['larg'], z0=P.ZT - P.k['pattes_collier']['recouvrement'],
                       z1=P.m['z_pied'] + P.m['collier_hauteur'] * math.cos(math.radians(P.m['quete_deg'])) + P.k['pattes_collier']['au_dessus_axe_collier'], wi=WI + 9))

# ---------- nomenclature ----------
nomen = []
for q in P.parts:
    x0, y0, x1, y1 = q['poly'].bounds
    ou = next((pl['id'] for pl in PLANCHES if any(r == q['ref'] for r, *_ in pl['items'])), "chute de C5" if q['ref'] == 'C6' else "chute CP 25 / massif")
    nomen.append(dict(ref=q['ref'], nom=q['nom'], ep=q['ep'], qte=q['qte'], L=round(x1 - x0), H=round(y1 - y0),
                      surf=round(q['poly'].area * q['qte'] / 1e6, 2), note=q['note'], planche=ou))
data = dict(planches=[dict(id=pl['id'], titre=pl['titre'], ep=pl['ep'], taux=round(pl['taux'] * 100), svg=svg_planche(pl)) for pl in PLANCHES],
            nomen=nomen, objs=objs, meshes=meshes, ctx=ctx,
            ord=dict(joue=ordonnees_joue(), cloison0=ordonnees_cloison('C7.2'), cloison650=ordonnees_cloison('C7.1'), borde=ordonnees_borde()),
            info=dict(dev_err=P.INFO['dev_err']))
json.dump(data, open("data.json", "w"), separators=(",", ":"))
print("data.json", round(len(open('data.json').read()) / 1024), "ko")
