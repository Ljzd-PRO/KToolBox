# コマンドリファレンス

正式な Cyclopts ヘルプは `ktoolbox COMMAND --help` で確認してください。コマンドとオプション名はハイフンを使います。旧アンダースコア表記も非表示の互換コマンドでは解析されます。

## グローバルオプション

| オプション | 意味 |
| --- | --- |
| `-h`, `--help` | ページャーを使わず直接ヘルプを表示。 |
| `--version` | インストール済みの KToolBox バージョンを表示。 |
| `--install-completion` | 検出したシェル用の補完をインストール。 |
| `--config PATH` | プロジェクトファイルを選択。解決順はこのオプション、`KTOOLBOX_PROJECT_CONFIG`、`./ktoolbox.toml`。 |
| `--verbose` | 診断ログを含める。 |
| `--quiet` | 進捗と通常ログを抑制。 |
| `--plain` | 安定した行単位の進捗を強制。非 TTY 出力と `NO_COLOR` では自動的に使用。 |
| `--no-color` | ANSI 色を無効化。 |

引数なしで `ktoolbox` を実行するとルートヘルプを表示し、正常終了します。

## コマンドツリー

| コマンド | 用途 |
| --- | --- |
| `download` | 1 件の投稿または選択した改訂をダウンロード。 |
| `sync [TARGET ...]` | 明示したクリエイターを同期。対象がなければ有効な一覧クリエイターをすべて同期。 |
| `creator list/add/remove/enable/disable/search` | 一覧の管理または Pawchive クリエイターの検索。 |
| `post show/search` | 投稿の確認またはクリエイター投稿の検索。 |
| `config edit/example/validate/path` | 環境とプロジェクト設定の編集または確認。 |
| `site-version` | Pawchive アプリケーションバージョンを表示。 |
| `webui [PROJECT_DIR]` | 1 つのプロジェクト用にオプションの HeroUI パネルを実行。 |

## `download`

Pawchive 投稿 URL、または `--service`、`--creator-id`、`--post-id` のすべてを指定します。

| 引数またはオプション | 型 | 既定値 | 意味 |
| --- | --- | --- | --- |
| `POST` | 文字列 | 省略 | Pawchive 投稿または改訂 URL。 |
| `--service` | 文字列 | 省略 | クリエイターのサービス。 |
| `--creator-id` | 文字列 | 省略 | クリエイター ID。 |
| `--post-id` | 文字列 | 省略 | 投稿 ID。 |
| `--revision-id` | 文字列 | 省略 | 改訂一覧からこの改訂を選択。 |
| `-o`, `--output`, `--path` | パス | `.` | 出力ルート。 |
| `--dump-post-data` / `--no-dump-post-data` | 真偽値 | 有効 | 検証済みメタデータを `post.json` に保存。 |

`download` は意図的に一覧の除外ルールを適用しません。

## `sync`

各 `TARGET` は Pawchive クリエイター URL、`service:id`、一覧エイリアスのいずれかです。明示した対象は一覧で無効でも実行します。対象がなければ、有効な一覧クリエイターをすべて実行します。

| 引数またはオプション | 型 | 既定値 | 意味 |
| --- | --- | --- | --- |
| `TARGET ...` | 文字列 | 有効な一覧 | 0 人以上のクリエイター。 |
| `--service` + `--creator-id` | 文字列 | 省略 | 1 人の明示的クリエイターを追加。両方を同時に指定。 |
| `-o`, `--output`, `--path` | パス | `.` | 出力ルート。 |
| `--save-creator-indices` | 真偽値 | 無効 | 生成成功後、クリエイター索引をアトミックに保存。 |
| `--mix-posts` / `--no-mix-posts` | 真偽値 | 環境設定 | `job.mix_posts` を上書き。 |
| `--start-time`, `--start` | 日付 | 省略 | 公開日の包含下限、`YYYY-MM-DD`。 |
| `--end-time`, `--end` | 日付 | 省略 | 公開日の包含上限、`YYYY-MM-DD`。 |
| `--offset` | 整数 | `0` | 最初の投稿インデックス。 |
| `--length` | 整数 | すべて | クリエイターごとに受け入れる最大投稿数。 |
| `--keywords` | 繰り返し文字列 | 環境設定 | いずれかの値を含むタイトルを採用。 |
| `--keywords-exclude` | 繰り返し文字列 | 環境設定 | 廃止予定のタイトル除外互換入力。 |

