# KToolBox

KToolBox est un outil de téléchargement asynchrone en ligne de commande, un panneau de projet HeroUI et un client Python typé pour les données publiques de [Pawchive](https://pawchive.pw/). La version 1 prend exclusivement en charge Pawchive et nécessite Python 3.10 à 3.14.

!!! warning "La v1 est une nouvelle version majeure"
    Cette série n'a pas encore été suffisamment validée en usage réel. Commencez par un téléchargement limité, conservez une sauvegarde de la configuration existante et signalez tout comportement inattendu. Kemono n'étant plus disponible, KToolBox utilise par défaut le miroir Pawchive.

## Choisir votre parcours

<div class="grid cards" markdown>

-   :material-console-line: **Commencer en ligne de commande**

    Installez KToolBox, exécutez un téléchargement limité, puis poursuivez avec le [guide des commandes](commands/guide.md).

-   :material-view-dashboard-outline: **Gérer un projet dans le navigateur**

    Installez le panneau facultatif et suivez le [guide de la WebUI](webui.md) pour la connexion, la sécurité, les tâches et les paramètres du projet.

-   :material-update: **Mettre à niveau depuis la v0**

    Sauvegardez les anciens fichiers dotenv et suivez la [migration vers v1](migration-v1.md) avant de modifier les téléchargements existants.

-   :material-calendar-sync: **Maintenir les créateurs à jour**

    Constituez d'abord une liste, puis utilisez la [synchronisation automatique](automatic-sync.md) pour les vérifications périodiques.

</div>

## Fonctionnalités

- Télécharge une publication ou synchronise en parallèle une liste de créateurs.
- Applique des règles d'exclusion ordonnées, globales ou propres à un créateur, avant de créer les tâches de téléchargement.
- Reprend les fichiers partiels et ignore ceux qui existent déjà.
- Filtre par date, titre, motif de nom de fichier et taille.
- Contrôle séparément les couvertures, pièces jointes, images du contenu, métadonnées et liens externes.
- Fournit une WebUI persistante en sept langues pour configurer le projet, modifier la liste des créateurs et les règles d'exclusion, interroger Pawchive et contrôler le cycle de vie des tâches.
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

Sans `--output`, les téléchargements utilisent l'emplacement par défaut du projet : `downloads` sous le répertoire du projet, sauf modification.

## Carte de la documentation

| Objectif | À lire |
| --- | --- |
| Apprendre les commandes courantes | [Guide des commandes](commands/guide.md) et [référence des commandes](commands/reference.md) |
| Exécuter le panneau dans le navigateur | [Guide de la WebUI](webui.md) |
| Planifier des vérifications périodiques | [Synchronisation automatique](automatic-sync.md) |
| Contrôler les répertoires et noms | [Format de nommage](naming.md) |
| Comprendre tous les paramètres | [Guide de configuration](configuration/guide.md) et [référence de configuration](configuration/reference.md) |
| Connecter une autre application | [MCP](mcp.md) ou [API Python](api.md) |
| Mettre à niveau ou résoudre un problème | [Migration vers v1](migration-v1.md) et [FAQ](faq.md) |
