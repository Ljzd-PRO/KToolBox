# よくある質問

## アカウントのお気に入りを使えないのはなぜですか？

KToolBox v1 はログイン不要の 14 の Pawchive 操作を実装しています。`cookieAuth` で保護された 5 つの OpenAPI 操作は意図的に除外しているため、API クライアントがアカウントセッションを受け取ったり送信したりすることはありません。

投稿のフラグは別の公開操作として実装されています。成功するとサーバー状態が変わり、すでにフラグ済みの投稿は `PawchiveConflictError` を返す場合があるため、意図して呼び出してください。

## API 呼び出しが失敗したらどうすればよいですか？

CLI は部分的に解析したレスポンスではなく、型付きの Pawchive エラーを報告します。一般的なクラスは、トランスポート、HTTP、認証、未検出、競合、レスポンス検証です。

- URL、または `service`、クリエイター ID、投稿 ID が正しいか確認します。
- 接続が遅い場合は `KTOOLBOX_API__TIMEOUT` を増やします。
- 一時的なトランスポート、`429`、`5xx` の失敗には `KTOOLBOX_API__RETRY_TIMES` と `KTOOLBOX_API__RETRY_INTERVAL` を調整します。
- API 設定にアカウント Cookie を追加しないでください。API リクエストは使用しません。

リダイレクト、通常の `4xx`、競合、無効なレスポンスデータは再試行しません。

## ファイルのダウンロードが 403 を返すのはなぜですか？

特定の資産についてファイルホストがセッションを要求する場合は、ダウンローダー専用キーを設定します。

```dotenv
KTOOLBOX_DOWNLOADER__SESSION_KEY=xxxxx
```

Cookie はファイルダウンロードのリクエストだけに限定され、Pawchive API には送信されません。`.env` と `prod.env` はシークレットを含むローカルファイルとして扱い、コミットしないでください。

## 中断したダウンロードを再開するには？

同じコマンドを再実行します。KToolBox は完成済みの対象ファイルをスキップします。`downloader.temp_suffix` の未完了ファイルがあり、サーバーが範囲に対応していれば、残りのバイトを要求して結合後のサイズを検証します。

## カバーまたは添付ファイルを無効にするには？

```dotenv
# 添付ファイルのみ。
KTOOLBOX_JOB__DOWNLOAD_FILE=False
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True

# カバーのみ。
#KTOOLBOX_JOB__DOWNLOAD_FILE=True
#KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`download_file` はメイン投稿ファイル、通常はカバーを意味します。両方の既定値は `True` です。

## 添付ファイルを投稿ディレクトリに直接保存できますか？

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 長いファイル名を避けるには？

連番名または書式の精度制限を使います。

```dotenv
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}_{title:.30}
KTOOLBOX_JOB__FILENAME_FORMAT={title:.30}_{}
```

## プロキシを設定するには？

HTTPX は標準のプロキシ環境変数を読み取ります。

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5://127.0.0.1:7897
```

PowerShell の場合：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## 設定エディターが開かないのはなぜですか？

オプションのターミナル UI 依存関係をインストールします。

```bash
pip install "ktoolbox[urwid]"
# または
pipx install "ktoolbox[urwid]" --force
```

## 多数のクリエイターを定期的に同期するには？

各クリエイターをプロジェクト一覧に追加し、必要に応じて短いエイリアスを割り当て、対象なしで `sync` を実行します。

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

対象なしの実行に含めず項目を残すには `creator disable` を使います。無効なエイリアスも明示的に同期できます。クリエイター準備とファイル転送には別の並行数制限があるため、大きなクリエイターが準備済みダウンロードを独占しません。

## クリエイターごとに異なる話題を除外するには？

`ktoolbox.toml` に別々の `[[blockers]]` 項目を追加します。全員共通のルールは `scope.mode = "global"`、特定のクリエイターは `scope.mode = "creators"` と正確な `service:id` を使います。ファイル順に評価し、最初の一致で停止します。

長時間の実行前に正規表現とスコープを検証します。

```bash
ktoolbox config validate
```

## リダイレクトしたログで進捗の見え方が違うのはなぜですか？

Rich ライブ進捗は対話的なターミナルだけで使います。各アクティブファイルの速度と ETA、および `Files` 行に全ダウンロードの合計速度を表示します。パイプ、CI、`NO_COLOR`、`--plain` は安定した行出力を使い、ログが ANSI ライブ領域を壊さないようにします。色なしの対話的レイアウトには `--no-color`、進捗と通常ログの抑制には `--quiet` を使います。

## WebUI が起動を拒否するのはなぜですか？

`ktoolbox[webui]` をインストールしてプロジェクトディレクトリを渡します。アカウント設定は省略でき、その場合は今回用の `admin` とランダムパスワードがターミナルに表示されます。明示したハッシュは有効な Argon2 値である必要があります。`ktoolbox.toml` は警告後に自動作成され、プロジェクトロックは同じプロジェクトの 2 つ目のプロセスを拒否します。

## WebUI をネットワークに公開しても安全ですか？

既定のサーバーは平文 HTTP なので、`0.0.0.0` は信頼できる LAN だけで使ってください。ローカルでは `127.0.0.1` にバインドし、リモートでは HTTPS リバースプロキシの背後に置きます。認証、CSRF、厳格な Cookie、レート制限、セキュリティヘッダーはアプリを保護しますが、HTTP 経路を暗号化できません。

## 再起動後の WebUI タスクはどうなりますか？

キュー内のタスクはそのままです。実行中だった作業は設定やリモート状態が変わった可能性があるため、黙って再開せず `interrupted` になります。確認して手動で再開してください。完成済みファイルと再開可能な一時ファイルは残ります。

## WebUI タスクの削除で無関係なファイルが消えますか？

通常の削除はタスク履歴だけを消します。出力の削除はプレビューと確認を求め、資産所有記録とファイルメタデータを確認します。既存、変更済み、共有、非通常ファイル、シンボリックリンクはスキップします。

## 同期が失敗した本当の理由を確認するには？

失敗したタスクを開き、「タスクが失敗した理由」を確認します。KToolBox は対象のクリエイターまたはファイル、失敗段階、再試行の有効性、推奨対応を示します。レスポンス形式の非互換は、Pawchive がフィールド形状を変更した可能性があります。KToolBox を更新し、パネルに表示される安全な操作名とフィールドパスを報告してください。ネットワーク、タイムアウト、レート制限は再試行で解決する場合があります。診断レポートに上流レスポンス本文、作品タイトル、Cookie、完全なダウンロード URL は含まれません。

## uvloop または winloop は必須ですか？

いいえ。オプションのイベントループ最適化です。Linux/macOS では `ktoolbox[uvloop]`、Windows では `ktoolbox[winloop]` を使います。どちらもなければ標準 asyncio ループで続行します。

## パッケージ済み実行ファイルをウイルス対策ソフトが警告するのはなぜですか？

ヒューリスティックスキャンが PyInstaller バンドルやダウンロードマネージャーを警告する場合があります。リリースはリポジトリの公開自動化でビルドされます。`pipx` を使うか、ソースを監査してローカルでビルドすることもできます。
