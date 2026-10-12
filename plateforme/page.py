"""Assemble la page Plateforme HC16 : gabarit.html + p3d.json + profil/dessus/face.svg -> plateforme_hc16.html"""
import os, re
d = os.path.dirname(os.path.abspath(__file__))
s = open(f"{d}/gabarit.html").read()
ARIA = {'profil': "Profil coté de la plateforme HC16, modèle recalé et modèle précédent",
        'dessus': "Vue de dessus cotée de la plateforme HC16",
        'face': "Vue de face cotée au droit de la poutre avant",
        'semelle': "Coupes de la semelle de pied de mât et de son bourrage époxy",
        'attache_poutre': "Coupe de l'accroche du coffre posée sur la poutre avant, avec l'œil dans C4 et le brêlage en diagonale vers le pied du pilier de martingale",
        'attache_longeron': "Coupe d'un couple de banc posé sur le longeron, tenu par le laçage sous la toile"}
for k, lab in ARIA.items():
    v = open(f"{d}/{k}.svg").read()
    v = re.sub(r'<metadata>.*?</metadata>\s*', '', v, flags=re.S)
    v = re.sub(r'<svg([^>]*?) width="[^"]*" height="[^"]*"', r'<svg\1', v, count=1)
    v = v.replace('<svg ', f'<svg role="img" aria-label="{lab}" ', 1)
    tag = f"<!--SVG:{k}-->"; assert tag in s, tag
    s = s.replace(tag, v)
assert "/*P3D*/null" in s
import json, sys, yaml
sys.path.insert(0, '/home/claude/cao/etudes')
from greement_hc16 import greement
P3D = json.load(open(f"{d}/p3d.json"))
P3D['rig']['hc16'] = greement(yaml.safe_load(open('/home/claude/cao/cotes.yaml'))['hc16_origine'])   # gréement HC16 d'origine (book, CV de comparaison)
import os
_TJ = os.environ.get('TENTE_JSON', '/home/claude/cao/plans/tente_3d.json')   # (12/10) TENTE_JSON, PAGE_OUT : variantes de tente sans toucher à la page publiée
if os.path.exists(_TJ):                                              # (JD 09/10) tente igloo : python3 plans/tente.py (après export3d.py)
    P3D['tente'] = json.load(open(_TJ))
def _bb(n):                                                          # boîte englobante d'une pièce du modèle exporté
    o = next((o for g in ('full', 'new') for o in P3D.get(g, []) if o['n'] == n and o['v']), None)
    if o is None: return None
    v = o['v']; return [min(v[0::3]), max(v[0::3]), min(v[1::3]), max(v[1::3]), min(v[2::3]), max(v[2::3])]
# (JD 12/10) équipage assis face à face sur les bancs : assise, dossier (joue), accoudoir, dessus du trampoline, tube des colliers
_as, _ac, _tu, _jo = _bb('banc_babord_assise'), _bb('accoudoir_babord_avant'), _bb('tube_colliers'), _bb('joue_babord')
_tr = next((o for o in P3D['new'] if o['n'] == 'trampoline'), None)
if _as and _tr:
    v = _tr['v']; pts = list(zip(v[0::3], v[1::3], v[2::3])); x0_ = min(p[0] for p in pts)
    prof = {}
    for x, y, z in pts:                                              # dessus du trampoline en travers (bombé au laçage, plus bas vers les longerons)
        if abs(x - x0_) < 1: prof[round(abs(y))] = max(prof.get(round(abs(y)), -1e9), z)
    P3D['equipage'] = dict(
        z_assise=round(_as[5], 1), y_dos=round(_as[3], 1), y_bord=round(_as[2], 1), x_assise=[round(_as[0], 1), round(_as[1], 1)],
        x_accoudoir=round(_ac[0], 1) if _ac else round(_as[1], 1), z_dossier=round(_jo[5], 1) if _jo else None,
        tramp=[[y, round(z, 1)] for y, z in sorted(prof.items())],
        tube=dict(x=round((_tu[0] + _tu[1]) / 2, 1), z=round((_tu[4] + _tu[5]) / 2, 1), r=round((_tu[1] - _tu[0]) / 2, 1), y=round(_tu[3], 1)) if _tu else None,
        x_def=2450)
s = s.replace("/*P3D*/null", json.dumps(P3D, separators=(',', ':')))
open(os.environ.get("PAGE_OUT", f"{d}/plateforme_hc16.html"), "w").write(s)
print("OK plateforme_hc16.html", len(s))
