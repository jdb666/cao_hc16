"""Page « Découpe coffre HC16 » : plaques imbriquées (SVG), nomenclature, contrôle du dépliage, notes de fabrication.
Lit plans/decoupe3.json (decoupe3.py) et plans/decoupe3_extra.json (fournitures hors plan) -> plans/decoupe_coffre_hc16.html"""
import json, html, os, re
from shapely.geometry import Polygon
from shapely.ops import polylabel
D = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(f"{D}/decoupe3.json"))
X = json.load(open(f"{D}/decoupe3_extra.json")) if os.path.exists(f"{D}/decoupe3_extra.json") else {}
esc = html.escape
nb = lambda v, d=0: f"{v:,.{d}f}".replace(",", " ").replace(".", ",")

P = {p['ref']: p for p in J['pieces']}
EPS = sorted({p['ep'] for p in J['pieces']})
SH = J['panneau'][1]

# ---------------------------------------------------------------- chiffres
n_refs = len(J['pieces']); n_pcs = sum(p['qte'] for p in J['pieces'])
pl_ep = {ep: [pl for pl in J['planches'] if pl['ep'] == ep] for ep in EPS}
compte = lambda ep: sum(0.5 if pl['sw'] < 2000 else 1 for pl in pl_ep[ep])
surf_cp = sum(p['aire'] * p['qte'] for p in J['pieces'])
surf_pl = sum(pl['sw'] * SH for pl in J['planches']) / 1e6
fmt_n = lambda v: (nb(v) if v == int(v) else nb(v, 1))

# ---------------------------------------------------------------- plaques
def etiquette(d):
    """Position, taille et sens du repère : pôle d'inaccessibilité de la pièce (trous compris) s'il y a la place,
    sinon celui du contour extérieur (au milieu du vide pour un cadre étroit) ; vertical sur une pièce haute et étroite."""
    rings = [[(float(a), float(b)) for a, b in (q.split(',') for q in r.strip().split())] for r in re.findall(r'M([^Z]*)Z', d)]
    ext = Polygon(rings[0]).buffer(0)
    mat = Polygon(rings[0], rings[1:]).buffer(0)
    ext = ext if ext.geom_type == 'Polygon' else max(ext.geoms, key=lambda g: g.area)
    mat = mat if mat.geom_type == 'Polygon' else max(mat.geoms, key=lambda g: g.area)
    p = polylabel(mat, tolerance=2.0); r = mat.exterior.distance(p)
    if mat.interiors:
        r = min(r, min(Polygon(i).exterior.distance(p) for i in mat.interiors))
    if r < 35 and mat.interiors:
        p = polylabel(ext, tolerance=2.0); r = 35
    x0, y0, x1, y1 = mat.bounds
    vert = (y1 - y0) > 1.6 * (x1 - x0)
    return p.x, p.y, max(14, min(34, 0.8 * r)), vert

def svg_plaque(pl):
    sw = pl['sw']
    out = [f'<svg class="plaque" viewBox="-20 {-SH - 20} {sw + 40} {SH + 70}" style="width:{(sw + 40) / 2540 * 100:.1f}%;min-width:{560 * (sw + 40) / 2540:.0f}px" role="img" aria-label="Plaque {esc(pl["id"])} : CP {pl["ep"]}, {sw} × {SH}, {len(pl["pieces"])} pièces">',
           f'<rect class="pl-fond" x="0" y="{-SH}" width="{sw}" height="{SH}"/>']
    for q in pl['pieces']:
        p = P.get(q['ref'], {})
        tip = f"{q['ref']} — {p.get('nom', '')}, CP {pl['ep']}"
        ex, ey, fs, vert = etiquette(q['d'])            # chemin déjà en y SVG (y = -y plaque)
        rot = f' transform="rotate(-90 {ex:.0f} {ey:.0f})"' if vert else ''
        out.append(f'<g class="pc" data-ref="{esc(q["ref"])}" tabindex="0"><title>{esc(tip)}</title><path d="{q["d"]}"/>'
                   f'<text x="{ex:.0f}" y="{ey:.0f}" style="font-size:{fs:.0f}px"{rot}>{esc(q["ref"])}</text></g>')
    out.append(f'<text class="pl-cote" x="{sw / 2}" y="40" text-anchor="middle">{nb(sw)} × {nb(SH)}</text>')
    out.append('</svg>')
    return ''.join(out)

