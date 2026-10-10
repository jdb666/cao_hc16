"""(JD 08/10 soir et 09/10) Pages du book : poteaux de la glissière dans le coffre, coffre en moustache et hiloire,
dessous des bancs fermé à l'eau, trois haubans par mât (plus de haubans de pied), semelle unique, emplanture à 3 crans,
joue d'un seul trait jusqu'au dossier, capot horizontal. Chiffres repris des études. python3 book/slides_0910.py"""
import json, html
E = '/home/claude/cao/etudes/'
OUT = '/home/claude/cao/book/deck/slides/'
EF = json.load(open(E + 'efforts_colliers.json')); VZ = json.load(open(E + 'vol_zones.json'))
esc = html.escape
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
MONO = "font-family:'IBM Plex Mono', 'Courier New', monospace"
DISP = "font-family:'Barlow Semi Condensed', Arial, sans-serif"
sy, gl = EF['synthese'], EF['glissiere']
assert gl.get('type') == 'poteau_coffre', gl

def entete(sid, titre):
    return (f'<section id="{sid}" style="background:#F7F8F8;color:#18262E;font-family:\'IBM Plex Sans\', Arial, sans-serif">\n'
            f'<p style="position:absolute;left:128px;top:64px;width:1200px;{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:#1F6F8B">06 · Détails</p>\n'
            f'<h2 style="position:absolute;left:128px;top:100px;width:1600px;{DISP};font-size:44px;font-weight:600;line-height:1.15;color:#18262E">{esc(titre)}</h2>\n')
PIED = f'<p style="position:absolute;right:128px;bottom:56px;width:120px;text-align:right;{MONO};font-size:24px;color:#4A5A63">0</p>\n</section>\n'

def deux_images(sid, titre, g, d, texte, fs=25):
    (cg, ig, ag), (cd, id_, ad) = g, d
    return (entete(sid, titre)
            + f'<p style="position:absolute;left:128px;top:196px;width:812px;{MONO};font-size:24px;color:#4A5A63">{esc(cg)}</p>\n'
            + f'<p style="position:absolute;left:980px;top:196px;width:812px;{MONO};font-size:24px;color:#4A5A63">{esc(cd)}</p>\n'
            + f'<img src="IMG:{ig}" alt="{esc(ag)}" style="position:absolute;left:128px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">\n'
            + f'<img src="IMG:{id_}" alt="{esc(ad)}" style="position:absolute;left:980px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">\n'
            + f'<p style="position:absolute;left:128px;top:730px;width:1664px;font-size:{fs}px;line-height:1.45;color:#33434B">{esc(texte)}</p>\n' + PIED)

def une_image(sid, titre, img, alt, puces, contain=False):
    fit = 'object-fit:contain' if contain else 'object-fit:cover;border:1px solid #D5DCDF'
    return (entete(sid, titre)
            + f'<img src="IMG:{img}" alt="{esc(alt)}" style="position:absolute;left:128px;top:196px;width:1040px;height:585px;{fit}">\n'
            + '<ul style="position:absolute;left:1216px;top:196px;width:576px;font-size:24px;line-height:1.42;color:#33434B">\n'
            + ''.join(f'<li>{esc(p_)}</li>\n' for p_ in puces) + '</ul>\n' + PIED)

S = {}
S['d-glissiere'] = deux_images(
    'd-glissiere', 'Le tube des colliers repose sur deux poteaux, dans le coffre',
    ("Poteau, potence et bloc PEHD", 'm_glissiere',
     "Bout bâbord du tube des colliers : il repose dans le bloc PEHD vissé sur la potence, qui passe au-dessus de C4 et coiffe le poteau carbone sortant du dessus du coffre ; le collier tourne autour sans toucher"),
    ('Coupes : le poteau dans le coffre', 'f_glissiere',
     "Coupes de la glissière : poteau carbone dans le coffre contre C4, bague sous le dessus, cale coulée sur le toit de la poche de la pièce d'angle, potence et bloc PEHD sous le bout du tube"),
    f"Ce n'est pas le collier qui porte : le tube Ø 50 × 2, où il tourne sur son tourillon, repose à chaque bout dans un bloc PEHD "
    f"creusé en U, vissé sur une potence CP (4 × CP 10) qui passe au-dessus de C4. Elle coiffe un poteau carbone Ø 50 × 2,5 logé "
    f"dans le coffre, à 3 devant C4 : il sort par le dessus (bague CP 18 collée dessous) et descend sur le toit de la poche de la "
    f"pièce d'angle AV, sur une cale coulée. Plus rien sur la joue. Par collier : {fr(sy['V_reglage'][0] / 1000)} à {fr(sy['V_reglage'][1] / 1000)} kN "
    f"au réglage, {fr(sy['V_max'] / 1000)} kN à la gîte maxi ; à {fr(sy['V_max_15'] / 1000)} kN (× 1,5), poteau {round(gl['s_poteau_flexion'])} MPa "
    f"en flexion ({fr(gl['porte_a_faux'])} de porte-à-faux), {fr(gl['H_appuis'] / 1000)} kN à la bague et au pied, potence {round(gl['s_potence'])} MPa, "
    f"PEHD {fr(gl['p_pehd'])} MPa.", fs=24)

