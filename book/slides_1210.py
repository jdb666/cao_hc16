"""(JD 12/10) Book : équipage assis face à face (nouvelle diapo d-equipage, section 06) ; point d'écoute automatique
selon l'enroulement (diapo d-ecoute refaite) ; une phrase sur l'écoute dans s4-50-av et s4-75-av.
Données : etudes/equipage_ecoutes.json (python3 etudes/equipage_ecoutes.py). Images en IMG:<nom> jusqu'au passage de
maj_book.py avec la carte des téléversements. python3 book/slides_1210.py (d-equipage n'est créée qu'une fois ; d-ecoute est réécrite)"""
import json, os, re
S = '/home/claude/cao/book/deck/'
esc = lambda s: s.replace('&', '&amp;').replace("'", '&#x27;').replace('<', '&lt;').replace('>', '&gt;')
fr = lambda v, d=1: f'{v:.{d}f}'.replace('.', ',')
mil = lambda n: f'{round(n):,}'.replace(',', ' ')
sg = lambda v: ('−' if v < 0 else '+' if v > 0 else '') + mil(abs(v))
PNUM = ('<p style="position:absolute;right:128px;bottom:56px;width:120px;text-align:right;font-family:\'IBM Plex Mono\', \'Courier New\', monospace;'
        'font-size:24px;color:#4A5A63">0</p>')
KICK = ('<p style="position:absolute;left:128px;top:64px;width:1200px;font-family:\'IBM Plex Mono\', \'Courier New\', monospace;font-size:24px;'
        'letter-spacing:2px;text-transform:uppercase;color:#1F6F8B">06 · Détails</p>')
TITRE = lambda t: (f'<h2 style="position:absolute;left:128px;top:100px;width:1600px;font-family:\'Barlow Semi Condensed\', Arial, sans-serif;font-size:44px;'
                   f'font-weight:600;line-height:1.15;color:#18262E">{esc(t)}</h2>')
J = json.load(open('/home/claude/cao/etudes/equipage_ecoutes.json'))
EQ = J['equipage']

def garde(x, am, choc, qui):                          # qui : 'H' ou 'F' ; H à bâbord, F à tribord
    g = next(g for g in J['gardes'] if g['x'] == x and g['amures'] == am and g['choc'] == choc)
    return next(t['m'] for t in g['tetes'] if t['nom'].startswith(qui))
def bras(x, qui):
    g = next(g for g in J['gardes'] if g['x'] == x)
    return next(b['m'] for b in g['bras'] if b['nom'].startswith(qui))
def zero_bras(qui):                                   # place où le bras touche le tube (interpolée)
    xs = sorted({g['x'] for g in J['gardes']})
    for a, b in zip(xs, xs[1:]):
        ma, mb = bras(a, qui), bras(b, qui)
        if ma < 0 <= mb: return a + (b - a) * (-ma) / (mb - ma)
    return xs[0]
def tz(y):                                            # dessus du trampoline en travers
    T = EQ['tramp']; y = abs(y)
    for (y0, z0), (y1, z1) in zip(T, T[1:]):
        if y <= y1: return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return T[-1][1]
X0 = 2450
zs = EQ['z_assise']
y_pied = EQ['y_dos'] - (10 + .07 * 1800 + .385 * 1800)          # cheville de l'homme (même formule que la page)
h_pieds, h_bord = zs - tz(y_pied), zs - tz(EQ['y_bord'])
pointes = (EQ['y_dos'] - (10 + .455 * 1800) - .134 * 1800) + (EQ['y_dos'] - (10 + .455 * 1600) - .134 * 1600)   # écart des pointes de pied
H15 = [garde(x, -1, 15, 'H') for x in (2400, 2450, 2500, 2600, 2700, 2780)]
H25 = [garde(x, -1, 25, 'H') for x in (2400, 2450, 2500)]
F_v = [garde(x, 1, c, 'F') for x in (2400, 2450, 2500) for c in (15, 25)]
sous_vent = min(min(garde(x, 1, c, 'H'), garde(x, -1, c, 'F')) for x in (2400, 2450, 2500, 2600, 2700, 2780) for c in (15, 25))

