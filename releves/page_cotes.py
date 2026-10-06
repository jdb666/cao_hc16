"""Formulaire « Cotes manquantes » (06/10/2026) : croquis SVG + champs enregistrés dans le db de l'artifact.
python3 page_cotes.py -> releves/cotes_manquantes_hc16.html"""
import math, html, json

esc = html.escape
OUT = '/home/claude/cao/releves/cotes_manquantes_hc16.html'


# ---------- aides SVG ----------
def chip(x, y, t):
    w = 12 + 9.2 * len(t)
    return (f'<g class="sc"><rect x="{x - w / 2:.1f}" y="{y - 11:.1f}" width="{w:.1f}" height="22" rx="5"/>'
            f'<text x="{x:.1f}" y="{y + 4.6:.1f}" text-anchor="middle">{esc(t)}</text></g>')


def dim(x1, y1, x2, y2, m='a'):
    return f'<line class="dm" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" marker-start="url(#{m}s)" marker-end="url(#{m}e)"/>'


def ext(x1, y1, x2, y2):
    return f'<line class="ex" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'


def txt(x, y, t, cls='lb', anchor='start'):
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{esc(t)}</text>'


def defs(m):
    return (f'<defs><marker id="{m}s" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path class="ah" d="M10,1 L1,5 L10,9 z"/></marker>'
            f'<marker id="{m}e" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path class="ah" d="M0,1 L9,5 L0,9 z"/></marker></defs>')


def svg(m, vb, label, body, cls='w'):
    return f'<svg class="{cls}" viewBox="{vb}" role="img" aria-label="{esc(label)}">{defs(m)}{body}</svg>'


# ---------- croquis 1 : coin AV bâbord vu de dessus (échelle 1,1 px/mm) ----------
def croquis_dessus():
    s = 1.1
    X = lambda x: 24 + (x - 1700) * s
    Y = lambda y: 420 - (y - 880) * s
    b = []
    yb = Y(1192.5)
    b.append(f'<rect class="hu" x="{X(1700):.1f}" y="{yb:.1f}" width="{X(2330) - X(1700):.1f}" height="{440 - yb:.1f}"/>')
    b.append(f'<line class="ed" x1="{X(1700):.1f}" y1="{yb:.1f}" x2="{X(2330):.1f}" y2="{yb:.1f}"/>')
    b.append(f'<rect class="li" x="{X(1700):.1f}" y="{Y(1199):.1f}" width="{X(2330) - X(1700):.1f}" height="{Y(1192.5) - Y(1199):.1f}"/>')
    b.append(f'<line class="ax" x1="{X(1700):.1f}" y1="{Y(1000):.1f}" x2="{X(2330):.1f}" y2="{Y(1000):.1f}"/>')
    b.append(txt(30, Y(1000) - 6, 'axe de la coque'))
    # semelle prévue
    b.append(f'<rect class="pv" x="{X(1860):.1f}" y="{Y(1186):.1f}" width="{X(2110) - X(1860):.1f}" height="{Y(1045) - Y(1186):.1f}"/>')
    b.append(txt(X(1860) + 6, Y(1045) - 8, 'semelle prévue', 'lb sm'))
    # poutre AV et longeron
    b.append(f'<rect class="mt" x="{X(2022.5):.1f}" y="{Y(925):.1f}" width="{X(2118) - X(2022.5):.1f}" height="{440 - Y(925):.1f}"/>')
    b.append(txt(X(2118) + 8, 414, 'poutre AV'))
    b.append(f'<rect class="mt" x="{X(2124):.1f}" y="{Y(1115):.1f}" width="{740 - X(2124):.1f}" height="{Y(1071) - Y(1115):.1f}"/>')
    b.append(txt(X(2124) + 110, Y(1071) + 20, 'longeron'))
    # pièce d'angle : manchon + nez arrondi
    r = 35 * s
    xn, xr_, yt, yb2 = X(1973), X(2065), Y(1122), Y(1040)
    xm0, xm1, ym0, ym1 = X(2016), X(2124), Y(1050), Y(925)
    b.append(f'<path class="dk" d="M{xn + r:.1f},{yt:.1f} H{xr_:.1f} V{ym0:.1f} H{xm1:.1f} V{ym1:.1f} H{xm0:.1f} V{yb2:.1f} H{xn + r:.1f} '
             f'A{r:.1f},{r:.1f} 0 0 1 {xn:.1f},{yb2 - r:.1f} V{yt + r:.1f} A{r:.1f},{r:.1f} 0 0 1 {xn + r:.1f},{yt:.1f} Z"/>')
    b.append(txt((xm0 + xm1) / 2, ym1 - 12, "pièce d'angle", 'lw', 'middle'))
    # pylône (dessous)
    b.append(f'<circle class="hid" cx="{X(2070):.1f}" cy="{Y(1000):.1f}" r="{35 * s:.1f}"/>')
    b.append(txt(X(2070), Y(1000) + 35 * s + 16, 'pylône (dessous)', 'lw sm', 'middle'))
    # mât prévu et son axe
    b.append(f'<line class="st" x1="{X(1960):.1f}" y1="14" x2="{X(1960):.1f}" y2="436"/>')
    b.append(f'<circle class="ms" cx="{X(1960):.1f}" cy="{Y(1161):.1f}" r="{30 * s:.1f}"/>')
    b.append(txt(X(1960) + 8, 22, 'mât prévu, Ø 60 : son axe à 60 devant'))
    b.append(txt(X(1960) + 8, 40, 'la face avant de la poutre AV'))
    b.append(txt(30, 22, '← étrave', 'lb b'))
    b.append(txt(30, Y(1199) - 8, 'bord de la coque (liston)', 'lb sm'))
    b.append(txt(30, 432, 'vers le trampoline ↓', 'lb sm'))
    # cotes
    xm4 = X(2048)
    b.append(dim(xm4, yb, xm4, yt))
    b.append(chip(xm4 + 26, (yb + yt) / 2, 'M4'))
    yp = Y(1035)
    xm6 = X(2150)
    b.append(ext(X(2070), yp, xm6 + 8, yp))
    b.append(dim(xm6, yb, xm6, yp))
    b.append(chip(xm6 + 26, yb + 26, 'M6'))
    b.append(chip(X(2070), Y(1000), 'M7'))
    b.append(ext(xn, yb2, xn, 404))
    b.append(dim(xn, 398, X(2022.5), 398))
    b.append(chip((xn + X(2022.5)) / 2, 424, 'M5'))
    yd = Y(1090)
    b.append(f'<line class="dm" x1="{xn:.1f}" y1="{yd:.1f}" x2="734" y2="{yd:.1f}" marker-end="url(#ae)"/>')
    b.append(chip(668, yd, 'D6'))
    b.append(txt(734, Y(1115) - 8, "→ nez de la pièce d'angle AR", 'lb sm', 'end'))
    return svg('a', '0 0 740 440', "Coin avant bâbord vu de dessus : bord de la coque, poutre AV, pièce d'angle et son nez, pylône, mât et semelle prévus, cotes M4, M5, M6, M7 et D6",
               ''.join(b))


# ---------- croquis 2a : coupe en travers au pied de mât, vue de l'avant (1 px/mm) ----------
B_, BO, ZL = 192.52, 35.0, 278.25


def zpont(y):
    t = (y - 1000) / B_
    return ZL + BO * math.sqrt(max(0.0, 1 - t * t))


