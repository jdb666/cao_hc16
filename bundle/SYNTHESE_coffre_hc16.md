# HC16 « Nacra 5.80 Rando » — coffre porte-mâts et bancs : état du projet (24/09/2026)

## Repère et sources
- Origine : étrave à la flottaison, dans l'axe. X vers l'arrière, Y vers bâbord, Z vers le haut. Unités : mm.
- Coques : profil et plan F. Chevalier recalés (±30 mm), sections simplifiées. Plan de voilure : plan Rando de JD (1/25).
- Modèle paramétrique : `hc16_rando.py` lit `cotes.yaml` et régénère le STEP (`python hc16_rando.py cotes.yaml sortie.step`).

## Contraintes figées (décisions JD)
- Voile d'origine et hauteur de bordure inchangées ; mâts posés sur le pont des coques (pas emplantés au fond).
- Quête 3° ; pied de mât placé pour que le CV voiles pleines = CV HC16 d'origine.
- Collier de mât à 70–80 cm du pied, porté par la joue.
- Joues ellipsoïdales : deux quarts d'ellipse tangents au collier ; extrémités = pointe avant du coffre, collier, bout arrière du banc.
- Coffre cousu-collé à fond en V transversal parallèle aux câbles de martingale (0,455 au milieu → 0,545 aux joues), dessus 0,90 ; les colliers de mât sont repris par des pattes verticales ; seul le carter moteur descend plus bas ; pylônes au bout.
- Moteur : chaise sous le coffre, décalée ; bascule vers l'arrière sous la martingale, bien au-dessus de l'eau. Variantes « avant » et « vertical » conservées dans le script.
- Joues coffre + dossier d'une pièce, jamais plus hautes que le collier ; le dossier ne couvre que la moitié avant du banc.
- Un banc par bord sur les longerons, longueur 1,20 m (validée), dossier = joue.
- Voile réduite : ni livarde ni bôme, lattes diagonales ; écoute sur la poutre arrière.

