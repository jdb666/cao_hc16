"""(JD 08/10) Textes de la page 3D : caissons de rangement, trappes de C4, glissière du tube, bancs renforcés, batteries
dans les accoudoirs, haubans Ø 5. Chiffres repris des études (etudes/*.json). python3 plateforme/maj_textes_0810.py"""
import json, re
P = '/home/claude/cao/plateforme/gabarit.html'
s = open(P, encoding='utf-8').read()
E = '/home/claude/cao/etudes/'
VZ = json.load(open(E + 'vol_zones.json')); EF = json.load(open(E + 'efforts_colliers.json')); BR = json.load(open(E + 'banc_resistance.json'))
FT = json.load(open(E + 'fiche_technique.json')); IN = json.load(open(E + 'infos_texte.json'))
PO = json.load(open('/home/claude/cao/plateforme/pose_coffre.json'))
HC = json.load(open(E + 'hauban_collier_poutre.json'))
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
mil = lambda n: f'{round(n):,}'.replace(',', ' ')
sy = EF['synthese']; gl = EF['glissiere']
def jmin(pas):                                   # tubes carbone sur leurs semelles : ils s'y posent à la fin (contact voulu)
    v = [j[2] for q in pas for j in q['jeux'] if not j[0].startswith('pylone')]
    return min(v) if v else 12.0
PO['jeu_min_descente'], PO['jeu_min_fin'] = jmin(PO['pas'][:6]), jmin(PO['pas'][6:-1])
assert not any(q['contacts'] for q in PO['pas'][:-1]), 'contact pendant la pose'
assert all(c_[0].startswith('pylone') for c_ in PO['pas'][-1]['contacts']), PO['pas'][-1]['contacts']
HJ = {}
for d_, n_, _ in HC['en marche']['babord']:
    HJ.setdefault(n_, d_)
def hj(n_):
    return fr(HJ[n_], 0) if n_ in HJ else 'plus de 60'
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

# ---------------------------------------------------------------- en-tête de la maquette
remplace("<b>batterie 24 V 50 Ah dans un caisson sur l'avant du banc bâbord</b>, contre C4 (JD 07/10).",
         "<b>deux batteries 24 V 50 Ah dans des accoudoirs étanches au bout des bancs</b>, <b>caissons de rangement</b> de chaque côté du moteur, "
         "<b>trappes dans C4</b> pour les compartiments extérieurs ; le <b>tube des colliers repose sur les joues</b>, dans une glissière, et les bancs sont renforcés (JD 08/10).")

# ---------------------------------------------------------------- collier : le tube porte, pas le collier
remplace("Dessous 10 au-dessus du haut des joues, 11 de la joue : collier, tube, haubans et mâts forment un ensemble qui ne touche pas le coffre.</li>",
         "Dessous 10 au-dessus du haut des joues, 11 de la joue : le collier ne touche pas le coffre. C'est le <b>tube</b>, où il tourne sur son tourillon, "
         "qui repose sur le coffre, dans la <b>glissière</b> d'un sabot sur la joue (JD 08/10, voir « Glissière du tube »).</li>")

# ---------------------------------------------------------------- coffre
li('Largeur', f"""<li><b>Largeur</b> <span class="num">2 240</span>, joues à ±1 120 ; mâts à ±1 161, à 11 des joues : ils ne tiennent plus au coffre (JD 06/10). <b>Mâts reculés de 194</b> (pied à x 1 960) pour aligner le CV sur celui du HC16 ; les côtés du coffre ont reculé d'autant (JD 06/10). <b>Avant droit au ras des joues</b> (JD 07/10) : la pointe est à x <span class="num">1 584</span> sur toute la largeur. Au milieu, l'avant monte en quart d'ellipse jusqu'au dessus plat à z <span class="num">810</span> ; le <b>plat va jusqu'à ±450</b> (JD 08/10, ±360 avant) ; derrière x 1 760, <b>capot arrière en pente</b> jusqu'à C4 (z 740) pour les haubans du collier vers la poutre AV ; au-delà de ±450, le dessus remonte jusqu'en haut des joues. Volume du coffre <span class="num">{round(VZ['ext_L'])} L</span> à l'extérieur, {round(VZ['int_L'])} L à l'intérieur : {round(par_cote)} L de chaque côté au-delà des couples ±420 (compartiments extérieurs), {round(VZ['coffre_ancre_L'])} L de coffre à ancre, {round(VZ['puits_L'])} L de puits et, de chaque côté du moteur, un caisson de rangement de {round(VZ['rangement_L'])} L.</li>""")

