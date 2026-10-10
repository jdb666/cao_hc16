"""(JD 09/10 après-midi) Textes du book : plus de glissière (le tube repose à plat sur les potences, les haubans l'avancent
ou le reculent), coffre à ancre ouvert comme une poche (face avant remontée à z 650, évacuation dessous), puits du moteur sans
face arrière, ouvertures de C4 sans trappe, trampoline lacé au milieu, trappes jaunes, tente igloo derrière l'hiloire. python3 book/textes_book_0910b.py (après slides_0910b.py
et les études : efforts_colliers, vol_zones, tente, balayage_levee, decoupe3)"""
import json, re
S = '/home/claude/cao/book/deck/slides/'
E = '/home/claude/cao/etudes/'
VZ = json.load(open(E + 'vol_zones.json')); EF = json.load(open(E + 'efforts_colliers.json'))
BAL = json.load(open('/home/claude/cao/plateforme/balayage_levee.json'))
J = json.load(open('/home/claude/cao/plans/decoupe3.json'))
OC = json.load(open(E + 'infos_texte.json'))['geom']['_ouvertures_c4']
mil = lambda n: f'{round(n):,}'.replace(',', ' ')
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
sy, gl = EF['synthese'], EF['glissiere']
e0, sig = gl['porte_a_faux'], gl['s_poteau_flexion']
def rep(f, pairs):
    p = S + f; t = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert t.count(a) == 1, (f, a[:70], t.count(a))
        t = t.replace(a, b)
    open(p, 'w', encoding='utf-8').write(t)

rep('cover.html', [('coffre en moustache, hiloire, poteaux de glissière dans le coffre et trampoline étanche le 9 octobre',
                    'coffre en moustache, tube posé sur deux poteaux, poche à ancre et puits ouverts, tente igloo le 9 octobre')])
# ---------------------------------------------------------------- appui du tube (plus de glissière)
rep('d-glissiere.html', [
    ('Le tube des colliers repose sur deux poteaux, dans le coffre', 'Le tube des colliers posé à plat sur deux poteaux, dans le coffre'),
    ('>Poteau, potence et bloc PEHD<', '>Poteau carbone et potence<'),
    ('alt="Bout bâbord du tube des colliers : il repose dans le bloc PEHD vissé sur la potence, qui passe au-dessus de C4 et coiffe le poteau carbone sortant du dessus du coffre ; le collier tourne autour sans toucher"',
     'alt="Bout bâbord du tube des colliers : il repose à plat sur la potence, qui passe au-dessus de C4 et coiffe le poteau carbone sortant du dessus du coffre ; le collier tourne sur le tube sans toucher"'),
    ('alt="Coupes de la glissière : poteau carbone dans le coffre contre C4, bague sous le dessus, cale coulée sur le toit de la poche de la pièce d&#x27;angle, potence et bloc PEHD sous le bout du tube"',
     'alt="Coupes de l&#x27;appui du tube : poteau carbone dans le coffre contre C4, bague sous le dessus, cale coulée sur le toit de la poche de la pièce d&#x27;angle, potence sous le bout du tube"'),
])
t = open(S + 'd-glissiere.html', encoding='utf-8').read()
m = re.search(r"(<p style=\"position:absolute;left:128px;top:730px;[^\"]*\">)Ce n&#x27;est pas le collier qui porte.*?(</p>)", t, re.S)
assert m
txt = (f"Ce n&#x27;est pas le collier qui porte : c&#x27;est le tube Ø 50 × 2, dans lequel le collier tourne sur son tourillon. "
       f"Plus de glissière (JD 09/10) : le tube n&#x27;a ni à tourner ni à coulisser ; il repose à chaque bout à plat sur une potence CP (4 × CP 10) "
       f"qui passe au-dessus de C4, et ce sont les haubans qui l&#x27;avancent ou le reculent. La potence coiffe un poteau carbone Ø 50 × 2,5 logé "
       f"dans le coffre, à 3 devant C4 : il sort par le dessus (bague CP 18 collée dessous) et descend sur le toit de la poche de la pièce "
       f"d&#x27;angle AV, sur une cale coulée. Par collier : {fr(sy['V_reglage'][0] / 1000)} à {fr(sy['V_reglage'][1] / 1000)} kN au réglage, "
       f"{fr(sy['V_max'] / 1000)} kN à la gîte maxi ; à {fr(sy['V_max_15'] / 1000)} kN (× 1,5), poteau {round(sig)} MPa en flexion "
       f"({fr(e0)} de porte-à-faux ; {round(sig * (e0 - 20) / e0)} à {round(sig * (e0 + 20) / e0)} si le tube avance ou recule de 20), "
       f"{fr(gl['H_appuis'] / 1000)} kN à la bague et au pied, potence {fr(gl['s_potence'], 0)} MPa.")
