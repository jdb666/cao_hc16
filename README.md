# HC16 Rando

Conversion d'un Hobie Cat 16 :
- gréement Rando dessiné par JD (deux mâts carbone de 7,30 m posés sur le pont des coques, voiles sur enrouleur, livardes) ; collier, haubans, tube et mâts forment un ensemble indépendant du coffre ; collier et emplanture en CP collé stratifié, quête réglée au trou ;
- coffre en CP cousu-collé avec joues, bancs, accroches de poutre intégrées aux couples ;
- moteur Haswing Protruar relevable à la verticale dans un puits central, deux batteries 24 V dans les accoudoirs des bancs.

Repère : origine à l'étrave, à la flottaison, dans l'axe du bateau. X vers l'arrière, Y vers bâbord, Z vers le haut. Unités : mm.

## Contenu

| Chemin | Rôle |
|---|---|
| `cotes.yaml` | Toutes les cotes. C'est la seule source : tout le reste en est tiré. `regen_v.py` en tire `v_pleine_0.yaml` (moteur en marche) et `v_releve.yaml` (relevé). |
| `hc16_rando.py` | Modèle CadQuery paramétrique : `build(cfg)` → assemblage nommé (coques, plateforme, coffre, mâts, voiles, moteur…). |
| `export_step.py` | Export STEP de l'assemblage complet. |
| `SYNTHESE_coffre_hc16.md` | Synthèse des choix, cotes et vérifications (tenue à jour à chaque modification). |
| `plateforme/` | Page 3D interactive : `export3d.py` → `p3d.json`, `page.py` + `gabarit.html` → `plateforme_hc16.html`. Vues cotées (`dessins.py`), attaches (`attaches.py`). |
| `plans/` | Plan de découpe : `decoupe3.py` (dépliage du bordé, contours des pièces planes), `imbrique3.py` + `imbrication.py` (imbrication, DXF), `page_decoupe.py` → `decoupe_coffre_hc16.html`. DXF par planche et par pièce dans `plans/dxf3/`. Patron de la tente dans `plans/dxf_tente/`. |
| `etudes/` | Balayage du relevage moteur, pose du coffre, recouvrements, jeux du collier et du tube (`collier_tube.py`), volumes du coffre par zones (`vol_zones.py`), gréement HC16 d'origine, hydrostatique et assiette, fiche technique : poids, charge utile, assiette, comparaison avec le HC16 (`fiche_technique.py`). |
| `book/` | Captures du book (`captures_3d.py`, `captures_page.py` → `book/img/`), sources du deck Slides (`book/deck/`), pages de la fiche technique (`fiche_slides.py`), numéros, sommaire, nomenclature et images (`maj_book.py`). |
| `releves/` | Photos annotées et formulaire des relevés du 28/09 ; formulaire des cotes manquantes (`page_cotes.py` → `cotes_manquantes_hc16.html`). |
| `*.step` | Exports STEP (le complet : `hc16_rando_complet.step`). |
| `cotes_avant_*.yaml`, `hc16_rando_avant_*.py` | États successifs : sauvegarde avant chaque modification, le suffixe dit laquelle. |
| `bundle/`, `projet_hc16_coffre.zip` | Dossier du 26/09 (première version). |
| `dessins/` | Dessins du gréement Rando. |

Les pages HTML (`plateforme/plateforme_hc16.html`, `plans/decoupe_coffre_hc16.html`, `releves/cotes_manquantes_hc16.html`) s'ouvrent directement dans un navigateur ; hors de claude.ai, le formulaire garde les saisies dans le navigateur et « Copier le texte » les exporte.

## Regénérer

```sh
pip install -r requirements.txt
python3 regen_v.py                    # v_pleine_0.yaml, v_releve.yaml
python3 hc16_rando.py                 # contrôle du modèle
python3 export_step.py                # STEP complet
python3 plateforme/export3d.py && python3 plateforme/page.py   # page 3D (≈ 6 min)
python3 plans/decoupe3.py && python3 plans/page_decoupe.py     # plan de découpe + DXF
```

Les scripts lisent et écrivent sous `/home/claude/cao/` (chemins absolus) : cloner le dépôt à cet endroit, ou remplacer ce préfixe.

## Mises à jour

Chaque série de modifications arrive en `hc16_rando_N.bundle` (un commit, à appliquer dans l'ordre). Dans ce dossier :

```sh
git pull /chemin/vers/hc16_rando_N.bundle main
```
