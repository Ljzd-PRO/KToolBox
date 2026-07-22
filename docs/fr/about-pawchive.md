# À propos de Pawchive

[Pawchive](https://pawchive.pw/) est le seul serveur pris en charge par KToolBox v1. KToolBox utilise son API publique pour trouver les créateurs et les publications, puis télécharge les fichiers depuis le serveur de fichiers dédié de Pawchive.

## Adresses par défaut

| Usage | Valeur par défaut |
| --- | --- |
| API publique | `https://pawchive.pw/api/v1` |
| Icônes et bannières des créateurs | `https://pawchive.pw` |
| Fichiers des publications | `https://file.pawchive.pw/data/...` |

Les requêtes d'API ne transportent jamais de session de compte. Lorsqu'il est configuré, `downloader.session_key` est envoyé comme cookie `session` uniquement dans les requêtes de téléchargement de fichiers.

## Périmètre de l'API

KToolBox met en œuvre les 14 opérations du document OpenAPI publié qui ne nécessitent pas `cookieAuth` : recherche de créateurs et de publications, profils, annonces, cartes de fans, liens, détails des publications, recherche par hachage de fichier, état et envoi du signalement d'une publication, révisions, commentaires et version de l'application.

Les cinq opérations sur les favoris nécessitent un compte Pawchive connecté et sont volontairement exclues.

## Utilisation responsable

Respectez les lois applicables, les conditions de la plateforme, les droits des créateurs et les limites de stockage. Lors du premier essai d'un créateur, utilisez une synchronisation limitée (`--length`) et des limites de taille de fichier.
