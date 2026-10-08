"""Fiche technique (JD 06/10 soir) : volumes, poids estimés, charge utile et assiette, comparaison avec le HC16 d'origine.
Poids tirés du modèle (volumes des pièces) et du plan de découpe (CP), densités usuelles ; ce qui n'est pas dans le modèle
(voiles, mâts carbone, coques du HC16) est estimé et marqué comme tel.
python3 etudes/fiche_technique.py -> etudes/fiche_technique.json"""
import sys, math, json, re, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import yaml, cadquery as cq, hc16_rando as H
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union
V = cq.Vector
RHO = 1025.0
CP = 0.50e-6            # kg/mm3 : CP okoumé ≈ 500 kg/m3
ALU, INOX, CARB, PEHD, EPOX = 2.70e-6, 7.90e-6, 1.55e-6, 0.95e-6, 1.20e-6   # kg/mm3
STRAT = 0.6             # kg/m2 de pièce : époxy de saturation, joints congés et bandes de verre, peinture
c = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
VZ = json.load(open('/home/claude/cao/etudes/vol_zones.json'))      # python3 etudes/vol_zones.py hc16_rando.py v_pleine_0.yaml etudes/vol_zones.json
A = H.build(c)
D = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children}
vol = lambda n: D[n].Volume() if n in D else 0.0
cdg = lambda n: D[n].Center().x if n in D else None
noms = lambda p: [n for n in D if n.startswith(p)]

# ---------------- coffre et bancs : CP du plan de découpe
import os
J = json.load(open(os.environ.get('DECOUPE_JSON', '/home/claude/cao/plans/decoupe3.json')))   # pièces du plan de découpe (aires, épaisseurs)
GREEMENT = ('CO', 'JE', 'CE', 'SM', 'RP')
cof_cp = cof_aire = gr_cp = 0.0
detail_cp = {}
for p in J['pieces']:
    r = p['ref']
    m = p['aire'] * 1e6 * p['ep'] * p['qte'] * CP          # aire m2 (une face)
    if r.startswith(GREEMENT):
        gr_cp += m
    else:
        cof_cp += m; cof_aire += p['aire'] * p['qte'] / (p.get('plis') or 1)
        detail_cp[p['ep']] = detail_cp.get(p['ep'], 0) + m
cof_strat = STRAT * cof_aire
pyl = sum(vol(n) for n in noms('pylone_coffre')) * CARB           # tubes Ø 40 × 2, creux dans le modèle
cordage = 0.5                                                   # laçages Dyneema 5, brêlages
quinc = 1.0                                                     # charnières, vis, taquets, poignées, tourniquets des trappes
glis = sum(vol(n) for n in noms('glissiere_pehd')) * PEHD + sum(vol(n) for n in noms('glissiere_cale')) * EPOX   # (JD 08/10) garnitures PEHD et cales coulées
coffre_total = cof_cp + cof_strat + pyl + cordage + quinc + glis
# centre de gravité du coffre et des bancs : volumes du modèle
cg_parts = [n for n in D if n.startswith(('coffre_', 'joue_', 'banc_', 'caisson_', 'accoudoir_', 'couple_coffre', 'moteur_puits', 'moteur_tableau', 'batterie_cale', 'accroche_', 'glissiere_'))]
xg_coffre = sum(vol(n) * cdg(n) for n in cg_parts) / sum(vol(n) for n in cg_parts)

