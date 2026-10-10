"""Navigateur sans tête pour les captures du book : three.js et polices servis en local, page en mode « rendu » (maquette plein cadre)."""
import asyncio, os
from playwright.async_api import async_playwright
THREE = '/tmp/claude-0/package/build/three.min.js'
FONTS = '/tmp/claude-0/-home-claude/443c7138-f497-5d10-bc14-ca79d36f67f9/scratchpad/fonts'
FACES = [('Barlow Semi Condensed', 'barlow-semi-condensed', (500, 600)), ('IBM Plex Sans', 'ibm-plex-sans', (400, 500, 600)), ('IBM Plex Mono', 'ibm-plex-mono', (400, 500))]
CSS = ''.join(f'@font-face{{font-family:"{fam}";font-style:normal;font-weight:{w};src:url(https://fonts.gstatic.com/local/{d}/{d}-latin-{w}-normal.woff2) format("woff2")}}\n'
              for fam, d, ws in FACES for w in ws)
RENDU = """
body.rendu{padding:0!important;overflow:hidden}
body.rendu #viewer{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;max-height:none!important;aspect-ratio:auto!important;z-index:9999;border:0!important;background:#F7F8F8!important}
body.rendu .lbl.cvl{font-size:17px!important;padding:6px 10px!important}
"""
async def route(r):
    u = r.request.url
    if 'three.min.js' in u:
        await r.fulfill(path=THREE, content_type='application/javascript')
    elif u.startswith('https://fonts.googleapis.com/'):
        await r.fulfill(body=CSS, content_type='text/css')
    elif u.startswith('https://fonts.gstatic.com/local/'):
        rel = u.split('/local/')[1]
        await r.fulfill(path=os.path.join(FONTS, rel.split('/')[0], 'files', rel.split('/')[1]), content_type='font/woff2')
    elif u.startswith('file:') and u.split('?')[0].endswith('.html'):      # (09/10) page locale servie en UTF-8 (sans <meta charset>, le navigateur la lisait en latin-1)
        await r.fulfill(path=u.split('?')[0][len('file://'):], content_type='text/html; charset=utf-8')
    elif u.startswith('file:') or u.startswith('data:'):
        await r.continue_()
    else:
        await r.fulfill(status=204, body='')

class Navig:
    def __init__(self, page_html, w=1600, h=900, dpr=2):
        self.page_html, self.w, self.h, self.dpr = page_html, w, h, dpr
    async def __aenter__(self):
        self.p = await async_playwright().start()
        self.b = await self.p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        self.ctx = await self.b.new_context(viewport={'width': self.w, 'height': self.h}, device_scale_factor=self.dpr, reduced_motion='reduce')
        self.pg = await self.ctx.new_page()
        self.msgs = []
        self.pg.on('console', lambda m: self.msgs.append(m.text))
        self.pg.on('pageerror', lambda e: self.msgs.append('ERR ' + str(e)))
        await self.pg.route('**/*', route)
        await self.pg.goto('file://' + self.page_html)
        await self.pg.wait_for_timeout(6000)
        await self.pg.add_style_tag(content=RENDU)
        return self
    async def __aexit__(self, *a):
        await self.b.close(); await self.p.stop()
    async def taille(self, w, h):
        await self.pg.set_viewport_size({'width': w, 'height': h}); await self.pg.wait_for_timeout(400)
    async def rendu(self, on=True):
        await self.pg.evaluate(f"document.body.classList.toggle('rendu', {str(on).lower()})"); await self.pg.wait_for_timeout(300)
    async def case(self, id_, on):
        await self.pg.evaluate(f"(() => {{ const c = document.getElementById('{id_}'); if (c.checked !== {str(on).lower()}) c.click(); }})()")
    async def curseur(self, id_, v):
        await self.pg.evaluate(f"(() => {{ const c = document.getElementById('{id_}'); c.value = {v}; c.dispatchEvent(new Event('input', {{bubbles: true}})); }})()")
    async def amures(self, s):
        await self.pg.evaluate(f"(() => {{ const r = document.querySelector('input[name=amures][value=\"{s}\"]'); r.checked = true; r.dispatchEvent(new Event('change', {{bubbles: true}})); }})()")
    async def cam(self, a, p):
        await self.pg.evaluate(f"window.__cam({list(a)}, {list(p)})")
    async def shot(self, path, sel='#viewer', t=900):
        await self.pg.wait_for_timeout(t)
        el = await self.pg.query_selector(sel)
        await el.screenshot(path=path, type='jpeg' if path.endswith('.jpg') else 'png', **({'quality': 90} if path.endswith('.jpg') else {}))