`job.creator_concurrency` はクリエイター生成を、`job.count` は共有ファイルワーカーを制限します。

## `creator`

| コマンド | 引数とオプション | 意味 |
| --- | --- | --- |
| `creator list` | `--json` | 一覧項目を Rich テーブルまたは JSON で表示。 |
| `creator add TARGET` | `--alias NAME`, `--disabled` | URL または `service:id` を追加。 |
| `creator remove TARGET` | | エイリアス、URL、識別子で削除。 |
| `creator enable TARGET` | | 保存済みクリエイターを有効化。 |
| `creator disable TARGET` | | 保存済みクリエイターを無効化。 |
| `creator search` | `--name`, `--creator-id`/`--id`, `--service`, `--dump`, `--json` | 公開クリエイター一覧を絞り込み。 |

## `post`

| コマンド | 引数とオプション | 意味 |
| --- | --- | --- |
| `post search` | `--creator-id`/`--id`, `--name`, `--service`, `-q`/`--query`, `-o`/`--offset`, `--dump`, `--json` | 選択したクリエイターの投稿を検索。直接 API クエリは 3 文字以上、API オフセットは 50 で割り切れる値。 |
| `post show SERVICE CREATOR_ID POST_ID [REVISION_ID]` | `--dump`, `--json` | 現在の投稿メタデータまたは選択した改訂を表示。 |

`--json` がない場合、検索コマンドは意図的にターミナル表から投稿本文を省略します。

## `config`

| コマンド | 意味 |
| --- | --- |
| `config path` | 解決済みプロジェクトパスを折り返さず表示。 |
| `config validate` | スキーマバージョン、クリエイターの一意性、除外ルールの型、スコープ、条件、正規表現を検証。 |
| `config example` | 設定モデルの docstring から全 dotenv 設定を生成。 |
| `config edit` | オプションの Urwid エディターを開き、保存前に検証。 |

## `webui`

これらのコマンドを使う前に `ktoolbox[webui]` をインストールしてください。既定のコマンドはプロジェクトディレクトリを受け取り、`ktoolbox.toml` がない場合は警告後に作成します。有効な単一アカウントの認証情報は必要です。

| 引数またはオプション | 既定値 | 意味 |
| --- | --- | --- |
| `PROJECT_DIR` | `.` | このプロセスが提供する固定同期プロジェクト。 |
| `--host` | `webui.host` | 待ち受けインターフェースを上書き。 |
| `--port` | `webui.port` | TCP ポートを上書き。 |
| `--no-open` | 無効 | 既定のブラウザでローカル URL を開かない。 |
| `webui hash-password` | | 非表示のターミナル入力で 2 回確認し、Argon2id ハッシュを表示。 |

内蔵サーバーは HTTP セキュリティ警告を表示します。localhost の外へ公開する前に [WebUI ガイド](../webui.md)を参照してください。

## 互換エイリアス

次のエイリアスはヘルプに表示されず、呼び出しごとに廃止警告を 1 回発行します。

| 旧名称 | 置き換え |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

## 終了コードとストリーム

| コード | 意味 |
| --- | --- |
| `0` | 成功。 |
| `1` | リモート、クリエイター、ダウンロードの失敗。複数クリエイターの部分成功を含む。 |
| `2` | 無効な引数または設定。 |
| `130` | ユーザーによる中断。 |

テーブルと JSON は stdout を使います。ログ、進捗、警告、エラーは stderr を使います。
