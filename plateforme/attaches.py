"""Coupes des attaches sur la poutre AV et sur les longerons (accroche / couple posés par-dessus, brêlage et laçage dessous) -> attache_poutre.svg, attache_longeron.svg"""
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
# (JD 30/09) le couple ±850 traverse C4 et fait l'accroche : dessus de la poutre, nez contre C4 et lèvre sous le nez ;
# fin de pose en diagonale arrière-bas ; brêlage du trou de la lèvre au pied du pilier de martingale (y 0, en arrière-plan)
from shapely import affinity as AF
import math
ac = k['accroches_poutre']; br = ac.get('brelage') or {}; tb = br.get('trou') or {'u': -20, 'v': -50, 'diam': 8}
du = p.get('poutre_axe_u', 0.0); xn = p['poutre_av_x'] - du               # centre du nez
yh = 850; zc = H.z_cambre(yh, p['poutre_av_z'], p['poutre_av_fleche'], p['poutre_av_y_libre'])
vmax = max(v for u, v in P['poutre']); umax = max(u for u, v in P['poutre']); rn = -min(u for u, v in P['poutre'])
bq = k['bancs']; v_ass = bq['plan_z'] + bq['hauteur'] - bq['ep_assise'] - zc
uc = k['face_ar_x'] - xn                                                   # face arrière de C4
e4 = k['ep_face_ar']
po = ac.get('pose') or {'angle': 45, 'course': 33}; a_ = math.radians(po['angle'])
P0 = SPoly(P['poutre']).buffer(ac['jeu'], join_style=1)
P1 = AF.translate(P0, po['course'] * math.cos(a_), -po['course'] * math.sin(a_))
cor = sunion([P0, P1]).convex_hull.union(sunion([P1, AF.translate(P1, 0, -1000)]).convex_hull).intersection(sbox(uc, -1e4, 1e4, 1e4))
fin = sbox(uc - e4, -ac['sous_axe'], ac['fin_x'] - xn, v_ass).difference(cor)
fin = max(fin.geoms, key=lambda q: q.area) if fin.geom_type != 'Polygon' else fin
mg = p['martingale']; zt = H.z_tige_martingale(mg, p['poutre_av_z'], rn, yh)
ut, vt = p['poutre_av_x'] - xn, zt - zc
zb_s = k['fond_z'] + (k['fond_z_cotes'] - k['fond_z']) * min(1, (yh - k['fond_plat_demi']) / (k['largeur'] / 2 - k['ep_flasque'] - k['fond_plat_demi']))
z_pied = p['poutre_av_z'] - mg['pied_sous_axe_extremites']
uf, vf = p['poutre_av_x'] - 12 - br.get('diam', 5) / 2 - 1 - xn, z_pied - br.get('diam', 5) / 2 - 1 - zc   # passe sous le bord avant du pied
up_ = p['poutre_av_x'] - xn                                                # axe du pilier (y 0)
vbA = (-118, -212, 118, 148)
cadre = sunion([fin, sbox(uc - e4 - 60, max(zb_s - zc, vbA[1] - 5), uc - e4, vbA[3] + 5)])   # le couple continue dans le coffre (cadre de 60 le long de C4)
c4h = sbox(uc - e4, v_ass, uc, vbA[3] + 5); c4b = sbox(uc - e4, max(zb_s - zc, vbA[1] - 5), uc, -ac['sous_axe'])
ass = sbox(uc, v_ass, vbA[2] + 5, v_ass + bq['ep_assise'])
pil = sbox(up_ - 12, z_pied - zc, up_ + 12, z_pied - zc + 34)             # bas du pilier seulement
corps = f'<g clip-path="url(#cA)"><path class="at-cp" d="{d_poly(cadre)}"/><path class="at-c4" d="{d_poly(c4h)}"/><path class="at-c4" d="{d_poly(c4b)}"/><path class="at-assise" d="{d_poly(ass)}"/></g>'
corps += f'<path class="at-fond" d="{d_poly(pil)}"/>'
corps += f'<path class="at-alu" d="{d_poly(SPoly(P["poutre"]))}"/>'
corps += f'<line class="at-trampo" x1="{umax:.1f}" y1="0" x2="{vbA[2]}" y2="0"/>'
corps += f'<circle class="at-tige" cx="{ut:.1f}" cy="{-vt:.1f}" r="3"/>'
corps += f'<circle class="at-oeil" cx="{tb["u"]:.1f}" cy="{-tb["v"]:.1f}" r="{tb["diam"] / 2:.1f}"/>'
corps += f'<polyline class="at-lace" points="{tb["u"]:.1f},{-tb["v"]:.1f} {uf:.1f},{-vf:.1f}"/>'
# sens de la fin de pose
ax0, ay0 = -104, 58; ax1, ay1 = ax0 + 26 * math.cos(a_), ay0 - 26 * math.sin(a_)
corps += f'<line class="at-fleche" x1="{ax0}" y1="{-ay0}" x2="{ax1:.1f}" y2="{-ay1:.1f}"/><path class="at-fleche-p" d="M {ax1:.1f} {-ay1:.1f} l -7 -1.5 l 5.5 -5.5 Z"/>'
corps += T(-104, 70, 'fin de pose en', 'start') + T(-104, 63, f"diagonale : {po['course']} à {po['angle']}°", 'start')
corps += T(-3, 6, 'poutre AV', 'middle')
corps += L([(uc - e4 / 2, 128), (-60, 128)]) + T(-62, 126.5, 'C4', 'end')
corps += L([(uc - e4 - 30, 104), (-86, 104)]) + T(-114, 112, 'couple ±850 CP 9', 'start') + T(-114, 97, 'traverse C4 (fente)', 'start')
corps += L([(20, 60), (20, 104), (26, 104)]) + T(28, 102.5, "accroche = le couple,")
corps += T(28, 94.5, "jusqu'à l'assise")
corps += T(60, v_ass + 13, 'assise du banc', 'middle')
corps += T(umax + 6, 4, 'trampoline') + T(ut + 6, vt - 2, 'tige de martingale')
corps += L([(uc + 4, -38), (-86, -38)]) + T(-114, -30, 'lèvre sous le nez', 'start')
corps += L([(tb['u'] - 5, tb['v'] - 3), (-86, -66)]) + T(-114, -74, f"trou Ø {tb['diam']} du brêlage", 'start')
corps += T(-114, -118, 'brêlage Ø 5', 'start', 'at-t-lace') + T(-114, -126, 'en diagonale sous', 'start', 'at-t-lace') + T(-114, -134, 'la poutre, vers le', 'start', 'at-t-lace') + T(-114, -142, 'pied du pilier (y 0)', 'start', 'at-t-lace')
corps += L([(-10, -110), (-40, -121)])
corps += T(up_ + 16, z_pied - zc + 22, 'pied du pilier de', 'start') + T(up_ + 16, z_pied - zc + 14, 'martingale (y 0,', 'start') + T(up_ + 16, z_pied - zc + 6, 'en arrière-plan)', 'start')
corps += T(70, -30, 'dessous de la queue', 'middle') + T(70, -38, 'ouvert (trampoline)', 'middle')
corps += echelle(58, -200)
open('/home/claude/cao/plateforme/attache_poutre.svg', 'w').write(svg(vbA, corps, 'cA'))

