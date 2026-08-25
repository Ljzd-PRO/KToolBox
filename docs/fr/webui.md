# WebUI

La WebUI est la méthode recommandée pour utiliser KToolBox. Elle rassemble dans le navigateur les réglages, tâches, progressions et historiques d'un projet de synchronisation.

## Premier démarrage

Installez le paquet WebUI, créez un répertoire de projet et démarrez KToolBox :

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

Le navigateur s'ouvre automatiquement. Connectez-vous avec le nom `admin` et le mot de passe aléatoire affichés dans le terminal. Si `ktoolbox.toml` manque, KToolBox le crée ; les nouvelles tâches utilisent par défaut le répertoire `downloads` du projet.

![Vue d'ensemble de la WebUI KToolBox](../assets/webui/40-overview-showcase-desktop-light.png)

## Première synchronisation

1. Ouvrez **Créateurs**, puis sélectionnez **Ajouter un créateur**.
2. Collez une URL de créateur Pawchive, ou saisissez sa plateforme et son ID.
3. Ouvrez **Tâches**, sélectionnez **Créer une tâche**, puis **Synchroniser les créateurs**.
4. Limitez le premier essai pendant la vérification d'un nouveau créateur et du nommage.
5. Ouvrez la tâche pour suivre les téléchargements, le débit, les nouvelles tentatives et les messages utiles.

Les fichiers terminés sont conservés, les fichiers temporaires compatibles peuvent reprendre et l'échec d'un créateur ne supprime pas les téléchargements réussis de la même tâche.

## Poursuivre selon votre objectif

<div class="grid cards" markdown>

-   :material-folder-account-outline: **Créateurs, œuvres, exclusions et nommage**

    Utilisez les [parcours du projet](webui/project-workflows.md) pour la gestion quotidienne.

-   :material-progress-download: **Progression et contrôle des tâches**

    Consultez [tâches et mises à jour](webui/tasks.md) pour la pause, l'arrêt, la relance, les diagnostics et le nettoyage sûr.

-   :material-server-security: **Comptes et déploiement**

    N'utilisez la [référence de déploiement](webui/reference.md) que pour des identifiants stables, l'accès distant, les sauvegardes ou les détails de sécurité.

-   :material-update: **Projet v0 existant**

    Lisez le [guide de migration](migration-v1.md) avant de convertir d'anciens réglages ou téléchargements.

</div>

## Compte stable facultatif

Les identifiants générés suffisent pour le premier démarrage. Pour conserver le même compte après un redémarrage, créez un hachage de mot de passe :

```bash
ktoolbox webui hash-password
```

Ajoutez le résultat au fichier `.env` du projet :

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

## Accès sûr

Le serveur intégré utilise HTTP. Pour un usage sur le même ordinateur, liez-le à `127.0.0.1` :

```bash
ktoolbox webui . --host 127.0.0.1
```

Pour un accès distant, utilisez un réseau fiable ou un proxy inverse HTTPS. Toute personne connectée peut voir les chemins, réglages et journaux du projet : ne donnez pas cet accès à un utilisateur non fiable. Un seul processus WebUI peut gérer un projet à la fois.
