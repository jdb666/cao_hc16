"""(JD 08/10 soir et 09/10) Textes de la page 3D : simplifications du gréement (trois haubans par collier, plus de haubans
de pied, semelle unique, emplanture à 3 crans), coffre en moustache (dessus et fond à 10°, fond à 25° vers l'avant),
hiloire, poteau de la glissière dans le coffre, capot arrière horizontal, joue d'un seul trait jusqu'au dossier (400),
trampoline étanche et dessous des bancs fermé, plus de yin-yang sur les joues, bordé en CP 4 + verre.
Chiffres repris des études (etudes/*.json). python3 plateforme/maj_textes_0910.py"""
import json, re
P = '/home/claude/cao/plateforme/gabarit.html'
s = open(P, encoding='utf-8').read()
E = '/home/claude/cao/etudes/'
VZ = json.load(open(E + 'vol_zones.json')); EF = json.load(open(E + 'efforts_colliers.json'))
FT = json.load(open(E + 'fiche_technique.json')); IN = json.load(open(E + 'infos_texte.json'))
PO = json.load(open('/home/claude/cao/plateforme/pose_coffre.json'))
HC = json.load(open(E + 'hauban_collier_poutre.json'))
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
mil = lambda n: f'{round(n):,}'.replace(',', ' ')
sy, gl = EF['synthese'], EF['glissiere']
assert gl.get('type') == 'poteau_coffre', gl
def jmin(pas):                                   # tubes carbone sur leurs semelles : ils s'y posent à la fin (contact voulu)
    v = [j[2] for q in pas for j in q['jeux'] if not j[0].startswith('pylone')]
    return min(v) if v else 12.0
PO['jeu_min_descente'], PO['jeu_min_fin'] = jmin(PO['pas'][:6]), jmin(PO['pas'][6:-1])
assert not any(q['contacts'] for q in PO['pas'][:-1]), 'contact pendant la pose'
assert all(c_[0].startswith('pylone') for c_ in PO['pas'][-1]['contacts']), PO['pas'][-1]['contacts']
HJ = {}
for d_, n_, _ in HC['en marche']['babord']:
    HJ.setdefault(n_, d_)
for d_, n_, _ in HC['relevé']['babord']:
    if n_.startswith('moteur_tete'):
        HJ.setdefault(n_ + '_releve', d_)
def hj(*noms):
    v = [HJ[n_] for n_ in noms if n_ in HJ]
    return fr(min(v), 0) if v else 'plus de 60'
L = IN['longueurs']
par_cote = VZ['hors_centre_L'] / 2

def li(label_debut, nouveau):
    """Remplace l'élément <li> qui commence par <li><b>label_debut ... </li>."""
    global s
    m = re.search(r'<li><b>' + re.escape(label_debut) + r'.*?</li>', s, re.S)
    assert m, label_debut
    s = s[:m.start()] + nouveau + s[m.end():]

def remplace(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a))
    s = s.replace(a, b)

def remplace_re(motif, b):
    global s
    s, k = re.subn(motif, b, s, count=1, flags=re.S)
    assert k == 1, motif[:80]

