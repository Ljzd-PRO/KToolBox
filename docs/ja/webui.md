# WebUI

KToolBox WebUI は React と HeroUI で構築された、プロジェクトに結び付く管理パネルです。CLI と同じ設定を編集し、同じ Python サービスを呼び出します。CLI サブプロセスの起動や解析はしません。タスク、試行、ログ、所有記録は選択したプロジェクト内の `.ktoolbox/webui.sqlite3` に永続化されます。

## 目的別に読み進める

<div class="grid cards" markdown>

-   :material-arrow-right-circle-outline: **プロジェクトデータを管理**

    [プロジェクトワークフロー](webui/project-workflows.md)でクリエイター、作品、命名、設定、任意のメディアを管理します。

-   :material-arrow-right-circle-outline: **ダウンロードを監視**

    [タスクとリアルタイム更新](webui/tasks.md)で作成、診断、一時停止、再開、再実行、安全な削除を行います。

-   :material-arrow-right-circle-outline: **デプロイと保守**

    [デプロイリファレンス](webui/reference.md)で環境変数、バックアップ、ランタイム、多言語対応を確認します。

</div>

## インストールと起動

オプションのランタイムをインストールし、プロジェクトディレクトリを作成します。

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

起動時の認証情報は省略できます。未設定の場合、そのプロセスで使う `admin` と新しいランダムパスワードがターミナルに表示されます。固定の認証情報には、非表示入力で Argon2id ハッシュを生成します。

```bash
ktoolbox webui hash-password
```

アカウントをプロジェクトの `.env` に保存します。シェル形式の `$` をそのまま残すため、ハッシュを引用符で囲みます。

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

プロジェクト用パネルを起動します。

```bash
ktoolbox webui .
ktoolbox webui . --host 127.0.0.1 --port 8789 --no-open
```

既定値は `0.0.0.0:8789` で、ローカルブラウザが自動で開きます。`--host`、`--port`、`--no-open` はそのプロセスの環境設定を上書きします。`ktoolbox.toml` がない場合は、警告を表示して最小の有効な文書をアトミックに作成します。認証情報がなくても起動でき、空のユーザー名は `admin`、両方のパスワードが空なら今回用の新しいパスワードを生成してターミナルに表示します。

## セキュリティモデル

KToolBox のローカル WebUI アカウントは 1 つです。明示設定が優先され、`KTOOLBOX_WEBUI__PASSWORD_HASH` は平文の `KTOOLBOX_WEBUI__PASSWORD` より優先されます。どちらも未設定なら起動ごとにメモリ上でパスワードを生成し、有効なユーザー名とともにそのターミナルだけへ表示します。安定運用ではハッシュを設定し、両 dotenv ファイルをバージョン管理から除外してください。

セッションはランダムな不透明トークンを使います。SQLite はトークンハッシュだけを保存します。ブラウザ Cookie は `HttpOnly` と `SameSite=Strict` で、HTTPS では `Secure` になります。変更リクエストにはセッション別 CSRF トークンと同一オリジン確認が必要です。ログイン試行はレート制限され、API レスポンスはキャッシュされず、厳格なコンテンツ、フレーム、リファラー、ブラウザ権限ヘッダーを送信します。

内蔵サーバーは HTTP を使います。既定の LAN リスナーは信頼できるネットワーク専用で、そうでなければパスワード、Cookie、パス、ログ、設定が通信中に見えます。1 台では `--host 127.0.0.1`、リモートでは信頼できるリバースプロキシで HTTPS を終端し、ネットワークアクセスを制限してください。安全でないページではログインページとアプリシェルに HTTP 警告が残ります。

同時に 1 つのスケジューラーだけがプロジェクトを開けます。プロジェクトロックが 2 つの WebUI プロセスによるキューと出力の競合を防ぎます。
