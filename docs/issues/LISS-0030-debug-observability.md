# LISS-0030: LLM開発時デバッグ観測性

## Metadata

- Local issue ID: LISS-0030
- Status: done
- Phase: phase-3-refactor
- Type: feature
- Priority: medium
- Related branch: feature/sakana-ollama-interchangeability

## Goal

開発時に、LLM呼び出しのキャッシュ適用状況、トークン使用量、任意設定時の
コスト推定、リトライ経過、通信エラーのスタックトレースを安全に追跡できる
デバッグログを提供する。

## Scope and safety boundary

- CLIに `--debug` と任意の `--log-file` を追加する。
- Manager APIでも `debug=True`、`logger`、`event_sink` を指定できる。
- 成功・リトライ・失敗・完了を相関ID付きの構造化ログで出力する。
- `prompt_cache`、input/output tokens、attempts/retries、request ID、status codeを出力する。
- pricing設定がある場合だけコストを推定し、未設定時は `available: false` とする。
- APIキー、Authorization、全文プロンプト、全文レスポンス、秘密情報はログに出さない。
- デバッグ無効時は通常のCLI出力を変更せず、スタックトレースも出力しない。

## Out of Scope

- providerの料金表を外部から自動取得すること
- ログの永続化・集計基盤・課金確定値の保証
- provider/host/endpointのfallback
- OpenAI/Anthropic実接続テスト

## Acceptance Criteria

- [x] `--debug`で構造化デバッグログをstderrへ出力できる
- [x] `--log-file`指定時に同じログをファイルへ出力できる
- [x] 成功時にprovider/model/response_id/token/cache/attempt/cost情報を追跡できる
- [x] キャッシュ適用なし、適用あり、provider非対応を区別できる
- [x] pricing未設定時にコストを推測せず、利用不可として記録する
- [x] retrying/exhausted/cancelled/errorの状態を追跡できる
- [x] デバッグ有効時のエラーでスタックトレースを出力できる
- [x] ログにAPIキー、Authorization、全文プロンプト、全文レスポンスが含まれない
- [x] 既存テストとFake PortテストがGreenで、実プロバイダ接続を追加しない

## Implementation slices

1. Logging configuration and safe structured event output
2. Usage/cache/cost observability
3. Error stack traces and CLI options
4. Regression tests and documentation

## Follow-up issues

- LISS-0031: production log safety and rotation
- LISS-0032: production observability event contract and correlation
- LISS-0033: production cost policy
- LISS-0034: production debug operations and verification
