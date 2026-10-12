"""(12/10) Vues de la tente sur la maquette (case « Tente », voiles roulées, sans équipage) : av, pr, fa, avp, ar.
python3 etudes/tente_vues.py page.html prefixe dossier  -> dossier/prefixe_<vue>.jpg"""
import asyncio, sys, math
sys.path.insert(0, '/home/claude/cao/book')
from navig import Navig
PI = math.pi
VUES = {'av': ([2.35, 1.12, 9000], [2700, 0, 1100], 28), 'pr': ([PI / 2, PI / 2, 14000], [2900, 0, 1100], 14),
        'fa': ([PI, 1.42, 9000], [2500, 0, 1150], 20), 'avp': ([2.6, 1.2, 4600], [1980, 0, 1000], 30), 'ar': ([-0.75, 1.17, 9800], [3000, 0, 1100], 26)}
async def main(page, pre, out):
    async with Navig(page, 1600, 900, 1) as n:
        await n.rendu()
        for c, v in (('c-ten', True), ('c-equ', False), ('c-cv', False)): await n.case(c, v)
        await n.curseur('r-enr-b', 100); await n.curseur('r-enr-t', 100)
        for nom, (a, p, fov) in VUES.items():
            await n.pg.evaluate(f"window.__cam({a}, {p}, {fov})")
            await n.shot(f'{out}/{pre}_{nom}.jpg', t=900)
        print([m for m in n.msgs if 'rror' in m][:3])
asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
