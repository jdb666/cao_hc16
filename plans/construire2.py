import json, math, numpy as np, ezdxf, os
from shapely.geometry import box
from shapely import affinity
import panneaux2 as P, imbrication as I

PARTS = {q['ref']: q for q in P.parts}
CHUTES = {'C4.2': 'chute de C4.1', 'C4.3': 'chute de C4.1', 'T1': 'chute de C5'}
def rings(g): return [list(g.exterior.coords)] + [list(r.coords) for r in g.interiors]

# ---------- imbrication ----------
planches = []
for ep, lettre in ((6, "6"), (9, "9")):
    items = [(q['ref'], n + 1, q['poly']) for q in P.parts if q['ep'] == ep and q['mat'] == "CP okoumé" and q['ref'] not in CHUTES for n in range(q['qte'])]
    I.SW = 2500
    pls, half = I.imbriquer_mieux(items, essais=8, graine=1)
    if half:
        half[0]['sw'] = 1250; pls = pls[:-1] + half
    for i, pl in enumerate(pls):
        pl['sw'] = pl.get('sw', 2500); pl['ep'] = ep
        pl['id'] = f"{lettre}-{'ABC'[i]}"
        pl['titre'] = f"CP okoumé {ep} mm" + (" — demi-panneau 1 250 × 1 220" if pl['sw'] == 1250 else "")
        pl['taux'] = sum(g.area for _, _, g, _ in pl['placed']) / (pl['sw'] * I.SH)
        planches.append(pl)
for pl in planches:
    print(pl['id'], pl['sw'], f"{pl['taux']*100:.0f} %", [r for r, *_ in pl['placed']])

