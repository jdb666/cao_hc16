"""Captures 3D du book depuis la page Plateforme HC16 (plateforme/plateforme_hc16.html).
python3 captures_3d.py [dpr] [filtre]  -> book/img/<nom>.jpg"""
import asyncio, sys, math, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from navig import Navig
PI = math.pi
DPR = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
FILTRE = sys.argv[2] if len(sys.argv) > 2 else ''
OUT = sys.argv[3] if len(sys.argv) > 3 else '/home/claude/cao/book/img/'
os.makedirs(OUT, exist_ok=True)
W16, SQ = (1600, 900), (1000, 1000)
BASE = dict(h16=False, cof=True, trp=False, rig=True, hau=True, tra=True, eau=True, cv=True, lbl=False, ten=False, enr_b=0, enr_t=0, choc=15, am=1, levee=0, tire=False, charge=0,
            equ=False, eqx=2450, hbab=True, auto=True)   # (JD 12/10) équipage assis (masqué par défaut), point d'écoute automatique
# vues d'ensemble : [th, ph, rayon], cible (x, y, z), champ (°)
AV, AR = ([2.35, 1.22, 27500], [2700, 0, 3800], 20), ([-0.75, 1.17, 27500], [2750, 0, 3800], 20)
PR, FA = ([PI / 2, PI / 2, 50500], [2650, 0, 4050], 12), ([PI, PI / 2, 50500], [2500, 0, 4050], 12)
DE = ([PI / 2, 0.02, 41000], [2650, 0, 500], 6)
VUES = lambda pre, **e: [
    (pre + '_av', W16, dict(e), AV), (pre + '_ar', W16, dict(e), AR),
    (pre + '_pr', SQ, dict(e, choc=0), PR), (pre + '_fa', SQ, dict(e), FA), (pre + '_de', W16, dict(e), DE)]
