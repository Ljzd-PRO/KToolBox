<div align="center">

# KToolBox

Un outil en ligne de commande asynchrone, un panneau de gestion HeroUI et un client Python permettant de télécharger les publications publiques de [Pawchive](https://pawchive.pw/).

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/fr/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

KToolBox v1 utilise Pawchive comme seul serveur pris en charge. Il fournit un accès typé à toutes les opérations publiques du document OpenAPI de Pawchive et exclut volontairement les opérations sur les favoris qui nécessitent l'authentification d'un compte.

## Fonctionnalités

- Télécharger une publication ou synchroniser un nombre quelconque de créateurs avec une seule commande.
- Conserver une liste réutilisable de créateurs, activables ou désactivables, dans le fichier `ktoolbox.toml` propre au projet.
- Exclure les publications qui ne sont pas des œuvres grâce à des règles ordonnées de filtrage des champs, globales ou propres à un créateur.
- Réutiliser un même `PawchiveClient` asynchrone et typé pour plusieurs opérations d'API.
- Reprendre les téléchargements partiels avec les requêtes HTTP Range et ignorer les fichiers existants.
- Limiter la taille des fichiers, choisir les extensions, filtrer les titres et les dates, et contrôler séparément le téléchargement des couvertures et des pièces jointes.
- Personnaliser la structure des répertoires, le nom des publications et des fichiers, la numérotation séquentielle et le regroupement par année et par mois.
- Enregistrer les métadonnées des publications, les index des créateurs, le contenu extrait, ses images et les liens externes correspondants.
- Diffuser les tâches produites simultanément pour plusieurs créateurs vers un pool de téléchargement équitable, avec une progression Rich stable, la vitesse de chaque fichier et le débit global.
- Gérer un projet de synchronisation dans un panneau HeroUI adaptatif disponible en sept langues, avec des tâches persistantes, une progression en temps réel, des formulaires de configuration, des éditeurs de créateurs et de règles d'exclusion, ainsi que des thèmes clair et sombre.
- Utiliser une suite de tests MockTransport entièrement hors ligne, qui bloque tout accès réseau accidentel.

## Prérequis

- Python 3.10 à 3.14
- Windows, macOS ou Linux

## Installation

L'utilisation de `pipx` est recommandée :

```bash
pipx install ktoolbox
```

Dépendances facultatives pour optimiser la boucle d'événements et éditer la configuration dans le terminal :

```bash
# Windows
pipx install "ktoolbox[urwid,winloop]" --force

# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force
```

Installer les composants facultatifs de la WebUI :

```bash
pipx install "ktoolbox[webui]" --force
```

## Démarrage rapide

Afficher l'aide des commandes :

```bash
ktoolbox -h
ktoolbox download -h
```

![Aperçu des commandes KToolBox](docs/assets/cli-overview.png)

Télécharger une publication :

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
```

Synchroniser un créateur en limitant la première exécution à une publication :

```bash
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

Utiliser un décalage, une plage de dates ou des filtres de titre :

```bash
ktoolbox sync fanbox:123 patreon:456 --length 10
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

Enregistrer les créateurs régulièrement synchronisés, puis exécuter `sync` sans cible :

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

Les fichiers existants sont ignorés lors des exécutions suivantes. Un fichier temporaire incomplet reprend son téléchargement si l'hôte prend en charge les plages d'octets.

## WebUI

La WebUI est liée à un seul répertoire de projet contenant `ktoolbox.toml`. Configurez un compte unique, de préférence avec un hachage Argon2id :

```bash
ktoolbox webui hash-password
```

Ajoutez le hachage affiché et le nom du compte au fichier `.env` du projet, puis démarrez le panneau :

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

```bash
ktoolbox webui /path/to/project
```

![Configuration de la WebUI KToolBox](docs/assets/webui/09-configuration-light.png)

Toute l'interface est disponible en chinois simplifié, chinois traditionnel, anglais, japonais, coréen, français et russe. La première visite suit la langue du navigateur ; un choix manuel est mémorisé et actualise ensemble les dates, les nombres, le tri, les descriptions de configuration, la validation et les erreurs du serveur.

Les lignes de tâches conservent des titres de publication et des noms de créateur lisibles dans un instantané de présentation hors ligne. Les dispositions pour ordinateur et mobile donnent directement accès aux détails, au cycle de vie, à la modification, au classement et à la suppression. Les interrupteurs sont gris lorsqu'ils sont désactivés et bleus lorsqu'ils sont activés ; les cases à cocher n'affichent un indicateur que lorsqu'elles sont sélectionnées.

Une tâche en échec conserve un rapport expurgé par étape avec le créateur ou fichier concerné, la possibilité de réessayer, les chemins de champs sûrs et l'action recommandée. L'interface mobile compacte utilise une barre de 64px et un espacement de 12px, place l'apparence dans un petit Popover et replie le catalogue MCP par catégorie.

Après la connexion, une seule connexion SSE synchronise automatiquement les tâches, créateurs, règles d'exclusion, configurations, jetons MCP et répertoires distants ouverts entre les onglets. En cas de coupure, seules les données locales sont actualisées toutes les 10 secondes, sans interroger les recherches Pawchive ni les détails d'œuvres ; les brouillons non enregistrés restent protégés des mises à jour externes.

L'écoute par défaut sur `0.0.0.0:8789` est pratique sur un réseau local de confiance, mais HTTP ne protège ni les identifiants ni les données du projet en transit. Sur un réseau non fiable, liez le service à `127.0.0.1` ou placez-le derrière un proxy inverse HTTPS. Il n'existe aucun compte par défaut et le démarrage échoue tant que des identifiants valides ne sont pas configurés. Consultez le [guide de la WebUI](https://ktoolbox.readthedocs.io/latest/fr/webui/) pour le cycle de vie des tâches, la sécurité et le déploiement.

## Configuration

KToolBox lit d'abord `.env`, puis `prod.env`, depuis le répertoire de travail actuel. Les champs imbriqués utilisent `__` :

```dotenv
# Valeurs Pawchive par défaut ; aucune modification n'est généralement nécessaire.
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data

# Contrôle des téléchargements.
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576
```

Si `KTOOLBOX_DOWNLOADER__SESSION_KEY` est défini, il n'est envoyé que lors du téléchargement des fichiers. Le client API n'envoie jamais la session d'un compte.

Le fichier `.env` contrôle l'exécution et les transferts. Le fichier de projet `ktoolbox.toml` contient la liste des créateurs et les règles d'exclusion :

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[blockers]]
id = "skip-progress-updates"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["état d'avancement"] }] } }
```

Générer une référence de configuration, valider le fichier du projet ou lancer l'éditeur de terminal facultatif :

```bash
ktoolbox config example
ktoolbox config validate
ktoolbox config edit
```

Consultez le [guide de configuration](https://ktoolbox.readthedocs.io/latest/fr/configuration/guide/) et le fichier [`example.env`](example.env).

## API Python

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        posts = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(posts))


asyncio.run(main())
```

Les appels réussis renvoient des modèles Pydantic v2. Les échecs de transport, d'état HTTP, d'authentification, de ressource introuvable, de conflit et de validation de la réponse utilisent des classes d'exception distinctes. Consultez la [documentation de l'API](https://ktoolbox.readthedocs.io/latest/fr/api/).

## Migration depuis v0

La version 1 supprime la couche de compatibilité Kemono/Coomer ainsi que les anciennes interfaces `BaseAPI`, les fonctions `get_*` au niveau du module, `APIRet` et les réponses enveloppées. Fire a été remplacé par Cyclopts : utilisez `download`, `sync`, `creator`, `post` et `config`. Les anciens alias masqués restent temporairement disponibles avec un avertissement d'obsolescence. Déplacez `KTOOLBOX_API__SESSION_KEY` vers `KTOOLBOX_DOWNLOADER__SESSION_KEY` et consultez le [guide de migration vers v1](https://ktoolbox.readthedocs.io/latest/fr/migration-v1/).

L'ancien fichier `kemono_openapi.json` reste dans le dépôt à titre de référence uniquement ; il ne constitue pas un contrat d'exécution pris en charge.

## Développement

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run ruff check k_generator ktoolbox/api ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py tests
poetry run mypy --strict ktoolbox/api/client.py ktoolbox/api/errors.py ktoolbox/api/parameters.py ktoolbox/api/utils.py ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py
poetry run mkdocs build --strict
cd webui && npm ci && npm run typecheck && npm run lint && npm run test && npm run build && npm run test:e2e
```

Les tests par défaut sont hermétiques et ne doivent contacter ni Pawchive ni aucun autre service distant.

## Licence

KToolBox est distribué sous la [licence BSD à 3 clauses](LICENSE).
