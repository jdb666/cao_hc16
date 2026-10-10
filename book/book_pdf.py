"""Book en PDF (10/10) : les diapos de book/deck/ (ordre de deck.json), images locales (book/img, book/img/blobs),
polices de book/vendor ; une page 1920 × 1080 par diapo.
python3 book/book_pdf.py [sortie.pdf]           -> book/HC16_Rando_book.pdf (images d'origine, ≈ 17 Mo)
python3 book/book_pdf.py --leger [sortie.pdf]   -> book/HC16_Rando_book_leger.pdf : JPEG ramenés à leur taille
                                                   d'affichage sur la page, qualité 72 (envoi par courriel)"""
import asyncio, json, os, re, shutil, sys, tempfile
from playwright.async_api import async_playwright
from PIL import Image
B = os.path.dirname(os.path.abspath(__file__))
LEGER = '--leger' in sys.argv
ARGS = [a for a in sys.argv[1:] if a != '--leger']
SORTIE = os.path.abspath(ARGS[0]) if ARGS else os.path.join(B, 'HC16_Rando_book_leger.pdf' if LEGER else 'HC16_Rando_book.pdf')
QUALITE = 72
d = json.load(open(os.path.join(B, 'deck', 'deck.json'), encoding='utf-8'))
carte = json.load(open(os.path.join(B, 'carte_images.json'), encoding='utf-8'))
inv = {v: k for k, v in carte.items()}

def local(src):                                   # /_blob/<id> -> fichier du dépôt
    if src in inv:
        for ext in ('.jpg', '.png'):
            if os.path.exists(os.path.join(B, 'img', inv[src] + ext)):
                return 'img/' + inv[src] + ext
    i = src.rsplit('/', 1)[-1]
    for ext in ('.jpg', '.png'):
        if os.path.exists(os.path.join(B, 'img', 'blobs', i + ext)):
            return 'img/blobs/' + i + ext
    raise SystemExit(f'image introuvable : {src}')

TMPD = tempfile.mkdtemp(prefix='_leger_', dir=B) if LEGER else None
deja = {}

def allege(rel, style):
    """JPEG réduit à sa taille d'affichage (object-fit cover : le plus grand des deux rapports), qualité QUALITE ;
    les PNG (plans, schémas) restent tels quels."""
    if not rel.endswith('.jpg'):
        return rel
    im = Image.open(os.path.join(B, rel))
    bw = re.search(r'(?<![-\w])width:\s*([\d.]+)px', style)
    bh = re.search(r'(?<![-\w])height:\s*([\d.]+)px', style)
    ks = ([float(bw.group(1)) / im.width] if bw else []) + ([float(bh.group(1)) / im.height] if bh else [])
    k = min(1.0, max(ks)) if ks else 1.0
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    if (rel, w) not in deja:
        out = os.path.join(TMPD, f'{len(deja)}.jpg')
        im = im.convert('RGB')
        if w < im.width:
            im = im.resize((w, h), Image.LANCZOS)
        im.save(out, quality=QUALITE, optimize=True)
        deja[(rel, w)] = os.path.relpath(out, B)
    return deja[(rel, w)]

def img(m):
    tag = m.group(0)
    s = re.search(r'src="(/_blob/[0-9a-f]+)"', tag)
    if not s:
        return tag
    rel = local(s.group(1))
    if LEGER:
        st = re.search(r'style="([^"]*)"', tag)
        rel = allege(rel, st.group(1) if st else '')
    return tag.replace(s.group(1), rel)

FACES = [('Barlow Semi Condensed', 'barlow-semi-condensed', (500, 600)), ('IBM Plex Sans', 'ibm-plex-sans', (400, 500, 600)), ('IBM Plex Mono', 'ibm-plex-mono', (400, 500))]
css = ''.join(f'@font-face{{font-family:"{fam}";font-weight:{w};src:url(vendor/fonts/{dd}/files/{dd}-latin-{w}-normal.woff2) format("woff2")}}\n'
              for fam, dd, ws in FACES for w in ws)
css += """
@page{size:1920px 1080px;margin:0}
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff}
body{font-family:'IBM Plex Sans',Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}
section{position:relative;width:1920px;height:1080px;overflow:hidden;break-after:page;page-break-after:always}
p,h1,h2,h3,ul,ol{margin:0}
ul{padding-left:1.1em}
table{border-collapse:collapse}
th{text-align:left;font-family:'IBM Plex Mono','Courier New',monospace;font-size:20px;font-weight:500;color:#4A5A63;border-bottom:2px solid #18262E;padding:4px 10px}
td{border-bottom:1px solid #D5DCDF;padding:3px 10px;vertical-align:top}
"""
TMP = os.path.join(B, '_book_pdf.html')
try:
    parts = []
    for sid in d['order']:
        t = open(os.path.join(B, 'deck', 'slides', sid + '.html'), encoding='utf-8').read()
        parts.append(re.sub(r'<img\b(?:[^>"]|"[^"]*")*>', img, t))
    html = f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{d.get("title", "Book")}</title><style>{css}</style></head><body>\n' + '\n'.join(parts) + '\n</body></html>'
    open(TMP, 'w', encoding='utf-8').write(html)

    async def main():
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
            await pg.goto('file://' + TMP, wait_until='load')
            await pg.evaluate('document.fonts.ready')
            await pg.wait_for_timeout(500)
            await pg.pdf(path=SORTIE, width='1920px', height='1080px', print_background=True, margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
            await b.close()
    asyncio.run(main())
finally:
    if os.path.exists(TMP):
        os.remove(TMP)
    if TMPD:
        shutil.rmtree(TMPD, ignore_errors=True)
print('PDF', SORTIE, len(d['order']), 'pages', round(os.path.getsize(SORTIE) / 1e6, 1), 'Mo',
      f'({len(deja)} JPEG réduits, qualité {QUALITE})' if LEGER else '')