## Poutre avant et martingale (relevées sur photos, 25/09/2026)
- Échelle : entraxe des pylônes 2 100, recoupée avec une règle 200 × 100 posée devant ; incertitude ≈ ±20 mm.
- Poutre avant cintrée vers le haut : flèche ≈ +100 au milieu (profil parabolique entre les pièces d'angle) ; diamètre ≈ 65 (à confirmer au pied à coulisse).
- Martingale : pilier sous le milieu de la poutre, pied 144 sous l'axe de poutre aux extrémités (≈ 210 sous le dessous de poutre au milieu), soit z ≈ 446 ; câbles vers les pylônes, fixés ≈ 50 sous l'axe de poutre.
- Hauteurs absolues calées sur l'axe de poutre aux extrémités z 590 (profil Chevalier, à mesurer).

## Géométrie du modèle actuel (valeurs par défaut de cotes.yaml)
| Élément | Valeur |
|---|---|
| Pied de mât | x 1 766, y ±1 151 (contre la joue), z 325 ; mât 7 300 × Ø60 |
| Collier | 750 mm du pied (z ≈ 1 074) |
| CV voiles pleines | x 3 010 (= HC16), z ≈ 3 930 ; enroulé 50 % : x ≈ 2 600 |
| Coffre | largeur 2 240, face AR x 1 972 ; fond en V : z 455 au milieu, 545 au droit des joues ; dessus z 900 ; pointe avant x 1 400 ; ≈ 430 L |
| Joues | quart d'ellipse avant + quart d'ellipse arrière jusqu'au bout des bancs (x 3 172), base z 545 (niveau des câbles), sommet z 900 ; 9 mm ; dossier 180 au-dessus de l'assise à x 2 500, 120 à 2 800 |
| Pattes de collier | 2 par mât, alu 60 × 10, sur la face extérieure des joues devant et derrière le mât, de z 780 à 1 114 ; le demi-collier s'y boulonne |
| Pylônes | sous chaque joue, au droit du mât, 120 × 90, CP 9 mm (ou tube alu), du pont à z 500 |
| Bancs | 1 200 × 310 (y 800 → 1 111), assise +100 au-dessus du trampoline, ≈ 40 L dessous, entaillés sur poutre AV et longeron |
| Bois | ≈ 28 kg |

## Moteur (Haswing Protruar 2.0 24 V) — version transversale (26/09/2026)
| Élément | Valeur |
|---|---|
| Position | centré (y 0), arbre à x 1 775 |
| Chaise pivotante | entièrement dans le coffre : charnière longitudinale (axe x) à z 500, décalée de 80 côté tribord ; paliers inox à x 1 510 et 1 625 ; planche de serrage 40 × 200 × 70, flasque 20 mm, bras massif |
| En marche | axe d'hélice −330, haut des pales −212 ; tête jusqu'à +880 |
| Relevage | ouvrir le volet de fond, basculer vers bâbord de 90°, goupiller, refermer le volet |
| Relevé | moteur couché en travers dans le coffre : axe de l'arbre +580, bas de l'hélice +462 ; seule la fente de l'arbre (70 × 350) reste ouverte |
| Fente de fond | x 1 610–1 966, y −40 à +905 ; volet en deux parties (plat + pan) collées à l'angle du fond |
| Contrôle | aucun contact de 0 à 90° (jeu mini 3 mm entre flasque et fond vers 10°) |

## Coffre (version transversale)
- Fond polygonal à 3 segments : plat z 378 sur ±200, pans jusqu'à z 465 au droit des joues ; dessus z 960 (passage de la tête pendant la bascule).
- Cloisons à y −500 (soute moteur / caisse) et +920 (fin de soute) ; compartiment tribord de 608 mm pour la caisse 590 × 260 × 330 ; capot sur toute la largeur de ce compartiment.
- Bordé en 3 panneaux : central 400 × 948 (cylindrique), deux latéraux légèrement vrillés ; ≈ 590 L.
- Joues : base z 465, sommet z 960.
- Plans : 2 panneaux + 1 demi-panneau CP 6 mm, 1 panneau CP 9 mm ; DXF dans plans/dxf2.

## Contrôles
- Garde bordure / haut de joue : ≥ 190 mm sur tout le débattement.
- Garde tête / bordure (assise +100, tête à 0,98 m de l'axe) : −40 mm à x 2 450, 0 à 2 800, +16 à 2 950, +33 à 3 100, +68 à 3 400. Avec des bancs de 1,20 m, une seule place par bord, au bout.
- Dossier au-dessus de l'assise : 416 mm à x 2 100, 332 à 2 300, 115 à 2 500 ; rien sur la moitié arrière des bancs (places assises à x ≥ 2,95 m).
- Couple de chavirage (surface × hauteur du CV) : deux voiles pleines ≈ +37 % vs HC16 ; une voile ≈ −32 % ; deux voiles à 50 % ≈ −38 %. Réduire tôt.
- Vent arrière : au-delà de ~80° de choqué du même bord, la livarde au vent touche le mât sous le vent → ciseaux.

## Construction (cousu-collé, CP okoumé)
- Bordé cintré R450 : 4 mm ; fond 6 ; face AR 6 ; joues 9 (doublées au collier) ; cloisons 6 (évidées) ; assises 9 (ou 6 + lisses).
- Arêtes extérieures arrondies R ≥ 15 sous tissu ; trappes d'accès sur la face arrière.
- Allègement possible vers ≈ 25 kg de bois : joues 6 mm hors zone collier, assises 6 mm sur lisses, cloisons évidées.

## Écoute (voile réduite)
- Tire idéale = prolongement milieu du guindant → point d'écoute. Surface 75 % : hors bateau (≈ 5,45 m) ; 50 % : ≈ 4,78 m ; 25 % : sur la poutre AR.
- Montage : écoute sur rail de poutre AR ; barber (anneau sur l'écoute → poulie sur pontet extérieur du pont arrière vers 4,90–4,95 m → renvoi le long du bord extérieur → taquet vers 2,8 m, à portée de l'assise).
- Barre d'accouplement 20–30 cm derrière la poutre AR : barber toujours à l'extérieur des bras de safran, jamais sous la barre.
- Côté extérieur, angle d'écoute limité à ~3° sans bras en porte-à-faux.

## Points ouverts / mesures à prendre
- Entraxe des coques, longueur et section de la poutre AV, section des longerons.
- Pièces de fonderie d'angle Hobie (jonction poutre AV / longeron) : dégagement des entailles de joue et de banc.
- Système de barre : recul et hauteur de la barre d'accouplement, longueur et décalage des bras, débattement, axe des safrans.
- Choix restant : hauteur de coupe du coffre, longueur du plateau devant les mâts, hauteur exacte du collier (700–800 mm).
- Ensuite : développés des panneaux en DXF, imbriqués sur 2 500 × 1 220.

## Fichiers
- `hc16_rando_coffre_joues_voiles_pleines.step`, `hc16_rando_coffre_joues_voiles_50.step` : assemblage complet.
- `hc16_rando.py` + `cotes.yaml` : modèle paramétrique (CadQuery 2.8).
- `dessins/` : superpositions profil Chevalier, plans de pont, vues 3D de la conversation « Centre vélique sur la voile du HC 16 ».
