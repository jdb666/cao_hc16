"""(JD 08/10) Résistance du banc à deux personnes : assise CP 9 okoumé (plaque de Kirchhoff orthotrope, éléments de Morley,
scikit-fem), âme des couples, basculement du banc vers l'intérieur autour de la queue du longeron (tenu par le laçage sous
la jambe extérieure des couples), dossier (joue). Comparaison banc d'avant (rive libre, couples évidés, jambe 23 x 9,
laçage 57 sous le pivot) et banc renforcé (lisse sous la rive, couples pleins, jambe doublée et descendue, Dyneema).
Charges : 100 kg par personne ; assis : 80 % du poids sur l'assise, x2 dynamique ; debout : un pied, x1,5.
Résistances du CP okoumé : flexion 40 MPa le long du fil des plis extérieurs, 22 en travers ; compression dans le plan 25.
python3 etudes/banc_resistance.py -> etudes/banc_resistance.json"""
import json, math, yaml
import numpy as np
from skfem import MeshTri, Basis, ElementTriMorley, BilinearForm, LinearForm, asm, condense, solve
from skfem.helpers import dd
c = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
b = c['coffre']['bancs']; acc = c['coffre'].get('accoudoirs')
X0 = b['x_debut']; XR = c['coffre']['face_ar_x'] + b['longueur']
X1 = XR - (acc['batterie']['larg'] + 2 * acc['jeu'] + 2 * acc['ep']) if acc else XR     # face avant de l'accoudoir
Y0, Y1 = b['y_int'], c['coffre']['largeur'] / 2 - c['coffre']['ep_flasque']
COUPLES = [x for x in b['couples_x'] if X0 < x < X1]
T = b['ep_assise']; EL, ET, NU, G = 9000.0, 450.0, 0.06, 550.0
FMX, FMY, FC = 40.0, 22.0, 25.0
def rigidites(t, npl=5):
    tp = t / npl; D11 = D22 = 0.0
    for i in range(npl):
        z0, z1 = -t / 2 + i * tp, -t / 2 + (i + 1) * tp; Ii = (z1 ** 3 - z0 ** 3) / 3
        if i % 2 == 0: D11 += EL * Ii; D22 += ET * Ii
        else: D11 += ET * Ii; D22 += EL * Ii
    return D11, D22, NU * D22, G * t ** 3 / 12
# ------------------------------------------------------------------ assise
def assise(lisse_h):
    D11, D22, D12, D66 = rigidites(T)
    xs = sorted(set(np.round(np.concatenate([np.linspace(X0, X1, 81), COUPLES, [2135, 2185, 2285, 2385, 2435, 2495, 2545, 2595, 2655, 2705]]), 2)))
    ys = sorted(set(np.round(np.concatenate([np.linspace(Y0, Y1, 25), [891.0, 900.0, 950.0, 1091.0]]), 2)))
    m = MeshTri.init_tensor(np.array(xs), np.array(ys)); ib = Basis(m, ElementTriMorley())
    @BilinearForm
    def plaque(u, v, w):
        U, W_ = dd(u), dd(v)
        return D11 * U[0, 0] * W_[0, 0] + D22 * U[1, 1] * W_[1, 1] + D12 * (U[0, 0] * W_[1, 1] + U[1, 1] * W_[0, 0]) + 4 * D66 * U[0, 1] * W_[0, 1]
    K = asm(plaque, ib)
    if lisse_h:                                                # lisse CP 9 sous la rive : bande raide de 20 mm le long de y_int
        EI = 5580.0 * (9 * lisse_h ** 3 / 12 + 9 * lisse_h * (lisse_h / 2 + T / 2) ** 2)
        @BilinearForm
        def raid(u, v, w):
            return (w.x[1] < Y0 + 20.0) * (EI / 20.0) * dd(u)[0, 0] * dd(v)[0, 0]
        K = K + asm(raid, ib)
    P = m.p; du = ib.nodal_dofs[0]
    sur = lambda fn: np.where(fn(P[0], P[1]))[0]
    lignes = {'C4': sur(lambda x, y: np.isclose(x, X0)), 'accoudoir': sur(lambda x, y: np.isclose(x, X1)), 'joue': sur(lambda x, y: np.isclose(y, Y1))}
    for cc in COUPLES:
        lignes[cc] = sur(lambda x, y, cc=cc: np.isclose(x, cc))
    fixe = np.unique(np.concatenate([du[n] for n in lignes.values()]))
    CAS = {'2 assis côte à côte': [(2135, 2435, 891, 1091, 1570.0), (2435, 2705, 891, 1091, 1570.0)],
           'assis sur le bord': [(2435, 2655, Y0, Y0 + 150, 1570.0)],
           'pied sur la rive, entre couples': [(2495, 2595, Y0, Y0 + 100, 1470.0)],
           "pied sur la rive, au droit d'un couple": [(2630, 2730, Y0, Y0 + 100, 1470.0)]}
    out = {}
    for nom, pats in CAS.items():
        @LinearForm
        def f(v, w, pats=pats):
            x, y = w.x; q = 0 * x
            for a0, a1, b0, b1, F_ in pats:
                q = q + F_ / ((a1 - a0) * (b1 - b0)) * ((x >= a0) & (x <= a1) & (y >= b0) & (y <= b1))
            return q * v
        F = asm(f, ib); u = solve(*condense(K, F, D=fixe)); r = K @ u - F
        H_ = dd(ib.interpolate(u)); wxx, wyy = H_[0, 0].mean(axis=1), H_[1, 1].mean(axis=1)
        sx = (6 * np.abs(D11 * wxx + D12 * wyy) / T ** 2).max(); sy = (6 * np.abs(D12 * wxx + D22 * wyy) / T ** 2).max()
        cpl = {}
        for cc in COUPLES:
            Fi, yi = -r[du[lignes[cc]]], P[1, lignes[cc]]
            cpl[cc] = dict(M_ame=float(np.sum(Fi[yi < 1005] * (1005 - yi[yi < 1005]))), M_bascule=float(np.sum(Fi * (1042 - yi))))
        out[nom] = dict(fleche=round(float(np.abs(u[du]).max()), 1), sx=round(float(sx), 1), SF=round(FMX / float(sx), 2), sy=round(float(sy), 1),
                        M_ame=round(max(v['M_ame'] for v in cpl.values()) / 1e3, 1), M_bascule=round(max(v['M_bascule'] for v in cpl.values()) / 1e3, 1))
    return out
