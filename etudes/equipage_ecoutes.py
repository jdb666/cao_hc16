"""(JD 12/10) Équipage assis face à face et point d'écoute automatique, calculés par la page 3D elle-même (mêmes formules) :
- gardes des têtes sous les voiles et des bras au tube des colliers, selon la place sur les bancs, le choqué et les amures ;
- point d'écoute automatique de la voile sous le vent selon l'enroulement, pour plusieurs choqués.
python3 etudes/equipage_ecoutes.py  -> etudes/equipage_ecoutes.json (après plateforme/page.py)"""
import asyncio, sys, json
sys.path.insert(0, '/home/claude/cao/book')
from navig import Navig
OUT = '/home/claude/cao/etudes/equipage_ecoutes.json'
XS, CHOCS, ENR = (2300, 2350, 2400, 2450, 2500, 2600, 2700, 2780), (0, 15, 25, 35), (0, 10, 25, 40, 50, 55, 60, 65, 70, 75, 78, 80, 85, 90, 95)

async def main():
    async with Navig('/home/claude/cao/plateforme/plateforme_hc16.html', 1200, 800, 1) as n:
        await n.rendu()
        eq = await n.pg.evaluate("P3D.equipage")
        gardes = []
        for x in XS:                                  # H 1,80 m à bâbord, F 1,60 m à tribord (symétrique en changeant de bord et d'amures)
            await n.pg.evaluate(f"window.__equipage({x}, true)")
            for am in (1, -1):
                await n.amures(am)
                for choc in CHOCS:
                    await n.curseur('r-choc', choc)
                    g = await n.pg.evaluate("window.__gardesVal")
                    gardes.append(dict(x=x, amures=am, choc=choc, tetes=g['tetes'], bras=g['bras']))
        await n.amures(1)
        ecoutes = {}
        for choc in (0, 15, 25, 40):
            await n.curseur('r-choc', choc)
            ecoutes[choc] = await n.pg.evaluate(f"window.__ecoutes({list(ENR)})")
        json.dump(dict(equipage=eq, gardes=gardes, ecoutes=ecoutes,
                       note="gardes en mm (négatif : contact) ; H 1,80 m à bâbord, F 1,60 m à tribord ; amures 1 = tribord (voiles à bâbord) ; "
                            "écoutes : voile bâbord (sous le vent en tribord amures), enroulement en % de la surface, typ poutre (pos = y) ou flotteur (pos = x)"),
                  open(OUT, 'w'), ensure_ascii=False, indent=1)
        print('OK', OUT, len(gardes), 'cas ;', [m for m in n.msgs if 'rror' in m][:3])

asyncio.run(main())
