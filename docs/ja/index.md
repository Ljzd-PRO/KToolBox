# KToolBox

KToolBox は公開 [Pawchive](https://pawchive.pw/) データ向けの非同期コマンドラインダウンローダー、HeroUI プロジェクトパネル、型付き Python クライアントです。バージョン 1 が対応するのは Pawchive のみで、Python 3.10～3.14 が必要です。

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

## 次のステップ

- [コマンドガイド](commands/guide.md)
- [WebUI ガイド](webui.md)
- [設定ガイド](configuration/guide.md)
- [Python API](api.md)
- [v1 への移行](migration-v1.md)
- [よくある質問](faq.md)
