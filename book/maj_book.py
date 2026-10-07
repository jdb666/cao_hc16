"""Mise à jour du book (06/10) : nomenclature, plans, numéros de page, sommaire, images.
python3 maj_book.py [carte_images.json]"""
import json, re, sys, os
S = '/home/claude/cao/book/deck/'
J = json.load(open('/home/claude/cao/plans/decoupe3.json'))
P = {p['ref']: p for p in J['pieces']}
fr = lambda v, d=3: f'{v:.{d}f}'.replace('.', ',')
mil = lambda n: f'{n:,}'.replace(',', ' ')

NOMS = {
    'C4': "Face arrière C4, milieu",
    'B': "Bordé (avant cintré + dessus)", 'F': "Fond", 'P': "Paroi de poche (pièce d'angle)",
    'TR': "Trappe de visite de C4, dans la chute de C4",
    'CV': "Couvercle du coffre à ancre : bordé central cintré, échancré pour le puits",
    'CA': "Caisse de la batterie : cloison avant", 'CB': "Caisse de la batterie : côté",
    'CM': "Cloison avant du puits, arrière du coffre à ancre",
    'AN': "Cloison du coffre à ancre (±250)",
    'BB': "Caisson du banc : côté intérieur", 'BR': "Caisson du banc : face arrière", 'BV': "Caisson du banc : couvercle",
    'PM': "Paroi du puits moteur et son accroche (±131), au travers de C4",
    'K331': "Couple ±331, de la cloison du puits à C4, et son accroche", 'K850': "Couple ±850 et son accroche, au travers de C4",
    'CL1': "Cale du bac de batterie, 40 = 4 × CP 10", 'CL2': "Cale du bac de batterie, 40 = 4 × CP 10",
    'PL': "Planche de la pince du moteur, 40 = 4 × CP 10", 'TA': "Table, sur la caisse",
    'CR': "Capot arrière en pente, découpé pour la tête du moteur", 'CJ': "Joue triangulaire du capot arrière",
    'J': "Joue, dossier du banc", 'AS': "Assise du banc",
    'BC1': "Couple de banc, x 2 160", 'BC2': "Couple de banc, x 2 410", 'BC3': "Couple de banc, x 2 680",
    'BC4': "Couple de banc, x 2 950", 'BC5': "Couple de banc, x 3 212",
    'SR': "Semelle sur les tubes carbone, 18 = 2 × CP 9",
    'SM': "Semelle de pied de mât, sous l'emplanture, 18 = 2 × CP 9",
    'JE': "Joue de l'emplanture, percée Ø 8 tous les 20", 'CE': "Cale de l'emplanture, 30 = 3 × CP 10, percée Ø 8",
    'CO1': "Collier du mât : plis 1 et 7, dessous et dessus", 'CO2': "Collier : plis 2 et 6, encoche du tourillon de 34",
    'CO3': "Collier : plis 3, 4 et 5, encoche du tourillon de 45",
    'ST': "Semelle des tubes du coffre, sur le pont, 18 = 2 × CP 9",
    'RP': "Renfort de pont, 8 = 2 × CP 4, cintré en place",
    'LC': "Collier ouvert de la livarde, 20 = 2 × CP 10", 'LG': "Godet de la livarde, pli percé Ø 34", 'LF': "Godet de la livarde, pli du fond",
}
def nom(ref):
    if ref in NOMS:
        return NOMS[ref]
    base = NOMS[re.match(r'[A-Z]+', ref).group(0)]
    cote = 'milieu' if '(milieu)' in P[ref]['nom'] else 'bâbord et tribord'
    return f'{base}, {cote}'

GROUPES = {
    'p-nom1': ['C4', 'B1', 'B2', 'B3', 'B4', 'CV', 'F1', 'F2', 'F3', 'F4', 'F5', 'P1', 'P2', 'P3', 'TR'],
    'p-nom2': ['AN', 'CM', 'PM', 'K331', 'K850', 'PL', 'CR', 'CJ'],
    'p-nom3': ['J', 'AS', 'BC1', 'BC2', 'BC3', 'BC4', 'BC5', 'BB', 'BR', 'BV', 'SR', 'ST'],
    'p-nom4': ['RP', 'SM', 'JE', 'CE', 'CO1', 'CO2', 'CO3', 'LC', 'LG', 'LF'],
}
TD = '<td style="text-align:right">'
for sid, refs in GROUPES.items():
    p = S + f'slides/{sid}.html'; t = open(p, encoding='utf-8').read()
    m = re.search(r'(<table[^>]*>\n<tr><th.*?</tr>\n)(.*?)(</table>)', t, re.S)
    rows = ''.join(f'<tr><td>{r}</td><td>{nom(r)}</td>{TD}{P[r]["ep"]}</td>{TD}{P[r]["qte"]}</td>{TD}{mil(P[r]["dim"][0])} × {mil(P[r]["dim"][1])}</td>{TD}{fr(P[r]["aire"])}</td></tr>\n'
                   for r in refs if r in P)
    t = t[:m.start(2)] + rows + t[m.end(2):]
    open(p, 'w', encoding='utf-8').write(t)
manq = sorted(set(P) - {r for g in GROUPES.values() for r in g})
print('nomenclature : pièces hors tableaux', manq)

# plans : chiffres
nref = len(P); npieces = sum(p['qte'] for p in P.values())
pl = J['planches']
def compte(ep):
    n = sum(1 if q['sw'] >= 2400 else 0.5 for q in pl if q['ep'] == ep)
    return fr(n, 1 if n % 1 else 0)