def double(sid, titre, leg1, img1, alt1, leg2, img2, alt2, texte, fs=22):
    return f'''<section id="{sid}" style="background:#F7F8F8;color:#18262E;font-family:'IBM Plex Sans', Arial, sans-serif">
{KICK}
{TITRE(titre)}
<p style="position:absolute;left:128px;top:196px;width:812px;font-family:'IBM Plex Mono', 'Courier New', monospace;font-size:24px;color:#4A5A63">{esc(leg1)}</p>
<p style="position:absolute;left:980px;top:196px;width:812px;font-family:'IBM Plex Mono', 'Courier New', monospace;font-size:24px;color:#4A5A63">{esc(leg2)}</p>
<img src="IMG:{img1}" alt="{esc(alt1)}" style="position:absolute;left:128px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">
<img src="IMG:{img2}" alt="{esc(alt2)}" style="position:absolute;left:980px;top:236px;width:812px;height:457px;object-fit:cover;border:1px solid #D5DCDF">
<p style="position:absolute;left:128px;top:722px;width:1664px;font-size:{fs}px;line-height:1.45;color:#33434B">{esc(texte)}</p>
{PNUM}
</section>
'''

equipage = double(
    'd-equipage', 'Deux équipiers assis face à face',
    'Bâbord amures, choqué 15° : H au vent', 'e_equ_ar',
    "De l'arrière, dans l'axe : l'homme de 1,80 m sur le banc bâbord, la femme de 1,60 m sur le banc tribord, face à face ; la voile bâbord, au vent, passe au-dessus du banc bâbord et touche la tête de l'homme",
    'Tribord amures, choqué 15° : F au vent', 'e_equ_fa',
    "De face : la femme, au vent sur le banc tribord, passe sous la bordure de la voile tribord ; l'homme est sous le vent",
    f"Un homme de 1,80 m et une femme de 1,60 m, un sur chaque banc à x {mil(X0)}, assis au fond de l'assise, dos contre la joue, mains sur les cuisses ; "
    f"proportions moyennes, en fractions de la taille (Drillis et Contini). L'assise n'est qu'à {mil(h_pieds)} au-dessus du trampoline sous les pieds "
    f"({mil(h_bord)} au bord du banc) : genoux relevés, pointes de pied à {fr(pointes / 1000)} m l'une de l'autre. Sommet des têtes à z {mil(zs + .52 * 1800)} (H) et {mil(zs + .52 * 1600)} (F) ; "
    f"la bordure passe à z ≈ 1 560 au-dessus des bancs. Voiles dans l'axe, la toile est à côté des têtes : {mil(garde(X0, 1, 0, 'H'))} et {mil(garde(X0, 1, 0, 'F'))} de garde. "
    f"Choquée, la voile au vent passe au-dessus du banc au vent : F y tient sous la bordure ({mil(min(F_v))} à {mil(max(F_v))} de garde à 15–25°) ; "
    f"H a la bordure sur la tête ({sg(H15[1])} à 15°, {sg(H25[1])} à 25° à x {mil(X0)} ; de {sg(max(H15))} à {sg(min(H15))} tout le long du banc à 15°). "
    f"Sous le vent, plus de {mil(sous_vent)}. Bras : le tube des colliers est devant les épaules ; contact devant x {mil(round(zero_bras('H'), -1))} (H) et {mil(round(zero_bras('F'), -1))} (F), "
    f"{mil(bras(X0, 'H'))} et {mil(bras(X0, 'F'))} de jeu à x {mil(X0)}. Page 3D : case « Équipage assis », place sur les bancs, changer de bord, gardes en direct.")

E15 = {e['f']: e for e in J['ecoutes']['15']}
LIGNES = (0, 25, 50, 60, 70, 75, 80, 90)
def point(e):
    if e.get('liv'): return f"rail poutre AR, y {mil(e['pos'])}", 'livarde posée'
    if e['typ'] == 'flotteur': return f"flotteur, x {mil(e['pos'])}", 'bout du flotteur' if e['pos'] >= 4995 else 'pontet'
    return f"poutre AR, y {mil(e['pos'])}", "angle des poutres" if e['pos'] >= 940 else 'vers l’axe'
rows = ''.join(
    f'<tr><td>{f} %</td><td style="text-align:right">{fr(E15[f]["S"] / 1e6)} m²</td><td>{esc(point(E15[f])[0])}'
    f'<br><span style="color:#4A5A63;font-size:17px">{esc(point(E15[f])[1])}</span></td><td style="text-align:right">{"—" if E15[f].get("liv") else str(round(E15[f]["ecart"])) + "°"}</td></tr>\n'
    for f in LIGNES)
