"""Pose du coffre sur la plateforme (JD 30/09) : descente verticale puis fin de pose en diagonale arrière-bas (accroches.pose),
coffre + bancs d'une pièce, moteur relevé. Contrôle des contacts avec la plateforme (poutre, longerons, pièces d'angle, trampoline,
martingale, semelles) à chaque pas. -> plateforme/pose_coffre.json"""
import sys, json, math, time, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import yaml, cadquery as cq, hc16_rando as H
t0 = time.time()
c = yaml.safe_load(open('/home/claude/cao/v_releve.yaml'))
A = H.build(c)
D = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children if ch.obj is not None}
FIXE = ('coque_', 'poutre_', 'longeron_', 'piece_angle', 'trampoline', 'martingale', 'safran_', 'barre_', 'pylone_av', 'pylone_ar', 'repere_', 'semelle_', 'renfort_pont', 'bourrage_')
APRES = ('mat_', 'hauban', 'voile', 'decor_yinyang_voile', 'lacage', 'brelage', 'tube_colliers', 'bras_tube')
import re
FIXE = ('poutre_av', 'longeron_', 'piece_angle_av', 'trampoline', 'martingale', 'semelle_', 'renfort_pont', 'bourrage_')   # coques : sous les semelles, hors d'atteinte
MOB = ('coffre_coque', 'couple_coffre_', 'moteur_puits', 'joue_', 'banc_', 'pylone_coffre', 'pylone_renfort', 'coffre_table', 'moteur_tableau', 'coffre_cloison', 'glissiere_')
fixes = {n: s for n, s in D.items() if n.startswith(FIXE)}
mob = {n: s for n, s in D.items() if n.startswith(MOB) and not n.startswith('glissiere_cale')}   # le reste est dans le coffre ou au-dessus ; la cale de la glissière est coulée après la pose
# zone utile : de l'avant des pylônes au 2e couple de banc (au-delà, joues et bancs glissent le long des longerons, parallèles)
ROI = cq.Solid.makeBox(2280 - 1640, 3000, 1500, cq.Vector(1640, -1500, 0))
def clip(n, s_):
    if n.startswith(('pylone', 'semelle', 'bourrage', 'renfort_pont', 'piece_angle', 'martingale')):
        return s_
    r_ = s_.intersect(ROI)
    return r_ if r_.Volume() > 1 else None
fixes = {n: clip(n, s_) for n, s_ in fixes.items()}; fixes = {n: s_ for n, s_ in fixes.items() if s_ is not None}
mob = {n: clip(n, s_) for n, s_ in mob.items()}; mob = {n: s_ for n, s_ in mob.items() if s_ is not None}
print(len(mob), 'pièces mobiles,', len(fixes), 'fixes', round(time.time() - t0), 's', flush=True)
po = c['coffre']['accroches_poutre']['pose']; a = math.radians(po['angle']); S = po['course']
dxS, dzS = S * math.cos(a), S * math.sin(a)
pas = [(-dxS, z) for z in (150, 100, 60, 40, 30)] + [(-dxS * t, dzS * t) for t in (1.0, 0.8, 0.6, 0.4, 0.25, 0.12, 0.05, 0.0)]
def bb(s): b = s.BoundingBox(); return (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)
BF = {n: bb(s) for n, s in fixes.items()}; BM = {n: bb(s) for n, s in mob.items()}
def proches(b1, b2, m):
    return not (b1[1] < b2[0] - m or b2[1] < b1[0] - m or b1[3] < b2[2] - m or b2[3] < b1[2] - m or b1[5] < b2[4] - m or b2[5] < b1[4] - m)
res = []
for dx, dz in pas:
    v = cq.Vector(dx, 0, dz); hits, jeux = [], {}
    for nm, sm in mob.items():
        b0 = BM[nm]; bm = (b0[0] + dx, b0[1] + dx, b0[2], b0[3], b0[4] + dz, b0[5] + dz)
        cand = [nf for nf in fixes if proches(bm, BF[nf], 12)]
        if not cand:
            continue
        smv = sm.translate(v)
        for nf in cand:
            if proches(bm, BF[nf], 0):
                vol = smv.intersect(fixes[nf]).Volume()
                if vol > 0.5:
                    hits.append((nm, nf, round(vol))); continue
            if nf.startswith('coque_'):
                continue                                   # coques : contact seulement (distance trop lente)
            dist = smv.distance(fixes[nf])
            if dist < 12:
                jeux[(nm, nf)] = round(dist, 1)
    top = sorted(jeux.items(), key=lambda kv: kv[1])[:6]
    print(f"dx {dx:6.1f} dz {dz:6.1f} | contacts {hits if hits else '-'} | jeux mini {[(a_, b_, j) for (a_, b_), j in top]}", flush=True)
    res.append(dict(dx=round(dx, 1), dz=round(dz, 1), contacts=hits, jeux=[[a_, b_, j] for (a_, b_), j in top]))
json.dump(dict(pose=po, pas=res), open('/home/claude/cao/plateforme/pose_coffre.json', 'w'), ensure_ascii=False)
print('t', round(time.time() - t0), 's')
