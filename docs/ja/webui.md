# WebUI

WebUI は KToolBox の推奨利用方法です。1 つの同期プロジェクトの設定、タスク、進捗、履歴をブラウザー画面にまとめます。

## 初回起動

WebUI 版をインストールし、プロジェクト用ディレクトリを作成して KToolBox を起動します。

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

ブラウザーが自動的に開きます。端末に表示された `admin` とランダムパスワードでログインしてください。`ktoolbox.toml` がなければ KToolBox が作成し、新しいタスクは既定でプロジェクトの `downloads` を使います。

![KToolBox WebUI の概要](../assets/webui/40-overview-showcase-desktop-light.png)

## 最初の同期

1. **クリエイター**を開き、**クリエイターを追加**を選びます。
2. Pawchive のクリエイター URL を貼り付けるか、プラットフォームと ID を入力します。
3. **タスク**を開き、**タスクを作成**から **クリエイターを同期**を選びます。
4. 新しいクリエイターと命名形式を確認する間は、最初の件数を少なくします。
5. タスクを開き、ダウンロード、速度、再試行、有用なアクティビティを確認します。

完了したファイルは保持され、互換性のある一時ファイルは再開できます。1 人のクリエイターが失敗しても、同じタスクで成功したダウンロードは削除されません。

## 目的別の続き

<div class="grid cards" markdown>

-   :material-folder-account-outline: **クリエイター、作品、除外、命名**

    日常の管理には[プロジェクトの操作](webui/project-workflows.md)を使います。

-   :material-progress-download: **進捗とタスク操作**

    一時停止、停止、再実行、診断、安全な削除は[タスクとリアルタイム更新](webui/tasks.md)を参照してください。

-   :material-server-security: **アカウントと配備**

    固定認証情報、遠隔アクセス、バックアップ、詳細な安全動作が必要な場合だけ[配備リファレンス](webui/reference.md)を使います。

-   :material-update: **既存の v0 プロジェクト**

    古い設定やダウンロードを変換する前に[移行ガイド](migration-v1.md)を読んでください。

</div>

## 任意の固定ログイン

初回は生成された認証情報で十分です。再起動後も同じログインを使う場合はパスワードハッシュを作成します。

```bash
ktoolbox webui hash-password
```

結果をプロジェクトの `.env` に追加します。

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

## 安全なアクセス

内蔵サーバーは HTTP を使用します。同じコンピューターだけで使う場合は `127.0.0.1` にバインドします。

```bash
ktoolbox webui . --host 127.0.0.1
```

遠隔アクセスには信頼できるネットワークまたは HTTPS リバースプロキシを使用してください。ログインできる利用者はプロジェクトのパス、設定、タスクログを確認できるため、信頼できない相手には公開しないでください。同じプロジェクトを同時に管理できる WebUI プロセスは 1 つだけです。