H16 = dict(h16=True)
SCENES = (VUES('s1_hc16', **H16) + VUES('s2_rando') + VUES('s3_transp', trp=True) + [
    # coffre transparent de près, sans gréement
    ('s3_coffre_av', W16, dict(trp=True, rig=False), ([2.45, 1.05, 9800], [1750, 0, 600], 24)),
    ('s3_coffre_ar', W16, dict(trp=True, rig=False), ([-0.9, 1.0, 9800], [1850, 0, 600], 24)),
    ('s3_coffre_de', W16, dict(trp=True, rig=False), ([PI / 2, 0.02, 14500], [1750, 0, 600], 12)),
    ('s3_coffre_pr', W16, dict(trp=True, rig=False), ([PI / 2, PI / 2, 17500], [2050, 0, 500], 12)),
] + [
    # une voile à 0, 50, 75 %, l'autre roulée
    (f's4_{e:02d}_{v}', taille, dict(enr_b=e, enr_t=100, choc=(0 if v == 'pr' else 15)), cam)
    for e in (0, 50, 75) for v, taille, cam in (('av', W16, AV), ('pr', SQ, PR), ('fa', SQ, FA), ('de', W16, DE))
] + [
    # moteur en marche / relevé
    (f's5_{n}_{v}', W16, dict(rig=False, trp=t, levee=l), cam)
    for n, l in (('bas', 0), ('haut', 'max'))
    for v, t, cam in (('ar', False, ([-0.62, 1.08, 6200], [1900, 0, 650], 24)),
                      ('ar_transp', True, ([-0.62, 1.08, 6200], [1900, 0, 650], 24)),
                      ('av_transp', True, ([2.5, 1.12, 6200], [1900, 0, 600], 24)),
                      ('pr_transp', True, ([PI / 2, PI / 2, 12500], [1900, 0, 550], 12)))
] + [
    # détails
    ('d_livarde', W16, dict(enr_b=100, enr_t=100, cv=False), ([2.75, 1.3, 2700], [1845, 1150, 1000], 30)),
    ('d_joue', W16, dict(rig=True, cv=False), ([PI / 2, PI / 2, 4200], [2300, 1120, 820], 30)),
    ('d_pied_mat', W16, dict(cv=False), ([2.15, 1.25, 2600], [1985, 1150, 520], 30)),
    ('d_collier', W16, dict(enr_b=100, enr_t=100, cv=False), ([0.62, 0.78, 1350], [2005, 1150, 1160], 30)),
    ('d_collier_av', W16, dict(enr_b=100, enr_t=100, cv=False), ([2.25, 1.02, 1500], [1990, 1150, 1150], 30)),
    ('d_emplanture', W16, dict(trp=True, cv=False), ([2.05, 1.18, 760], [1965, 1161, 400], 30)),
    ('d_brelage', W16, dict(tra=False, rig=False), ([-0.35, 1.95, 2300], [2040, 0, 480], 30)),
    ('d_accroches', W16, dict(tra=False, rig=False, trp=True), ([-0.1, 1.75, 2400], [2030, 560, 520], 30)),
    ('d_bancs', W16, dict(rig=False), ([-0.55, 0.92, 4600], [2650, 950, 560], 30)),
    ('d_haubans', W16, dict(rig=True, trp=True, cv=False), ([2.55, 1.18, 6000], [2000, 0, 900], 28)),
    ('d_assiette_0', W16, dict(rig=False, charge=0), ([PI / 2, 1.49, 17500], [2650, 0, 250], 12)),
    ('d_assiette_150', W16, dict(rig=False, charge=150), ([PI / 2, 1.49, 17500], [2650, 0, 250], 12)),
    ('d_ecoute', W16, dict(tire=True, choc=15, cv=False, enr_b=50, enr_t=80), ([-0.62, 1.12, 9000], [3700, 0, 1300], 30)),   # (JD 12/10) point d'écoute automatique : flotteur à 50 %, angle des poutres à 80 %
    # (JD 08/10) accoudoirs étanches sur l'arrière des bancs, batteries dedans ; la joue finit avec eux
    ('v_acc_ar', W16, dict(rig=False, cv=False), ([0.62, 1.12, 3600], [2900, 1000, 760], 30)),
    ('v_acc_transp', W16, dict(rig=False, trp=True, cv=False), ([0.62, 1.12, 3600], [2900, 1000, 760], 30)),
    ('v_acc_int', W16, dict(rig=False, cv=False), ([-0.55, 1.02, 4200], [2850, 900, 760], 30)),
    ('v_acc_pr', W16, dict(rig=False, cv=False), ([PI / 2, PI / 2, 11000], [2450, 0, 760], 24)),
    # (JD 08/10) caissons de rangement de chaque côté du moteur, trappes ; trappes C4 au-dessus des bancs ; glissière du collier ; banc renforcé
    ('v_rang_ar', W16, dict(rig=False, cv=False), ([-0.62, 1.0, 4300], [1900, 0, 700], 26)),
    ('v_rang_transp', W16, dict(rig=False, trp=True, cv=False), ([-0.62, 1.0, 4300], [1900, 0, 650], 26)),
    ('v_trappes_dessus', W16, dict(rig=False, cv=False, hau=False), ([PI / 2, 0.02, 5600], [1900, 0, 900], 26)),
    ('v_trappes_c4', W16, dict(rig=False, cv=False), ([-0.45, 1.35, 1900], [2022, 890, 805], 30)),
    ('v_glissiere', W16, dict(rig=True, hau=True, cv=False, enr_b=100, enr_t=100), ([-0.45, 1.2, 1150], [2085, 1080, 1060], 30)),
    ('v_glissiere_berceau', W16, dict(rig=True, hau=True, cv=False, enr_b=100, enr_t=100), ([-1.0, 1.05, 900], [2085, 1050, 1150], 30)),
    ('v_glissiere_transp', W16, dict(rig=True, trp=True, cv=False, enr_b=100, enr_t=100), ([-0.45, 1.25, 1700], [2085, 1080, 900], 30)),
    ('v_banc_dessous', W16, dict(rig=False, cv=False), ([-1.45, 1.38, 1700], [2450, 950, 610], 34)),
    ('v_banc_jambes', W16, dict(rig=False, cv=False), ([1.15, 1.42, 2300], [2560, 1140, 520], 30)),
    # (JD 07/10) batterie dans le caisson du banc bâbord, coffre à ancre devant le puits
    ('d_caisson', W16, dict(rig=False, trp=True), ([-0.3, 1.02, 2100], [2165, 1010, 820], 30)),
    ('d_ancre', W16, dict(rig=False, trp=True), ([2.6, 0.95, 2300], [1650, 0, 520], 30)),
    # (JD 06/10 soir) sans coffre ni trampoline : haubans des pieds de mât, voiles roulées
    ('h_pieds_av', W16, dict(cof=False, tra=False, enr_b=100, enr_t=100, cv=False), ([2.55, 1.0, 6400], [1600, 0, 450], 32)),
    ('h_pieds_ar', W16, dict(cof=False, tra=False, enr_b=100, enr_t=100, cv=False), ([-0.8, 1.0, 7800], [2000, 0, 520], 32)),
    ('h_pieds_de', W16, dict(cof=False, tra=False, enr_b=100, enr_t=100, cv=False), ([PI / 2, 0.02, 41000], [2600, 0, 450], 6.2)),
    ('h_pied_detail', W16, dict(cof=False, tra=False, enr_b=100, enr_t=100, cv=False), ([2.0, 1.02, 1700], [1990, 1150, 430], 32)),
    # (JD 09/10) moustache à 10°, hiloire, poteau de glissière dans le coffre, trampoline étanche, fermeture sous les bancs
    ('m_coffre_av', W16, dict(enr_b=100, enr_t=100, cv=False), ([2.45, 1.08, 9800], [1800, 0, 700], 24)),
    ('m_coffre_fa', W16, dict(enr_b=100, enr_t=100, cv=False, eau=False), ([PI, PI / 2, 9800], [1800, 0, 650], 20)),
    ('m_coffre_ar', W16, dict(enr_b=100, enr_t=100, cv=False), ([-0.75, 1.05, 9800], [2200, 0, 700], 24)),
    ('m_hiloire', W16, dict(enr_b=100, enr_t=100, cv=False, hau=False), ([2.25, 0.82, 3600], [1860, 0, 860], 30)),
    ('m_glissiere', W16, dict(enr_b=100, enr_t=100, cv=False), ([-0.5, 1.2, 1500], [2040, 1045, 1000], 30)),
    ('m_glissiere_transp', W16, dict(enr_b=100, enr_t=100, cv=False, trp=True), ([2.35, 1.2, 2100], [2000, 1045, 850], 30)),
    ('m_banc_tape', W16, dict(rig=False, cv=False), ([-1.35, 1.4, 1500], [2080, 1010, 610], 34)),
    ('m_banc_joint', W16, dict(rig=False, cv=False), ([1.2, 1.45, 1900], [2250, 1120, 560], 30)),
    # (JD 09/10 après-midi) le coffre par en dessous ; tente igloo sur deux arceaux ; coffre à ancre ouvert ; appui du tube sans glissière
    ('s3_dessous_av', W16, dict(rig=False, eau=False, cv=False), ([2.6, 2.05, 4200], [1800, 0, 450], 30)),
    ('s3_dessous_ar', W16, dict(rig=False, eau=False, cv=False, tra=False), ([-0.5, 2.3, 4200], [1900, 0, 450], 30)),   # trampoline ôté
    ('s3_dessous_fa', W16, dict(rig=False, eau=False, cv=False), ([PI, 1.85, 6000], [1750, 0, 500], 24)),
    ('t_tente_av', W16, dict(ten=True, enr_b=100, enr_t=100, cv=False), ([2.35, 1.22, 9800], [2900, 0, 1100], 26)),
    ('t_tente_ar', W16, dict(ten=True, enr_b=100, enr_t=100, cv=False), ([-0.75, 1.17, 9800], [3000, 0, 1100], 26)),
    ('t_tente_pr', W16, dict(ten=True, enr_b=100, enr_t=100, cv=False), ([PI / 2, PI / 2, 14000], [2900, 0, 1100], 14)),
    ('m_ancre_poche', W16, dict(rig=False, cv=False), ([2.7, 0.85, 2600], [1660, 0, 600], 30)),
    # (JD 09/10 17 h) puits du moteur sans face arrière : C4 ouverte sur la largeur du puits
    ('m_puits_ar', W16, dict(rig=False, cv=False, eau=False, tra=False), ([0.25, 1.6, 1900], [2010, 0, 480], 32)),   # sans le trampoline, de derrière, sous la poutre AR
    # (JD 12/10) deux personnes assises face à face, H 1,80 m à bâbord, F 1,60 m à tribord
    ('e_equ_ar', W16, dict(equ=True, cv=False, choc=15, am=-1), ([0.0, 1.16, 4600], [2450, 0, 1250], 30)),      # de l'arrière, dans l'axe    # bâbord amures : H au vent, la bordure de la voile bâbord sur la tête
    ('e_equ_fa', W16, dict(equ=True, cv=False, choc=15, am=1, eau=False), ([PI, 1.5, 9000], [2450, 0, 1300], 14)),    # tribord amures : F au vent, sous la bordure de la voile tribord
])

