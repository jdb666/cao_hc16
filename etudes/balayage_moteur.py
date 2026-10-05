"""Balayage rapide de la bascule avant2 : un seul build à 0°, pièces mobiles tournées autour de l'axe de la bride."""
import sys, yaml, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/claude/cao')
import cadquery as cq, hc16_rando as H
V = cq.Vector
cfgf = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/cao/v_pleine_0.yaml'
step = int(sys.argv[2]) if len(sys.argv) > 2 else 5
c = yaml.safe_load(open(cfgf)); c['coffre']['moteur']['avant2']['bascule'] = 0
A = H.build(c); d = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children}
MOB = ('moteur_arbre', 'moteur_tete', 'moteur_nacelle', 'moteur_helice', 'moteur_bride')
xp, ym, zp = c['coffre']['_moteur']['pivot']
oth = [n for n in d if n not in MOB and not n.startswith(('voile', 'livarde', 'mat_', 'repere', 'safran'))]
def cat(n):
    if n.startswith('hauban'): return 'haubans'
    if n.startswith(('coffre_', 'moteur_puits', 'joue_', 'coffre')): return 'coffre'
    if n in ('moteur_tableau', 'moteur_etrier'): return 'fixe'
    if n.startswith(('poutre', 'martingale', 'accroche', 'machoire', 'piece_angle')): return 'poutre'
    if n.startswith('trampoline'): return 'trampoline'
    if n.startswith('batterie'): return 'batterie'
    return 'autre'
BB = {n: d[n].BoundingBox() for n in oth}
res = []
for ang in range(0, 91, step):
    mv = {n: (d[n].rotate(V(xp, ym, zp), V(xp, ym + 1, zp), ang) if ang else d[n]) for n in MOB}
    hits, best = [], {}
    for a, sa in mv.items():
        ba = sa.BoundingBox()
        for b in oth:
            bb = BB[b]; m = 250
            if ba.xmax + m < bb.xmin or bb.xmax + m < ba.xmin or ba.ymax + m < bb.ymin or bb.ymax + m < ba.ymin or ba.zmax + m < bb.zmin or bb.zmax + m < ba.zmin: continue
            if a == 'moteur_bride' and b in ('moteur_etrier', 'moteur_tableau'): continue   # la bride tourne dans l'étrier
            v = sa.intersect(d[b]).Volume()
            if v > 0.5:
                ib = sa.intersect(d[b]).BoundingBox()
                hits.append((a, b, round(v), [round(q) for q in (ib.xmin, ib.xmax, ib.ymin, ib.ymax, ib.zmin, ib.zmax)]))
                dist = 0.0
            else:
                dist = sa.distance(d[b])
            k = cat(b)
            if k not in best or dist < best[k][0]: best[k] = (round(dist, 1), a, b)
    bbs = [s.BoundingBox() for s in mv.values()]
    r = dict(a=ang, xmin=round(min(b.xmin for b in bbs)), xmax=round(max(b.xmax for b in bbs)), zmin=round(min(b.zmin for b in bbs)),
             zmax=round(max(b.zmax for b in bbs)), hits=hits, jeux=best)
    res.append(r)
    print(f"{ang:3d}° x {r['xmin']}–{r['xmax']} z {r['zmin']}–{r['zmax']} | contacts {hits or '-'} | " + ' '.join(f"{k}:{v[0]}({v[1][7:]}/{v[2]})" for k, v in sorted(best.items())), flush=True)
json.dump(res, open('/home/claude/cao/plateforme/balayage.json', 'w'))
