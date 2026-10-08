"""(JD 08/10) Efforts sur les colliers et le tube : prétension des haubans + réaction d'étambrai du mât sous voile.
Modèle linéaire à 2 nœuds (les colliers), libres en x et y ; le tube des colliers repose dans la glissière du sabot (z tenu).
Haubans inox 1x19 (diamètre de cotes.yaml), ne travaillant qu'en traction ; tube alu Ø 50 x 2.
Sorties : effort vertical sur chaque glissière, tensions des haubans, effort dans le tube, moment de tangage des colliers
autour du tube (repris par le mât dans l'alésage), contraintes de la glissière.
python3 etudes/efforts_colliers.py -> etudes/efforts_colliers.json"""
import sys, json, math, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import numpy as np, yaml, cadquery as cq, hc16_rando as H
c = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
A = H.build(c)
D = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children if ch.obj is not None}
DH = c['coffre']['haubans']['diam']
MBL = {4: 12.6e3, 5: 19.5e3, 6: 28.0e3}.get(DH, 0.78 * DH ** 2 * 1000)      # N, inox 1x19
EA_c = 120e3 * 0.75 * math.pi * DH ** 2 / 4                                 # N : 1x19, section métallique ≈ 75 %
tc = c['coffre']['haubans']['tube_colliers']
A_t = math.pi * ((tc['diam'] / 2) ** 2 - (tc['diam'] / 2 - tc['ep']) ** 2); I_t = math.pi / 64 * (tc['diam'] ** 4 - (tc['diam'] - 2 * tc['ep']) ** 4)
EA_t = 69e3 * A_t
co = c['mats']['collier']; yt = c['mats']['y_axe'] - co.get('demi_y_int', co['demi_y']) - co['tourillon'].get('jeu_tube', 3)
L_t = 2 * yt
P_cr = math.pi ** 2 * 69e3 * I_t / L_t ** 2
def bouts(n):
    cs = [e for e in D[n].Edges() if e.geomType() == 'CIRCLE']
    pts = sorted({(round(e.Center().x, 2), round(e.Center().y, 2), round(e.Center().z, 2)) for e in cs})
    a, b = np.array(pts[0]), np.array(pts[-1])
    return (a, b) if a[2] > b[2] else (b, a)                          # (collier, ancrage)
NOMS = {'av': 'hauban_coffre_av_{}', 'avc': 'hauban_coffre_av_croise_{}', 'ar': 'hauban_coffre_ar_{}', 'pou': 'hauban_coffre_collier_poutre_{}'}
membres = []
for cote, nd in (('babord', 0), ('tribord', 1)):
    for k, f in NOMS.items():
        att, anc = bouts(f.format(cote)); d = anc - att; L = float(np.linalg.norm(d))
        membres.append((f'{k}_{cote}', nd, att, d / L, L))
# ---- voile et réaction d'étambrai
cont = c['voile']['contour']
def aire_cdg(p):
    A_ = cx = cy = 0
    for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]):
        k_ = x0 * y1 - x1 * y0; A_ += k_; cx += (x0 + x1) * k_; cy += (y0 + y1) * k_
    A_ /= 2; return abs(A_), (cx / (6 * A_), cy / (6 * A_))
S, (uc, wc) = aire_cdg(cont)
h_emp = H.hauteur_emplanture(c['mats']['emplanture'])
h_c = c['mats']['_collier']['hauteur'] - h_emp
z_ce = c['mats']['z_pied'] + h_emp + wc * math.cos(math.radians(c['mats']['quete_deg']))
try:
    m_vide = json.load(open('/home/claude/cao/etudes/fiche_technique.json'))['rando']['vide']
except Exception:
    m_vide = 211.5
m_bat, m_eq, y_eq = m_vide + 20, 160, 955                              # bateau à vide (+ 20 kg d'affaires), équipage au vent sur le banc
RM = 9.81 * (m_bat * 1.0 + m_eq * (1.0 + y_eq / 1000))                # une coque décolle
bras = (z_ce + 150) / 1000
F = RM / bras / 2
R = F * wc / h_c
def rig(Rvec, T0):
    actif = {m[0]: True for m in membres}; kt = EA_t / L_t
    for _ in range(30):
        K = np.zeros((4, 4)); f = np.array([Rvec[0][0], Rvec[0][1], Rvec[1][0], Rvec[1][1]], float)
        for nom, nd, att, u, L in membres:
            if not actif[nom]: continue
            k = EA_c / L; uh = u[:2]; i = slice(2 * nd, 2 * nd + 2)
            K[i, i] += k * np.outer(uh, uh); f[i] += T0[nom] * uh
        K[1, 1] += kt; K[3, 3] += kt; K[1, 3] -= kt; K[3, 1] -= kt
        f[1] += -T0['tube']; f[3] += T0['tube']
        d = np.linalg.solve(K, f)
        chg = False; out = {}
        for nom, nd, att, u, L in membres:
            T = T0[nom] - EA_c / L * np.dot(u[:2], d[2 * nd:2 * nd + 2])
            if actif[nom] and T < -1e-6: actif[nom] = False; chg = True
            elif not actif[nom] and T > 1e-6: actif[nom] = True; chg = True
            out[nom] = T if actif[nom] else 0.0
        if not chg: break
    V = [0.0, 0.0]; M = [0.0, 0.0]
    axe = np.array([c['mats']['_collier']['tube'][0], 0.0, c['mats']['_collier']['tube'][1]])
    for nom, nd, att, u, L in membres:
        Fv = out[nom] * u; V[nd] += -Fv[2]
        r = att - axe; M[nd] += (r[2] * Fv[0] - r[0] * Fv[2]) / 1000              # N·m autour de l'axe du tube
    out['tube'] = T0['tube'] + kt * (d[1] - d[3])
    return out, V, M
