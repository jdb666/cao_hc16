"""Pages « Fiche technique » du book (section 08) depuis etudes/fiche_technique.json : s8, f-comparaison, f-poids.
python3 book/fiche_slides.py"""
import json, html
F = json.load(open('/home/claude/cao/etudes/fiche_technique.json'))
OUT = '/home/claude/cao/book/deck/slides/'
esc = html.escape
num = lambda v, d=0: (f'{v:,.{d}f}').replace(',', ' ').replace('.', ',')
R, Hc, C, Hy, Vo = F['rando'], F['hc16'], F['charge'], F['hydro'], F['volumes']
MONO = "font-family:'IBM Plex Mono', 'Courier New', monospace"
DISP = "font-family:'Barlow Semi Condensed', Arial, sans-serif"
PAGE = lambda col: f'<p style="position:absolute;right:128px;bottom:56px;width:120px;text-align:right;{MONO};font-size:24px;color:{col}">0</p>'
arr = lambda v: int(5 * round(v / 5))           # poids estimés : à 5 kg près
vide = arr(R['vide']); utile_ce = int(C['depl_ce'] - vide); utile_us = int(C['depl_us'] - vide)
XP = F['x_equipage_a_plat']; REF = F['cas']['HC16, 2 équipiers près de la poutre AV (référence)']; PO = F['positions']
bag = utile_ce - 160

# ---------------------------------------------------------------- s8 : intercalaire
big = [(f'≈ {vide} kg', f"à vide, prêt à naviguer, sans ancre (HC16 d'origine : {num(Hc['poids'])} kg)"),
       (f"{Vo['hors_centre']} L", f"de rangement dans le coffre hors batterie et moteur, plus {Vo['bancs_par_cote']} L sous chaque banc"),
       (f'≈ {utile_ce} kg', f"de charge utile au déplacement maxi CE du HC16 ({num(C['depl_ce'])} kg) ; HC16 : 240 kg")]
cells = ''.join(f'<div style="flex:1;display:flex;flex-direction:column;gap:8px;border-top:2px solid #6DB9D4;padding:20px 0px 0px 0px">'
                f'<p style="{MONO};font-size:44px;line-height:1.15;color:#EDF0F0">{esc(a)}</p><p style="font-size:24px;line-height:1.35;color:#9AABB3">{esc(b)}</p></div>' for a, b in big)
s8 = f'''<section id="s8" style="background:#18262E;color:#EDF0F0;font-family:'IBM Plex Sans', Arial, sans-serif;padding:128px 128px 160px;display:flex;flex-direction:column;justify-content:space-between">
<div style="display:flex;flex-direction:column;gap:28px">
<p style="{MONO};font-size:28px;letter-spacing:2px;color:#6DB9D4">08</p>
<h2 style="{DISP};font-size:64px;font-weight:600;line-height:1.1;color:#EDF0F0">Fiche technique</h2>
<p style="width:1300px;font-size:28px;line-height:1.45;color:#B8C6CC">Poids estimés pièce par pièce depuis le modèle et le plan de découpe, volumes du coffre, charge utile et assiette calculées sur les coques du modèle, comparés au HC16 d'origine.</p>
</div>
<div style="display:flex;flex-direction:row;gap:48px">
{cells}
</div>
{PAGE('#9AABB3')}
</section>
'''

