"""Étude : Protruar monté à l'envers (tourné de 160°), replié vers l'avant, au milieu du coffre -> etude_moteur_avant.png"""
import sys, math, yaml, json
sys.path.insert(0, '/home/claude/cao')
import hc16_rando as H
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Rectangle, Circle, Arc
c = yaml.safe_load(open('/home/claude/cao/cotes.yaml')); k, p, mo = c['coffre'], c['plateforme'], c['coffre']['moteur']
PT = json.load(open('/home/claude/cao/plateforme/pente.json'))['angles']
G = json.load(open('/home/claude/cao/plateforme/p3d.json'))['pente']['geom']
# moteur (enveloppe du modèle) et articulation retenue
L, dA, tete, nd, nl, hd = mo['arbre_l'], mo['arbre_d'], mo['tete'], mo['nacelle_d'], mo['nacelle_l'], mo['helice_d']
dessus = 900 - mo['bride_nacelle_max'] + nd / 2          # arbre au-dessus de la bride (hélice au plus profond)
xa_int = k['face_ar_x'] - k['ep_face_ar']
xp = xa_int - 10 - (dessus + tete[2])                    # la tête relevée s'arrête à 10 de C4
zp = 560; xs = xp - 10
rot = lambda x, z, a: (xp + (z - zp) * math.sin(math.radians(a)) + (x - xp) * math.cos(math.radians(a)), zp + (z - zp) * math.cos(math.radians(a)) - (x - xp) * math.sin(math.radians(a)))
zsb = zp + dessus - L; zn = zsb - nd / 2
enveloppe = lambda a: dict(
    arbre=[rot(xs, zsb, a), rot(xs, zsb + L, a)],
    tete=[rot(xs + dx, zsb + L + dz, a) for dx, dz in ((-tete[0] / 2, 0), (tete[0] / 2, 0), (tete[0] / 2, tete[2]), (-tete[0] / 2, tete[2]))],
    nac=rot(xs, zn, a))
E0, E90 = enveloppe(0), enveloppe(90)
xn90, zn90 = E90['nac']; avant90 = xn90 - hd / 2
print(f"pivot x {xp:.0f} z {zp} | en marche : nacelle z {zn:.0f}, bas de pale {zn - hd / 2:.0f}, tête z {zsb + L:.0f}–{zsb + L + tete[2]:.0f}")
print(f"relevé 90° : nacelle x {xn90:.0f} z {zn90:.0f}, avant de l'hélice x {avant90:.0f}, dépassement devant le coffre {G['xf'] - avant90:.0f}, tête x {min(q[0] for q in E90['tete']):.0f}–{max(q[0] for q in E90['tete']):.0f}")
# haubans avant : croisés au droit de l'axe
m = c['mats']; a3 = math.radians(m['quete_deg']); f = (m['x_pied'], m['y_axe'], m['z_pied'])
et = (c['coffre']['haubans']['etrave']['x'], 1000, H.interp(c['coques']['pont'], 50) + c['coffre']['haubans']['etrave']['dz'])
cc = (f[0] + 750 * math.sin(a3) - 60 * math.cos(a3), f[2] + 750 * math.cos(a3) + 60 * math.sin(a3) + 35)
sm = (f[0] - 60, f[2] + 60 * math.tan(a3) + 10)
cross = lambda P0: (P0[0] + (et[0] - P0[0]) * 1151 / 2151, P0[1] + (et[2] - P0[1]) * 1151 / 2151)
Xs, Xc = cross(sm), cross(cc)
print(f"croisement des haubans de semelle x {Xs[0]:.0f} z {Xs[1]:.0f} ; des haubans de collier x {Xc[0]:.0f} z {Xc[1]:.0f}")

INK, INK2, WOOD, WOODBG, ACC, OLD, WATER = '#18262E', '#4A5A63', '#9C5F2C', '#EFD9C0', '#1F6F8B', '#C23B4E', '#2D7FA6'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': '#C5CED2'})
fig, (ax, bx) = plt.subplots(1, 2, figsize=(17, 8.2), gridspec_kw={'width_ratios': [1.0, 1.15]})
# ---- profil (coupe dans l'axe) ----
t_ = math.tan(math.radians(10)); D = t_ * (G['x0'] - G['xf']); af = G['xcol'] - G['xf']
ell = [(G['xcol'] - af * math.cos(u), G['zb'] + D + (G['ztop'] - G['zb'] - D) * math.sin(u)) for u in [math.pi / 2 * i / 40 for i in range(41)]]
ax.add_patch(MP([(G['xa'], G['zb']), (G['x0'], G['zb'])] + ell + [(G['xa'], G['ztop'])], closed=True, fc=WOODBG, ec=WOOD, lw=1.6, label='coffre actuel (coupe dans l\'axe)'))
ax.add_patch(MP([(u + 0, v) for u, v in G['poutre']], closed=True, fc='#DCE2E4', ec=INK2, lw=1))
ax.plot([G['pilier'][0]] * 2, [G['pilier'][1], G['pilier'][2]], color=INK2, lw=3)
ax.axhline(0, color=WATER, lw=1.2); ax.text(420, 12, 'flottaison', color=WATER)
for P0, lab in ((sm, 'haubans de semelle'), (cc, 'haubans de collier')):
    ax.plot([P0[0], et[0]], [P0[1], et[2]], color=INK2, lw=.8, ls='--')
