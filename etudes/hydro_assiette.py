"""Hydrostatique d'une coque HC16 du modèle par sections tous les 50 mm (shapely), ×2 pour le catamaran.
Charge W au CdG du coffre -> enfoncement et assiette, par équilibre exact (volume et centre de carène)."""
import sys, math, warnings, json; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import yaml, cadquery as cq, hc16_rando as H
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union
V = cq.Vector
RHO = 1025.0                     # kg/m3
c = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
A = H.build(c, plateforme_seule=True)
h = {ch.name: (ch.obj.val() if isinstance(ch.obj, cq.Workplane) else ch.obj) for ch in A.children}['coque_babord']
DX = 50.0
XS = [25 + DX * i for i in range(0, 102)]
SEC = {}
for x in XS:
    s = h.intersect(cq.Solid.makeBox(1.0, 3000, 2000, V(x - 0.5, -500, -1000)))
    if s.Volume() < 1:
        continue
    vs, ts = s.tessellate(0.3, 0.2)
    tri = [Polygon([(vs[i].y, vs[i].z) for i in t]) for t in ts]
    SEC[x] = unary_union([p.buffer(0.01) for p in tri if p.area > 1e-4])
print('sections', len(SEC), 'x', min(SEC), max(SEC))
def carene(dz, tau, xf):
    """Volume (m3) et xB (mm) des deux coques sous l'eau z = dz + tau (xf - x)."""
    v, mx = 0.0, 0.0
    for x, P in SEC.items():
        zw = dz + tau * (xf - x)
        a = P.intersection(sbox(-1e4, -1e4, 1e4, zw)).area            # mm2
        v += a * DX; mx += a * DX * x
    return 2 * v / 1e9, (mx / v if v else 0)
def flottaison(dz, tau, xf):
    aw, mx, pts = 0.0, 0.0, []
    for x, P in SEC.items():
        zw = dz + tau * (xf - x)
        ch = P.intersection(sbox(-1e4, zw - 0.5, 1e4, zw + 0.5)).area    # corde × 1 mm
        aw += ch * DX; mx += ch * DX * x; pts.append((x, ch))
    xF = mx / aw
    IL = sum(ch * DX * ((x - xF) ** 2 + DX ** 2 / 12) for x, ch in pts)
    return 2 * aw / 1e6, xF, 2 * IL / 1e12                              # m2, mm, m4
V0, xB0 = carene(0, 0, 0)
Aw, xF0, IL0 = flottaison(0, 0, 0)
D0 = RHO * V0
print(f"flottaison du plan : carène {V0*1000:.1f} L -> {D0:.0f} kg, xB {xB0:.0f} ; flottaison {Aw:.3f} m2, xF {xF0:.0f}, IL {IL0:.3f} m4 ; {RHO*Aw/1000:.2f} kg/mm ; {RHO*IL0*math.pi/180:.1f} kg.m/°")
def equilibre(W, xW, D=D0, xG=xB0):
    Mt, xt = D + W, (D * xG + W * xW) / (D + W)
    dz, tau = W / (RHO * Aw) * 1000, W * (xF0 - xW) / 1000 / (RHO * IL0)
    for it in range(30):
        v, xb = carene(dz, tau, xF0)
        f1, f2 = RHO * v - Mt, xb - xt
        va, xba = carene(dz + 0.2, tau, xF0); vb, xbb = carene(dz, tau + 2e-5, xF0)
        J = [[RHO * (va - v) / 0.2, RHO * (vb - v) / 2e-5], [(xba - xb) / 0.2, (xbb - xb) / 2e-5]]
        det = J[0][0] * J[1][1] - J[0][1] * J[1][0]
        ddz, dtau = (-f1 * J[1][1] + f2 * J[0][1]) / det, (-f2 * J[0][0] + f1 * J[1][0]) / det
        dz += ddz; tau += dtau
        if abs(ddz) < 0.01 and abs(dtau) < 1e-7:
            break
    v, xb = carene(dz, tau, xF0)
    return dz, tau, RHO * v - Mt, xb - xt
out = dict(D0=D0, xB0=xB0, Aw=Aw, xF0=xF0, IL0=IL0, cas=[])
for W, xW in [(50, 1700), (100, 1700), (150, 1700), (100, 1550), (100, 1850), (100, 2500)]:
    dz, tau, r1, r2 = equilibre(W, xW)
    hh = lambda x: dz + tau * (xF0 - x)
    print(f"W {W:3d} kg à x {xW} : assiette {math.degrees(math.atan(tau)):.2f}° sur le nez, eau +{hh(0):.0f} à l'étrave, {hh(5050):+.0f} au tableau ; "
          f"au coffre x 1 250 +{hh(1250):.0f}, x 1 860 +{hh(1860):.0f}, C4 +{hh(2022.5):.0f}  (résidus {r1:.2f} kg, {r2:.2f} mm)")
    out['cas'].append(dict(W=W, xW=xW, dz=dz, tau=tau))
json.dump(out, open('/home/claude/cao/plateforme/hydro_assiette.json', 'w'))
