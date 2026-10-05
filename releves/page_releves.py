import json, html
d = json.load(open('/tmp/claude-0/rel_data.json'))
M, imgs, P7 = d['M'], d['imgs'], d['P7']
esc = html.escape
sections = []
for key in ('profil', 'dessus', 'avant', 'arriere'):
    titre, note, rows = M[key]
    trs = ''.join(f'''<tr><td class="id"><span class="chip">{esc(i)}</span></td><td>{esc(t)}</td><td class="n">{esc(mv)}</td>
      <td class="in"><input id="m-{esc(i)}" data-id="{esc(i)}" data-lib="{esc(t)}" data-u="{esc(u)}" inputmode="decimal" autocomplete="off" aria-label="{esc(i)} en {esc(u)}"><span class="u">{esc(u)}</span></td></tr>''' for i, t, u, mv in rows)
    sections.append(f'''<section class="vue" id="{key}">
  <h2>{esc(titre)}</h2>
  {f'<p class="note">{esc(note)}</p>' if note else ''}
  <figure><img src="{imgs[key]}" alt="{esc(titre)} annotée avec les repères de mesure" loading="lazy"></figure>
  <div class="tbl"><table><thead><tr><th>Repère</th><th>À mesurer</th><th>Modèle</th><th>Relevé</th></tr></thead><tbody>{trs}</tbody></table></div>
</section>''')
    if key == 'profil':
        cells = ''.join(f'<tr><td class="n">{x/1000:.1f} m</td><td class="n">{v}</td><td class="in"><input id="m-P7-{x}" data-id="P7 à {x/1000:.1f} m" data-lib="flèche cordeau → pont" data-u="mm" inputmode="decimal" autocomplete="off" aria-label="Flèche à {x/1000:.1f} m"><span class="u">mm</span></td></tr>' for x, v in P7)
        sections.append(f'''<section class="vue" id="p7">
  <h2><span class="chip cyan">P7</span> Ligne de pont au cordeau</h2>
  <p class="note">Tendre un cordeau de la pointe de l'étrave au haut du tableau, sur le bord extérieur du pont. Mesurer à l'équerre la distance cordeau → pont tous les 50 cm depuis l'étrave. Indépendant de l'assiette de la remorque.</p>
  <div class="tbl narrow"><table><thead><tr><th>Depuis l'étrave</th><th>Modèle</th><th>Relevé</th></tr></thead><tbody>{cells}</tbody></table></div>
</section>''')
page = f'''<title>Relevés HC16</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{--paper:#EEF1F0;--sheet:#F9FAF9;--ink:#15232A;--ink2:#4B5B62;--rule:#C7D0D3;--chip:#FFD400;--chipink:#141414;--cyan:#12A7C9;--warn:#B8650E;--accent:#0E7C95;
  --f-disp:"Barlow Semi Condensed","Arial Narrow",system-ui,sans-serif;--f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#101A1E;--sheet:#152228;--ink:#DDE6E9;--ink2:#9DB0B7;--rule:#2C3C43;--accent:#5CC3DB;--warn:#E3A35A;color-scheme:dark}}}}
:root[data-theme="dark"]{{--paper:#101A1E;--sheet:#152228;--ink:#DDE6E9;--ink2:#9DB0B7;--rule:#2C3C43;--accent:#5CC3DB;--warn:#E3A35A;color-scheme:dark}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 var(--f-body);padding-inline:16px;padding-block:28px 110px}}
.wrap{{max-width:1180px;margin:0 auto;display:grid;gap:40px}}
h1,h2{{font-family:var(--f-disp);font-weight:700;letter-spacing:.01em;line-height:1.15;text-wrap:balance;margin:0}}
h1{{font-size:clamp(30px,5vw,46px)}} h2{{font-size:26px;display:flex;gap:10px;align-items:center}}
.eyebrow{{font:500 12px/1 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--ink2)}}
header{{display:grid;gap:12px;border-bottom:1px solid var(--rule);padding-bottom:22px}}
.lead{{color:var(--ink2);max-width:72ch;margin:0}}
.res{{background:var(--sheet);border:1px solid var(--rule);border-left:4px solid var(--chip);padding:16px 18px;display:grid;gap:10px;max-width:880px}}
.res h2{{font-size:22px}} .res p{{margin:0;max-width:76ch}}
.big{{display:flex;flex-wrap:wrap;gap:8px 28px;font-family:var(--f-mono);color:var(--ink2);font-size:13px}}
.big b{{font-size:22px;color:var(--ink);font-weight:500;margin-right:6px}}
.vue{{display:grid;gap:14px}} .note{{color:var(--ink2);margin:0;max-width:78ch}}
figure{{margin:0;border:1px solid var(--rule);background:var(--sheet)}} figure img{{display:block;width:100%;height:auto}}
.tbl{{overflow-x:auto;border:1px solid var(--rule);background:var(--sheet)}} .tbl.narrow{{max-width:520px}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th{{font:500 11px/1.2 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);text-align:left;padding:10px 10px;border-bottom:1px solid var(--rule)}}
td{{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:middle}}
tr:last-child td{{border-bottom:0}}
td.n{{font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--ink2)}}
td.id{{width:1%}} td.in{{white-space:nowrap;width:1%}}
.chip{{display:inline-block;background:var(--chip);color:var(--chipink);font:700 14px/1 var(--f-mono);padding:5px 8px;border:2px solid #141414;border-radius:7px}}
.chip.cyan{{background:#6FD8EF}}
input{{font:500 15px/1.2 var(--f-mono);width:8.5em;padding:7px 8px;border:1px solid var(--rule);border-radius:4px;background:var(--paper);color:var(--ink);text-align:right}}
input:focus-visible{{outline:2px solid var(--accent);outline-offset:1px}}
input.rempli{{border-color:var(--accent)}}
.u{{font:400 12px var(--f-mono);color:var(--ink2);margin-left:6px}}
.barre{{position:fixed;left:0;right:0;bottom:0;padding:12px 16px calc(12px + env(safe-area-inset-bottom,0px));background:var(--sheet);border-top:1px solid var(--rule);display:flex;gap:14px;align-items:center;justify-content:center;flex-wrap:wrap}}
button{{font:600 15px/1 var(--f-body);padding:11px 18px;border-radius:6px;border:2px solid #141414;background:var(--chip);color:#141414;cursor:pointer}}
button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
#etat{{font:400 13px var(--f-mono);color:var(--ink2)}}
#sortie{{width:100%;min-height:9em;font:13px/1.5 var(--f-mono);background:var(--sheet);color:var(--ink);border:1px solid var(--rule);padding:10px}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
<div class="wrap">
<header>
  <span class="eyebrow">Hobie 16 · gréement Rando · relevés sur le bateau</span>
  <h1>Relevés HC16</h1>
  <p class="lead">Chaque repère des photos correspond à une ligne des tableaux, avec la valeur actuelle du modèle. Saisis tes mesures sur place, puis « Copier les relevés » et colle le texte dans la conversation : le modèle, les plans et la tente seront recalés dessus. La saisie reste dans ce navigateur.</p>
</header>
<div class="res">
  <h2>Angle du pont au pied de mât</h2>
  <div class="big"><span><b>+1,7°</b> en long, d'après la photo de profil</span><span><b>−0,7°</b> dans le modèle</span><span><b>≈ 10°</b> en travers, modèle</span></div>
  <p>Sur le profil, la bande décorative (parallèle au bord du pont) a son point bas sous la poutre avant, pas 40 cm devant comme dans le modèle. Au pied de mât prévu, le pont monte donc vers l'étrave d'environ 1,7° par rapport au longeron (incertitude ±0,7° : perspective, bande supposée parallèle au pont). La remorque met le bateau nez en bas d'environ 1,1°, corrigé par le longeron.</p>
  <p>En travers, le pied est sur le bombé du pont : ces photos ne permettent pas de le mesurer. Le modèle donne environ 10°, pont descendant vers l'extérieur. Relevés P4, Q, V6 et V7 pour trancher ; ils fixent l'épaisseur des cales de l'embase de mât.</p>
</div>
{''.join(sections)}
<section class="vue"><h2>Texte à coller</h2><textarea id="sortie" readonly aria-label="Relevés au format texte"></textarea></section>
</div>
<div class="barre"><button id="copier" type="button">Copier les relevés</button><span id="etat">0 valeur saisie</span></div>
<script>
const ins = [...document.querySelectorAll('input[data-id]')];
const K = 'releves-hc16';
try {{ const s = JSON.parse(localStorage.getItem(K) || '{{}}'); ins.forEach(i => {{ if (s[i.id]) i.value = s[i.id]; }}); }} catch (e) {{}}
function texte() {{
  const l = ins.filter(i => i.value.trim()).map(i => `${{i.dataset.id}} (${{i.dataset.lib}}) : ${{i.value.trim()}} ${{i.dataset.u}}`);
  return l.length ? 'Relevés HC16\\n' + l.join('\\n') : '';
}}
function maj() {{
  const n = ins.filter(i => i.value.trim()).length;
  ins.forEach(i => i.classList.toggle('rempli', !!i.value.trim()));
  document.getElementById('etat').textContent = n + (n > 1 ? ' valeurs saisies' : ' valeur saisie');
  document.getElementById('sortie').value = texte();
  try {{ const s = {{}}; ins.forEach(i => {{ if (i.value.trim()) s[i.id] = i.value; }}); localStorage.setItem(K, JSON.stringify(s)); }} catch (e) {{}}
}}
ins.forEach(i => i.addEventListener('input', maj)); maj();
document.getElementById('copier').addEventListener('click', () => {{
  const t = texte(), e = document.getElementById('etat');
  if (!t) {{ e.textContent = 'Aucune valeur à copier'; return; }}
  navigator.clipboard.writeText(t).then(() => {{ e.textContent = 'Copié : colle-le dans la conversation'; }})
    .catch(() => {{ const s = document.getElementById('sortie'); s.focus(); s.select(); e.textContent = 'Texte sélectionné : copie-le à la main'; }});
}});
</script>'''
open('releves_hc16.html', 'w').write(page)
print(len(page) // 1024, 'ko')
