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
cr_ = next((cc for cc in (c['coffre'].get('couples_coffre') or []) if cc.get('x0') == 'puits'), None)
YR, EPR = (cr_['y'], cr_.get('ep', 6)) if cr_ else (331, 6)   # (JD 08/10) couple plein des caissons de rangement : ±420 (avant ±331)
res['couple_rangement_y'] = YR
res['centre_L'] = vol(X0, X1, 0, YR, sym=False) * 2
pq = c['coffre'].get('_puits') or {}; xpa, xpi = pq.get('x_av', 1711), pq.get('x_int', 1717)
ca = c['coffre'].get('_coffre_ancre')
if ca:                                                    # (JD 07/10) coffre à ancre devant le puits, plus de caisse de batterie
    res['coffre_ancre_L'] = vol(X0, xpa, 0, ca['demi_y'], sym=False) * 2
    res['centre_devant_puits_hors_ancre_L'] = vol(X0, xpa, ca['demi_y'] + ca['ep'], YR)
else:
    res['centre_devant_caisse_L'] = vol(X0, 1384, 0, YR, sym=False) * 2
    res['centre_caisse_L'] = vol(1384, 1717, 0, YR, sym=False) * 2
res['puits_L'] = vol(xpi, X1, 0, 131, sym=False) * 2
res['flancs_puits_L'] = vol(xpi, X1, 131, YR)
cap_ = c['coffre'].get('_capot_arriere')
if c['coffre'].get('rangements') and cap_:                # (JD 08/10) caisson de rangement (un par bord) : de la paroi du puits au couple plein, de la cloison du puits à C4, sous le capot
    y_in, y_out = pq.get('demi_y', 128) + pq.get('ep', 6), YR - EPR / 2
    xa_ = c['coffre']['face_ar_x']; epc_ = c['coffre']['capot_arriere'].get('ep', 6)
    b_ = cq.Solid.makeBox(X1 - xpi, y_out - y_in, 4000, V(xpi, y_in, -2000))
    pente_ = (cap_['z0'] - cap_['z_c4']) / (xa_ - cap_['x0'])
    dessus_ = cq.Workplane('XZ', origin=(0, y_out, 0)).polyline([(cap_['x0'], cap_['z0'] - epc_), (xa_ + 10, cap_['z0'] - epc_ - pente_ * (xa_ + 10 - cap_['x0'])),
                                                                 (xa_ + 10, 3000), (cap_['x0'], 3000)]).close().extrude(y_out - y_in).val()
    res['rangement_L'] = (I.intersect(b_).Volume() - I.intersect(b_).intersect(dessus_).Volume()) / 1e6
res[f'cotes_{YR}_850_L'] = vol(X0, X1, YR, 850)
res['cotes_850_joue_L'] = vol(X0, X1, 850, wi)
res['hors_centre_L'] = res[f'cotes_{YR}_850_L'] + res['cotes_850_joue_L']
acc_ = (c['coffre'].get('_accoudoirs') or {}).get('babord')
if acc_:                                                  # (JD 08/10) intérieur d'un accoudoir (batterie)
    res['accoudoir_L'] = acc_['interieur'][0] * acc_['interieur'][1] * acc_['interieur'][2] / 1e6
cb = c['coffre'].get('batterie_banc')
if cb:                                                    # caisson sur l'avant de chaque banc (batterie à bâbord, rangement à tribord)
    cs = cb['caisson']
    res['caisson_banc_L'] = (cb['l'] + 2 * cs['jeu']) * (cb['larg'] + 2 * cs['jeu']) * (cb['h'] + cs['h_libre']) / 1e6
json.dump(res, open(out, 'w'), indent=1); print(json.dumps(res, indent=1))
