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
s = s.replace("/*P3D*/null", json.dumps(P3D, separators=(',', ':')))
open(f"{d}/plateforme_hc16.html", "w").write(s)
print("OK plateforme_hc16.html", len(s))
