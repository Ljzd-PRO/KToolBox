# API Python

`PawchiveClient` est un client asynchrone qui doit être instancié. Réutilisez une même instance pour les requêtes liées et fermez-la avec un gestionnaire de contexte asynchrone :

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

Les opérations JSON réussies renvoient des modèles Pydantic v2 générés. `get_app_version()` renvoie du texte brut et `flag_post()` renvoie `None` après une réponse `201` réussie.

## Opérations publiques

| Méthode du client | Requête | Résultat |
| --- | --- | --- |
| `list_creators()` | `GET /creators` | `list[CreatorSummary]` |
| `list_recent_posts(query=None, offset=None)` | `GET /posts` | `list[Post]` |
| `get_creator_profile(service, creator_id)` | `GET /{service}/user/{creator_id}/profile` | `CreatorProfile` |
| `list_creator_posts(service, creator_id, query=None, offset=None)` | `GET /{service}/user/{creator_id}` | `list[Post]` |
| `list_announcements(service, creator_id)` | `GET /{service}/user/{creator_id}/announcements` | `list[Announcement]` |
| `list_fancards(service, creator_id)` | `GET /{service}/user/{creator_id}/fancards` | `list[Fancard]` |
| `list_creator_links(service, creator_id)` | `GET /{service}/user/{creator_id}/links` | `list[CreatorProfile]` |
| `get_post(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}` | `Post` |
| `search_file_by_hash(file_hash)` | `GET /search_hash/{file_hash}` | `FileSearchResult` |
| `flag_post(service, creator_id, post_id)` | `POST /{service}/user/{creator_id}/post/{post_id}/flag` | `None` |
| `is_post_flagged(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/flag` | `bool` |
| `list_post_revisions(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/revisions` | `list[Revision]` |
| `list_post_comments(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/comments` | `list[Comment]` |
| `get_app_version()` | `GET /app_version` | `str` |

Les cinq opérations OpenAPI protégées par `cookieAuth` sont volontairement exclues : consulter les favoris du compte et ajouter ou retirer des publications ou des créateurs des favoris. Le signalement d'une publication fait partie du contrat public et n'utilise pas de session de compte.

## Validation des paramètres

- `service`, les identifiants de créateur et de publication doivent contenir au moins un caractère qui ne soit pas une espace.
- Une requête de recherche fournie doit contenir au moins trois caractères.
- Les décalages d'API doivent être positifs ou nuls et multiples de 50.
- Les hachages de fichier doivent comporter exactement 64 caractères hexadécimaux.
- Les paramètres de requête facultatifs valant `None` sont omis.

Une valeur incorrecte déclenche une `ValidationError` Pydantic avant l'envoi de toute requête.

## Contrat des erreurs

Toutes les erreurs propres à l'API dérivent de `PawchiveError` :

| Exception | Signification |
| --- | --- |
| `PawchiveTransportError` | Échec DNS, de connexion, TLS ou de délai après les nouvelles tentatives |
| `PawchiveHTTPError` | Échec HTTP sans correspondance plus précise |
| `PawchiveAuthenticationError` | HTTP `401` ou `403` |
| `PawchiveNotFoundError` | HTTP `404` |
| `PawchiveConflictError` | HTTP `409`, y compris une publication déjà signalée |
| `PawchiveResponseValidationError` | JSON incorrect ou réponse incompatible avec le modèle |

`is_post_flagged()` constitue l'unique exception d'état volontaire : `404` devient `False`. Les requêtes utilisent `Accept: application/json`, ne suivent pas les redirections et ne sont retentées que pour les erreurs de transport et les réponses `429` ou `5xx`. Les autres réponses `4xx` et les échecs de validation ne sont jamais retentés.

## Modèles et dérive du schéma

Les modèles générés se trouvent dans `ktoolbox.api.generated` et conservent les champs inconnus des réponses grâce à l'option Pydantic `extra="allow"`. Le client transmet leur chemin à `drift_reporter` ; fournissez une fonction de rappel personnalisée lors de l'intégration de la télémétrie.

Le contrat source non modifié est `k_generator/pawchive_openapi.json`. Les corrections de compatibilité vérifiables sont stockées dans `k_generator/pawchive_openapi.overrides.json` et produisent `k_generator/pawchive_openapi.normalized.json` ainsi que des modèles générés de manière déterministe.
