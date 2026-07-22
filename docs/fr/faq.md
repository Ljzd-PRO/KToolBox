# Questions fréquentes

## Pourquoi les favoris du compte sont-ils indisponibles ?

KToolBox v1 met en œuvre les 14 opérations Pawchive qui ne nécessitent aucune connexion. Les cinq opérations OpenAPI protégées par `cookieAuth` sont volontairement exclues ; le client API n'accepte et n'envoie donc jamais de session de compte.

Le signalement d'une publication est une opération publique distincte et mise en œuvre. Appelez-la intentionnellement : un signalement réussi modifie l'état du serveur et une publication déjà signalée peut renvoyer `PawchiveConflictError`.

## Que faire lorsqu'un appel d'API échoue ?

La CLI signale des échecs Pawchive typés plutôt que de renvoyer une réponse partiellement analysée. Les classes courantes concernent le transport, HTTP, l'authentification, une ressource introuvable, un conflit et la validation de la réponse.

- Vérifiez l'URL ou les valeurs de `service`, de l'ID du créateur et de l'ID de la publication.
- Augmentez `KTOOLBOX_API__TIMEOUT` pour une connexion lente.
- Ajustez `KTOOLBOX_API__RETRY_TIMES` et `KTOOLBOX_API__RETRY_INTERVAL` pour les échecs temporaires de transport, `429` ou `5xx`.
- N'ajoutez pas de cookie de compte aux réglages de l'API ; les requêtes d'API n'en utilisent pas.

Les redirections, réponses `4xx` ordinaires, conflits et données de réponse incorrectes ne sont pas retentés.

## Pourquoi les téléchargements renvoient-ils 403 ?

Si le serveur de fichiers exige une session pour une ressource donnée, définissez la clé réservée au téléchargeur :

```dotenv
KTOOLBOX_DOWNLOADER__SESSION_KEY=xxxxx
```

Le cookie est limité aux requêtes de téléchargement et n'est pas envoyé à l'API Pawchive. Traitez `.env` et `prod.env` comme des fichiers locaux contenant des secrets et ne les validez pas dans le dépôt.

## Comment reprendre un téléchargement interrompu ?

Relancez la même commande. KToolBox ignore les fichiers de destination complets. Si un fichier incomplet avec `downloader.temp_suffix` existe et que le serveur accepte les plages, le téléchargeur demande les octets restants et valide la taille combinée.

## Comment désactiver les couvertures ou les pièces jointes ?

```dotenv
# Pièces jointes uniquement.
KTOOLBOX_JOB__DOWNLOAD_FILE=False
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True

# Couvertures uniquement.
#KTOOLBOX_JOB__DOWNLOAD_FILE=True
#KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`download_file` désigne le fichier principal de la publication, généralement la couverture. Les deux options valent `True` par défaut.

## Les pièces jointes peuvent-elles être enregistrées directement dans le répertoire de la publication ?

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## Comment éviter les noms de fichiers trop longs ?

Utilisez des noms séquentiels ou une limite de précision du format :

```dotenv
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}_{title:.30}
KTOOLBOX_JOB__FILENAME_FORMAT={title:.30}_{}
```

## Comment configurer un proxy ?

HTTPX lit les variables d'environnement standard des proxys :

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5://127.0.0.1:7897
```

Dans PowerShell :

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## Pourquoi l'éditeur de configuration ne s'ouvre-t-il pas ?

Installez la dépendance facultative de l'interface de terminal :

```bash
pip install "ktoolbox[urwid]"
# ou
pipx install "ktoolbox[urwid]" --force
```

## Comment synchroniser régulièrement de nombreux créateurs ?

Ajoutez chaque créateur à la liste du projet, attribuez éventuellement un alias court, puis exécutez `sync` sans cible :

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

Utilisez `creator disable` pour conserver une entrée sans l'inclure dans les exécutions sans cible. Vous pouvez toujours synchroniser explicitement un alias désactivé. La préparation des créateurs et le transfert des fichiers ont des limites de simultanéité distinctes, de sorte qu'un grand créateur ne monopolise pas tous les téléchargements prêts.

## Comment exclure des sujets différents selon les créateurs ?

Ajoutez des entrées `[[blockers]]` distinctes à `ktoolbox.toml`. Définissez `scope.mode = "global"` pour les règles partagées par tous, ou `scope.mode = "creators"` avec les valeurs `service:id` exactes. Les règles sont évaluées dans l'ordre du fichier et s'arrêtent à la première correspondance.

Validez les expressions régulières et les portées avant une longue exécution :

```bash
ktoolbox config validate
```

## Pourquoi la progression diffère-t-elle dans un journal redirigé ?

La progression Rich en direct n'est utilisée que dans un terminal interactif. Elle affiche la vitesse et l'heure estimée de chaque fichier actif, ainsi que la vitesse totale sur la ligne `Files`. Les tubes, l'intégration continue, `NO_COLOR` et `--plain` utilisent des lignes stables afin que les journaux n'endommagent pas la zone ANSI. Utilisez `--no-color` pour conserver la disposition interactive sans couleurs ou `--quiet` pour masquer la progression et les journaux ordinaires.

## Pourquoi la WebUI refuse-t-elle de démarrer ?

Installez `ktoolbox[webui]` et transmettez un répertoire de projet. Les réglages du compte sont facultatifs : sans eux, le terminal affiche le nom `admin` et un mot de passe aléatoire pour cette exécution. Un hachage explicitement configuré doit rester une valeur Argon2 valide. Un fichier `ktoolbox.toml` absent est créé après un avertissement, tandis que le verrou refuse toujours un second processus WebUI pour le même projet.

## Est-il sûr d'exposer la WebUI sur mon réseau ?

Le serveur par défaut utilise HTTP en clair ; n'utilisez donc `0.0.0.0` que sur un réseau local fiable. Liez `127.0.0.1` pour un usage local ou placez le service derrière un proxy inverse HTTPS pour un accès distant. L'authentification, CSRF, les cookies stricts, la limitation des requêtes et les en-têtes de sécurité protègent l'application, mais ne peuvent pas chiffrer un chemin HTTP.

## Que devient une tâche WebUI après un redémarrage ?

Les tâches en attente le restent. Le travail en cours est marqué `interrupted` au lieu d'être relancé silencieusement, car sa configuration et son état distant peuvent avoir changé. Vérifiez-le et reprenez-le manuellement. Les fichiers terminés et temporaires pouvant être repris restent disponibles.

## Supprimer une tâche WebUI peut-il enlever des fichiers sans rapport ?

Une suppression ordinaire ne retire que l'historique. La suppression des sorties exige un aperçu et une confirmation, puis vérifie les enregistrements de propriété et les métadonnées. Les fichiers préexistants, modifiés, partagés, non ordinaires et les liens symboliques sont ignorés.

## uvloop ou winloop est-il nécessaire ?

Non. Ce sont des optimisations facultatives de la boucle d'événements. Utilisez `ktoolbox[uvloop]` sous Linux/macOS ou `ktoolbox[winloop]` sous Windows. Sans eux, KToolBox continue avec la boucle asyncio standard de Python.

## Pourquoi un antivirus peut-il signaler un exécutable empaqueté ?

Certains analyseurs heuristiques signalent les paquets PyInstaller ou les gestionnaires de téléchargement. Les versions sont construites par l'automatisation publique du dépôt ; vous pouvez aussi installer avec `pipx` ou vérifier et construire les sources localement.
