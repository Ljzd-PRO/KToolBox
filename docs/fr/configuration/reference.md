# Référence de configuration

Les noms d'environnement commencent par `KTOOLBOX_` et relient les champs imbriqués du modèle avec `__`. Les types indiqués comme `path`, `set` ou `list` sont analysés par Pydantic ; utilisez des tableaux JSON pour les collections dans dotenv.

## Racine

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `ssl_verify` | booléen | `True` | Vérifier les certificats TLS des requêtes d'API et de téléchargement. |
| `json_dump_indent` | entier | `4` | Indentation de la sortie JSON. |
| `use_uvloop` | booléen | `True` | Utiliser uvloop sous Unix ou winloop sous Windows lorsqu'il est installé. |

## `api`

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | Schéma de l'URL de l'API. |
| `netloc` | chaîne | `pawchive.pw` | Serveur de l'API. |
| `statics_netloc` | chaîne | `pawchive.pw` | Serveur des ressources statiques des créateurs. |
| `path` | chaîne | `/api/v1` | Chemin racine de l'API. |
| `timeout` | nombre réel | `5.0` | Délai de chaque requête en secondes. |
| `retry_times` | entier | `3` | Tentatives supplémentaires pour les échecs de transport, `429` et `5xx`. |
| `retry_interval` | nombre réel | `2.0` | Délai entre les tentatives d'API en secondes. |

Le groupe API ne contient volontairement aucune clé de session.

## `downloader`

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | Schéma de l'URL des fichiers. |
| `files_netloc` | chaîne | `file.pawchive.pw` | Serveur de fichiers Pawchive. |
| `file_path_prefix` | chaîne | `/data` | Préfixe ajouté aux chemins de fichiers de l'API. |
| `session_key` | chaîne | vide | Cookie facultatif envoyé uniquement aux requêtes de fichiers. |
| `timeout` | nombre réel | `30.0` | Délai d'une requête de fichier en secondes. |
| `encoding` | chaîne | `utf-8` | Encodage des noms et du texte extrait. |
| `buffer_size` | entier | `20480` | Taille du tampon d'E/S en octets. |
| `chunk_size` | entier | `1024` | Taille d'un bloc de flux en octets. |
| `temp_suffix` | chaîne | `tmp` | Suffixe des téléchargements incomplets. |
| `retry_times` | entier | `10` | Tentatives supplémentaires de téléchargement. |
| `retry_stop_never` | booléen | `False` | Réessayer indéfiniment et ignorer `retry_times`. |
| `retry_interval` | nombre réel | `3.0` | Délai entre les tentatives en secondes. |
| `tps_limit` | nombre réel | `5.0` | Nombre maximal de nouvelles connexions par seconde. |
| `use_bucket` | booléen | `False` | Activer le stockage local par liens physiques adressé par contenu. |
| `bucket_path` | chemin | `.ktoolbox/bucket_storage` | Répertoire du stockage local. |
| `reverse_proxy` | chaîne | `{}` | Modèle d'URL de téléchargement ; `{}` est remplacé par l'URL source. |
| `keep_metadata` | booléen | `True` | Conserver les métadonnées distantes de modification lorsqu'elles existent. |

Le mode de stockage se désactive si le système de fichiers cible ne peut pas créer de liens physiques.

## `job.post_structure`

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `attachments` | chemin | `attachments` | Sous-répertoire des pièces jointes. Utilisez `./` pour la racine de la publication. |
| `content` | chemin | `content.txt` | Fichier du contenu extrait. |
| `external_links` | chemin | `external_links.txt` | Fichier des liens externes extraits. |
| `file` | chaîne | `{id}_{}` | Modèle de nom de la couverture. |
| `revisions` | chemin | `revisions` | Sous-répertoire des révisions. |

## `job`

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `count` | entier | `4` | Travailleurs de téléchargement simultanés. |
| `creator_concurrency` | entier | `4` | Producteurs de créateurs simultanés alimentant les travailleurs partagés. |
| `include_revisions` | booléen | `False` | Inclure toutes les révisions connues de la publication actuelle. |
| `post_dirname_format` | chaîne | `{title}` | Modèle de répertoire par publication. |
| `mix_posts` | booléen | `False` | Stocker ensemble tous les fichiers du créateur sans répertoires de publication. |
| `sequential_filename` | booléen | `False` | Renommer les pièces jointes dans l'ordre numérique. |
| `sequential_filename_excludes` | ensemble | vide | Extensions qui conservent leur nom d'origine. |
| `filename_format` | chaîne | `{}` | Modèle de nom des pièces jointes. |
| `allow_list` | ensemble | vide | Motifs de noms Unix shell à inclure. |
| `block_list` | ensemble | vide | Motifs de noms Unix shell à exclure. |
| `extract_content` | booléen | `False` | Enregistrer séparément le texte de la publication. |
| `extract_content_images` | booléen | `False` | Télécharger les images référencées dans le contenu. |
| `extract_external_links` | booléen | `False` | Enregistrer les liens externes correspondants du contenu. |
| `external_link_patterns` | liste | intégré | Expressions régulières servant à extraire les liens externes. |
| `group_by_year` | booléen | `False` | Regrouper les répertoires par année de publication. |
| `group_by_month` | booléen | `False` | Regrouper par mois ; nécessite le regroupement par année. |
| `year_dirname_format` | chaîne | `{year}` | Modèle de répertoire d'année. |
| `month_dirname_format` | chaîne | `{year}-{month:02d}` | Modèle de répertoire de mois. |
| `keywords` | ensemble | vide | Termes de titre à inclure, sans distinction de casse. |
| `keywords_exclude` | ensemble | vide | Anciennes exclusions de titre, converties en règle globale implicite. |
| `download_file` | booléen | `True` | Télécharger le fichier principal, généralement la couverture. |
| `download_attachments` | booléen | `True` | Télécharger les pièces jointes. |
| `min_file_size` | entier / omis | omis | Ignorer les fichiers plus petits que ce nombre d'octets. |
| `max_file_size` | entier / omis | omis | Ignorer les fichiers plus grands que ce nombre d'octets. |

