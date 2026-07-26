# Format de nommage

Dans KToolBox v1, le nommage appartient au projet. La CLI et la WebUI lisent la même section `[naming]` de `ktoolbox.toml` ; ces champs ne sont plus modifiés comme paramètres dotenv globaux.

## Configurer la structure

La page **Format de nommage** permet de définir :

- un ou plusieurs répertoires racines de téléchargement ;
- les modèles de dossiers d’auteur, d’œuvre, de révision, d’année et de mois ;
- les modèles du fichier principal et des pièces jointes ;
- les noms internes des pièces jointes, révisions, contenus et liens externes ;
- le classement annuel ou mensuel, le mélange des œuvres et la numérotation des pièces jointes.

Seules les variables affichées à côté du champ sont acceptées, par exemple `{creator_name}`, `{creator_id}`, `{service}`, `{title}`, `{post_id}`, `{revision_id}`, `{year}` et `{month}`. Les séparateurs de chemin, remontées parent, variables inconnues et noms dangereux sont refusés avant l’analyse.

![Modèles de nommage en thème sombre](../assets/webui/34-naming-templates-desktop-dark.png)

## Prévisualiser les téléchargements

**Analyser et vérifier** parcourt les vrais répertoires racines. L’opération ne dépend pas de l’historique des tâches et ne contacte pas Pawchive. Elle utilise l’identité des dossiers d’auteur, `creator-indices.ktoolbox` et `post.json`, sans suivre les liens symboliques hors des racines.

La prévisualisation indique anciens et nouveaux chemins, nombres d’œuvres et de fichiers, taille totale, éléments ignorés et conflits. **Convertir les auteurs téléchargés** est activé par défaut et sélectionne tous les auteurs convertibles en sécurité.

![Prévisualisation mobile de conversion](../assets/webui/35-naming-conversion-mobile-light.png)

KToolBox n’écrase ni ne fusionne une cible. Une prévisualisation périmée, une configuration modifiée, une tâche liée active, une cible dupliquée ou un changement du système de fichiers impose une nouvelle analyse.

## Appliquer et récupérer

Lorsque la conversion est active, KToolBox enregistre un instantané en attente puis déplace les fichiers en arrière-plan. Le nouveau format n’est activé qu’après la réussite de toutes les opérations choisies. Une annulation, une erreur d’écriture ou une interruption restaure les déplacements en ordre inverse et conserve l’ancienne configuration.

La progression et l’historique résident dans `.ktoolbox/webui.sqlite3`. Les journaux temporaires sont supprimés après réussite ; l’historique reste jusqu’à sa suppression manuelle. Les anciens dossiers devenus vides sont retirés, jamais les fichiers sans rapport.

Sans conversion, seul le nouveau format est enregistré. Les téléchargements existants restent en place et les futurs téléchargements CLI ou WebUI utilisent le nouveau format du projet.

## Migration au premier démarrage

Au premier démarrage de la WebUI, KToolBox migre les anciennes clés de `.env` et `prod.env` avant de créer une configuration par défaut :

1. écriture des valeurs effectives dans `ktoolbox.toml` ;
2. sauvegarde sous `.ktoolbox/migrations/project-naming-v2/` ;
3. suppression des anciennes clés dotenv ;
4. résumé dans le terminal ;
5. notification WebUI unique après connexion.

![Notification unique de migration](../assets/webui/36-naming-migration-notice-light.png)

La CLI utilise également le nommage du projet. Démarrez une fois la WebUI d’un ancien projet pour terminer cette migration atomique avec sauvegarde.
