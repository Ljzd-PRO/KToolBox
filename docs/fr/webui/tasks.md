# Tâches WebUI et mises à jour en direct

La file persistante réunit définitions, tentatives, progression, diagnostics et propriété des fichiers. Cette page décrit les commandes d'exécution et la synchronisation en direct.

## Cycle de vie des tâches

Les tâches `sync` et `download` conservent toutes les entrées de la CLI correspondante. Une synchronisation sans cible résout la liste actuellement activée lors de la création. Chaque tentative reçoit ensuite un instantané immuable et expurgé de la configuration ; les modifications ultérieures n'affectent que les tentatives futures.

Chaque tâche conserve aussi un instantané réservé à la présentation avec sa clé cible normalisée, ainsi que les titre et nom du créateur facultatifs. Il reste lisible hors ligne et n'affecte jamais l'exécution, la déduplication ou les verrous. Les lignes commencent par cette cible plutôt que le chemin de sortie, et les détails, la pause/reprise, l'arrêt, la modification, le classement et la suppression restent visibles directement.

![File de tâches de bureau avec des cibles lisibles](../../assets/webui/43-task-queue-showcase-desktop-light.png)

![File mobile avec actions directes](../../assets/webui/22-task-queue-mobile-light-zh.png)

![Éditeur de tâche sombre](../../assets/webui/18-task-form-1024-dark-zh.png)

La file principale exécute deux tâches par défaut (`KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS`), tandis que chacune conserve sa simultanéité configurée de créateurs et de fichiers. Les tâches actives identiques renvoient à la tâche existante. Les tâches dont les sorties, créateurs ou publications normalisés se chevauchent attendent dans `blocked` la libération du verrou.

Les événements en direct utilisent SSE avec reconnexion. L'état REST reste la référence et seul un événement `task.status` peut le modifier ; la fin d'un fichier ne termine jamais prématurément sa tâche. La vitesse globale utilise une fenêtre glissante de cinq secondes et un bref délai de transition, ce qui évite un passage furtif à zéro entre deux fichiers. L'aperçu et la page des tâches additionnent la vitesse des tâches réellement actives.

![Aperçu avec vitesse globale](../../assets/webui/40-overview-showcase-desktop-light.png)

La vue détaillée indique les créateurs préparés, les fichiers, les octets, la progression totale, les vitesses globale et par fichier, l'heure estimée, les nombres ignorés/échoués, les créateurs actifs, les téléchargements actifs, les nouvelles tentatives en attente et les journaux structurés. Les trois panneaux en direct ont une hauteur stable et leur propre défilement : les changements de simultanéité ne déplacent plus le journal ni la page. La vue d'activité par défaut masque la progression par blocs et le bruit ordinaire de la file ; les vues transferts et diagnostic complet restent disponibles.

![Panneaux de tâche stables](../../assets/webui/44-task-live-showcase-desktop-dark.png)

Chaque tentative en échec conserve un rapport de diagnostic borné et expurgé au lieu d'un simple compteur. La ligne de tâche affiche la première cause utile ; le détail regroupe les échecs par créateur et fichier et indique l'étape, la possibilité de réessayer, les chemins de champs sûrs et l'action recommandée. Le corps des réponses amont, les titres d'œuvres, les cookies et les URL complètes de téléchargement ne sont jamais enregistrés. Sur écran étroit, la barre de 64px, l'espacement de page de 12px et le Popover d'apparence compact affichent davantage de contenu sans réduire le texte des formulaires sous 16px. Le catalogue MCP utilise des groupes HeroUI repliables et développe automatiquement les groupes correspondant à une recherche ou à un filtre de permission.

![Explication structurée d'un échec de tâche](../../assets/webui/26-task-failure-1440-light-zh.png)

![Contrôles d'apparence mobiles compacts](../../assets/webui/27-appearance-mobile-dark-zh.png)

![Progression d'une tâche en direct sur mobile](../../assets/webui/45-task-live-showcase-mobile-dark.png)

La pause est coopérative : les flux réseau actifs se ferment, les fichiers terminés et temporaires pouvant reprendre restent, et la reprise crée une nouvelle tentative. Seules les tâches en pause, arrêtées, échouées ou interrompues (`interrupted`) peuvent reprendre. Une synchronisation terminée propose « Relancer », qui conserve l'enregistrement et crée une nouvelle tentative ; un téléchargement unique terminé ne le propose pas.

Supprimer une tâche ne retire normalement que son enregistrement, ses tentatives et ses journaux. « Supprimer les sorties » présente la cible lisible, le répertoire, les totaux et une liste extensible de chemins relatifs sans UUID interne. La confirmation ne retire que les fichiers ordinaires inchangés enregistrés comme créés par cette tâche.

![Aperçu lisible du nettoyage](../../assets/webui/31-task-delete-preview-light.png)

![Synchronisation terminée avec relance](../../assets/webui/33-task-rerun-light.png)

## Actualisation automatique

Après la connexion, une seule connexion SSE synchronise les tâches, créateurs, règles d'exclusion, configurations, jetons MCP et répertoires distants ouverts entre les onglets du navigateur. Les changements structurels apparaissent normalement en moins d'une seconde ; la progression des tâches met directement à jour le cache local sans retélécharger toute la liste.

Si la connexion en direct reste indisponible plus de cinq secondes, la WebUI affiche un avertissement compact et actualise les données locales du projet toutes les 10 secondes. Dès le rétablissement de SSE, elle arrête ce mode de secours et effectue une actualisation unique. Les recherches Pawchive, détails d'œuvres et vérifications de version restent à la demande et ne sont jamais lancés par le mode de secours.

La page Système indique la méthode d'actualisation et l'heure du dernier signal, avec des actions d'actualisation et de reconnexion. Si un autre onglet ou client MCP modifie les données pendant qu'un formulaire contient des changements non enregistrés, KToolBox conserve le brouillon et propose de recharger ou de poursuivre l'édition ; les contrôles ETag et d'état restent actifs lors de l'enregistrement.

## Guides WebUI associés

- [Installation et sécurité](../webui.md)
- [Parcours du projet](project-workflows.md)
- [Tâches et mises à jour](tasks.md)
- [Référence de déploiement](reference.md)
