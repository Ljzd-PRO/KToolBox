# Référence des commandes

Exécutez `ktoolbox COMMAND --help` pour obtenir l'aide Cyclopts faisant autorité. Les noms des commandes et options utilisent des traits d'union ; les anciennes graphies avec traits de soulignement sont toujours analysées par les commandes de compatibilité masquées.

## Options globales

| Option | Signification |
| --- | --- |
| `-h`, `--help` | Afficher l'aide directement sans afficheur paginé. |
| `--version` | Afficher la version installée de KToolBox. |
| `--install-completion` | Installer l'autocomplétion pour l'interpréteur détecté. |
| `--config PATH` | Choisir un fichier de projet. L'ordre de résolution est cette option, `KTOOLBOX_PROJECT_CONFIG`, puis `./ktoolbox.toml`. |
| `--verbose` | Inclure les journaux de diagnostic. |
| `--quiet` | Masquer la progression et les journaux ordinaires. |
| `--plain` | Imposer une progression stable ligne par ligne. Les sorties hors TTY et `NO_COLOR` l'utilisent automatiquement. |
| `--no-color` | Désactiver les couleurs ANSI. |

Exécuter `ktoolbox` sans argument affiche l'aide principale et se termine correctement.

## Arbre des commandes

| Commande | Objet |
| --- | --- |
| `download` | Télécharger une publication ou la révision choisie. |
| `sync [TARGET ...]` | Synchroniser les créateurs explicites ou tous ceux activés dans la liste lorsqu'aucune cible n'est fournie. |
| `creator list/add/remove/enable/disable/search` | Gérer la liste ou rechercher des créateurs Pawchive. |
| `post show/search` | Examiner une publication ou rechercher les publications d'un créateur. |
| `config edit/example/validate/path` | Modifier ou examiner l'environnement et la configuration du projet. |
| `site-version` | Afficher la version de l'application Pawchive. |
| `webui [PROJECT_DIR]` | Exécuter le panneau HeroUI facultatif pour un projet. |

## `download`

Fournissez une URL de publication Pawchive, ou l'ensemble de `--service`, `--creator-id` et `--post-id`.

| Argument ou option | Type | Valeur par défaut | Signification |
| --- | --- | --- | --- |
| `POST` | chaîne | omis | URL d'une publication ou d'une révision Pawchive. |
| `--service` | chaîne | omis | Service du créateur. |
| `--creator-id` | chaîne | omis | ID du créateur. |
| `--post-id` | chaîne | omis | ID de la publication. |
| `--revision-id` | chaîne | omis | Choisir cette révision dans la liste. |
| `-o`, `--output`, `--path` | chemin | `.` | Racine de sortie. |
| `--dump-post-data` / `--no-dump-post-data` | booléen | activé | Enregistrer les métadonnées validées dans `post.json`. |

`download` n'applique volontairement pas les règles d'exclusion de la liste.

## `sync`

Chaque `TARGET` peut être une URL de créateur Pawchive, une identité `service:id` ou un alias de la liste. Les cibles explicites s'exécutent même lorsqu'elles sont désactivées dans la liste. Sans cible, tous les créateurs activés s'exécutent.

| Argument ou option | Type | Valeur par défaut | Signification |
| --- | --- | --- | --- |
| `TARGET ...` | chaînes | liste activée | Zéro ou plusieurs créateurs. |
| `--service` + `--creator-id` | chaînes | omis | Ajouter un créateur explicite ; les deux sont nécessaires ensemble. |
| `-o`, `--output`, `--path` | chemin | `.` | Racine de sortie. |
| `--save-creator-indices` | booléen | désactivé | Enregistrer atomiquement l'index du créateur après une production réussie. |
| `--mix-posts` / `--no-mix-posts` | booléen | configuration d'environnement | Remplacer `job.mix_posts`. |
| `--start-time`, `--start` | date | omis | Borne inférieure inclusive de publication, `YYYY-MM-DD`. |
| `--end-time`, `--end` | date | omis | Borne supérieure inclusive de publication, `YYYY-MM-DD`. |
| `--offset` | entier | `0` | Index de la première publication. |
| `--length` | entier | toutes | Nombre maximal de publications acceptées par créateur. |
| `--keywords` | chaîne répétée | configuration d'environnement | Inclure les titres contenant l'une des valeurs. |
| `--keywords-exclude` | chaîne répétée | configuration d'environnement | Ancienne entrée de compatibilité pour exclure les titres. |