async def etat(n, s):
    for k, id_ in (('h16', 'c-h16'), ('cof', 'c-cof'), ('trp', 'c-trp'), ('rig', 'c-rig'), ('hau', 'c-hau'), ('tra', 'c-tra'), ('eau', 'c-eau'), ('cv', 'c-cv'), ('lbl', 'c-lbl'), ('ten', 'c-ten'),
                   ('equ', 'c-equ'), ('auto', 'c-auto')):
        await n.case(id_, s[k])
    await n.pg.evaluate(f"window.__equipage && window.__equipage({s['eqx']}, {str(s['hbab']).lower()})")
    await n.pg.evaluate(f"window.__book = {{sansTire: {str(not s['tire']).lower()}}}")
    await n.curseur('r-enr-b', s['enr_b']); await n.curseur('r-enr-t', s['enr_t']); await n.curseur('r-choc', s['choc'])
    await n.amures(s['am'])
    await n.pg.evaluate(f"document.getElementById('s-charge').value = '{s['charge']}'")
    lv = s['levee']
    if lv == 'max':
        lv = await n.pg.evaluate("+document.getElementById('c-bascule').max")
    await n.curseur('c-bascule', lv)

async def main():
    sc = [x for x in SCENES if (x[0] in FILTRE.split(',') if ',' in FILTRE else FILTRE in x[0])]
    async with Navig('/home/claude/cao/plateforme/plateforme_hc16.html', *W16, DPR) as n:
        await n.rendu()
        info = {}
        for nom, taille, e, (a, p, fov) in sc:
            s = dict(BASE, **e)
            await n.taille(*taille)
            await etat(n, s)
            await n.cam(a, p) if fov is None else await n.pg.evaluate(f"window.__cam({list(a)}, {list(p)}, {fov})")
            await n.shot(OUT + nom + '.jpg', t=1100)
            info[nom] = await n.pg.evaluate("({cv: document.getElementById('v-cv').innerText, chav: document.getElementById('v-chav').innerText, surf: document.getElementById('v-surf').innerText, gardes: window.__gardesVal || null})")
            print(nom, info[nom]['cv'].replace('\n', ' | '), '|', info[nom]['chav'].split('\n')[0], flush=True)
        old = json.load(open(OUT + 'info.json')) if os.path.exists(OUT + 'info.json') else {}
        old.update(info); json.dump(old, open(OUT + 'info.json', 'w'), ensure_ascii=False, indent=1)
        if any('ERR' in m for m in n.msgs):
            print('\n'.join(m for m in n.msgs if 'ERR' in m))

asyncio.run(main())
