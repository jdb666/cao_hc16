"""Annote les photos du HC16 avec les repères de mesure (cotes, angles, diamètres)."""
from PIL import Image, ImageDraw, ImageFont
import math, os
D = os.path.dirname(os.path.abspath(__file__))
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
Fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
JAUNE, NOIR, CYAN = (255, 212, 0), (15, 15, 15), (0, 220, 255)
def trait(d, p, q, c=JAUNE, w=5):
    d.line([p, q], fill=NOIR, width=w + 4); d.line([p, q], fill=c, width=w)
def fleche(d, p, q, c=JAUNE):
    trait(d, p, q, c)
    for a, b in ((p, q), (q, p)):
        ang = math.atan2(b[1] - a[1], b[0] - a[0]); L = 26
        pts = [b, (b[0] - L * math.cos(ang - 0.4), b[1] - L * math.sin(ang - 0.4)), (b[0] - L * math.cos(ang + 0.4), b[1] - L * math.sin(ang + 0.4))]
        d.polygon(pts, fill=c, outline=NOIR)
def pointille(d, p, q, c=JAUNE, n=24):
    for i in range(n):
        if i % 2: continue
        a = (p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n); b = (p[0] + (q[0] - p[0]) * (i + 1) / n, p[1] + (q[1] - p[1]) * (i + 1) / n)
        trait(d, a, b, c, 4)
def chip(d, xy, txt, c=JAUNE, f=F):
    x, y = xy; bb = d.textbbox((0, 0), txt, font=f); w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.rounded_rectangle([x - w / 2 - 12, y - h / 2 - 10, x + w / 2 + 12, y + h / 2 + 12], radius=10, fill=c, outline=NOIR, width=3)
    d.text((x - w / 2, y - h / 2 - bb[1] + 1), txt, font=f, fill=NOIR)
def point(d, p, c=JAUNE, r=12):
    d.ellipse([p[0] - r - 3, p[1] - r - 3, p[0] + r + 3, p[1] + r + 3], fill=NOIR); d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=c)
def cote_h(d, x0, x1, y, yref0, yref1, lab, lx=None):
    trait(d, (x0, yref0), (x0, y - 15), JAUNE, 3); trait(d, (x1, yref1), (x1, y - 15), JAUNE, 3)
    fleche(d, (x0, y), (x1, y)); chip(d, (lx or (x0 + x1) / 2, y), lab)
def cote_v(d, x, y0, y1, lab, lx=None, ly=None):
    fleche(d, (x, y0), (x, y1)); chip(d, (lx or x + 60, ly or (y0 + y1) / 2), lab)

def profil():
    im = Image.open(f'{D}/profil.jpg').convert('RGB'); d = ImageDraw.Draw(im)
    etr, tab = (1952, 818), (40, 832)
    cote_h(d, tab[0], etr[0], 620, 820, 810, 'P1', lx=700)
    cote_h(d, 1150, etr[0], 560, 745, 805, 'P2', lx=1550)
    cote_h(d, 425, etr[0], 500, 770, 805, 'P3', lx=900)
    pointille(d, tab, etr, CYAN, 60)                                   # cordeau étrave -> tableau
    for k in range(11):
        x = etr[0] - k * 190
        if x < tab[0]: break
        trait(d, (x, 812 + (832 - 812) * (etr[0] - x) / (etr[0] - tab[0]) - 14), (x, 870), CYAN, 3)
    chip(d, (300, 790), 'P7 : cordeau, flèches tous les 50 cm', CYAN, Fs)
    cote_v(d, 1100, 856, 774, 'P5', lx=1030)
    cote_v(d, 1195, 858, 1028, 'P6', lx=1260, ly=960)
    point(d, (1279, 852)); chip(d, (1400, 740), 'P4 : pied de mât, angle long.')
    trait(d, (1279, 852), (1340, 765), JAUNE, 3)
    chip(d, (760, 700), 'Q : assiette du longeron', CYAN, Fs); trait(d, (760, 718), (760, 776), CYAN, 3)
    im.save(f'{D}/profil_annote.jpg', quality=88)
def arriere():
    im = Image.open(f'{D}/arriere.jpg').convert('RGB'); d = ImageDraw.Draw(im)
    cote_h(d, 535, 1440, 580, 690, 690, 'A1')
    cote_h(d, 465, 1510, 520, 640, 630, 'A2', lx=700)
    cote_v(d, 610, 728, 642, 'A3', lx=680, ly=760)
    point(d, (1000, 650)); chip(d, (1000, 720), 'A4 : Ø poutre AR')
    im.save(f'{D}/arriere_annote.jpg', quality=88)
def avant():
    im = Image.open(f'{D}/avant.jpg').convert('RGB'); d = ImageDraw.Draw(im)
    cote_h(d, 560, 1310, 520, 690, 685, 'V1')
    pointille(d, (520, 652), (1375, 648), CYAN, 30)
    fleche(d, (950, 650), (950, 604)); chip(d, (1060, 580), 'V2 : flèche')
    point(d, (720, 632)); chip(d, (700, 580), 'V3 : Ø')
    point(d, (945, 700)); chip(d, (945, 770), 'V4 : pied du pilier')
    point(d, (598, 718)); point(d, (1283, 712)); chip(d, (430, 690), 'V5', f=F); trait(d, (470, 695), (590, 716), JAUNE, 3)
    point(d, (1250, 742)); chip(d, (1560, 650), 'V6 + V7 : pont au pied de mât'); trait(d, (1250, 742), (1420, 668), JAUNE, 3)
    im.save(f'{D}/avant_annote.jpg', quality=88)
def dessus():
    im = Image.open(f'{D}/dessus.jpg').convert('RGB'); d = ImageDraw.Draw(im)
    fleche(d, (470, 548), (470, 1198)); chip(d, (400, 870), 'D1')
    trait(d, (470, 548), (560, 548), JAUNE, 3); trait(d, (470, 1198), (560, 1198), JAUNE, 3)
    fleche(d, (1300, 1200), (1300, 1800)); chip(d, (1370, 1500), 'P2')
    trait(d, (1235, 1200), (1300, 1200), JAUNE, 3); trait(d, (1205, 1800), (1300, 1800), JAUNE, 3)
    point(d, (566, 870)); chip(d, (700, 1000), 'D2 : longeron'); trait(d, (566, 870), (650, 980), JAUNE, 3)
    for p in ((560, 1276), (1212, 1276)): point(d, p)
    chip(d, (880, 1330), 'D3 : pieds de mât')
    trait(d, (560, 1276), (760, 1320), JAUNE, 3); trait(d, (1212, 1276), (1000, 1320), JAUNE, 3)
    chip(d, (900, 760), 'D4 : trampoline', CYAN, Fs)
    im.save(f'{D}/dessus_annote.jpg', quality=88)
for f in (profil, arriere, avant, dessus): f()
print('ok')