def croquis_coupe():
    X = lambda y: 60 + (y - 807.5)
    Y = lambda z: 360 - (z - 230)
    b = []
    ys = [807.5 + 385 * i / 60 for i in range(61)]
    top = ' '.join(f'{X(y):.1f},{Y(zpont(y)):.1f}' for y in ys)
    b.append(f'<polygon class="hu" points="{X(807.5) + 4:.1f},398 {top} {X(1192.5) - 4:.1f},398"/>')
    b.append(f'<polyline class="ed" points="{top}"/>')
    b.append(f'<rect class="li" x="{X(1192.5):.1f}" y="{Y(ZL) - 8:.1f}" width="7" height="16" rx="2"/>')
    b.append(f'<rect class="li" x="{X(807.5) - 7:.1f}" y="{Y(ZL) - 8:.1f}" width="7" height="16" rx="2"/>')
    # poutre AV derrière, pièce d'angle, pylône
    b.append(f'<rect class="mt" x="0" y="{Y(570.5):.1f}" width="{X(925):.1f}" height="62" rx="20"/>')
    b.append(f'<rect class="mt" x="{X(965):.1f}" y="{Y(499.5):.1f}" width="70" height="{Y(zpont(1000)) - Y(499.5):.1f}"/>')
    b.append(f'<rect class="dk" x="{X(925):.1f}" y="{Y(579.5):.1f}" width="125" height="80" rx="8"/>')
    b.append(f'<rect class="dk" x="{X(1040):.1f}" y="{Y(574.5):.1f}" width="82" height="70" rx="22"/>')
    b.append(txt(8, Y(508.5) + 20, 'poutre AV (derrière)', 'lb sm'))
    b.append(txt(X(1050) + 2, Y(499.5) + 20, "pièce d'angle", 'lb sm'))
    b.append(txt(X(965) - 6, 190, 'pylône', 'lb sm', 'end'))
    b.append(f'<line class="ax" x1="{X(1000):.1f}" y1="0" x2="{X(1000):.1f}" y2="398"/>')
    b.append(txt(X(1000) + 6, 300, 'axe', 'lb sm'))
    b.append(txt(515, 236, 'extérieur →', 'lb sm', 'end'))
    # V9
    xv = X(912)
    b.append(dim(xv, Y(570.5), xv, Y(zpont(912))))
    b.append(chip(xv - 30, 160, 'V9'))
    # M1
    b.append(ext(X(807.5), Y(ZL) + 10, X(807.5), 388))
    b.append(ext(X(1192.5), Y(ZL) + 10, X(1192.5), 388))
    b.append(dim(X(807.5), 380, X(1192.5), 380))
    b.append(chip(X(1000) + 40, 380, 'M1'))
    # appel du zoom
    b.append(f'<circle class="zo" cx="{X(1192.5) - 20:.1f}" cy="{Y(ZL) - 8:.1f}" r="34"/>')
    b.append(txt(X(1192.5) - 20, Y(ZL) - 50, 'zoom ci-contre', 'lb sm', 'middle'))
    return svg('b', '0 0 520 400', "Coupe en travers de la coque bâbord au pied de mât, vue de l'avant : largeur M1 et hauteur V9 de la poutre AV",
               ''.join(b))


# ---------- croquis 2b : zoom ×3 sur le bord du pont ----------
GAPS = [(10, 'T1'), (30, 'T2'), (60, 'T3'), (100, 'T4'), (150, 'T5')]


def croquis_zoom():
    X = lambda y: 20 + (y - 1030) * 3
    Y = lambda z: 230 - (z - 265) * 3
    b = []
    ys = [1030 + (1192.5 - 1030) * (1 - (1 - i / 60) ** 1.6) for i in range(61)]
    top = ' '.join(f'{X(y):.1f},{Y(zpont(y)):.1f}' for y in ys)
    b.append(f'<polygon class="hu" points="0,262 0,{Y(zpont(1023)):.1f} {top} {X(1192.5) - 3:.1f},262"/>')
    b.append(f'<polyline class="ed" points="0,{Y(zpont(1023)):.1f} {top}"/>')
    b.append(f'<rect class="li" x="{X(1192.5):.1f}" y="{Y(ZL) - 18:.1f}" width="21" height="36" rx="6"/>')
    yr = Y(zpont(1000))
    b.append(f'<line class="ru" x1="0" y1="{yr:.1f}" x2="636" y2="{yr:.1f}"/>')
    b.append(f'<rect class="bu" x="60" y="{yr - 22:.1f}" width="84" height="16" rx="8"/><circle class="bc" cx="102" cy="{yr - 14:.1f}" r="5"/>')
    b.append(txt(156, yr - 10, 'règle de niveau, posée sur le haut du bombé', 'lb sm'))
    xe = X(1192.5)
    b.append(f'<line class="ax" x1="{xe:.1f}" y1="{yr - 26:.1f}" x2="{xe:.1f}" y2="258"/>')
    b.append(txt(xe + 4, yr - 30, 'bord : point le plus large', 'lb sm', 'middle'))
    for d, t in GAPS:
        y = 1192.5 - d
        x = X(y)
        y1_ = Y(zpont(y)) - 1
        b.append(dim(x, yr + 1, x, y1_, 'c') if y1_ - yr > 16 else f'<line class="dm" x1="{x:.1f}" y1="{yr + 3:.1f}" x2="{x:.1f}" y2="{max(y1_, yr + 12):.1f}"/>')
        b.append(chip(x, 196, t))
        b.append(txt(x, 236, f'{d}', 'lb sm', 'middle'))
    b.append(txt(20, 256, 'distances en mm depuis le bord', 'lb sm'))
    # liston
    xl0, xl1 = X(1192.5), X(1192.5) + 21
    b.append(ext(xl0, Y(ZL) + 20, xl0, 252))
    b.append(ext(xl1, Y(ZL) + 20, xl1, 252))
    b.append(dim(xl0, 246, xl1, 246, 'c'))
    b.append(chip(xl1 + 30, 246, 'M2'))
    b.append(ext(xl1 + 2, Y(ZL) - 18, xl1 + 26, Y(ZL) - 18))
    b.append(ext(xl1 + 2, Y(ZL) + 18, xl1 + 26, Y(ZL) + 18))
    b.append(dim(xl1 + 20, Y(ZL) - 18, xl1 + 20, Y(ZL) + 18, 'c'))
    b.append(chip(xl1 + 54, Y(ZL), 'M3'))
    b.append(txt(xl1 + 8, Y(ZL) - 30, 'liston', 'lb sm'))
    return svg('c', '0 0 640 262', 'Zoom sur le bord du pont au pied de mât : jours T1 à T5 sous une règle de niveau, liston M2 et M3',
               ''.join(b))


