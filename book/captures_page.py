"""Figures 2D du book : vues cotées, semelle, attaches et coupe du relevage (page Plateforme HC16), planches de découpe (page Découpe coffre).
python3 captures_page.py -> book/img/*.png"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from navig import Navig
OUT = '/home/claude/cao/book/img/'
FIG = "figure{background:#F7F8F8!important}"

async def plateforme():
    async with Navig('/home/claude/cao/plateforme/plateforme_hc16.html', 1240, 900, 2) as n:
        await n.pg.add_style_tag(content=FIG)
        figs = await n.pg.query_selector_all('.planches figure')
        for el, nom in zip(figs, ('vue_profil', 'vue_dessus', 'vue_face')):
            await el.scroll_into_view_if_needed(); await el.screenshot(path=OUT + nom + '.png')
        el = await n.pg.query_selector('section[aria-labelledby=tsem] figure'); await el.screenshot(path=OUT + 'semelle.png')
        el = await n.pg.query_selector('.attaches'); await el.screenshot(path=OUT + 'attaches.png')
        mx = await n.pg.evaluate("+document.getElementById('c-bascule').max")
        for nom, l in (('coupe_bas', 0), ('coupe_haut', mx)):
            await n.curseur('c-bascule', l); await n.pg.wait_for_timeout(400)
            el = await n.pg.query_selector('figure.coupe'); await el.screenshot(path=OUT + nom + '.png')
            vals = await n.pg.evaluate("[...document.querySelectorAll('.relev:not(.voiles) dl div')].map(d => d.innerText.replace(/\\n/g, ' : '))")
            print(nom, l, vals)

async def decoupe():
    async with Navig('/home/claude/cao/plans/decoupe_coffre_hc16.html', 1240, 900, 2) as n:
        await n.pg.add_style_tag(content=FIG)
        for el in await n.pg.query_selector_all('figure.pl'):
            t = await el.eval_on_selector('figcaption .t', 'e => e.textContent')
            await el.scroll_into_view_if_needed(); await el.screenshot(path=OUT + 'planche_' + t.split()[-1] + '.png')
            print(t, await el.eval_on_selector('figcaption .m', 'e => e.textContent'))

async def main():
    await plateforme()
    await decoupe()
asyncio.run(main())
