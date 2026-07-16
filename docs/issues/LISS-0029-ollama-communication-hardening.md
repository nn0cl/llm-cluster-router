# LISS-0029: Ollama通信境界の製品水準化

## Metadata

- Local issue ID: LISS-0029
- Status: review
- Phase: phase-3-refactor
- Type: feature / architecture
- Priority: high
- Related branch: feature/sakana-ollama-interchangeability
- Related ADR: `docs/architecture/adr/0009-no-provider-fallback-and-bounded-retry-cost-control.md`

## Goal

Ollamaとの通信を、失敗・高負荷・長時間生成・不正レスポンスが発生しても
安全に扱える、単一のPort/Adapter境界へ整備する。

呼び出し側には、次の一貫した契約だけを提供する。

- 成功: 検証済みの生成結果と利用メタデータ
- 失敗: 分類済みのエラー、HTTPステータス、再試行可否、試行回数
- 再試行: 選択中のOllamaだけを、設定された上限内で再試行
- 終了: 別プロバイダ、別ホスト、mock、暗黙の別endpointへ切り替えない

## Background

現在のrouterには、Ollama通信、ステータス確認、レスポンス変換、リトライ、
エラー分類が複数の責務にまたがっている。参考実装には有用な要素がある一方、
そのまま取り込むと、parse retryと通信retryの二重化や、同一Ollama内のendpoint
fallbackによる試行回数増加を招く。

参考にする実装:

- `mt4-orchestration`: retry分類、モデル検出、モデル未導入エラー
- `novel-maker`: Port/Adapter境界、構造化レスポンス検証、キャンセル、
  完了済み呼び出しのcheckpoint

参考実装のプロダクト固有プロンプト、endpoint fallback、複数層のretryは
取り込まない。

## In Scope

### 1. Ollama通信Port/Adapter

- OllamaのGET/POST通信を `scripts/adapters/` の差し替え可能な境界へ集約する
- Manager、routing、CLIから `urllib` などの具体的HTTP実装を分離する
- `/api/tags`、`/api/ps`、生成endpointを同じエラー契約で扱う

### 2. エラー分類

次の分類を型付きエラーとして返す。

| 分類 | 例 | 再試行 |
| --- | --- | --- |
| authentication | 401/403 | しない |
| invalid_request | 400/404/409/413/422 | しない |
| model_not_found | Ollamaのモデル未導入 | しない |
| timeout | 接続/読み取り/生成タイムアウト | する |
| connection | 接続失敗、接続切断 | する |
| rate_limit | 429 | する |
| overloaded/server | 425/500/502/503/504 | する |
| protocol | 不正JSON、レスポンス形状不正 | しない |
| cancelled | 利用者によるキャンセル | しない |

エラーには可能な範囲で以下を保持する。

- provider、operation、model
- HTTP status code
- retryable
- attempt / max attempts
- request IDまたは相関ID
- 安全な短いメッセージ

APIキー、Authorizationヘッダ、全文プロンプト、レスポンス本文全体は保持・
出力しない。

### 3. リトライとコスト制御

- `max_retries` は0〜3、既定3
- total attemptsは最大4回
- timeout / connection / 429 / 5xx / overloadだけを再試行
- 指数バックオフと `Retry-After` を使用する
- `Retry-After` は設定された最大待機時間を超えない
- retry budgetは1つに統一し、adapter内・SDK内・orchestrator内で重複させない
- リトライ後も同じOllamaで失敗し、別プロバイダへ切り替えない

このIssueではexactly-onceは保証しない。タイムアウト後はOllama側で処理済みの
可能性があるため、試行回数をメタデータで追跡し、重複実行の可能性を明示する。

### 4. 構造化レスポンス検証

`response_schema` が指定された場合、Adapterは成功を返す前にレスポンスを検証する。

- 空レスポンスを拒否
- JSON parse失敗を `protocol` または `schema` エラーにする
- object/arrayなどのトップレベル型を検証
- required fieldを検証
- schema違反を成功扱いしない
- 欠落フィールドを合成しない

### 5. Ollamaモデル情報

- `/api/tags` のモデル名・タグ・detailsを取得する
- 大文字小文字を区別せずモデル名を解決する
- `model` と `model:tag` の基本名を適切に解決する
- モデル未導入とOllama停止を区別する
- `/api/ps` のloaded/running情報をステータスに反映する

### 6. キャンセルと観測可能性