ax.plot(*Xs, 'x', color=OLD, ms=9, mew=2); ax.text(Xs[0] - 40, Xs[1] - 42, 'croisement des haubans\nde semelle (z %d)' % Xs[1], color=OLD, ha='right', va='top', fontsize=9)
ax.plot(*Xc, 'x', color=INK2, ms=8, mew=1.5); ax.text(Xc[0] + 25, Xc[1] + 30, 'croisement des haubans\nde collier (z %d)' % Xc[1], color=INK2, ha='left', fontsize=9)
def moteur(ax, E, a, col, lab=None, alpha=1):
    ax.plot(*zip(*E['arbre']), color=col, lw=4, alpha=alpha, solid_capstyle='butt', label=lab)
    ax.add_patch(MP(E['tete'], closed=True, fc=col, ec=col, alpha=.85 * alpha))
    xn, zn_ = E['nac']
    if a == 0:
        ax.add_patch(Rectangle((xn - nl / 2, zn_ - nd / 2), nl, nd, fc=col, alpha=alpha)); ax.add_patch(Rectangle((xn + nl / 2 + 5, zn_ - hd / 2), 25, hd, fc=col, alpha=.6 * alpha))
    else:
        ax.add_patch(Circle((xn, zn_), nd / 2, fc=col, alpha=alpha)); ax.add_patch(Circle((xn, zn_), hd / 2, fc='none', ec=col, lw=1.5, alpha=alpha))
moteur(ax, E0, 0, INK, 'en marche (nacelle tournée de 160°)')
moteur(ax, E90, 90, ACC, 'relevé à 90°, nacelle en travers')
R_ = math.hypot(xn90 - xp, zn90 - zp) + hd / 2
ax.add_patch(Arc((xp, zp), 2 * R_, 2 * R_, theta1=180, theta2=270, color=ACC, lw=.9, ls=':'))
ax.plot(xp, zp, 'o', color=OLD, ms=6); ax.text(xp - 20, zp - 30, 'axe de bascule\nx %d · z %d' % (xp, zp), fontsize=9, color=OLD, ha='right', va='top')
ax.annotate('', xy=(avant90, 715), xytext=(G['xf'], 715), arrowprops=dict(arrowstyle='<->', color=ACC, lw=1.2))
ax.text((avant90 + G['xf']) / 2, 728, 'relevé : dépasse de %d devant le coffre' % (G['xf'] - avant90), ha='center', color=ACC, fontsize=10, fontweight='bold')
ax.text(1560, 960, 'tête en marche\nau-dessus du coffre', fontsize=9, color=INK, ha='center')
ax.text(1880, 440, 'tête relevée\ndans le coffre', fontsize=9, color=ACC, ha='center', va='top')
ax.text(E0['nac'][0], zn - hd / 2 - 40, 'nacelle z %d, bas de pale %d' % (zn, zn - hd / 2), ha='center', va='top', fontsize=9)
ax.text(2075, 700, 'poutre AV', ha='center', fontsize=9, color=INK2); ax.text(2090, 320, 'martingale', fontsize=9, color=INK2)
ax.set_xlim(450, 2200); ax.set_ylim(-560, 1080); ax.set_aspect('equal'); ax.set_title('Profil, coupe dans l\'axe du bateau (mm)', loc='left', fontsize=12, color=INK)
ax.legend(loc='lower left', fontsize=9, frameon=False); ax.grid(color='#EEF1F2', lw=.6)
# ---- dessus ----
W2 = k['largeur'] / 2
bx.add_patch(Rectangle((G['xf'], -W2), G['xa'] - G['xf'], 2 * W2, fc=WOODBG, ec=WOOD, lw=1.4))
bx.add_patch(Rectangle((G['xf'], -190), xa_int - G['xf'], 380, fc='white', ec=WOOD, lw=1.2, ls='--'))
bx.text(1410, 250, 'puits au milieu, 380 de large :\nouvert dessous, devant\net dessus (tête)', fontsize=9, color=WOOD, va='bottom')
bt = k['batterie']['bac']
bx.add_patch(Rectangle((k['batterie']['x_ar'] - bt[1], -215 - bt[0]), bt[1], bt[0], fc='#1F5A85', alpha=.75)); bx.text(k['batterie']['x_ar'] - bt[1] / 2, -540, 'batterie\nen travers\ntribord', color='white', ha='center', va='center', fontsize=9)
bx.plot([xs, xn90], [0, 0], color=ACC, lw=4); bx.add_patch(Rectangle((xn90 - nd / 2, -nl / 2), nd, nl, fc=ACC)); bx.add_patch(Rectangle((xn90 - hd / 2, nl / 2 + 5), hd, 25, fc=ACC, alpha=.6))
bx.add_patch(Rectangle((xp + dessus, -tete[1] / 2), tete[2], tete[1], fc=ACC, alpha=.85))
for sgn in (1, -1):
    bx.plot([sm[0], et[0]], [sgn * 1151, -sgn * 1000], color=INK2, lw=.8, ls='--'); bx.plot([sm[0], et[0]], [sgn * 1151, sgn * 1000], color=INK2, lw=.8, ls='--')
bx.plot(Xs[0], 0, 'x', color=OLD, ms=9, mew=2)
bx.plot([0, 0], [-1000, 1000], alpha=0); bx.text(60, 1030, 'pattes d\'étrave (x 50)', fontsize=9, color=INK2)
bx.axhline(0, color='#C5CED2', lw=.6)
bx.text(G['xf'] + 10, W2 - 60, 'coffre actuel', color=WOOD, fontsize=9)
bx.set_xlim(0, 2250); bx.set_ylim(-1250, 1300); bx.set_aspect('equal'); bx.set_title('Dessus, moteur relevé (mm)', loc='left', fontsize=12, color=INK)
bx.grid(color='#EEF1F2', lw=.6)
fig.tight_layout(); fig.savefig('/home/claude/cao/etudes/etude_moteur_avant.png', dpi=130)
print('OK')
