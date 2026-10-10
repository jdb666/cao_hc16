"""(JD 09/10 après-midi) Textes de la page 3D : plus de glissière (le collier tourne dans le tube, le tube repose à plat sur
la potence et les haubans l'avancent ou le reculent), coffre à ancre ouvert comme une poche avec évacuation dessous, trampoline
en deux moitiés lacées au milieu (l'eau s'en va par l'arrière), trappes en jaune, tente igloo sur deux arceaux diagonaux ;
(17 h) face avant du coffre à ancre remontée à z 650, puits du moteur sans face arrière ; (17 h 30) plus de trappes dans C4 : grandes
ouvertures polygonales au-dessus des assises ; (17 h 40) la tente couvre aussi le dessus du coffre, derrière l'hiloire.
Chiffres repris des études. python3 plateforme/maj_textes_0910b.py (après maj_textes_0910.py)"""
import json, re
P = '/home/claude/cao/plateforme/gabarit.html'
s = open(P, encoding='utf-8').read()
E = '/home/claude/cao/etudes/'
VZ = json.load(open(E + 'vol_zones.json')); EF = json.load(open(E + 'efforts_colliers.json'))
FT = json.load(open(E + 'fiche_technique.json')); HC = json.load(open(E + 'hauban_collier_poutre.json'))
TE = json.load(open('/home/claude/cao/plans/tente_info.json'))
OC = json.load(open(E + 'infos_texte.json'))['geom']['_ouvertures_c4']
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
mil = lambda n: f'{round(n):,}'.replace(',', ' ')
sy, gl = EF['synthese'], EF['glissiere']
e0 = gl['porte_a_faux']; sig = gl['s_poteau_flexion']
HJ = {}
for d_, n_, _ in HC['en marche']['babord']:
    HJ.setdefault(n_, d_)
def hj(*noms):
    v = [HJ[n_] for n_ in noms if n_ in HJ]
    return fr(min(v), 0) if v else 'plus de 60'

def li(label_debut, nouveau):
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

# ---------------------------------------------------------------- en-tête
remplace("Le tube repose à chaque bout sur un <b>poteau carbone logé dans le coffre</b> (JD 09/10).",
         "Le tube repose à chaque bout, à plat, sur la potence d'un <b>poteau carbone logé dans le coffre</b> ; plus de glissière : le collier tourne dans le tube et les haubans l'avancent ou le reculent (JD 09/10).")
remplace("avec un petit coffre à ancre devant le puits ;", "avec un petit coffre à ancre devant le puits, ouvert comme une poche, et un puits moteur ouvert derrière ;")
remplace("<b>trampoline étanche</b>, dessous des bancs fermé sur les longerons ;", "<b>trampoline étanche</b> lacé au milieu, dessous des bancs fermé sur les longerons ;")
remplace("<b>trappes dans C4</b> pour les compartiments extérieurs ;", "<b>grandes ouvertures dans C4</b>, sans trappe, pour les compartiments extérieurs ;")
remplace("Tout le bordé en CP 4 + verre (JD 09/10).</p>",
         "Tout le bordé en CP 4 + verre, trappes en jaune ; <b>tente igloo</b> sur deux arceaux diagonaux, du dessus du coffre derrière l'hiloire à la poutre AR (bouton « Tente ») (JD 09/10).</p>")

# ---------------------------------------------------------------- collier, tube, appui
remplace("qui repose sur le coffre, dans le bloc PEHD d'une potence portée par un poteau carbone logé dans le coffre (JD 09/10, voir « Glissière du tube »).</li>",
         "qui repose sur le coffre, à plat sur la potence d'un poteau carbone logé dans le coffre (JD 09/10, voir « Appui du tube »).</li>")
