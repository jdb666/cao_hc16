"""(JD 09/10 après-midi) Nouvelles diapos du book : le coffre par en dessous (section 03), poche à ancre et puits ouverts,
tente igloo (section 06). Images en IMG:<nom> jusqu'au passage de maj_book.py avec la carte des téléversements.
python3 book/slides_0910b.py (une fois ; refuse de refaire une diapo existante)"""
import json, os
S = '/home/claude/cao/book/deck/'
esc = lambda s: s.replace('&', '&amp;').replace("'", '&#x27;').replace('<', '&lt;').replace('>', '&gt;')
PNUM = ('<p style="position:absolute;right:128px;bottom:56px;width:120px;text-align:right;font-family:\'IBM Plex Mono\', \'Courier New\', monospace;'
        'font-size:24px;color:#4A5A63">0</p>')

def pleine(sid, kicker, titre, img, alt, texte):
    return f'''<section id="{sid}" style="background:#F7F8F8;color:#18262E;font-family:'IBM Plex Sans', Arial, sans-serif">
<img src="IMG:{img}" alt="{esc(alt)}" style="position:absolute;left:0px;top:0px;width:1920px;height:1080px;object-fit:cover">
<p style="position:absolute;left:128px;top:64px;width:1200px;font-family:'IBM Plex Mono', 'Courier New', monospace;font-size:24px;letter-spacing:2px;text-transform:uppercase;color:#1F6F8B">{esc(kicker)}</p>
<h2 style="position:absolute;left:128px;top:100px;width:1200px;font-family:'Barlow Semi Condensed', Arial, sans-serif;font-size:44px;font-weight:600;line-height:1.15;color:#18262E">{esc(titre)}</h2>
<p style="position:absolute;left:128px;bottom:56px;width:640px;padding:20px 24px;background:rgba(247,248,248,0.92);border-left:4px solid #1F6F8B;font-size:24px;line-height:1.42;color:#33434B">{esc(texte)}</p>
{PNUM}
</section>
'''

def double(sid, titre, leg1, img1, alt1, leg2, img2, alt2, texte, fs=24):
    return f'''<section id="{sid}" style="background:#F7F8F8;color:#18262E;font-family:'IBM Plex Sans', Arial, sans-serif">
<p style="position:absolute;left:128px;top:64px;width:1200px;font-family:'IBM Plex Mono', 'Courier New', monospace;font-size:24px;letter-spacing:2px;text-transform:uppercase;color:#1F6F8B">06 · Détails</p>
<h2 style="position:absolute;left:128px;top:100px;width:1600px;font-family:'Barlow Semi Condensed', Arial, sans-serif;font-size:44px;font-weight:600;line-height:1.15;color:#18262E">{esc(titre)}</h2>
<p style="position:absolute;left:128px;top:196px;width:812px;font-family:'IBM Plex Mono', 'Courier New', monospace;font-size:24px;color:#4A5A63">{esc(leg1)}</p>
<p style="position:absolute;left:980px;top:196px;width:812px;font-family:'IBM Plex Mono', 'Courier New', monospace;font-size:24px;color:#4A5A63">{esc(leg2)}</p>
<img src="IMG:{img1}" alt="{esc(alt1)}" style="position:absolute;left:128px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">
<img src="IMG:{img2}" alt="{esc(alt2)}" style="position:absolute;left:980px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">
<p style="position:absolute;left:128px;top:730px;width:1664px;font-size:{fs}px;line-height:1.45;color:#33434B">{esc(texte)}</p>
{PNUM}
</section>
'''