# ---------- longeron bâbord, premier couple (coupe dans le plan du couple, l'extérieur à gauche) ----------
b = k['bancs']; ly = p['longeron_y']
xc = b['couples_x'][0]; za = p['poutre_av_z'] + (p['poutre_ar_z'] - p['poutre_av_z']) * (xc - p['poutre_av_x']) / (p['poutre_ar_x'] - p['poutre_av_x'])
wi = k['largeur'] / 2 - k['ep_flasque']; zt0 = b['plan_z']; zs = zt0 + b['hauteur']; ceh = b.get('couple_ext_haut', 0)
ulm = max(u for u, v in P['longeron'])
cp = sunion([sbox(ly - wi, zt0 - za, ly - b['y_int'], zs - b['ep_assise'] - za), sbox(ly - b['couple_ext'], -b['couple_sous_axe'], ulm + 2, zt0 - za + ceh)]).difference(demi('longeron', 2))
cp = cp.buffer(-0.2, join_style=2).buffer(0.2, join_style=2)
cp = max(cp.geoms, key=lambda q: q.area) if cp.geom_type != 'Polygon' else cp
ev = b.get('evidement')
if ev:                                                   # couple évidé sous l'assise (âme sous l'assise, plein au-dessus du longeron)
    u_o = ulm + 2 + ev['marge']
    o_ = sbox(u_o, zt0 - za - 20, ly - b['y_int'] + 20, zs - b['ep_assise'] - za - ev['ame']).buffer(-ev['rayon'], join_style=1).buffer(ev['rayon'], join_style=1)
    cp = cp.difference(o_)
    cp = max(cp.geoms, key=lambda q: q.area) if cp.geom_type != 'Polygon' else cp