def mini(p):
    w, h = p['dim']
    m = max(w, h) * 0.04
    return f'<svg class="mini" viewBox="{-m:.0f} {-h - m:.0f} {w + 2 * m:.0f} {h + 2 * m:.0f}" aria-hidden="true"><path d="{p["d"]}"/></svg>'

filtres = ''.join(f'<button class="f" type="button" data-ep="{ep}" aria-pressed="false">CP {ep}</button>' for ep in EPS)
plaques = []
for ep in EPS:
    for pl in pl_ep[ep]:
        taux = round(pl['taux'] * 100)
        demi = ' (demi-plaque)' if pl['sw'] < 2000 else ''
        plaques.append(f'<figure class="pl" data-ep="{ep}"><figcaption><span class="t">Plaque {esc(pl["id"])}</span>'
                       f'<span class="m">CP {ep} · {nb(pl["sw"])} × {nb(SH)}{demi} · {len(pl["pieces"])} pièces · {taux} % utilisés</span></figcaption>'
                       f'<div class="svgbox">{svg_plaque(pl)}</div></figure>')

# ---------------------------------------------------------------- nomenclature
def ordre(p):
    m = re.match(r'([A-Z]+)(\d*)', p['ref']); return (p['ep'], m.group(1), int(m.group(2) or 0))
lignes = []
for p in sorted(J['pieces'], key=ordre):
    w, h = p['dim']
    plis = f"<small>{p['plis']} plis collés</small>" if (p.get('plis') or 1) > 1 else ''
    note = esc(re.sub(r'épaisseur modèle \d+ ; ', '', p['note'])).replace('babord', 'bâbord')
    lignes.append(f'<tr data-ref="{esc(p["ref"])}" tabindex="0"><td class="ref">{esc(p["ref"])}</td><td>{mini(p)}</td>'
                  f'<td class="nom">{esc(p["nom"])}<small class="ou">{note}</small></td><td class="n">{p["ep"]}</td>'
                  f'<td class="n">{p["qte"]}{plis}</td><td class="n">{nb(w)} × {nb(h)}</td><td class="n">{nb(p["aire"], 3)}</td></tr>')

ctrl = []
agr = {}
for c in J.get('controle', []):                      # un panneau par repère (les symétriques sont identiques)
    a = agr.setdefault(c['ref'], dict(ref=c['ref'], aire3d=c['aire3d'], aire2d=c['aire2d'], n=0)); a['n'] += 1
for c in agr.values():
    ec = (c['aire2d'] - c['aire3d']) / c['aire3d'] * 100 if c['aire3d'] else 0
    c = dict(c, ref=c['ref'] + (f" × {c['n']}" if c['n'] > 1 else ''))
    ctrl.append(f'<tr><td class="ref">{esc(str(c["ref"]))}</td><td class="n">{nb(c["aire3d"], 4)}</td><td class="n">{nb(c["aire2d"], 4)}</td><td class="n">{ec:+.2f}'.replace('.', ',') + ' %</td></tr>')
ec_max = max((abs(c['aire2d'] - c['aire3d']) / c['aire3d'] * 100 for c in J.get('controle', []) if c['aire3d']), default=0)

hors = ''.join(f'<li>{x}</li>' for x in X.get('hors', []))
notes = ''.join(f'<li>{x}</li>' for x in X.get('notes', []))
resume_pl = ' · '.join(f"CP {ep} : {fmt_n(compte(ep))}" for ep in EPS)

