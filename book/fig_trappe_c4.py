"""Figure du book (JD 08/10) : C4, moitié bâbord vue de l'arrière, avec la trappe du compartiment extérieur, l'assise,
les couples ±420 et ±850 derrière, la poutre AV et le poteau de la glissière. python3 book/fig_trappe_c4.py -> book/img/f_trappe_c4.jpg"""
import json, yaml, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MP
from matplotlib import font_manager
for f_ in ('IBM Plex Sans', 'DejaVu Sans'):
    if any(f_ in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.family'] = f_; break
plt.rcParams.update({'font.size': 13})
c = yaml.safe_load(open('/home/claude/cao/cotes.yaml')); k = c['coffre']
IN = json.load(open('/home/claude/cao/etudes/infos_texte.json'))
INK, MUTE, ACC = '#18262E', '#4A5A63', '#B8650E'
wi = k['largeur'] / 2 - k['ep_flasque']; ztop, cpt = k['dessus_z'], k['dessus_plat_demi']
zt_s = IN['geom']['_geom']['zt_s']; zc4 = k['capot_arriere']['z_c4']; dyc = k['capot_arriere']['demi_y']
t4 = [t for t in k['trappes_c4'] if t['y0'] > 0][0]
gl = k['glissiere_collier']; po = gl['poteau']
zt = lambda y: zc4 if y <= dyc else ztop + (zt_s - ztop) * (y - cpt) / (wi - cpt)
fig, ax = plt.subplots(figsize=(16, 9), dpi=100, facecolor='#F7F8F8')
ax.set_position([0.06, 0.09, 0.9, 0.84])
ys = [i * 2.0 for i in range(0, int(wi / 2) + 1)] + [wi]
haut = [(0, zc4), (dyc, zc4)] + [(y, zt(y)) for y in ys if y > dyc]
ax.add_patch(MP([(0, 540)] + haut + [(wi, 540)], closed=True, fc='#EBEEEF', ec=INK, lw=1.2, zorder=1))
ax.plot([y for y in ys if y > dyc], [zt(y) - 25 for y in ys if y > dyc], color=ACC, lw=0.8, ls=(0, (2, 3)), zorder=2)
pz = lambda y: 539.5 + 100 * max(0.0, 1 - (y / 925) ** 2) + 32.5           # dessus de la poutre AV, cintrée (flèche 100 entre les pièces d'angle)
ax.add_patch(MP([(0, 540)] + [(y, pz(y)) for y in ys] + [(wi, 540)], closed=True, fc='#C9CED1', ec='none', zorder=2))
ax.text(420, 600, 'poutre AV, contre C4', color=INK, fontsize=12)
ax.add_patch(Rectangle((t4['y0'], t4['z0']), t4['y1'] - t4['y0'], t4['z1'] - t4['z0'], fc='#F3D9B8', ec=ACC, lw=2.4, zorder=4))
ax.text((t4['y0'] + t4['y1']) / 2, (t4['z0'] + t4['z1']) / 2 + 12, f"trappe {round(t4['y1'] - t4['y0'])} × {round(t4['z1'] - t4['z0'])}", color=ACC, fontsize=17, fontweight='bold', ha='center', zorder=6)
ax.text((t4['y0'] + t4['y1']) / 2, (t4['z0'] + t4['z1']) / 2 - 22, 'la chute de C4 fait le couvercle', color=ACC, fontsize=12, ha='center', zorder=6)
ya, yb = 800, wi
ax.add_patch(Rectangle((ya, 676), yb - ya, 9, fc='#E9CFA3', ec='#7A5A2A', lw=0.8, zorder=5))
ax.text(1105, 662, 'assise (z 676 → 685)', color=INK, fontsize=12)
for yc, lib in ((420, 'couple plein ±420\n(caisson de rangement à gauche)'), (850, 'couple ±850, derrière :\nappui du couvercle')):
    ax.plot([yc - 3, yc - 3], [540, zt(yc) - 1], color='#7E888E', lw=0.9, ls=(0, (5, 3)), zorder=3)
    ax.plot([yc + 3, yc + 3], [540, zt(yc) - 1], color='#7E888E', lw=0.9, ls=(0, (5, 3)), zorder=3)
ax.text(640, 700, 'couple plein ±420\n(caisson de rangement à droite)', color=MUTE, fontsize=11)
ax.text(1095, 600, 'couple ±850, derrière :\nappui du couvercle', color=MUTE, fontsize=11)
# poteau de la glissière : 33 derrière C4, devant le bout extérieur de la trappe (vu au travers)
y0p = gl['y_int']; z0p, z1p = 685, 1122 - gl['sabot']['h']
ax.add_patch(Rectangle((y0p, z0p), wi - y0p, z1p - z0p, fc='#26292C', ec='none', alpha=0.28, hatch='///', zorder=7))
ax.add_patch(Rectangle((y0p, z1p), wi - y0p, gl['sabot']['h'], fc='#26292C', ec='none', alpha=0.45, zorder=7))
ax.annotate('poteau et sabot de la glissière,\n33 derrière C4 : le couvercle\nsort en glissant vers l\'intérieur', xy=(1040, 960), xytext=(1336, 1010), fontsize=12, color=INK,
            arrowprops=dict(arrowstyle='-', color='#7E888E', lw=0.8), zorder=8)
ax.text(380, 750, f'capot (z {zc4} contre C4)', color=INK, fontsize=12)
ax.annotate('', xy=(t4['y0'] + 2, zt(t4['y0'])), xytext=(t4['y0'] + 2, t4['z1']), arrowprops=dict(arrowstyle='<->', color=INK, lw=0.8))
ax.text(t4['y0'] - 8, (zt(t4['y0']) + t4['z1']) / 2, '25', ha='left', va='center', fontsize=11, color=INK)
ax.annotate('', xy=(t4['y1'] - 40, 685), xytext=(t4['y1'] - 40, t4['z0']), arrowprops=dict(arrowstyle='<->', color=INK, lw=0.8))
ax.text(t4['y1'] - 48, 697, '25', ha='left', va='center', fontsize=11, color=INK)
ax.set_xlim(1340, 0); ax.set_ylim(540, 1180); ax.set_aspect('equal')
ax.set_xlabel("y (mm) : joue bâbord à gauche, axe du bateau à droite", color=MUTE, fontsize=12)
ax.set_title("C4, moitié bâbord vue de l'arrière : trappe du compartiment extérieur", fontsize=15, color=INK, loc='left')
ax.tick_params(labelsize=10, colors=MUTE); ax.grid(color='#E6EAEC', lw=0.6, zorder=0); ax.set_facecolor('#FFFFFF')
fig.savefig('/home/claude/cao/book/img/f_trappe_c4.jpg', dpi=100, facecolor=fig.get_facecolor(), pil_kwargs=dict(quality=90))
print('ok')
