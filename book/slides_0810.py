"""(JD 08/10) Pages du book : glissière du tube, caissons de rangement et trappes, batteries dans les accoudoirs,
bancs renforcés et leur résistance. Chiffres repris des études. python3 book/slides_0810.py"""
import json, html
E = '/home/claude/cao/etudes/'
OUT = '/home/claude/cao/book/deck/slides/'
EF = json.load(open(E + 'efforts_colliers.json')); BR = json.load(open(E + 'banc_resistance.json'))
VZ = json.load(open(E + 'vol_zones.json')); IN = json.load(open(E + 'infos_texte.json'))
esc = html.escape
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
mil = lambda n: f'{round(n):,}'.replace(',', ' ')
MONO = "font-family:'IBM Plex Mono', 'Courier New', monospace"
DISP = "font-family:'Barlow Semi Condensed', Arial, sans-serif"
sy, gl = EF['synthese'], EF['glissiere']

def entete(sid, titre):
    return (f'<section id="{sid}" style="background:#F7F8F8;color:#18262E;font-family:\'IBM Plex Sans\', Arial, sans-serif">\n'
            f'<p style="position:absolute;left:128px;top:64px;width:1200px;{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:#1F6F8B">06 · Détails</p>\n'
            f'<h2 style="position:absolute;left:128px;top:100px;width:1600px;{DISP};font-size:44px;font-weight:600;line-height:1.15;color:#18262E">{esc(titre)}</h2>\n')
PIED = f'<p style="position:absolute;right:128px;bottom:56px;width:120px;text-align:right;{MONO};font-size:24px;color:#4A5A63">0</p>\n</section>\n'
def deux_images(sid, titre, g, d, texte):
    (cg, ig, ag), (cd, id_, ad) = g, d
    return (entete(sid, titre)
            + f'<p style="position:absolute;left:128px;top:196px;width:812px;{MONO};font-size:24px;color:#4A5A63">{esc(cg)}</p>\n'
            + f'<p style="position:absolute;left:980px;top:196px;width:812px;{MONO};font-size:24px;color:#4A5A63">{esc(cd)}</p>\n'
            + f'<img src="IMG:{ig}" alt="{esc(ag)}" style="position:absolute;left:128px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">\n'
            + f'<img src="IMG:{id_}" alt="{esc(ad)}" style="position:absolute;left:980px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">\n'
            + f'<p style="position:absolute;left:128px;top:730px;width:1664px;font-size:25px;line-height:1.45;color:#33434B">{esc(texte)}</p>\n' + PIED)

S = {}
S['d-glissiere'] = deux_images(
    'd-glissiere', 'Le tube des colliers repose sur les joues',
    ("Tube, berceau et sabot, de l'arrière", 'v_glissiere_berceau',
     "Bout bâbord du tube des colliers, vu de l'arrière : il repose dans le berceau en U garni de PEHD, sur le sabot collé au haut de la joue ; le collier tourne autour sans toucher"),
    ('Coupes : le tube dans son berceau', 'f_glissiere',
     "Coupe à x 2 085 de la joue au collier, et coupe en travers du tube : berceau en U, garniture PEHD, sabot, poteau caisson et cale coulée sur la pièce d'angle"),
    f"Ce n'est pas le collier qui porte : le tube Ø 50 × 2, où il tourne sur son tourillon, repose à chaque bout dans un berceau en U "
    f"(4 × CP 9) garni de PEHD, sur un sabot de 6 × CP 10 au ras du haut de la joue, de y 990 à la joue, sous tout le tourillon. "
    f"Dessous, un poteau caisson de trois parois CP 9 descend jusqu'à la pièce d'angle AV, sur une cale coulée. Le collier reste libre "
    f"(10 au-dessus du sabot). Par collier : {fr(sy['V_reglage'][0] / 1000)} à {fr(sy['V_reglage'][1] / 1000)} kN au réglage, "
    f"{fr(sy['V_max'] / 1000)} kN à la gîte maxi ; à {fr(sy['V_max_15'] / 1000)} kN (× 1,5), PEHD {fr(gl['p_pehd'])} MPa, "
    f"poteau {fr(gl['s_poteau'])} MPa, tourillon {round(gl['s_tourillon'])} MPa. Haubans passés en Ø 5 : {fr(sy['SF_hauban'])} fois sous la rupture.")

