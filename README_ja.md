<div align="center">

# KToolBox

[Pawchive](https://pawchive.pw/) の公開投稿をダウンロードするための、非同期 CLI、HeroUI 管理パネル、Python クライアントです。

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/ja/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

KToolBox v1 が対応するバックエンドは Pawchive のみです。Pawchive OpenAPI 文書に含まれるすべての公開操作へ型付きでアクセスでき、アカウント認証が必要なお気に入り操作は対象外です。

## 機能

- 1 件の投稿をダウンロード、または任意の数のクリエイターを 1 つのコマンドで同期。
- プロジェクト内の `ktoolbox.toml` で、再利用可能かつ有効・無効を切り替えられるクリエイター一覧を管理。
- 順序付きのグローバルまたはクリエイター単位のフィールド除外ルールで、作品ではない投稿を除外。
- 複数の API 操作で、型付き非同期 `PawchiveClient` を再利用。
- HTTP Range による未完了ダウンロードの再開と、既存ファイルのスキップ。
- ファイルサイズ、拡張子、タイトル、日付による絞り込みと、カバー・添付ファイルの個別制御。
- ディレクトリ構造、投稿名、ファイル名、連番、年月グループをカスタマイズ。
- 投稿メタデータ、クリエイター索引、抽出本文、本文画像、一致する外部リンクを保存。
- 複数クリエイターから並行生成されるジョブを公平な 1 つのダウンロードプールへ流し、ファイル別速度と総スループットを安定した Rich 進捗表示に出力。
- 7 言語対応のレスポンシブな HeroUI パネルで、永続タスク、リアルタイム進捗、設定フォーム、クリエイター・除外ルール編集、ライト・ダークテーマを備えた 1 つの同期プロジェクトを管理。
- MockTransport ベースで完全にオフラインのテストスイートを使用し、意図しないネットワークアクセスを禁止。

## 動作要件

- Python 3.10～3.14
- Windows、macOS、Linux

## インストール

`pipx` の使用を推奨します。

```bash
pipx install ktoolbox
```

イベントループ最適化とターミナル設定エディターのオプション依存関係：

```bash
# Windows
pipx install "ktoolbox[urwid,winloop]" --force

# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force
```

オプションの WebUI ランタイムをインストール：

```bash
pipx install "ktoolbox[webui]" --force
```

## クイックスタート

コマンドのヘルプを表示：

```bash
ktoolbox -h
ktoolbox download -h
```

![KToolBox コマンドの概要](docs/assets/cli-overview.png)

1 件の投稿をダウンロード：

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
```

初回を 1 件の投稿に制限して 1 人のクリエイターを同期：

```bash
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

オフセット、日付範囲、タイトルフィルターを使用：

```bash
ktoolbox sync fanbox:123 patreon:456 --length 10
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

頻繁に同期するクリエイターを保存し、対象を指定せずに `sync` を実行：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

再実行時には既存ファイルをスキップします。ファイルホストが Range に対応していれば、未完了の一時ファイルからダウンロードを再開します。

## WebUI

WebUI は `ktoolbox.toml` を含む 1 つのプロジェクトディレクトリに固定されます。単一アカウントを、できれば Argon2id ハッシュで設定してください。

```bash
ktoolbox webui hash-password
```

出力されたハッシュとユーザー名をプロジェクトの `.env` に追加し、パネルを起動します。

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

```bash
ktoolbox webui /path/to/project
```

![KToolBox WebUI の設定](docs/assets/webui/09-configuration-light.png)

インターフェイス全体は、簡体字中国語、繁体字中国語、英語、日本語、韓国語、フランス語、ロシア語に対応します。初回はブラウザ言語に従い、手動選択は保存され、日付、数値、並べ替え、設定説明、入力検証、サーバーエラーも同時に切り替わります。

タスク行は、オフライン表示スナップショット内に読みやすい投稿タイトルとクリエイター名を保持します。デスクトップとモバイルのレイアウトから詳細、ライフサイクル、編集、並べ替え、削除を直接操作でき、フォームのスイッチはオフ時がグレー、オン時がブルー、チェックボックスは選択時だけ印を表示します。

失敗したタスクには、対象クリエイターまたはファイル、再試行の可否、安全なフィールドパス、推奨対応を含む、段階別で秘匿化されたレポートが残ります。コンパクトなモバイル画面は 64px のワークバーと 12px のページ余白を使い、外観操作を小さな Popover にまとめ、MCP ツール一覧をカテゴリ別に折りたたみます。

ログイン後は 1 本の SSE 接続だけで、タスク、クリエイター、除外ルール、設定、MCP トークン、開いているリモートディレクトリをタブ間で自動同期します。切断時はローカルデータだけを 10 秒ごとに更新し、Pawchive 検索や作品詳細はポーリングしません。未保存のフォーム下書きも外部更新から保護されます。

既定の `0.0.0.0:8789` リスナーは信頼できる LAN では便利ですが、HTTP は認証情報やプロジェクトデータの通信を保護しません。信頼できないネットワークでは `127.0.0.1` にバインドするか、HTTPS リバースプロキシの背後に配置してください。既定のアカウントはなく、有効な認証情報を設定するまで起動に失敗します。タスクのライフサイクル、セキュリティ、デプロイについては [WebUI ガイド](https://ktoolbox.readthedocs.io/latest/ja/webui/) を参照してください。

## 設定

KToolBox は現在の作業ディレクトリから `.env`、次に `prod.env` を読み込みます。ネストしたフィールドには `__` を使用します。

```dotenv
# Pawchive の既定値。通常は変更不要です。
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data

# ダウンロード制御。
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY` を設定した場合、その値はファイルのダウンロードだけに送信されます。API クライアントがアカウントセッションを送信することはありません。

`.env` はランタイムと転送動作を制御し、プロジェクト単位の `ktoolbox.toml` はクリエイター一覧と除外ルールを保存します。

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[blockers]]
id = "skip-progress-updates"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["進捗報告"] }] } }
```

設定リファレンスの生成、プロジェクトファイルの検証、オプションのターミナルエディターの起動：

```bash
ktoolbox config example
ktoolbox config validate
ktoolbox config edit
```

詳しくは[設定ガイド](https://ktoolbox.readthedocs.io/latest/ja/configuration/guide/)と [`example.env`](example.env) を参照してください。

## Python API

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

成功した呼び出しは Pydantic v2 モデルを返します。トランスポート、HTTP ステータス、認証、未検出、競合、レスポンス検証の失敗には、それぞれ異なる例外クラスが使われます。[API ドキュメント](https://ktoolbox.readthedocs.io/latest/ja/api/)も参照してください。

## v0 からの移行

v1 では Kemono/Coomer 互換レイヤーと、旧 `BaseAPI`、モジュールレベルの `get_*`、`APIRet`、ラップされたレスポンスの各インターフェースを削除しました。Fire コマンドは Cyclopts に置き換えられたため、`download`、`sync`、`creator`、`post`、`config` を使用してください。非表示の旧エイリアスは廃止警告付きで一時的に利用できます。`KTOOLBOX_API__SESSION_KEY` を `KTOOLBOX_DOWNLOADER__SESSION_KEY` へ移し、[v1 移行ガイド](https://ktoolbox.readthedocs.io/latest/ja/migration-v1/)を確認してください。

過去の `kemono_openapi.json` は参照用としてリポジトリに残されていますが、サポート対象のランタイム契約ではありません。

## 開発

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run ruff check k_generator ktoolbox/api ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py tests
poetry run mypy --strict ktoolbox/api/client.py ktoolbox/api/errors.py ktoolbox/api/parameters.py ktoolbox/api/utils.py ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py
poetry run mkdocs build --strict
cd webui && npm ci && npm run typecheck && npm run lint && npm run test && npm run build && npm run test:e2e
```

既定のテストは完全にオフラインであり、Pawchive やその他のリモートサービスへ接続してはいけません。

## ライセンス

KToolBox は [BSD 3-Clause License](LICENSE) の下で提供されます。
