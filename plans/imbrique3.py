"""Imbrication du plan de découpe (depuis plans/pieces.pkl écrit par decoupe3.py) -> DXF par plaque et par pièce, decoupe3.json.
Seul : python3 imbrique3.py [essais] [graines...] : réimbrique sans reconstruire le modèle, garde la meilleure graine par épaisseur."""
import sys, os, json, pickle, math
sys.path.insert(0, '/home/claude/cao/plans')
import ezdxf, imbrication as I
if 'parts' not in globals():                                   # lancé seul
    OUT = os.environ.get('DECOUPE_OUT', '/home/claude/cao/plans')
    _pk = pickle.load(open(f"{OUT}/pieces.pkl", 'rb'))
    parts, CONTROLE, SEUIL = _pk['parts'], _pk['controle'], _pk['seuil']
    NON_IMBRIQUE = ('TR', 'TG')
ESSAIS = int(sys.argv[1]) if len(sys.argv) > 1 and 'imbrique3' in sys.argv[0] else int(os.environ.get('DECOUPE_ESSAIS', 150))
GRAINES = [int(g) for g in sys.argv[2:]] if len(sys.argv) > 2 and 'imbrique3' in sys.argv[0] else [3]
RES = float(os.environ.get('DECOUPE_RES', 4.0))
# ---------------------------------------------------------------- imbrication par épaisseur
planches = []
for ep in sorted({p['ep'] for p in parts}):
    items = [(p['ref'], n + 1, p['poly']) for p in parts if p['ep'] == ep and not p['ref'].startswith(NON_IMBRIQUE) for n in range(p['qte'])]
    trop = [r for r, n, g in items if min(g.bounds[2], g.bounds[3]) > I.SH - 2 * I.MARGE or max(g.bounds[2], g.bounds[3]) > I.SW - 2 * I.MARGE]
    assert not trop, (ep, trop)
    I.SW = 2500
    meil = None
    for g_ in GRAINES:                                          # grille + FFT : règle bas-gauche, ESSAIS ordres par graine, contrôle exact après
        pls_, demi_ = I.imbriquer_grille_mieux(items, essais=ESSAIS, graine=g_, res=RES)
        sc_ = (len(pls_) - (0.5 if demi_ else 0), -max(p['taux'] for p in pls_))
        if meil is None or sc_ < meil[0]:
            meil = (sc_, pls_, demi_)
    pls, demi = meil[1], meil[2]
    if demi:
        demi[0]['sw'] = 1250; pls = pls[:-1] + demi
    for i, pl in enumerate(pls):
        pl['sw'] = pl.get('sw', 2500); pl['ep'] = ep; pl['id'] = f"{ep}-{'ABCDEFGH'[i]}"
        pl['taux'] = sum(g.area for _, _, g, _ in pl['placed']) / (pl['sw'] * I.SH)
        planches.append(pl)
for pl in planches:
    print(pl['id'], pl['sw'], f"{pl['taux'] * 100:.0f} %", [f"{r}.{n}" for r, n, *_ in pl['placed']])

# ---------------------------------------------------------------- DXF
os.makedirs(f"{OUT}/dxf3", exist_ok=True)
import shutil
shutil.rmtree(f"{OUT}/dxf3", ignore_errors=True); os.makedirs(f"{OUT}/dxf3", exist_ok=True)
def anneaux(g):
    return [list(g.exterior.coords)] + [list(r.coords) for r in g.interiors]
for pl in planches:
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM
    for lay, col in (("PANNEAU", 8), ("DECOUPE", 1), ("REPERES", 5)):
        doc.layers.add(lay, color=col)
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (pl['sw'], 0), (pl['sw'], I.SH), (0, I.SH)], close=True, dxfattribs={"layer": "PANNEAU"})
    for ref, n, g, rot in pl['placed']:
        for r in anneaux(g):
            msp.add_lwpolyline([(round(x, 2), round(y, 2)) for x, y in r[:-1]], close=True, dxfattribs={"layer": "DECOUPE"})
        c = g.representative_point()
        msp.add_text(ref, height=30, dxfattribs={"layer": "REPERES"}).set_placement((c.x, c.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(f"{OUT}/dxf3/planche_{pl['id']}.dxf")
# une pièce par DXF, à l'échelle 1, pour la découpe à la demande
os.makedirs(f"{OUT}/dxf3/pieces", exist_ok=True)
for p in parts:
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM; msp = doc.modelspace()
    for r in anneaux(p['poly']):
        msp.add_lwpolyline([(round(x, 2), round(y, 2)) for x, y in r[:-1]], close=True)
    doc.saveas(f"{OUT}/dxf3/pieces/{p['ref']}.dxf")

# ---------------------------------------------------------------- données pour la page
def chemin(g):
    out = []
    for p in getattr(g, 'geoms', [g]):
        for r in [p.exterior] + list(p.interiors):
            c = list(r.coords)[:-1]
            out.append('M' + ' '.join(f"{x:.1f},{-y:.1f}" for x, y in c) + 'Z')
    return ''.join(out)
data = dict(
    date='08/10/2026', seuil=SEUIL, panneau=[I.SW, I.SH],
    pieces=[dict(ref=p['ref'], nom=p['nom'], ep=p['ep'], qte=p['qte'], plis=p['plis'], note=p['note'],
                 dim=[round(p['poly'].bounds[2]), round(p['poly'].bounds[3])], aire=round(p['poly'].area / 1e6, 3),
                 d=chemin(p['poly'].simplify(0.3))) for p in parts],
    planches=[dict(id=pl['id'], ep=pl['ep'], sw=pl['sw'], taux=round(pl['taux'], 3),
                   pieces=[dict(ref=r, n=n, d=chemin(g.simplify(0.3)), c=[round(g.representative_point().x), round(g.representative_point().y)]) for r, n, g, rot in pl['placed']])
              for pl in planches],
    controle=CONTROLE)
json.dump(data, open(f"{OUT}/decoupe3.json", 'w'), ensure_ascii=False, separators=(',', ':'))
print('pièces', len(parts), 'planches', len(planches))
