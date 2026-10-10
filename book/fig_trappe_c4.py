"""Figure du book (JD 08/10) : C4, moitié bâbord vue de l'arrière, avec la trappe du compartiment extérieur, l'assise,
les couples ±420 et ±850 derrière, la poutre AV et le poteau d'appui du tube (JD 09/10 : dans le coffre, dessus en moustache ; trappes jaunes, tube posé à plat sur la potence). python3 book/fig_trappe_c4.py -> book/img/f_trappe_c4.jpg"""
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
fr0 = lambda v: f'{round(v):,}'.replace(',', ' ')
fr2 = lambda v: f'{v:.2f}'.replace('.', ',')
wi = k['largeur'] / 2 - k['ep_flasque']; ztop, cpt = k['dessus_z'], k['dessus_plat_demi']
zt_s = IN['geom']['_geom']['zt_s']; zc4 = k['capot_arriere']['z_c4']; dyc = k['capot_arriere']['demi_y']
OC = IN['geom'].get('_ouvertures_c4')            # (JD 09/10 17 h 30) plus de trappe : ouverture polygonale, sans couvercle
t4 = None if OC else [t for t in k['trappes_c4'] if t['y0'] > 0][0]
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
pu_ = ((k.get('moteur') or {}).get('vertical2') or {}).get('puits') or {}
if pu_.get('arriere_ouvert'):                 # (JD 09/10 17 h) plus de face arrière du puits : C4 ouverte sur sa largeur, du fond au capot
    dyp, epp = pu_['demi_y'], pu_['ep']
    ax.add_patch(Rectangle((0, 540), dyp, zc4 - 6 - 540, fc='#FFFFFF', ec='#7E888E', lw=0.8, hatch='..', zorder=1.5))
    ax.add_patch(Rectangle((dyp, 540), epp, zc4 - 6 - 540, fc='#26292C', ec='none', zorder=1.6))
    ax.text(dyp / 2, 760, 'puits\nouvert\nderrière', color=INK, fontsize=11, ha='center', va='center', zorder=6)
if OC:
    ax.add_patch(MP(OC['contour'], closed=True, fc='#FFFFFF', ec=ACC, lw=2.4, zorder=4))
    ym_ = (OC['y'][0] + OC['y'][1]) / 2
    ax.text(ym_ + 40, OC['z_bas'] + 52, f"ouverture {fr0(OC['y'][1] - OC['y'][0])} de large,\n{fr0(OC['z_haut'][0] - OC['z_bas'])} à {fr0(OC['z_haut'][1] - OC['z_bas'])} de haut ({fr2(OC['aire_m2'])} m²)", color=ACC, fontsize=15, fontweight='bold', ha='center', va='center', zorder=6)
    ax.text(ym_ + 40, OC['z_bas'] + 16, 'sans couvercle', color=ACC, fontsize=12, ha='center', zorder=6)
else:
    ax.add_patch(Rectangle((t4['y0'], t4['z0']), t4['y1'] - t4['y0'], t4['z1'] - t4['z0'], fc='#F6DC8C', ec='#B8860B', lw=2.4, zorder=4))   # trappes jaunes (JD 09/10)
    ax.text((t4['y0'] + t4['y1']) / 2, (t4['z0'] + t4['z1']) / 2 + 12, f"trappe {round(t4['y1'] - t4['y0'])} × {round(t4['z1'] - t4['z0'])}", color=ACC, fontsize=17, fontweight='bold', ha='center', zorder=6)
    ax.text((t4['y0'] + t4['y1']) / 2, (t4['z0'] + t4['z1']) / 2 - 22, 'la chute de C4 fait le couvercle', color=ACC, fontsize=12, ha='center', zorder=6)
ya, yb = 800, wi
ax.add_patch(Rectangle((ya, 676), yb - ya, 9, fc='#E9CFA3', ec='#7A5A2A', lw=0.8, zorder=5))
ax.text(1105, 662, 'assise (z 676 → 685)', color=INK, fontsize=12)
for yc, lib in ((420, 'couple plein ±420\n(caisson de rangement à gauche)'), (850, 'couple ±850, derrière :\nappui du couvercle')):
    ax.plot([yc - 3, yc - 3], [540, zt(yc) - 1], color='#7E888E', lw=0.9, ls=(0, (5, 3)), zorder=3)
    ax.plot([yc + 3, yc + 3], [540, zt(yc) - 1], color='#7E888E', lw=0.9, ls=(0, (5, 3)), zorder=3)