li('Glissière du tube', f"""<li><b>Appui du tube</b> (JD 08–09/10) : les efforts verticaux des colliers passent par le <b>tube</b>, pas par le collier. <b>Plus de glissière</b> (JD 09/10) : c'est le collier qui tourne dans le tube, sur son tourillon ; le tube n'a pas à tourner ni à glisser dans son axe. À chaque bout, il repose <b>à plat sur une potence</b> en CP collé (4 × CP 10, 40 de haut, de y 990 à 1 078, de x 1 954 à 2 120) qui passe au-dessus de C4 ; les <b>haubans l'avancent ou le reculent</b> : il glisse ou roule sur la potence, à x 2 085 en nominal, {fr(e0)} derrière l'axe du poteau. Le collier ne touche rien (3 de la potence). Le <b>poteau</b>, tube carbone <b>Ø 50 × 2,5</b>, est <b>dans le coffre</b>, à 3 devant C4 (axe x 1 988,5, y ±1 045) : il sort par le dessus, dans une <b>bague</b> CP 18 collée dessous, et descend jusqu'au toit de la poche de la pièce d'angle AV, posé sur une <b>cale coulée</b> en époxy chargée (coffre en place, film de démoulage) ; {gl['L_poteau']} de long, douille de 20 dans la potence. Efforts (haubans Ø 5, prétension 300 à 500 N ; gîte maxi : une coque décolle, équipage au rappel) : <span class="num">{fr(sy['V_reglage'][0] / 1000)} à {fr(sy['V_reglage'][1] / 1000)} kN</span> par collier au réglage, {fr(sy['V_max'] / 1000)} kN à la gîte maxi, {fr(sy['V_max_15'] / 1000)} kN avec × 1,5 ; à {fr(sy['V_max_15'] / 1000)} kN : poteau {round(sig)} MPa en flexion ({gl['M_poteau']} N·m ; {round(sig * (e0 - 20) / e0)} à {round(sig * (e0 + 20) / e0)} MPa si les haubans avancent ou reculent le tube de 20 ; à comparer à la fiche du tube carbone, ou Ø 50 × 4 : ≈ {round(sig * 0.685)} MPa), {fr(gl['H_appuis'] / 1000)} kN à la bague et au pied, potence {fr(gl['s_potence'], 0)} MPa (CP okoumé : ≈ 40 à la rupture), tourillon {round(gl['s_tourillon'])} MPa (alu), pièce d'angle {fr(gl['p_piece_angle'])} MPa. Le collier tend à piquer autour du tube ({sy['M_tangage_reglage'][0]} à {sy['M_tangage_reglage'][1]} N·m au réglage, {sy['M_tangage_max']} au plus) : c'est le mât, dans l'alésage, qui l'en empêche (≈ {fr(sy['F_bords_alesage_max'] / 1000)} kN aux bords), aidé par le frottement de l'enroulement.</li>""")
remplace_re(r"Comprimé jusqu'à [\d,]+ kN à la gîte maxi, [\d,]+ fois sous son flambage \([\d,]+ kN\)\.",
            f"Comprimé jusqu'à {fr(sy['tube_max'] / 1000)} kN à la gîte maxi, {fr(sy['SF_tube'])} fois sous son flambage ({fr(EF['tube']['P_cr'] / 1000)} kN).")
remplace_re(r"Il passe au-dessus du coffre : [^<]*? du capot\.",
            f"Il passe au-dessus du coffre : {hj('moteur_puits')} au-dessus des parois du puits derrière C4, {hj('moteur_tete')} de la tête du moteur en marche, {hj('glissiere_potence_babord')} de la potence de l'appui du tube, {hj('coffre_capot_arriere', 'coffre_coque')} du capot.")

# ---------------------------------------------------------------- coffre à ancre ouvert
li('Coffre à ancre', f"""<li><b>Coffre à ancre</b> devant le puits, à la place de la caisse de batterie (JD 07/10) : deux cloisons CP 6 à ±250, de l'avant du coffre à la cloison du puits (x 1 711). <b>Ouvert dessus, comme une poche</b> (JD 09/10) : plus de couvercle ; la <b>face avant remonte jusqu'à z 650</b>, 250 au-dessus du bas de la pointe (450 avant), et le bordé central est découpé au-dessus, jusqu'à la cloison du puits : ouverture en pente de ≈ 150 × 500 (x 1 625 → 1 711, z 650 → 775) ; <b>évacuation en dessous</b> : deux trous Ø 25 dans le fond, au point bas de la poche, contre la cloison du puits (x 1 698, y ±120). Le grappin (370 × Ø 100 plié) est couché en travers sur le fond, contre la cloison du puits (z 386 → 486), avec son mouillage ; <span class="num">{round(VZ['coffre_ancre_L'])} L</span>.</li>""")

# ---------------------------------------------------------------- (17 h) puits du moteur sans face arrière
remplace("<b>Puits</b> CP 6 de 256 × 300 (y ±128, de x 1 717 à C4), ouvert dessous et dessus : c'est l'hélice (Ø 236) qui en fixe la largeur.",
         "<b>Puits</b> CP 6 de 256 × 300 (y ±128, de x 1 717 à C4), ouvert dessous, dessus et <b>derrière</b> : plus de face arrière (JD 09/10), C4 est ouverte sur toute la largeur du puits, du fond au capot ; l'eau des vagues qui frappent sous le coffre ressort derrière, vers la poutre AV et le trampoline, au lieu de monter dans le puits. C'est l'hélice (Ø 236) qui en fixe la largeur.")
