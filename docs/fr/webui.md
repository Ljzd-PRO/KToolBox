# WebUI

La WebUI de KToolBox est un panneau de gestion lié à un projet, construit avec React et HeroUI. Elle modifie la même configuration et appelle les mêmes services Python que la CLI ; elle ne lance ni n'analyse de sous-processus CLI. Les tâches, tentatives, journaux et enregistrements de propriété sont conservés dans `.ktoolbox/webui.sqlite3` au sein du projet choisi.

## Installation et démarrage

Installez les composants facultatifs et créez un répertoire de projet :

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

Générez un hachage de mot de passe Argon2id au moyen d'une saisie masquée dans le terminal :

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

La valeur par défaut est `0.0.0.0:8789` et le navigateur local s'ouvre automatiquement. `--host`, `--port` et `--no-open` remplacent la configuration d'environnement pour ce processus. Si `ktoolbox.toml` manque, le démarrage affiche un avertissement et crée atomiquement un document minimal valide. Le démarrage échoue toujours si le nom d'utilisateur ou les deux formes de mot de passe manquent.

## Modèle de sécurité

KToolBox possède un compte WebUI local et aucun identifiant par défaut. `KTOOLBOX_WEBUI__PASSWORD_HASH` a priorité sur le réglage de compatibilité en clair `KTOOLBOX_WEBUI__PASSWORD`. Préférez le hachage et excluez les deux fichiers dotenv du contrôle de version.

Les sessions utilisent des jetons opaques aléatoires. SQLite ne stocke que leur hachage ; le cookie du navigateur est `HttpOnly` et `SameSite=Strict`, et devient `Secure` avec HTTPS. Les requêtes modificatrices exigent un jeton CSRF par session et la vérification de la même origine. Les tentatives de connexion sont limitées, les réponses d'API ne sont pas mises en cache et l'application envoie des en-têtes restrictifs pour le contenu, les cadres, la provenance et les autorisations du navigateur.

Le serveur intégré utilise HTTP. Son écoute par défaut sur le réseau local ne convient qu'à un réseau fiable, car mots de passe, cookies, chemins, journaux et configuration sont autrement visibles en transit. Pour une machine, utilisez `--host 127.0.0.1`. Pour un accès distant, terminez HTTPS sur un proxy inverse fiable et restreignez l'accès réseau. La page de connexion et l'enveloppe de l'application conservent un avertissement HTTP tant que la page n'est pas sécurisée.

Un seul planificateur peut ouvrir un projet à la fois. Un verrou empêche deux processus WebUI de se concurrencer sur la file et les sorties.

## Processus du projet

L'interface suit la langue du navigateur lors de la première utilisation et conserve le choix entre l'anglais et le chinois simplifié. Le thème suit le système d'exploitation jusqu'au choix du mode clair ou sombre. Des accents bleu, émeraude, violet, rose et ambre sont proposés ; les interrupteurs activés restent bleus afin que leur état soit cohérent. L'ordinateur utilise une barre latérale compacte et les écrans étroits un Drawer.

![Éditeur de configuration clair](../assets/webui/09-configuration-light.png)

Les zones modifiables utilisent une surface secondaire discrète avec des arrière-plans de champs distincts. Les icônes facilitent le repérage, tandis que les interrupteurs et cases restent alignés à gauche avec leur libellé au lieu de ressembler à des boutons centrés. La piste est grise à l'arrêt et bleue en marche ; les cases n'affichent un indicateur que lorsqu'elles sont cochées ou indéterminées. Le contenu de la fenêtre modifiable et sa barre d'actions fixe partagent une surface continue.

Les zones principales sont :

- **Vue d'ensemble :** chemin du projet, état de la file, totaux des transferts actifs et tâches récentes.
- **Tâches :** créer, classer, modifier, mettre en pause, reprendre, arrêter, relancer, supprimer et examiner des synchronisations ou téléchargements uniques.
- **Créateurs :** rechercher dans Pawchive et ajouter, renommer, activer, désactiver ou retirer des entrées.
- **Publications :** rechercher sans afficher les médias distants ni le corps développé, examiner les révisions et créer une tâche de téléchargement.
- **Règles d'exclusion :** ordonner et limiter `field-match`, composer des groupes `any`/`all` imbriqués et des conditions de contenu, égalité, expression régulière et existence.
- **Configuration :** modifier `.env`, `prod.env` et `ktoolbox.toml` dans des formulaires typés ou des vues de texte avancées.
- **Système :** examiner les versions du projet et de l'application et télécharger un exemple d'environnement.

![Éditeur de tâche sur un écran étroit](../assets/webui/19-task-form-mobile-light-zh.png)