# ---------------- gréement Rando
D_H = c['coffre']['haubans']['diam']                                            # (JD 08/10) Ø 5
lg_h = sum(vol(n) for n in noms('hauban')) / (math.pi * (D_H / 2) ** 2) / 1000    # m de câble
KG_M_H = {4: 0.079, 5: 0.123, 6: 0.177}.get(D_H, 0.0049 * D_H ** 2)          # inox 1x19
gr = {
    'mâts carbone Ø 60 × 7,30 (2), renforts compris (estimé)': 2 * 6.5,
    'voiles 11,1 m² sur enrouleur (2, estimé)': 2 * 3.5,
    'livardes carbone Ø 30 × 2,84 (2)': 2 * math.pi * (15 ** 2 - 13.5 ** 2) * 2840 * CARB,
    'colliers CP collés stratifiés (2)': sum(vol(n) for n in noms('collier_pli')) * CP + 2 * 0.15
        + sum(vol(n) for n in noms('collier_chemise')) * PEHD
        + 2 * math.pi * (22.5 ** 2 - 20 ** 2) * 115 * ALU
        + sum(vol(n) for n in noms('collier_axe') + noms('collier_ferrure')) * INOX,
    'emplantures CP (2) : joues, cales, ergots, boulons': sum(vol(n) for n in noms('emplanture_joue') + noms('emplanture_cale')) * CP + 2 * 0.05
        + sum(vol(n) for n in noms('emplanture_ergot') + noms('emplanture_boulon')) * INOX,
    'semelles, renforts de pont et bourrage (2)': sum(vol(n) for n in ('semelle_babord', 'semelle_tribord', 'renfort_pont_babord', 'renfort_pont_tribord')) * CP
        + sum(vol(n) for n in ('bourrage_babord', 'bourrage_tribord')) * EPOX + 2 * 0.2,
    'tube alu Ø 50 × 2 des colliers': vol('tube_colliers') * ALU,
    f'haubans inox Ø {D_H} ({lg_h:.0f} m) et pontets': lg_h * KG_M_H + 0.6,
    'écoutes, poulies, taquets (estimé)': 2.0,
}
gr_total = sum(gr.values())
# CdG en x de chaque poste du gréement Rando, dans l'ordre de gr (JD 07/10 : vérification de l'assiette)
_qr = math.radians(c['mats'].get('quete_deg', 3)); _Lm = 7300.0
GR_X = [c['mats']['x_pied'] + _Lm / 2 * math.sin(_qr),        # mâts : milieu du mât, quête comprise
        3206.0,                                               # voiles : CV des contours, voiles pleines (aligné sur le HC16)
        2800.0,                                               # livardes en place, du mât au point d'écoute
        2003.0, c['mats']['x_pied'], c['mats']['x_pied'],     # colliers, emplantures, semelles et renforts
        2085.0,                                               # tube des colliers
        1600.0,                                               # haubans : vers les étraves, la poutre AV et l'arrière
        3700.0]                                               # écoutes vers la poutre AR
X_GR_R = sum(m * x for m, x in zip(gr.values(), GR_X)) / gr_total
hc16_greement = {'mât alu 8,07 m': 18.0, 'bôme': 3.0, 'grand-voile 13,77 m² et foc 5,12 m²': 9.0, 'étai, haubans, pattes d\'oie': 2.0, 'écoutes, poulies, chariot': 2.0}
hc16_gr = sum(hc16_greement.values())
_m = c['hc16_origine']['mat']; _qh = math.radians(_m['quete_deg'])
_xb = _m['x'] + (1295 - _m['z']) * math.tan(_qh)                 # vit-de-mulet de la bôme (z 1 295)
HC16_X = [_m['x'] + _m['longueur'] / 2 * math.sin(_qh),         # mât : milieu, quête 7,5°
          _xb + 2740 / 2,                                       # bôme : bordure 2 740
          3206.0,                                               # voiles : CV des contours (GV + foc)
          2000.0,                                               # étai, pattes d'oie, haubans
          3700.0]                                               # écoute de GV sur la poutre AR, écoutes de foc
X_GR_HC16 = sum(m * x for m, x in zip(hc16_greement.values(), HC16_X)) / hc16_gr
HC16 = 145.0                                                    # Hobie : bateau prêt à naviguer
plateforme = HC16 - hc16_gr

moteur = {'Haswing Protruar 2.0 (manuel)': 6.7}
if c['coffre'].get('batterie'):                                  # ancien état : batterie dans le coffre, dans son bac
    moteur.update({'batterie Dyness 24 V 100 Ah': c['coffre']['batterie'].get('masse', 19.3), 'bac de la batterie (estimé)': 3.0})
elif c['coffre'].get('accoudoirs'):                             # (JD 08/10) une batterie 24 V 50 Ah dans chaque accoudoir, sur l'arrière des bancs
    ac_ = c['coffre']['accoudoirs']; nb_b = len(ac_.get('cotes') or [1])
    moteur[f"batteries LiFePO4 24 V 50 Ah × {nb_b}, dans les accoudoirs"] = ac_['batterie']['masse'] * nb_b
else:                                                            # (JD 07/10) batterie 24 V 50 Ah dans le caisson du banc bâbord
    cbk_ = c['coffre']['batterie_banc']; nb_b = len(cbk_.get('cotes') or [1])
    moteur[f"batterie LiFePO4 24 V 50 Ah{' × ' + str(nb_b) if nb_b > 1 else ''}, dans le caisson du banc"] = cbk_['masse'] * nb_b
