import sys, yaml, warnings, itertools, time; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/claude/cao')
import cadquery as cq, hc16_rando as H
c=yaml.safe_load(open(sys.argv[1])); A=H.build(c)
d={ch.name:(ch.obj.val() if isinstance(ch.obj,cq.Workplane) else ch.obj) for ch in A.children}
N=[n for n in d if not n.startswith(('voile','repere','livarde'))]
BB={n:d[n].BoundingBox() for n in N}
t=time.time(); hits=[]
for a,b in itertools.combinations(N,2):
    ba,bb=BB[a],BB[b]
    if ba.xmax<bb.xmin or bb.xmax<ba.xmin or ba.ymax<bb.ymin or bb.ymax<ba.ymin or ba.zmax<bb.zmin or bb.zmax<ba.zmin: continue
    try: v=d[a].intersect(d[b]).Volume()
    except Exception as e: v=-1
    if v>1 or v<0: hits.append((a,b,round(v)))
for h in hits: print(h)
print(len(N),'pièces', len(hits),'recouvrements', round(time.time()-t),'s')
