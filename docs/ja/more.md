# プロジェクト情報

## リリース状況

KToolBox v1 は Pawchive を基盤とする新しいリリース系列です。v0 からの破壊的なアップグレードであり、まだ十分な実利用検証を受けていないため、大規模同期に依存する前に範囲を制限したダウンロードを試してください。既存環境を更新する場合は [v1 への移行](migration-v1.md)から始めます。

Kemono は利用できなくなり、Pawchive が唯一の対応バックエンドです。生成クライアントの変更を正規化済み契約と比較できるよう、元の Pawchive OpenAPI ファイルは変更しません。

## サポートとリソース

ドキュメントサイトを離れる前に、サイト内検索と[よくある質問](faq.md)を使用してください。答えがない場合は、目的が明確な次の外部リンクを利用できます。

- 再現可能な不具合は [Issue トラッカー](https://github.com/Ljzd-PRO/KToolBox/issues)へ報告します。
- 質問や提案は [Discussions](https://github.com/Ljzd-PRO/KToolBox/discussions)に投稿します。
- 公開ノートと成果物は [Releases](https://github.com/Ljzd-PRO/KToolBox/releases)で確認します。
- コードと貢献履歴は[ソースリポジトリ](https://github.com/Ljzd-PRO/KToolBox)で確認します。

## 品質とライセンス

既定のテストスイートは完全にオフラインで、意図しないネットワークアクセスを禁止します。CI は OpenAPI 契約、決定的な生成、テスト、Ruff、Mypy、Python バイトコード、パッケージ成果物、WebUI ビルド、厳格な MkDocs ビルドを検証します。

KToolBox は [BSD 3-Clause License](https://opensource.org/license/bsd-3-clause) の下で提供されます。Copyright © 2023 by Ljzd-PRO.
