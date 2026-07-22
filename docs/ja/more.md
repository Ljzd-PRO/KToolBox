# プロジェクト情報

## 開発ブランチ

Pawchive v1 の作業は、既定のリリース系列になる準備が整うまで [`pawchive`](https://github.com/Ljzd-PRO/KToolBox/tree/pawchive) ブランチで管理されます。

変更は契約、クライアント、プロジェクト移行、テスト、ドキュメント、リリースメタデータごとの集約されたコミットに分けられています。正規化済み契約に対して生成コードの変更を監査できるよう、元の Pawchive OpenAPI ファイルは変更しません。

## 品質方針

既定のテストスイートは完全にオフラインで、意図しないネットワークアクセスを禁止します。手書きの API レイヤーは行と分岐のカバレッジを 100% に維持し、生成済みモデルは統計から除外し、プロジェクト全体では 85% 以上を維持する必要があります。

CI は対応する Python バージョン上で OpenAPI 文書、決定的なモデル生成、Ruff、API レイヤーの厳格な Mypy、Python バイトコードのコンパイル、パッケージビルド、厳格な MkDocs ビルドも検証します。

## ライセンス

KToolBox は [BSD 3-Clause License](https://github.com/Ljzd-PRO/KToolBox/blob/master/LICENSE) の下で提供されます。

Copyright © 2023 by Ljzd-PRO.
