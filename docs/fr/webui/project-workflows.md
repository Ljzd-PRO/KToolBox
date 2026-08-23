# Parcours de projet WebUI

Après avoir installé la WebUI et l'avoir liée à un projet, utilisez cette page pour gérer ses données et réglages. L'exécution des tâches et le déploiement disposent de guides dédiés.

## Processus du projet

L'interface suit la langue du navigateur lors de la première utilisation et conserve le choix du chinois simplifié, du chinois traditionnel, de l'anglais, du japonais, du coréen, du français ou du russe. Changer de langue actualise aussi les dates React Aria, les formats numériques, le tri naturel, les métadonnées de configuration, la validation et les erreurs serveur connues. Le thème suit le système d'exploitation jusqu'au choix du mode clair ou sombre. Des accents bleu, émeraude, violet, rose et ambre sont proposés ; les interrupteurs activés restent bleus afin que leur état soit cohérent. L'ordinateur utilise une barre latérale compacte et les écrans étroits un Drawer.

![Sélecteur des sept langues](../../assets/webui/23-language-menu-seven-locales.png)

![Éditeur de configuration clair](../../assets/webui/09-configuration-light.png)

Les zones modifiables utilisent une surface secondaire discrète avec des arrière-plans de champs distincts. Les icônes facilitent le repérage, tandis que les interrupteurs et cases restent alignés à gauche avec leur libellé au lieu de ressembler à des boutons centrés. La piste est grise à l'arrêt et bleue en marche ; les cases n'affichent un indicateur que lorsqu'elles sont cochées ou indéterminées. Le contenu de la fenêtre modifiable et sa barre d'actions fixe partagent une surface continue.

Les zones principales sont :

- **Vue d'ensemble :** chemin du projet, état de la file, totaux des transferts actifs et tâches récentes.
- **Tâches :** créer, modifier, mettre en pause, reprendre, arrêter, relancer, supprimer et examiner des synchronisations ou téléchargements uniques. Seul le lien de cible lisible ouvre le détail, afin qu'un contrôle ne déclenche jamais la navigation ; la sélection multiple permet les actions groupées compatibles.
- **Synchronisation automatique :** créer plusieurs plans récurrents par créateur, consulter les mises à jour récentes et l’historique, suspendre ou exécuter immédiatement.
- **Créateurs :** rechercher dans Pawchive et ajouter, modifier la note, activer, désactiver ou retirer des entrées, y compris par actions groupées.
- **Publications :** rechercher des œuvres, examiner les révisions et créer une tâche de téléchargement. Les aperçus d’images n’apparaissent qu’après activation explicite du mode NSFW ; le texte reste replié par défaut.
- **Règles d'exclusion :** ordonner et limiter `field-match`, composer des groupes `any`/`all` imbriqués et des conditions de contenu, égalité, expression régulière et existence.
- **Configuration globale :** modifier `.env`, `prod.env` et `ktoolbox.toml` dans des formulaires typés ou des vues de texte avancées.
- **Système :** examiner les versions du projet et de l'application et télécharger un exemple d'environnement.
- **À propos :** consulter la version, la licence, l'environnement, l'auteur, la documentation, le dépôt et le suivi des problèmes sans exposer l'adresse électronique de l'auteur.

![Éditeur de tâche sur un écran étroit](../../assets/webui/19-task-form-mobile-light-zh.png)

![Liste des créateurs Pawchive](../../assets/webui/41-creators-showcase-desktop-light.png)

La création d'une tâche utilise deux onglets fixes sans commandes de débordement. Les dates de synchronisation restent dans un unique champ de plage HeroUI officiel au format `year/month/day - year/month/day`, tandis que « Aucune date de début » et « Aucune date de fin » effacent indépendamment la limite correspondante. Le décalage des publications progresse par pas de 50. Les filtres de titre utilisent des HeroUI Chip supprimables, créés avec une virgule ou Entrée. Le téléchargement d'une œuvre unique et l'ajout d'un créateur utilisent des champs HeroUI indépendants, séparés par des fragments de chemin Pawchive au style de code, tels que `/platform/user/creator/post/post` ; les séparateurs ne sont jamais simulés comme des champs de saisie.

L'identifiant du créateur est placé en premier dans les lignes de bureau comme dans les entrées mobiles. La note facultative de la liste est affichée séparément et ne remplace jamais cet identifiant. Lors de la modification d'un créateur existant, sa plateforme et son identifiant restent visibles, mais en lecture seule, car ils identifient ensemble l'entrée enregistrée.

## Aperçus facultatifs de médias sensibles

Le mode NSFW est désactivé dans tout nouveau navigateur. Tant qu’il est désactivé, les pages des créateurs et des œuvres restent textuelles, sans requête d’image ni espace multimédia vide. Chaque activation demande une confirmation ; l’état reste ensuite dans ce navigateur, synchronisé entre les onglets, jusqu’à sa désactivation.