li('Capot arrière', """<li><b>Capot arrière</b> (JD 05/10, élargi le 08/10) : un <b>capot fixe</b> en CP 6 descend en pente (15°) de z 810 à x 1 760 jusqu'à z <span class="num">740</span> contre C4, sur <b>±450</b>, fermé sur les côtés par deux joues triangulaires (CP 4) qui rejoignent les pans du dessus ; il garde la découpe de 140 de large pour la tête et la barre du moteur et porte les trappes des deux caissons de rangement. C4 est arasée à 740 au milieu, les couples ±420 et les parois du puits sous le capot. Plus de porte-à-faux au-dessus de la poutre AV.</li>
    <li><b>Caissons de rangement</b> (JD 08/10), de chaque côté du moteur : entre la paroi du puits (±134) et un <b>couple plein</b> CP 6 à <b>±420</b> (déplacé de ±331 pour les agrandir), de la cloison du puits, prolongée jusqu'au couple, à C4 ; fermés dessus par le capot : <span class="num">""" + str(round(VZ['rangement_L'])) + """ L</span> chacun. <b>Trappe de 205 × 250</b> découpée dans le capot (x 1 785 → 1 990, y ±150 → ±400) : la chute fait la trappe ; elle se pose sur un cadre de tasseaux 15 × 15 collé sous le capot, sur joint, tenue par deux tourniquets. Le couple ±420 fait aussi l'accroche de la poutre AV à cet endroit.</li>
    <li><b>Trappes de C4</b> (JD 08/10) : une seule par compartiment extérieur (de ±420 à la joue, """ + str(round(par_cote)) + """ L chacun), la plus grande possible dans C4, à l'horizontale : <span class="num">398 × 188</span> (y ±690 → ±1 088, z 710 → 898), sous le haut de C4 qui monte vers la joue (25 de bord) et 25 au-dessus de l'assise. Le couple ±850 passe derrière, dans le coffre, au milieu de la trappe : il porte le couvercle (la chute de C4, sur joint, deux tourniquets) avec un cadre de tasseaux. Le poteau de la glissière est à 33 derrière C4, devant le bout extérieur de la trappe : le couvercle se retire en le glissant vers l'intérieur.</li>""")

remplace("à y <span class=\"num\">±131, ±331, ±850</span> (parois du puits et couples ±331 en CP 6, couples ±850 en CP 9)",
         "à y <span class=\"num\">±131, ±420, ±850</span> (parois du puits et couples pleins ±420 en CP 6, couples ±850 en CP 9)")
remplace("six brins en éventail (<span class=\"num\">255, 390 et 855</span> de long à ±131, ±331 et ±850)",
         f"six brins en éventail (<span class=\"num\">{L['brelage_poutre_2']}, {L['brelage_poutre_1']} et {L['brelage_poutre_0']}</span> de long à ±131, ±420 et ±850)")
remplace("aucun contact, jeu mini 1,2 à la fin de la course, 2 le reste du temps (le jeu de découpe).",
         f"aucun contact, jeu mini {fr(PO['jeu_min_fin'])} à la fin de la course, {fr(PO['jeu_min_descente'])} le reste du temps (le jeu de découpe).")

remplace("à ±331, deux couples CP 6 de la cloison du puits à C4, évidés ;",
         "à ±420, deux <b>couples pleins</b> CP 6 de la cloison du puits à C4, côtés des caissons de rangement (JD 08/10) ;")
remplace("Fond des baies latérales : panneaux de 510 × 700 en V à 14°, à stratifier (ou CP 9). Les trappes de visite de C4 sont entre les couples, sous le haut de C4 : y ±500 → ±800, z 700 → 850.",
         "Fond des côtés en V à 14° (panneaux plans F1 et F2 du plan de découpe), à stratifier. Une trappe dans C4 par compartiment extérieur (voir « Trappes de C4 »).")