S['d-rangements'] = deux_images(
    'd-rangements', 'Caissons de rangement et trappes de C4',
    ('Caissons de chaque côté du moteur', 'v_rang_transp',
     "Coffre transparent vu de l'arrière : de chaque côté du puits du moteur, un caisson fermé par le capot arrière, avec sa trappe"),
    ('Trappe de C4, au-dessus du banc', 'f_trappe_c4',
     "C4, moitié bâbord vue de l'arrière : trappe de 398 × 188 au-dessus de l'assise, sous le haut de C4 qui monte vers la joue ; couples ±420 et ±850 derrière, poteau de la glissière devant son bout extérieur"),
    f"Dessus plat élargi à ±450. De chaque côté du puits, un caisson de {round(VZ['rangement_L'])} L entre la paroi du puits et un couple "
    f"plein CP 6 déplacé à ±420, fermé par le capot ; trappe de 205 × 250 découpée dans le capot, sur un cadre de tasseaux. "
    f"Dans C4, une trappe de 398 × 188 par compartiment extérieur ({round(VZ['hors_centre_L'] / 2)} L de ±420 à la joue), "
    f"25 au-dessus de l'assise ; le couple ±850, derrière, porte le couvercle, qui se retire en glissant vers l'intérieur.")

acc = IN['geom']['_accoudoirs']['babord']
S['d-batterie'] = deux_images(
    'd-batterie', 'Batteries dans les accoudoirs, coffre à ancre',
    ('Accoudoirs au bout des bancs, batteries en bleu', 'v_acc_transp',
     "Bancs en transparence vus de l'arrière : une batterie bleue en travers dans chaque accoudoir, au bout du banc, entre la joue, l'assise et les parois CP 6"),
    ('Coffre à ancre devant le puits', 'd_ancre',
     "Coffre transparent vu de l'avant : grappin couché en travers entre les deux cloisons du coffre à ancre, puits du moteur derrière"),
    f"Deux batteries LiFePO4 24 V 50 Ah en parallèle (100 Ah, 2,6 kWh ; 260 × 165 × 210, 11 kg chacune), une par accoudoir : "
    f"caisson CP 6 étanche au bout du banc (x {mil(acc['x'][0])} → {mil(acc['x'][1])}, toute la profondeur de l'assise, "
    f"{round(VZ['accoudoir_L'])} L), la joue fait l'extérieur, l'assise le fond ; couvercle sur joint, deux grenouillères. "
    f"Câbles 25 mm² sous l'assise, presse-étoupe dans C4. Devant le puits, deux cloisons à ±250 font un coffre à ancre "
    f"de {round(VZ['coffre_ancre_L'])} L, fermé par un couvercle découpé dans le bordé avant.")

S['d-bancs'] = (entete('d-bancs', 'Bancs renforcés et laçage')
    + '<img src="IMG:f_banc" alt="Coupes du banc bâbord : au droit d\'un couple, jambe doublée descendue sous le longeron et laçage dessous ; entre deux couples, lisse sous la rive de l\'assise" style="position:absolute;left:128px;top:196px;width:1040px;height:585px;object-fit:cover;border:1px solid #D5DCDF">\n'
    + '<ul style="position:absolute;left:1216px;top:196px;width:576px;font-size:24px;line-height:1.42;color:#33434B">\n'
    + '<li>Assise CP 9 de 1 195, collée à C4, sur cinq couples posés sur le longeron (x 2 160 → 3 212) ; accoudoir au bout.</li>\n'
    + '<li>Lisse CP 9 × 40 sous la rive intérieure, d\'un couple à l\'autre ; couples pleins.</li>\n'
    + '<li>Jambe du couple descendue à 115 sous l\'axe du longeron, jusqu\'à y 1 162, doublée de deux joues CP 9.</li>\n'
    + f'<li>Laçage Dyneema Ø 5 en double sous les jambes, d\'un banc à l\'autre sous la toile, sans la traverser ({fr(IN["longueurs"]["lacage_banc_0"] / 1000)} m par couple).</li>\n'
    + '</ul>\n' + PIED)

