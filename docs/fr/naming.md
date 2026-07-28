# Format de nommage

Dans KToolBox v1, le nommage appartient au projet. La CLI et la WebUI lisent la même section `[naming]` de `ktoolbox.toml` ; ces champs ne sont plus modifiés comme paramètres dotenv globaux.

## Configurer la structure

La page **Format de nommage** permet de définir :

- les modèles de dossiers d’auteur, d’œuvre, de révision, d’année et de mois ;
- les modèles du fichier principal et des pièces jointes ;
- les noms internes des pièces jointes, révisions, contenus et liens externes ;
- le classement annuel ou mensuel, le mélange des œuvres et la numérotation des pièces jointes.

Seules les variables affichées à côté du champ sont acceptées, par exemple `{creator_name}`, `{creator_id}`, `{service}`, `{title}`, `{post_id}`, `{revision_id}`, `{year}` et `{month}`. Les séparateurs de chemin, remontées parent, variables inconnues et noms dangereux sont refusés avant l’analyse.

**Structure des répertoires** et **Modèles de nommage** disposent de boutons d’enregistrement distincts. L’enregistrement s’applique immédiatement aux futurs téléchargements, sans jamais déplacer les anciens fichiers.

![Modèles de nommage en thème sombre](../assets/webui/34-naming-templates-desktop-dark.png)

## Convertir les anciens emplacements

Ouvrez l’onglet séparé **Conversion des anciens téléchargements** uniquement si le contenu existant doit adopter le format enregistré. Ajoutez les anciens emplacements, puis lancez leur analyse. Ces emplacements sont des sources de conversion, pas les destinations des futures tâches.

L’analyse lit directement le système de fichiers, ne dépend pas uniquement de l’historique des tâches et ne contacte pas Pawchive. Elle utilise l’identité des dossiers d’auteur, `creator-indices.ktoolbox` et `post.json`, sans suivre les liens symboliques hors des emplacements choisis.

La prévisualisation indique anciens et nouveaux chemins, nombres d’œuvres et de fichiers, taille totale, éléments ignorés et conflits. Tous les auteurs convertibles en sécurité sont sélectionnés par défaut.

![Prévisualisation mobile de conversion](../assets/webui/35-naming-conversion-mobile-light.png)

KToolBox n’écrase ni ne fusionne une cible. Une prévisualisation périmée, une configuration modifiée, une tâche liée active, une cible dupliquée ou un changement du système de fichiers impose une nouvelle analyse.

## Convertir et récupérer

KToolBox exécute les déplacements choisis dans une tâche persistante en arrière-plan. Une annulation, une erreur d’écriture ou une interruption restaure les déplacements en ordre inverse. Le format déjà enregistré reste actif pour les futurs téléchargements.

La progression et l’historique résident dans `.ktoolbox/webui.sqlite3`. Les journaux temporaires sont supprimés après réussite ; l’historique reste jusqu’à sa suppression manuelle. Les anciens dossiers devenus vides sont retirés, jamais les fichiers sans rapport.

## Migration au premier démarrage

Au premier démarrage de la WebUI, KToolBox migre les anciennes clés de `.env` et `prod.env` avant de créer une configuration par défaut :

1. écriture des valeurs effectives dans `ktoolbox.toml` ;
2. sauvegarde sous `.ktoolbox/migrations/project-naming-v2/` ;
3. suppression des anciennes clés dotenv ;
4. résumé dans le terminal ;
5. choix obligatoire après connexion entre ignorer définitivement l’ancien contenu et vérifier une conversion.

![Notification unique de migration](../assets/webui/36-naming-migration-notice-light.png)

La boîte de dialogue ne peut pas être fermée sans choix et réapparaît après actualisation. **Vérifier la conversion** ouvre l’onglet dédié ; les anciens emplacements connus sont analysés automatiquement, sinon la page demande d’en ajouter un. Aucun fichier n’est déplacé avant confirmation de la prévisualisation.

La CLI utilise également le nommage du projet. Démarrez une fois la WebUI d’un ancien projet pour terminer cette migration atomique de configuration avec sauvegarde.
