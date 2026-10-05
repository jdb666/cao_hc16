"""Variantes de la pente du fond du coffre (bouton de la page) : maillages des pièces qui en dépendent + cotes utiles."""
import sys, json, copy, time, yaml, math, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/cao')
import cadquery as cq
import hc16_rando as H
sys.path.insert(0, '/home/claude/cao/plateforme')
VAR = ('coffre_', 'joue_', 'chaise_joue', 'carter_', 'moteur_niche')
def maillages(A, tol=2.5):
    out = []
    for ch in A.children:
        if ch.obj is None or not ch.name.startswith(VAR):
            continue
        sh = ch.obj if not hasattr(ch.obj, 'val') else ch.obj.val()
        vs, ts = sh.tessellate(tol, 0.35)
        out.append(dict(n=ch.name, v=[round(c, 1) for p in vs for c in (p.x, p.y, p.z)], t=[i for tr in ts for i in tr]))
    return out
t0 = time.time()
cfg = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
H.build(cfg)                                   # fixe les globales (PLAT, POUTRE_AV, CFG_MAT…)
angles = [a / 2 for a in range(0, 61, 5)]      # 0 → 30° par 2,5°
res = dict(angles=angles, defaut=cfg['coffre']['fond_pente']['deg'], x0=cfg['coffre']['fond_pente']['x0'], infos={}, parts={})
for a in angles:
    k = copy.deepcopy(cfg['coffre']); k['fond_pente']['deg'] = a
    A = cq.Assembly(); H.coffre(A, k)
    g = k['_geom']; D = g['fond_pente']['montee']
    key = f"{a:g}"
    res['infos'][key] = dict(montee=round(D, 1), z_milieu=round(k['fond_z'] + D, 1), z_joues=round(k['fond_z_cotes'] + D, 1), volume=round(g['volume_L'], 1))
    res['parts'][key] = maillages(A)
    print(key, res['infos'][key], sum(len(o['t']) // 3 for o in res['parts'][key]), 'tri', round(time.time() - t0), 's', flush=True)
json.dump(res, open('/home/claude/cao/plateforme/pente.json', 'w'), separators=(',', ':'))
print('OK', round(time.time() - t0), 's')
