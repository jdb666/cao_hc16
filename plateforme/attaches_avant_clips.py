"""Coupes des attaches sur la poutre AV et sur les longerons (accroche / couple + mâchoire boulonnée) -> attache_poutre.svg, attache_longeron.svg"""
import sys, math, yaml
sys.path.insert(0, '/home/claude/cao')
import hc16_rando as H
from shapely.geometry import Polygon as SPoly, box as sbox, Point
from shapely.ops import unary_union as sunion
cfg = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
P, k, p = H.PROFILS, cfg['coffre'], cfg['plateforme']
def demi(nom, jeu):
    pb = SPoly(P[nom]).buffer(jeu, join_style=1); u0, _, u1, _ = pb.bounds
    return sunion([pb, sbox(u0, -400, u1, 0)])
def mach(nom, jeu, mj):
    pb = SPoly(P[nom]).buffer(jeu, join_style=1); r_ = -min(u for u, v in P[nom]) + jeu
    g = sbox(mj['u_ext'], -(r_ + mj['levre']), mj.get('u_fin', 0.0), mj['v_haut']).difference(pb)
    return max(g.geoms, key=lambda q: q.area) if g.geom_type != 'Polygon' else g
def d_poly(g):
    gs = g.geoms if hasattr(g, 'geoms') else [g]
    out = []
    for q in gs:
        for ring in [q.exterior] + list(q.interiors):
            out.append('M' + ' L'.join(f'{x:.1f},{-y:.1f}' for x, y in ring.coords) + ' Z')
    return ' '.join(out)
def svg(vb, corps, clip=None):
    x0, v0, x1, v1 = vb
    c = f'<defs><clipPath id="{clip}"><rect x="{x0}" y="{-v1}" width="{x1 - x0}" height="{v1 - v0}"/></clipPath></defs>' if clip else ''
    return f'<svg class="at" viewBox="{x0} {-v1} {x1 - x0} {v1 - v0}" xmlns="http://www.w3.org/2000/svg">{c}{corps}</svg>'
T = lambda x, y, s, a='start', cl='': f'<text x="{x:.1f}" y="{-y:.1f}" text-anchor="{a}" font-size="6.2"{" class=" + chr(34) + cl + chr(34) if cl else ""}>{s}</text>'
L = lambda pts: '<polyline class="at-fil" points="' + ' '.join(f'{x:.1f},{-y:.1f}' for x, y in pts) + '"/>'
B = lambda x, y: f'<circle class="at-boulon" cx="{x:.1f}" cy="{-y:.1f}" r="3.25"/>'
echelle = lambda x, y: f'<line class="at-ech" x1="{x}" y1="{-y}" x2="{x + 50}" y2="{-y}"/><line class="at-ech" x1="{x}" y1="{-y - 2}" x2="{x}" y2="{-y + 2}"/><line class="at-ech" x1="{x + 50}" y1="{-y - 2}" x2="{x + 50}" y2="{-y + 2}"/>' + T(x + 25, y + 3, '50 mm', 'middle')