ax.text(*((408, 728) if OC else (640, 700)), 'couple plein ±420\n(caisson de rangement\nà droite)' if OC else 'couple plein ±420\n(caisson de rangement à droite)', color=MUTE, fontsize=11)
ax.text(1095, 600, 'couple ±850, derrière' + ('\n(vu dans l\'ouverture)' if OC else ' :\nappui du couvercle'), color=MUTE, fontsize=11)
# (JD 09/10) poteau d'appui dans le coffre, 3 devant C4 (vu au travers de C4), potence au-dessus ; le tube est posé à plat sur la potence (plus de bloc PEHD)
G_ = IN['geom'].get('_glissiere', {}).get('babord', {}).get('poteau', {})
yp_, rp_ = po['y'], po['d'] / 2; z0p, zbp, z1p = G_.get('z0', 589.5), G_.get('dessus_coffre', zt(po['y'])), G_.get('z1', 1113.8)
ax.add_patch(Rectangle((yp_ - rp_, z0p), 2 * rp_, zbp - z0p, fc='#26292C', ec='none', alpha=0.28, hatch='///', zorder=7))
ax.add_patch(Rectangle((yp_ - rp_, zbp), 2 * rp_, z1p - zbp, fc='#26292C', ec='none', alpha=0.85, zorder=7))
pt_ = gl.get('potence', {}); h_pt = pt_.get('h', 40); z_pt = z1p - 20
ax.add_patch(Rectangle((gl['y_int'], z_pt), gl['berceau']['y_fin'] - gl['y_int'], h_pt, fc='#26292C', ec='none', alpha=0.85, zorder=8))
bl_ = gl.get('bloc'); h_bl = 0 if bl_ is None else bl_.get('sous_tube', 10)
if bl_ is not None:
    ax.add_patch(Rectangle((gl['y_int'], z_pt + h_pt), gl['berceau']['y_fin'] - gl['y_int'], 24, fc='#FFFFFF', ec='#7E888E', lw=0.8, zorder=8))
ax.add_patch(Rectangle((0, z_pt + h_pt + h_bl), gl['berceau']['y_fin'], 50, fc='#B3BCC1', ec='#6E7A80', lw=0.8, zorder=9))
ax.text(600, z_pt + h_pt + h_bl + 25, 'tube des colliers', color=INK, fontsize=12, va='center', zorder=10)
ax.add_patch(Rectangle((wi, 540), 9, 1085 - 540, fc='#F3F2ED', ec=INK, lw=0.8, zorder=6))
ax.text(wi + 16, 1065, 'joue', color=INK, fontsize=11, ha='right')
ax.annotate('poteau carbone Ø 50\nd\'appui du tube,\ndans le coffre,\n3 devant C4\n(grisé : vu au\ntravers de C4)', xy=(yp_ + rp_, 700), xytext=(1330, 640), fontsize=11, color=INK,
            arrowprops=dict(arrowstyle='-', color='#7E888E', lw=0.8), zorder=10)
ax.annotate('potence 4 × CP 10 :\nle tube est posé dessus' if bl_ is None else 'potence CP et bloc PEHD\nsous le bout du tube', xy=(gl['y_int'] + 20, z_pt + 20), xytext=(930, 1010), fontsize=12, color=INK,
            arrowprops=dict(arrowstyle='-', color='#7E888E', lw=0.8), zorder=10)
ax.text(380, 830, f'capot horizontal (z {zc4})', color=INK, fontsize=12)
ya_, yb_, za_ = (OC['y'][0] + 120, OC['y'][1] - 40, OC['z_bas']) if OC else (t4['y0'] + 2, t4['y1'] - 40, t4['z0'])
zh_ = (zt(ya_) - 25) if OC else t4['z1']
ax.annotate('', xy=(ya_, zt(ya_)), xytext=(ya_, zh_), arrowprops=dict(arrowstyle='<->', color=INK, lw=0.8))
ax.text(ya_ - 8, (zt(ya_) + zh_) / 2, '25', ha='left', va='center', fontsize=11, color=INK)
ax.annotate('', xy=(yb_, 685), xytext=(yb_, za_), arrowprops=dict(arrowstyle='<->', color=INK, lw=0.8))
ax.text(yb_ - 8, 697, '25', ha='left', va='center', fontsize=11, color=INK)
ax.set_xlim(1340, 0); ax.set_ylim(540, 1230); ax.set_aspect('equal')
ax.set_xlabel("y (mm) : joue bâbord à gauche, axe du bateau à droite", color=MUTE, fontsize=12)
ax.set_title("C4, moitié bâbord vue de l'arrière : " + ("ouverture du compartiment extérieur" if OC else "trappe du compartiment extérieur"), fontsize=15, color=INK, loc='left')
ax.tick_params(labelsize=10, colors=MUTE); ax.grid(color='#E6EAEC', lw=0.6, zorder=0); ax.set_facecolor('#FFFFFF')
fig.savefig('/home/claude/cao/book/img/f_trappe_c4.jpg', dpi=100, facecolor=fig.get_facecolor(), pil_kwargs=dict(quality=90))
print('ok')
