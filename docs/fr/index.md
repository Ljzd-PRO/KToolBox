# KToolBox

KToolBox est un outil de téléchargement asynchrone en ligne de commande, un panneau de projet HeroUI et un client Python typé pour les données publiques de [Pawchive](https://pawchive.pw/). La version 1 prend exclusivement en charge Pawchive et nécessite Python 3.10 à 3.14.

## Fonctionnalités

- Télécharge une publication ou synchronise en parallèle une liste de créateurs.
- Applique des règles d'exclusion ordonnées, globales ou propres à un créateur, avant de créer les tâches de téléchargement.
- Reprend les fichiers partiels et ignore ceux qui existent déjà.
- Filtre par date, titre, motif de nom de fichier et taille.
- Contrôle séparément les couvertures, pièces jointes, images du contenu, métadonnées et liens externes.
- Fournit une WebUI persistante en anglais et en chinois simplifié pour configurer le projet, modifier la liste des créateurs et les règles d'exclusion, interroger Pawchive et contrôler le cycle de vie des tâches.
- Expose les 14 opérations publiques d'OpenAPI Pawchive par l'intermédiaire de modèles Pydantic validés.

Les opérations sur les favoris nécessitant l'authentification d'un compte ne sont volontairement pas mises en œuvre. Une clé de session du téléchargeur, lorsqu'elle est configurée, n'est envoyée qu'au serveur de fichiers.

## Installation

`pipx` permet d'isoler l'application :

```bash
pipx install ktoolbox
```

Installer l'éditeur de terminal et l'optimisation de la boucle d'événements facultatifs :

```bash
# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force

# Windows
pipx install "ktoolbox[urwid,winloop]" --force
```

Installer séparément le panneau pour navigateur si nécessaire :

```bash
pipx install "ktoolbox[webui]" --force
```

## Démarrage rapide

```bash
# Examiner les commandes et leurs options.
ktoolbox -h
ktoolbox download -h

# Télécharger une publication.
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

# Commencer par une publication avant de synchroniser une plage plus large.
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

![Aperçu des commandes KToolBox](../assets/cli-overview.png)

Enregistrer plusieurs créateurs et synchroniser toutes les entrées activées :

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

Les fichiers existants sont ignorés lors des exécutions suivantes. Un fichier incomplet avec le suffixe temporaire configuré reprend si le serveur prend en charge les plages d'octets.

## Pour continuer

- [Guide des commandes](commands/guide.md)
- [Guide de la WebUI](webui.md)
- [Guide de configuration](configuration/guide.md)
- [API Python](api.md)
- [Migration vers v1](migration-v1.md)
- [FAQ](faq.md)