# ---------------------------------------------------------------- en-tête de la maquette
remplace_re(r'<p class="lead">Plateforme recalée.*?</p>', """<p class="lead">Plateforme recalée avec le coffre recalé dessus, bancs posés sur les longerons, moteur dans l'axe à relevage vertical (bouton sous la maquette) : le coffre ne touche le pont que par quatre tubes carbone posés sur les semelles des mâts ; sa face arrière s'appuie sur le nez de la poutre AV, sans jour. Coffre et bancs se posent d'une pièce, sans pièce en plus : les couples du coffre traversent C4 et font eux-mêmes les accroches ; le coffre descend, puis finit en diagonale vers l'arrière pour engager leur lèvre sous le nez de la poutre ; les couples des bancs se posent sur les longerons. On brêle ensuite le coffre sous la poutre, en diagonale jusqu'au pied du pilier de martingale, et on lace les bancs sous la toile. <b>Coffre en moustache</b> (JD 09/10) : vu de face, dessus et fond remontent à 10° vers les joues ; devant, le fond remonte à 25° pour ouvrir les vagues et une <b>hiloire</b> en haut de l'arrondi renvoie l'eau sur les côtés ; <b>trampoline étanche</b>, dessous des bancs fermé sur les longerons ; joues d'un seul trait de la pointe au dossier, 400 au-dessus de l'assise. <b>Gréement indépendant du coffre</b> (JD 06/10) : mâts, colliers, tube et haubans tiennent seuls ; <b>trois haubans par collier</b>, plus de haubans au pied du mât (JD 08/10 soir) ; chaque collier tourne sur le tube, au-dessus du coffre, et la cale de l'emplanture change de trou (3 crans) pour régler la quête. Le tube repose à chaque bout sur un <b>poteau carbone logé dans le coffre</b> (JD 09/10). Mâts reculés de 194 (pied à x 1 960) : leur CV est celui du HC16 d'origine ; côtés du coffre raccourcis d'autant (JD 06/10). Coffre raccourci devant, au ras des joues, avec un petit coffre à ancre devant le puits ; <b>deux batteries 24 V 50 Ah dans des accoudoirs étanches au bout des bancs</b>, <b>caissons de rangement</b> de chaque côté du moteur, sous un capot horizontal, <b>trappes dans C4</b> pour les compartiments extérieurs ; bancs renforcés (JD 08/10). Voiles réglables sous la maquette : enroulement de chaque voile, choqué, amures, point d'écoute sur la poutre AR ou sur le flotteur ; livardes en tube carbone droit, rangées debout contre la joue, devant le mât, dès que la voile est roulée. Tout le bordé en CP 4 + verre (JD 09/10).</p>""")

# ---------------------------------------------------------------- emplanture à 3 crans, semelle unique
remplace('<tr><td>Emplanture</td><td class="n">joues CP 10 × 40, 180</td>', '<tr><td>Emplanture</td><td class="n">joues CP 10 × 40, 140</td>')
remplace("Deux joues de CP 10, 180 × 40, collées sur la semelle à 31 l'une de l'autre, congés et verre-époxy ; cinq trous Ø 8 tous les 20,",
         "Deux joues de CP 10, 140 × 40, collées sur la semelle à 31 l'une de l'autre, congés et verre-époxy ; trois trous Ø 8 tous les 20 (JD 08/10 soir, cinq avant),")
remplace('<td class="n">5,8 · 4,4 · <b>3,0</b> · 1,6 · 0,2°</td>', '<td class="n">4,4 · <b>3,0</b> · 1,6°</td>')
remplace("dessous du collier 10 au-dessus du haut des joues.</td>",
         "dessous du collier à z 1 132, 47 au-dessus du haut de la joue (1 085 depuis le 09/10).</td>")
remplace("puis une semelle CP plate sur bourrage époxy, perpendiculaire au mât.",
         "puis une semelle CP plate sur bourrage époxy, perpendiculaire au mât, une seule par bord pour le mât et les deux tubes du coffre (JD 08/10 soir).")
remplace_re(r'<tr><td>Semelle du mât</td>.*?</tr>',
            """<tr><td>Semelle du mât et des tubes du coffre</td><td class="n">394 × 167, CP 18</td><td class="note">2 × CP 9 collés ; une seule par bord (JD 08/10 soir) : x 1 656 → 2 050, y 1 020 → 1 187 ; coin arrière intérieur échancré autour du pylône de la poutre AV (10 de jeu). Elle reçoit les joues de l'emplanture et, devant, les deux tubes carbone du coffre (x 1 716 et 1 816). Plus de pontets : plus de haubans au pied du mât.</td></tr>""")
remplace_re(r'<tr><td>Bourrage</td>.*?</tr>',
            """<tr><td>Bourrage</td><td class="n">3 → 39</td><td class="note">Aux coins : 9 AV intérieur, 39 AV extérieur, 3 AR intérieur, 29 AR extérieur ; environ 980 cm³ par semelle.</td></tr>""")
remplace_re(r'\s*<tr><td>Semelles des tubes du coffre</td>.*?</tr>', '')