S['d-moustache'] = deux_images(
    'd-moustache', 'Coffre en moustache, fond qui ouvre les vagues, hiloire',
    ('De face : dessus et fond à 10°', 'm_coffre_fa',
     "Le coffre vu de face entre les deux coques : dessus et fond remontent à 10° vers les joues, comme une moustache ; mâts, tube des colliers et poteaux des glissières"),
    ("Hiloire en haut de l'arrondi", 'm_hiloire',
     "L'avant du coffre de près : hiloire penchée vers l'avant en haut de l'arrondi, droite devant le capot puis en V jusqu'aux joues"),
    f"Vu de face, dessus et fond remontent à 10° vers les joues : le dessus de 810 (plat sur ±450) à 927 contre la joue, le fond de 270 "
    f"(plat sur ±150) à 439, 105 au-dessus du pont à l'axe des coques. Devant, le fond remonte à 25° jusqu'à la pointe (z ≈ 400 au milieu) : "
    f"c'est lui qui ouvre les vagues ; en cas d'enfournement, le coffre porte, et il protège le trampoline des vagues qui passent dessous. "
    f"En haut de l'arrondi, une hiloire CP 9 de 30, penchée à 45° vers l'avant, droite devant le capot (±460) puis en V jusqu'aux joues, "
    f"renvoie l'eau sur les côtés. Volume {round(VZ['ext_L'])} L (469 avant).", fs=24)

S['d-etanche'] = deux_images(
    'd-etanche', "Dessous des bancs fermé à l'eau",
    ("Tape au-dessus de la pièce d'angle", 'm_banc_tape',
     "Sous l'avant du banc bâbord : tape CP collée contre la joue au-dessus de la pièce d'angle AV, taillée à son profil, jusque sous l'assise"),
    ('Joint sous la joue, sur le longeron', 'm_banc_joint',
     "Bas de la joue bâbord, côté extérieur : joint néoprène sur le longeron, sous la joue, jusqu'au bout du banc"),
    "Trampoline en toile PVC étanche (mesh avant). Pour que l'eau qui passe sous le coffre ne remonte pas entre les poutres et le "
    "dessous du banc : au-dessus de la pièce d'angle AV, où la joue est dégagée, une tape CP 6 contre la joue, de C4 au bout de la "
    "pièce d'angle (x 2 130), taillée à son profil et à celui du longeron (1 de jeu), jusque sous l'assise ; plus loin, un joint "
    "néoprène 10 × 10 sur le longeron, sous la joue, jusqu'au bout du banc. Tous deux se posent une fois le coffre en place : "
    "ils gêneraient la fin de pose en diagonale.")

S['d-rangements'] = deux_images(
    'd-rangements', 'Caissons de rangement et trappes de C4',
    ('Caissons de chaque côté du moteur', 'v_rang_transp',
     "Coffre transparent vu de l'arrière : de chaque côté du puits du moteur, un caisson fermé par le capot arrière horizontal, avec sa trappe"),
    ('Trappe de C4, au-dessus du banc', 'f_trappe_c4',
     "C4, moitié bâbord vue de l'arrière : trappe de 320 × 117 au-dessus de l'assise, sous le dessus en moustache ; couples ±420 et ±850 derrière ; poteau de la glissière dans le coffre, au bout de la trappe"),
    f"Dessus plat à ±450, prolongé jusqu'à C4 par le capot horizontal (z 810). De chaque côté du puits, un caisson de {round(VZ['rangement_L'])} L "
    f"entre la paroi du puits et un couple plein CP 6 à ±420, fermé par le capot ; trappe de 205 × 250 découpée dans le capot, à plat, "
    f"sur un cadre de tasseaux. Dans C4, une trappe de 320 × 117 par compartiment extérieur ({round(VZ['hors_centre_L'] / 2)} L de ±420 à la joue), "
    f"25 au-dessus de l'assise, sous le dessus abaissé ; le couple ±850, derrière, porte le couvercle.")

