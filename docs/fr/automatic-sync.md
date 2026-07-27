# Synchronisation automatique

La page **Synchronisation automatique** exécute le flux existant de synchronisation des créateurs selon un calendrier. Chaque exécution crée une tâche normale ; sa progression, ses erreurs, sa pause, son arrêt et ses journaux restent accessibles dans **Tâches**.

![Plans automatiques et mises à jour récentes](../assets/webui/37-auto-sync-desktop-light.png)

## Créer un plan

1. Ajoutez les créateurs à la liste du projet.
2. Ouvrez **Synchronisation automatique**, puis **Nouveau plan**.
3. Sélectionnez un ou plusieurs créateurs.
4. Choisissez une expression Cron à cinq champs ou un intervalle fixe d'au moins 15 minutes.
5. Choisissez un fuseau IANA et vérifiez les trois prochaines exécutions.
6. Définissez la date de première vérification et les options de synchronisation, puis enregistrez.

![Cron et aperçu des prochaines exécutions](../assets/webui/38-auto-sync-schedule-preview-light.png)

L'éditeur visuel couvre les fréquences horaires, quotidiennes, hebdomadaires et mensuelles. Le mode avancé accepte les expressions standard. **Exécuter maintenant** ne décale pas le prochain intervalle automatique.

## Points de contrôle et mises à jour

L'heure de fin est figée au démarrage. KToolBox privilégie l'horodatage `added` de Pawchive, interprété comme UTC, relit une fenêtre de 24 heures avant le dernier point réussi et déduplique par plateforme, ID de créateur et ID d'œuvre.

- Chaque créateur réussi avance son propre point de contrôle.
- Un créateur en échec conserve son ancien point.
- Une première exécution sans date établit une base sans compter tout l'historique comme nouveau.
- Une exécution manuelle utilise les mêmes points de contrôle.
- Les mises à jour n'affichent que les créateurs et les nombres ; aucun titre ni média n'est chargé.
- La carte **Nouvelles œuvres** contrôle la période du total et de la liste : **Aujourd’hui** commence à minuit local, tandis que les dernières 24 heures, 7, 14 et 30 jours sont des fenêtres glissantes.

## Pause, conflits et arrêts

Mettre un plan en pause bloque les futurs déclenchements sans arrêter la tâche courante. Les exécutions manquées pendant l'arrêt de KToolBox ne sont pas rejouées.