remplace("elle dépasse de C4 de 22 au-dessus du nez de la poutre : C4 échancrée à y ±70 au-dessus de z 680.",
         "elle dépasse de C4 de 22 au-dessus du nez de la poutre, dans l'ouverture du puits ; le capot est découpé à ±70 pour elle.")
remplace("Une trappe dans C4 par compartiment extérieur (voir « Trappes de C4 »).", "Une grande ouverture dans C4 par compartiment extérieur, au-dessus des assises (voir « Ouvertures de C4 »).")
remplace("Une seule ouverture : le bas du puits moteur, 256 × 300.",
         "Ouvertures : le bas du puits moteur, 256 × 300, ouvert aussi derrière (JD 09/10), et les deux évacuations Ø 25 de la poche à ancre.")

# ---------------------------------------------------------------- trampoline lacé au milieu
remplace("trampoline en toile PVC <b>étanche</b> ;",
         "trampoline en toile PVC <b>étanche</b>, en deux moitiés <b>lacées au milieu</b>, dans la longueur : l'eau s'en va d'elle-même par l'arrière ;")

# ---------------------------------------------------------------- finition
li('Finition', """<li><b>Finition</b> : coffre, joues, hiloire, assises, accoudoirs et capot peints en blanc ; <b>trappes</b> des caissons de rangement <b>en jaune</b> (JD 09/10) ; couples, jambes, lisses, accroches, colliers, potences, bagues et poteaux des appuis du tube, joints, supports de livarde, semelles et parois du puits en noir ; brêlage et laçages (Dyneema) bleus. <b>Yin-yang</b>, le dessin du bateau : Ø 360 sur chaque face des deux voiles, dans le coin du point d'écoute, au-dessus de la livarde : centre x 4 324, z 2 139, à 100 de la chute et 60 de la livarde ; il suit la toile quand on roule la voile. Plus sur les joues (JD 09/10). <b>Trampoline étanche</b> en toile PVC, lacé au milieu (JD 09/10 ; mesh blanc avant).</li>""")

# ---------------------------------------------------------------- tente
li('Plan de découpe', f"""<li><b>Tente igloo</b> (JD 09/10), bouton « Tente » sous la maquette : toile simple paroi sur <b>deux arceaux alu Ø 11 en diagonale</b>, croisés au sommet. Elle couvre <b>le dessus du coffre derrière l'hiloire</b> (JD 09/10 : « tente inclut le coffre, ou derrière l'hiloire »), le tube des colliers, les bancs et le trampoline, jusqu'à la poutre AR : <span class="num">{mil(TE['long'])} × {mil(TE['larg'])}</span> (de x {mil(TE['x'][0])} au milieu, {mil(TE['x_coins'])} aux coins, à {mil(TE['x'][1])}), sommet à z {mil(TE['sommet'])}, <b>{mil(TE['haut_tramp'])} au-dessus du trampoline</b>. Bord avant posé sur le dessus du coffre, {TE['bord_avant']['derriere_hiloire']} derrière le pied de l'hiloire (z {mil(TE['bord_avant']['z_milieu'])} au milieu), puis en V jusqu'aux coins, sur les joues, juste devant les colliers (x {mil(TE['bord_avant']['x_coins'])}, z {mil(TE['bord_avant']['coins'])}) : la poche à ancre et la pointe restent dehors. Bords latéraux sur le haut des dossiers et des accoudoirs, puis le long des longerons ; bord arrière sur la poutre AR, porte dans le pan arrière. Arceaux de {mil(TE['arceau'])} chacun, pieds aux quatre coins ({TE['angle_pied']}° au pied), en forme d'élastique ; la toile passe à {TE['garde']} au moins au-dessus du coffre, du tube et du moteur (petite bosse sur la barre relevée : la rabattre). Les colliers traversent les flancs, juste au-dessus des joues : manchons cousus. Des <b>jupes</b> ferment sous les bords latéraux, derrière les bancs. Toile {fr(TE['toile'])} m², jupes {fr(TE['jupe'])} m². Mâts dehors ; voiles roulées ; moteur en bas (relevé, sa tête sortirait par la découpe du capot, sous la toile).</li>
    <li><b>Plan de découpe</b> refait sur ce coffre : tout le bordé (dessus, fond, C4, poches) en <b>CP 4 + verre</b> (JD 09/10) ; panneaux du bordé dépliés, pièces plates imbriquées sur des plaques de 2 500 × 1 220, DXF à l'échelle 1 (page séparée).</li>""")

