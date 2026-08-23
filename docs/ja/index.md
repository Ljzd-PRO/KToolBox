# KToolBox

KToolBox は公開 [Pawchive](https://pawchive.pw/) データ向けの非同期コマンドラインダウンローダー、HeroUI プロジェクトパネル、型付き Python クライアントです。バージョン 1 が対応するのは Pawchive のみで、Python 3.10～3.14 が必要です。

!!! warning "v1 は新しいメジャーバージョンです"
    このリリース系列は、まだ十分な実利用検証を受けていません。まず範囲を制限したダウンロードを行い、既存設定をバックアップして、想定外の動作を報告してください。Kemono が利用できなくなったため、KToolBox は既定で Pawchive ミラーを使用します。

## 利用方法を選ぶ

<div class="grid cards" markdown>

-   :material-console-line: **コマンドラインから始める**

    KToolBox をインストールし、範囲を制限したダウンロードを 1 回実行してから[コマンドガイド](commands/guide.md)へ進みます。

-   :material-view-dashboard-outline: **ブラウザでプロジェクトを管理する**

    オプションのパネルをインストールし、[WebUI ガイド](webui.md)に沿ってログイン、セキュリティ、タスク、プロジェクト設定を確認します。

-   :material-update: **v0 からアップグレードする**

    古い dotenv ファイルをバックアップし、既存ダウンロードを変更する前に [v1 への移行](migration-v1.md)を確認します。

-   :material-calendar-sync: **クリエイターを定期更新する**

    先に一覧を作成し、[自動同期](automatic-sync.md)で定期チェックを設定します。

</div>

## 主な機能

- 1 件の投稿をダウンロード、またはクリエイター一覧を並行して同期。
- ダウンロード作業を作成する前に、順序付きのグローバルまたはクリエイター単位の除外ルールを適用。
- 部分ファイルの再開と、既存ファイルのスキップ。
- 日付、タイトル、ファイル名パターン、ファイルサイズで絞り込み。
- カバー、添付ファイル、本文画像、メタデータ、外部リンクの出力を個別に制御。
- プロジェクト設定、クリエイター一覧と除外ルールの編集、Pawchive 検索、タスクのライフサイクル制御に使える、7 言語対応の永続 WebUI。
- 検証済み Pydantic モデルで Pawchive OpenAPI の 14 の公開操作をすべて提供。

アカウント認証が必要なお気に入り操作は意図的に実装していません。ダウンローダーのセッションキーを設定しても、ファイルホストだけに送信されます。

## インストール

`pipx` を使うとアプリケーションを分離できます。

```bash
pipx install ktoolbox
```

オプションのターミナルエディターと最適化されたイベントループをインストール：

```bash
# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force

# Windows
pipx install "ktoolbox[urwid,winloop]" --force
```

必要な場合はブラウザパネルを別途インストール：

```bash
pipx install "ktoolbox[webui]" --force
```

## クイックスタート

```bash
# コマンドとオプションを確認。
ktoolbox -h
ktoolbox download -h

# 1 件の投稿をダウンロード。
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

# 広い範囲を同期する前に、まず 1 件の投稿から開始。
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

![KToolBox コマンドの概要](../assets/cli-overview.png)

複数のクリエイターを保存し、有効な項目をすべて同期：

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

再実行時には既存ファイルをスキップします。設定された一時サフィックスを持つ未完了ファイルは、ファイルサーバーがバイト範囲に対応していれば再開されます。

`--output` を指定しない場合、ダウンロードはプロジェクトの既定場所を使用します。設定を変更していなければ、プロジェクト内の `downloads` です。

## ドキュメントマップ

| 目的 | 読むページ |
| --- | --- |
| 日常的なコマンドを学ぶ | [コマンドガイド](commands/guide.md)と[コマンドリファレンス](commands/reference.md) |
| ブラウザパネルを実行する | [WebUI ガイド](webui.md) |
| 定期チェックを設定する | [自動同期](automatic-sync.md) |
| ディレクトリとファイル名を制御する | [命名形式](naming.md) |
| すべての設定を理解する | [設定ガイド](configuration/guide.md)と[設定リファレンス](configuration/reference.md) |
| 別のアプリケーションを接続する | [MCP](mcp.md)または [Python API](api.md) |
| アップグレードまたは問題を解決する | [v1 への移行](migration-v1.md)と[よくある質問](faq.md) |
