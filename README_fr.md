<div align="center">

# KToolBox

Une WebUI simple, une CLI et un client Python pour télécharger les œuvres publiques de [Pawchive](https://pawchive.pw/).

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/fr/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> KToolBox v1 est une nouvelle version majeure qui manque encore de recul en conditions réelles. Certaines fonctions peuvent échouer. N'hésitez pas à signaler tout problème.
>
> Kemono n'étant plus disponible, KToolBox utilise désormais le miroir Pawchive par défaut.

## Commencer avec la WebUI

La WebUI est la méthode recommandée. Elle gère les téléchargements, la synchronisation des créateurs, les programmes automatiques, le nommage, les filtres, la progression et la configuration sans exiger d'apprendre d'abord des commandes ou des fichiers de réglages.

1. Installez KToolBox avec la WebUI :

    ```bash
    pipx install "ktoolbox[webui]"
    ```

2. Créez un répertoire de projet et démarrez-le :

    ```bash
    mkdir ktoolbox-project
    cd ktoolbox-project
    ktoolbox webui .
    ```

3. Le navigateur s'ouvre automatiquement. Connectez-vous avec le nom et le mot de passe aléatoire affichés dans le terminal.
4. Ajoutez vos créateurs dans **Créateurs**, puis créez une synchronisation ou un téléchargement dans **Tâches**.

KToolBox crée `ktoolbox.toml` s'il manque et télécharge par défaut dans le répertoire `downloads` du projet.

![Vue d'ensemble de la WebUI KToolBox](docs/assets/webui/40-overview-showcase-desktop-light.png)

Poursuivez avec le court [guide WebUI](https://ktoolbox.readthedocs.io/latest/fr/webui/) ou choisissez une action depuis [l'accueil de la documentation](https://ktoolbox.readthedocs.io/latest/fr/).

## Ce que contient la WebUI

- Téléchargement d'une œuvre et synchronisation parallèle de plusieurs créateurs.
- Liste de créateurs, règles d'exclusion, formats de nommage et plusieurs programmes automatiques.
- Historique persistant, progression en direct, débit total, nouvelles tentatives, pause, arrêt, relance et nettoyage sûr.
- Configuration du projet avec des libellés lisibles et un sélecteur de chemin seulement lorsque nécessaire.
- Sept langues, mise en page adaptative, thèmes clair et sombre et aperçu NSFW facultatif.
- Service MCP intégré pour Codex, Claude, Cursor, VS Code et les clients compatibles.

## Réglage facultatif

Les identifiants générés suffisent pour un premier essai. Pour conserver un mot de passe, créez un hachage et ajoutez-le au fichier `.env` du projet :

```bash
ktoolbox webui hash-password
```

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

Pour un accès sur la même machine, ajoutez `--host 127.0.0.1`. Le serveur intégré utilise HTTP : pour un accès distant, choisissez un réseau fiable ou un proxy inverse HTTPS.

## Usage avancé

La CLI reste disponible pour les scripts et le terminal :

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
ktoolbox sync fanbox:123 patreon:456 --length 10
```

Consultez le [guide CLI](https://ktoolbox.readthedocs.io/latest/fr/commands/guide/) pour les commandes, le [guide MCP](https://ktoolbox.readthedocs.io/latest/fr/mcp/) pour les clients IA et l'[API Python](https://ktoolbox.readthedocs.io/latest/fr/api/) pour les intégrations.

## Mise à niveau depuis v0

Sauvegardez `.env`, `prod.env` et les téléchargements existants. La WebUI détecte les anciens réglages de nommage et guide la conversion de la configuration et des répertoires. Lisez le [guide de migration v1](https://ktoolbox.readthedocs.io/latest/fr/migration-v1/) avant de modifier un projet existant ; consultez le [dépannage](https://ktoolbox.readthedocs.io/latest/fr/faq/) en cas d'échec.

## Développement

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run mkdocs build --strict
cd webui && npm ci && npm run test && npm run build
```

Les tests par défaut sont hors ligne et ne doivent contacter ni Pawchive ni aucun service distant.

## Licence

KToolBox est distribué sous [BSD 3-Clause License](LICENSE).