bascule = next(f for f in sorted(E15) if f > 0 and E15[f]['typ'] == 'poutre')
avant_b = max(f for f in sorted(E15) if f < bascule)
ecoute = f'''<section id="d-ecoute" style="background:#F7F8F8;color:#18262E;font-family:'IBM Plex Sans', Arial, sans-serif">
{KICK}
{TITRE("Point d'écoute automatique : il suit l'enroulement")}
<img src="IMG:d_ecoute" alt="{esc("Vue de trois quarts arrière : voile bâbord roulée à 50 %, écoute au bout du flotteur ; voile tribord roulée à 80 %, écoute à l'angle des poutres ; tires idéales en pointillé rouge")}" style="position:absolute;left:128px;top:196px;width:1040px;height:585px;object-fit:cover;border:1px solid #D5DCDF">
<p style="position:absolute;left:1216px;top:196px;width:576px;font-family:'IBM Plex Mono', 'Courier New', monospace;font-size:20px;color:#4A5A63">Voile sous le vent, choquée de 15°</p>
<table style="position:absolute;left:1216px;top:234px;width:576px;font-size:20px;color:#18262E">
<tr><th style="width:15%">Roulé</th><th style="width:20%;text-align:right">Surface</th><th style="width:50%">Point d&#x27;écoute</th><th style="width:15%;text-align:right">Écart</th></tr>
{rows}</table>
<p style="position:absolute;left:128px;top:810px;width:1664px;font-size:22px;line-height:1.45;color:#33434B">{esc(
    "Voile pleine, la livarde tient la chute : l'écoute reste sur le rail de la poutre AR. Dès qu'une voile est roulée, la livarde est rangée et l'écoute tient seule la chute et la bordure : "
    "elle passe d'elle-même au point qui suit au mieux la tire idéale (du milieu du guindant par le point d'écoute de la voile) en la bordant. "
    f"Peu roulée, la tire tombe derrière le bateau : pontet au bout du flotteur (x 5 000), {round(E15[25]['ecart'])}° d'écart à 25 %, {round(E15[50]['ecart'])}° à 50 %. "
    f"Puis le pontet avance sur le flotteur jusqu'à x {mil(E15[avant_b]['pos'])} ({avant_b} %) ; vers {bascule} %, la tire passe devant les pontets et l'écoute bascule sur la poutre AR, à l'angle des poutres, "
    f"puis glisse vers l'axe. Plus choquée, la bascule vient plus tôt. Écart : angle entre l'écoute et la tire, dans le plan de la voile.")}</p>
{PNUM}
</section>
'''
p = S + 'slides/d-equipage.html'
if os.path.exists(p): print('existe déjà, laissée : d-equipage')
else: open(p, 'w', encoding='utf-8').write(equipage)
open(S + 'slides/d-ecoute.html', 'w', encoding='utf-8').write(ecoute)

# s4 : une phrase sur l'écoute (voile bâbord, choquée de 15° sur les vues 3/4 avant)
for sid, f, ajout in (('s4-50-av', 50, None), ('s4-75-av', 75, None)):
    e = E15[f]; ajout = f" Écoute passée d'elle-même sur {'le pontet du bout du flotteur' if e['pos'] >= 4995 else 'un pontet du flotteur, à x ' + mil(e['pos'])}." if e['typ'] == 'flotteur' else f" Écoute sur la poutre AR, y {mil(e['pos'])}."
    q = S + f'slides/{sid}.html'; t = open(q, encoding='utf-8').read()
    m = re.search(r'(border-left:4px solid #1f6f8b[^"]*">)([^<]*)(</p>)', t, re.I)
    corps = re.sub(r" Écoute (passée d(?:'|&#x27;)elle-même sur|sur la poutre AR)[^.]*\.", '', m.group(2))
    t = t[:m.start(2)] + corps + esc(ajout) + t[m.end(2):]
    open(q, 'w', encoding='utf-8').write(t)
    print(sid, '→', (corps + ajout)[-140:])

d = json.load(open(S + 'deck.json')); o = d['order']
if 'd-equipage' not in o: o.insert(o.index('d-banc-res') + 1, 'd-equipage')
json.dump(d, open(S + 'deck.json', 'w'), ensure_ascii=False, indent=1)
print(len(o), 'diapos ; d-equipage après', o[o.index('d-equipage') - 1])
print('textes :', len(equipage), len(ecoute))
