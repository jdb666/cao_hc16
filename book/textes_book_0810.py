"""(JD 08/10) Textes du book mis à jour : accoudoirs, rangements, trappes de C4, glissière du tube, bancs renforcés, haubans Ø 5.
python3 book/textes_book_0810.py (après les études : vol_zones, infos_texte, balayage_levee)"""
import json, re
S = '/home/claude/cao/book/deck/slides/'
E = '/home/claude/cao/etudes/'
VZ = json.load(open(E + 'vol_zones.json')); IN = json.load(open(E + 'infos_texte.json'))
L = IN['longueurs']
def rep(f, pairs):
    p = S + f; t = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert t.count(a) == 1, (f, a[:70], t.count(a))
        t = t.replace(a, b)
    open(p, 'w', encoding='utf-8').write(t)

rep('cover.html', [('modèle du 6 octobre 2026', 'modèle du 8 octobre 2026'),
                   ('collier, emplanture, centres véliques réalignés le 6 octobre', 'accoudoirs, rangements, glissière du tube et bancs renforcés le 8 octobre')])
rep('s2.html', [('481 L', f"{round(VZ['ext_L'])} L")])
rep('s3.html', [("coffre à ancre, puits du moteur, caissons des bancs (batterie à bâbord), couples en long qui traversent C4, tubes carbone posés sur les semelles.",
                 "coffre à ancre, puits du moteur et ses deux caissons de rangement, accoudoirs des bancs (une batterie dans chacun), couples en long qui traversent C4, tubes carbone posés sur les semelles."),
                ('>24 V 50 Ah<', '>2 × 24 V 50 Ah<'),
                ('batterie dans le caisson du banc bâbord, contre C4', 'batteries dans les accoudoirs, au bout des bancs')])
rep('s3-av.html', [("coffre à ancre devant le puits du moteur, caissons sur l'avant des bancs (batterie à bâbord), couples en long, tubes carbone sur leurs semelles.",
                    "coffre à ancre devant le puits du moteur, caissons de rangement de chaque côté du puits, accoudoirs au bout des bancs (batteries), couples en long, tubes carbone sur leurs semelles.")])
rep('s3-ar.html', [('les couples à ±131, ±331 et ±850 la traversent', 'les couples à ±131, ±420 et ±850 la traversent')])
rep('s3-de.html', [("de chaque côté, les bancs, ouverts dessous, avec leur caisson contre C4 (batterie à bâbord).",
                    "de part et d'autre du puits, les deux caissons de rangement sous le capot ; de chaque côté, les bancs, ouverts dessous, avec leur accoudoir au bout (batteries).")])
rep('s3-cav.html', [("caissons sur l'avant des bancs, contre C4 ; le tube des colliers passe au-dessus, derrière C4.",
                     "dessus plat élargi à ±450 ; le tube des colliers passe au-dessus, derrière C4, posé sur les joues dans ses glissières.")])
rep('s3-cde.html', [(f"Volume 481 L (676 avant) : avant droit au ras des joues, coffre à ancre devant le puits, caissons sur l'avant des bancs. Trappes de visite dans C4, entre les couples (y ±500 → ±800) ; un seul trou dans le fond : le bas du puits, 256 × 300.",
                     f"Volume {round(VZ['ext_L'])} L : avant droit au ras des joues, coffre à ancre devant le puits, de chaque côté du puits un caisson de rangement de {round(VZ['rangement_L'])} L sous le capot, avec sa trappe. Une grande trappe dans C4 par compartiment extérieur ; un seul trou dans le fond : le bas du puits, 256 × 300.")])
rep('s6.html', [('>Bancs et laçage ; batterie sur le banc, coffre à ancre<', ">Bancs renforcés, laçage ; batteries dans les accoudoirs ; rangements<"),
                ('>Pied de mât, collier sur le tube, emplanture<', '>Pied de mât, collier sur le tube, glissière du tube, emplanture<')])
rep('fin.html', [("Collier et emplanture en CP collé stratifié (06/10) ; batterie 24 V 50 Ah sur le banc bâbord, coffre raccourci au ras des joues, coffre à ancre (07/10).",
                  "Batteries dans les accoudoirs, caissons de rangement et trappes de C4, tube des colliers posé dans les glissières des joues, bancs renforcés pour s'asseoir à deux, haubans Ø 5 (08/10).")])
rep('p-fab.html', [("Bordé cintré CP 4 ; fond, C4, cloisons, puits, couples ±331 et caissons des bancs CP 6 ; joues, couples ±850, assises et couples de banc CP 9 ; collier et emplanture des mâts CP 10. Pièces de 18 à 70 en plis collés.",
                    "Bordé cintré CP 4 ; fond, C4, cloisons, puits, couples pleins ±420, capot, trappes et accoudoirs CP 6 ; joues, couples ±850, assises, couples, lisses et joues de jambe des bancs, poteaux des glissières CP 9 ; collier et emplanture des mâts, sabots des glissières CP 10. Pièces de 18 à 70 en plis collés."),
                   ("K850, K331 et PM : présenter un gabarit", "K850, K420 et PM : présenter un gabarit"),
                   ("4 tubes carbone Ø 40 × 2 ; tube alu Ø 50 × 2 de 2 156 ; tourillons alu Ø 45 et chemises PEHD des colliers ; ergots, boulons, axes et ferrures inox ; bout Ø 5 pour le laçage et le brêlage ; bourrage époxy, ≈ 535 cm³ sous chaque semelle de mât ; haubans Ø 4 ; batterie 24 V 50 Ah, sangle et presse-étoupe.",
                    "4 tubes carbone Ø 40 × 2 ; tube alu Ø 50 × 2 de 2 156 ; tourillons alu Ø 45 et chemises PEHD des colliers ; garnitures PEHD 3 et cales coulées des glissières ; ergots, boulons, axes et ferrures inox ; Dyneema Ø 5 pour le laçage et le brêlage ; bourrage époxy, ≈ 535 cm³ sous chaque semelle de mât ; haubans Ø 5 ; 2 batteries 24 V 50 Ah, sangles, joints, grenouillères, tourniquets et presse-étoupe.")])
rep('d-accroches.html', [("Six couples-accroches, à ±131, ±331 et ±850.", "Six couples-accroches, à ±131, ±420 et ±850."),
                         ("six brins en éventail de 255, 390 et 855,", f"six brins en éventail de {L['brelage_poutre_2']}, {L['brelage_poutre_1']} et {L['brelage_poutre_0']},")])
rep('d-haubans.html', [("Deux niveaux, Ø 4 :", "Deux niveaux, Ø 5 (JD 08/10) :")])
rep('d-hpieds.html', [("quatre haubans Ø 4 par mât", "quatre haubans Ø 5 par mât")])
rep('d-joue.html', [("Haubans Ø 4 aux ferrures du collier", "Haubans Ø 5 aux ferrures du collier")])
rep('d-collier.html', [("Environ 0,6 kg ; dessous 10 au-dessus des joues : rien ne touche le coffre.",
                        "Environ 0,6 kg ; dessous 10 au-dessus des joues : le collier ne touche pas le coffre, c'est le tube qui repose sur les joues, dans les glissières.")])
print('ok')