moteur['câbles 25 mm², coupe-circuit (estimé)'] = 1.5
moteur_total = sum(moteur.values())
ancre = 3.5
vide = plateforme + gr_total + coffre_total + moteur_total
vide_ancre = vide + ancre

# ---------------- hydrostatique (sections de la coque tous les 50)
P = H.build(c, plateforme_seule=True)
h = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in P.children}['coque_babord']
DX = 50.0
SEC = {}
for x in [25 + DX * i for i in range(102)]:
    s = h.intersect(cq.Solid.makeBox(1.0, 3000, 2000, V(x - 0.5, -500, -1000)))
    if s.Volume() < 1:
        continue
    vs, ts = s.tessellate(0.3, 0.2)
    SEC[x] = unary_union([p.buffer(0.01) for p in (Polygon([(vs[i].y, vs[i].z) for i in t]) for t in ts) if p.area > 1e-4])
def carene(dz, tau, xf):
    v = mx = 0.0
    for x, Pg in SEC.items():
        a = Pg.intersection(sbox(-1e4, -1e4, 1e4, dz + tau * (xf - x))).area
        v += a * DX; mx += a * DX * x
    return 2 * v / 1e9, (mx / v if v else 0)
V0, xB0 = carene(0, 0, 0)
D0 = RHO * V0
aw = mx = 0.0
for x, Pg in SEC.items():
    ch = Pg.intersection(sbox(-1e4, -0.5, 1e4, 0.5)).area
    aw += ch * DX; mx += ch * DX * x
xF0 = mx / aw
def equilibre(M, xG):
    """Enfoncement dz (mm, au droit de xF0) et assiette tau (rad, + sur le nez) pour une masse M (kg) de CdG xG (mm)."""
    dz, tau = (M - D0) / (RHO * 2 * aw / 1e6 / 1000), 0.0
    for _ in range(40):
        v, xb = carene(dz, tau, xF0)
        f1, f2 = RHO * v - M, xb - xG
        va, xba = carene(dz + 0.2, tau, xF0); vb, xbb = carene(dz, tau + 2e-5, xF0)
        J_ = [[RHO * (va - v) / 0.2, RHO * (vb - v) / 2e-5], [(xba - xb) / 0.2, (xbb - xb) / 2e-5]]
        det = J_[0][0] * J_[1][1] - J_[0][1] * J_[1][0]
        if abs(det) < 1e-12:
            print('jacobien nul', M, xG, dz, tau, v, xb); break
        ddz, dtau = (-f1 * J_[1][1] + f2 * J_[0][1]) / det, (-f2 * J_[0][0] + f1 * J_[1][0]) / det
        ddz = max(-30.0, min(30.0, ddz)); dtau = max(-0.02, min(0.02, dtau))     # pas amortis
        dz += ddz; tau += dtau
        if abs(ddz) < 0.01 and abs(dtau) < 1e-7:
            break
    return dz, tau
# point le plus bas du coffre (fond, puits) : garde au-dessus de l'eau calme
_pts = []
for n_ in [n for n in D if n.startswith(('coffre_', 'moteur_puits'))]:
    vs_, _ = D[n_].tessellate(1.0, 0.3); _pts += [(v.z, v.x) for v in vs_]
Z_COF, X_COF = min(_pts)
def etat(M, xG):
    dz, tau = equilibre(M, xG)
    hh = lambda x: dz + tau * (xF0 - x)
    return dict(M=round(M, 1), xG=round(xG), assiette=round(math.degrees(math.atan(tau)), 2), etrave=round(hh(0)), tableau=round(hh(5050)), x1250=round(hh(1250)),
                garde_coffre=round(Z_COF - hh(X_COF)))

# Référence : le HC16 d'origine avec 2 équipiers (160 kg) assis près de la poutre AV flotte à plat ; on en déduit le CdG de la plateforme nue
# (JD 06/10 soir : « on navigue assis près de la poutre avant » ; avant : équipage supposé à x 3 000, CdG du HC16 nu trop en avant)
X_MAT_HC16, X_MAT = 2070.0, c['mats']['x_pied']
EQ_X = 2300.0                                                   # équipage assis juste derrière la poutre AV (axe x 2 070)
x_moteur = c['coffre']['moteur']['vertical2']['x_arbre']
_bats = [n for n in D if re.match(r'^batterie(_babord|_tribord)?$', n)]
x_batt = sum(D[n].Center().x for n in _bats) / len(_bats) if _bats else 1550.0
M_h = plateforme + hc16_gr
dz_ = (M_h + 160 - D0) / (RHO * 2 * aw / 1e6 / 1000)
for _ in range(30):                                             # enfoncement à plat pour HC16 + 2 équipiers
    v_, xbl = carene(dz_, 0.0, xF0); r_ = RHO * v_ - (M_h + 160)
    if abs(r_) < 0.01: break
    v2_, _ = carene(dz_ + 0.5, 0.0, xF0); dz_ -= r_ / ((RHO * v2_ - RHO * v_) / 0.5)
