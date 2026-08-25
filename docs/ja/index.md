# KToolBox へようこそ

KToolBox は Pawchive の公開作品をダウンロードします。推奨される使い方は WebUI です。一般的な操作は案内付きフォームで行え、ページを移動しても進捗を確認できます。

!!! warning "新しいメジャーバージョン"
    v1 は実環境での検証がまだ十分ではなく、一部の機能が失敗する可能性があります。移行前に既存の設定とダウンロードをバックアップし、予期しない動作を報告してください。

## WebUI から始める

1. WebUI 版をインストールします。
2. 同期プロジェクト用のディレクトリを作成します。
3. そのディレクトリで KToolBox を起動します。

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

ブラウザーが自動的に開きます。端末に表示された `admin` とランダムパスワードでログインし、クリエイターを追加して最初のタスクを作成します。必要なら KToolBox が `ktoolbox.toml` を自動作成し、既定では `downloads` に保存します。

![KToolBox WebUI の概要](../assets/webui/40-overview-showcase-desktop-light.png)

## 次の操作を選ぶ

<div class="grid cards" markdown>

-   :material-account-multiple-plus-outline: **クリエイターを追加してダウンロード**

    [プロジェクトの操作](webui/project-workflows.md)に従って、クリエイターの追加、作品検索、タスク作成、除外ルールの調整を行います。

-   :material-progress-download: **タスクを確認**

    [タスクとリアルタイム更新](webui/tasks.md)で、進捗、再試行、一時停止、停止、再実行、安全な削除を確認します。

-   :material-calendar-sync-outline: **定期実行**

    [自動同期ガイド](automatic-sync.md)で繰り返しプランを作成します。

-   :material-folder-cog-outline: **名前とフォルダーを設定**

    [命名形式ガイド](naming.md)で既定の出力先と読みやすい構造を設定します。

</div>

## 高度な入口

通常の初回利用では、以下のページを読む必要はありません。

| 目的 | ガイド |
| --- | --- |
| 固定ログインまたは別端末への配備 | [WebUI 配備リファレンス](webui/reference.md) |
| 端末で自動化 | [CLI ガイド](commands/guide.md)と[コマンドリファレンス](commands/reference.md) |
| すべての設定を確認 | [設定ガイド](configuration/guide.md)と[リファレンス](configuration/reference.md) |
| AI クライアントまたは Python プログラムを接続 | [MCP](mcp.md) と [Python API](api.md) |
| 既存プロジェクトを更新または問題を解決 | [移行ガイド](migration-v1.md)と [FAQ](faq.md) |

## 安全な既定値

WebUI はログイン情報を生成し、センシティブなメディア表示を無効にし、プロジェクト内の出力先を使用します。同じ端末だけで使う場合は `127.0.0.1` にバインドし、信頼できないネットワークでは HTTPS を使用してください。KToolBox は Pawchive のアカウント機能やお気に入り操作を実装しません。