# ---------- croquis 3 : haubans (schéma) ----------
def croquis_haubans():
    b = []
    hull = 'M20,170 C60,128 140,118 230,118 L740,118 L740,222 L230,222 C140,222 60,212 20,170 Z'
    b.append(f'<path class="hu" d="{hull}"/>')
    b.append('<path class="ed" d="M20,170 C60,128 140,118 230,118 L740,118"/>')
    b.append('<line class="ax" x1="20" y1="170" x2="740" y2="170"/>')
    b.append(txt(20, 30, '← étrave', 'lb b'))
    b.append(txt(236, 192, 'axe de la coque', 'lb sm'))
    # patte d'étrave
    b.append('<rect class="dk" x="40" y="164" width="34" height="12" rx="4"/><circle class="hl" cx="62" cy="170" r="3.5"/>')
    b.append(ext(20, 170, 20, 92))
    b.append(ext(62, 166, 62, 92))
    b.append(dim(20, 98, 62, 98, 'd'))
    b.append(chip(41, 76, 'H1'))
    b.append(txt(84, 160, "patte d'étrave", 'lb sm'))
    # poutre AV, pièce d'angle, pylône
    b.append('<rect class="mt" x="430" y="200" width="32" height="96"/>')
    b.append('<rect class="dk" x="418" y="146" width="56" height="70" rx="10"/>')
    b.append('<circle class="hid" cx="446" cy="170" r="13"/>')
    b.append('<line class="ax2" x1="446" y1="150" x2="446" y2="74"/>')
    b.append(txt(424, 290, 'poutre AV', 'lb sm', 'end'))
    # cadène
    b.append('<rect class="dk" x="566" y="128" width="28" height="12" rx="3"/><circle class="hl" cx="580" cy="134" r="3.5"/>')
    b.append(ext(580, 130, 580, 74))
    b.append(dim(446, 80, 580, 80, 'd'))
    b.append(chip(513, 62, 'H4'))
    b.append(txt(446, 58, 'axe du pylône', 'lb sm', 'middle'))
    b.append(ext(584, 134, 628, 134))
    b.append(dim(620, 118, 620, 134, 'd'))
    b.append(chip(648, 126, 'H5'))
    b.append(txt(600, 160, 'cadène', 'lb sm'))
    # détails de profil
    b.append('<g transform="translate(24,236)"><rect class="pv" x="0" y="0" width="210" height="62" rx="6"/>'
             '<line class="ed" x1="10" y1="48" x2="200" y2="48"/><rect class="dk" x="92" y="20" width="10" height="28"/>'
             '<circle class="hl" cx="97" cy="30" r="4"/>' + ext(102, 30, 132, 30) + dim(126, 30, 126, 48, 'd') +
             chip(156, 39, 'H2') + chip(56, 26, 'H3 Ø') + txt(10, 14, "patte d'étrave, de profil", 'lb sm') + '</g>')
    b.append('<g transform="translate(500,236)"><rect class="pv" x="0" y="0" width="226" height="62" rx="6"/>'
             '<line class="ed" x1="10" y1="48" x2="216" y2="48"/><path class="dk" d="M86,48 V30 A11,11 0 0 1 108,30 V48 Z"/>'
             '<circle class="hl" cx="97" cy="31" r="4"/>' + ext(102, 31, 140, 31) + dim(134, 31, 134, 48, 'd') +
             chip(164, 39, 'H6') + chip(52, 28, 'H7 Ø') + txt(10, 14, 'cadène, de profil', 'lb sm') + '</g>')
    return svg('d', '0 0 740 300', "Schéma d'une coque vue de dessus avec la patte d'étrave et la cadène, et leurs détails de profil : cotes H1 à H7",
               ''.join(b))


# ---------- croquis 4 : moteur Protruar 2.0 de profil (0,36 px/mm) ----------
def croquis_moteur():
    s = 0.36
    X = lambda x: 300 + x * s
    Y = lambda z: 40 + (455 - z) * s
    b = []
    # barre repliée
    b.append(f'<rect class="mo" x="{X(-119):.1f}" y="{Y(455):.1f}" width="{40 * s:.1f}" height="{315 * s:.1f}" rx="5"/>')
    b.append(txt(X(-79) + 6, Y(420), 'barre repliée', 'lb sm'))
    # tête
    b.append(f'<rect class="mo" x="{X(-129):.1f}" y="{Y(140):.1f}" width="{264 * s:.1f}" height="{140 * s:.1f}" rx="10"/>')
    b.append(txt(X(3), Y(70) + 4, 'tête', 'lw sm', 'middle'))
    # arbre
    b.append(f'<rect class="mo" x="{X(-15):.1f}" y="{Y(0):.1f}" width="{30 * s:.1f}" height="{900 * s:.1f}"/>')
    # bride et planche
    b.append(f'<rect class="dk" x="{X(-56):.1f}" y="{Y(-52):.1f}" width="{96 * s:.1f}" height="{164 * s:.1f}" rx="3"/>')
    b.append(f'<rect class="wd" x="{X(-96):.1f}" y="{Y(-100):.1f}" width="{40 * s:.1f}" height="{110 * s:.1f}"/>')
    b.append(txt(X(40) + 6, Y(-120), 'bride', 'lb sm'))
    b.append(txt(X(-96) - 6, Y(-200), 'planche', 'lb sm', 'end'))
    # nacelle, hélice, aileron
    b.append(f'<rect class="mo" x="{X(-159):.1f}" y="{Y(-900):.1f}" width="{220 * s:.1f}" height="{100 * s:.1f}" rx="{50 * s:.1f}"/>')
    b.append(f'<rect class="dk" x="{X(66):.1f}" y="{Y(-950 + 118):.1f}" width="{25 * s:.1f}" height="{236 * s:.1f}" rx="4"/>')
    b.append(f'<path class="mo" d="M{X(-50):.1f},{Y(-1000):.1f} L{X(10):.1f},{Y(-1000):.1f} L{X(4):.1f},{Y(-1090):.1f} L{X(-40):.1f},{Y(-1090):.1f} Z"/>')
    b.append(txt(X(-159) - 6, Y(-900) - 4, 'nacelle', 'lb sm', 'end'))
    b.append(txt(X(91) + 6, Y(-950 + 118) - 4, 'hélice', 'lb sm'))
    b.append(txt(X(10) + 8, Y(-1080), 'aileron', 'lb sm'))
    b.append(txt(X(15) + 6, Y(-500), 'arbre', 'lb sm'))
    b.append(f'<line class="ax" x1="{X(0):.1f}" y1="{Y(140) - 6:.1f}" x2="{X(0):.1f}" y2="{Y(-1090) + 4:.1f}"/>')
    # cotes
    b.append(dim(X(-129), Y(140) - 12, X(135), Y(140) - 12, 'e'))
    b.append(chip(X(135) + 24, Y(140) - 12, 'E1'))
    b.append(dim(X(-129) - 18, Y(140), X(-129) - 18, Y(0), 'e'))
    b.append(chip(X(-129) - 44, Y(70), 'E3'))
    b.append(dim(X(-129), Y(0) + 10, X(0), Y(0) + 10, 'e'))
    b.append(chip(X(-129) - 30, Y(0) + 14, 'E4'))
    b.append(ext(X(-99) + 8, Y(455), X(330), Y(455)))
    b.append(ext(X(135), Y(0), X(330), Y(0)))
    b.append(dim(X(320), Y(455), X(320), Y(0), 'e'))
    b.append(chip(X(320) + 26, Y(230), 'E5'))
    b.append(ext(X(40), Y(-52), X(200), Y(-52)))
    b.append(dim(X(186), Y(0), X(186), Y(-52), 'e'))
    b.append(chip(X(186) + 26, Y(-26), 'E6'))
    b.append(ext(X(40), Y(-216), X(140), Y(-216)))
    b.append(dim(X(126), Y(-52), X(126), Y(-216), 'e'))
    b.append(chip(X(126) + 26, Y(-162), 'E7'))
    b.append(ext(X(-56), Y(-216), X(-56), Y(-216) + 18))
    b.append(dim(X(-56), Y(-216) + 12, X(0), Y(-216) + 12, 'e'))
    b.append(chip(X(-56) - 28, Y(-216) + 16, 'E8'))
    b.append(chip(X(-96) - 34, Y(-130), 'E9'))
    b.append(ext(X(140), Y(-216), X(330), Y(-216)))
    b.append(ext(X(61), Y(-950), X(330), Y(-950)))
    b.append(dim(X(320), Y(-216), X(320), Y(-950), 'e'))
    b.append(chip(X(320) + 30, Y(-583), 'E10'))
    b.append(chip(X(15) + 30, Y(-380), 'E11 Ø'))
    b.append(dim(X(-159) - 16, Y(-900), X(-159) - 16, Y(-1000), 'e'))
    b.append(chip(X(-159) - 52, Y(-950), 'E12'))
    b.append(ext(X(-159), Y(-950), X(-159), 640))
    b.append(ext(X(61), Y(-950), X(61), 640))
    b.append(dim(X(-159), 634, X(61), 634, 'e'))
    b.append(chip(X(-50), 650, 'E13'))
    b.append(ext(X(91), Y(-832), X(160), Y(-832)))
    b.append(ext(X(91), Y(-1068), X(160), Y(-1068)))
    b.append(dim(X(150), Y(-832), X(150), Y(-1068), 'e'))
    b.append(chip(X(150) + 30, Y(-1010), 'E14'))
    b.append(ext(X(-50), Y(-1000), X(-90), Y(-1000)))
    b.append(ext(X(-40), Y(-1090), X(-90), Y(-1090)))
    b.append(dim(X(-80), Y(-1000), X(-80), Y(-1090), 'e'))
    b.append(chip(X(-80) - 32, Y(-1045) + 4, 'E15'))
    # vue de dessus de la tête
    b.append('<g transform="translate(24,26)">' + txt(0, 0, 'tête vue de dessus', 'lb sm') +
             f'<rect class="mo" x="0" y="10" width="{264 * s:.1f}" height="{120 * s:.1f}" rx="10"/>' +
             dim(264 * s + 12, 10, 264 * s + 12, 10 + 120 * s, 'e') + chip(264 * s + 40, 10 + 60 * s, 'E2') + '</g>')
    return svg('e', '0 0 560 668', 'Moteur Haswing Protruar 2.0 de profil, schématique : tête, barre repliée, bride, planche, arbre, nacelle, hélice et aileron, cotes E1 à E15',
               ''.join(b), 'm')