![Liste des créateurs sur un écran étroit](../assets/webui/12-creators-mobile-light-zh.png)

## Modification de la configuration

Les libellés sont du texte explicite en anglais et en chinois simplifié, pas des identifiants Python. Les descriptions proviennent des chaînes `:ivar field:` des classes anglaises et chinoises ; Pydantic fournit les types, valeurs par défaut, plages et métadonnées secrètes.

Les onglets `.env` et `prod.env` affichent la valeur effective finale et une puce de provenance. Les valeurs remplacées par l'environnement du processus sont en lecture seule. Les secrets sont masqués par défaut. L'édition avancée du texte affiche un avertissement supplémentaire, car elle peut dévoiler des secrets.

Avant l'enregistrement, le serveur analyse et valide le fichier proposé, puis renvoie une différence sémantique. Un ETag refuse les modifications obsolètes et le fichier est remplacé atomiquement. L'éditeur TOML utilise le stockage TomlKit/Pydantic existant, les commentaires survivent donc aux changements structurés.

![Éditeur de configuration sombre](../assets/webui/20-configuration-1024-dark-zh.png)

![Éditeur de règle à portée limitée](../assets/webui/17-blocker-form-1024-light-zh.png)

## Cycle de vie des tâches

Les tâches `sync` et `download` conservent toutes les entrées de la CLI correspondante. Une synchronisation sans cible résout la liste actuellement activée lors de la création. Chaque tentative reçoit ensuite un instantané immuable et expurgé de la configuration ; les modifications ultérieures n'affectent que les tentatives futures.

Chaque tâche conserve aussi un instantané réservé à la présentation avec sa clé cible normalisée, ainsi que les titre et nom du créateur facultatifs. Il reste lisible hors ligne et n'affecte jamais l'exécution, la déduplication ou les verrous. Les lignes commencent par cette cible plutôt que le chemin de sortie, et les détails, la pause/reprise, l'arrêt, la modification, le classement et la suppression restent visibles directement.

![File de tâches de bureau avec des cibles lisibles](../assets/webui/21-task-queue-1440-dark-zh.png)

![File mobile avec actions directes](../assets/webui/22-task-queue-mobile-light-zh.png)

![Éditeur de tâche sombre](../assets/webui/18-task-form-1024-dark-zh.png)

La file principale exécute deux tâches par défaut (`KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS`), tandis que chacune conserve sa simultanéité configurée de créateurs et de fichiers. Les tâches actives identiques renvoient à la tâche existante. Les tâches dont les sorties, créateurs ou publications normalisés se chevauchent attendent dans `blocked` la libération du verrou.

Les événements en direct utilisent SSE avec reconnexion. L'état REST reste la référence. La vue détaillée indique les créateurs préparés, les fichiers, les octets, la progression totale, les vitesses globale et par fichier, l'heure estimée, les nombres ignorés/échoués, les éléments actifs et les journaux structurés.

![Progression d'une tâche en direct](../assets/webui/14-task-running-1024-dark-zh.png)

La pause est coopérative : les flux réseau actifs se ferment, les fichiers terminés et temporaires pouvant reprendre restent, et la reprise crée une nouvelle tentative. L'arrêt conserve la définition pour pouvoir la modifier et la relancer. Un redémarrage marque l'ancien travail actif `interrupted` ; la récupération est toujours explicite.

Supprimer une tâche ne retire normalement que son enregistrement, ses tentatives et ses journaux. « Supprimer les sorties » présente d'abord le nombre de fichiers et d'octets. La confirmation ne retire que les fichiers ordinaires inchangés enregistrés comme créés par cette tâche ; les liens symboliques et les fichiers préexistants, modifiés ou partagés ne sont ni suivis ni retirés.

## Référence de l'environnement WebUI

| Variable | Valeur par défaut | Signification |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | Interface d'écoute. |
| `KTOOLBOX_WEBUI__PORT` | `8789` | Port d'écoute, de 1 à 65535. |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | Ouvrir l'URL locale après le démarrage. |
| `KTOOLBOX_WEBUI__USERNAME` | vide | Nom requis du compte unique. |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | vide | Hachage Argon2id recommandé. |
| `KTOOLBOX_WEBUI__PASSWORD` | vide | Solution en clair ; ignorée si un hachage existe. |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | Tâches principales simultanées, de 1 à 16. |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | Durée de session depuis la dernière utilisation. |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | Durée maximale depuis la connexion. |

Sauvegardez ensemble `ktoolbox.toml`, les fichiers dotenv locaux et `.ktoolbox/webui.sqlite3` lorsque l'historique importe. Ne copiez pas la base pendant l'exécution de la WebUI.
