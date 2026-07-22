# v1 への移行

KToolBox v1 は、バックエンドとライブラリ API に互換性のない変更を含むリリースです。

## アップグレード前

1. `.env` または `prod.env` をバックアップします。
2. 実行中の v0 ダウンロードを完了またはキャンセルします。
3. 完全な同期の前に、`--length=1` を指定して 1 人のクリエイターを試します。

## 必要な変更

| v0 の動作 | v1 の動作 |
| --- | --- |
| Kemono/Coomer エンドポイント | Pawchive のみ |
| Python 3.8+ | Python 3.10-3.14 |
| `KTOOLBOX_API__SESSION_KEY` | `KTOOLBOX_DOWNLOADER__SESSION_KEY` |
| API 設定に API とファイルホストが混在 | API と静的ホストは `api`、ファイルホストは `downloader` |
| 改訂詳細リクエスト | 改訂一覧を取得し、`revision_id` で選択 |
| `.data.post` などのラッパーレスポンス | 型付き `Post`、`Revision`、その他の Pydantic モデルを直接返す |
| Python Fire のコマンド画面 | ハイフン区切りオプションと明示的な終了コードを持つ Cyclopts コマンドツリー |
| 同期ごとに 1 人のクリエイター | 任意の数の対象、または有効なプロジェクト一覧 |
| グローバルな `keywords_exclude` のみ | 順序付きのグローバルおよびクリエイター単位の `field-match` 除外ルール |

新しい既定値は次のとおりです。

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

## CLI コマンド

非表示のエイリアスにより既存の自動化は一時的に動作しますが、呼び出すたびに廃止警告が表示されます。

| v0 コマンド | v1 コマンド |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

オプションは Python 風のアンダースコアではなく `--creator-id` と表示されます。互換エイリアスでは旧アンダースコア表記も引き続き受け付けます。ヘルプは直接表示され、ページャーを終了する必要はありません。

CLI の失敗はプロセスステータスを使います。`0` は成功、`1` はリモート・クリエイター・ダウンロードの失敗、`2` は引数・設定の失敗、`130` は中断です。JSON と表は stdout、進捗とログは stderr を使います。

## プロジェクト一覧と除外ルール

再利用可能な一覧や構造化された除外ルールが必要な場合にだけ `ktoolbox.toml` を作成してください。ファイルがない状態は有効な空のプロジェクトです。

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true
```

空でない `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` の値は、グローバルな `field-match` タイトル条件へ移してください。旧設定は暗黙の除外ルールとして引き続き動作して警告を表示しますが、KToolBox がローカルファイルを書き換えることはありません。[設定ガイド](configuration/guide.md#post-blockers)を参照してください。

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` の既定値は `4` で、クリエイターのプロデューサー数を制限します。既存の `KTOOLBOX_JOB__COUNT` は引き続きファイルワーカー数を制限します。

## オプションの WebUI

v1 には新しい HeroUI パネルが追加されます。過去の実験的な `webui` ブランチは移行も再利用もしません。`ktoolbox[webui]` をインストールしてプロジェクトを選びます。`ktoolbox.toml` は警告後に自動作成されます。アカウント未設定なら毎回 `admin` と新しいランダムパスワードを表示し、固定認証情報が必要な場合だけ単一アカウントを設定します。

```bash
ktoolbox webui hash-password
ktoolbox webui /path/to/project --host 127.0.0.1
```

`.env` と `prod.env` は、バージョン管理された例ではなく、無視されるローカルファイルになりました。認証情報とダウンローダーのセッションはここに保存し、公開テンプレートには `example.env` を使い、アップグレード前に以前追跡していた dotenv ファイルを監査してください。WebUI は `.ktoolbox/webui.sqlite3` とプロジェクトロックを作成しますが、どちらも CLI のダウンロード出力形式を変更しません。

HTTP デプロイの危険性と永続タスクの動作については [WebUI ガイド](webui.md)を参照してください。

## ライブラリ API

旧 `BaseAPI`、クラス呼び出し機構、モジュールレベルの `get_*` 関数、`APIRet`、Kemono レスポンスラッパーは、互換エイリアスなしで削除されました。インスタンス化した非同期クライアントを使用してください。

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        posts = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(posts))


asyncio.run(main())
```

成功した呼び出しは Pydantic v2 モデルを返します。失敗時は型付きの `PawchiveError` サブクラスが発生します。[API ドキュメント](api.md)も参照してください。
