"""(JD 08/10 soir et 09/10) Textes du book mis à jour : coffre en moustache, fond à 25°, hiloire, poteaux de glissière
dans le coffre, capot horizontal, trampoline étanche, trois haubans par mât, semelle unique, emplanture à 3 crans,
bordé CP 4 + verre. python3 book/textes_book_0910.py (après les études : vol_zones, infos_texte, pose_coffre)"""
import json, re
S = '/home/claude/cao/book/deck/slides/'
E = '/home/claude/cao/etudes/'
VZ = json.load(open(E + 'vol_zones.json')); IN = json.load(open(E + 'infos_texte.json'))
PO = json.load(open('/home/claude/cao/plateforme/pose_coffre.json'))
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
L = IN['longueurs']
def jmin(pas):
    v = [j[2] for q in pas for j in q['jeux'] if not j[0].startswith('pylone')]
    return min(v) if v else 12.0
def rep(f, pairs):
    p = S + f; t = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert t.count(a) == 1, (f, a[:70], t.count(a))
        t = t.replace(a, b)
    open(p, 'w', encoding='utf-8').write(t)

rep('cover.html', [('modèle du 8 octobre 2026', 'modèle du 9 octobre 2026'),
                   ('accoudoirs, rangements, glissière du tube et bancs renforcés le 8 octobre',
                    'coffre en moustache, hiloire, poteaux de glissière dans le coffre et trampoline étanche le 9 octobre')])
rep('s2.html', [('>469 L<', f">{round(VZ['ext_L'])} L<")])
rep('s2-ar.html', [('Haubans aux colliers et aux semelles ;', 'Trois haubans par mât, aux colliers ;')])
rep('s3-prfa.html', [("fond à z 250 sous le puits, remontant à 12° jusqu'à la pointe.",
                      "fond à z 270 sous le puits, remontant à 25° jusqu'à la pointe ; en travers, dessus et fond à 10° (moustache).")])
rep('s3-cav.html', [("dessus plat élargi à ±450 ; le tube des colliers passe au-dessus, derrière C4, posé sur les joues dans ses glissières.",
                     "dessus plat à ±450 et capot horizontal ; hiloire en haut de l'arrondi ; le tube des colliers passe au-dessus, derrière C4, sur les potences des deux poteaux logés dans le coffre.")])
rep('s3-cde.html', [('Volume 469 L :', f"Volume {round(VZ['ext_L'])} L :"),
                    ('un caisson de rangement de 42 L sous le capot', f"un caisson de rangement de {round(VZ['rangement_L'])} L sous le capot")])
rep('s3-cpr.html', [("Joue arrondie de la pointe (x 1 584) au sommet sous le collier (x 1 999, z 1 122), tangente à l'horizontale ; dessus central à z 810 ;",
                     "Joue arrondie d'un seul trait de la pointe (x 1 584) au haut du dossier (x 1 999, z 1 085), tangente à l'horizontale ; dessus central et capot à z 810 ; fond à 25° vers l'avant ;")])
rep('s5-prt.html', [('le fond du coffre est à z 250 sous le puits.', 'le fond du coffre est à z 270 sous le puits.')])
rep('s6.html', [('>Pied de mât, collier sur le tube, glissière du tube, emplanture<', '>Pied de mât, collier sur le tube, poteaux de la glissière, emplanture<'),
                ('>Bancs renforcés, laçage ; batteries dans les accoudoirs ; rangements<', ">Bancs renforcés, laçage, dessous fermé à l'eau ; batteries dans les accoudoirs ; rangements<"),
                ('>Haubans des mâts, pieds de mât à nu<', '>Haubans des mâts, coffre en moustache et hiloire, pied de mât à nu<')])
rep('fin.html', [("Batteries dans les accoudoirs, caissons de rangement et trappes de C4, tube des colliers posé dans les glissières des joues, bancs renforcés pour s'asseoir à deux, haubans Ø 5 (08/10).",
                  "Coffre en moustache à 10°, fond à 25° vers l'avant, hiloire ; poteaux de glissière dans le coffre ; trampoline étanche et dessous des bancs fermé ; dossier à 400 ; bordé CP 4 + verre (09/10). Trois haubans par mât, semelle unique, emplanture à 3 crans (08/10 soir).")])
