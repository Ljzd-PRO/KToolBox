# 設定リファレンス

環境変数名は `KTOOLBOX_` で始まり、ネストしたモデルフィールドを `__` で結びます。`path`、`set`、`list` と示した型は Pydantic が解析します。dotenv 内のコレクションには JSON 配列を使ってください。

## ルート

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `ssl_verify` | 真偽値 | `True` | API とダウンロードリクエストの TLS 証明書を検証。 |
| `json_dump_indent` | 整数 | `4` | JSON 出力のインデント。 |
| `use_uvloop` | 真偽値 | `True` | インストール済みなら Unix で uvloop、Windows で winloop を使用。 |

## `api`

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | API URL スキーム。 |
| `netloc` | 文字列 | `pawchive.pw` | API ホスト。 |
| `statics_netloc` | 文字列 | `pawchive.pw` | 静的クリエイター資産ホスト。 |
| `path` | 文字列 | `/api/v1` | API ルートパス。 |
| `timeout` | 浮動小数点数 | `5.0` | リクエストごとのタイムアウト秒数。 |
| `retry_times` | 整数 | `3` | トランスポート、`429`、`5xx` の失敗時の追加試行回数。 |
| `retry_interval` | 浮動小数点数 | `2.0` | API 試行間の待機秒数。 |

API グループには意図的にセッションキーがありません。

## `downloader`

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | ファイル URL スキーム。 |
| `files_netloc` | 文字列 | `file.pawchive.pw` | Pawchive ファイルホスト。 |
| `file_path_prefix` | 文字列 | `/data` | API ファイルパスに加える接頭辞。 |
| `session_key` | 文字列 | 空 | ファイルリクエストだけに送るオプションの Cookie。 |
| `timeout` | 浮動小数点数 | `30.0` | ファイルリクエストのタイムアウト秒数。 |
| `encoding` | 文字列 | `utf-8` | 名前と抽出テキストのエンコーディング。 |
| `buffer_size` | 整数 | `20480` | バッファー付きファイル I/O のバイト数。 |
| `chunk_size` | 整数 | `1024` | ストリームチャンクのバイト数。 |
| `temp_suffix` | 文字列 | `tmp` | 未完了ダウンロードのサフィックス。 |
| `retry_times` | 整数 | `10` | 追加ダウンロード試行回数。 |
| `retry_stop_never` | 真偽値 | `False` | `retry_times` を無視して永久に再試行。 |
| `retry_interval` | 浮動小数点数 | `3.0` | ダウンロード試行間の待機秒数。 |
| `tps_limit` | 浮動小数点数 | `5.0` | 1 秒あたりの新規接続上限。 |
| `use_bucket` | 真偽値 | `False` | 内容アドレス方式のローカルハードリンク保存を有効化。 |
| `bucket_path` | パス | `.ktoolbox/bucket_storage` | ローカルバケットディレクトリ。 |
| `reverse_proxy` | 文字列 | `{}` | ダウンロード URL テンプレート。`{}` を元 URL で置換。 |
| `keep_metadata` | 真偽値 | `True` | 利用可能なリモート更新メタデータを保持。 |

対象ファイルシステムがハードリンクを作れない場合、バケットモードは自動的に無効になります。

## `job.post_structure`

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `attachments` | パス | `attachments` | 添付ファイルのサブディレクトリ。投稿ルートには `./`。 |
| `content` | パス | `content.txt` | 抽出した内容のファイル。 |
| `external_links` | パス | `external_links.txt` | 抽出した外部リンクのファイル。 |
| `file` | 文字列 | `{id}_{}` | カバーファイルの名前テンプレート。 |
| `revisions` | パス | `revisions` | 改訂のサブディレクトリ。 |

## `job`

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `count` | 整数 | `4` | 同時ダウンロードワーカー数。 |
| `creator_concurrency` | 整数 | `4` | 共有ファイルワーカーへ供給する同時クリエイタープロデューサー数。 |
| `include_revisions` | 真偽値 | `False` | 現在の投稿で既知の改訂をすべて含める。 |
| `post_dirname_format` | 文字列 | `{title}` | 投稿ごとのディレクトリテンプレート。 |
| `mix_posts` | 真偽値 | `False` | 投稿ディレクトリを作らず、全クリエイターファイルを一緒に保存。 |
| `sequential_filename` | 真偽値 | `False` | 添付ファイルを数値順に改名。 |
| `sequential_filename_excludes` | 集合 | 空 | 元の名前を保持する拡張子。 |
| `filename_format` | 文字列 | `{}` | 添付ファイル名テンプレート。 |
| `allow_list` | 集合 | 空 | 含める Unix シェルファイル名パターン。 |
| `block_list` | 集合 | 空 | 除外する Unix シェルファイル名パターン。 |
| `extract_content` | 真偽値 | `False` | 投稿テキストを別に保存。 |
| `extract_content_images` | 真偽値 | `False` | 投稿内容で参照される画像をダウンロード。 |
| `extract_external_links` | 真偽値 | `False` | 内容から一致する外部リンクを保存。 |
| `external_link_patterns` | リスト | 組み込み | 外部リンク抽出用の正規表現。 |
| `group_by_year` | 真偽値 | `False` | 投稿ディレクトリを公開年で分類。 |
| `group_by_month` | 真偽値 | `False` | 月で分類。年での分類が必要。 |
| `year_dirname_format` | 文字列 | `{year}` | 年ディレクトリテンプレート。 |
| `month_dirname_format` | 文字列 | `{year}-{month:02d}` | 月ディレクトリテンプレート。 |
| `keywords` | 集合 | 空 | 含める、大文字小文字を区別しないタイトル用語。 |
| `keywords_exclude` | 集合 | 空 | 廃止予定のタイトル除外。暗黙的グローバルルールに変換。 |
| `download_file` | 真偽値 | `True` | 通常はカバーであるメイン投稿ファイルをダウンロード。 |
| `download_attachments` | 真偽値 | `True` | 添付ファイルをダウンロード。 |
| `min_file_size` | 整数 / 省略 | 省略 | このバイト数より小さいファイルをスキップ。 |
| `max_file_size` | 整数 / 省略 | 省略 | このバイト数より大きいファイルをスキップ。 |

