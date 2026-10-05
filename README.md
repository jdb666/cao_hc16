# HC16 « Nacra 5.80 Rando »

Conversion d'un Hobie Cat 16 :
- gréement Nacra 5.80 Rando dessiné par JD (deux mâts carbone de 7,30 m posés sur le pont des coques, voiles sur enrouleur, livardes) ;
- coffre en CP cousu-collé avec joues, bancs, accroches de poutre intégrées aux couples ;
- moteur Haswing Protruar relevable à la verticale dans un puits central, batterie 24 V.

Repère : origine à l'étrave, à la flottaison, dans l'axe du bateau. X vers l'arrière, Y vers bâbord, Z vers le haut. Unités : mm.

## Contenu

| Chemin | Rôle |
|---|---|
| `cotes.yaml` | Toutes les cotes. C'est la seule source : tout le reste en est tiré. |
| `hc16_rando.py` | Modèle CadQuery paramétrique : `build(cfg)` → assemblage nommé (coques, plateforme, coffre, mâts, voiles, moteur…). |
| `export_step.py` | Export STEP de l'assemblage complet. |
| `SYNTHESE_coffre_hc16.md` | Synthèse des choix, cotes et vérifications (tenue à jour à chaque modification). |
| `plateforme/` | Page 3D interactive : `export3d.py` → `p3d.json`, `page.py` + `gabarit.html` → `plateforme_hc16.html`. Vues cotées (`dessins.py`), attaches (`attaches.py`). |
| `plans/` | Plan de découpe : `decoupe3.py` (dépliage du bordé, contours des pièces planes), `imbrique3.py` + `imbrication.py` (imbrication, DXF), `page_decoupe.py` (page). DXF par planche dans `plans/dxf3/`. Patron de la tente dans `plans/dxf_tente/`. |
| `etudes/` | Balayage du relevage moteur, pose du coffre, recouvrements, hydrostatique et assiette. |
| `releves/` | Photos annotées et formulaire des relevés sur le bateau. |
| `*.step` | Exports STEP (le complet : `hc16_rando_complet.step`). |
| `cotes_avant_*.yaml`, `hc16_rando_avant_*.py` | États successifs : sauvegarde avant chaque modification, le suffixe dit laquelle. |
| `bundle/`, `projet_hc16_coffre.zip` | Dossier du 26/09 (première version). |
| `dessins/` | Dessins du gréement Rando. |

## Regénérer

```sh
pip install -r requirements.txt
python3 hc16_rando.py                 # contrôle du modèle
python3 export_step.py                # STEP complet
python3 plateforme/export3d.py && python3 plateforme/page.py   # page 3D
python3 plans/decoupe3.py             # plan de découpe + DXF
```

Les scripts lisent et écrivent sous `/home/claude/cao/` (chemins absolus) : cloner le dépôt à cet endroit, ou remplacer ce préfixe.
