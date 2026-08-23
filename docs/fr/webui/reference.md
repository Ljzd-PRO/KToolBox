# Référence de déploiement WebUI

Après la première configuration sécurisée, utilisez cette référence pour exploiter et sauvegarder une instance WebUI.

## À propos

La page À propos regroupe version, licence, environnement et liens officiels. Les URL, adresses IP et adresses d'écoute utilisent un style de code en ligne.

![Page À propos mobile sombre](../../assets/webui/32-about-mobile-dark.png)

## Référence de l'environnement WebUI

| Variable | Valeur par défaut | Signification |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | Interface d'écoute. |
| `KTOOLBOX_WEBUI__PORT` | `8789` | Port d'écoute, de 1 à 65535. |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | Ouvrir l'URL locale après le démarrage. |
| `KTOOLBOX_WEBUI__USERNAME` | vide → `admin` au démarrage | Nom facultatif du compte unique. |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | vide | Hachage Argon2id stable recommandé. |
| `KTOOLBOX_WEBUI__PASSWORD` | vide → aléatoire à chaque démarrage | Solution en clair ; ignorée si un hachage existe. |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | Tâches principales simultanées, de 1 à 16. |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | Durée de session depuis la dernière utilisation. |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | Durée maximale depuis la connexion. |

Sauvegardez ensemble `ktoolbox.toml`, les fichiers dotenv locaux et `.ktoolbox/webui.sqlite3` lorsque l'historique importe. Ne copiez pas la base pendant l'exécution de la WebUI.

## Vérification multilingue dans le navigateur

Les sept catalogues sont testés réellement sur ordinateur et mobile, en thèmes clair et sombre. Voici deux états représentatifs validés ; le contenu utilisateur et les chemins du système de fichiers conservent leur texte d'origine.

![Configuration française sur mobile](../../assets/webui/24-configuration-mobile-fr.png)

![Sélecteur de chemin distant russe sur mobile](../../assets/webui/25-path-picker-mobile-ru.png)

## Guides WebUI associés

- [Installation et sécurité](../webui.md)
- [Parcours du projet](project-workflows.md)
- [Tâches et mises à jour](tasks.md)
- [Référence de déploiement](reference.md)
