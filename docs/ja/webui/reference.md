# WebUI デプロイリファレンス

最初の安全設定を終えた後、WebUI インスタンスの運用とバックアップにはこのリファレンスを使用してください。

## 情報

情報ページはバージョン、ライセンス、実行環境と公式リンクをまとめます。URL、IP、リッスンアドレスはインラインコードとして表示します。

![暗色のモバイル情報ページ](../../assets/webui/32-about-mobile-dark.png)

## WebUI 環境リファレンス

| 変数 | 既定値 | 意味 |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | 待ち受けインターフェース。 |
| `KTOOLBOX_WEBUI__PORT` | `8789` | 1～65535 の待ち受けポート。 |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | 起動後にローカル URL を開く。 |
| `KTOOLBOX_WEBUI__USERNAME` | 空 → 起動時 `admin` | 任意の単一アカウント名。 |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | 空 | 推奨する固定 Argon2id ハッシュ。 |
| `KTOOLBOX_WEBUI__PASSWORD` | 空 → 起動ごとにランダム | 平文の代替。ハッシュがあれば無視。 |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | 同時最上位タスク、1～16。 |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | 最終利用からのセッション期間。 |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | ログインからの最大セッション期間。 |

タスク履歴が重要な場合は `ktoolbox.toml`、ローカル dotenv、`.ktoolbox/webui.sqlite3` を一緒にバックアップします。WebUI 実行中にデータベースをコピーしないでください。

## 多言語ブラウザ検証

7 つの言語カタログを、デスクトップとモバイルのライト・ダークテーマで実際に検証しています。以下は合格した代表画面です。ユーザー内容とファイルシステムのパスは原文のまま表示されます。

![フランス語のモバイル設定画面](../../assets/webui/24-configuration-mobile-fr.png)

![ロシア語のモバイルリモートパス選択](../../assets/webui/25-path-picker-mobile-ru.png)

## 関連 WebUI ガイド

- [インストールとセキュリティ概要](../webui.md)
- [プロジェクトワークフロー](project-workflows.md)
- [タスクとリアルタイム更新](tasks.md)
- [デプロイリファレンス](reference.md)
