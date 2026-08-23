# Informations sur le projet

## État de la version

KToolBox v1 est la nouvelle série basée sur Pawchive. Il s'agit d'une mise à niveau incompatible depuis la v0 qui n'a pas encore été suffisamment validée en usage réel ; testez donc un téléchargement limité avant une synchronisation importante. Pour une installation existante, commencez par la [migration vers v1](migration-v1.md).

Kemono n'est plus disponible et Pawchive est l'unique serveur pris en charge. Le fichier OpenAPI Pawchive d'origine reste intact afin de comparer les changements du client généré au contrat normalisé.

## Assistance et ressources

Utilisez la recherche du site et la [FAQ](faq.md) avant de quitter la documentation. Si la réponse manque, utilisez ces liens externes au rôle explicite :

- le [suivi des problèmes](https://github.com/Ljzd-PRO/KToolBox/issues) pour les défauts reproductibles ;
- les [Discussions](https://github.com/Ljzd-PRO/KToolBox/discussions) pour les questions et propositions ;
- les [Releases](https://github.com/Ljzd-PRO/KToolBox/releases) pour les notes et fichiers publiés ;
- le [dépôt source](https://github.com/Ljzd-PRO/KToolBox) pour le code et l'historique des contributions.

## Qualité et licence

La suite de tests par défaut est entièrement hors ligne et bloque les accès réseau accidentels. L'intégration continue valide les contrats OpenAPI, la génération déterministe, les tests, Ruff, Mypy, le code intermédiaire Python, les paquets, la WebUI et la construction MkDocs stricte.

KToolBox utilise la [licence BSD à 3 clauses](https://opensource.org/license/bsd-3-clause). Copyright © 2023 by Ljzd-PRO.