E = '/home/claude/cao/etudes/'
VZ = json.load(open(E + 'vol_zones.json'))
TE = json.load(open('/home/claude/cao/plans/tente_info.json'))
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
mil = lambda n: f'{round(n):,}'.replace(',', ' ')
K = '03 · Coffre par en dessous'
NOUV = {
    's3-dsav': pleine('s3-dsav', K, 'Par en dessous, 3/4 avant', 's3_dessous_av', "Le coffre vu d'en dessous, de trois quarts avant : pointe, fond en pente, moustache",
                      "Le fond remonte à 25° vers la pointe (z ≈ 400 au milieu) et à 10° vers les joues : c'est lui qui ouvre les vagues. Plat à z 270 sur ±150 sous le puits. Dans le fond, seulement le bas du puits et les deux évacuations Ø 25 de la poche à ancre."),
    's3-dsar': pleine('s3-dsar', K, 'Par en dessous, 3/4 arrière', 's3_dessous_ar', "Le coffre et les bancs vus d'en dessous, de trois quarts arrière, sans le trampoline : puits du moteur ouvert dessous et derrière, poutre AV",
                      "Trampoline ôté. Le puits du moteur est ouvert dessous et derrière (plus de face arrière, JD 09/10) : l'eau des vagues qui frappent sous le coffre ressort vers l'arrière au lieu de monter dans le puits. Fond à 10° vers les joues ; dessous des bancs sur leurs couples."),
    's3-dsfa': pleine('s3-dsfa', K, 'De face, par en dessous', 's3_dessous_fa', "Le coffre vu de face et d'en dessous entre les deux coques : dessus et fond en moustache",
                      "De face, dessus et fond remontent à 10° vers les joues : le fond passe de z 270 (plat sur ±150) à 439 contre la joue, 105 au-dessus du pont à l'axe des coques."),
    'd-poche': double('d-poche', 'Poche à ancre ouverte, puits ouvert derrière',
                      'Poche à ancre, face avant à z 650', 'm_ancre_poche', "La poche à ancre de près : face avant remontée, ouverture en pente jusqu'à la cloison du puits, entre les deux cloisons à ±250",
                      'Puits du moteur sans face arrière', 'm_puits_ar', "Le bas du puits du moteur vu de l'arrière : C4 ouverte sur toute la largeur du puits, du fond au capot",
                      f"Poche à ancre (JD 09/10) : plus de couvercle ; la face avant remonte à z 650, 250 au-dessus du bas de la pointe, et le bordé central est découpé au-dessus, jusqu'à la cloison du puits : ouverture en pente de ≈ 150 × 500 ; deux trous Ø 25 dans le fond, contre la cloison, la vident ; {round(VZ['coffre_ancre_L'])} L, le grappin couché en travers. Puits du moteur : plus de face arrière (JD 09/10) ; C4 est ouverte sur toute la largeur du puits (±128), du fond au capot, et ses deux moitiés sont collées aux parois du puits. L'eau des vagues qui frappent sous le coffre ressort derrière, vers la poutre AV et le trampoline, au lieu de monter dans le puits."),
    'd-tente': double('d-tente', 'Tente igloo sur deux arceaux en diagonale',
                      "3/4 avant : bord avant derrière l'hiloire", 't_tente_av', "La tente igloo montée, vue de trois quarts avant : bord avant posé sur le dessus du coffre derrière l'hiloire, coins sur les joues devant les colliers, voiles roulées",
                      'De profil', 't_tente_pr', "La tente igloo de profil, du dessus du coffre jusqu'à la poutre AR",
                      f"Toile simple paroi sur deux arceaux alu Ø 11 de {fr(TE['arceau'] / 1000)} m, croisés au sommet, pieds aux quatre coins ({TE['angle_pied']}° au pied). Elle couvre le dessus du coffre derrière l'hiloire (JD), le tube des colliers, les bancs et le trampoline, jusqu'à la poutre AR : {mil(TE['long'])} × {mil(TE['larg'])}, sommet à z {mil(TE['sommet'])}, {mil(TE['haut_tramp'])} au-dessus du trampoline. Bord avant posé sur le dessus du coffre, {TE['bord_avant']['derriere_hiloire']} derrière le pied de l'hiloire, en V jusqu'aux coins sur les joues, juste devant les colliers : la poche à ancre et la pointe restent dehors. Bords latéraux sur le haut des dossiers et des accoudoirs, puis le long des longerons ; bord arrière sur la poutre AR, porte dans le pan arrière ; jupes sous les bords, derrière les bancs. La toile passe à {TE['garde']} au moins au-dessus du coffre, du tube et du moteur ; les colliers traversent les flancs (manchons). Toile {fr(TE['toile'])} m², jupes {fr(TE['jupe'])} m² ; mâts dehors, voiles roulées, barre du moteur rabattue.", fs=23),
}
for sid, html in NOUV.items():
    p = S + f'slides/{sid}.html'
    if os.path.exists(p):
        print('existe déjà, laissée :', sid); continue
    open(p, 'w', encoding='utf-8').write(html)
d = json.load(open(S + 'deck.json')); o = d['order']
def apres(ref, ids):
    i = o.index(ref)
    for j, sid in enumerate([s for s in ids if s not in o]):
        o.insert(i + 1 + j, sid)
apres('s3-cpr', ['s3-dsav', 's3-dsar', 's3-dsfa'])
apres('d-batterie', ['d-poche'])
apres('d-etanche', ['d-tente'])
d['sections']['transp']['description'] = 'Les mêmes vues, coffre transparent, puis le coffre de près et par en dessous'
json.dump(d, open(S + 'deck.json', 'w'), ensure_ascii=False, indent=1)
print(len(o), o)