x_plat = ((M_h + 160) * xbl - 160 * EQ_X - hc16_gr * X_GR_HC16) / plateforme
masses_h = [(plateforme, x_plat), (hc16_gr, X_GR_HC16)]
xg_h = sum(m * x for m, x in masses_h) / M_h
masses_r = [(plateforme, x_plat), (gr_total, X_GR_R), (coffre_total, xg_coffre), (6.7, x_moteur), (moteur_total - 6.7, x_batt)]
M_r = sum(m for m, _ in masses_r); xg_r = sum(m * x for m, x in masses_r) / M_r
DEPL_EU, DEPL_US = HC16 + 240, HC16 + 362
bb_ = [D[n].BoundingBox() for n in D if n.startswith('banc_') and ('assise' in n or 'caisson' in n)] or [D[n].BoundingBox() for n in D if n.startswith('banc_')]
xb0_, xb1_ = min(b.xmin for b in bb_), max(b.xmax for b in bb_)
X_BAG, X_BANC_AR = 1780.0, xb1_ - (xb1_ - xb0_) / 4           # milieu des coffres latéraux ; milieu de la moitié AR des bancs
def charge(base, xbase, eq=160.0, x_eq=EQ_X, bags=()):
    M = base + eq + sum(m for m, _ in bags)
    return M, (base * xbase + eq * x_eq + sum(m * x for m, x in bags)) / M
cas = {}
cas['HC16, 2 équipiers près de la poutre AV (référence)'] = etat(*charge(M_h, xg_h))
cas['HC16 au maxi CE : 3 équipiers (240 kg)'] = etat(*charge(M_h, xg_h, 240.0))
print('X_GR_HC16', round(X_GR_HC16), 'X_GR_R', round(X_GR_R), 'M_h', round(M_h, 1), 'xg_h', round(xg_h), 'x_plat', round(x_plat), 'M_r', round(M_r, 1), 'xg_r', round(xg_r), 'xg_coffre', round(xg_coffre),
      'x_moteur', round(x_moteur), 'x_batt', round(x_batt), 'bancs', round(xb0_), round(xb1_), 'coffre bas', round(Z_COF), round(X_COF), flush=True)
cas['Rando à vide'] = etat(M_r, xg_r)
cas['Rando, 2 équipiers, coffre vide'] = etat(*charge(M_r, xg_r))
cas['Rando, 2 équipiers + 30 kg au coffre'] = etat(*charge(M_r, xg_r, bags=[(30, X_BAG)]))
cas['Rando, 2 équipiers + 60 kg au coffre'] = etat(*charge(M_r, xg_r, bags=[(60, X_BAG)]))
bag_eu = DEPL_EU - M_r - 160
cas[f'Rando au déplacement maxi CE du HC16 : 2 équipiers + {bag_eu:.0f} kg dans le coffre'] = etat(*charge(M_r, xg_r, bags=[(bag_eu, X_BAG)]))
cas["Rando, 2 équipiers + 60 kg sous l'arrière des bancs"] = etat(*charge(M_r, xg_r, bags=[(60, X_BANC_AR)]))
def x_equipage_a_plat(base, xbase, bags=()):
    """Où asseoir les 2 équipiers (160 kg) pour flotter à plat."""
    M = base + 160 + sum(m for m, _ in bags); dz = (M - D0) / (RHO * 2 * aw / 1e6 / 1000)
    for _ in range(30):
        v, xb = carene(dz, 0.0, xF0); r = RHO * v - M
        if abs(r) < 0.01: break
        v2, _ = carene(dz + 0.5, 0.0, xF0); dz -= r / ((RHO * v2 - RHO * v) / 0.5)
    return (M * xb - base * xbase - sum(m * x for m, x in bags)) / 160