eps = sorted({q['ep'] for q in pl})
nplaques = sum(1 if q['sw'] >= 2400 else 0.5 for q in pl)
t = open(S + 'slides/s7.html', encoding='utf-8').read()
t = re.sub(r'>\d+<(/p><p[^>]*>repères)', f'>{nref}<\\1', t)
t = re.sub(r'>\d+<(/p><p[^>]*>pièces, plis compris)', f'>{npieces}<\\1', t)
t = re.sub(r'>[\d,]+<(/p><p[^>]*>plaques :)[^<]*<', lambda mm: f'>{fr(nplaques, 1 if nplaques % 1 else 0)}<' + mm.group(1) + ' ' + ' ; '.join(f'CP {e} × {compte(e)}' for e in eps) + '<', t)
open(S + 'slides/s7.html', 'w', encoding='utf-8').write(t)
print('plans :', nref, 'repères,', npieces, 'pièces,', nplaques, 'plaques', [(q['nom'] if 'nom' in q else q.get('id'), q['ep'], q['sw']) for q in pl][:10])

# numéros de page et sommaire
d = json.load(open(S + 'deck.json')); o = d['order']
for i, sid in enumerate(o):
    p = S + f'slides/{sid}.html'; t = open(p, encoding='utf-8').read()
    t2 = re.sub(r'(<p style="position:absolute;right:128px;bottom:56px;[^"]*">)\d+(</p>)', f'\\g<1>{i + 1}\\2', t)
    if t2 != t:
        open(p, 'w', encoding='utf-8').write(t2)
debut = {k: o.index(v['start']) + 1 for k, v in d['sections'].items()}
t = open(S + 'slides/sommaire.html', encoding='utf-8').read()
for k, num in (('hc16', '01'), ('actuel', '02'), ('transp', '03'), ('reduction', '04'), ('moteur', '05'), ('details', '06'), ('decoupe', '07'), ('fiche', '08'), ('fin', '—')):
    if k not in debut:
        continue
    t = re.sub(r'(>' + num + r'</p>.*?<p style="width:100px;[^"]*">)\d+(</p>)', f'\\g<1>{debut[k]}\\2', t, count=1, flags=re.S)
open(S + 'slides/sommaire.html', 'w', encoding='utf-8').write(t)
print('sommaire', debut)

# images : carte nom -> url (téléversements), diapo -> noms dans l'ordre
IMAGES = {
    'cover': ['s2_rando_av'],
    's2-av': ['s2_rando_av'], 's2-ar': ['s2_rando_ar'], 's2-prfa': ['s2_rando_pr', 's2_rando_fa'], 's2-de': ['s2_rando_de'],
    's3-av': ['s3_transp_av'], 's3-ar': ['s3_transp_ar'], 's3-prfa': ['s3_transp_pr', 's3_transp_fa'], 's3-de': ['s3_transp_de'],
    's3-cav': ['s3_coffre_av'], 's3-car': ['s3_coffre_ar'], 's3-cde': ['s3_coffre_de'], 's3-cpr': ['s3_coffre_pr'],
    's4-00-av': ['s4_00_av'], 's4-00-prfa': ['s4_00_pr', 's4_00_fa'], 's4-50-av': ['s4_50_av'], 's4-50-prfa': ['s4_50_pr', 's4_50_fa'],
    's4-75-av': ['s4_75_av'], 's4-75-prfa': ['s4_75_pr', 's4_75_fa'], 's4-de': ['s4_00_de', 's4_50_de', 's4_75_de'],
    's5-ar': ['s5_bas_ar', 's5_haut_ar'], 's5-art': ['s5_bas_ar_transp', 's5_haut_ar_transp'], 's5-avt': ['s5_bas_av_transp', 's5_haut_av_transp'],
    's5-prt': ['s5_bas_pr_transp', 's5_haut_pr_transp'], 's5-coupe': ['coupe_bas', 'coupe_haut'],
    'd-vprofil': ['vue_profil'], 'd-vdessus': ['vue_dessus'], 'd-vface': ['vue_face'], 'd-semelle': ['semelle'], 'd-pied': ['d_pied_mat'],
    'd-collier': ['d_collier', 'd_collier_av'], 'd-emplanture': ['d_emplanture'],
    'd-joue': ['d_joue'], 'd-livarde': ['d_livarde'], 'd-attaches': ['attaches'], 'd-accroches': ['d_accroches', 'd_brelage'], 'd-bancs': ['d_bancs'], 'd-batterie': ['d_caisson', 'd_ancre'],
    'd-haubans': ['d_haubans'], 'd-hpieds': ['h_pieds_av', 'h_pieds_de'], 'd-hpied': ['h_pied_detail'], 'd-ecoute': ['d_ecoute'], 'd-assiette': ['d_assiette_0', 'd_assiette_150'],
    'p-4a': ['planche_4-A'], 'p-6a': ['planche_6-A'], 'p-6b': ['planche_6-B'], 'p-9a': ['planche_9-A'], 'p-9b': ['planche_9-B'], 
    'p-demi': ['planche_4-B', 'planche_10-A'],
}
if len(sys.argv) > 1:
    carte = json.load(open(sys.argv[1]))
    n = 0
    for sid, noms in IMAGES.items():
        p = S + f'slides/{sid}.html'; t = open(p, encoding='utf-8').read()
        srcs = re.findall(r'src="([^"]+)"', t)
        assert len(srcs) == len(noms), (sid, srcs, noms)
        for s_, nm in zip(srcs, noms):
            if nm in carte:
                t = t.replace(f'src="{s_}"', f'src="{carte[nm]}"', 1); n += 1
        open(p, 'w', encoding='utf-8').write(t)
    reste = [(sid, s_) for sid in IMAGES for s_ in re.findall(r'src="(IMG:[^"]+)"', open(S + f'slides/{sid}.html', encoding='utf-8').read())]
    print('images remplacées :', n, '; sans image :', reste)