S['d-haubans'] = une_image(
    'd-haubans', 'Haubans : trois par mât', 'd_haubans', 'Coffre transparent vu de trois quarts avant avec les haubans des colliers',
    ["Un seul niveau, aux colliers, Ø 5 : trois haubans par mât (JD 08/10 soir). Ils tiennent les mâts, pas le coffre.",
     "Direct AV vers la patte d'étrave et direct AR vers la cadène, du même bord ; diagonale vers le milieu de la poutre AV, au-dessus du capot.",
     "Plus de croisés AV ni de haubans au pied : la semelle collée sur le renfort passe au pont l'effort du pied (≈ 2,4 kN).",
     f"À la gîte maxi, le plus chargé monte à {fr(sy['T_max'] / 1000)} kN : {fr(sy['SF_hauban'])} fois sous la rupture.",
     "Le tube alu d'un collier à l'autre tient les mâts en travers et, relevé, le moteur."])

S['d-hpied'] = une_image(
    'd-hpied', 'Pied de mât bâbord, à nu', 'h_pied_detail',
    "Pied de mât bâbord sans le coffre : renfort de pont, semelle unique avec l'emplanture et les deux tubes carbone du coffre, nez de la pièce d'angle et pylône",
    ["Du pont vers le haut : renfort CP 2 × 4, bourrage, semelle CP 18, joues et cale de l'emplanture en CP, ergot inox.",
     "Une seule semelle par bord, 394 × 167 : le mât et, devant, les deux tubes carbone du coffre ; échancrée autour du pylône de la poutre AV.",
     "Plus de pontets ni de haubans au pied (JD 08/10 soir).",
     "Le mât longe le nez de la pièce d'angle (18 de jeu) ; le coffre se pose ensuite sur ses tubes : il ne touche ni au pied, ni aux haubans."])

S['d-pied'] = une_image(
    'd-pied', 'Pied de mât', 'd_pied_mat', 'Pied de mât bâbord sur sa semelle, contre la joue du coffre',
    ["Mât Ø 60 à x 1 960, y ±1 161 : reculé de 194 pour aligner son CV sur celui du HC16 ; son bord arrive au bord du pont, la paroi de coque reprend l'effort vertical ; 11 de jeu à la joue.",
     "Semelle CP 18 sur bourrage époxy, perpendiculaire au mât, une seule par bord pour le mât et les deux tubes du coffre (x 1 656 → 2 050) ; à 10 du pylône de la poutre AV.",
     "Renfort de pont cintré sur toute la largeur, 2 plis de CP 4, de x 1 616 à 2 130.",
     "Plus de haubans au pied : trois haubans par mât, au collier."])

S['d-emplanture'] = une_image(
    'd-emplanture', 'Emplanture en CP : quête au trou', 'd_emplanture',
    "Emplanture bâbord en CP : deux joues sur la semelle, cale triangulaire pointe en bas sur son boulon, pied du mât sur l'ergot",
    ["Deux joues de CP 10, 140 × 40, collées sur la semelle et stratifiées ; trois trous Ø 8 tous les 20 (cinq avant le 08/10 soir), remplis d'époxy puis repercés.",
     "Cale en triangle pointe en bas, 3 plis de CP 10 collés et stratifiés : elle pivote sur le boulon inox, qui la tient.",
     "Ergot inox Ø 20 sur la cale : le mât, embout percé, tourne dessus. Il garde ses 7,30 m : la voile monte de 45.",
     "Quête, du trou avant au trou arrière : 4,4 · 3,0 · 1,6°."])

S['d-joue'] = une_image(
    'd-joue', "Joue d'un seul trait, haubans", 'd_joue', 'Joue bâbord vue de profil, avec le mât, le collier et les haubans',
    ["Joue CP 9 d'un seul trait : superellipse de la pointe (x 1 584) au haut du dossier (x 1 999, z 1 085, 400 au-dessus de l'assise), tangente à l'horizontale ; le dossier redescend jusqu'à l'accoudoir.",
     "Le coffre s'arrête à 927 contre la joue (moustache à 10°) : la joue le dépasse, sans décrochage.",
     "Collier 47 au-dessus de la joue, mât à 11 : le gréement ne touche pas le coffre.",
     "Haubans Ø 5 aux ferrures du collier : directs vers la patte d'étrave et la cadène, diagonale vers le milieu de la poutre AV. Plus de yin-yang sur la joue."])

for sid, h in S.items():
    open(OUT + sid + '.html', 'w', encoding='utf-8').write(h)
print('ok', list(S))