# ---------- DXF ----------
os.makedirs("dxf2", exist_ok=True)
for f in os.listdir("dxf2"): os.remove(os.path.join("dxf2", f))
for pl in planches:
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM
    for lay, col in (("PANNEAU", 8), ("DECOUPE", 1), ("REPERES", 5)): doc.layers.add(lay, color=col)
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (pl['sw'], 0), (pl['sw'], I.SH), (0, I.SH)], close=True, dxfattribs={"layer": "PANNEAU"})
    for ref, n, g, rot in pl["placed"]:
        for r in rings(g): msp.add_lwpolyline([(round(x, 2), round(y, 2)) for x, y in r[:-1]], close=True, dxfattribs={"layer": "DECOUPE"})
        c = g.representative_point()
        msp.add_text(ref, height=30, dxfattribs={"layer": "REPERES"}).set_placement((c.x, c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(f"dxf2/planche_{pl['id']}.dxf")
doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM; msp = doc.modelspace(); x = 0
for ref in [r for r in ("M1", "M2.1", "M2.2", "S1") if r in PARTS]:
    g = affinity.translate(I.norm(PARTS[ref]['poly']), x, 0)
    for r in rings(g): msp.add_lwpolyline(r[:-1], close=True)
    msp.add_text(ref, height=20).set_placement((g.centroid.x, g.centroid.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    x += g.bounds[2] - g.bounds[0] + 30
doc.saveas("dxf2/chaise_massif.dxf")

# ---------- SVG ----------
def path_d(g, SH):
    return "".join("M" + " L".join(f"{x:.1f},{SH - y:.1f}" for x, y in r[:-1]) + " Z " for r in rings(g))
def svg_planche(pl):
    SW, SH = pl['sw'], I.SH
    out = [f'<svg viewBox="-60 -70 {SW + 120} {SH + 140}" class="planche{" demi" if SW < 2000 else ""}" role="img" aria-label="Planche {pl["id"]}">',
           f'<rect x="0" y="0" width="{SW}" height="{SH}" class="feuille"/>']
    for gx in range(500, SW, 500): out.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{SH}" class="grille"/>')
    for gy in range(500, SH, 500): out.append(f'<line x1="0" y1="{SH-gy}" x2="{SW}" y2="{SH-gy}" class="grille"/>')
    for ref, n, g, rot in pl["placed"]:
        out.append(f'<path d="{path_d(g, SH)}" class="piece p{ref[0]}" fill-rule="evenodd"><title>{ref} — {PARTS[ref]["nom"]}</title></path>')
        x0, y0, x1, y1 = g.bounds; c = g.representative_point()
        fs = 44 if min(x1 - x0, y1 - y0) > 150 else 28
        out.append(f'<text x="{c.x:.0f}" y="{SH - c.y:.0f}" class="rep" font-size="{fs}" text-anchor="middle" dominant-baseline="central">{ref}</text>')
        if min(x1 - x0, y1 - y0) > 160:
            out.append(f'<text x="{c.x:.0f}" y="{SH - c.y + fs * 0.95:.0f}" class="dim" font-size="24" text-anchor="middle" dominant-baseline="central">{x1-x0:.0f} × {y1-y0:.0f}</text>')
    out.append(f'<text x="0" y="-22" class="cote" font-size="30">{SW:,} mm'.replace(",", " ") + '</text>')
    out.append(f'<text x="{SW + 20}" y="{SH/2:.0f}" class="cote" font-size="30" writing-mode="vertical-rl" text-anchor="middle">1 220</text></svg>')
    return "".join(out)

# ---------- ordonnées ----------
def ord_haut(ref, pas=100):
    g = PARTS[ref]['poly']; rows = []
    for x in range(0, int(g.bounds[2]) + 1, pas):
        xs = min(max(x, 0.5), g.bounds[2] - 0.5)
        sec = g.intersection(box(xs - 0.1, -1, xs + 0.1, 3000))
        rows.append((x, round(sec.bounds[3]) if not sec.is_empty else 0))
    return rows
def ord_cloison(ref):
    g = PARTS[ref]['poly']; x1 = g.bounds[2]; rows = []
    for z in list(range(0, int(g.bounds[3]), 50)) + [int(g.bounds[3])]:
        zz = min(max(z, 0.5), g.bounds[3] - 0.5)
        sec = g.intersection(box(-1, zz - 0.1, 3000, zz + 0.1)); rows.append((z, round(x1 - sec.bounds[0])))
    return rows
def ord_borde(A2, B2):
    s = [0.0]
    for i in range(1, len(A2)): s.append(s[-1] + np.linalg.norm(A2[i] - A2[i - 1]))
    rows = []
    for sv in list(np.arange(0, s[-1], 50)) + [s[-1]]:
        i = max(0, min(len(A2) - 2, int(np.searchsorted(s, sv) - 1))); f = (sv - s[i]) / (s[i + 1] - s[i])
        a = A2[i] + f * (A2[i + 1] - A2[i]); b_ = B2[i] + f * (B2[i + 1] - B2[i])
        rows.append((round(a[0]), round(a[1]), round(b_[0]), round(b_[1])))
    return rows

# ---------- 3D ----------
Pk, am = P.k, P.am
WI, XA, XF, E, CPL, ZBC, ZBS = P.WI, P.XA, P.XF, P.E, P.CPL, P.ZBC, P.ZBS
def inst(O, U, V, N): return dict(O=list(map(float, O)), U=list(map(float, U)), V=list(map(float, V)), N=list(map(float, N)))
def mir(i): return {kk: [v[0], -v[1], v[2]] for kk, v in i.items()}
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
def polyjs(g): return [[[round(x, 1), round(y, 1)] for x, y in r[:-1]] for r in rings(g)]
objs = []
def obj(ref, ep, instances, grp, ex, mob=False, poly=None):
    objs.append(dict(ref=ref, poly=polyjs(poly if poly is not None else PARTS[ref]['poly']), ep=ep, inst=instances, grp=grp, ex=ex, mob=mob))
sl = P.WS; vy, vz = (WI - CPL) / sl, (ZBS - ZBC) / sl
obj("C1", 6, [inst((XF, -CPL, ZBC), X, Y, Z)], "6", (0, 0, -1))
fb = inst((XF, CPL, ZBC), X, (0, vy, vz), (0, -vz, vy))
obj("C2", 6, [fb], "6", (0, 0.3, -1)); obj("C3", 6, [mir(fb)], "6", (0, -0.3, -1))
obj("C4.1", 6, [inst((XA - E, 0, ZBC), Y, Z, X)], "6", (1, 0, 0))
obj("C4.2", 6, [inst((XA - E, 0, ZBC), Y, Z, X)], "c", (1.6, 0, 0.3))
obj("C4.3", 6, [inst((XA - E, 0, ZBC), Y, Z, X)], "c", (1.6, 0, 0.3))
NN, YM = P.NN, P.YM; en = NN['ep']
for i, yw in enumerate((YM - NN['demi_y'] - en, YM + NN['demi_y']), 1):
    ymid = yw + en / 2
    obj(f"N1.{i}", 6, [inst((NN['x0'] - en, yw, P.zb(ymid) + E), X, Z, Y)], "6", (0, 0, 0.9))
obj("N2", 6, [inst((NN['x0'] - en, P.ys_[0], P.zb(P.ys_[0]) + E), Y, Z, X)], "6", (-0.6, 0, 0.9))
for i, yc in enumerate(Pk['cloisons_y'], 1):
    obj(f"C9.{i}", 6, [inst((P.XCOL - P.AF + E, yc - 3, P.zb(yc) + E), X, Z, Y)], "6", (0, 0.4 * (1 if yc > 0 else -1), 0.2))
jo = inst((XF, WI, ZBS), X, Z, Y)
obj("J1", 9, [jo, mir(jo)], "9", (0, 1, 0))
b = P.b; XB0 = P.XB0
a1 = inst((XB0, b['y_int'], b['plan_z'] + b['hauteur'] - b['ep_assise']), X, Y, Z); obj("B1", 9, [a1, mir(a1)], "9", (0, 0.35, 1.1))
ci = inst((XB0, b['y_int'], b['plan_z']), X, Z, Y); obj("B2", 6, [ci, mir(ci)], "6", (0, 0.2, 0.5))
fi = inst((XB0 + 6, b['y_int'] + 6, b['plan_z']), X, Y, Z); obj("B3", 6, [fi, mir(fi)], "6", (0, 0.35, 0.3))
e1, e2 = inst((XB0, b['y_int'] + 6, b['plan_z']), Y, Z, X), inst((P.XR - 6, b['y_int'] + 6, b['plan_z']), Y, Z, X)
obj("B4", 6, [e1, e2, mir(e1), mir(e2)], "6", (0, 0.35, 0.5))
py = Pk['pylones']; x0p = P.m['x_pied'] - py['dx'] / 2; y0p = WI - py['dy']; z0 = P.z0
p1 = inst((x0p, y0p, z0), X, Z, Y); p2 = inst((x0p, WI - 9, z0), X, Z, Y)
obj("P1", 9, [p1, mir(p1)], "9", (0, 0.3, -1)); obj("P2", 9, [p2, mir(p2)], "9", (0, 0.3, -1))
p3a, p3b = inst((x0p, y0p + 9, z0), Y, Z, X), inst((x0p + py['dx'] - 9, y0p + 9, z0), Y, Z, X)
obj("P3", 9, [p3a, p3b, mir(p3a), mir(p3b)], "9", (0, 0.3, -1))
obj("M1", am['planche_ep'], [inst((P.XB1 - am['planche_ep'], YM - am['demi_larg'], P.ZBAS), Y, Z, X)], "m", (0.3, 0, -0.9))
ej = am['ep_joue']
obj("M2.1", ej, [inst((P.XAV, P.YM + P.YL, P.ZBAS), X, Z, Y)], "m", (0, 0.4, -0.9))
obj("M2.2", ej, [inst((P.XAV, P.YM - P.YL - ej, P.ZBAS), X, Z, Y)], "m", (0, -0.4, -0.9))
obj("M3", am['carter']['ep'], [inst((P.XAV, P.YM - P.YL, P.ZBAS), X, Y, Z)], "9", (0, 0, -1.2))
obj("M4", am['carter']['ep'], [inst((P.XAV, P.YM - P.YL, P.ZBAS + am['carter']['ep']), Y, Z, X)], "9", (-0.8, 0, -1.0))
bt = Pk['batterie']; x0b = bt['x_ar'] - bt['bac'][1]; zpl_b = P.zpl_b
if P.LI and not bt.get('appui_direct'): obj("S1", P.LI['h'], [inst((x0b, yl - P.LI['larg'] / 2, ZBC + E), X, Y, Z) for yl in P.LI['y']], "m", (0, 0, -0.5))
batt = dict(bac=[x0b, bt['x_ar'], P.y0b, P.y1b, zpl_b, zpl_b + bt['bac'][2]], cell=bt['cellule'], masse=bt['masse'])
# bordés (maillages)
tr = Pk['trappe']
def mesh(A3, B3, sg, trou=None, vlist=None):
    vs = sorted(set(list(np.linspace(0, 1, 13)) + (list(trou[1:]) if trou else [])))
    verts, tris, cap = [], [], []
    for i in range(len(A3)):
        for v in vs:
            p_ = A3[i] + v * (B3[i] - A3[i]); verts.append([round(p_[0], 1), round(sg * p_[1], 1), round(p_[2], 1)])
    nv = len(vs)
    for i in range(len(A3) - 1):
        for j in range(nv - 1):
            vm = (vs[j] + vs[j + 1]) / 2
            xm = ((A3[i][0] + A3[i + 1][0]) / 2) * (1 - vm) + ((B3[i][0] + B3[i + 1][0]) / 2) * vm
            q = [i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1]
            inside = trou and trou[0][0] <= xm <= trou[0][1] and trou[1] <= vm <= trou[2]
            (cap if inside else tris).extend([q[0], q[1], q[2], q[0], q[2], q[3]])
    return verts, tris, cap
TX = (tr['x0'], tr['x1'])
vc, tc, cc = mesh(P.A3c, P.B3c, 1, (TX, P.u0, P.u1))
vb, tb, cb = mesh(P.A3s, P.B3s, 1, (TX, P.INFO['v0'], P.INFO['v1']))
vt, tt, ct = mesh(P.A3s, P.B3s, -1, (TX, P.INFO['v0'], P.INFO['v1']))
meshes = [dict(ref="C5", v=vc, t=tc, grp="6", ex=(-0.4, 0, 1.0)), dict(ref="C6", v=vb, t=tb, grp="6", ex=(-0.4, 0.35, 0.9)),
          dict(ref="C7", v=vt, t=tt, grp="6", ex=(-0.4, -0.35, 0.9)),
          dict(ref="T1", v=vc, t=cc, grp="c", ex=(0, 0, 1.8)), dict(ref="", v=vb, t=cb, grp="c", ex=(0, 0, 1.8)), dict(ref="", v=vt, t=ct, grp="c", ex=(0, 0, 1.8))]
mo = Pk['moteur']
moteur = dict(mode='arriere', xs=am['x_arbre'], ym=YM, zsb=P.ZP + am['arbre_au_dessus'] - mo['arbre_l'], L=mo['arbre_l'], rd=mo['arbre_d'] / 2,
              tete=mo['tete'], nd=mo['nacelle_d'] / 2, nl=mo['nacelle_l'], hd=mo['helice_d'] / 2, xp=P.XP, zp=P.ZP,
              rot=am['rotation_tete_avant_bascule'], bride=[P.XB1, P.XB1 + am['bride_axe_derriere_planche'] + 30, YM - 40, YM + 40, P.ZC_ - 50, P.ZC_ + 40])
PR = P.H.PROFILS; _pp = P.p
def _anneaux_poutre(n=24):
    L = _pp['poutre_longueur'] / 2; out = []
    for i in range(n + 1):
        y = -L + 2 * L * i / n; zc = _pp['poutre_z'] + _pp.get('poutre_av_fleche', 0) * (1 - (y / L) ** 2)
        out.append([[round(_pp['poutre_av_x'] + u, 1), round(y, 1), round(zc + v, 1)] for u, v in PR['poutre']])
    return out
def _anneaux_longeron(sg, x0, x1):
    return [[[x, round(sg * (b['longeron_y'] - u), 1), round(_pp['poutre_z'] + v, 1)] for u, v in PR['longeron']] for x in (x0, x1)]
balayages = [_anneaux_poutre()] + [_anneaux_longeron(sg, _pp['poutre_av_x'], _pp['poutre_av_x'] + 1500) for sg in (1, -1)]
ctx = dict(balayages=balayages, poutre=dict(x=P.p['poutre_av_x'], z=P.p['poutre_z'], f=P.p['poutre_av_fleche'], r=P.p['poutre_diam'] / 2, L=P.p['poutre_longueur'] / 2),
           longerons=dict(y=b['longeron_y'], z=P.p['poutre_z'], x0=P.p['poutre_av_x'], r=P.p['longeron_diam'] / 2),
           mats=dict(x=P.m['x_pied'], y=P.m['y_axe'], z=P.m['z_pied'], q=P.m['quete_deg'], r=P.m['diam'] / 2, L=1300),
           pattes=None if P.ZTS >= P.ZC else dict(xc=P.XCOL, ecart=Pk['pattes_collier']['ecart'], larg=Pk['pattes_collier']['larg'], z0=P.ZT - Pk['pattes_collier']['recouvrement'],
                       z1=P.m['z_pied'] + P.m['collier_hauteur'] * math.cos(math.radians(P.m['quete_deg'])) + Pk['pattes_collier']['au_dessus_axe_collier'], wi=WI + 9))
import yaml, cadquery as cq
_c = yaml.safe_load(open('/home/claude/cao/v_releve.yaml')); _A = P.H.build(_c)
RZMIN = round(min(ch.obj.BoundingBox().zmin for ch in _A.children if ch.name.startswith(('moteur_arbre', 'moteur_tete', 'moteur_nacelle', 'moteur_helice'))))
VOL = round(_c['coffre']['_geom']['volume_L'])
nomen = []
for q in P.parts:
    x0, y0, x1, y1 = q['poly'].bounds
    ou = CHUTES.get(q['ref']) or next((pl['id'] for pl in planches if any(r == q['ref'] for r, *_ in pl['placed'])), "à débiter : " + q['mat'])
    nomen.append(dict(ref=q['ref'], nom=q['nom'], ep=q['ep'], qte=q['qte'], L=round(x1 - x0), H=round(y1 - y0), surf=round(q['poly'].area * q['qte'] / 1e6, 2), note=q['note'], planche=ou, mat=q['mat']))
data = dict(batt=batt, planches=[dict(id=pl['id'], titre=pl['titre'], ep=pl['ep'], taux=round(pl['taux'] * 100), svg=svg_planche(pl)) for pl in planches],
            nomen=nomen, objs=objs, meshes=meshes, ctx=ctx, moteur=moteur,
            ord=dict(joue=ord_haut('J1'), cloisons=[dict(ref=r, nom=PARTS[r]['nom'], rows=ord_cloison(r)) for r in ['C9.1', 'N1.1', 'N1.2']], borde=ord_borde(P.A2s, P.B2s)),
            info=dict(fond=[ZBC, ZBS, CPL], dessus=[P.ZT, round(P.ZTS), P.CPT],  trappe=[tr['x0'], tr['x1'], tr['y1']], releve_zmin=RZMIN, volume=VOL))
json.dump(data, open("data2.json", "w"), separators=(",", ":"))
print("data2.json", round(os.path.getsize('data2.json') / 1024), "ko")
