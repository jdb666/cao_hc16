"""(JD 12/10 : « tout faire en CP 6 mm ? ») Poids et surface de CP si toutes les pièces du plan de découpe passaient en CP 6 :
pièces d'un pli -> CP 6 ; pièces en plis collés -> même épaisseur totale en plis de CP 6 (colliers 70 -> 72, potences et planche du
moteur 40 -> 42, semelles 18 -> 18, joues d'emplanture 10 -> 12) ; le renfort de pont, cintré en place, reste en CP 4.
Rayons de cintrage du bordé de l'avant mesurés sur la maquette (angles entre facettes voisines de coffre_coque, < 8° : cintré).
python3 etudes/cp6_poids.py -> etudes/cp6_poids.json (après plans/decoupe3.py et plateforme/p3d.json)"""
import json, math
from collections import defaultdict
import numpy as np
J = json.load(open('/home/claude/cao/plans/decoupe3.json'))
KG = 0.5                                               # kg/m² par mm de CP okoumé (500 kg/m³)
GREE = ('CO', 'JE', 'CE', 'SM', 'RP')                  # pièces du gréement (hors coffre et bancs)
d_cof = d_gre = aire6 = 0.0; par_ep = defaultdict(float); aire_par_ep = defaultdict(float)
for p in J['pieces']:
    ep, q, a, pl, ref = p['ep'], p['qte'], p['aire'], (p['plis'] or 1), p['ref']
    aire_par_ep[ep] += a * q
    if ref == 'RP':
        continue
    if ref.startswith('CO'):                           # colliers : 7 plis de CP 10 -> 12 plis de CP 6 (70 -> 72), au prorata des plis
        dm = (72 - 70) / 70 * ep * KG * a * q; aire6 += a * q * 12 / 7
    elif pl > 1 or ref.startswith(('GQ', 'PL', 'CE', 'LC')):   # plis collés : qte compte déjà les plis
        n_p = q / pl if pl > 1 else q; tot = ep * pl; n6 = max(1, round(tot / 6))
        dm = (6 * n6 - tot) * KG * a * n_p; aire6 += a * n_p * n6
    elif ref == 'JE':                                  # joues d'emplanture : 2 × CP 6 au lieu d'un CP 10
        dm = (12 - 10) * KG * a * q; aire6 += a * q * 2
    else:
        dm = (6 - ep) * KG * a * q; aire6 += a * q
    par_ep[ep] += dm
    if ref.startswith(GREE): d_gre += dm
    else: d_cof += dm
aB = sum(p['aire'] * p['qte'] for p in J['pieces'] if p['ref'].startswith('B') and p['ep'] == 4)
# rayons de cintrage du bordé de l'avant (maillage de coffre_coque)
P3 = json.load(open('/home/claude/cao/plateforme/p3d.json'))
o = next(o for g in ('full', 'new') for o in P3[g] if isinstance(o, dict) and o['n'] == 'coffre_coque')
V = np.array(o['v'], float).reshape(-1, 3); T = np.array(o['t']).reshape(-1, 3)
uniq, inv = np.unique(np.round(V, 2), axis=0, return_inverse=True); Tw = inv.ravel()[T]; Vw = uniq
A, B, C = Vw[Tw[:, 0]], Vw[Tw[:, 1]], Vw[Tw[:, 2]]
N = np.cross(B - A, C - A); ar = np.linalg.norm(N, axis=1) / 2; N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
G = (A + B + C) / 3; ed = defaultdict(list)
for i, (a, b, c) in enumerate(Tw):
    for e in ((a, b), (b, c), (c, a)): ed[tuple(sorted(e))].append(i)
R = []
for (a, b), tr in ed.items():
    if len(tr) != 2: continue
    i, j = tr
    if ar[i] < 1 or ar[j] < 1: continue
    th = math.degrees(math.acos(np.clip(abs(np.dot(N[i], N[j])), -1, 1)))
    if th < 0.05 or th > 8.0: continue
    e = Vw[b] - Vw[a]; Le = np.linalg.norm(e); e = e / Le
    di = G[i] - Vw[a]; di -= np.dot(di, e) * e; dj = G[j] - Vw[a]; dj -= np.dot(dj, e) * e
    m = (G[i] + G[j]) / 2; nm = (N[i] + N[j]) / 2
    if m[0] < 1800 and nm[2] > -0.6 and nm[0] < 0.9 and Le > 20:
        R.append(((np.linalg.norm(di) + np.linalg.norm(dj)) / math.radians(th), m))
rayons = {}
for y0, y1 in ((200, 450), (450, 700), (700, 950), (950, 1112)):
    s = np.array([r for r, m in R if y0 <= abs(m[1]) < y1])
    if len(s): rayons[f'|y| {y0}-{y1}'] = dict(p5=round(float(np.percentile(s, 5))), mediane=round(float(np.median(s))))
out = dict(delta_coffre_bancs_kg=round(d_cof, 2), delta_greement_kg=round(d_gre, 2), delta_par_ep_kg={str(k): round(v, 2) for k, v in par_ep.items()},
           aire_cp6_m2=round(aire6, 2), plaques_2500x1220=round(aire6 / 3.05, 2), plaques_a_78pc=round(aire6 / (3.05 * 0.78), 2),
           aire_par_ep_m2={str(k): round(v, 2) for k, v in aire_par_ep.items()},
           borde_cintre_cp4_m2=round(aB, 2), delta_si_borde_reste_cp4_kg=round(-(6 - 4) * KG * aB, 2), rayons_borde_avant_mm=rayons,
           rayon_mini_a_froid_mm={'CP 4 (3 plis)': [254, 406], 'CP 6 (5 plis)': [508, 787], 'CP 9 (5 plis)': [914, 1372],
                                  'source': 'FAA AC 43.13-1B (0-45° / 90° du fil des plis extérieurs)'})
json.dump(out, open('/home/claude/cao/etudes/cp6_poids.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