# ---------- poutre AV, accroche à y 850 (coupe dans le plan de l'accroche, l'avant à gauche) ----------
ac, mj = k['accroches_poutre'], k['accroches_poutre']['machoire']
du = p.get('poutre_axe_u', 0.0); xn = p['poutre_av_x'] - du               # centre du nez
yh = 850; zc = H.z_cambre(yh, p['poutre_av_z'], p['poutre_av_fleche'], p['poutre_av_y_libre'])
vmax = max(v for u, v in P['poutre']); umax = max(u for u, v in P['poutre']); rn = -min(u for u, v in P['poutre'])
bq = k['bancs']; v_ass = bq['plan_z'] + bq['hauteur'] - bq['ep_assise'] - zc
uc = k['face_ar_x'] - xn                                                   # face arrière de C4
acc = sbox(uc, -ac['sous_axe'], ac['fin_x'] - xn, v_ass).difference(demi('poutre', ac['jeu']))
acc = max(acc.geoms, key=lambda q: q.area) if acc.geom_type != 'Polygon' else acc
mg = p['martingale']; zt = H.z_tige_martingale(mg, p['poutre_av_z'], rn, yh)
ut, vt = p['poutre_av_x'] - xn, zt - zc
zb_s = k['fond_z'] + (k['fond_z_cotes'] - k['fond_z']) * min(1, (yh - k['fond_plat_demi']) / (k['largeur'] / 2 - k['ep_flasque'] - k['fond_plat_demi']))
va = -rn - mj['jeu']; te = mj['ep']
corn = SPoly([(uc, va), (uc + mj['aile_h'], va), (uc + mj['aile_h'], va - te), (uc + te, va - te), (uc + te, va - mj['aile_v']), (uc, va - mj['aile_v'])])
e4 = k['ep_face_ar']; dbl = sbox(uc - e4 - 12, va - mj['aile_v'] - 6, uc - e4, va - 6)
vb_ = va - mj['aile_v'] / 2 - 2
vbA = (-118, -104, 118, 148)
c4 = sbox(uc - e4, zb_s - zc, uc, vbA[3] + 5)
ass = sbox(uc, v_ass, vbA[2] + 5, v_ass + bq['ep_assise'])
corps = f'<g clip-path="url(#cA)"><path class="at-cp" d="{d_poly(c4)}"/><path class="at-assise" d="{d_poly(ass)}"/></g>'
corps += f'<path class="at-cp" d="{d_poly(acc)}"/><path class="at-cp" d="{d_poly(dbl)}"/><path class="at-corn" d="{d_poly(corn)}"/>'
corps += f'<path class="at-alu" d="{d_poly(SPoly(P["poutre"]))}"/>'
corps += f'<line class="at-trampo" x1="{umax:.1f}" y1="0" x2="{vbA[2]}" y2="0"/>'
corps += f'<circle class="at-tige" cx="{ut:.1f}" cy="{-vt:.1f}" r="3"/>'
corps += f'<rect class="at-boulon" x="{uc - e4 - 18:.1f}" y="{-(vb_ + 3):.1f}" width="{e4 + 18 + te + 4:.1f}" height="6"/>'
corps += f'<rect class="at-boulon" x="{uc + te:.1f}" y="{-(vb_ + 5):.1f}" width="4" height="10"/><rect class="at-boulon" x="{uc - e4 - 18:.1f}" y="{-(vb_ + 5):.1f}" width="5" height="10"/>'
corps += f'<path class="at-ouvert" d="M 2 -2 L 2 {-(-60)} L {umax + 8:.1f} {-(-60)} L {umax + 8:.1f} -2"/>'
corps += T(-3, 6, 'poutre AV', 'middle')
corps += L([(uc - e4 / 2, 96), (-60, 96)]) + T(-62, 94.5, 'C4', 'end') + T(-62, 86.5, 'sans jour', 'end')
corps += L([(20, 60), (20, 104), (26, 104)]) + T(28, 102.5, 'accroche CP 9')
corps += T(28, 94.5, "jusqu'à l'assise")
corps += T(60, v_ass + 13, 'assise du banc', 'middle')
corps += L([(uc + mj['aile_h'] - 4, va - te), (uc + mj['aile_h'] - 4, -84), (-8, -84)]) + T(-6, -85.5, 'cornière alu 4 mm')
corps += L([(uc - e4 - 16, vb_ - 5), (uc - e4 - 16, -86)]) + T(-114, -92, '2 × M6 dans C4')
corps += T(-114, -100, 'doublage intérieur')
corps += T(umax + 6, 4, 'trampoline') + T(ut + 6, vt - 2, 'tige de martingale')
corps += T((2 + umax + 8) / 2, -52, 'quart ouvert', 'middle')
corps += echelle(58, -92)
open('/home/claude/cao/plateforme/attache_poutre.svg', 'w').write(svg(vbA, corps, 'cA'))