名前テンプレートは `id`、`user`、`service`、`title`、`added`、`published`、`edited` を受け付けます。年と月のテンプレートは `year` と `month` を受け付けます。

## プロジェクトの `ktoolbox.toml`

プロジェクト文書は環境設定とは別です。パスはグローバル `--config`、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml` の順で解決します。

### ルート

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `schema_version` | リテラル `1` | `1` | プロジェクトスキーマバージョン。他の値は拒否。 |
| `creators` | テーブル配列 | 空 | 保存済みクリエイター一覧。 |
| `blockers` | テーブル配列 | 空 | 順序付き除外ルール仕様。 |

### クリエイター項目

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `service` | 空でない文字列 | 必須 | Pawchive サービス。 |
| `creator_id` | 空でない文字列 | 必須 | Pawchive クリエイター ID。 |
| `alias` | 文字列 / 省略 | 省略 | 一意な CLI 対象。`:` は禁止。 |
| `enabled` | 真偽値 | `True` | 対象なしの `sync` に含める。 |

### 除外ルール項目

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `id` | 識別子 | 必須 | 文字、数字、`.`、`_`、`-` に一致する一意な ID。 |
| `type` | 文字列 | `field-match` | 登録済み実装。未知の型は拒否。 |
| `enabled` | 真偽値 | `True` | このルールを評価に含めるか。 |
| `scope.mode` | `global` / `creators` | `global` | グローバルまたは選択した識別子に適用。 |
| `scope.creators` | `service:id` のリスト | 空 | クリエイタースコープでは必須かつ非空、グローバルでは禁止。 |
| `options.rule` | 条件グループ | `field-match` で必須 | ルート再帰ルール。 |

条件グループは `kind = "group"`、`mode = "any"` または `"all"`、空でない `conditions` リスト、オプションの `negate` を使います。フィールド条件は `kind = "field"`、安全なドット区切り `field`、`contains`、`equals`、`regex`、`exists` のいずれか、オプションの `case_sensitive`、`negate`、`expected` を使います。`exists` 以外では空でない `values` リストが必要で、`exists` では `values` を禁止します。

## `webui`

これらの設定は `ktoolbox[webui]` をインストールした場合だけ使い、起動には必須ではありません。空のユーザー名は `admin` になり、両方のパスワードが空ならランダムパスワードを生成し、有効な認証情報をターミナルへ表示してそのプロセス内だけに保持します。

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `host` | 文字列 | `0.0.0.0` | HTTP 待ち受けインターフェース。信頼できる LAN 外では `127.0.0.1` を推奨。 |
| `port` | 整数 | `8789` | 1～65535 の HTTP 待ち受けポート。 |
| `open_browser` | 真偽値 | `True` | 起動後にローカルパネル URL を開く。 |
| `username` | 文字列 | 空 | 任意。空なら起動時に `admin` を使います。 |
| `password_hash` | シークレット文字列 | 空 | 推奨する固定 Argon2id ハッシュ。 |
| `password` | シークレット文字列 | 空 | 平文の代替。両方が空なら起動時に生成します。 |
| `max_active_tasks` | 整数 | `2` | 同時トップレベルタスク数、1～16。 |
| `session_idle_hours` | 整数 | `24` | 最終利用から測るセッション期限。 |
| `session_absolute_hours` | 整数 | `168` | ログインから測る最大セッション期間。 |

すべての名前は通常の接頭辞を使います。例：`KTOOLBOX_WEBUI__PASSWORD_HASH`。`ktoolbox webui hash-password` でハッシュを生成し、Argon2 ハッシュには `$` が含まれるため dotenv では引用符で囲んでください。コマンドラインの `--host`、`--port`、`--no-open` は 1 回の起動について対応する設定を上書きします。

## `logger`

| フィールド | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `path` | パス / 省略 | 省略 | ログファイルパス。省略するとファイルログを無効化。 |
| `level` | 文字列 / 整数 | `DEBUG` | 最小ログレベル。 |
| `rotation` | 文字列 / 整数 / 時間 | `1 week` | Loguru ローテーション条件。 |
