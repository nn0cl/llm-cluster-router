# LISS-0034: 本番デバッグ運用設定と検証

## Metadata

- Local issue ID: LISS-0034
- Status: done
- Phase: phase-3-refactor
- Type: documentation / operations
- Priority: medium
- Depends on: LISS-0031, LISS-0032, LISS-0033
- Related branch: feature/sakana-ollama-interchangeability

## Goal

運用者が本番で安全にデバッグログを有効化し、障害時に必要な情報を取得し、
不要になったら確実に無効化できる手順を定義する。

## Acceptance Criteria

- [x] CLIのdebug/log-file設定を文書化する
- [x] ローテーションと保持世代数を文書化する
- [x] cache/token/cost/errorの読み方を文書化する
- [x] 本番で本文・秘密情報を収集しない運用を明記する
- [x] OpenAI/Anthropic実接続なしの回帰検証を実施する
