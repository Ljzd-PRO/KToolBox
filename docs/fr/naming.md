# Format de nommage

Dans KToolBox v1, le nommage appartient au projet. La CLI et la WebUI lisent la même section `[naming]` de `ktoolbox.toml` ; ces champs ne sont plus modifiés comme paramètres dotenv globaux.

## Configurer la structure

La page **Format de nommage** permet de définir :

- les modèles de dossiers d’auteur, d’œuvre, de révision, d’année et de mois ;
- les modèles du fichier principal (couverture) et des pièces jointes ;
- les noms internes des pièces jointes, révisions, contenus et liens externes ;
- le classement annuel ou mensuel, le mélange des œuvres et la numérotation des pièces jointes.

La numérotation séquentielle des pièces jointes est activée par défaut, car Pawchive fournit souvent des noms de stockage illisibles. Désactivez-la uniquement lorsque les noms d’origine sont significatifs et doivent être conservés.

Seules les variables affichées à côté du champ sont acceptées, par exemple `{creator_name}`, `{creator_id}`, `{service}`, `{title}`, `{post_id}`, `{revision_id}`, `{year}` et `{month}`. Les séparateurs de chemin, remontées parent, variables inconnues et noms dangereux sont refusés avant l’analyse.

**Structure des répertoires** et **Modèles de nommage** disposent de boutons d’enregistrement distincts. L’enregistrement s’applique immédiatement aux futurs téléchargements, sans jamais déplacer les anciens fichiers.

L’**emplacement de téléchargement par défaut** appartient aussi au projet. Sa valeur initiale est `downloads` ; un chemin relatif est résolu depuis la racine du projet et un chemin absolu peut sortir du projet. L’ordre est : sortie explicite de la tâche, sortie explicite du plan de synchronisation automatique, puis valeur par défaut du projet. Chaque tâche conserve le chemin absolu résolu à sa création.

![Structure et emplacement par défaut](../assets/webui/37-naming-structure-desktop-light.png)

## Pièces jointes dans le dossier de l’œuvre

Dans **Structure des répertoires**, indiquez `.` ou `./` comme dossier des pièces jointes pour les placer à côté de la couverture et des métadonnées. Cette exception concerne uniquement les pièces jointes ; les chemins du contenu, des liens externes et des révisions doivent toujours porter un nom.

Les fichiers téléchargés avec ce réglage v0 sont pris en charge dans **Conversion des anciens téléchargements > Coller une configuration** :

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

Ajoutez les autres réglages de nommage modifiés en v0, car les champs ENV omis utilisent les valeurs par défaut de v0. Le format actuel du projet reste toujours la cible. Vérifiez la prévisualisation avant de confirmer : les pièces jointes identifiées par `post.json` ou l’index de l’auteur sont déplacées individuellement, y compris dans les révisions reconnues. Couvertures et métadonnées ne sont pas traitées comme des pièces jointes ; les fichiers non identifiés conservent leur emplacement relatif dans l’œuvre. Un fichier cible existant ou un chemin dangereux bloque la conversion sans écrasement.

## Convertir les anciens emplacements

Ouvrez l’onglet séparé **Conversion des anciens téléchargements** uniquement si le contenu existant doit adopter le format enregistré. Ajoutez les anciens emplacements, puis lancez leur analyse. Ces emplacements sont des sources de conversion, pas les destinations des futures tâches.

Le convertisseur reste disponible à tout moment et propose deux modes de source. **Historique du projet** permet de sélectionner plusieurs versions de nommage enregistrées lorsqu’un emplacement contient plusieurs générations d’arborescences. **Coller une configuration** accepte les anciennes clés `.env`, un `ktoolbox.toml` complet, une table `[naming]` ou un fragment sans en-tête. L’éditeur avec coloration fournit des exemples et localise les erreurs par champ ; le texte source reste uniquement en mémoire et n’est écrit ni dans le stockage du navigateur, ni dans les journaux, événements ou historiques. Dans les deux modes, la version actuelle du projet reste la cible en lecture seule et n’est jamais remplacée.

L’analyse lit directement le système de fichiers, ne dépend pas uniquement de l’historique des tâches et ne contacte pas Pawchive. Elle utilise l’identité des dossiers d’auteur, `creator-indices.ktoolbox` et `post.json`, sans suivre les liens symboliques hors des emplacements choisis.

La prévisualisation indique anciens et nouveaux chemins, nombres d’œuvres et de fichiers, taille totale, éléments ignorés et conflits. Tous les auteurs convertibles en sécurité sont sélectionnés par défaut.

![Prévisualisation mobile de conversion](../assets/webui/38-naming-conversion-mobile-dark.png)

KToolBox n’écrase ni ne fusionne une cible. Une prévisualisation périmée, une configuration modifiée, une tâche liée active, une cible dupliquée ou un changement du système de fichiers impose une nouvelle analyse.

## Convertir et récupérer

KToolBox exécute les déplacements choisis dans une tâche persistante en arrière-plan. **Pause** attend la fin de l’opération de fichier atomique en cours et conserve les déplacements achevés. **Continuer** revérifie la configuration, l’empreinte du système de fichiers, les conflits et l’espace libre. **Annuler** restaure les déplacements en ordre inverse. Une erreur d’écriture ou une interruption déclenche également une restauration sûre.

La progression et l’historique résident dans `.ktoolbox/webui.sqlite3`. Les journaux temporaires sont supprimés après réussite ; l’historique reste jusqu’à sa suppression manuelle. Les anciens dossiers devenus vides sont retirés, jamais les fichiers sans rapport.

## Migration au premier démarrage

L’assistant n’apparaît que si KToolBox détecte d’anciennes clés de nommage dans `.env` ou `prod.env`. Le démarrage se limite à la détection et à un avertissement dans le terminal ; aucun fichier n’est modifié. Après connexion, l’assistant :

1. présente la source, l’ancienne valeur et la valeur actuelle ;
2. sélectionne les anciennes valeurs par défaut, avec choix champ par champ ;
3. prévisualise les modifications du projet et les clés dotenv supprimées ;
4. après confirmation, sauvegarde sous `.ktoolbox/migrations/project-naming-v2/`, écrit `ktoolbox.toml` et supprime les anciennes clés de façon atomique ;
5. propose ensuite, séparément, la conversion des anciens répertoires.

![Assistant de migration des anciens réglages](../assets/webui/39-naming-migration-desktop-light.png)

Fermer ou choisir **Ignorer** ne masque que cette occurrence. Tant que les anciennes clés existent, l’assistant réapparaît après actualisation ou reconnexion. Migration de configuration et conversion de répertoires sont distinctes : vérifiez les anciens emplacements puis lancez explicitement leur analyse. Ouvrir l’outil ne déclenche ni analyse ni déplacement.

La CLI utilise également le nommage du projet. Pour un ancien projet, confirmez dans la WebUI la migration atomique avec sauvegarde. Les anciennes valeurs présentes uniquement dans l’environnement du processus ne peuvent pas être supprimées : elles sont ignorées pour le nommage et restent signalées jusqu’à leur retrait de l’environnement de lancement.

## Guides associés

- Consultez le [guide WebUI](webui.md) pour la page de nommage et le processus de conversion.
- Utilisez le [guide de configuration](configuration/guide.md) pour les réglages globaux du réseau et du téléchargeur.
- Suivez le [guide de migration v1](migration-v1.md) lors de la mise à niveau d'un projet existant.
