# LISS-0033: 本番コスト観測ポリシー

## Metadata

- Local issue ID: LISS-0033
- Status: done
- Phase: phase-3-refactor
- Type: operations / finance
- Priority: high
- Depends on: LISS-0030
- Related branch: feature/sakana-ollama-interchangeability

## Goal

LLM利用量とコスト推定を、実請求額と混同せず、provider-managed cacheを含めて
監査可能な形で記録する。

## Implementation

- providerごとの料金は設定値として明示する。
- input/output/cached input tokenを分離する。
- 未設定・不完全な料金は推定せず `available: false` とする。
- 推定値には `basis: configured_rates` と `confidence: estimate_only` を付ける。

## Acceptance Criteria

- [x] cached tokenを通常のinput tokenと分離して計算する
- [x] 料金未設定時に0や推測値を出さない
- [x] 推定値と確定請求額を区別できる
- [x] currencyと料金設定の根拠を記録できる
- [x] 負数・非数値の料金設定をコスト推定に使用しない