# ---------- croquis 5 : barre et safrans (schéma, vue de dessus) ----------
def croquis_barre():
    b = []
    b.append('<path class="hu" d="M0,40 L610,40 L610,110 L0,110 Z"/>')
    b.append('<line class="ed" x1="0" y1="40" x2="610" y2="40"/>')
    b.append('<line class="ed" x1="610" y1="40" x2="610" y2="110"/>')
    b.append('<line class="ax" x1="0" y1="75" x2="720" y2="75"/>')
    b.append(txt(6, 30, '← étrave', 'lb b'))
    b.append(txt(616, 132, 'tableau', 'lb sm'))
    b.append('<rect class="mt" x="150" y="110" width="34" height="210"/>')
    b.append('<rect class="dk" x="140" y="56" width="54" height="56" rx="8"/>')
    b.append(txt(142, 316, 'poutre AR', 'lb sm', 'end'))
    b.append('<rect class="tr" x="0" y="112" width="150" height="208"/>')
    b.append(txt(10, 300, 'trampoline', 'lb sm'))
    b.append('<line class="ax" x1="0" y1="304" x2="740" y2="304"/>')
    b.append(txt(736, 296, 'axe du bateau', 'lb sm', 'end'))
    # safran, bras, barre d'accouplement
    b.append('<rect class="dk" x="626" y="71" width="94" height="8" rx="3"/>')
    b.append('<circle class="hl" cx="636" cy="75" r="5"/>')
    b.append(txt(668, 64, 'safran', 'lb sm'))
    b.append('<line class="ar" x1="636" y1="75" x2="330" y2="134"/>')
    b.append('<circle class="hl" cx="330" cy="134" r="6"/>')
    b.append('<line class="ar" x1="330" y1="134" x2="330" y2="320"/>')
    b.append(txt(338, 230, "barre d'accouplement →", 'lb sm'))
    b.append(txt(338, 248, "vers l'autre coque", 'lb sm'))
    b.append(txt(470, 136, 'bras de barre', 'lb sm'))
    # cotes
    b.append(ext(636, 80, 636, 20))
    b.append(dim(610, 24, 636, 24, 'f'))
    b.append(chip(670, 18, 'S1'))
    b.append(ext(330, 140, 330, 186))
    b.append(dim(184, 180, 330, 180, 'f'))
    b.append(chip(257, 162, 'S2'))
    b.append(chip(300, 286, 'S3'))
    b.append(chip(590, 60, 'S4'))
    b.append(ext(336, 134, 370, 134))
    b.append(dim(362, 75, 362, 134, 'f'))
    b.append(chip(392, 104, 'S5'))
    b.append(chip(368, 270, 'S6'))
    a0, a1, R_ = math.radians(152), math.radians(186), 150
    p0 = (636 + R_ * math.cos(a0), 75 + R_ * math.sin(a0)); p1 = (636 + R_ * math.cos(a1), 75 + R_ * math.sin(a1))
    b.append(f'<line class="ex" x1="636" y1="75" x2="{636 + 330 * math.cos(a0):.1f}" y2="{75 + 330 * math.sin(a0):.1f}"/>')
    b.append(f'<path class="dm" d="M{p0[0]:.1f},{p0[1]:.1f} A{R_},{R_} 0 0 1 {p1[0]:.1f},{p1[1]:.1f}" marker-start="url(#fs)" marker-end="url(#fe)"/>')
    b.append(chip(p1[0] - 26, p1[1] - 6, 'S7'))
    return svg('f', '0 0 740 330', "Schéma de l'arrière vu de dessus : poutre AR, tableau, safran, bras de barre et barre d'accouplement, cotes S1 à S7",
               ''.join(b))


