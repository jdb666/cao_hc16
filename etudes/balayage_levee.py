"""Balayage du relevage vertical (mode vertical2) : un seul build moteur en marche, pièces mobiles montées de 0 à levee_max.
Donne pour chaque levée les contacts et le jeu mini par famille de pièces ; vérifie aussi la sortie verticale du bac de batterie.
Usage : python balayage_levee.py [cotes.yaml] [pas_mm]  -> plateforme/balayage_levee.json"""
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import yaml, cadquery as cq, hc16_rando as H
V = cq.Vector
cfgf = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/cao/v_pleine_0.yaml'
pas = float(sys.argv[2]) if len(sys.argv) > 2 else 25
c = yaml.safe_load(open(cfgf)); v2 = c['coffre']['moteur']['vertical2']; v2['levee'] = 0
A = H.build(c); d = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children}
MOB = [n for n in ('moteur_arbre', 'moteur_tete', 'moteur_barre', 'moteur_nacelle', 'moteur_helice', 'moteur_aileron') if n in d]
LM = v2['levee_max']
oth = [n for n in d if n not in MOB and not n.startswith(('voile', 'livarde', 'mat_', 'repere', 'safran', 'coque_'))]
def cat(n):
    if n.startswith('hauban'): return 'haubans'
    if n.startswith(('coffre_', 'moteur_puits', 'joue_', 'couple_coffre')): return 'coffre'
    if n in ('moteur_tableau', 'moteur_etrier', 'moteur_bride'): return 'bride'
    if n.startswith(('poutre', 'martingale', 'accroche', 'machoire', 'piece_angle')): return 'poutre'
    if n.startswith('tube_colliers'): return 'tube'
    if n.startswith('trampoline'): return 'trampoline'
    if n.startswith('batterie'): return 'batterie'
    return 'autre'
BB = {n: d[n].BoundingBox() for n in oth}
def proche(ba, bb, m):
    return not (ba.xmax + m < bb.xmin or bb.xmax + m < ba.xmin or ba.ymax + m < bb.ymin or bb.ymax + m < ba.ymin or ba.zmax + m < bb.zmin or bb.zmax + m < ba.zmin)
levees = sorted(set([round(i * pas, 1) for i in range(int(LM // pas) + 1)] + [LM]))
res = []
for lv in levees:
    mv = {n: (d[n].translate(V(0, 0, lv)) if lv else d[n]) for n in MOB}
    hits, best = [], {}
    for a, sa in mv.items():
        ba = sa.BoundingBox()
        for b in oth:
            if a == 'moteur_arbre' and b == 'moteur_bride':
                continue                                   # l'arbre coulisse dans le fourreau de la bride
            if not proche(ba, BB[b], 300):
                continue
            v = sa.intersect(d[b]).Volume()
            if v > 0.5:
                ib = sa.intersect(d[b]).BoundingBox()
                hits.append((a, b, round(v), [round(q) for q in (ib.xmin, ib.xmax, ib.ymin, ib.ymax, ib.zmin, ib.zmax)])); dist = 0.0
            else:
                dist = sa.distance(d[b])
            k = cat(b)
            if k not in best or dist < best[k][0]:
                best[k] = (round(dist, 1), a, b)
    bbs = [s.BoundingBox() for s in mv.values()]
    r = dict(l=lv, zmin=round(min(b.zmin for b in bbs)), zmax=round(max(b.zmax for b in bbs)), hits=hits, jeux=best)
    res.append(r)
    print(f"{lv:6.1f} z {r['zmin']}–{r['zmax']} | contacts {hits or '-'} | " + ' '.join(f"{k}:{v[0]}({v[1][7:]}/{v[2]})" for k, v in sorted(best.items())), flush=True)
# sortie du bac : monté à la verticale de 0 à 700
bac = [n for n in ('batterie_bac', 'batterie') if n in d]
sortie = []
for dz in range(0, 701, 50):
    bh = {n: d[n].translate(V(0, 0, dz)) for n in bac}
    hits, jmin = [], (1e9, None)
    for a, sa in bh.items():
        ba = sa.BoundingBox()
        for b in oth:
            if b in bac or b in ('coffre_caisse_couvercle', 'coffre_table') or b.startswith('ancre_') or not proche(ba, BB[b], 60):   # table, couvercle et ancre ôtés pour sortir le bac
                continue
            v = sa.intersect(d[b]).Volume()
            if v > 0.5:
                hits.append((a, b, round(v)))
            elif a == 'batterie_bac':
                dd = sa.distance(d[b])
                if dd < jmin[0]:
                    jmin = (round(dd, 1), b)
    sortie.append(dict(dz=dz, hits=hits, jeu=jmin))
    print(f"bac +{dz:3d} : contacts {hits or '-'} jeu mini {jmin}", flush=True)
json.dump(dict(levees=res, sortie_bac=sortie), open('/home/claude/cao/plateforme/balayage_levee.json', 'w'))
