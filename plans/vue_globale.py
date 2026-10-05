import sys, json, yaml, time
sys.path.insert(0,'/home/claude/cao')
import hc16_rando as H
t=time.time()
cfg=yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
A=H.build(cfg)
out=[]
def walk(a):
    for ch in a.children:
        yield ch
        yield from walk(ch)
for ch in walk(A):
    if ch.name.startswith('repere_'): continue
    if ch.obj is None: continue
    sh = ch.obj if not hasattr(ch.obj,'val') else ch.obj.val() if not hasattr(ch.obj,'vals') else ch.obj.vals()
    shapes = sh if isinstance(sh,list) else [sh]
    col = ch.color.toTuple()[:3] if ch.color else (0.7,0.7,0.7)
    V=[];T=[]
    for s in shapes:
        try:
            vs,ts=s.tessellate(2.0 if 'voile' in ch.name else 3.0, 0.4)
        except Exception as e:
            print('ERR',ch.name,e); continue
        o=len(V)
        V+= [(round(v.x),round(v.y),round(v.z)) for v in vs]
        T+= [(a+o,b+o,c+o) for a,b,c in ts]
    out.append(dict(n=ch.name,c=[round(x,3) for x in col],v=[c for p in V for c in p],t=[i for tr in T for i in tr]))
    pass
# tente igloo (optionnelle, affichée à la demande)
import math
sys.path.insert(0, '/home/claude/cao/plans')
import tente as TE
Vt, Tt, _ = TE.maillage(56)
out.append(dict(n='tente_toile', c=[0.24, 0.49, 0.42], v=[round(c) for p in Vt for c in p], t=Tt))
def tube(pts, r, nr=8):
    V, T = [], []
    for i, p in enumerate(pts):
        q0 = pts[max(0, i - 1)]; q1 = pts[min(len(pts) - 1, i + 1)]
        d = [q1[j] - q0[j] for j in range(3)]; L = math.sqrt(sum(x * x for x in d)); d = [x / L for x in d]
        a = [0, 0, 1] if abs(d[2]) < 0.9 else [1, 0, 0]
        e1 = [d[1] * a[2] - d[2] * a[1], d[2] * a[0] - d[0] * a[2], d[0] * a[1] - d[1] * a[0]]; n1 = math.sqrt(sum(x * x for x in e1)); e1 = [x / n1 for x in e1]
        e2 = [d[1] * e1[2] - d[2] * e1[1], d[2] * e1[0] - d[0] * e1[2], d[0] * e1[1] - d[1] * e1[0]]
        for k_ in range(nr):
            th = 2 * math.pi * k_ / nr
            V.append([round(p[j] + r * (math.cos(th) * e1[j] + math.sin(th) * e2[j]), 1) for j in range(3)])
    for i in range(len(pts) - 1):
        for k_ in range(nr):
            a0, a1 = i * nr + k_, i * nr + (k_ + 1) % nr
            T += [a0, a0 + nr, a1 + nr, a0, a1 + nr, a1]
    return V, T
for i, sens in enumerate((1, -1), 1):
    pts, L = TE.arceau(sens, 120)
    pts = [(x, y, z + TE.t['arceau_diam']) for x, y, z in pts]           # arceau à l'extérieur de la toile
    Vp, Tp = tube(pts, TE.t['arceau_diam'] / 2 + 3)
    out.append(dict(n=f'tente_arceau_{i}', c=[0.2, 0.22, 0.24], v=[c for p in Vp for c in p], t=Tp))
json.dump(out,open('/home/claude/cao/plans/global.json','w'),separators=(',',':'))
print('t',time.time()-t)