# ---------- données des cotes ----------
BT = ('bd', 'td')
SECTIONS = [
    dict(id='A', n='1', prio='Essentiel avant de découper', titre="Pied de mât et pièce d'angle AV",
         intro="Les mâts ont reculé de 194 : l'axe du pied est maintenant à 60 mm devant la face avant de la poutre AV, au bord de la coque, "
               "juste à l'extérieur du nez de la pièce d'angle. Le mât Ø 60 doit y loger avec au moins 10 mm de jeu.",
         figs=[croquis_dessus()],
         rows=[
             ('M4', "Bord de la coque → flanc extérieur du nez de la pièce d'angle",
              "Vu de dessus, à l'équerre du bord, liston non compris. Le mât loge là : en dessous de 70, sa place est à revoir.", '71', 'mm', BT),
             ('M5', "Dépassement du nez de la pièce d'angle devant la poutre AV",
              "Le long du longeron, du bout du nez jusqu'au nez arrondi de la poutre.", '50', 'mm', BT),
             ('M6', "Bord de la coque → face extérieure du pylône",
              "Le pylône est le tube vertical sous la pièce d'angle. La semelle du mât passe à 10 de lui.", '159', 'mm', BT),
             ('M7', "Ø du pylône", "Pied à coulisse, sous la pièce d'angle.", '70', 'mm', None),
             ('D6', "Nez à nez des pièces d'angle AV et AR", "Le long du longeron, du bout du nez AV au bout du nez AR.", '2 269', 'mm', BT),
         ]),
    dict(id='B', n='2', prio='Essentiel avant de découper', titre='Pont au pied de mât et poutre AV',
         intro="La semelle du mât et le renfort de pont se collent sur le bombé, au bord de la coque : ces cotes donnent l'épaisseur du "
               "bourrage (3 à 34 mm dans le modèle). Toutes au droit du pied de mât, 60 mm devant la face avant de la poutre AV.",
         figs=[croquis_coupe(), croquis_zoom()],
         rows=[
             ('M1', 'Largeur de la coque au niveau du pont, bord à bord', 'Au point le plus large, liston non compris.', '385', 'mm', BT),
             ('T1', 'Jour sous la règle à 10 mm du bord',
              "Règle droite tenue de niveau (bulle) en travers, posée sur le haut du bombé. Le bord est l'aplomb du point le plus large.", '24', 'mm', BT),
             ('T2', 'Jour sous la règle à 30 mm du bord', '', '16', 'mm', BT),
             ('T3', 'Jour sous la règle à 60 mm du bord', '', '10', 'mm', BT),
             ('T4', 'Jour sous la règle à 100 mm du bord', '', '4', 'mm', BT),
             ('T5', 'Jour sous la règle à 150 mm du bord', '', '1', 'mm', BT),
             ('M2', 'Liston : saillie hors de la coque', "Pas dessiné dans le modèle.", '–', 'mm', None),
             ('M3', 'Liston : hauteur', '', '–', 'mm', None),
             ('V9', "Dessus de la poutre AV au-dessus du pont, au ras de la pièce d'angle", '', '261', 'mm', BT),
             ('L1', 'Pente du pont en long, au pied de mât',
              "Inclinomètre posé sur le pont dans l'axe de la coque, + si le pont monte vers l'étrave. Modèle : valeur avec Q = 0.", '+0,6', '°', BT),
             ('Q', 'Inclinomètre sur le longeron, au même moment', 'Même convention que L1.', '0', '°', None),
             ('R', 'Gîte de la plateforme', 'Inclinomètre en travers sur la poutre AR, + si bâbord plus bas. Sert à corriger T1 à T5.', '0', '°', None),
         ]),
    dict(id='C', n='3', prio='Avant de couper les haubans', titre="Haubans : ferrures d'origine",
         intro="Les haubans des colliers vont aux pattes d'étrave et aux cadènes d'origine ; leurs positions viennent des photos. "
               "Un seul bord suffit : note en remarque si l'autre diffère.",
         figs=[croquis_haubans()],
         rows=[
             ('H1', "Patte d'étrave : pointe de l'étrave → centre du trou", 'Vu de dessus, dans l\'axe de la coque.', '50', 'mm', None),
             ('H2', "Patte d'étrave : centre du trou au-dessus du pont", '', '12', 'mm', None),
             ('H3', "Patte d'étrave : Ø du trou", '', '–', 'mm', None),
             ('H4', 'Cadène : axe du pylône AV → centre du trou', 'Le long du bord de la coque.', '620', 'mm', None),
             ('H5', 'Cadène : centre du trou → bord de la coque', 'Vu de dessus.', '12', 'mm', None),
             ('H6', 'Cadène : centre du trou au-dessus du pont', '', '8', 'mm', None),
             ('H7', 'Cadène : Ø du trou', '', '–', 'mm', None),
         ]),
    dict(id='D', n='4', lat=True, prio='Sur le moteur, quand tu l\'as sous la main', titre='Moteur Haswing Protruar 2.0',
         intro="Le puits, la levée de 674 et les jeux viennent du schéma du manuel ; les largeurs et la bride sont estimées. "
               "Arbre descendu à fond, barre repliée à la verticale.",
         figs=[croquis_moteur()],
         rows=[
             ('E1', 'Tête : longueur hors tout', 'De l\'avant à l\'arrière, dans l\'axe du bateau.', '264', 'mm', None),
             ('E2', 'Tête : largeur', '', '120', 'mm', None),
             ('E3', 'Tête : hauteur, barre non comprise', '', '140', 'mm', None),
             ('E4', "Avant de la tête → axe de l'arbre", '', '129', 'mm', None),
             ('E5', 'Barre repliée : sommet au-dessus du bas de la tête', '', '455', 'mm', None),
             ('E6', 'Bas de la tête → haut de la bride', '', '52', 'mm', None),
             ('E7', 'Bride : hauteur', '', '164', 'mm', None),
             ('E8', "Bride : face d'appui sur la planche → axe de l'arbre", '', '56', 'mm', None),
             ('E9', 'Bride : ouverture maxi', 'Épaisseur de planche acceptée ; la planche PL fait 40.', '40', 'mm', None),
             ('E10', 'Bas de la bride → axe de la nacelle', '', '734', 'mm', None),
             ('E11', "Arbre : Ø", '', '30', 'mm', None),
             ('E12', 'Nacelle : Ø', '', '100', 'mm', None),
             ('E13', 'Nacelle : longueur', '', '220', 'mm', None),
             ('E14', 'Hélice : Ø', '', '236', 'mm', None),
             ('E15', 'Aileron : profondeur sous la nacelle', '', '90', 'mm', None),
         ]),
    dict(id='E', n='5', prio="Plus tard, pour l'écoute et la tente", titre='Barre et safrans',
         intro="La barre d'accouplement est à 20–30 cm derrière la poutre AR ; le reste du système de barre n'est pas encore dessiné. "
               "Un seul bord, barre au milieu.",
         figs=[croquis_barre()],
         rows=[
             ('S1', 'Axe des safrans : distance derrière le tableau', '', '70', 'mm', None),
             ('S2', "Barre d'accouplement : distance derrière la poutre AR", 'Depuis la face arrière de la poutre.', '200–300', 'mm', None),
             ('S3', "Barre d'accouplement : hauteur au-dessus du trampoline", '', '–', 'mm', None),
             ('S4', "Bras de barre : axe du safran → rotule de la barre d'accouplement", '', '–', 'mm', None),
             ('S5', "Rotule : écart à l'axe de la coque, vers l'intérieur", '', '–', 'mm', None),
             ('S6', "Barre d'accouplement : longueur, rotule à rotule", '', '–', 'mm', None),
             ('S7', 'Débattement : angle maxi de la barre, de chaque bord', '', '–', '°', None),
         ]),
]

COTE = {'bd': 'bâbord', 'td': 'tribord'}


def champ(key, unit, lab, cote=None):
    cap = f'<span class="cote">{COTE[cote]}</span>' if cote else ''
    return (f'<label class="f" for="f-{key}">{cap}<span class="in"><input id="f-{key}" data-k="{key}" type="text" inputmode="decimal" '
            f'autocomplete="off" spellcheck="false" aria-label="{esc(lab)}"><span class="u">{esc(unit)}</span></span></label>')


def ligne(sec, r):
    rid, lab, aide, mod, unit, cotes = r
    if cotes:
        champs = ''.join(champ(f'{rid}-{c}', unit, f'{rid} {COTE[c]}, en {unit}', c) for c in cotes)
    else:
        champs = champ(rid, unit, f'{rid}, en {unit}')
    a = f'<p class="aide">{esc(aide)}</p>' if aide else ''
    return (f'<div class="row" data-sec="{sec}"><span class="chip">{esc(rid)}</span>'
            f'<div class="lib"><p class="t">{esc(lab)}</p>{a}</div>'
            f'<p class="mod"><span class="k">modèle</span>{esc(mod)}{"" if mod == "–" else (unit if unit == "°" else " " + unit)}</p>'
            f'<div class="champs{" deux" if cotes else ""}">{champs}</div></div>')


def section(S):
    figs = ''.join(f'<figure>{f}</figure>' for f in S['figs'])
    rows = ''.join(ligne(S['id'], r) for r in S['rows'])
    n = sum(len(r[5]) if r[5] else 1 for r in S['rows'])
    return f'''<section class="sec{' lat' if S.get('lat') else ''}" id="s{S['id']}" aria-labelledby="h{S['id']}">
  <header class="sh"><span class="num">{S['n']}</span><div><p class="prio">{esc(S['prio'])}</p><h2 id="h{S['id']}">{esc(S['titre'])}</h2></div>
  <p class="cpt" data-cpt="{S['id']}">0 / {n}</p></header>
  <p class="intro">{esc(S['intro'])}</p>
  <div class="corps"><div class="figs n{len(S['figs'])}">{figs}</div>
  <div class="rows">{rows}</div></div>
  <div class="extra">
    <label class="rq" for="rq-{S['id']}"><span class="k">Remarques</span><textarea id="rq-{S['id']}" data-rq="{S['id']}" rows="2" placeholder="Ce qui ne colle pas au croquis, une cote douteuse, l'autre bord…"></textarea></label>
    <div class="ph" data-ph="{S['id']}"><div class="phh"><span class="k">Photos</span>
      <label class="btn sec2" data-up="{S['id']}" hidden><input type="file" accept="image/*" multiple data-file="{S['id']}">Ajouter des photos</label></div>
      <div class="thumbs" data-thumbs="{S['id']}"></div></div>
  </div>
</section>'''