# ---------------------------------------------------------------- collier : trois haubans, tube sur le poteau du coffre
remplace("devant, le direct AV (40 vers l'extérieur) et le croisé AV (30 vers l'intérieur) ;",
         "devant, le direct AV (40 vers l'extérieur) ; plus de croisé AV (JD 08/10 soir : trois haubans par collier) ;")
remplace("Dessous 10 au-dessus du haut des joues, 11 de la joue : le collier ne touche pas le coffre. C'est le <b>tube</b>, où il tourne sur son tourillon, "
         "qui repose sur le coffre, dans la <b>glissière</b> d'un sabot sur la joue (JD 08/10, voir « Glissière du tube »).</li>",
         "Dessous à z 1 132, 47 au-dessus du haut de la joue : le collier ne touche pas le coffre. C'est le <b>tube</b>, où il tourne sur son tourillon, "
         "qui repose sur le coffre, dans le bloc PEHD d'une potence portée par un poteau carbone logé dans le coffre (JD 09/10, voir « Glissière du tube »).</li>")

# ---------------------------------------------------------------- coffre
li('Largeur', f"""<li><b>Largeur</b> <span class="num">2 240</span>, joues à ±1 120 ; mâts à ±1 161, à 11 des joues : ils ne tiennent plus au coffre (JD 06/10). <b>Mâts reculés de 194</b> (pied à x 1 960) pour aligner le CV sur celui du HC16 ; les côtés du coffre ont reculé d'autant (JD 06/10). <b>Avant droit au ras des joues</b> (JD 07/10) : la pointe est à x <span class="num">1 584</span> sur toute la largeur. Au milieu, l'avant monte en quart d'ellipse jusqu'au dessus plat à z <span class="num">810</span> ; le plat va jusqu'à ±450 (JD 08/10) et se prolonge derrière x 1 760 par le <b>capot arrière horizontal</b>, jusqu'à C4 (JD 09/10). <b>Moustache</b> (JD 09/10) : au-delà de ±450, le dessus remonte à <b>10°</b> jusqu'aux joues (z 927 contre la joue, 1 122 avant) ; le fond, plat à z 270 sur ±150, remonte aussi à 10° (z 439 contre la joue) : vu de face, dessus et fond sont parallèles, comme une moustache, et le coffre est 487 de haut contre la joue. Volume du coffre <span class="num">{round(VZ['ext_L'])} L</span> à l'extérieur (469 L avant), {round(VZ['int_L'])} L à l'intérieur : {round(par_cote)} L de chaque côté au-delà des couples ±420 (compartiments extérieurs), {round(VZ['coffre_ancre_L'])} L de coffre à ancre, {round(VZ['puits_L'])} L de puits et, de chaque côté du moteur, un caisson de rangement de {round(VZ['rangement_L'])} L.</li>""")

li('Joues arrondies', """<li><b>Joues arrondies</b> (superellipses, JD 30/09), <b>d'un seul trait de la pointe au dossier</b> (JD 09/10, sans décrochage) : l'avant de la joue part de la pointe (x 1 584, tangente verticale) et monte sans cassure de courbure (exposant 2,3 ; 2 serait l'ellipse) jusqu'au haut du dossier, z <span class="num">1 085</span>, <b>400 au-dessus de l'assise</b>, atteint au droit du collier (x 1 999) tangent à l'horizontale ; plat jusqu'à C4 ; de C4, le dossier redescend en quart de superellipse (2,2) jusqu'au dessus de l'accoudoir, au bout du banc. Le coffre, lui, s'arrête à 927 contre la joue : la joue dépasse au-dessus. Le collier passe 47 au-dessus de la joue. Les haubans AV partent du collier, au-dessus de la joue : plus de plot. Plus de yin-yang sur les joues (JD 09/10).</li>""")

