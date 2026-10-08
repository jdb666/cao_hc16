"""Figures en coupe du book (JD 08/10) depuis etudes/coupes_book.json : glissière du tube des colliers, banc renforcé.
python3 book/fig_coupes.py -> book/img/f_glissiere.jpg, book/img/f_banc.jpg"""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from matplotlib import font_manager
for f_ in ('IBM Plex Sans', 'DejaVu Sans'):
    if any(f_ in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.family'] = f_; break
plt.rcParams.update({'font.size': 13, 'axes.edgecolor': '#9AA4A9', 'axes.linewidth': 0.8})
C = json.load(open('/home/claude/cao/etudes/coupes_book.json'))
INK, MUTE, ACC = '#18262E', '#4A5A63', '#B8650E'
STY = {   # nom -> (remplissage, bord, ordre)
    'cp': ('#C98A3E', '#5A3A12', 5), 'cp2': ('#E9CFA3', '#7A5A2A', 4), 'creux': ('#F4E6D0', '#B89A6E', 2),
    'pehd': ('#FFFFFF', '#3E4A50', 7), 'tube': ('#D3D9DC', '#5E686D', 8), 'tour': ('#9EA8AD', '#4A5257', 9),
    'col': ('#2B2F33', '#111417', 10), 'cale': ('#4A4F54', '#22272B', 3), 'alu': ('#BCC5CA', '#6C767B', 1),
    'coque': ('#E3E6E8', '#9AA4A9', 0), 'corde': ('#2F6FB0', '#1D4E80', 11), 'tramp': ('#C9CED1', '#8A9398', 1)}
def trace(ax, coupe, nom, sty, fen=None, alpha=1.0, hatch=None, z=None):
    for pts in C[coupe]['pieces'].get(nom, []):
        fc, ec, zo = STY[sty]
        ax.add_patch(MP(pts, closed=True, fc=fc, ec=ec, lw=0.9, alpha=alpha, zorder=z if z is not None else zo, hatch=hatch))
def note(ax, txt, xy, xyt, ha='left', col=INK, fs=12.5):
    ax.annotate(txt, xy=xy, xytext=xyt, fontsize=fs, color=col, ha=ha, va='center',
                arrowprops=dict(arrowstyle='-', color='#7E888E', lw=0.8, shrinkA=2, shrinkB=1), zorder=20,
                bbox=dict(fc='white', ec='none', pad=1.0, alpha=0.85))
def cadre(ax, x0, x1, z0, z1, titre):
    ax.set_xlim(x0, x1); ax.set_ylim(z0, z1); ax.set_aspect('equal')
    ax.set_title(titre, fontsize=14, color=INK, loc='left', pad=8)
    ax.tick_params(labelsize=10, colors=MUTE); ax.grid(color='#E6EAEC', lw=0.6, zorder=-1)
    ax.set_facecolor('#FFFFFF')

# ------------------------------------------------------------------ glissière
fig = plt.figure(figsize=(16, 9), dpi=100, facecolor='#F7F8F8')
a1 = fig.add_axes([0.045, 0.07, 0.30, 0.86]); a2 = fig.add_axes([0.42, 0.07, 0.56, 0.86])
k = 'glissiere_x2085'
for n, s in (('coque_babord', 'coque'), ('poutre_av', 'alu'), ('longeron_babord', 'alu'), ('piece_angle_av_babord', 'alu'), ('glissiere_cale_babord', 'cale'),
             ('joue_babord', 'cp2'), ('banc_babord_assise', 'cp2'), ('banc_babord_lisse_0', 'cp'), ('glissiere_poteau_haut_babord_int', 'cp'),
             ('glissiere_poteau_bas_babord_int', 'cp'), ('glissiere_sabot_babord', 'cp'), ('glissiere_berceau_babord', 'cp'), ('glissiere_pehd_babord', 'pehd'),
             ('collier_tourillon_babord', 'tour')):
    trace(a1, k, n, s)
for n in ('glissiere_poteau_haut_babord_av', 'glissiere_poteau_bas_babord_av'):     # paroi AV du poteau, derrière le plan de coupe
    trace(a1, 'glissiere_x2059', n, 'creux', z=1)
for pts in C[k]['pieces']['tube_colliers']:
    trace_ = MP(pts, closed=True, fc=STY['tube'][0], ec=STY['tube'][1], lw=0.9, zorder=8); a1.add_patch(trace_)
a1.add_patch(MP([(880, 1145.8), (1078, 1145.8), (1078, 1191.8), (880, 1191.8)], closed=True, fc='#EEF1F2', ec='none', zorder=7))
for i in range(1, 8):
    trace(a1, k, f'collier_pli{i}_babord', 'col')
cadre(a1, 880, 1235, 470, 1235, "Coupe à x 2 085 (axe du tube), bâbord, vue vers l'arrière")
a1.set_xlabel('y (mm)', color=MUTE, fontsize=11)
note(a1, 'tube Ø 50 × 2', (950, 1192), (900, 1222))
note(a1, 'collier', (1100, 1200), (1150, 1222))
note(a1, 'tourillon Ø 45', (1060, 1170), (1135, 1145))
note(a1, 'berceau en U\n4 × CP 9, PEHD 3', (1030, 1132), (900, 1040))
note(a1, 'sabot 6 × CP 10\ny 990 → joue', (1050, 1080), (1135, 1060))
note(a1, 'joue', (1116, 900), (1150, 900))
note(a1, 'poteau caisson\n3 parois CP 9', (1040, 880), (900, 930))
note(a1, 'assise', (950, 680), (905, 720))
note(a1, 'cale coulée\népoxy chargée', (1080, 570), (1150, 610))
note(a1, "pièce d'angle AV", (980, 520), (900, 500))
note(a1, 'longeron', (1090, 540), (1150, 530))

k2 = 'glissiere_y1040'
for n, s in (('poutre_av', 'alu'), ('piece_angle_av_babord', 'alu'), ('glissiere_cale_babord', 'cale'), ('banc_babord_assise', 'cp2'), ('coffre_coque', 'cp2'),
             ('coffre_trappe_c4_2', 'cp2'), ('glissiere_poteau_haut_babord_av', 'cp'), ('glissiere_poteau_haut_babord_ar', 'cp'),
             ('glissiere_poteau_bas_babord_av', 'cp'), ('glissiere_poteau_bas_babord_ar', 'cp'), ('glissiere_sabot_babord', 'cp'),
             ('glissiere_berceau_babord', 'cp'), ('glissiere_pehd_babord', 'pehd')):
    trace(a2, k2, n, s)
tp = sorted(C[k2]['pieces']['tube_colliers'], key=lambda p: -(max(q[0] for q in p) - min(q[0] for q in p)))
a2.add_patch(MP(tp[0], closed=True, fc=STY['tube'][0], ec=STY['tube'][1], lw=1.0, zorder=8))
a2.add_patch(MP(tp[1], closed=True, fc='#EEF1F2', ec=STY['tube'][1], lw=0.8, zorder=8))
trace(a2, k2, 'collier_tourillon_babord', 'tour', alpha=0.9)
cadre(a2, 2020, 2155, 1030, 1215, "Détail : coupe en travers du tube, à y 1 040 (vue de bâbord)")
a2.set_xlabel('x (mm)', color=MUTE, fontsize=11)
zt = 1168.8
a2.plot([2040, 2130], [zt, zt], color=ACC, lw=0.8, ls=(0, (6, 4)), zorder=12)
a2.annotate('', xy=(2085, 1196), xytext=(2085, 1212), arrowprops=dict(arrowstyle='-|>', color=ACC, lw=2.2, mutation_scale=18), zorder=21)
EF = json.load(open('/home/claude/cao/etudes/efforts_colliers.json'))['synthese']
f1 = lambda v: f'{v / 1000:.1f}'.replace('.', ',').replace(',0', '')
a2.text(2088, 1208, f"effort d'un collier : {f1(EF['V_reglage'][0])} à {f1(EF['V_reglage'][1])} kN au réglage,\n{f1(EF['V_max'])} kN à la gîte maxi ({f1(EF['V_max_15'])} kN × 1,5)", color=ACC, fontsize=12, va='center')
note(a2, 'axe du tube', (2128, zt), (2132, 1180))
note(a2, 'tube Ø 50 × 2', (2108, 1185), (2128, 1195))
note(a2, 'tourillon Ø 45 du collier\n(dans le bout du tube)', (2075, 1160), (2025, 1205), ha='left')
note(a2, 'garniture PEHD 3 : le tube y glisse\nen long et y tourne', (2100, 1146), (2128, 1137))
note(a2, 'joues du U : 11 sous l\'axe,\nle tube s\'enlève par le haut', (2117, 1154), (2124, 1112))
note(a2, 'berceau 4 × CP 9', (2070, 1130), (2026, 1118))
note(a2, 'sabot 6 × CP 10 (60), au ras\ndu haut de la joue (z 1 122)', (2060, 1090), (2024, 1080))
note(a2, 'poteau : parois AV et AR CP 9', (2110, 1050), (2124, 1048))
fig.savefig('/home/claude/cao/book/img/f_glissiere.jpg', dpi=100, facecolor=fig.get_facecolor(), pil_kwargs=dict(quality=90))
plt.close(fig)

# ------------------------------------------------------------------ banc
fig = plt.figure(figsize=(16, 9), dpi=100, facecolor='#F7F8F8')
b1 = fig.add_axes([0.035, 0.07, 0.455, 0.87]); b2 = fig.add_axes([0.53, 0.07, 0.455, 0.87])
k = 'banc_x2680'
for n, s in (('coque_babord', 'coque'), ('longeron_babord', 'alu'), ('joue_babord', 'cp2'), ('banc_babord_assise', 'cp2'), ('banc_babord_couple_2', 'cp')):
    trace(b1, k, n, s)
trace(b1, 'banc_x2689', 'banc_babord_jambe_2_ar', 'cp', alpha=0.55, z=6)
for pts in C[k]['pieces'].get('lacage_banc_2', []):
    b1.add_patch(MP(pts, closed=True, fc=STY['corde'][0], ec=STY['corde'][1], lw=0.6, zorder=11))
cadre(b1, 760, 1210, 395, 905, "Au droit d'un couple (x 2 680), vue vers l'arrière")
b1.set_xlabel('y (mm)', color=MUTE, fontsize=11)
note(b1, 'assise CP 9', (900, 683), (800, 730))
note(b1, 'couple CP 9 plein', (900, 630), (790, 600))
note(b1, 'joue (dossier)', (1115, 800), (1000, 830))
note(b1, 'longeron', (1075, 540), (960, 520))
note(b1, 'jambe : 115 sous l\'axe du longeron,\njusqu\'à y 1 162, deux joues CP 9\ncollées de part et d\'autre', (1140, 470), (880, 455))
note(b1, 'laçage Dyneema Ø 5, en double,\nvers l\'autre banc sous la toile', (1000, 416), (790, 415))
k = 'banc_x2545'
for n, s in (('coque_babord', 'coque'), ('longeron_babord', 'alu'), ('joue_babord', 'cp2'), ('banc_babord_assise', 'cp2'), ('banc_babord_lisse_2', 'cp')):
    trace(b2, k, n, s)
cadre(b2, 760, 1210, 395, 905, "Entre deux couples (x 2 545)")
b2.set_xlabel('y (mm)', color=MUTE, fontsize=11)
note(b2, 'assise CP 9 (311 de large)', (950, 683), (830, 730))
note(b2, 'lisse CP 9 × 40 collée sous la rive\nintérieure, d\'un couple à l\'autre', (805, 650), (830, 600))
note(b2, 'joue (dossier)', (1115, 800), (1000, 830))
note(b2, 'longeron', (1075, 540), (960, 520))
note(b2, 'rangement sous l\'assise,\nouvert côté trampoline', (1000, 640), (1000, 470))
fig.savefig('/home/claude/cao/book/img/f_banc.jpg', dpi=100, facecolor=fig.get_facecolor(), pil_kwargs=dict(quality=90))
print('ok')