# ---------------------------------------------------------------- f-comparaison
th = lambda t, w, al='left': f'<th style="width:{w}%;text-align:{al}">{esc(t)}</th>'
td = lambda t, al='left', b=False: f'<td style="text-align:{al}">{"<b>" if b else ""}{esc(t)}{"</b>" if b else ""}</td>'
lignes = [
    ('Longueur × largeur', '5,04 × 2,41 m', '5,04 × 2,41 m', ''),
    ('Poids prêt à naviguer', f"{num(Hc['poids'])} kg (Hobie)", f'≈ {vide} kg', f'+ {vide - int(Hc["poids"])} kg'),
    ('Gréement', "1 mât alu 8,07 m sur la poutre AV, GV + foc", '2 mâts carbone 7,30 m sur les coques', ''),
    ('Voilure', '18,9 m²', '22,2 m², deux voiles sur enrouleur', '+ 17 %'),
    ('Centre vélique x · z', '3 206 · 3 735', '3 206 · 3 993', '258 plus haut'),
    ('Couple de chavirage', '100 %', '125 %', ''),
    ('Rangement', 'aucun', f"coffre {Vo['hors_centre']} L + bancs 2 × {Vo['bancs_par_cote']} L", ''),
    ('Moteur', 'aucun', 'Protruar 2.0, 24 V 100 Ah (2,4 kWh)', ''),
    (f"Charge utile, déplacement maxi CE {num(C['depl_ce'])} kg", '240 kg', f'≈ {utile_ce} kg', f'− {240 - utile_ce} kg'),
    (f"Charge utile, déplacement maxi US {num(C['depl_us'])} kg", '362 kg', f'≈ {utile_us} kg', f'− {362 - utile_us} kg'),
]
rows = ''.join('<tr>' + td(a) + td(b) + td(c, b=True) + td(d, 'right') + '</tr>\n' for a, b, c, d in lignes)
fc = f'''<section id="f-comparaison" style="background:#EDF0F0;color:#18262E;font-family:'IBM Plex Sans', Arial, sans-serif">
<p style="position:absolute;left:128px;top:64px;width:1200px;{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:#1F6F8B">08 · Fiche technique</p>
<h2 style="position:absolute;left:128px;top:100px;width:1600px;{DISP};font-size:44px;font-weight:600;line-height:1.15;color:#18262E">HC16 d'origine et HC16 Rando</h2>
<table style="position:absolute;left:128px;top:190px;width:1664px;font-size:24px;color:#18262E">
<tr>{th('', 30)}{th("HC16 d'origine", 25)}{th('HC16 Rando : deux mâts, coffre, moteur', 31)}{th('Écart', 14, 'right')}</tr>
{rows}</table>
<p style="position:absolute;left:128px;top:880px;width:1664px;font-size:22px;line-height:1.4;color:#4A5A63">HC16 : données Hobie (poids 145 kg, charge maxi 240 kg en CE, 362 kg aux États-Unis). Rando : poids estimés, détail page suivante. Même déplacement maxi pour les deux : la charge utile baisse de ce que pèsent coffre, moteur et batterie.</p>
{PAGE('#4A5A63')}
</section>
'''

# ---------------------------------------------------------------- f-poids
cd = R['coffre_detail']; gd = R['gréement_detail']
poids = [
    ('Plateforme HC16 sans son gréement', f"≈ {arr(R['plateforme'])} kg", f"145 kg moins un gréement d'origine estimé à {arr(Hc['gréement'])} kg"),
    ('Gréement Rando', f"≈ {arr(R['gréement'])} kg", f"mâts carbone 2 × 6,5 (estimé), voiles 2 × 3,5, colliers et emplantures CP, tube, semelles, haubans"),
    ('Coffre et bancs', f"≈ {arr(R['coffre_bancs'])} kg", f"CP {num(cd['cp'])} kg sur {num(cd['aire_m2'], 1)} m², époxy, verre et peinture {num(cd['stratification'])} kg, tubes, cordages, quincaillerie"),
    ('Moteur et batterie', f"{num(R['moteur'], 1)} kg", 'Protruar 6,7 ; Dyness 19,3 ; bac 3 ; câbles 1,5'),
    ('À vide, prêt à naviguer', f'≈ {vide} kg', f"ancre en plus : {num(R['ancre'], 1)} kg"),
]
rp = ''.join(f'<tr><td>{"<b>" if i == len(poids) - 1 else ""}{esc(a)}{"</b>" if i == len(poids) - 1 else ""}</td><td style="text-align:right">{"<b>" if i == len(poids) - 1 else ""}{esc(b)}{"</b>" if i == len(poids) - 1 else ""}</td><td style="color:#4A5A63;font-size:20px">{esc(c)}</td></tr>\n'
             for i, (a, b, c) in enumerate(poids))