# ---------- longeron bâbord, couple à x 2 136 (coupe dans le plan du couple, l'extérieur à gauche) ----------
b = k['bancs']; mjb = b['machoire']; ly = p['longeron_y']
xc = b['couples_x'][0]; za = p['poutre_av_z'] + (p['poutre_ar_z'] - p['poutre_av_z']) * (xc - p['poutre_av_x']) / (p['poutre_ar_x'] - p['poutre_av_x'])
wi = k['largeur'] / 2 - k['ep_flasque']; zt0 = b['plan_z']; zs = zt0 + b['hauteur']
ulm = max(u for u, v in P['longeron'])
cp = sunion([sbox(ly - wi, zt0 - za, ly - b['y_int'], zs - b['ep_assise'] - za), sbox(ly - b['couple_ext'], -b['couple_sous_axe'], ulm + 2, zt0 - za)]).difference(demi('longeron', 2))
cp = max(cp.geoms, key=lambda q: q.area) if cp.geom_type != 'Polygon' else cp
ev = b.get('evidement')
if ev:                                                   # couple évidé sous l'assise (âme sous l'assise, plein au-dessus du longeron)
    u_o = ulm + 2 + ev['marge']
    o_ = sbox(u_o, zt0 - za - 20, ly - b['y_int'] + 20, zs - b['ep_assise'] - za - ev['ame']).buffer(-ev['rayon'], join_style=1).buffer(ev['rayon'], join_style=1)
    cp = cp.difference(o_)
    cp = max(cp.geoms, key=lambda q: q.area) if cp.geom_type != 'Polygon' else cp
mjl = mach('longeron', 2, mjb)
# joue jusqu'au longeron : bas au-dessus du longeron sous son épaisseur + jeu (comme le modèle)
jl = b.get('jeu_joue_longeron', 2); ua_, ub_ = ly - k['largeur'] / 2, ly - wi
loc = SPoly(P['longeron']).intersection(sbox(ua_ - jl, -100, ub_ + jl, 100))
v_joue = loc.bounds[3] + jl if b.get('joue_jusqu_au_longeron') else zt0 - za
joue = sbox(ua_, v_joue, ub_, 200)
assise = sbox(ly - wi, zs - b['ep_assise'] - za, ly - b['y_int'], zs - za)
vbB = (-78, -62, 128, 104)
lc = b['lacage']; R_ = -min(u for u, v in P['longeron']) + lc['diam'] / 2 + 1
ye = ly - b['couple_ext'] - lc['diam'] / 2 - 0.5
lac = [(ye, lc['haut']), (ye, -R_), (vbB[2], -R_)]
blb = [(-38, -10), (-38, -27)]
corps = f'<g clip-path="url(#cB)"><path class="at-cp" d="{d_poly(cp)}"/><path class="at-joue" d="{d_poly(joue)}"/><path class="at-assise" d="{d_poly(assise)}"/></g>'
corps += f'<polyline class="at-lace" points="' + ' '.join(f'{u:.1f},{-v:.1f}' for u, v in lac) + '"/>'
corps += f'<path class="at-mach" d="{d_poly(mjl)}"/>'
corps += f'<path class="at-alu" d="{d_poly(SPoly(P["longeron"]))}"/>'
corps += f'<line class="at-trampo" x1="{ulm:.1f}" y1="{-6.6:.1f}" x2="{vbB[2]}" y2="{-6.6:.1f}"/>' + ''.join(B(*q) for q in blb)
corps += f'<path class="at-ouvert" d="M 2 -2 L 2 {-(-50)} L {ulm + 10:.1f} {-(-50)} L {ulm + 10:.1f} -2"/>'
corps += T(12, -3, 'longeron', 'middle')
corps += L([(-22, 70), (-22, 88), (-12, 88)]) + T(-10, 86.5, "joue (dossier), jusqu'au longeron")
corps += L([(60, 70), (60, 78)]) + T(60, 80, 'couple CP 9', 'middle')
corps += L([(-44, -36), (-44, -50), (-60, -50)]) + T(-74, -58, 'mâchoire CP 9, 2 × M6')
corps += T(ulm + 6, -3, 'trampoline') + T(126, -33, 'laçage, devant le couple', 'end', 'at-t-lace')
corps += T((2 + ulm + 10) / 2, -46, 'quart ouvert', 'middle')
corps += echelle(62, -55)
open('/home/claude/cao/plateforme/attache_longeron.svg', 'w').write(svg(vbB, corps, 'cB'))
print('OK', 'poutre y', yh, 'zc', round(zc, 1), 'tige v', round(vt, 1), '| longeron x', xc, 'za', round(za, 1))
