<div align="center">

# KToolBox

[Pawchive](https://pawchive.pw/) の公開作品をダウンロードする、使いやすい WebUI、CLI、Python クライアントです。

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/ja/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> KToolBox v1 は新しいメジャーバージョンで、実環境での検証はまだ十分ではありません。一部の機能が失敗する可能性があります。問題があれば報告してください。
>
> Kemono が利用できなくなったため、KToolBox は既定でミラーサイト Pawchive を使用します。

## WebUI から始める

WebUI が KToolBox の推奨利用方法です。作品のダウンロード、クリエイター同期、自動同期、命名、フィルター、進捗、プロジェクト設定を、コマンドや設定ファイルを先に覚えずに操作できます。

1. WebUI 付きで KToolBox をインストールします。

    ```bash
    pipx install "ktoolbox[webui]"
    ```

2. プロジェクト用ディレクトリを作成して起動します。

    ```bash
    mkdir ktoolbox-project
    cd ktoolbox-project
    ktoolbox webui .
    ```

3. ブラウザーが自動的に開きます。端末に表示されたユーザー名とランダムパスワードでログインします。
4. **クリエイター**で対象を追加し、**タスク**で同期またはダウンロードを作成します。

`ktoolbox.toml` がなければ自動作成され、既定ではプロジェクト内の `downloads` に保存されます。

![KToolBox WebUI の概要](docs/assets/webui/40-overview-showcase-desktop-light.png)

次は短い [WebUI ガイド](https://ktoolbox.readthedocs.io/latest/ja/webui/)を読むか、[ドキュメントのホーム](https://ktoolbox.readthedocs.io/latest/ja/)から目的を選んでください。

## WebUI でできること

- 単一作品のダウンロードと複数クリエイターの並行同期。
- クリエイター一覧、除外ルール、命名形式、複数の自動同期プランの管理。
- 永続タスク履歴、リアルタイム進捗、総速度、再試行、一時停止、停止、再実行、安全な削除。
- 説明付きフォームと必要箇所だけのパス選択によるプロジェクト設定。
- 7 言語、レスポンシブ表示、明暗テーマ、任意の NSFW メディアプレビュー。
- Codex、Claude、Cursor、VS Code などに接続できる内蔵 MCP サービス。

## 任意の設定

初回は自動生成されたログイン情報で十分です。固定パスワードが必要なら、ハッシュを生成してプロジェクトの `.env` に追加します。

```bash
ktoolbox webui hash-password
```

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

同じ端末だけで使う場合は `--host 127.0.0.1` を指定できます。内蔵サーバーは HTTP のため、遠隔利用では信頼できるネットワークまたは HTTPS リバースプロキシを使用してください。

## 高度な使い方

スクリプトや端末作業には CLI も利用できます。

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
ktoolbox sync fanbox:123 patreon:456 --length 10
```

コマンドは [CLI ガイド](https://ktoolbox.readthedocs.io/latest/ja/commands/guide/)、AI クライアントは [MCP ガイド](https://ktoolbox.readthedocs.io/latest/ja/mcp/)、プログラム連携は [Python API](https://ktoolbox.readthedocs.io/latest/ja/api/)を参照してください。

## v0 からのアップグレード

更新前に `.env`、`prod.env`、既存のダウンロードをバックアップしてください。WebUI は旧命名設定を検出し、設定とディレクトリ変換を案内します。既存プロジェクトでは先に [v1 移行ガイド](https://ktoolbox.readthedocs.io/latest/ja/migration-v1/)を読み、失敗時は[トラブルシューティング](https://ktoolbox.readthedocs.io/latest/ja/faq/)を確認してください。

## 開発

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run mkdocs build --strict
cd webui && npm ci && npm run test && npm run build
```

既定のテストは完全にオフラインで、Pawchive などの外部サービスへ接続してはいけません。

## ライセンス

KToolBox は [BSD 3-Clause License](LICENSE) の下で提供されます。
