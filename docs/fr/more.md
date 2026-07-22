# Informations sur le projet

## Branche de développement

Le travail sur Pawchive v1 est maintenu dans la branche [`pawchive`](https://github.com/Ljzd-PRO/KToolBox/tree/pawchive) jusqu'à ce qu'il soit prêt à devenir la ligne de publication par défaut.

Les changements sont répartis en commits ciblés couvrant le contrat, le client, la migration du projet, les tests, la documentation et les métadonnées de publication. Le fichier OpenAPI Pawchive d'origine reste intact afin que les changements du code généré puissent être vérifiés par rapport au contrat normalisé.

## Politique de qualité

La suite de tests par défaut est entièrement hors ligne et bloque les accès réseau accidentels. La couche d'API écrite manuellement doit conserver une couverture de 100 % des lignes et des branches, les modèles générés sont exclus des statistiques et le projet complet doit rester à 85 % ou plus.

L'intégration continue valide également le document OpenAPI, la génération déterministe des modèles, Ruff, le contrôle Mypy strict de la couche API, la compilation du code intermédiaire Python, la construction des paquets et la construction MkDocs stricte sur les versions de Python prises en charge.

## Licence

KToolBox est distribué sous la [licence BSD à 3 clauses](https://github.com/Ljzd-PRO/KToolBox/blob/master/LICENSE).

Copyright © 2023 by Ljzd-PRO.