# ---------------------------------------------------------------- volumes et assiette (études refaites)
par_cote = VZ['hors_centre_L'] / 2
remplace_re(r'Volume du coffre <span class="num">\d+ L</span> à l\'extérieur \(469 L avant\), \d+ L à l\'intérieur : \d+ L de chaque côté au-delà des couples ±420 \(compartiments extérieurs\), \d+ L de coffre à ancre, \d+ L de puits et, de chaque côté du moteur, un caisson de rangement de \d+ L\.',
            f'Volume du coffre <span class="num">{round(VZ["ext_L"])} L</span> à l\'extérieur (469 L avant), {round(VZ["int_L"])} L à l\'intérieur : {round(par_cote)} L de chaque côté au-delà des couples ±420 (compartiments extérieurs), {round(VZ["coffre_ancre_L"])} L de coffre à ancre (ouvert), {round(VZ["puits_L"])} L de puits et, de chaque côté du moteur, un caisson de rangement de {round(VZ["rangement_L"])} L.')
cas = FT['cas']; H0 = cas['HC16, 2 équipiers près de la poutre AV (référence)']
r0 = cas['Rando, 2 équipiers, coffre vide']; r60 = cas['Rando, 2 équipiers + 60 kg au coffre']; r60b = cas["Rando, 2 équipiers + 60 kg sous l'arrière des bancs"]
hy = FT['hydro']
li('Assiette', f"""<li><b>Assiette</b> (fiche technique, JD 06–09/10) : calcul statique, au repos ; le plan Chevalier flotte à {round(hy['D0'])} kg ({fr(hy['kg_mm'])} kg par mm, ≈ {round(FT['mct'])} kg·m par degré vers 360 kg). À équipage égal, assis près de la poutre AV, la Rando a <span class="num">{fr(r0['assiette'] - H0['assiette'])}°</span> de plus sur le nez que le HC16, coffre vide (eau {'+' if r0['etrave'] - H0['etrave'] >= 0 else '−'} {abs(r0['etrave'] - H0['etrave'])} à l'étrave, {'+' if r0['tableau'] - H0['tableau'] >= 0 else '−'} {abs(r0['tableau'] - H0['tableau'])} au tableau) ; {fr(r60['assiette'] - H0['assiette'])}° avec 60 kg au coffre, {fr(r60b['assiette'] - H0['assiette'])}° si ces 60 kg vont sous l'arrière des bancs. Les batteries dans les accoudoirs, au bout des bancs, tirent l'arrière vers le bas. Point bas du coffre (puits, z 270) à {r0['garde_coffre']} au-dessus de l'eau calme coffre vide, {r60['garde_coffre']} avec 60 kg. En route, la vitesse enfonce l'arrière et la voile appuie sur le nez, autant pour les deux bateaux : le HC16 s'assied sur l'arrière, la Rando le fera moins. Ranger le lourd sous les bancs. Menu « coffre » sous la maquette (étude du 30/09, charge au CdG du coffre) ; pointillé dans la coupe du relevage.</li>""")

remplace("(x 1 950, devant le poteau de la glissière)", "(x 1 950, devant le poteau d'appui du tube)")
li('Trappes de C4', f"""<li><b>Ouvertures de C4</b> (JD 09/10 : « pas de trappes sur les caissons extérieurs, une ouverture polygonale aussi grande que possible au-dessus du niveau des sièges ») : une par compartiment extérieur (de ±420 à la joue, {round(VZ['hors_centre_L'] / 2)} L chacun), <b>sans couvercle</b> : de y ±{mil(OC['y'][0])} (25 du couple plein ±420) à ±{mil(OC['y'][1])} (5 du poteau d'appui du tube), de z {mil(OC['z_bas'])} (25 au-dessus des assises) jusqu'à 25 sous le haut de C4, qui monte à 10° vers la joue : <span class="num">{mil(OC['y'][1] - OC['y'][0])}</span> de large, {mil(OC['z_haut'][0] - OC['z_bas'])} de haut côté moteur et {mil(OC['z_haut'][1] - OC['z_bas'])} côté joue, coins arrondis R {OC['rayon']} ; {fr(OC['aire_m2'], 2)} m² (0,037 pour la trappe de 320 × 117 d'avant). Le couple ±850, évidé, passe derrière, au milieu.</li>""")
remplace("/^glissiere/.test(n) ? 'glissière' :", "/^glissiere/.test(n) ? 'appui du tube' :")
remplace("Tubes carbone : pylônes, poteaux des glissières, livardes</span>", "Tubes carbone : pylônes, poteaux d'appui du tube, livardes</span>")
for mot in ('bloc PEHD', 'Glissière du tube', 'Reste à refaire : la tente', 'glissière)', 'poteau de la glissière', 'couvercle : le bordé central', 'C4 échancrée', 'Une seule ouverture', 'Trappes de C4', 'trappes dans C4'):
    assert mot not in s, mot
open(P, 'w', encoding='utf-8').write(s)
print('ok', len(s))
