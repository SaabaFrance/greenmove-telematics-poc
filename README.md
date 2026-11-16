# GreenMove Logistics
POC Python 3 pour le bloc 2. Depuis le répertoire du projet, sans réseau et sans dépendance tierce :
```sh
python3 moteur.py
python3 -m json.tool daily_score.json
python3 -m unittest -v
```
Le dossier data reprend les valeurs de l’annexe 3. Geo calcule OUT, OUT, OUT, IN, IN et signale l’entrée à 08:00:30. Le libellé fourni pour 08:00:20 contredit les coordonnées. Le champ expected n’est jamais lu. Chaque point est traité dès sa lecture dans la trace simulée ; aucune mesure de latence matérielle n’est revendiquée.

Safety traite un CSV par jour UTC, en ordre chronologique, dans le repère du véhicule. L’axe Y négatif indique une décélération. Le seuil strict d’entrée est −2,5 m/s² et le réarmement intervient à −2,0 m/s². Un franchissement donne un événement horodaté, avec son minimum. Score illustratif = max(0, 100 − 10 × nombre d’événements), sans valeur contractuelle. Sortie écrite seulement après lecture réussie. Vérifier le code retour avant d’exploiter un fichier de sortie existant.

Pour comparer la lecture littérale de 2,5 g :
```sh
python3 moteur.py --seuil 24.516625 --sortie score_g.json
```
Résultat attendu : zéro freinage, contre un au seuil de l’annexe. Pour la démo d’erreur, exécuter les tests puis modifier une copie des données :
```sh
cp -R data essai
echo '1678880010,0,invalide,9.81' >> essai/accelerometer_data.csv
python3 moteur.py --data essai --sortie essai/score.json
```
Pour cloner la version Git fournie, depuis le dossier qui contient le bundle : `git clone GreenMove.bundle GreenMove`. La branche main contient le code et les données. Le moteur n’intègre pas la navigation prédictive, les cartes européennes, l’interface, SQLite ou la transmission distante. L’exécution sur tablette et le calibrage de l’axe restent à valider.