t = t[:m.start()] + m.group(1) + txt + m.group(2) + t[m.end():]
open(S + 'd-glissiere.html', 'w', encoding='utf-8').write(t)
rep('d-collier.html', [("c&#x27;est le tube qui repose sur les poteaux des glissières." if "c&#x27;est le tube qui repose sur les poteaux des glissières." in open(S + 'd-collier.html', encoding='utf-8').read()
                        else "c'est le tube qui repose sur les poteaux des glissières.",
                        "c'est le tube qui repose, à plat, sur les potences des deux poteaux d'appui.")])
rep('d-moustache.html', [('mâts, tube des colliers et poteaux des glissières"', 'mâts, tube des colliers et poteaux d&#x27;appui"')])
rep('d-rangements.html', [
    ('>Caissons de rangement et trappes de C4<', '>Caissons de rangement, ouvertures de C4<'),
    ('>Trappe de C4, au-dessus du banc<', '>Ouverture de C4, au-dessus du banc<'),
    ('alt="C4, moitié bâbord vue de l&#x27;arrière : trappe de 320 × 117 au-dessus de l&#x27;assise, sous le dessus en moustache ; couples ±420 et ±850 derrière ; poteau de la glissière dans le coffre, au bout de la trappe"',
     'alt="C4, moitié bâbord vue de l&#x27;arrière : grande ouverture polygonale sans couvercle au-dessus de l&#x27;assise, sous le dessus en moustache ; couples ±420 et ±850 derrière ; poteau d&#x27;appui du tube dans le coffre, au bout de l&#x27;ouverture ; puits du moteur ouvert derrière"'),
    ("Dans C4, une trappe de 320 × 117 par compartiment extérieur (112 L de ±420 à la joue), 25 au-dessus de l&#x27;assise, sous le dessus abaissé ; le couple ±850, derrière, porte le couvercle.",
     f"Dans C4, plus de trappe (JD 09/10) : une grande ouverture polygonale par compartiment extérieur ({round(VZ['hors_centre_L'] / 2)} L de ±420 à la joue), sans couvercle, de 25 au-dessus des assises à 25 sous le haut de C4 : {mil(OC['y'][1] - OC['y'][0])} de large, {mil(OC['z_haut'][0] - OC['z_bas'])} à {mil(OC['z_haut'][1] - OC['z_bas'])} de haut, {fr(OC['aire_m2'], 2)} m² ; le couple ±850 passe derrière.")])
# ---------------------------------------------------------------- poche à ancre, puits ouvert, trampoline
rep('d-batterie.html', [(f"Devant le puits, deux cloisons à ±250 font un coffre à ancre de {round(VZ['coffre_ancre_L'])} L, fermé par un couvercle découpé dans le bordé avant.",
                         f"Devant le puits, deux cloisons à ±250 font une poche à ancre de {round(VZ['coffre_ancre_L'])} L, ouverte dessus, vidée par en dessous (page suivante).")])
rep('d-etanche.html', [('Trampoline en toile PVC étanche (mesh avant).',
                        "Trampoline en toile PVC étanche, en deux moitiés lacées au milieu dans la longueur : l&#x27;eau s&#x27;en va d&#x27;elle-même par l&#x27;arrière (mesh avant).")])
rep('s3.html', [("puis le coffre de près, sans le gréement : coffre à ancre, puits du moteur et ses deux caissons de rangement,",
                 "puis le coffre de près, sans le gréement, et par en dessous : poche à ancre, puits du moteur ouvert derrière et ses deux caissons de rangement,"),
                (">puits du moteur, ouvert dessous et dessus<", ">puits du moteur, ouvert dessous, dessus et derrière<")])
rep('sommaire.html', [(">Coffre transparent<", ">Coffre transparent, puis par en dessous<")])
rep('s3-cav.html', [("coffre à ancre devant le puits, son couvercle découpé dans le bordé ;", "poche à ancre devant le puits, ouverte au-dessus de z 650 ;")])
rep('s3-car.html', [("Couples-accroches au travers de C4.", "Couples-accroches au travers de C4 ; le puits du moteur est ouvert derrière, sur toute sa largeur.")])
rep('s3-cde.html', [("Une grande trappe dans C4 par compartiment extérieur ;", "Une grande ouverture dans C4 par compartiment extérieur, sans trappe ;"),
                    ("coffre à ancre devant le puits, de chaque côté", "poche à ancre ouverte devant le puits, de chaque côté"),
                    ("un seul trou dans le fond : le bas du puits, 256 × 300.",
                     "dans le fond, le bas du puits (256 × 300, ouvert aussi derrière) et les deux évacuations de la poche à ancre.")])
# jeux du moteur (balayage refait : puits ouvert derrière)
NOMJ = {'coffre_coque': 'le coffre', 'coffre_capot_arriere': 'la découpe du capot', 'moteur_puits': 'le puits', 'coffre_cloison_moteur': 'la cloison du puits',
        'poutre_av': 'la poutre AV', 'moteur_etrier': "l'étrier", 'moteur_bride': 'la bride', 'moteur_tableau': 'la planche', 'trampoline': 'le trampoline'}