`job.creator_concurrency` limite la production des créateurs, tandis que `job.count` limite les travailleurs de fichiers partagés.

## `creator`

| Commande | Arguments et options | Signification |
| --- | --- | --- |
| `creator list` | `--json` | Afficher les entrées comme tableau Rich ou JSON. |
| `creator add TARGET` | `--alias NAME`, `--disabled` | Ajouter une URL ou un `service:id`. |
| `creator remove TARGET` | | Retirer par alias, URL ou identité. |
| `creator enable TARGET` | | Activer un créateur enregistré. |
| `creator disable TARGET` | | Désactiver un créateur enregistré. |
| `creator search` | `--name`, `--creator-id`/`--id`, `--service`, `--dump`, `--json` | Filtrer la liste publique des créateurs. |

## `post`

| Commande | Arguments et options | Signification |
| --- | --- | --- |
| `post search` | `--creator-id`/`--id`, `--name`, `--service`, `-q`/`--query`, `-o`/`--offset`, `--dump`, `--json` | Rechercher les publications des créateurs choisis. Une requête directe d'API comporte au moins 3 caractères et son décalage est divisible par 50. |
| `post show SERVICE CREATOR_ID POST_ID [REVISION_ID]` | `--dump`, `--json` | Afficher les métadonnées de la publication actuelle ou une révision choisie. |

Sans `--json`, les commandes de requête omettent volontairement le corps de la publication dans les tableaux du terminal.

## `config`

| Commande | Signification |
| --- | --- |
| `config path` | Afficher le chemin résolu du projet sans retour à la ligne. |
| `config validate` | Valider la version du schéma, l'unicité des créateurs, les types et portées des règles, les conditions et les expressions régulières. |
| `config example` | Produire tous les réglages dotenv à partir des chaînes de documentation du modèle. |
| `config edit` | Ouvrir l'éditeur Urwid facultatif et valider avant l'enregistrement. |

## `webui`

Installez `ktoolbox[webui]` avant d'utiliser ces commandes. La commande par défaut accepte un répertoire de projet et crée un fichier `ktoolbox.toml` absent après un avertissement. Les identifiants valides d'un compte unique restent nécessaires.

| Argument ou option | Valeur par défaut | Signification |
| --- | --- | --- |
| `PROJECT_DIR` | `.` | Projet de synchronisation fixe servi par ce processus. |
| `--host` | `webui.host` | Remplacer l'interface d'écoute. |
| `--port` | `webui.port` | Remplacer le port TCP. |
| `--no-open` | désactivé | Ne pas ouvrir l'URL locale dans le navigateur par défaut. |
| `webui hash-password` | | Demander deux fois une saisie masquée dans le terminal et afficher un hachage Argon2id. |

Le serveur intégré affiche un avertissement de sécurité HTTP. Consultez le [guide de la WebUI](../webui.md) avant de l'exposer au-delà de localhost.

## Alias de compatibilité

Ces alias sont masqués dans l'aide et émettent un avertissement d'obsolescence par appel :

| Ancien nom | Remplacement |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

## Codes de sortie et flux

| Code | Signification |
| --- | --- |
| `0` | Succès. |
| `1` | Échec distant, de créateur ou de téléchargement, y compris une réussite partielle avec plusieurs créateurs. |
| `2` | Arguments ou configuration incorrects. |
| `130` | Interruption par l'utilisateur. |

Les tableaux et JSON utilisent stdout. Les journaux, la progression, les avertissements et les erreurs utilisent stderr.