Les modèles de nom acceptent `id`, `user`, `service`, `title`, `added`, `published` et `edited`. Les modèles d'année et de mois acceptent `year` et `month`.

## Fichier de projet `ktoolbox.toml`

Le document de projet est distinct de la configuration d'environnement. Son chemin est résolu depuis `--config`, puis `KTOOLBOX_PROJECT_CONFIG`, puis `./ktoolbox.toml`.

### Racine

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `schema_version` | littéral `1` | `1` | Version du schéma du projet ; les autres valeurs sont refusées. |
| `creators` | tableau de tables | vide | Liste enregistrée des créateurs. |
| `blockers` | tableau de tables | vide | Spécifications ordonnées des règles. |

### Entrée d'un créateur

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `service` | chaîne non vide | requis | Service Pawchive. |
| `creator_id` | chaîne non vide | requis | ID du créateur Pawchive. |
| `alias` | chaîne / omis | omis | Cible CLI unique ; `:` est interdit. |
| `enabled` | booléen | `True` | Inclus par `sync` sans cible. |

### Entrée d'une règle

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `id` | identifiant | requis | ID unique composé de lettres, chiffres, `.`, `_` ou `-`. |
| `type` | chaîne | `field-match` | Mise en œuvre enregistrée. Les types inconnus sont refusés. |
| `enabled` | booléen | `True` | Indique si cette règle participe. |
| `scope.mode` | `global` / `creators` | `global` | Appliquer globalement ou aux identités choisies. |
| `scope.creators` | liste de `service:id` | vide | Requise et non vide pour la portée par créateur ; interdite pour la portée globale. |
| `options.rule` | groupe de conditions | requis pour `field-match` | Règle récursive racine. |

Les groupes utilisent `kind = "group"`, `mode = "any"` ou `"all"`, une liste `conditions` non vide et un `negate` facultatif. Les conditions de champ utilisent `kind = "field"`, un `field` sûr à points, l'un de `contains`, `equals`, `regex` ou `exists`, et les options `case_sensitive`, `negate` ou `expected`. Les opérateurs autres que `exists` exigent une liste `values` non vide ; `exists` interdit `values`.

## `webui`

Ces réglages ne sont nécessaires que lorsque `ktoolbox[webui]` est installé. Il n'existe aucun identifiant par défaut et le serveur refuse de démarrer sans nom d'utilisateur et l'une des formes de mot de passe.

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `host` | chaîne | `0.0.0.0` | Interface d'écoute HTTP. Préférez `127.0.0.1` hors d'un réseau local fiable. |
| `port` | entier | `8789` | Port d'écoute HTTP, de 1 à 65535. |
| `open_browser` | booléen | `True` | Ouvrir l'URL locale du panneau après le démarrage. |
| `username` | chaîne | vide | Nom d'utilisateur requis du compte unique. |
| `password_hash` | chaîne secrète | vide | Hachage Argon2id recommandé du mot de passe. |
| `password` | chaîne secrète | vide | Solution de repli en clair, ignorée si `password_hash` est défini. |
| `max_active_tasks` | entier | `2` | Tâches de premier niveau simultanées, de 1 à 16. |
| `session_idle_hours` | entier | `24` | Expiration de la session depuis la dernière utilisation. |
| `session_absolute_hours` | entier | `168` | Durée de vie maximale depuis la connexion. |

Tous les noms utilisent le préfixe habituel, par exemple `KTOOLBOX_WEBUI__PASSWORD_HASH`. Générez un hachage avec `ktoolbox webui hash-password` ; placez-le entre guillemets dans dotenv, car les hachages Argon2 contiennent des caractères `$`. `--host`, `--port` et `--no-open` remplacent les réglages correspondants pour un démarrage.

## `logger`

| Champ | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `path` | chemin / omis | omis | Chemin du journal ; l'omettre désactive la journalisation dans un fichier. |
| `level` | chaîne / entier | `DEBUG` | Niveau minimal des journaux. |
| `rotation` | chaîne / entier / temps | `1 week` | Condition de rotation Loguru. |