Le navigateur récupère les médias uniquement par le proxy WebUI authentifié de même origine, jamais directement depuis les hôtes de fichiers Pawchive. Le proxy décode et vérifie entièrement le bitmap, refuse les redirections, SVG, fichiers non graphiques ou endommagés et les ressources de plus de 32 Mio ou 50 MP, puis crée des miniatures bornées. Il peut afficher avatars, bannières, couvertures, pièces jointes image et images de contenu compatibles. La galerie charge 12 éléments à la fois et la visionneuse accepte les flèches et Échap. Vidéos, archives et autres pièces jointes restent textuelles.

![Avatars avec le mode NSFW activé](../../assets/webui/46-creators-nsfw-preview-light.png)

![Couverture et galerie multimédia paginée](../../assets/webui/47-post-media-gallery-light.png)

## Synchronisation automatique

La page **Synchronisation automatique** prend en charge plusieurs plans, plusieurs créateurs, les expressions Cron à cinq champs et les intervalles ancrés d’au moins 15 minutes. Chaque plan définit un fuseau IANA, une limite de première exécution, les options de sortie et un aperçu des trois prochaines exécutions. Une exécution immédiate utilise la même file et avance les points de contrôle des créateurs réussis sans déplacer l’axe de l’intervalle.

Les vérifications privilégient l’horodatage `added` de Pawchive, interprété comme UTC, et recouvrent de 24 heures le dernier point de contrôle réussi. La déduplication au niveau du projet évite de compter deux fois la même œuvre entre plusieurs plans. Une première exécution sans date établit uniquement une base et ne marque pas toutes les archives comme nouvelles. Les exécutions manquées pendant l’arrêt sont ignorées, tout comme les déclenchements en double lorsqu’un plan est déjà actif. Consultez le [guide de synchronisation automatique](../automatic-sync.md).

## Nommage du projet

Le nommage et la sortie par défaut sont enregistrés dans `ktoolbox.toml` et partagés par la CLI, la WebUI, MCP, les téléchargements d’œuvres et la synchronisation automatique. La page **Format de nommage** enregistre séparément structure et modèles. Le convertisseur réutilisable accepte plusieurs formats enregistrés ou une ancienne configuration `.env`/TOML collée, conserve le projet actuel comme cible en lecture seule et ne mémorise pas le texte source. Il analyse uniquement les anciens emplacements choisis explicitement, sans contacter Pawchive, et prend en charge pause, reprise et restauration. Ces emplacements ne deviennent jamais des destinations futures. Consultez le [guide du nommage](../naming.md).

## Modification de la configuration

Les libellés et descriptions sont du texte explicitement localisé, pas des identifiants Python. Les docstrings `:ivar field:` de la classe anglaise restent la source sémantique des champs ; les catalogues dont la complétude est vérifiée fournissent tous les libellés et explications dans les sept langues. Pydantic fournit les types, valeurs par défaut, plages et métadonnées secrètes.

Les choix fixes comme le niveau de journal utilisent un Select HeroUI enrichi d’icônes, tandis que les champs proposant des valeurs recommandées tout en acceptant une saisie personnalisée utilisent ComboBox. Les noms internes `attachments`, `content.txt` et `external_links.txt` restent des champs de texte ordinaires ; seuls les véritables emplacements du système de fichiers proposent le sélecteur de chemin.

Les onglets `.env` et `prod.env` affichent la valeur effective finale et une puce de provenance. Les valeurs remplacées par l'environnement du processus sont en lecture seule. Les secrets sont masqués par défaut. L'édition avancée du texte affiche un avertissement supplémentaire, car elle peut dévoiler des secrets.

Les champs liés au système de fichiers conservent la saisie manuelle et ajoutent un bouton de navigation. La boîte de dialogue affiche l'ordinateur distant qui exécute KToolBox, et non l'appareil du navigateur, avec emplacements rapides, fil d'Ariane, recherche, éléments cachés, pagination et création de répertoire. Les valeurs de configuration relatives au projet restent relatives après sélection ; les sorties absolues des tâches et publications restent absolues. Les valeurs en lecture seule provenant de l'environnement ne peuvent pas ouvrir le sélecteur.

Avant l'enregistrement, le serveur analyse et valide le fichier proposé, puis renvoie une différence sémantique. Un ETag refuse les modifications obsolètes et le fichier est remplacé atomiquement. L'éditeur TOML utilise le stockage TomlKit/Pydantic existant, les commentaires survivent donc aux changements structurés.

![Éditeur de configuration sombre](../../assets/webui/20-configuration-1024-dark-zh.png)

![Choix du niveau de journal dans la configuration globale](../../assets/webui/30-global-configuration-log-level-light.png)

![Éditeur de règle à portée limitée](../../assets/webui/17-blocker-form-1024-light-zh.png)

## Guides WebUI associés

- [Installation et sécurité](../webui.md)
- [Parcours du projet](project-workflows.md)
- [Tâches et mises à jour](tasks.md)
- [Référence de déploiement](reference.md)
