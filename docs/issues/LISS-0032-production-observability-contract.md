# LISS-0032: 本番観測イベント契約と相関

## Metadata

- Local issue ID: LISS-0032
- Status: done
- Phase: phase-3-refactor
- Type: architecture / operations
- Priority: high
- Depends on: LISS-0030
- Related branch: feature/sakana-ollama-interchangeability

## Goal

LLM呼び出しを1つの相関単位として追跡でき、ログ基盤や将来のOpenTelemetry
Exporterへ変換可能なイベント契約を提供する。

## Implementation

- correlation_id、trace_id、span_idを生成する。
- provider/model/request ID、operation、状態、試行、duration、token属性を出力する。
- prompt/response content属性は意図的に提供しない。
- event_sinkにも同じ相関情報を渡す。

## Acceptance Criteria

- [x] 1回の実行の全状態イベントが同じcorrelation_idを持つ
- [x] retryごとにspan_idを区別できる
- [x] token/cache情報がprovider-neutralなイベントに含まれる
- [x] OpenTelemetryのtrace/logモデルへ変換可能な命名になっている
- [x] イベントに本文・秘密情報を含めない