X_PLAT = {'coffre vide': round(x_equipage_a_plat(M_r, xg_r)),
          '30 kg au coffre': round(x_equipage_a_plat(M_r, xg_r, [(30, X_BAG)])),
          '60 kg au coffre': round(x_equipage_a_plat(M_r, xg_r, [(60, X_BAG)])),
          "60 kg sous l'arrière des bancs": round(x_equipage_a_plat(M_r, xg_r, [(60, X_BANC_AR)]))}
print('équipage à plat', X_PLAT, flush=True)
# bilan des moments (kg·m) par rapport au HC16 de référence, équipage au même endroit ; + = sur le nez
_ref = cas['HC16, 2 équipiers près de la poutre AV (référence)']
xF_ = xF0
BILAN = {'gréement HC16 enlevé': -hc16_gr * (xF_ - X_GR_HC16) / 1000, 'gréement Rando': gr_total * (xF_ - X_GR_R) / 1000,
         'coffre et bancs': coffre_total * (xF_ - xg_coffre) / 1000, 'moteur': 6.7 * (xF_ - x_moteur) / 1000,
         'batterie et câbles': (moteur_total - 6.7) * (xF_ - x_batt) / 1000}
BILAN = {k: round(v, 1) for k, v in BILAN.items()}
_M2, _x2 = charge(M_r, xg_r); _a = etat(_M2, _x2)['assiette']; _b = etat(_M2, _x2 + 1000 * 10 / _M2)['assiette']
MCT = round(10 / abs(_a - _b), 1)                              # kg·m par degré vers 375 kg
print('bilan', BILAN, 'total', round(sum(BILAN.values()), 1), 'MCT', MCT, flush=True)
out = dict(
    hc16=dict(poids=HC16, gréement=round(hc16_gr, 1), gréement_detail=hc16_greement, plateforme=round(plateforme, 1), capacite_ce=240, capacite_us=362, voilure=18.9),
    rando=dict(plateforme=round(plateforme, 1), gréement=round(gr_total, 1), gréement_detail={k: round(v, 2) for k, v in gr.items()},
               coffre_bancs=round(coffre_total, 1), coffre_detail=dict(cp=round(cof_cp, 1), cp_par_ep={k: round(v, 1) for k, v in sorted(detail_cp.items())},
                                                                     aire_m2=round(cof_aire, 2), stratification=round(cof_strat, 1), tubes=round(pyl, 2), cordages=cordage, quincaillerie=quinc,
                                                                     glissieres=round(glis, 2)),
               moteur=round(moteur_total, 1), moteur_detail=moteur, ancre=ancre, vide=round(vide, 1), vide_ancre=round(vide_ancre, 1),
               cp_greement=round(gr_cp, 2), xg_coffre=round(xg_coffre), xg_vide=round(xg_r), voilure=22.2),
    charge=dict(depl_ce=DEPL_EU, depl_us=DEPL_US, utile_ce=round(DEPL_EU - vide), utile_us=round(DEPL_US - vide), utile_ce_ancre=round(DEPL_EU - vide_ancre)),
    hydro=dict(D0=round(D0, 1), xB0=round(xB0), xF0=round(xF0), kg_mm=round(RHO * 2 * aw / 1e6 / 1000, 2), x_plateforme=round(x_plat), xg_hc16=round(xg_h)),
    cas=cas, x_equipage_a_plat=X_PLAT, bilan_moments=BILAN, mct=MCT,
    positions=dict(greement_hc16=round(X_GR_HC16), greement_rando=round(X_GR_R), equipage=EQ_X, bagages_coffre=X_BAG, bagages_bancs=round(X_BANC_AR), bancs=[round(xb0_), round(xb1_)], batterie=round(x_batt),
                   moteur=round(x_moteur), coffre_bas=[round(X_COF), round(Z_COF)]),
    volumes=dict(coffre_ext=round(VZ['ext_L']), coffre_int=round(VZ['int_L']), hors_centre=round(VZ['hors_centre_L']), par_cote=round(VZ['hors_centre_L'] / 2),
                 centre=round(VZ['centre_L']), coffre_ancre=round(VZ.get('coffre_ancre_L', 0)), caisson_banc=round(VZ.get('caisson_banc_L', 0), 1),
                 rangement=round(VZ.get('rangement_L', 0)), accoudoir=round(VZ.get('accoudoir_L', 0), 1),
                 bancs_par_cote=round(((1195.5 - 5 * 9) * 311 * 127 - 9 * 40 * 1150) / 1e6)),   # (08/10) moins les couples (5 × CP 9) et la lisse sous la rive
)
json.dump(out, open('/home/claude/cao/etudes/fiche_technique.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