li('Capot arrière', f"""<li><b>Capot arrière</b> (JD 05/10 ; élargi le 08/10 ; <b>horizontal</b> le 09/10) : un capot fixe en CP 4 + verre prolonge le dessus plat à z <span class="num">810</span>, de x 1 760 jusqu'à C4, sur <b>±450</b> ; il garde la découpe de 140 de large pour la tête et la barre du moteur et porte, à plat, les trappes des deux caissons de rangement. Il descendait en pente jusqu'à 740 contre C4 pour laisser passer les haubans du collier vers la poutre AV ; depuis le recul des mâts, ils passent {hj('coffre_capot_arriere', 'coffre_coque')} au-dessus du capot à plat. Plus de joues triangulaires sur les côtés.</li>
    <li><b>Hiloire</b> (JD 09/10) : un brise-lames en CP 9 de 30 de haut, <b>penché à 45° vers l'avant</b>, en haut de l'arrondi de l'avant : droit en travers devant le capot et les trappes (x 1 755, de −460 à +460), puis en V vers l'arrière jusqu'aux joues (x 1 950, devant le poteau de la glissière). L'eau qui monte sur l'arrondi est arrêtée et renvoyée sur les côtés, au lieu de filer sur le capot et vers les bancs.</li>""")

remplace("fermés dessus par le capot : <span class=\"num\">42 L</span> chacun.",
         f"fermés dessus par le capot horizontal : <span class=\"num\">{round(VZ['rangement_L'])} L</span> chacun.")

li('Trappes de C4', f"""<li><b>Trappes de C4</b> (JD 08/10) : une seule par compartiment extérieur (de ±420 à la joue, {round(par_cote)} L chacun), la plus grande possible dans C4, à l'horizontale : <span class="num">320 × 117</span> (y ±690 → ±1 010, z 710 → 827), sous le dessus abaissé en moustache (JD 09/10, 398 × 188 avant) et 25 au-dessus de l'assise. Le couple ±850 passe derrière, dans le coffre, au milieu de la trappe : il porte le couvercle (la chute de C4, sur joint, deux tourniquets) avec un cadre de tasseaux. Le poteau de la glissière est dans le coffre, 10 après le bout extérieur de la trappe.</li>""")

li('Appuis sur le pont', """<li><b>Appuis sur le pont</b> : 4 tubes carbone Ø 40 × 2, deux par bord (x <span class="num">1 716</span> et <span class="num">1 816</span>, y ±1 066), posés sur la semelle du mât (une seule par bord depuis le 08/10 soir), à l'ancienne place du pied de mât ; leur haut, coupé à la pente du fond (z 517 devant, 469 derrière), porte sous une semelle CP 18 collée sur le fond contre la joue.</li>""")

remplace_re(r"aucun contact, jeu mini [\d,]+ à la fin de la course, [\d,]+ le reste du temps \(le jeu de découpe\)\.",
            f"aucun contact, jeu mini {fr(PO['jeu_min_fin'])} à la fin de la course, {fr(PO['jeu_min_descente'])} le reste du temps (le jeu de découpe).")
remplace_re(r'six brins en éventail \(<span class="num">[\d ]+, [\d ]+ et [\d ]+</span> de long',
            f"six brins en éventail (<span class=\"num\">{L['brelage_poutre_2']}, {L['brelage_poutre_1']} et {L['brelage_poutre_0']}</span> de long")

remplace("Fond des côtés en V à 14° (panneaux plans F1 et F2 du plan de découpe), à stratifier.",
         "Fond des côtés en V à 10° (moustache, JD 09/10), panneaux plans du plan de découpe, CP 4 + verre.")

li('Fond en pente', """<li><b>Fond en pente</b>, au-dessus du moteur relevé : z <span class="num">270</span> sur ±150 (le puits et ses parois) de x 1 860 à C4, sous l'aileron (274) et l'hélice (296) relevés, 20 plus haut qu'avant (JD 09/10) ; de là, il remonte à <span class="num">25°</span> vers l'avant jusqu'à la pointe (z ≈ 400 au milieu, ≈ 565 contre les joues) : c'est lui qui ouvre les vagues, 12° avant (JD 09/10 : « garder voire augmenter »). En travers, le fond remonte à <b>10°</b> du plat aux joues, comme le dessus : 105 au-dessus du pont à l'axe de chaque coque (x 1 900). Même pente partout : les panneaux de fond restent plans. Plus de haubans croisés sous le coffre (plus de haubans au pied du mât). Une seule ouverture : le bas du puits moteur, 256 × 300. Le bas du coffre protège aussi le trampoline des vagues qui passent dessous ; en cas d'enfournement, il porte.</li>""")

