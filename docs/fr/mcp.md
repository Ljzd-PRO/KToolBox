# MCP

KToolBox démarre un serveur MCP Streamable HTTP dans le même processus et sur le même port que la WebUI. Il expose une sélection d'outils pour le projet, les tâches, les créateurs, les règles d'exclusion, la recherche Pawchive, le nommage, la synchronisation automatique et la configuration sûre. Les sessions du navigateur et les clients MCP utilisent des identifiants distincts.

| Service | Adresse par défaut |
| --- | --- |
| WebUI | `http://127.0.0.1:8789/` |
| MCP | `http://127.0.0.1:8789/mcp` |
| OpenAPI REST WebUI | `http://127.0.0.1:8789/api/v1/openapi.yaml` |

Le téléchargement OpenAPI exige une session WebUI authentifiée. Le contrat canonique du dépôt est `webui/openapi.yaml`.

## Créer un jeton d'accès

1. Démarrez la WebUI et connectez-vous.
2. Ouvrez **MCP** dans la barre latérale.
3. Sélectionnez **Nouveau jeton d'accès**.
4. Saisissez un nom descriptif et confirmez le mot de passe WebUI actuel.
5. Choisissez la lecture seule ou la gestion, puis 7, 30, 90, 365 jours ou aucune expiration.
6. Enregistrez immédiatement la valeur `ktmcp_...` affichée. Elle ne sera visible qu'une seule fois.

KToolBox ne conserve que le hachage du jeton. La page MCP affiche les dates de création, d'expiration et de dernière utilisation et permet une révocation immédiate. Un jeton sans expiration reste valide jusqu'à sa révocation et ne convient que si son cycle de vie est activement géré.

## Connecter Codex

Stockez le jeton hors du dépôt :

```shell
export KTOOLBOX_MCP_TOKEN="ktmcp_..."
```

Ajoutez le serveur à la configuration Codex :

```toml
[mcp_servers.ktoolbox]
url = "http://127.0.0.1:8789/mcp"
bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"
```

La page MCP génère aussi des configurations pour les clients HTTP génériques, Claude, Cursor, VS Code et Codex. Les modèles utilisent une variable d'environnement ou une saisie protégée au lieu d'intégrer le jeton.

## Autorisations et limites

- Un jeton en lecture seule peut consulter le résumé du projet, les tâches, les créateurs, les règles d'exclusion, la synchronisation automatique, l'historique de nommage, la configuration expurgée et une vue bornée des fichiers du projet.
- Un jeton de gestion peut aussi effectuer les modifications de tâches, créateurs, règles, synchronisation automatique et configuration structurée sûre explicitement listées.
- Connexion, déconnexion, sessions du navigateur, édition dotenv/TOML brute, secrets, accès arbitraire au système de fichiers hôte, suppression des sorties et journaux ou contenus non bornés ne sont pas exposés.
- Les recherches et consultations Pawchive sont des opérations ouvertes susceptibles de contacter le service configuré.
- Les listes, journaux, événements, contenus d'œuvres et fichiers sont bornés ou paginés.

La page **MCP** constitue le catalogue de référence des outils de la version en cours d'exécution.

## Sécurité

Les jetons Bearer donnent un accès direct au projet. Ne les placez jamais dans Git, l'historique du shell, les captures d'écran, les journaux ou les conversations. Utilisez un jeton distinct par client et révoquez les identifiants inutilisés.

Le serveur intégré utilise HTTP. Sur le même ordinateur, liez la WebUI à `127.0.0.1`. Pour un accès distant, terminez HTTPS sur un proxy inverse fiable et limitez l'accès réseau.

## Limites des API

- L'OpenAPI Pawchive décrit le service public en amont.
- L'[API Python](api.md) fournit le client typé `PawchiveClient`.
- `webui/openapi.yaml` décrit l'API REST authentifiée de la WebUI KToolBox.
- `/mcp` expose les outils MCP sélectionnés à partir de ce contrat WebUI.

Le contrat REST WebUI et MCP ne remplacent pas l'API Pawchive.