rep('p-fab.html', [("Bordé cintré CP 4 ; fond, C4, cloisons, puits, couples pleins ±420, capot, trappes et accoudoirs CP 6 ; joues, couples ±850, assises, couples, lisses et joues de jambe des bancs, poteaux des glissières CP 9 ; collier et emplanture des mâts, sabots des glissières CP 10. Pièces de 18 à 70 en plis collés.",
                    "Tout le bordé (dessus, fond, C4, poches), le capot et les trappes en CP 4 + verre (JD 09/10) ; cloisons, puits, couples pleins ±420, accoudoirs et tapes CP 6 ; joues, couples ±850, assises, couples, lisses et joues de jambe des bancs, hiloire CP 9 ; collier et emplanture des mâts, potences des glissières CP 10. Pièces de 18 à 70 en plis collés."),
                   ("Tubes carbone Ø 40 dans le fond, passages du laçage.", "Tubes carbone Ø 40 dans le fond, poteaux Ø 50 des glissières dans le dessus, passages du laçage."),
                   ("4 tubes carbone Ø 40 × 2 ; tube alu Ø 50 × 2 de 2 156 ; tourillons alu Ø 45 et chemises PEHD des colliers ; garnitures PEHD 3 et cales coulées des glissières ; ergots, boulons, axes et ferrures inox ; Dyneema Ø 5 pour le laçage et le brêlage ; bourrage époxy, ≈ 535 cm³ sous chaque semelle de mât ; haubans Ø 5 ; 2 batteries 24 V 50 Ah, sangles, joints, grenouillères, tourniquets et presse-étoupe.",
                    "4 tubes carbone Ø 40 × 2 et 2 poteaux carbone Ø 50 × 2,5 ; tube alu Ø 50 × 2 de 2 156 ; tourillons alu Ø 45 et chemises PEHD des colliers ; blocs PEHD et cales coulées des glissières ; ergots, boulons, axes et ferrures inox ; Dyneema Ø 5 pour le laçage et le brêlage ; bourrage époxy, ≈ 980 cm³ sous chaque semelle ; haubans Ø 5 ; tissu de verre du bordé ; trampoline PVC étanche, joints néoprène 10 × 10 ; 2 batteries 24 V 50 Ah, sangles, joints, grenouillères, tourniquets et presse-étoupe.")])
rep('d-batterie.html', [('un coffre à ancre de 20 L,', f"un coffre à ancre de {round(VZ['coffre_ancre_L'])} L,")])
rep('d-collier.html', [(">De l'avant : ferrures des haubans AV<", ">De l'avant : ferrure du hauban direct AV<"),
                       ("Collier bâbord vu de l'avant : ferrures des haubans direct et croisé AV, tube des colliers derrière", "Collier bâbord vu de l'avant : ferrure du hauban direct AV, tube des colliers derrière"),
                       ("Environ 0,6 kg ; dessous 10 au-dessus des joues : le collier ne touche pas le coffre, c'est le tube qui repose sur les joues, dans les glissières.",
                        "Environ 0,6 kg ; dessous 47 au-dessus de la joue : le collier ne touche pas le coffre, c'est le tube qui repose sur les poteaux des glissières. Trois haubans : direct AV, direct AR, diagonale vers la poutre AV.")])
rep('d-livarde.html', [("36 de jeu au hauban direct AV, attaché 40 plus à l'extérieur sur le collier ; le croisé AV passe à plus de 60.",
                        "36 de jeu au hauban direct AV, attaché 40 plus à l'extérieur sur le collier.")])
rep('d-semelle.html', [("semelle du mât 250 × 142, CP 18 · bourrage époxy de 3 à 35 · dessus de semelle à z 345 · emplanture en CP collé stratifié : joues CP 10 × 40, cale de 3 plis de CP 10 pointe en bas, ergot Ø 20 · quête de 5,8 à 0,2° selon le trou.",
                        "semelle unique du mât et des tubes du coffre 394 × 167, CP 18, échancrée au pylône · bourrage époxy de 3 à 39 · dessus de semelle à z 345 · emplanture en CP collé stratifié : joues CP 10 × 40 de 140, cale de 3 plis de CP 10 pointe en bas, ergot Ø 20 · quête 4,4, 3,0 ou 1,6° selon le trou.")])
rep('d-bancs.html', [("</li>\n</ul>", "</li>\n<li>Dessous fermé à l'eau : trampoline étanche, tape et joint sous la joue.</li>\n</ul>")])
rep('d-attaches.html', [('jeu mini 1,2 en fin de course.', f"jeu mini {fr(jmin(PO['pas'][6:-1]))} en fin de course.")])
print('ok')
# (appliqué à la main le 09/10, après le balayage) s5-coupe : « Jeu mini ailleurs : 10, entre la tête et le coffre (échancrure de C4). »
# (appliqué le 09/10 après l'imbrication) p-demi : potences des glissières (GQ) au lieu des sabots, CP 4 sur deux plaques ; p-4b ajoutée, p-6b retirée.
# (appliqué le 09/10) titres : p-nom1 « Coffre : bordé, fond, face arrière, poches, capot, trappes » ; p-nom2 « Intérieur du coffre, hiloire, glissières du tube, tapes ».