cas = F['cas']
def ligne_cas(lib, k, garde=True):
    e = cas[k]
    a = e['assiette']
    sens = '—' if k.startswith('HC16, 2') else 'à plat' if abs(a) < 0.1 else (f"{num(abs(a), 1)}° sur le nez" if a > 0 else f"{num(abs(a), 1)}° sur l'arrière")
    sg = lambda v: ('+ ' if v > 0 else '− ' if v < 0 else '') + str(abs(v))
    de, dt = sg(e["etrave"] - REF["etrave"]), sg(e["tableau"] - REF["tableau"])
    g = str(e["garde_coffre"]) if garde else '—'
    return (f'<tr><td>{esc(lib)}</td><td style="text-align:right">{num(e["M"])} kg</td><td style="text-align:right">{esc(sens)}</td>'
            f'<td style="text-align:right">{de}</td><td style="text-align:right">{dt}</td><td style="text-align:right">{g}</td></tr>\n')
rc = (ligne_cas("HC16, 2 équipiers près de la poutre AV (référence)", 'HC16, 2 équipiers près de la poutre AV (référence)', garde=False)
      + ligne_cas('Rando, même équipage, coffre vide', 'Rando, 2 équipiers, coffre vide')
      + ligne_cas('Rando, même équipage + 30 kg au coffre', 'Rando, 2 équipiers + 30 kg au coffre')
      + ligne_cas('Rando, même équipage + 60 kg au coffre', 'Rando, 2 équipiers + 60 kg au coffre')
      + ligne_cas("Rando, même équipage + 60 kg sous l'arrière des bancs", "Rando, 2 équipiers + 60 kg sous l'arrière des bancs"))
BI = F['bilan_moments']; gre_ = BI['gréement HC16 enlevé'] + BI['gréement Rando']; tot_ = sum(BI.values())
fp = f'''<section id="f-poids" style="background:#EDF0F0;color:#18262E;font-family:'IBM Plex Sans', Arial, sans-serif">
<p style="position:absolute;left:128px;top:64px;width:1200px;{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:#1F6F8B">08 · Fiche technique</p>
<h2 style="position:absolute;left:128px;top:100px;width:1600px;{DISP};font-size:44px;font-weight:600;line-height:1.15;color:#18262E">Poids, charge et assiette</h2>
<table style="position:absolute;left:128px;top:180px;width:1664px;font-size:22px;color:#18262E">
<tr><th style="width:26%">Poste</th><th style="width:12%;text-align:right">Poids</th><th style="width:62%">Détail</th></tr>
{rp}</table>
<table style="position:absolute;left:128px;top:540px;width:1664px;font-size:22px;color:#18262E">
<tr><th style="width:40%">Chargement</th><th style="width:11%;text-align:right">Déplacement</th><th style="width:14%;text-align:right">Écart d'assiette</th><th style="width:12%;text-align:right">Eau à l'étrave</th><th style="width:11%;text-align:right">Au tableau</th><th style="width:12%;text-align:right">Garde du coffre</th></tr>
{rc}</table>
<p style="position:absolute;left:128px;top:900px;width:1664px;font-size:20px;line-height:1.4;color:#4A5A63">Calcul statique (au repos), équipage près de la poutre AV (x {num(PO['equipage'])}) sur les deux bateaux. Écart dû aux poids : batterie {num(BI['batterie, bac, câbles'])} kg·m, coffre {num(BI['coffre et bancs'])}, gréement {num(gre_)}, moteur {num(BI['moteur'])} ; {num(tot_)} kg·m ≈ {num(tot_ / F['mct'], 1)}°. En route, la vitesse enfonce l'arrière et la voile appuie sur le nez, autant pour les deux : là où le HC16 s'assied sur l'arrière, la Rando le fera d'environ 1° de moins. Même assiette que le HC16 : équipage {num((XP['coffre vide'] - PO['equipage']) / 1000, 2)} m plus en arrière coffre vide, {num((XP['60 kg au coffre'] - PO['equipage']) / 1000, 2)} m avec 60 kg au coffre.</p>
{PAGE('#4A5A63')}
</section>
'''
for nom, s in (('s8', s8), ('f-comparaison', fc), ('f-poids', fp)):
    open(OUT + nom + '.html', 'w', encoding='utf-8').write(s)
print('ok', vide, utile_ce, utile_us, bag)