NTOT = sum(sum(len(r[5]) if r[5] else 1 for r in S['rows']) for S in SECTIONS)
META = {S['id']: dict(n=S['n'], titre=S['titre'], rows=[[r[0], r[1], r[3], r[4], list(r[5]) if r[5] else None] for r in S['rows']]) for S in SECTIONS}

CSS = '''
/* Fiche de relevé d'atelier : papier gris-vert, pastilles jaunes des photos annotées, croquis cotés au trait bleu */
:root{--paper:#EEF1F0;--sheet:#F9FAF9;--ink:#15232A;--ink2:#4B5B62;--rule:#C7D0D3;--accent:#0E7C95;--warn:#B8650E;--ok:#2E7D4F;
  --hull:#DCE3E5;--hulle:#33454F;--metal:#9AA5AA;--dark:#2A3439;--wood:#C9A06A;--dim:#0E7C95;--field:#FFFFFF;
  --f-disp:"Barlow Semi Condensed","Arial Narrow",system-ui,sans-serif;--f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#101A1E;--sheet:#152228;--ink:#DDE6E9;--ink2:#9DB0B7;--rule:#2C3C43;--accent:#5CC3DB;--warn:#E3A35A;--ok:#6BC18F;
  --hull:#23333A;--hulle:#9DB0B7;--metal:#55646A;--dark:#0A1114;--wood:#8C6B42;--dim:#5CC3DB;--field:#0D161A;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#101A1E;--sheet:#152228;--ink:#DDE6E9;--ink2:#9DB0B7;--rule:#2C3C43;--accent:#5CC3DB;--warn:#E3A35A;--ok:#6BC18F;
  --hull:#23333A;--hulle:#9DB0B7;--metal:#55646A;--dark:#0A1114;--wood:#8C6B42;--dim:#5CC3DB;--field:#0D161A;color-scheme:dark}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 var(--f-body);padding-inline:16px;padding-block:28px 120px}
.wrap{max-width:1080px;margin:0 auto;display:grid;gap:44px}
h1,h2{font-family:var(--f-disp);font-weight:700;line-height:1.12;letter-spacing:.01em;text-wrap:balance;margin:0}
h1{font-size:clamp(32px,5.4vw,48px)} h2{font-size:clamp(22px,3.2vw,28px)}
p{margin:0}
.k,.eyebrow,.prio,.cote,.mod .k{font:500 11px/1.2 var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--ink2)}
.eyebrow{font-size:12px}
header.top{display:grid;gap:14px;border-bottom:1px solid var(--rule);padding-bottom:24px}
.lead{max-width:70ch;color:var(--ink2)}
.kit{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:12px 28px;max-width:900px}
.kit div{display:grid;gap:4px}
.kit p{color:var(--ink2);font-size:14px}
.sec{display:grid;gap:18px}
.sh{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:14px;align-items:end;border-top:3px solid var(--ink);padding-top:14px}
.num{font:700 40px/0.9 var(--f-disp);color:var(--ink)}
.cpt{font:500 14px/1 var(--f-mono);color:var(--ink2);font-variant-numeric:tabular-nums;white-space:nowrap}
.cpt.plein{color:var(--ok)}
.intro{max-width:74ch;color:var(--ink2)}
.figs{display:grid;gap:14px}
.figs.n2{grid-template-columns:minmax(0,52fr) minmax(0,64fr)}
@media (max-width:820px){.figs.n2{grid-template-columns:minmax(0,1fr)}}
figure{margin:0;background:var(--sheet);border:1px solid var(--rule);padding:10px;min-width:0}
figure svg{display:block;width:100%;height:auto;max-height:640px}
svg text{font-family:var(--f-body)}
svg .hu{fill:var(--hull);stroke:none}
svg .ed{fill:none;stroke:var(--hulle);stroke-width:2}
svg .li{fill:var(--dark)}
svg .ax,svg .ax2{stroke:var(--ink2);stroke-width:1;stroke-dasharray:6 4;fill:none}
svg .st{stroke:var(--accent);stroke-width:1.2;stroke-dasharray:10 4 2 4}
svg .pv{fill:none;stroke:var(--ink2);stroke-width:1.2;stroke-dasharray:5 4}
svg .mt{fill:var(--metal)}
svg .dk{fill:var(--dark)}
svg .wd{fill:var(--wood)}
svg .mo{fill:var(--metal);stroke:var(--hulle);stroke-width:1}
svg .hid{fill:none;stroke:#E8EDEE;stroke-width:1.4;stroke-dasharray:4 3}
svg .hl{fill:var(--sheet);stroke:var(--ink);stroke-width:1}
svg .ms{fill:var(--accent);fill-opacity:.18;stroke:var(--accent);stroke-width:2;stroke-dasharray:6 3}
svg .zo{fill:none;stroke:var(--accent);stroke-width:1.5;stroke-dasharray:4 3}
svg .ru{stroke:var(--ink);stroke-width:6;stroke-linecap:round}
svg .bu{fill:#E9F5C9;stroke:var(--ink);stroke-width:1}
svg .bc{fill:#7FB800}
svg .tr{fill:var(--accent);fill-opacity:.07}
svg .ar{stroke:var(--ink);stroke-width:5;stroke-linecap:round}
svg .dm{stroke:var(--dim);stroke-width:1.6;fill:none}
svg .ex{stroke:var(--dim);stroke-width:.9;stroke-dasharray:3 3}
svg .ah{fill:var(--dim)}
svg .lb{fill:var(--ink2);font-size:13px}
svg .lb.sm{font-size:12px}
svg .lb.b{font-weight:600;fill:var(--ink)}
svg .lw{fill:#EEF2F3;font-size:12px}
svg .sc rect{fill:#FFD400;stroke:#141414;stroke-width:2}
svg .sc text{fill:#141414;font:700 13px var(--f-mono)}
.rows{display:grid;border-top:1px solid var(--rule)}
.corps{display:grid;gap:18px}
.row{display:grid;grid-template-columns:62px minmax(0,1fr) 96px 284px;gap:6px 16px;align-items:center;padding:12px 0;border-bottom:1px solid var(--rule)}
@media (min-width:900px){.lat .corps{grid-template-columns:minmax(0,380px) minmax(0,1fr);gap:28px;align-items:start}
  .lat .figs{position:sticky;top:calc(env(safe-area-inset-top,0px) + 12px)}
  .lat .row{grid-template-columns:56px minmax(0,1fr) 84px 150px}}
.chip{justify-self:start;background:#FFD400;color:#141414;font:700 14px/1 var(--f-mono);padding:5px 7px;border:2px solid #141414;border-radius:7px;white-space:nowrap}
.lib{min-width:0;display:grid;gap:2px}
.lib .t{font-weight:500}
.aide{color:var(--ink2);font-size:13.5px;max-width:62ch}
.mod{font:500 15px/1.2 var(--f-mono);color:var(--ink2);font-variant-numeric:tabular-nums;display:grid;gap:3px;text-align:right}
.champs{display:flex;gap:10px;justify-content:flex-start;flex-wrap:wrap}
.f{display:grid;gap:3px}
.cote{font-size:10.5px}
.in{display:flex;align-items:center;gap:6px}
input[data-k]{font:500 16px/1.2 var(--f-mono);width:6.2em;padding:8px 9px;border:1px solid var(--rule);border-radius:5px;background:var(--field);color:var(--ink);text-align:right;font-variant-numeric:tabular-nums}
input[data-k]:focus-visible,textarea:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
input[data-k][data-s="ok"]{border-color:var(--ok);box-shadow:inset 3px 0 0 var(--ok)}
input[data-k][data-s="att"]{border-color:var(--warn)}
input[data-k][data-s="err"]{border-color:var(--warn);box-shadow:inset 3px 0 0 var(--warn)}
input[readonly],textarea[readonly]{opacity:.75}
.u{font:400 12px var(--f-mono);color:var(--ink2);min-width:1.6em}
@media (max-width:640px){
  .row,.lat .row{grid-template-columns:64px minmax(0,1fr);}
  .mod{font-size:14px}
  figure{overflow-x:auto}
  figure svg.w{min-width:600px}
  .row .mod{grid-column:1/2;text-align:left;align-self:start}
  .row .champs{grid-column:2/3;justify-content:flex-start}
}
.extra{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}
@media (max-width:720px){.extra{grid-template-columns:minmax(0,1fr)}}
.rq{display:grid;gap:6px}
textarea{font:15px/1.45 var(--f-body);width:100%;box-sizing:border-box;min-height:4.2em;padding:9px 10px;border:1px solid var(--rule);border-radius:5px;background:var(--field);color:var(--ink);resize:vertical}
.ph{display:grid;gap:8px;align-content:start}
.phh{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px}
.thumb{position:relative;border:1px solid var(--rule);background:var(--sheet)}
.thumb img{display:block;width:100%;aspect-ratio:4/3;object-fit:cover}
.thumb button{position:absolute;top:4px;right:4px;font:600 12px/1 var(--f-body);padding:5px 7px;border-radius:4px;border:1px solid #141414;background:#F9FAF9;color:#141414;cursor:pointer}
.thumb button.conf{background:#B8650E;color:#fff;border-color:#B8650E}
.thumbs .vide{font-size:13px;color:var(--ink2)}
.btn{font:600 14px/1 var(--f-body);padding:10px 14px;border-radius:6px;border:2px solid #141414;background:#FFD400;color:#141414;cursor:pointer;display:inline-flex;align-items:center;gap:8px}
.btn.sec2{background:transparent;color:var(--ink);border-color:var(--ink)}
.btn input[type=file]{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.btn:focus-within,.btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.barre{position:fixed;left:0;right:0;bottom:0;padding:10px 16px calc(10px + env(safe-area-inset-bottom,0px));background:var(--sheet);border-top:1px solid var(--rule);display:flex;gap:10px 18px;align-items:center;justify-content:center;flex-wrap:wrap;z-index:5}
.barre .tot{font:600 15px var(--f-mono);font-variant-numeric:tabular-nums}
#etat{font:400 13px var(--f-mono);color:var(--ink2);max-width:46ch}
#etat.warn{color:var(--warn)}
.sortie{display:grid;gap:8px}
#sortie{width:100%;box-sizing:border-box;min-height:8em;font:13px/1.5 var(--f-mono);background:var(--sheet);color:var(--ink);border:1px solid var(--rule);padding:10px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
'''