m = re.search(r'<li><b>Bancs</b>.*?</li>', s, re.S); assert m
b0 = m.group(0)
a_ = "Entre la toile et l'assise, 110 à 145 de haut, fermé côté extérieur, ouvert côté trampoline sous la lisse ; au-dessus des pièces d'angle AV, la joue reste dégagée."
assert b0.count(a_) == 1
b1 = b0.replace(a_, "Entre la toile et l'assise, 110 à 145 de haut, fermé côté extérieur, ouvert côté trampoline sous la lisse. <b>Fermé à l'eau</b> (JD 09/10) : "
                "trampoline en toile PVC <b>étanche</b> ; sous la joue, un <b>joint</b> néoprène 10 × 10 sur le longeron, du bout de la pièce d'angle AV (x 2 130) "
                "au bout du banc ; au-dessus de la pièce d'angle, où la joue est dégagée, une <b>tape</b> CP 6 contre la joue, de C4 à x 2 130, "
                "taillée au profil de la pièce d'angle et du longeron (1 de jeu), jusque sous l'assise. Joint et tape se posent une fois le coffre en place "
                "(ils gêneraient la fin de pose en diagonale) : l'eau qui passe sous le coffre ne remonte plus entre les poutres et le dessous du banc.")
s = s.replace(b0, b1)

li('Coffre à ancre', f"""<li><b>Coffre à ancre</b> devant le puits, à la place de la caisse de batterie (JD 07/10) : deux cloisons CP 6 à ±250, de l'avant du coffre à la cloison du puits (x 1 711) ; couvercle : le bordé central (±250, une seule pièce cintrée) au-dessus de z 450, de l'avant jusqu'au capot arrière (x 1 590 → 1 776), échancré au-dessus du puits ; ses bords portent sur des tasseaux collés le long des cloisons. Le grappin (370 × Ø 100 plié) est couché en travers sur le fond, contre la cloison du puits (z 386 → 486), avec son mouillage ; <span class="num">{round(VZ['coffre_ancre_L'])} L</span>.</li>""")

remplace("l'aileron descend à +274 : tout le bas du moteur est dans le puits, 24 au-dessus de son bord bas (z 250).",
         "l'aileron descend à +274 : tout le bas du moteur est dans le puits, au ras du fond (z 270, remonté de 20 le 09/10).")

cas = FT['cas']; H0 = cas['HC16, 2 équipiers près de la poutre AV (référence)']
r0 = cas['Rando, 2 équipiers, coffre vide']; r60 = cas['Rando, 2 équipiers + 60 kg au coffre']; r60b = cas["Rando, 2 équipiers + 60 kg sous l'arrière des bancs"]
hy = FT['hydro']
li('Assiette', f"""<li><b>Assiette</b> (fiche technique, JD 06–09/10) : calcul statique, au repos ; le plan Chevalier flotte à {round(hy['D0'])} kg ({fr(hy['kg_mm'])} kg par mm, ≈ {round(FT['mct'])} kg·m par degré vers 360 kg). À équipage égal, assis près de la poutre AV, la Rando a <span class="num">{fr(r0['assiette'] - H0['assiette'])}°</span> de plus sur le nez que le HC16, coffre vide (eau {'+' if r0['etrave'] - H0['etrave'] >= 0 else '−'} {abs(r0['etrave'] - H0['etrave'])} à l'étrave, {'+' if r0['tableau'] - H0['tableau'] >= 0 else '−'} {abs(r0['tableau'] - H0['tableau'])} au tableau) ; {fr(r60['assiette'] - H0['assiette'])}° avec 60 kg au coffre, {fr(r60b['assiette'] - H0['assiette'])}° si ces 60 kg vont sous l'arrière des bancs. Les batteries dans les accoudoirs, au bout des bancs, tirent l'arrière vers le bas. Point bas du coffre (puits, z 270) à {r0['garde_coffre']} au-dessus de l'eau calme coffre vide, {r60['garde_coffre']} avec 60 kg. En route, la vitesse enfonce l'arrière et la voile appuie sur le nez, autant pour les deux bateaux : le HC16 s'assied sur l'arrière, la Rando le fera moins. Ranger le lourd sous les bancs. Menu « coffre » sous la maquette (étude du 30/09, charge au CdG du coffre) ; pointillé dans la coupe du relevage.</li>""")

