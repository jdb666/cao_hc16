"""Gréement HC16 d'origine approché (cotes.yaml : hc16_origine), dans le plan du mât :
GV en repère du mât (u vers l'arrière, w le long du mât depuis la rotule), foc dans le plan axial (x, z).
Surfaces officielles atteintes par le rond de chute (parabolique). CV par contours (rond compris) et par triangles."""
import math, sys, yaml

def aire_cdg(C):
    A = cx = cy = 0
    for i in range(len(C)):
        (x1, y1), (x2, y2) = C[i], C[(i + 1) % len(C)]; c = x1 * y2 - x2 * y1; A += c; cx += (x1 + x2) * c; cy += (y1 + y2) * c
    return abs(A) / 2, cx / (3 * A), cy / (3 * A)

def rond(A_, B_, prof, n=24):
    """Points d'un rond parabolique entre A_ et B_ (exclus), creux maxi prof, à droite de A_->B_."""
    (xa, ya), (xb, yb) = A_, B_; L = math.hypot(xb - xa, yb - ya); nx, ny = (yb - ya) / L, -(xb - xa) / L
    return [(xa + (xb - xa) * t + nx * 4 * prof * t * (1 - t), ya + (yb - ya) * t + ny * 4 * prof * t * (1 - t)) for t in (i / n for i in range(1, n))]

def regle(f, cible, lo, hi):
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if f(m) < cible else (lo, m)
    return (lo + hi) / 2

def greement(h):
    m, g, f, e = h['mat'], h['gv'], h['foc'], h['etai']
    q = math.radians(m['quete_deg']); UM, AX = (math.sin(q), math.cos(q)), (math.cos(q), -math.sin(q))
    P = lambda u, w: (m['x'] + UM[0] * w + AX[0] * u, m['z'] + UM[1] * w + AX[1] * u)
    # GV : amure et têtière sur le mât, point d'écoute par bordure et chute
    L = g['tetiere_w'] - g['amure_w']; d = (L * L - (g['chute'] ** 2 - g['bordure'] ** 2)) / (2 * L); uc = math.sqrt(g['bordure'] ** 2 - d * d)
    T, H, Cl = (0.0, g['amure_w']), (0.0, g['tetiere_w']), (uc, g['amure_w'] + d)
    pg = regle(lambda p: aire_cdg([T, Cl] + rond(Cl, H, p) + [H])[0], g['surface'] * 1e6, 0, 3000)
    gv = [T, Cl] + rond(Cl, H, pg) + [H]
    # foc : point d'étai sur les pattes d'oie, étai jusqu'au capelage, amure et têtière sur l'étai
    xf, yf, zf = e['ferrure']; za = zf + 235; dx = math.sqrt(e['patte_oie'] ** 2 - yf ** 2 - (za - zf) ** 2); apex = (xf + dx, za)
    hd = P(0, e['capelage_w']); v = (hd[0] - apex[0], hd[1] - apex[1]); Lf = math.hypot(*v); ue = (v[0] / Lf, v[1] / Lf)
    Tf = (apex[0] + ue[0] * f['jeu_amure'], apex[1] + ue[1] * f['jeu_amure']); Hf = (apex[0] + ue[0] * (Lf - f['jeu_tete']), apex[1] + ue[1] * (Lf - f['jeu_tete']))
    Cf = tuple(f['point_ecoute'])
    pf = regle(lambda p: aire_cdg([Tf, Cf] + rond(Cf, Hf, p) + [Hf])[0], f['surface'] * 1e6, 0, 2000)
    foc = [Tf, Cf] + rond(Cf, Hf, pf) + [Hf]
    # centres véliques dans le plan axial (voiles dans l'axe)
    Ag, ug, wg = aire_cdg(gv); xg, zg = P(ug, wg); Af, xff, zff = aire_cdg(foc)
    At, ut, wt = aire_cdg([T, Cl, H]); xt, zt = P(ut, wt); Aft, xft, zft = aire_cdg([Tf, Cf, Hf])
    S = Ag + Af; St = At + Aft
    r1 = lambda p: [round(c, 1) for c in p]
    return dict(
        mat=dict(x=m['x'], z=m['z'], quete=m['quete_deg'], L=m['longueur'], diam=m['diam']),
        gv=dict(contour=[r1(p) for p in gv], amure=r1(T), ecoute=r1(Cl), tetiere=r1(H), rond=round(pg), lattes=g.get('lattes', 7)),
        foc=dict(contour=[r1(p) for p in foc], amure=r1(Tf), ecoute=r1(Cf), tetiere=r1(Hf), rond=round(pf)),
        etai=dict(apex=r1(apex), capelage=r1(hd), w=e['capelage_w'], ferrure=list(e['ferrure'])),
        cadene=list(h['cadene_hauban']), ecoute_gv=list(h['ecoute_gv']), ecoute_foc=list(h['ecoute_foc']),
        surfaces=dict(gv=round(Ag / 1e6, 2), foc=round(Af / 1e6, 2)),
        cv=dict(x=round((Ag * xg + Af * xff) / S, 1), z=round((Ag * zg + Af * zff) / S, 1)),
        cv_triangles=dict(x=round((At * xt + Aft * xft) / St, 1), z=round((At * zt + Aft * zft) / St, 1)),
        cv_reference=h.get('cv_reference'),
        bome_z=round(P(0, g['amure_w'])[1], 1), tete_mat=r1(P(0, m['longueur'])))

if __name__ == '__main__':
    c = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
    r = greement(c['hc16_origine'])
    for k in ('surfaces', 'cv', 'cv_triangles', 'cv_reference', 'bome_z', 'tete_mat', 'etai'):
        print(k, r[k])
    print('GV rond', r['gv']['rond'], 'écoute', r['gv']['ecoute'], '| foc rond', r['foc']['rond'], 'amure', r['foc']['amure'], 'têtière', r['foc']['tetiere'])
    # Rando, même méthode (contour avec rond de chute) et triangles
    v, mt = c['voile'], c['mats']; q = math.radians(mt['quete_deg'])
    sys.path.insert(0, '/home/claude/cao'); import hc16_rando as H_
    xpm, zpm = H_.pied_mat(c)                    # pied du mât sur la cale de l'emplanture (JD 06/10)
    P = lambda u, w: (xpm + math.sin(q) * w + math.cos(q) * u, zpm + math.cos(q) * w - math.sin(q) * u)
    A, u, w = aire_cdg(v['contour']); At, ut, wt = aire_cdg([v['contour'][0], v['contour'][1], v['contour'][-1]])
    print('Rando contour : %.2f m² par voile, CV x %.0f z %.0f | triangle : x %.0f z %.0f' % ((A / 1e6,) + P(u, w) + P(ut, wt)))
    zr = P(u, w)[1]; S16 = (r['surfaces']['gv'] + r['surfaces']['foc'])
    print('couple deux voiles pleines / HC16 (contours) : %.2f' % (2 * A / 1e6 * zr / (S16 * r['cv']['z'])))
