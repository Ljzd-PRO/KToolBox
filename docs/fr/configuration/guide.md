# Guide de configuration

KToolBox possède deux niveaux de configuration :

- `.env`, `prod.env` et les variables du processus contrôlent l'API, les transferts, le nommage et le comportement global des téléchargements.
- `ktoolbox.toml` conserve la liste des créateurs du projet et les règles ordonnées d'exclusion des publications.

KToolBox lit `.env`, puis `prod.env`, depuis le répertoire de travail actuel. Les valeurs de `prod.env` remplacent les valeurs correspondantes de `.env`, tandis que les variables d'environnement du processus ont la priorité la plus élevée.

Les champs imbriqués utilisent deux traits de soulignement. Par exemple, `KTOOLBOX_API__TIMEOUT` correspond à `config.api.timeout`.

```dotenv
# Requêtes de l'API Pawchive.
KTOOLBOX_API__TIMEOUT=10
KTOOLBOX_API__RETRY_TIMES=4
KTOOLBOX_API__RETRY_INTERVAL=2

# Transferts de fichiers.
KTOOLBOX_DOWNLOADER__TIMEOUT=30
KTOOLBOX_DOWNLOADER__TPS_LIMIT=5

# Tâches de téléchargement.
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

Tous les réglages sont facultatifs. Consultez la [référence de configuration](reference.md) pour les valeurs par défaut.

## Générer ou modifier la configuration

Générez toutes les clés dotenv disponibles à partir du modèle actuel :

```bash
ktoolbox config example
```

L'éditeur de terminal facultatif peut afficher les descriptions de champs extraites des chaînes de documentation du modèle :

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config edit
```

La [WebUI](../webui.md) facultative présente les mêmes descriptions en anglais et en chinois simplifié dans des contrôles typés, ainsi que la source des valeurs finales, le masquage des secrets, la modification directe de dotenv/TOML, la validation, l'aperçu des différences et la protection contre les conflits ETag.

Examinez ou validez le fichier du projet sans ouvrir l'éditeur :

```bash
ktoolbox config path
ktoolbox config validate
```

Le chemin du projet est résolu dans l'ordre suivant : l'option globale `--config`, `KTOOLBOX_PROJECT_CONFIG`, puis `./ktoolbox.toml`. Les écritures utilisent un fichier temporaire dans le même répertoire et un remplacement atomique ; TomlKit conserve les commentaires.

## Liste des créateurs

Chaque document de projet commence par `schema_version = 1`. Les créateurs sont uniques par `service:id` sans distinction de casse ; les alias facultatifs sont également uniques.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[creators]]
service = "patreon"
creator_id = "456"
alias = "studio-b"
enabled = false
```

Utilisez `creator add`, `remove`, `enable` et `disable` plutôt que de modifier à la main les entrées simples. `sync` sans cible utilise toutes les entrées activées ; les alias ou identités explicites s'exécutent indépendamment de `enabled`.

## Règles d'exclusion des publications {#post-blockers}

Les règles s'exécutent dans l'ordre du TOML et la première correspondance exclut la publication. Une règle globale s'applique à tous les créateurs synchronisés ; une portée par créateur répertorie les valeurs `service:id` exactes. Les règles désactivées restent configurées mais ne s'exécutent pas.

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["life update", "daily note"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["progress|practice"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match` prend en charge les groupes récursifs `any`/`all` et `negate` sur un groupe ou une condition. Les conditions acceptent :

| Opérateur | Comportement |
| --- | --- |
| `contains` | L'une des valeurs scalaires choisies contient une valeur configurée. |
| `equals` | L'une des valeurs scalaires choisies est égale à une valeur configurée. |
| `regex` | L'une des valeurs scalaires choisies correspond à une expression régulière. Les motifs sont compilés lors de la validation. |
| `exists` | Le chemin choisi existe et n'est pas nul ; `expected = false` inverse cette attente. |

Les comparaisons ne tiennent pas compte de la casse, sauf si `case_sensitive = true`. Les chemins sûrs à points peuvent inclure des sélecteurs de liste `[*]`, par exemple `tags[*]`, `file.name` et `attachments[*].name`. Un chemin absent ne correspond pas. Les expressions Python et le code arbitraire ne sont jamais évalués.

Les règles évaluent la réponse de la liste avant les détails, révisions, répertoires, métadonnées ou tâches de téléchargement. Les publications et révisions exclues n'entrent pas dans l'index du créateur, et le texte correspondant n'est pas affiché. L'interface asynchrone `PostBlocker` et son registre permettent d'ajouter de futurs types sans modifier le coordinateur de synchronisation.

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` reste accepté comme ancienne règle globale implicite « le titre contient ». KToolBox ne le réécrit pas automatiquement ; transférez-le vers `ktoolbox.toml`.

## Adresses Pawchive

Les valeurs par défaut de v1 ne nécessitent normalement aucune modification :

```dotenv
KTOOLBOX_API__SCHEME=https
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__SCHEME=https
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY` est facultatif et n'est joint qu'aux requêtes du téléchargeur de fichiers. Il n'est jamais envoyé par `PawchiveClient`, qui ne prend pas en charge les sessions de compte.

## Collections et chemins

Utilisez des tableaux JSON pour les ensembles et les listes dans les fichiers dotenv :

```dotenv
KTOOLBOX_JOB__ALLOW_LIST='["*.jpg", "*.png"]'
KTOOLBOX_JOB__BLOCK_LIST='["*.zip", "*.psd"]'
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".zip", ".psd"]'
```

Les chemins relatifs de sortie et de stockage sont résolus depuis le répertoire de travail. Définissez le chemin des pièces jointes sur `./` pour les placer directement dans chaque répertoire de publication :

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## Modèles de nommage

Les modèles de publication et de fichier peuvent utiliser `id`, `user`, `service`, `title`, `added`, `published` et `edited`. La paire vide `{}` dans un modèle de fichier représente le nom de base original ou séquentiel.

```dotenv
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title:.60}
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title:.60}_{}
KTOOLBOX_JOB__POST_STRUCTURE__FILE={id}_{}
```

La précision du format Python, comme `{title:.60}`, est utile pour respecter les limites de longueur du système de fichiers.

## Limiter les téléchargements

Les limites de taille sont exprimées en octets et s'appliquent avant la mise en file d'un fichier. Omettez une variable pour désactiver la borne correspondante.

```dotenv
# Minimum de 1 Kio et maximum de 1 Mio.
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# Récupérer uniquement la couverture, sans pièces jointes.
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` contrôle les producteurs de créateurs simultanés. `KTOOLBOX_JOB__COUNT` contrôle séparément les travailleurs de fichiers partagés par tous les créateurs.