# ---------------------------------------------------------------- haubans : trois par collier
li('Haubans', f"""<li><b>Haubans</b> (<b>Ø 5</b> inox 1 × 19), pièces du gréement : ils tiennent les mâts par les colliers et ne touchent pas le coffre (JD 06/10). <b>Trois par collier</b> (JD 08/10 soir) : devant, le direct vers la patte d'étrave du même bord, 40 vers l'extérieur (il passe à 36 de la livarde rangée) ; sur la face extérieure, derrière le mât, le direct AR vers la cadène, à l'extérieur du mât ; en haut de la face intérieure, la diagonale vers le milieu de la poutre AV. Plus de croisés AV, plus de haubans au pied du mât : la semelle, collée sur le renfort, passe au pont l'effort du pied (≈ 2,4 kN). À la gîte maxi, le plus chargé monte à {fr(sy['T_max'] / 1000)} kN, {fr(sy['SF_hauban'])} fois moins que la rupture (19,5 kN). Après un changement de quête, on les retend. <b>Hauban du collier au milieu de la poutre AV</b> (JD 05/10), un par bord : de la ferrure en haut de la face intérieure du collier jusqu'à une ferrure sur le dessus de la poutre AV au milieu, 15 derrière son axe (là où était le pied de mât du HC16) ; <span class="num">{mil(L['hauban_coffre_collier_poutre_babord'])}</span> de long, 26° sous l'horizontale, presque en travers depuis que les mâts sont au droit de C4. Il passe au-dessus du coffre : {hj('moteur_puits')} au-dessus des parois du puits derrière C4, {hj('moteur_tete')} de la tête du moteur en marche, {hj('glissiere_bloc_babord', 'glissiere_potence_babord')} de la glissière, {hj('coffre_capot_arriere', 'coffre_coque')} du capot. Avec le tube entre les colliers, il tient les mâts en travers : le hauban sous le vent travaille quand le mât pousse son collier vers l'extérieur.</li>""")

# ---------------------------------------------------------------- tube et glissière
remplace("il repose à chaque bout dans la glissière d'un sabot (ci-dessous).", "il repose à chaque bout sur la potence d'un poteau logé dans le coffre (ci-dessous).")
remplace_re(r"Comprimé jusqu'à [\d,]+ kN à la gîte maxi, [\d,]+ fois sous son flambage \([\d,]+ kN\)\.",
            f"Comprimé jusqu'à {fr(sy['tube_max'] / 1000)} kN à la gîte maxi, {fr(sy['SF_tube'])} fois sous son flambage ({fr(EF['tube']['P_cr'] / 1000)} kN).")

