# Guide des commandes

KToolBox utilise des commandes Cyclopts avec des options conventionnelles à traits d'union et l'aide Rich. L'aide est affichée directement et n'ouvre jamais d'afficheur paginé.

```bash
ktoolbox --help
ktoolbox sync --help
```

![Aperçu des commandes KToolBox](../../assets/cli-overview.png)

Les options globales peuvent précéder ou suivre une commande :

```bash
ktoolbox --config ./ktoolbox.toml --plain sync
ktoolbox creator list --json --config ./ktoolbox.toml
```

Utilisez `--verbose` pour les journaux de diagnostic, `--quiet` pour masquer la progression et les journaux ordinaires, `--plain` pour une progression stable ligne par ligne et `--no-color` pour conserver la disposition interactive sans couleurs ANSI.

## Télécharger une publication

Transmettez l'URL d'une page Pawchive ou les trois valeurs d'identification :

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

ktoolbox download \
  --service fanbox \
  --creator-id 6570768 \
  --post-id 1836570 \
  --output downloads
```

Utilisez `--revision-id` pour sélectionner une révision. KToolBox récupère la liste des révisions et recherche cet ID, car Pawchive ne possède aucun point d'accès aux détails d'une seule révision. Définissez `KTOOLBOX_JOB__INCLUDE_REVISIONS=True` pour inclure toutes les révisions lors du téléchargement de la publication actuelle.

Relancez la même commande après une interruption. Les fichiers complets sont ignorés et les fichiers temporaires compatibles reprennent grâce aux requêtes HTTP Range. La commande explicite `download` n'applique pas les règles d'exclusion de la synchronisation.

## Synchroniser les créateurs

`sync` accepte un nombre quelconque d'URL de créateur, d'identités `service:id` ou d'alias enregistrés dans la liste du projet :

```bash
# Une synchronisation limitée d'un créateur.
ktoolbox sync fanbox:123 --length 1

# Plusieurs créateurs partagent un même pool de téléchargement simultané.
ktoolbox sync fanbox:123 patreon:456 studio-c --length 10
```

Omettre `--length` parcourt toutes les pages disponibles. À la frontière de la CLI, `--offset` est un index de publication ; KToolBox le convertit en décalages de pages Pawchive de 50 éléments.

```bash
ktoolbox sync fanbox:123 --offset 10 --length 5
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

Chaque créateur est stocké sous la forme `Creator name [service-creator_id]`. Au plus `job.creator_concurrency` producteurs de créateurs s'exécutent simultanément. Leurs files limitées alimentent un planificateur équitable en tourniquet, tandis que `job.count` contrôle le nombre de transferts de fichiers simultanés. Les téléchargements commencent dès que les premières tâches existent, sans attendre tous les créateurs.

L'échec d'un créateur n'efface pas le travail terminé pour les autres. Les créateurs en échec conservent leur index précédent et la commande finale se termine avec l'état `1` après avoir affiché un résumé.

## Gérer une liste de créateurs

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add https://pawchive.pw/patreon/user/456 --alias studio-b
ktoolbox creator disable studio-b
ktoolbox creator list
ktoolbox creator enable studio-b
ktoolbox creator remove studio-b
```

Exécutez `ktoolbox sync` sans cible pour synchroniser toutes les entrées activées de la liste. Un créateur désactivé explicitement nommé est tout de même exécuté. Les identités `service:id` sont uniques, les alias sont facultatifs et uniques, et les écritures de configuration conservent les commentaires.

## Exclure les publications qui ne sont pas des œuvres

Définissez des règles ordonnées sur les champs dans `ktoolbox.toml`. Elles peuvent s'appliquer globalement ou seulement à certains créateurs `service:id`, et examiner les titres, le contenu, les étiquettes, les noms de fichiers, les ID et les chemins de listes imbriquées. La première règle correspondante exclut la publication avant la création des détails, révisions, métadonnées, répertoires ou tâches de téléchargement.

Consultez le [guide de configuration](../configuration/guide.md#post-blockers) pour des exemples complets. `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` demeure une ancienne règle globale sur les titres réservée à la migration.

## Examiner les données publiques

```bash
ktoolbox creator search --name example --service fanbox
ktoolbox post search --creator-id 6570768 --service fanbox --query preview --offset 0
ktoolbox post show fanbox 6570768 1836570
```

Les commandes de requête utilisent par défaut des tableaux Rich compacts. Ajoutez `--json` pour obtenir des données lisibles par une machine sur stdout ; les journaux et la progression restent sur stderr. `--dump path.json` écrit également les modèles validés dans un fichier.

## Utilitaires de configuration

```bash
ktoolbox config path
ktoolbox config validate
ktoolbox config example
ktoolbox config edit
ktoolbox site-version
```

L'éditeur nécessite la dépendance facultative `urwid`. Il modifie les réglages dotenv et le document de projet contenant la liste et les règles, puis les valide avant l'enregistrement.

## Exécuter le panneau de projet facultatif

Après avoir installé `ktoolbox[webui]` et configuré un compte, liez le panneau à un répertoire de projet. Un fichier `ktoolbox.toml` absent est créé automatiquement après un avertissement dans le terminal :

```bash
ktoolbox webui . --host 127.0.0.1
```

Le panneau présente les mêmes processus de téléchargement, synchronisation, liste, règles d'exclusion, requête et configuration comme actions gérées du projet, avec une progression et des commandes de tâches persistantes. Consultez le [guide de la WebUI](../webui.md) avant d'écouter sur une interface réseau.

## État de sortie

| Code | Signification |
| --- | --- |
| `0` | La commande s'est terminée correctement. |
| `1` | Une opération distante, un créateur ou un téléchargement a échoué ; les fichiers partiels sont conservés. |
| `2` | Les arguments ou la configuration sont incorrects. |
| `130` | L'utilisateur a interrompu la commande. |

Les échecs attendus sont affichés sans trace d'appels Python.