c2, a2 = BR['avant'], BR['renforce']
k2 = '2 assis côte à côte'; kb = 'pied sur la rive, entre couples'; kc = "pied sur la rive, au droit d'un couple"
li('Bancs', f"""<li><b>Bancs</b> : couples CP 9 à x <span class="num">2 160, 2 410, 2 680, 2 950, 3 212</span>, accrochés au longeron (profil + 2 mm) ; le premier est reculé de 24 pour que, pendant la fin de pose en diagonale, il passe au-dessus de la queue de la pièce d'angle. Plus de mâchoire : le couple se pose sur le longeron et le dessous reste ouvert ; c'est le laçage qui passe dessous. Un couple ne peut pas passer sous le longeron : il descend d'en haut, et la toile quitte le longeron par sa queue. Pose : coffre et bancs descendent d'une pièce et se mettent en place seuls, puis on brêle et on lace. Bancs liés au coffre : l'assise CP 9 (z 676 → 685, y 800 → 1 111) part de C4, où elle est collée, passe 79 au-dessus de la poutre et 96 au-dessus des pièces d'angle, et va jusqu'à x 3 218 (1 195 de long), accoudoir compris. L'assise porte sur C4, les accroches à ±850 et les couples, dont le bas passe à z 585, au-dessus de la toile. <b>Rangement sous l'assise</b> : la joue (dossier) descend jusqu'au longeron, à 3 du dessus du longeron ; c'est la <b>joue qui est entaillée</b> par le bas au droit de chaque couple, le couple reste entier. Entre la toile et l'assise, 110 à 145 de haut, fermé côté extérieur, ouvert côté trampoline sous la lisse ; au-dessus des pièces d'angle AV, la joue reste dégagée. <b>Renforcés pour s'asseoir à deux</b> (JD 08/10) : <b>lisse CP 9 × 40</b> collée sous la rive intérieure de l'assise, d'un couple à l'autre ; <b>couples pleins</b> (plus d'évidement) ; <b>jambe extérieure</b> du couple descendue à 115 sous l'axe du longeron, élargie jusqu'à y 1 162 et <b>doublée de deux joues CP 9</b> collées de part et d'autre (27 d'épaisseur) ; laçage en Dyneema. Résistance (étude du 08/10, CP okoumé, 100 kg par personne) : deux personnes assises (× 2 dynamique), assise {fr(a2[k2]['assise_SF'])} fois sous la rupture ; un pied sur la rive (× 1,5), {fr(a2[kb]['assise_SF'])} fois ({fr(c2[kb]['assise_SF'])} sans la lisse) ; âme des couples {fr(a2[kc]['ame_MPa'])} MPa au pire ({fr(c2[kc]['ame_MPa'])} évidés). Le banc ne peut que basculer vers l'intérieur autour de la queue du longeron : le laçage le retient, {fr(a2[kc]['T_lacage'] / 1000)} kN au pire ({fr(c2[kc]['T_lacage'] / 1000)} kN avant), jambe à {fr(a2[kc]['s_jambe'], 0)} MPa ({fr(c2[kc]['s_jambe'], 0)} avant, au-delà de la rupture), {fr(a2[kc]['rotation_deg'])}° et {fr(a2[kc]['rive_mm'])} à la rive. Dossier : 500 N en haut, solide mais souple (1,4 à 4,7 cm).</li>""")

zl = [IN['boites'][f'lacage_banc_{j}'][4] + 2.5 for j in range(5)]
li('Laçage des bancs', f"""<li><b>Laçage des bancs</b>, dans le plan de chaque couple : c'est lui qui tient les bancs sur les longerons et ferme le dessous. D'un longeron à l'autre sous la toile, aux <span class="num">cinq</span> couples : la ligne descend le long de la jambe extérieure du couple, passe sous son bas et file tout droit sous les longerons et la toile jusqu'à l'autre bord, sans jamais traverser la toile, à z ≈ {round(min(zl))}–{round(max(zl))}. <b>Dyneema Ø 5</b>, en double (JD 08/10) : raide, il laisse basculer le banc de moins de 1° ; {fr(L['lacage_banc_0'] / 1000)} m par couple. Le moteur ne va plus sous le trampoline : le couple 2 680 est lacé comme les autres.</li>""")

acc = IN['geom']['_accoudoirs']['babord']
li('Batterie sur le banc bâbord', f"""<li><b>Batteries dans les accoudoirs</b> (JD 08/10) : deux batteries LiFePO4 <b>24 V 50 Ah</b> en parallèle (100 Ah, 2,6 kWh ; type Sterling LH2450 : 260 × 165 × 210, 11 kg chacune), une dans chaque <b>accoudoir</b>, au bout des bancs : un caisson CP 6 étanche sur l'arrière du banc, x <span class="num">{mil(acc['x'][0])} → {mil(acc['x'][1])}</span>, sur toute la profondeur de l'assise (y 800 → 1 111), z 685 → 916. La batterie est en travers, sanglée sur l'assise, 5 de jeu devant et derrière, 15 dessus ; la joue fait l'extérieur, l'assise le fond ; face avant, face arrière et côté intérieur collés sur l'assise ; couvercle amovible sur joint, deux grenouillères ; l'arrondi du dossier finit sur le dessus de l'accoudoir. {round(VZ['accoudoir_L'])} L à l'intérieur. Câbles 25 mm² sous l'assise jusqu'à C4 (presse-étoupe), puis jusqu'au moteur, ≈ 2,2 m par batterie. Les 22 kg sont au bout des bancs, loin derrière : l'assiette y gagne. Plus de caisson sur l'avant des bancs.</li>""")

