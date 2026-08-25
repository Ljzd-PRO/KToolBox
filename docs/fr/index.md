# Bienvenue dans KToolBox

KToolBox télécharge les œuvres publiques de Pawchive. La WebUI est la méthode recommandée : les opérations courantes utilisent des formulaires guidés et leur progression reste visible après un changement de page.

!!! warning "Nouvelle version majeure"
    La version 1 manque encore de recul en conditions réelles et certaines fonctions peuvent échouer. Sauvegardez les réglages et téléchargements existants avant une migration et signalez les comportements inattendus.

## Commencer avec la WebUI

1. Installez le paquet WebUI.
2. Créez un répertoire pour votre projet de synchronisation.
3. Démarrez KToolBox dans ce répertoire.

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

Le navigateur s'ouvre automatiquement. Connectez-vous avec le nom `admin` et le mot de passe aléatoire affichés dans le terminal, ajoutez un créateur, puis créez votre première tâche. KToolBox crée `ktoolbox.toml` si nécessaire et utilise `downloads` comme sortie par défaut.

![Vue d'ensemble de la WebUI KToolBox](../assets/webui/40-overview-showcase-desktop-light.png)

## Choisir l'étape suivante

<div class="grid cards" markdown>

-   :material-account-multiple-plus-outline: **Ajouter des créateurs et télécharger**

    Suivez les [parcours du projet](webui/project-workflows.md) pour ajouter des créateurs, rechercher des œuvres, créer des tâches et régler les exclusions.

-   :material-progress-download: **Suivre une tâche**

    Consultez [tâches et mises à jour](webui/tasks.md) pour la progression, les nouvelles tentatives, la pause, l'arrêt, la relance et le nettoyage sûr.

-   :material-calendar-sync-outline: **Exécuter selon un calendrier**

    Créez des plans récurrents avec le [guide de synchronisation automatique](automatic-sync.md).

-   :material-folder-cog-outline: **Choisir les noms et dossiers**

    Réglez la sortie par défaut et une structure lisible avec le [guide du nommage](naming.md).

</div>

## Parcours avancés

Ces pages ne sont pas nécessaires pour un premier démarrage ordinaire.

| Objectif | Guide |
| --- | --- |
| Conserver un compte ou déployer sur plusieurs appareils | [Référence de déploiement WebUI](webui/reference.md) |
| Automatiser depuis un terminal | [Guide CLI](commands/guide.md) et [référence des commandes](commands/reference.md) |
| Examiner tous les réglages | [Guide de configuration](configuration/guide.md) et [référence](configuration/reference.md) |
| Connecter un client IA ou un programme Python | [MCP](mcp.md) et [API Python](api.md) |
| Mettre à niveau un projet ou résoudre un problème | [Guide de migration](migration-v1.md) et [FAQ](faq.md) |

## Valeurs sûres par défaut

La WebUI génère des identifiants, désactive les aperçus de médias sensibles et utilise un dossier de sortie dans le projet. Pour un accès local, liez le service à `127.0.0.1` ; utilisez HTTPS sur un réseau non fiable. KToolBox n'implémente pas les comptes ni les favoris Pawchive.
