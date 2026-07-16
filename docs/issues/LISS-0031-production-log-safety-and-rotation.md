# LISS-0031: 本番ログの安全性と容量制御

## Metadata

- Local issue ID: LISS-0031
- Status: done
- Phase: phase-3-refactor
- Type: security / operations
- Priority: high
- Depends on: LISS-0030
- Related branch: feature/sakana-ollama-interchangeability

## Goal

本番プロセスでデバッグ観測を有効化しても、秘密情報を漏えいさせず、
ログ容量とログ出力障害を制御できるようにする。

## Implementation

- サイズ上限と世代数を持つ `RotatingFileHandler` を使う。
- ログファイル初期化・書込み失敗はLLM呼び出しを失敗させずstderrへ継続する。
- URLのquery/fragment、認証情報、エラー本文をログへ出さない。
- プロンプト・レスポンス本文をログイベント契約から除外する。

## Acceptance Criteria

- [x] ログファイルのサイズとバックアップ世代数が設定できる
- [x] CLIからログファイルのサイズとバックアップ世代数を設定できる
- [x] ローテーション後の総容量が設定値で上限管理される
- [x] ログ出力失敗でprovider呼び出しが失敗しない
- [x] URL query/fragment、認証情報、本文がログに出ない
- [x] ログファイルを所有者のみ読み書きできる権限で作成する
- [x] Fake Portによる秘匿性・ローテーションテストがある