# ---------------------------------------------------------------- assiette (fiche technique)
cas = FT['cas']; H0 = cas['HC16, 2 équipiers près de la poutre AV (référence)']
r0 = cas['Rando, 2 équipiers, coffre vide']; r60 = cas['Rando, 2 équipiers + 60 kg au coffre']; r60b = cas["Rando, 2 équipiers + 60 kg sous l'arrière des bancs"]
hy = FT['hydro']
li('Assiette', f"""<li><b>Assiette</b> (fiche technique, JD 06–08/10) : calcul statique, au repos ; le plan Chevalier flotte à {round(hy['D0'])} kg ({fr(hy['kg_mm'])} kg par mm, ≈ {round(FT['mct'])} kg·m par degré vers 360 kg). À équipage égal, assis près de la poutre AV, la Rando a <span class="num">{fr(r0['assiette'] - H0['assiette'])}°</span> de plus sur le nez que le HC16, coffre vide (eau {'+' if r0['etrave'] - H0['etrave'] >= 0 else '−'} {abs(r0['etrave'] - H0['etrave'])} à l'étrave, {'+' if r0['tableau'] - H0['tableau'] >= 0 else '−'} {abs(r0['tableau'] - H0['tableau'])} au tableau) ; {fr(r60['assiette'] - H0['assiette'])}° avec 60 kg au coffre, {fr(r60b['assiette'] - H0['assiette'])}° si ces 60 kg vont sous l'arrière des bancs. Les batteries dans les accoudoirs, au bout des bancs, tirent l'arrière vers le bas. Point bas du coffre (puits, z 250) à {r0['garde_coffre']} au-dessus de l'eau calme coffre vide, {r60['garde_coffre']} avec 60 kg. En route, la vitesse enfonce l'arrière et la voile appuie sur le nez, autant pour les deux bateaux : le HC16 s'assied sur l'arrière, la Rando le fera moins. Ranger le lourd sous les bancs. Menu « coffre » sous la maquette (étude du 30/09, charge au CdG du coffre) ; pointillé dans la coupe du relevage.</li>""")

# ---------------------------------------------------------------- haubans Ø 5
remplace("<li><b>Haubans</b> (Ø 4), pièces du gréement :",
         f"<li><b>Haubans</b> (<b>Ø 5</b> inox 1 × 19, JD 08/10 : à la gîte maxi, le plus chargé monte à {fr(sy['T_max'] / 1000)} kN, {fr(sy['SF_hauban'])} fois moins que la rupture, 19,5 kN ; le Ø 4, 12,6 kN, était juste), pièces du gréement :")
remplace("<b>Hauban du collier au milieu de la poutre AV</b> (JD 05/10), un par bord, Ø 4 :", "<b>Hauban du collier au milieu de la poutre AV</b> (JD 05/10), un par bord, Ø 5 :")
remplace("Il passe au-dessus du coffre : 50 au-dessus du bordé, 53 au-dessus des joues du capot, 33 de la tête du moteur en marche, 21 au-dessus des parois du puits derrière C4.",
         f"Il passe au-dessus du coffre : {hj('moteur_puits')} au-dessus des parois du puits derrière C4, {hj('moteur_tete')} de la tête du moteur en marche, {hj('glissiere_berceau_babord')} du berceau de la glissière, {hj('coffre_capot_arriere')} du capot et de ses joues.")