def pretension(T):
    T0 = {}
    for cote in ('babord', 'tribord'):
        m = {k: next(mm for mm in membres if mm[0] == f'{k}_{cote}') for k in NOMS}
        for k in ('av', 'avc', 'pou'): T0[f'{k}_{cote}'] = T
        T0[f'ar_{cote}'] = -sum(T * m[k][3][0] for k in ('av', 'avc', 'pou')) / m['ar'][3][0]
    m = {k: next(mm for mm in membres if mm[0] == f'{k}_babord') for k in NOMS}
    T0['tube'] = sum(T0[f'{k}_babord'] * m[k][3][1] for k in m)
    return T0
CAS = []
for Tp in (300, 500):
    T0 = pretension(Tp)
    o, V, M = rig([(0, 0), (0, 0)], T0)
    CAS.append(dict(cas=f'réglage {Tp} N', V=[round(v) for v in V], M=[round(m) for m in M], Tmax=round(max(v for k, v in o.items() if k != 'tube')), tube=round(o['tube'])))
    for ang in (90, 60, 30, 0, -30):
        a = math.radians(ang)
        for fd in (1.0, 1.5):
            Rv = (-R * math.cos(a) * fd, -R * math.sin(a) * fd)
            o, V, M = rig([Rv, Rv], T0)
            CAS.append(dict(cas=f'réglage {Tp} N, poussée {ang}° x{fd}', V=[round(v) for v in V], M=[round(m) for m in M],
                            Tmax=round(max(v for k, v in o.items() if k != 'tube')), tube=round(o['tube']),
                            mous=[k for k, v in o.items() if k != 'tube' and v <= 0]))
Vmax1 = max(max(cc['V']) for cc in CAS if 'x1.0' in cc['cas']); Vmax15 = max(max(cc['V']) for cc in CAS if 'x1.5' in cc['cas'])
Tmax1 = max(cc['Tmax'] for cc in CAS if 'x1.0' in cc['cas']); Tmax15 = max(cc['Tmax'] for cc in CAS if 'x1.5' in cc['cas'])
Mmax1 = max(max(abs(m) for m in cc['M']) for cc in CAS if 'x1.0' in cc['cas'])
Vreg = [max(cc['V']) for cc in CAS if cc['cas'].startswith('réglage') and 'poussée' not in cc['cas']]
Mreg = [max(abs(m) for m in cc['M']) for cc in CAS if cc['cas'].startswith('réglage') and 'poussée' not in cc['cas']]
# ---- glissière : contraintes à Vmax15
gl = c['coffre']['glissiere_collier']; x0g, x1g = gl['x']; yi = gl['y_int']; yb = gl['berceau']['y_fin']
po = gl['poteau']; xp0, xp1 = po['x']; ep = po.get('ep', 9)
wi = c['coffre']['largeur'] / 2 - c['coffre']['ep_flasque']
A_pot = (2 * (wi - yi) + (xp1 - xp0 - 2 * ep)) * ep                  # trois parois CP 9 (la joue en plus, non comptée)
A_pehd = tc['diam'] * 0.6 * (yb - yi)                                  # contact sur ≈ 60 % du diamètre projeté
TOUR = co['tourillon']; d_t = TOUR['d']; e_t = 4.0
W_t = math.pi / 32 * (d_t ** 4 - (d_t - 2 * e_t) ** 4) / d_t
M_t = Vmax15 * 25.0                                                    # porte-à-faux du tourillon ≈ 25, du bout du tube au milieu de sa prise dans le collier
res = dict(
    hauban=dict(diam=DH, MBL=MBL, EA=round(EA_c)), tube=dict(EA=round(EA_t), L=L_t, P_cr=round(P_cr)),
    voile=dict(S=round(S / 1e6, 2), w_cv=round(wc), h_collier=round(h_c), z_cv=round(z_ce), RM=round(RM), F_par_voile=round(F), R_etambrai=round(R)),
    cas=CAS,
    synthese=dict(V_reglage=[min(Vreg), max(Vreg)], V_max=round(Vmax1), V_max_15=round(Vmax15), T_max=round(Tmax1), T_max_15=round(Tmax15),
                  SF_hauban=round(MBL / Tmax1, 2), SF_hauban_15=round(MBL / Tmax15, 2), tube_max=max(abs(cc['tube']) for cc in CAS), SF_tube=round(P_cr / max(abs(cc['tube']) for cc in CAS), 1),
                  M_tangage_reglage=[min(Mreg), max(Mreg)], M_tangage_max=round(Mmax1), F_bords_alesage_max=round(Mmax1 * 1000 / co['ep'])),
    glissiere=dict(p_pehd=round(Vmax15 / A_pehd, 1), s_poteau=round(Vmax15 / A_pot, 1), s_assise=round(Vmax15 / A_pot, 1),
                   s_tourillon=round(M_t / W_t, 1), p_piece_angle=round(Vmax15 / ((xp1 - xp0) * (wi + 9 - yi)), 1)),
)
json.dump(res, open('/home/claude/cao/etudes/efforts_colliers.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'cas'}, ensure_ascii=False, indent=1))