# joue : dans le plan du couple, elle est entaillée jusqu'au haut de la joue du couple ; entre les couples, elle descend jusqu'au longeron
jl = b.get('jeu_joue_longeron', 2); ua_, ub_ = ly - k['largeur'] / 2, ly - wi
loc = SPoly(P['longeron']).intersection(sbox(ua_ - jl, -100, ub_ + jl, 100))
v_joue = loc.bounds[3] + jl if b.get('joue_jusqu_au_longeron') else zt0 - za
v_ent = zt0 - za + ceh if b.get('entaille_dans_joue') else v_joue
joue = sbox(ua_, v_ent, ub_, 200)
joue_bas = sbox(ua_, v_joue, ub_, v_ent)
assise = sbox(ly - wi, zs - b['ep_assise'] - za, ly - b['y_int'], zs - za)
vbB = (-78, -84, 128, 104)
lc = b['lacage']; rc = lc['diam'] / 2
ye = ly - b['couple_ext'] - rc - 0.5; vl = -b['couple_sous_axe'] - rc - 1
lac = [(ye, lc['haut']), (ye, vl), (vbB[2], vl)]
corps = f'<g clip-path="url(#cB)"><path class="at-cp" d="{d_poly(cp)}"/><path class="at-joue" d="{d_poly(joue)}"/><path class="at-assise" d="{d_poly(assise)}"/></g>'
corps += f'<path class="at-fond" d="{d_poly(joue_bas)}"/>'
corps += f'<polyline class="at-lace" points="' + ' '.join(f'{u:.1f},{-v:.1f}' for u, v in lac) + '"/>'
corps += f'<path class="at-alu" d="{d_poly(SPoly(P["longeron"]))}"/>'
corps += f'<line class="at-trampo" x1="{ulm:.1f}" y1="{-6.6:.1f}" x2="{vbB[2]}" y2="{-6.6:.1f}"/>'
corps += f'<path class="at-ouvert" d="M 2 26 L 2 {-vl - 6:.1f} L {ulm + 10:.1f} {-vl - 6:.1f} L {ulm + 10:.1f} 26"/>'
corps += T(12, -3, 'longeron', 'middle')
corps += L([(-22, 70), (-22, 88), (-12, 88)]) + T(-10, 86.5, 'joue (dossier), entaillée')
corps += T(-10, 79, 'au droit du couple')
corps += L([(ua_ - 3, (v_joue + v_ent) / 2), (-50, (v_joue + v_ent) / 2), (-50, 58)]) + T(-76, 64, 'joue entre', 'start') + T(-76, 57, 'les couples', 'start')
corps += T(28, 30, 'couple CP 9, entier', 'middle')
corps += T(-74, -70, 'couple posé par-dessus,') + T(-74, -78, 'sans pièce en plus')
corps += T(ulm + 6, -3, 'trampoline') + T(126, vl - 9, 'laçage : tient le banc', 'end', 'at-t-lace')
corps += T((2 + ulm + 10) / 2, -34, 'ouvert dessous', 'middle')
corps += echelle(62, -76)
open('/home/claude/cao/plateforme/attache_longeron.svg', 'w').write(svg(vbB, corps, 'cB'))
print('OK', 'poutre y', yh, 'zc', round(zc, 1), 'tige v', round(vt, 1), '| longeron x', xc, 'za', round(za, 1), 'laçage v', round(vl, 1))