- 長時間生成をキャンセルできる境界を用意する
- `waiting`、`retrying`、`completed`、`cancelled`、`exhausted` を観測できる
- 観測イベントに秘密情報や全文プロンプトを含めない

## Out of Scope

- OpenAI/Anthropic/Sakanaへのフォールバック
- 別Ollamaホストへの自動フォールバック
- `/api/chat` から `/v1/chat/completions` などへの暗黙endpoint fallback
- SDKの導入
- ストリーミング対応
- Ollamaのモデルpull自動化
- 永続的なレスポンスキャッシュ
- providerが提供しないexactly-once/idempotencyの仮実装
- Novel Maker固有のpersona promptやtask schemaの移植

## Acceptance Criteria

### Communication boundary

- [ ] OllamaのGET/POSTはPort経由で呼ばれ、Manager/UseCaseがHTTPライブラリに依存しない
- [x] `/api/tags`、`/api/ps`、生成処理が同じtyped error contractを使用する
- [x] 成功レスポンスと失敗レスポンスのDTO/メタデータ形状が定義されている

### Error and retry behavior

- [x] 400/401/403/404/409/413/422/429/5xxとtimeout/connectionを分類できる
- [x] モデル未導入404とendpoint未導入404を区別できる
- [x] retryable errorだけが0〜3回の予算内で再試行される
- [x] 認証・入力不正・モデル未導入・protocol/schema errorは再試行されない
- [x] `Retry-After` と指数バックオフが上限付きで適用される
- [x] retry exhaustion後に他provider、他host、mock、別endpointを呼ばない
- [x] attempt数、status、retryable、request IDを安全に確認できる

### Response validation

- [x] `response_schema` 違反は成功として扱われない
- [x] 空本文、不正JSON、必須フィールド欠落を検出する
- [x] 欠落データを自動合成しない

### Model and operation visibility

- [x] `/api/tags` のモデル名とdetailsを取得できる
- [x] model/tagの大小文字差を吸収できる
- [x] `/api/ps` のloaded/running情報を利用できる
- [x] waiting/retrying/completed/cancelled/exhaustedが秘密情報なしで観測できる

### Regression and safety

- [ ] 既存Ollama/Sakana/OpenAI/Anthropic/CodexのテストがGreen
- [x] 通信テストはfake Portを使い、実Ollamaや実APIを呼ばない
- [ ] OpenAI/Anthropicの実接続テストを追加しない
- [ ] フォールバック実装を追加しない

## Implementation Slices

1. **LISS-0029-A: Transport contract**
   - Ollama request/response/error DTO
   - HTTP status and transport classification
   - safe request metadata
2. **LISS-0029-B: Response validation**
   - `response_schema` validation
   - protocol/schema error handling
3. **LISS-0029-C: Model and health information**
   - tags/details parsing
   - model identity resolution
   - loaded/running model status
4. **LISS-0029-D: Retry and cancellation boundary**
   - single retry budget
   - bounded backoff
   - cancellation and attempt events
5. **LISS-0029-E: Regression and documentation**
   - fake Port tests
   - no-fallback tests
   - README/architecture/config documentation

## Dependencies

- Depends on LISS-0021 provider adapter extraction.
- Depends on LISS-0022 manager/CLI thinning for final Port ownership.
- Related to LISS-0028 response-schema and provider-error hardening.
- Enforced by ADR 0009.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py`
- `python3 -m json.tool references/agent_tool_schema.json >/dev/null`
- `git diff --check`
- Confirm no real provider endpoint is contacted by tests.

## Implementation note

Slices A-E are implemented on the adapter boundary and covered by the local
fake-transport suite. Final closure remains a review step because LISS-0022
still owns the complete manager/CLI HTTP dependency removal; the compatibility
wrappers currently remain in place to preserve the existing command contract.

## References

- `/Users/nn0cl/Documents/git/mt4-orchestration/mt4-orchestration/backend/app/llm/ollama_client.py`
- `/Users/nn0cl/Documents/git/mt4-orchestration/mt4-orchestration/backend/app/llm/provider_client.py`
- `/Users/nn0cl/Documents/git/mt4-orchestration/mt4-orchestration/backend/app/llm/retry.py`
- `/Users/nn0cl/Documents/git/novel-maker/backend/src/novel_maker/adapters/llm_cluster_router/ollama_http.py`
- `/Users/nn0cl/Documents/git/novel-maker/backend/src/novel_maker/core/application/loop/llm_call_guard.py`
- `docs/architecture/adr/0009-no-provider-fallback-and-bounded-retry-cost-control.md`