li('Glissière du tube', f"""<li><b>Glissière du tube</b> (JD 08/10 ; poteau dans le coffre le 09/10) : les efforts verticaux des colliers passent par le <b>tube</b>, pas par le collier. À chaque bout, le tube repose dans un <b>bloc PEHD</b> où est creusé un berceau en U (0,5 de jeu, joues 11 sous l'axe : le tube s'enlève par le haut) ; il y glisse dans son axe et tourne ; le collier, sur son tourillon dans le bout du tube, reste libre de tourner autour quand on change de cran, et ne touche rien (3 du bloc). Le bloc est vissé sur une <b>potence</b> en CP collé (4 × CP 10, 40 de haut, de y 990 à 1 078) qui passe au-dessus de C4, du poteau jusque sous le tube : {fr(gl['porte_a_faux'])} de porte-à-faux. Le <b>poteau</b>, tube carbone <b>Ø 50 × 2,5</b>, est <b>dans le coffre</b>, à 3 devant C4 (axe x 1 988,5, y ±1 045) : il sort par le dessus, dans une <b>bague</b> CP 18 collée dessous, et descend jusqu'au toit de la poche de la pièce d'angle AV, posé sur une <b>cale coulée</b> en époxy chargée (coulée coffre en place, film de démoulage) ; {gl['L_poteau']} de long, douille de 20 dans la potence. Plus rien sur la joue ni sous l'assise. Efforts (haubans Ø 5, prétension 300 à 500 N ; gîte maxi : une coque décolle, équipage au rappel) : <span class="num">{fr(sy['V_reglage'][0] / 1000)} à {fr(sy['V_reglage'][1] / 1000)} kN</span> par collier au réglage, {fr(sy['V_max'] / 1000)} kN à la gîte maxi, {fr(sy['V_max_15'] / 1000)} kN avec × 1,5 ; à {fr(sy['V_max_15'] / 1000)} kN : poteau {round(gl['s_poteau_flexion'])} MPa en flexion ({gl['M_poteau']} N·m sous la potence ; à comparer à la fiche du tube carbone), {fr(gl['H_appuis'] / 1000)} kN à la bague et au pied, PEHD {fr(gl['p_pehd'])} MPa, potence {fr(gl['s_potence'], 0)} MPa (CP okoumé : ≈ 40 à la rupture), tourillon {round(gl['s_tourillon'])} MPa (alu), pièce d'angle {fr(gl['p_piece_angle'])} MPa. Le collier tend à piquer autour du tube ({sy['M_tangage_reglage'][0]} à {sy['M_tangage_reglage'][1]} N·m au réglage, {sy['M_tangage_max']} au plus) : c'est le mât, dans l'alésage, qui l'en empêche (≈ {fr(sy['F_bords_alesage_max'] / 1000)} kN aux bords), aidé par le frottement de l'enroulement.</li>""")

li('Finition', """<li><b>Finition</b> : coffre, joues, hiloire, assises, accoudoirs, capot et trappes peints en blanc ; couples, jambes, lisses, accroches, colliers, potences, bagues et poteaux des glissières, joints, supports de livarde, semelles et parois du puits en noir ; blocs PEHD blancs ; brêlage et laçage (Dyneema) bleus. <b>Yin-yang</b>, le dessin du bateau : Ø 360 sur chaque face des deux voiles, dans le coin du point d'écoute, au-dessus de la livarde : centre x 4 324, z 2 139, à 100 de la chute et 60 de la livarde ; il suit la toile quand on roule la voile. Plus sur les joues (JD 09/10). <b>Trampoline étanche</b> en toile PVC (JD 09/10 ; mesh blanc avant).</li>""")

li('Plan de découpe', """<li><b>Plan de découpe</b> refait sur ce coffre : tout le bordé (dessus, fond, C4, poches) en <b>CP 4 + verre</b> (JD 09/10) ; panneaux du bordé dépliés, pièces plates imbriquées sur des plaques de 2 500 × 1 220, DXF à l'échelle 1 (page séparée). Reste à refaire : la tente.</li>""")

remplace("Jeux : 36 au hauban direct AV, plus de 60 au croisé AV, 11 au bordé du coffre ;", "Jeux : 36 au hauban direct AV, 11 au bordé du coffre ;")

remplace("(poches à 4 de jeu, parois CP 6)", "(poches à 4 de jeu, parois CP 4 + verre)")

remplace("Tubes carbone : pylônes, livardes</span>", "Tubes carbone : pylônes, poteaux des glissières, livardes</span>")

# ---------------------------------------------------------------- noms courts du panneau de relevage
remplace("coffre_capot_arriere: 'capot', bras_tube_moteur: 'bras'}[n]", "coffre_capot_arriere: 'capot', bras_tube_moteur: 'bras', coffre_hiloire: 'hiloire'}[n]")

for mot in ('croisé AV (30', 'sabot sur la joue', 'z 250)', 'joues triangulaires (CP 4)', 'pontets des haubans du pied'):
    assert mot not in s, mot
open(P, 'w', encoding='utf-8').write(s)
print('ok', len(s))