def ame(M_Nm, h):                                              # âme CP 9 x h + assise collaborante (12 t + 9) : compression au bas de l'âme
    bf = 12 * T + 9; Af, zf, Aw, zw = bf * T, h + T / 2, 9 * h, h / 2
    zn = (Af * zf + Aw * zw) / (Af + Aw); I = bf * T ** 3 / 12 + Af * (zf - zn) ** 2 + 9 * h ** 3 / 12 + Aw * (zw - zn) ** 2
    return round(M_Nm * 1e3 / (I / zn), 1)
def bascule(M_Nm, bras, ep_j, larg_j, bras_j, k_lac):         # laçage sous la jambe : tension, contrainte dans la jambe, rotation du banc
    T_ = M_Nm * 1e3 / bras; s = T_ * bras_j / (ep_j * larg_j ** 2 / 6); th = M_Nm * 1e3 / (k_lac * bras ** 2)
    return dict(T_lacage=round(T_), s_jambe=round(s, 1), rotation_deg=round(math.degrees(th), 1), rive_mm=round((1042 - Y0) * th, 1))
zav, zar, fb, rb = c['plateforme']['poutre_av_z'], c['plateforme']['poutre_ar_z'], c['plateforme']['poutre_av_x'], c['plateforme']['poutre_ar_x']
za = zav + (zar - zav) * (2680 - fb) / (rb - fb)               # axe du longeron au couple du milieu
z_piv = za + 13                                                # queue du longeron (pivot du basculement)
jb = b.get('jambe') or {}
avant = assise(0); renf = assise((b.get('lisse_rive') or {}).get('h', 0))
k_poly, k_dyn = 520.0, 1040.0                                  # N/mm : laçage polyester (≈ Dyneema simple) / Dyneema 5 double, 2,3 m
res = dict(parametres=dict(assise=T, couples=COUPLES, x=[X0, X1], y=[Y0, Y1], lisse=b.get('lisse_rive'), jambe=jb, pivot_z=round(z_piv)),
           avant={}, renforce={})
for nom in avant:
    a_, r_ = avant[nom], renf[nom]
    res['avant'][nom] = dict(assise_SF=a_['SF'], fleche=a_['fleche'], ame_MPa=ame(a_['M_ame'], 55),
                            **bascule(a_['M_bascule'], z_piv - (za - b['couple_sous_axe'] - 3.5), 9, 23, 44, k_poly))
    res['renforce'][nom] = dict(assise_SF=r_['SF'], fleche=r_['fleche'], ame_MPa=ame(r_['M_ame'], b['hauteur'] - T),
                               **bascule(r_['M_bascule'], z_piv - (za - jb.get('sous_axe', 115) - 3.5), 9 + 2 * jb.get('joues', 9),
                                         jb.get('ext', 1162) - 1117, (za - 0) - (za - jb.get('sous_axe', 115)) - 0, k_dyn))
# dossier (joue CP 9 au-dessus de l'assise) : une personne qui s'adosse (500 N), voir scratch : contraintes faibles, flèche notable
res['dossier'] = dict(charge_N=500, SF_min=2.5, fleche_mm=[14, 47], note="solide mais souple : 1,4 à 4,7 cm en haut selon l'encastrement à l'assise")
json.dump(res, open('/home/claude/cao/etudes/banc_resistance.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