JS = r'''
const META = __META__;
const NTOT = __NTOT__;
const ins = [...document.querySelectorAll('input[data-k]')];
const byK = Object.fromEntries(ins.map(i => [i.dataset.k, i]));
const rqs = [...document.querySelectorAll('textarea[data-rq]')];
const byRq = Object.fromEntries(rqs.map(t => [t.dataset.rq, t]));
const etat = document.getElementById('etat');
let db = null, assets = null, lectureSeule = false, local = false;
const minuteurs = {}, chaines = {}, enCours = {};
const LS = 'cotes-manquantes-hc16';

function dire(t, warn) { etat.textContent = t; etat.classList.toggle('warn', !!warn); }
function heure() { return new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'}); }

function compter() {
  let tot = 0;
  for (const s of Object.keys(META)) {
    const mine = ins.filter(i => i.closest('.row').dataset.sec === s);
    const n = mine.filter(i => i.value.trim()).length; tot += n;
    const c = document.querySelector(`[data-cpt="${s}"]`);
    c.textContent = `${n} / ${mine.length}`; c.classList.toggle('plein', n === mine.length);
  }
  document.getElementById('tot').textContent = `${tot} / ${NTOT} cotes saisies`;
  document.getElementById('sortie').value = texte();
}

function texte() {
  const L = [];
  for (const [s, m] of Object.entries(META)) {
    const lignes = [];
    for (const [rid, lab, mod, u, cotes] of m.rows) {
      const ks = cotes ? cotes.map(c => [rid + '-' + c, c === 'bd' ? ' bâbord' : ' tribord']) : [[rid, '']];
      for (const [k, suf] of ks) {
        const v = (byK[k] && byK[k].value.trim()) || '';
        if (v) lignes.push(`${rid}${suf} (${lab}) : ${v} ${u} [modèle ${mod}]`);
      }
    }
    const r = byRq[s] && byRq[s].value.trim();
    if (r) lignes.push(`Remarques : ${r}`);
    if (lignes.length) L.push(`${m.n} · ${m.titre}`, ...lignes, '');
  }
  return L.length ? 'Cotes manquantes HC16\n\n' + L.join('\n').trim() : '';
}

function localSauver() {
  try { const o = {}; ins.forEach(i => { if (i.value.trim()) o[i.dataset.k] = i.value; }); rqs.forEach(t => { if (t.value.trim()) o['rq-' + t.dataset.rq] = t.value; });
        localStorage.setItem(LS, JSON.stringify(o)); } catch (e) {}
}
function localCharger() {
  try { const o = JSON.parse(localStorage.getItem(LS) || '{}');
        ins.forEach(i => { if (o[i.dataset.k] != null && !i.value) i.value = o[i.dataset.k]; });
        rqs.forEach(t => { if (o['rq-' + t.dataset.rq] != null && !t.value) t.value = o['rq-' + t.dataset.rq]; }); } catch (e) {}
}

function passerLectureSeule() {
  if (lectureSeule) return; lectureSeule = true;
  ins.forEach(i => i.readOnly = true); rqs.forEach(t => t.readOnly = true);
  document.querySelectorAll('[data-up]').forEach(b => b.hidden = true);
  dire('Lecture seule : ce lien ne permet pas d\'enregistrer. « Copier le texte » reste possible.', true);
}

function ecrire(chemin, corps, marque) {
  enCours[chemin] = (enCours[chemin] || 0) + 1;
  chaines[chemin] = (chaines[chemin] || Promise.resolve()).then(async () => {
    const ref = db.doc(chemin);
    if (corps === null) await ref.delete(); else await ref.set(corps);
  }).then(() => { marque && marque('ok'); dire(`Enregistré à ${heure()}`); },
          e => { marque && marque('err');
                 if (e && (e.code === 'invalid_argument' || e.code === 'not_granted')) passerLectureSeule();
                 else dire('Pas enregistré (réseau ?) : la valeur reste dans la case, réessaie ou copie le texte.', true); })
    .finally(() => { enCours[chemin]--; });
}

function surSaisie(i) {
  compter();
  if (local || !db) { localSauver(); return; }
  if (lectureSeule) return;
  const k = i.dataset.k; i.dataset.s = 'att'; dire('Enregistrement…');
  clearTimeout(minuteurs[k]);
  minuteurs[k] = setTimeout(() => {
    const v = i.value.trim();
    ecrire('releves/' + k, v ? {v, at: new Date().toISOString()} : null, s => { i.dataset.s = v ? s : ''; });
  }, 700);
}
function surRemarque(t) {
  compter();
  if (local || !db) { localSauver(); return; }
  if (lectureSeule) return;
  const s = t.dataset.rq; dire('Enregistrement…');
  clearTimeout(minuteurs['rq' + s]);
  minuteurs['rq' + s] = setTimeout(() => {
    const v = t.value.trim();
    ecrire('remarques/' + s, v ? {t: v, at: new Date().toISOString()} : null);
  }, 900);
}
ins.forEach(i => i.addEventListener('input', () => surSaisie(i)));
rqs.forEach(t => t.addEventListener('input', () => surRemarque(t)));

document.getElementById('copier').addEventListener('click', () => {
  const t = texte();
  if (!t) { dire('Aucune cote saisie pour l\'instant.'); return; }
  navigator.clipboard.writeText(t).then(() => dire('Texte copié : colle-le dans la conversation.'))
    .catch(() => { const s = document.getElementById('sortie'); s.focus(); s.select(); dire('Texte sélectionné ci-dessous : copie-le à la main.'); });
});

// ----- photos -----
let photos = [];
function rendrePhotos() {
  for (const s of Object.keys(META)) {
    const box = document.querySelector(`[data-thumbs="${s}"]`);
    const mine = photos.filter(p => p.sec === s);
    box.replaceChildren();
    if (!mine.length) { const p = document.createElement('p'); p.className = 'vide'; p.textContent = 'Aucune photo.'; box.append(p); continue; }
    for (const p of mine) {
      const d = document.createElement('div'); d.className = 'thumb';
      const a = document.createElement('a'); a.href = '/_blob/' + p.asset; a.target = '_blank'; a.rel = 'noopener';
      const im = document.createElement('img'); im.src = '/_blob/' + p.asset; im.alt = 'Photo de relevé, section ' + META[s].n; im.loading = 'lazy';
      a.append(im); d.append(a);
      if (assets && !lectureSeule) {
        const b = document.createElement('button'); b.type = 'button'; b.textContent = 'Retirer';
        b.addEventListener('click', async () => {
          if (!b.classList.contains('conf')) { b.classList.add('conf'); b.textContent = 'Confirmer'; setTimeout(() => { b.classList.remove('conf'); b.textContent = 'Retirer'; }, 4000); return; }
          b.disabled = true;
          try { await db.doc('photos/' + p.id).delete(); await assets.delete(p.asset); dire('Photo retirée.'); }
          catch (e) { dire('La photo n\'a pas pu être retirée.', true); b.disabled = false; }
        });
        d.append(b);
      }
      box.append(d);
    }
  }
}
async function reduire(f) {
  try {
    const url = URL.createObjectURL(f);
    const im = await new Promise((ok, ko) => { const i = new Image(); i.onload = () => ok(i); i.onerror = ko; i.src = url; });
    const k = Math.min(1, 2000 / Math.max(im.naturalWidth, im.naturalHeight));
    const c = document.createElement('canvas'); c.width = Math.round(im.naturalWidth * k); c.height = Math.round(im.naturalHeight * k);
    c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
    return await new Promise(ok => c.toBlob(b => ok(b), 'image/jpeg', 0.85));
  } catch (e) { return f; }
}
document.querySelectorAll('input[data-file]').forEach(inp => inp.addEventListener('change', async () => {
  const s = inp.dataset.file, fs = [...inp.files]; inp.value = '';
  if (!fs.length || !assets || !db) return;
  let n = 0;
  for (const f of fs) {
    dire(`Envoi de la photo ${++n} / ${fs.length}…`);
    try {
      const bl = await reduire(f);
      const r = await assets.upload(bl, bl.type ? undefined : {type: 'image/jpeg'});
      await db.collection('photos').add({sec: s, asset: r.id, at: new Date().toISOString()});
    } catch (e) {
      const c = e && e.code;
      dire(c === 'unsupported_type' ? 'Format de photo refusé : prends-la en JPEG.' : c === 'too_large' ? 'Photo trop lourde.' :
           c === 'rate_limited' ? 'Trop d\'envois d\'un coup : réessaie dans un moment.' : 'La photo n\'a pas pu être envoyée.', true);
      return;
    }
  }
  dire(`Photos enregistrées à ${heure()}`);
}));

// ----- démarrage -----
compter(); rendrePhotos();
(async () => {
  const cl = window.claude;
  db = cl && cl.use ? await cl.use('db').catch(() => null) : null;
  if (!db) { local = true; localCharger(); compter(); dire('Hors de claude.ai : les cotes restent sur cet appareil. « Copier le texte » pour me les envoyer.', true); return; }
  dire('Connecté : chaque cote s\'enregistre dès que tu la tapes.');
  db.collection('releves').onSnapshot(snap => {
    for (const ch of snap.docChanges()) {
      const i = byK[ch.doc.id]; if (!i) continue;
      const busy = document.activeElement === i || enCours['releves/' + ch.doc.id] > 0 || i.dataset.s === 'att';
      if (busy) continue;
      if (ch.type === 'removed') { i.value = ''; i.dataset.s = ''; }
      else { const v = (ch.doc.data() || {}).v; if (typeof v === 'string' && v !== i.value) i.value = v; i.dataset.s = 'ok'; }
    }
    compter();
  }, e => dire('Lecture des cotes interrompue : recharge la page.', true));
  db.collection('remarques').onSnapshot(snap => {
    for (const ch of snap.docChanges()) {
      const t = byRq[ch.doc.id]; if (!t || document.activeElement === t || enCours['remarques/' + ch.doc.id] > 0) continue;
      t.value = ch.type === 'removed' ? '' : ((ch.doc.data() || {}).t || '');
    }
    compter();
  }, () => {});
  db.collection('photos').orderBy('at').onSnapshot(snap => {
    photos = snap.docs.map(d => Object.assign({id: d.id}, d.data())).filter(p => p.asset && META[p.sec]);
    rendrePhotos();
  }, () => {});
  assets = cl.use ? await cl.use('assets').catch(() => null) : null;
  if (assets && !lectureSeule) document.querySelectorAll('[data-up]').forEach(b => b.hidden = false);
  rendrePhotos();
})();
'''