NOMM = {'moteur_tete': 'la tête', 'moteur_helice': "l'hélice", 'moteur_nacelle': 'la nacelle', 'moteur_arbre': "l'arbre", 'moteur_barre': 'la barre', 'moteur_aileron': "l'aileron"}
def jeu_mini(r):
    j = [(v[0], v[1], v[2]) for c_, v in r['jeux'].items() if c_ not in ('tube', 'bride')]
    return min(j)
lv = BAL['levees']; j0, j1 = jeu_mini(lv[0]), jeu_mini(lv[-1])
phr = lambda j: f"Jeu mini ailleurs : {fr(j[0], 0)}, entre {NOMM.get(j[1], j[1])} et {NOMJ.get(j[2], j[2])}."
t = open(S + 's5-coupe.html', encoding='utf-8').read()
t2 = re.sub(r"Jeu mini ailleurs : [\d,]+, entre la tête et le coffre \(échancrure de C4\)\.", phr(j0), t, count=1)
t2 = re.sub(r"Jeu mini ailleurs : [\d,]+, entre l&#x27;hélice et le puits\.|Jeu mini ailleurs : [\d,]+, entre l'hélice et le puits\.", phr(j1).replace("'", '&#x27;') if '&#x27;' in t else phr(j1), t2, count=1)
assert t2 != t or (phr(j0) in t and phr(j1) in t), 's5-coupe'
open(S + 's5-coupe.html', 'w', encoding='utf-8').write(t2)
print('jeux moteur', j0, j1)
# ---------------------------------------------------------------- sommaire des détails, fabrication, points ouverts
rep('s6.html', [('>Pied de mât, collier sur le tube, poteaux de la glissière, emplanture<', '>Pied de mât, collier sur le tube, appui du tube, emplanture<'),
                ('>Bancs renforcés, laçage, dessous fermé à l&#x27;eau ; batteries dans les accoudoirs ; rangements<' if '&#x27;eau ; batteries' in open(S + 's6.html', encoding='utf-8').read()
                 else ">Bancs renforcés, laçage, dessous fermé à l'eau ; batteries dans les accoudoirs ; rangements<",
                 ">Bancs renforcés, laçage, dessous fermé à l'eau, tente igloo ; batteries, poche à ancre et puits ouverts ; rangements, ouvertures de C4<")])
pl = J['planches']
def demi(nom_):
    q = next((q for q in pl if (q.get('nom') or q.get('id')) == nom_), None)
    return q
rep('p-fab.html', [('potences des glissières CP 10.', "potences d'appui du tube CP 10."),
                   ('poteaux Ø 50 des glissières dans le dessus,', "poteaux Ø 50 d'appui du tube dans le dessus,"),
                   ('blocs PEHD et cales coulées des glissières ;', "cales coulées sous les poteaux d'appui ;"),
                   ('trampoline PVC étanche, joints néoprène 10 × 10 ;', 'trampoline PVC étanche lacé au milieu, joints néoprène 10 × 10 ; tente : toile, porte et jupes, 2 arceaux alu Ø 11 de 3,9 m ;')])
rep('p-demi.html', [('potences des glissières (GQ, 4 plis chacune)', "potences d'appui du tube (GQ, 4 plis chacune)"),
                    ('planche du moteur, potences des glissières, supports de livarde"', 'planche du moteur, potences d&#x27;appui du tube, supports de livarde"')])
rep('p-nom2.html', [('Intérieur du coffre, hiloire, glissières du tube, tapes', 'Intérieur du coffre, hiloire, appuis du tube, tapes')])
rep('fin.html', [("Coffre en moustache à 10°, fond à 25° vers l'avant, hiloire ; poteaux de glissière dans le coffre ; trampoline étanche et dessous des bancs fermé ; dossier à 400 ; bordé CP 4 + verre (09/10). Trois haubans par mât, semelle unique, emplanture à 3 crans (08/10 soir).",
                  "Tube posé à plat sur les potences, les haubans le déplacent (plus de glissière) ; poche à ancre ouverte, face avant à z 650 ; puits ouvert derrière ; ouvertures de C4 sans trappe ; trampoline lacé au milieu ; trappes jaunes ; tente igloo derrière l'hiloire (09/10 après-midi). Coffre en moustache, fond à 25°, hiloire ; poteaux d'appui dans le coffre ; bordé CP 4 + verre (09/10). Trois haubans par mât, semelle unique, emplanture à 3 crans (08/10 soir)."),
                 ("Tente igloo à refaire sur ce coffre ; semelle et bourrage recalés sur les cotes relevées.",
                  "Patron de la tente (toile, jupes, porte arrière, manchons des colliers) ; course du tube sur les potences ; semelle et bourrage recalés sur les cotes relevées.")])
print('ok')
