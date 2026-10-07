"""Volume intérieur du coffre par zones : python3 vol_zones.py module.py cotes.yaml sortie.json"""
import sys, json, copy, importlib.util, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/cao')
import yaml, cadquery as cq
mod, cotes, out = sys.argv[1:4]
spec = importlib.util.spec_from_file_location('Hx', mod); H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
c = yaml.safe_load(open(cotes))
for m_ in ('transversal', 'arriere', 'avant2'):
    if m_ in c['coffre']['moteur']: c['coffre']['moteur'][m_]['bascule'] = 0
v2 = c['coffre']['moteur'].get('vertical2')
if v2: v2['levee'] = 0
A = H.build(c)
I, E = H.COFFRE_CACHE['int'], H.COFFRE_CACHE['ext']
V = cq.Vector
def vol(x0, x1, y0, y1, sym=True):
    v = 0.0
    for sg in ((1, -1) if sym else (1,)):
        ya, yb = sorted((sg * y0, sg * y1))
        b = cq.Solid.makeBox(x1 - x0, yb - ya, 4000, V(x0, ya, -2000))
        v += I.intersect(b).Volume()
    return v / 1e6
g = c['coffre'].get('_geom') or {}
bb = I.BoundingBox()
X0, X1 = bb.xmin - 10, bb.xmax + 10
wi = bb.ymax + 1
res = dict(ext_L=E.Volume() / 1e6, int_L=I.Volume() / 1e6, bbox=[bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax])
res['centre_L'] = vol(X0, X1, 0, 331, sym=False) * 2
pq = c['coffre'].get('_puits') or {}; xpa, xpi = pq.get('x_av', 1711), pq.get('x_int', 1717)
ca = c['coffre'].get('_coffre_ancre')
if ca:                                                    # (JD 07/10) coffre à ancre devant le puits, plus de caisse de batterie
    res['coffre_ancre_L'] = vol(X0, xpa, 0, ca['demi_y'], sym=False) * 2
    res['centre_devant_puits_hors_ancre_L'] = vol(X0, xpa, ca['demi_y'] + ca['ep'], 331)
else:
    res['centre_devant_caisse_L'] = vol(X0, 1384, 0, 331, sym=False) * 2
    res['centre_caisse_L'] = vol(1384, 1717, 0, 331, sym=False) * 2
res['puits_L'] = vol(xpi, X1, 0, 131, sym=False) * 2
res['flancs_puits_L'] = vol(xpi, X1, 131, 331)
res['cotes_331_850_L'] = vol(X0, X1, 331, 850)
res['cotes_850_joue_L'] = vol(X0, X1, 850, wi)
res['hors_centre_L'] = res['cotes_331_850_L'] + res['cotes_850_joue_L']
cb = c['coffre'].get('batterie_banc')
if cb:                                                    # caisson sur l'avant de chaque banc (batterie à bâbord, rangement à tribord)
    cs = cb['caisson']
    res['caisson_banc_L'] = (cb['l'] + 2 * cs['jeu']) * (cb['larg'] + 2 * cs['jeu']) * (cb['h'] + cs['h_libre']) / 1e6
json.dump(res, open(out, 'w'), indent=1); print(json.dumps(res, indent=1))
