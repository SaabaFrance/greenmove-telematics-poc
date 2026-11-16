# GreenMove Logistics

À la sortie du tunnel de Fourvière, un chauffeur a reçu une amende parce que l’application n’avait pas pu charger la carte de la zone à faibles émissions (ZFE). C’est le point de départ de ce prototype. Si une alerte doit être donnée dans la cabine, le camion doit pouvoir la déclencher même quand la 4G est coupée.

Pour le bloc 2 du Mastère CTO & Tech Lead, j’ai donc travaillé sur deux questions. Peut-on détecter localement l’entrée du camion dans une ZFE ? Et peut-on retrouver un freinage brusque dans les vibrations enregistrées pendant le trajet ?

## Lancer le prototype

Il suffit d’avoir Python 3. Le programme utilise uniquement sa bibliothèque standard. Une fois le projet téléchargé, la démonstration fonctionne hors connexion.

Depuis un terminal ouvert dans le dossier qui contient `moteur.py`, lancer :

```bash
python3 moteur.py
```

Avec les données de l’annexe 3, deux lignes permettent de vérifier le résultat :

```text
08:00:30 IN [ALERT ZFE]
[FREINAGE] 1678880005 -3.45 m/s²
```

Le programme écrit aussi un bilan dans `daily_score.json`. Pour le lire, puis lancer les six tests :

```bash
python3 -m json.tool daily_score.json
python3 -m unittest -v
```

## Comment le moteur détecte l’entrée en ZFE

Le programme lit le contour de la zone dans `data/lyon_polygon.json` et les positions successives du camion dans `data/truck_gps.json`.

J’ai choisi un calcul en deux temps. Je commence par le rectangle qui entoure la ZFE (*bounding box*). Si le camion est en dehors de ce rectangle, je peux passer au point suivant. S’il est dedans, il reste à vérifier la forme réelle de la zone. Pour cela, je trace un rayon depuis le point GPS et je compte ses intersections avec le contour (*ray casting*). Un nombre impair indique que le point est à l’intérieur.

Le troisième point du trajet montre pourquoi cette seconde vérification est utile. À `08:00:20`, il est dans le rectangle, mais ses coordonnées le placent encore au nord du polygone. L’annexe l’étiquette « IN (Bordure) ». J’ai conservé les données fournies et laissé le moteur décider à partir des coordonnées. L’entrée est détectée au point suivant, à `08:00:30`. Le camion est encore dans la zone dix secondes plus tard, donc l’alerte ne se répète pas.

## Comment le moteur repère un freinage

Dans `data/accelerometer_data.csv`, l’axe Y correspond au mouvement avant-arrière du camion. Le passage intéressant se lit sur trois mesures successives : **−0,80**, **−3,45**, puis **−1,20 m/s²**.

J’enregistre un freinage quand Y descend sous **−2,5 m/s²**. J’attends ensuite que Y remonte à **−2,0 m/s²** ou davantage avant de pouvoir compter un nouvel événement. Cela évite de compter plusieurs freinages si le signal oscille autour du seuil pendant une même manœuvre.

L’unité a son importance ici. La consigne du module mentionne **2,5 g**, tandis que l’annexe donne les mesures et le seuil en **m/s²**. J’ai retenu l’unité de l’annexe pour le réglage par défaut. On peut vérifier l’effet de l’autre interprétation avec cette commande :

```bash
python3 moteur.py --seuil 24.516625 --sortie score_g.json
```

Avec le seuil de l’annexe, le bilan donne **un freinage sur dix mesures**. Avec un seuil de 2,5 g, il en donne **zéro**. Le score de 90/100 dans le premier bilan illustre un barème simple : dix points retirés par événement. Un freinage brusque peut être justifié par un obstacle. À lui seul, ce score ne permet pas de juger la conduite.

## Vérifier le comportement en cas d’erreur

Pour la démonstration, je travaille sur une copie des données. Sur Mac ou Linux, ces commandes ajoutent une mesure illisible et relancent le moteur :

```bash
essai=$(mktemp -d)
cp -R data "$essai/data"
echo '1678880010,0,invalide,9.81' >> "$essai/data/accelerometer_data.csv"
python3 moteur.py --data "$essai/data" --sortie "$essai/score.json"
python3 -m json.tool "$essai/score.json"
```

Le programme signale la ligne incorrecte et traite les autres mesures. Dans le bilan, `ignorees` vaut alors `1` et le freinage reste détecté.

## Ce qu’il reste à vérifier sur le terrain

Ce prototype permet de rejouer un trajet court sur ordinateur. Avant d’équiper une flotte, je testerais la cadence de 100 Hz sur la tablette Zebra, l’orientation du capteur une fois fixé dans la cabine et la capacité à distinguer un freinage d’un choc sur la chaussée. Je vérifierais également le délai de l’alerte en conditions réelles. Détecter un franchissement et prévenir le chauffeur assez tôt pour qu’il puisse prendre une autre sortie sont deux étapes distinctes.
