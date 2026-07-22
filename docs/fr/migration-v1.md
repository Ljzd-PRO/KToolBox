# Migration vers v1

KToolBox v1 introduit des changements incompatibles du serveur et de l'API de la bibliothèque.

## Avant la mise à niveau

1. Sauvegardez votre fichier `.env` ou `prod.env`.
2. Terminez ou annulez tout téléchargement v0 en cours.
3. Testez la synchronisation limitée d'un créateur avec `--length=1` avant une synchronisation complète.

## Changements nécessaires

| Comportement v0 | Comportement v1 |
| --- | --- |
| Serveurs Kemono/Coomer | Pawchive uniquement |
| Python 3.8+ | Python 3.10-3.14 |
| `KTOOLBOX_API__SESSION_KEY` | `KTOOLBOX_DOWNLOADER__SESSION_KEY` |
| Serveurs d'API et de fichiers mélangés dans la configuration de l'API | Serveurs d'API et statique dans `api` ; serveur de fichiers dans `downloader` |
| Requête de détail d'une révision | Obtenir la liste des révisions, puis sélectionner par `revision_id` |
| Réponses enveloppées comme `.data.post` | Modèles typés `Post`, `Revision` et autres modèles Pydantic directement |
| Interface de commandes Python Fire | Arbre de commandes Cyclopts avec options à traits d'union et codes de sortie explicites |
| Un créateur par synchronisation | Nombre quelconque de cibles ou liste activée du projet |
| Uniquement `keywords_exclude` global | Règles `field-match` ordonnées, globales et propres à un créateur |

Les nouvelles valeurs par défaut sont :

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

## Commandes CLI

Des alias masqués permettent temporairement aux automatisations existantes de continuer à fonctionner, mais chaque appel affiche un avertissement d'obsolescence :

| Commande v0 | Commande v1 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

Les options s'affichent sous la forme `--creator-id`, sans les traits de soulignement du style Python. Les anciennes graphies avec traits de soulignement restent acceptées par les alias de compatibilité. L'aide s'affiche directement et ne nécessite plus de quitter un afficheur paginé.

Les échecs de la CLI utilisent désormais l'état du processus : `0` pour le succès, `1` pour un échec distant, de créateur ou de téléchargement, `2` pour un échec d'argument ou de configuration et `130` pour une interruption. Les données JSON et les tableaux utilisent stdout ; la progression et les journaux utilisent stderr.

## Liste des créateurs et règles d'exclusion

Créez `ktoolbox.toml` uniquement si vous avez besoin d'une liste réutilisable ou de règles d'exclusion structurées. L'absence du fichier représente un projet vide valide.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true
```

Déplacez les valeurs non vides de `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` vers une condition de titre `field-match` globale. L'ancien réglage reste actif comme règle implicite et affiche un avertissement, mais KToolBox ne réécrit pas les fichiers locaux. Consultez le [guide de configuration](configuration/guide.md#post-blockers).

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` vaut `4` par défaut et limite les producteurs de créateurs. Le réglage existant `KTOOLBOX_JOB__COUNT` continue de limiter les travailleurs de fichiers.

## WebUI facultative

La version 1 ajoute un nouveau panneau HeroUI ; elle ne migre ni ne réutilise l'ancienne branche expérimentale `webui`. Installez `ktoolbox[webui]`, sélectionnez un répertoire de projet et configurez un nouveau compte unique. Un fichier `ktoolbox.toml` absent est créé automatiquement après un avertissement ; aucun identifiant par défaut n'est créé.

```bash
ktoolbox webui hash-password
ktoolbox webui /path/to/project --host 127.0.0.1
```

`.env` et `prod.env` sont maintenant des fichiers locaux ignorés plutôt que des exemples suivis par le contrôle de version. Conservez-y les identifiants et les sessions du téléchargeur, utilisez `example.env` comme modèle public et vérifiez tout ancien fichier dotenv suivi avant la mise à niveau. La WebUI crée `.ktoolbox/webui.sqlite3` et un verrou de projet ; aucun des deux ne modifie les formats de sortie des téléchargements de la CLI.

Consultez le [guide de la WebUI](webui.md) pour les risques du déploiement HTTP et le fonctionnement des tâches persistantes.

## API de la bibliothèque

Les anciens `BaseAPI`, invocateurs de classe, fonctions `get_*` au niveau du module, `APIRet` et enveloppes de réponse Kemono ont été supprimés sans alias de compatibilité. Utilisez une instance du client asynchrone :

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

Les appels réussis renvoient des modèles Pydantic v2. Les échecs déclenchent des sous-classes typées de `PawchiveError` ; consultez la [documentation de l'API](api.md).
