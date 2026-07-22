# 設定ガイド

KToolBox には 2 つの設定レイヤーがあります。

- `.env`、`prod.env`、プロセス変数は API、転送、命名、グローバルなダウンロード動作を制御します。
- `ktoolbox.toml` はプロジェクトのクリエイター一覧と順序付き投稿除外ルールを保存します。

KToolBox は現在の作業ディレクトリから `.env`、次に `prod.env` を読み込みます。`prod.env` の値は `.env` の同じ値を上書きし、プロセス環境変数が最優先です。

ネストしたフィールドは 2 つのアンダースコアでつなぎます。たとえば `KTOOLBOX_API__TIMEOUT` は `config.api.timeout` に対応します。

```dotenv
# Pawchive API リクエスト。
KTOOLBOX_API__TIMEOUT=10
KTOOLBOX_API__RETRY_TIMES=4
KTOOLBOX_API__RETRY_INTERVAL=2

# ファイル転送。
KTOOLBOX_DOWNLOADER__TIMEOUT=30
KTOOLBOX_DOWNLOADER__TPS_LIMIT=5

# ダウンロードジョブ。
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

すべての設定は省略できます。既定値については[設定リファレンス](reference.md)を参照してください。

## 設定を生成または編集

現在のモデルから利用可能な dotenv キーをすべて生成します。

```bash
ktoolbox config example
```

オプションのターミナルエディターは、設定モデルの docstring から解析したフィールド説明を表示できます。

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config edit
```

オプションの [WebUI](../webui.md) は、7 つの対応言語すべてでローカライズされたラベルと説明を型付きコントロールに表示し、最終値の取得元、シークレットのマスク、dotenv/TOML の直接編集、検証、差分プレビュー、ETag 競合保護を提供します。英語の設定 docstring は引き続きフィールドと意味の基準であり、他言語のカタログは全フィールドパスの網羅性を検査します。

エディターを開かずにプロジェクトファイルを確認または検証できます。

```bash
ktoolbox config path
ktoolbox config validate
```

プロジェクトパスの解決順は、グローバル `--config`、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml` です。書き込みには同じディレクトリの一時ファイルとアトミック置換を使い、TomlKit がコメントを保持します。

## クリエイター一覧

各プロジェクト文書は `schema_version = 1` で始まります。クリエイターは大文字小文字を区別しない `service:id` で一意で、オプションのエイリアスも一意です。

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[creators]]
service = "patreon"
creator_id = "456"
alias = "studio-b"
enabled = false
```

単純な一覧項目を手動編集する代わりに、`creator add`、`remove`、`enable`、`disable` を使ってください。対象なしの `sync` はすべての有効な項目を使い、明示したエイリアスや識別子は `enabled` に関係なく実行します。

## 投稿の除外ルール {#post-blockers}

除外ルールは TOML の順番で実行し、最初の一致で投稿を除外します。グローバルルールは同期するすべてのクリエイターに適用し、クリエイタースコープは正確な `service:id` 値を列挙します。無効なルールは設定に残りますが実行しません。

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["life update", "daily note"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["progress|practice"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match` は再帰的な `any`/`all` グループと、グループまたは条件の `negate` に対応します。条件で使える演算子：

| 演算子 | 動作 |
| --- | --- |
| `contains` | 選択したいずれかのスカラーが設定値を含む。 |
| `equals` | 選択したいずれかのスカラーが設定値と等しい。 |
| `regex` | 選択したいずれかのスカラーが正規表現と一致。パターンは設定検証時にコンパイル。 |
| `exists` | 選択したパスが存在して null ではない。`expected = false` で期待を反転。 |

`case_sensitive = true` でない限り、比較は大文字小文字を区別しません。安全なドット区切りパスには `tags[*]`、`file.name`、`attachments[*].name` のような `[*]` リストセレクターを含められます。存在しないパスは一致しません。Python 式や任意のコードは決して評価しません。

除外ルールは、詳細、改訂、ディレクトリ、メタデータ、ダウンロード作業より前に一覧レスポンスを評価します。除外した投稿と改訂はクリエイター索引に入らず、一致したテキストも表示しません。非同期 `PostBlocker` インターフェースとレジストリにより、同期コーディネーターを変更せずに将来のルール型を追加できます。

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` は、廃止予定の暗黙的グローバルタイトル包含ルールとして引き続き受け付けます。KToolBox は自動で書き換えないため、`ktoolbox.toml` に移行してください。

## Pawchive エンドポイント

v1 の既定値は通常変更不要です。

```dotenv
KTOOLBOX_API__SCHEME=https
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__SCHEME=https
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY` は省略可能で、ファイルダウンローダーのリクエストだけに付加されます。アカウントセッションに対応しない `PawchiveClient` が送信することはありません。

## コレクションとパス

dotenv ファイル内の集合とリストには JSON 配列を使います。

```dotenv
KTOOLBOX_JOB__ALLOW_LIST='["*.jpg", "*.png"]'
KTOOLBOX_JOB__BLOCK_LIST='["*.zip", "*.psd"]'
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".zip", ".psd"]'
```

相対的な出力パスとバケットパスは作業ディレクトリから解決します。添付ファイルを各投稿ディレクトリに直接置くには、そのパスを `./` にします。

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 名前テンプレート

投稿とファイルのテンプレートには `id`、`user`、`service`、`title`、`added`、`published`、`edited` を使えます。ファイルテンプレート内の空の `{}` は元または連番の基本ファイル名を表します。

```dotenv
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title:.60}
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title:.60}_{}
KTOOLBOX_JOB__POST_STRUCTURE__FILE={id}_{}
```

`{title:.60}` のような Python 書式指定の精度は、ファイルシステムの長さ制限に役立ちます。

## ダウンロードを制限

サイズ制限の単位はバイトで、ファイルをキューに入れる前に適用します。対応する境界を無効にするには変数を省略します。

```dotenv
# 最小 1 KiB、最大 1 MiB。
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# 投稿のカバーだけを取得し、添付ファイルは取得しない。
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` は同時実行するクリエイタープロデューサーを制御します。`KTOOLBOX_JOB__COUNT` は、すべてのクリエイターが共有するファイルワーカーを個別に制御します。
