# WebUI

La WebUI de KToolBox est un panneau de gestion lié à un projet, construit avec React et HeroUI. Elle modifie la même configuration et appelle les mêmes services Python que la CLI ; elle ne lance ni n'analyse de sous-processus CLI. Les tâches, tentatives, journaux et enregistrements de propriété sont conservés dans `.ktoolbox/webui.sqlite3` au sein du projet choisi.

## Poursuivre selon votre objectif

<div class="grid cards" markdown>

-   :material-arrow-right-circle-outline: **Gérer les données du projet**

    Gérez les créateurs, les œuvres, le nommage, la configuration et les médias facultatifs dans les [parcours du projet](webui/project-workflows.md).

-   :material-arrow-right-circle-outline: **Surveiller les téléchargements**

    Créez, diagnostiquez, mettez en pause, reprenez, relancez et supprimez en sécurité dans [Tâches et mises à jour](webui/tasks.md).

-   :material-arrow-right-circle-outline: **Déployer et maintenir**

    Consultez les variables, sauvegardes, informations d'exécution et langues dans la [référence de déploiement](webui/reference.md).

</div>

## Installation et démarrage

Installez les composants facultatifs et créez un répertoire de projet :

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

Les identifiants sont facultatifs au démarrage. S'ils sont absents, le terminal affiche le nom `admin` et un nouveau mot de passe aléatoire valable pour ce processus. Pour utiliser des identifiants stables, générez un hachage Argon2id au moyen d'une saisie masquée :

```bash
ktoolbox webui hash-password
```

Enregistrez le compte dans le fichier `.env` du projet. Placez le hachage entre guillemets afin que les caractères `$` de style shell restent littéraux :

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

Démarrez le panneau pour ce projet :

```bash
ktoolbox webui .
ktoolbox webui . --host 127.0.0.1 --port 8789 --no-open
```

La valeur par défaut est `0.0.0.0:8789` et le navigateur local s'ouvre automatiquement. `--host`, `--port` et `--no-open` remplacent la configuration d'environnement pour ce processus. Si `ktoolbox.toml` manque, le démarrage affiche un avertissement et crée atomiquement un document minimal valide. L'absence d'identifiants ne bloque plus le démarrage : un nom vide devient `admin` et, si les deux formes de mot de passe sont vides, un nouveau mot de passe est généré et affiché dans le terminal pour cette exécution.

## Modèle de sécurité

KToolBox possède un seul compte WebUI local. La configuration explicite est prioritaire et `KTOOLBOX_WEBUI__PASSWORD_HASH` prime sur le réglage compatible en clair `KTOOLBOX_WEBUI__PASSWORD`. Si aucun mot de passe n'est configuré, KToolBox en génère un en mémoire à chaque démarrage et l'affiche avec le nom effectif uniquement dans ce terminal. Pour un déploiement stable, configurez de préférence un hachage et excluez les deux fichiers dotenv du contrôle de version.

Les sessions utilisent des jetons opaques aléatoires. SQLite ne stocke que leur hachage ; le cookie du navigateur est `HttpOnly` et `SameSite=Strict`, et devient `Secure` avec HTTPS. Les requêtes modificatrices exigent un jeton CSRF par session et la vérification de la même origine. Les tentatives de connexion sont limitées, les réponses d'API ne sont pas mises en cache et l'application envoie des en-têtes restrictifs pour le contenu, les cadres, la provenance et les autorisations du navigateur.

Le serveur intégré utilise HTTP. Son écoute par défaut sur le réseau local ne convient qu'à un réseau fiable, car mots de passe, cookies, chemins, journaux et configuration sont autrement visibles en transit. Pour une machine, utilisez `--host 127.0.0.1`. Pour un accès distant, terminez HTTPS sur un proxy inverse fiable et restreignez l'accès réseau. La page de connexion et l'enveloppe de l'application conservent un avertissement HTTP tant que la page n'est pas sécurisée.

Un seul planificateur peut ouvrir un projet à la fois. Un verrou empêche deux processus WebUI de se concurrencer sur la file et les sorties.

Le sélecteur de chemin distant utilise les droits du processus KToolBox. Les champs de tâche, de publication et de structure de téléchargement limités au projet ne peuvent pas sortir du projet lié, y compris via un lien symbolique. Les champs du répertoire de stockage et des journaux couvrent explicitement l'hôte et peuvent révéler les noms et métadonnées accessibles à ce compte. Les API du sélecteur se limitent à lister les métadonnées et à créer des répertoires : elles ne lisent pas le contenu, ne transfèrent, ne renomment et ne suppriment aucun fichier. Saisir un nouveau nom sélectionne un chemin sans créer de fichier vide. Considérez l'accès WebUI comme un accès sensible à l'hôte et ne l'accordez pas à des utilisateurs non fiables.