# ---------------------------------------------------------------- tube et glissière
remplace("Il ne traverse pas le coffre : 22 au-dessus du haut des joues, derrière C4, plus de trous ni de manchons. La tête du moteur passe 15 devant lui ; il tient le moteur relevé par le bras rabattu vers l'avant sur l'arbre. La batterie sort de son caisson en dessous : 19 de jeu une fois levée de 230.</li>",
         f"""Il ne traverse pas le coffre : derrière C4, plus de trous ni de manchons ; il repose à chaque bout dans la glissière d'un sabot (ci-dessous). La tête du moteur passe 15 devant lui ; il tient le moteur relevé par le bras rabattu vers l'avant sur l'arbre. Comprimé jusqu'à {fr(sy['tube_max'] / 1000)} kN à la gîte maxi, {fr(sy['SF_tube'])} fois sous son flambage ({fr(EF['tube']['P_cr'] / 1000)} kN).</li>
    <li><b>Glissière du tube</b> (JD 08/10) : les efforts verticaux des colliers passent par le <b>tube</b>, pas par le collier. À chaque bout, le tube repose dans un <b>berceau en U garni de PEHD</b> (3), où il glisse dans son axe et tourne ; le collier, sur son tourillon dans le bout du tube, reste libre de tourner autour quand on change de cran, et ne touche rien (10 au-dessus du sabot, 3 du berceau). <b>Sabot</b> CP de 70 × 121 × 60 (6 × CP 10) au ras du haut de la joue, de y 990 à la joue, sous tout le tourillon (1 001 → 1 081) ; <b>berceau</b> 4 × CP 9 collé dessus, de 990 à 1 078, gorge au rayon du tube : ses joues s'arrêtent 11 sous l'axe, le tube s'enlève par le haut. Dessous, un <b>poteau caisson</b> de trois parois CP 9 (60 × 121) collé contre la joue descend jusqu'à l'assise, puis de l'assise au bas de la joue, sur une <b>cale coulée</b> en époxy chargée posée sur la pièce d'angle AV et le longeron (coulée coffre en place, film de démoulage). Efforts (haubans Ø 5, prétension 300 à 500 N ; gîte maxi : une coque décolle, équipage au rappel) : <span class="num">{fr(sy['V_reglage'][0] / 1000)} à {fr(sy['V_reglage'][1] / 1000)} kN</span> par collier au réglage, {fr(sy['V_max'] / 1000)} kN à la gîte maxi, {fr(sy['V_max_15'] / 1000)} kN avec × 1,5 ; à {fr(sy['V_max_15'] / 1000)} kN : PEHD {fr(gl['p_pehd'])} MPa, poteau {fr(gl['s_poteau'])} MPa, tourillon {round(gl['s_tourillon'])} MPa (alu), pièce d'angle {fr(gl['p_piece_angle'])} MPa. Le collier tend à piquer autour du tube ({sy['M_tangage_reglage'][0]} à {sy['M_tangage_reglage'][1]} N·m au réglage, {sy['M_tangage_max']} au plus) : c'est le mât, dans l'alésage, qui l'en empêche (≈ {fr(sy['F_bords_alesage_max'] / 1000)} kN aux bords), aidé par le frottement de l'enroulement.</li>""")

li('Finition', """<li><b>Finition</b> : coffre, joues, assises, accoudoirs et trappes peints en blanc ; couples, jambes, lisses, accroches, colliers, sabots, berceaux et poteaux des glissières, supports de livarde, semelles et parois du puits en noir ; garnitures PEHD blanches ; brêlage et laçage (Dyneema) bleus. <b>Yin-yang</b>, le dessin du bateau : Ø 360 sur la face extérieure de chaque joue, sur le dossier derrière le mât ; Ø 360 aussi sur chaque face des deux voiles, dans le coin du point d'écoute, au-dessus de la livarde : centre x 4 324, z 2 139, à 100 de la chute et 60 de la livarde. Il suit la toile quand on roule la voile. <b>Trampoline en mesh blanc</b>.</li>""")


# ---------------------------------------------------------------- noms courts du panneau de relevage
remplace("trampoline: 'trampoline', batterie_bac: 'bac', tube_colliers: 'tube', coffre_cloison_moteur: 'cloison', martingale_pilier: 'pilier de martingale'}[n]",
         "trampoline: 'trampoline', batterie_bac: 'bac', tube_colliers: 'tube', coffre_cloison_moteur: 'cloison', martingale_pilier: 'pilier de martingale', coffre_capot_arriere: 'capot', bras_tube_moteur: 'bras'}[n]")
remplace("/^lacage/.test(n) ? 'laçage' :", "/^lacage/.test(n) ? 'laçage' : /^glissiere/.test(n) ? 'glissière' : /^coffre_trappe/.test(n) ? 'trappe' : /^banc_/.test(n) ? 'banc' :")

open(P, 'w', encoding='utf-8').write(s)
print('ok', len(s))