A_, R_ = BR['avant'], BR['renforce']
CAS = [('2 assis côte à côte', 'Deux assis côte à côte (× 2)'), ('assis sur le bord', 'Assis sur le bord (× 2)'),
       ('pied sur la rive, entre couples', 'Un pied sur la rive, entre couples (× 1,5)'),
       ("pied sur la rive, au droit d'un couple", "Un pied sur la rive, au droit d'un couple (× 1,5)")]
td = lambda t, al='right', st='': f'<td style="text-align:{al};{st}">{t}</td>'
rows = ''.join('<tr>' + td(esc(lib), 'left') + td(f"{fr(A_[k]['assise_SF'])} → <b>{fr(R_[k]['assise_SF'])}</b>")
               + td(f"{fr(A_[k]['ame_MPa'])} → <b>{fr(R_[k]['ame_MPa'])}</b>")
               + td(f"{fr(A_[k]['T_lacage'] / 1000)} → <b>{fr(R_[k]['T_lacage'] / 1000)}</b>")
               + td(f"{round(A_[k]['s_jambe'])} → <b>{round(R_[k]['s_jambe'])}</b>")
               + td(f"{fr(A_[k]['rotation_deg'])}° → <b>{fr(R_[k]['rotation_deg'])}°</b>") + '</tr>\n' for k, lib in CAS)
S['d-banc-res'] = (entete('d-banc-res', "Assez costaud pour s'asseoir à deux")
    + f'<p style="position:absolute;left:128px;top:196px;width:1664px;font-size:24px;line-height:1.4;color:#33434B">Banc d\'avant → banc renforcé. 100 kg par personne, CP okoumé 9 (rupture 40 MPa le long du fil, 22 en travers) ; assise calculée en plaque, couples entre C4 et l\'accoudoir. Le banc ne peut que basculer vers l\'intérieur autour de la queue du longeron : c\'est le laçage, sous la jambe, qui le retient.</p>\n'
    + '<table style="position:absolute;left:128px;top:300px;width:1664px;font-size:23px;color:#18262E">\n'
    + '<tr><th style="width:34%;text-align:left">Cas</th><th style="width:15%;text-align:right">Assise : fois sous la rupture</th><th style="width:13%;text-align:right">Âme des couples, MPa</th>'
    + '<th style="width:12%;text-align:right">Laçage, kN</th><th style="width:13%;text-align:right">Jambe, MPa</th><th style="width:13%;text-align:right">Bascule</th></tr>\n'
    + rows + '</table>\n'
    + f'<p style="position:absolute;left:128px;top:600px;width:1664px;font-size:24px;line-height:1.45;color:#33434B">Le point faible était la jambe du couple sous le laçage : {round(A_[CAS[3][0]]["s_jambe"])} MPa pour un pied au-dessus d\'un couple, bien au-delà de la rupture, et le banc basculait de {fr(A_[CAS[3][0]]["rotation_deg"])}°. '
    + f'Jambe doublée et descendue, laçage plus bas et en Dyneema : {round(R_[CAS[3][0]]["s_jambe"])} MPa et {fr(R_[CAS[3][0]]["rotation_deg"])}°. La lisse porte la rive : un pied entre deux couples passe de {fr(A_[CAS[2][0]]["assise_SF"])} à {fr(R_[CAS[2][0]]["assise_SF"])} fois sous la rupture. '
    + f'Dossier (joue CP 9) : 500 N en haut, solide mais souple, 1,4 à 4,7 cm.</p>\n' + PIED)

for sid, h in S.items():
    open(OUT + sid + '.html', 'w', encoding='utf-8').write(h)
print('ok', list(S))