page = f'''<title>Découpe coffre HC16</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Mise en page : feuille d'atelier, plaques pleine largeur puis nomenclature ; mêmes jetons que la page Plateforme HC16 */
:root{{
  --paper:#EDF0F0; --sheet:#F7F8F8; --ink:#18262E; --ink2:#4A5A63; --rule:#C5CED2; --grid:#DCE2E4;
  --accent:#1F6F8B; --wood:#9C5F2C; --woodbg:#EFD9C0; --hl:#1F6F8B;
  --f-disp:"Barlow Semi Condensed","Arial Narrow",Arial,sans-serif;
  --f-body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --f-mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{ color-scheme:dark;
    --paper:#10181C; --sheet:#152026; --ink:#DCE4E7; --ink2:#9AABB3; --rule:#2E3D44; --grid:#223037;
    --accent:#6DB9D4; --wood:#D99A5E; --woodbg:#3B2A1C; --hl:#6DB9D4; }}
}}
:root[data-theme="dark"]{{ color-scheme:dark;
  --paper:#10181C; --sheet:#152026; --ink:#DCE4E7; --ink2:#9AABB3; --rule:#2E3D44; --grid:#223037;
  --accent:#6DB9D4; --wood:#D99A5E; --woodbg:#3B2A1C; --hl:#6DB9D4; }}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 var(--f-body);padding-inline:16px;padding-block:28px 64px}}
.wrap{{max-width:1180px;margin:0 auto;display:flex;flex-direction:column;gap:44px}}
h1,h2{{font-family:var(--f-disp);font-weight:600;letter-spacing:.01em;text-wrap:balance;margin:0}}
h1{{font-size:clamp(30px,4.2vw,44px);line-height:1.05}}
h2{{font-size:25px;line-height:1.15}}
p{{margin:0;max-width:72ch}}
.eyebrow{{font:500 12px/1 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--ink2)}}
header{{display:grid;gap:14px;border-bottom:1px solid var(--rule);padding-bottom:22px}}
.lead{{color:var(--ink2)}}
.figs{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px 24px;margin-top:6px}}
.figs div{{display:grid;gap:2px;border-top:2px solid var(--ink);padding-top:8px;min-width:0}}
.figs span{{font:500 11px/1.3 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink2)}}
.figs b{{font:500 18px/1.25 var(--f-mono);font-variant-numeric:tabular-nums}}
section{{display:grid;gap:16px;min-width:0}}
.filtres{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.filtres span{{font:500 12px/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);margin-right:4px}}
button.f{{font:500 13px/1 var(--f-mono);padding:8px 12px;border:1px solid var(--rule);background:var(--sheet);color:var(--ink);cursor:pointer}}
button.f[aria-pressed="true"]{{background:var(--ink);color:var(--paper);border-color:var(--ink)}}
button.f:focus-visible,.pc:focus-visible,tr:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.plaques{{display:grid;gap:22px}}
figure{{margin:0}}
.pl{{background:var(--sheet);border:1px solid var(--rule);padding:12px 14px 10px;display:grid;gap:8px;min-width:0}}
figcaption{{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline}}
figcaption .t{{font:600 17px/1.2 var(--f-disp);letter-spacing:.02em}}
figcaption .m{{font:400 12.5px/1.3 var(--f-mono);color:var(--ink2);font-variant-numeric:tabular-nums}}
.svgbox{{overflow-x:auto}}
svg.plaque{{display:block;height:auto}}
.pl-fond{{fill:var(--paper);stroke:var(--ink2);stroke-width:3}}
.pl-cote{{font:500 30px var(--f-mono);fill:var(--ink2)}}
.pc path{{fill:var(--woodbg);stroke:var(--wood);stroke-width:2.2;fill-rule:evenodd}}
.pc text{{font:500 34px var(--f-mono);fill:var(--ink);text-anchor:middle;dominant-baseline:middle;pointer-events:none}}
.pc{{cursor:pointer}}
.pc.hl path{{fill:var(--hl);fill-opacity:.35;stroke:var(--hl);stroke-width:4}}
.tab{{overflow-x:auto;border:1px solid var(--rule);background:var(--sheet)}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:7px 10px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:middle}}
th{{font:500 11.5px/1.3 var(--f-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);background:var(--paper);position:sticky;top:0}}
td.n,th.n{{text-align:right;font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap}}
td.ref{{font:600 15px/1 var(--f-mono);white-space:nowrap}}
td.nom{{min-width:240px}}
td small{{display:block;color:var(--ink2);font-size:12px;line-height:1.35}}
td small.ou{{font-family:var(--f-mono);font-size:11px;word-break:break-word}}
tr.hl td{{background:color-mix(in srgb,var(--hl) 14%,transparent)}}
svg.mini{{display:block;width:74px;height:40px}}
svg.mini path{{fill:var(--woodbg);stroke:var(--wood);stroke-width:1;vector-effect:non-scaling-stroke;fill-rule:evenodd}}
ul.notes{{margin:0;padding-left:20px;display:grid;gap:8px;max-width:80ch}}
.cols{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:28px;align-items:start}}
@media (max-width:820px){{.cols{{grid-template-columns:1fr}}}}
@media (prefers-reduced-motion:no-preference){{.pc path,tr td{{transition:fill .15s,background .15s}}}}
</style>
<div class="wrap">
<header>
  <div class="eyebrow">Nacra 5.80 Rando · coffre HC16 · état du {esc(J['date'])}</div>
  <h1>Plan de découpe du coffre</h1>
  <p class="lead">Tout sort du modèle CAO : le bordé est déplié exactement, facette par facette, depuis sa face extérieure ; les pièces planes sont prises dans leur plan, trous compris. Pièces imbriquées par épaisseur sur des plaques de CP de 2 500 × 1 220, 10 de marge, 8 entre pièces. Les DXF (une plaque par fichier, et une pièce par fichier, à l'échelle 1) sont joints à part. Survoler une pièce ou une ligne de la nomenclature la montre partout.</p>
  <div class="figs">
    <div><span>Repères</span><b>{n_refs}</b></div>
    <div><span>Pièces à découper</span><b>{n_pcs}</b></div>
    <div><span>Plaques 2 500 × 1 220</span><b>{fmt_n(sum(compte(ep) for ep in EPS))}</b></div>
    <div><span>Par épaisseur</span><b style="font-size:14px">{resume_pl}</b></div>
    <div><span>Surface de CP découpée</span><b>{nb(surf_cp, 1)} m²</b></div>
    <div><span>Écart de dépliage maxi</span><b>{nb(ec_max, 2)} %</b></div>
  </div>
</header>

<section aria-labelledby="t-pl">
  <h2 id="t-pl">Plaques</h2>
  <div class="filtres" role="group" aria-label="Épaisseur"><span>Épaisseur</span><button class="f" type="button" data-ep="tout" aria-pressed="true">Toutes</button>{filtres}</div>
  <div class="plaques">{''.join(plaques)}</div>
</section>

<section aria-labelledby="t-nom">
  <h2 id="t-nom">Nomenclature</h2>
  <p class="lead">Les pièces symétriques bâbord / tribord sont regroupées sous un repère : même contour, une retournée. Les pièces épaisses sont faites de plis collés ; la quantité compte les plis.</p>
  <div class="tab"><table>
    <thead><tr><th>Repère</th><th>Forme</th><th>Pièce · où</th><th class="n">CP</th><th class="n">Qté</th><th class="n">Encombrement</th><th class="n">m² l'une</th></tr></thead>
    <tbody>{''.join(lignes)}</tbody>
  </table></div>
</section>

<div class="cols">
<section aria-labelledby="t-fab">
  <h2 id="t-fab">Fabrication</h2>
  <ul class="notes">{notes}</ul>
</section>
<section aria-labelledby="t-ctl">
  <h2 id="t-ctl">Contrôle du dépliage</h2>
  <p class="lead">Surface de chaque panneau du bordé, mesurée sur le modèle 3D puis sur le contour déplié.</p>
  <div class="tab"><table>
    <thead><tr><th>Panneau</th><th class="n">3D, m²</th><th class="n">Déplié, m²</th><th class="n">Écart</th></tr></thead>
    <tbody>{''.join(ctrl)}</tbody>
  </table></div>
  <h2 id="t-hors" style="margin-top:14px">Hors plan</h2>
  <ul class="notes">{hors}</ul>
</section>
</div>
</div>
<script>
(function(){{
  const surl = (ref, on) => document.querySelectorAll('[data-ref="' + CSS.escape(ref) + '"]').forEach(e => e.classList.toggle('hl', on));
  document.querySelectorAll('[data-ref]').forEach(e => {{
    const r = e.getAttribute('data-ref');
    e.addEventListener('mouseenter', () => surl(r, true)); e.addEventListener('mouseleave', () => surl(r, false));
    e.addEventListener('focus', () => surl(r, true)); e.addEventListener('blur', () => surl(r, false));
  }});
  const bts = document.querySelectorAll('button.f');
  bts.forEach(b => b.addEventListener('click', () => {{
    const ep = b.dataset.ep;
    bts.forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
    document.querySelectorAll('figure.pl').forEach(f => {{ f.hidden = !(ep === 'tout' || f.dataset.ep === ep); }});
  }}));
}})();
</script>
'''
open(f"{D}/decoupe_coffre_hc16.html", "w").write(page)
print('OK', len(page), 'octets', n_refs, 'repères', n_pcs, 'pièces', resume_pl)