HTML = f'''<title>Cotes manquantes HC16</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;700&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header class="top">
  <span class="eyebrow">Hobie 16 · gréement Rando · relevés sur le bateau · 06/10/2026</span>
  <h1>Cotes manquantes</h1>
  <p class="lead">Mâts reculés de 194 et coffre raccourci : il manque {NTOT} cotes à prendre sur le bateau et sur le moteur. Chaque cote a son repère jaune sur le croquis et la valeur actuelle du modèle, à confirmer ou corriger. Ce que tu tapes s'enregistre tout seul et je le lis directement ici ; les sections 1 et 2 bloquent la découpe de la semelle et du renfort de pont.</p>
  <div class="kit">
    <div><span class="k">Matériel</span><p>Mètre ruban, réglet ou pied à coulisse, équerre, règle droite de 50 cm, niveau à bulle, inclinomètre (téléphone), crayon.</p></div>
    <div><span class="k">Conventions</span><p>mm, angles en degrés. « Bord » = le point le plus large de la coque, liston non compris. Une cote douteuse : mets « ≈ » devant.</p></div>
  </div>
</header>
{''.join(section(S) for S in SECTIONS)}
<section class="sortie" aria-labelledby="hs"><h2 id="hs">Texte des relevés</h2><p class="intro">Le même contenu en texte, si tu préfères me l'envoyer dans la conversation.</p><textarea id="sortie" readonly aria-label="Relevés au format texte"></textarea></section>
</div>
<div class="barre"><span class="tot" id="tot">0 / {NTOT} cotes saisies</span><span id="etat">Chargement…</span><button class="btn" id="copier" type="button">Copier le texte</button></div>
<script>{JS.replace('__META__', json.dumps(META, ensure_ascii=False)).replace('__NTOT__', str(NTOT))}</script>
'''

open(OUT, 'w', encoding='utf-8').write(HTML)
print(OUT, len(HTML) // 1024, 'ko', NTOT, 'champs')
