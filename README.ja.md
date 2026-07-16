# LLM Cluster Router

ローカル Ollama、OpenAI 互換 API、Anthropic Claude、ローカル Codex SDK をまたいで
コンパクトな LLM タスクパッケージをルーティングし、許可されたプロジェクト
ルート内にだけ出力するエージェント向けツールです。

[English README](README.md)

**一言で:** タスクごとに最適なモデル実行先を選び、コストを抑えつつ、安全な
出力パスを強制する薄いルーティング層。

## なぜ使うか

- **コスト管理:** 小さなタスクは無料のローカルモデルへ。深い推論が必要なときだけ
  有料 API へ段階的に上げられる。
- **プロバイダ横断:** 1 つのタスクパッケージ形式と設定ファイルで Ollama / OpenAI /
  Anthropic / Codex SDK を扱える。
- **エージェント連携:** CLI、agent skill、任意の MCP server として同じルーティング
  ロジックを使える。

## 30 秒デモ

設定済みプロバイダを確認:

```sh
python3 scripts/ollama_cluster_manager.py status_check \
  --config references/ollama_cluster_config.sample.json
```

タスクを実行（有料プロバイダを使う設定のときだけ API キーを設定）:

```sh
python3 scripts/ollama_cluster_manager.py execute_task \
  --config references/ollama_cluster_config.sample.json \
  --allowed-root "$PWD" \
  --task-package references/example-task-package.json \
  --output-path generated/demo-output.txt
```

## できること

- コンパクトな JSON **タスクパッケージ**（system prompt、context、instruction、
  任意の routing profile）を受け取る。
- 設定に基づきプロバイダとモデルを選択する（`easy` / `standard` / `hard` /
  `agentic` の **profile ベースルーティング** を含む）。
- モデル呼び出し**前**に `--allowed-root` 配下かどうかを検証する。
- 生成テキストの Markdown コードフェンス 1 重を除去してから書き込む。
- 生成全文を返さず、metadata（provider、model、profile 証拠、バイト数）で報告できる。

## できないこと

- エージェント全体のオーケストレーション、ツール計画、多段ワークフロー。
- 自動料金計算、クォータ追跡、SaaS 的ガバナンス。
- 永続化、監査 DB、チーム管理 UI。
- 設定根拠なしの、より高価なモデルへの黙示的エスカレーション。

設計詳細: `docs/architecture/README.md`。プロファイル一覧:
`docs/architecture/model-routing-catalog.md`。

## クイックスタート

1. リポジトリを clone する。
2. `references/ollama_cluster_config.sample.json` をコピーし、host / model を調整する。
3. 必要なら環境変数に API キーを設定する（`OPENAI_API_KEY`、`ANTHROPIC_API_KEY` など）。
4. `status_check` のあと `--allowed-root` 付きで `execute_task` を実行する。

agent skill としてインストール:

```sh
python3 scripts/install_skill.py
# または
scripts/setup_skill.sh --help
```

## 構成

- `SKILL.md` – エージェント向け skill 手順。
- `agents/openai.yaml` – OpenAI/Codex 向けメタデータ。
- `scripts/ollama_cluster_manager.py` – 標準ライブラリ CLI とルーティング本体。
- `scripts/mcp_server.py` – MCP 専用クライアント向け配信アダプタ（任意）。
- `scripts/setup_mcp_venv.sh` / `scripts/run_mcp_server.sh` – venv 起動。
- `Dockerfile` / `docker-compose.yml` – Python なし環境向け Docker 起動。
- `references/` – サンプル設定、ツール schema、system prompt、例タスクパッケージ。
- `tests/` – fake client と一時ディレクトリを使った単体テスト。

## テスト

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
python3 -m py_compile scripts/ollama_cluster_manager.py scripts/install_skill.py scripts/mcp_server.py
python3 -m json.tool references/ollama_cluster_config.sample.json >/dev/null
python3 -m json.tool references/agent_tool_schema.json >/dev/null
```

## MCP Server（任意）

MCP のみのクライアント向けに、skill の代わりに MCP server として起動できます。
CLI / skill と同じ設定ファイルと `OllamaClusterManager` を使います。

- **Option A:** `scripts/run_mcp_server.sh`（ローカルに Python がある場合）
- **Option B:** `docker compose run --rm -T mcp-server`（Python がない場合）

詳細は [English README](README.md) の MCP セクションを参照してください。

## プロバイダと profile ルーティング

`references/ollama_cluster_config.sample.json` で以下を設定できます。

| プロバイダ | 用途 |
| --- | --- |
| `ollama` | ローカル / LAN の Ollama |
| `openai` | OpenAI Responses API（`OPENAI_API_KEY`） |
| `anthropic` | Claude Messages API（`ANTHROPIC_API_KEY`） |
| `sakana` | Sakana Fugu Responses API（`SAKANA_API_KEY`、model `fugu`） |
| `codex` | ローカル Codex SDK（`openai-codex`） |

`routing.profiles` で `routing_profile` または `task_complexity` から実行先を
解決します。コスト最小化の原則と各 tier の説明は
`docs/architecture/model-routing-catalog.md` を参照してください。

Sakana Fuguの入力トークンキャッシュはprovider管理です。利用者は
`prompt_cache.policy: "provider_managed"` とstable/dynamic入力データを指定でき、
適用結果はmetadataで報告されます。provider間のfallbackは行いません。

`max_retries` は `0`〜`3`（既定値 `3`）で指定できます。408/425/429、5xx、
タイムアウト、接続失敗は上限付きバックオフで再試行し、選択済みproviderを
別providerやmockへ切り替えません。構造化出力はtask packageの
`response_schema` にJSON Schemaを指定できます。

## 安全性

`execute_task` では必ず `--allowed-root` を渡してください。モデル呼び出し前に
出力パスを検証します。

開発時の調査には `--debug` を指定できます。安全な構造化イベントをstderrへ出力し、
`--log-file path` を併用するとファイルにも保存します。トークン使用量、プロバイダが
返すプロンプトキャッシュ情報、リトライ、request ID、エラー時のスタックトレースを
確認できますが、プロンプト本文・レスポンス本文・認証情報は出力しません。hostに
`pricing`（`input_per_1m`、`cached_input_per_1m`、`output_per_1m`）を設定した場合だけ
コスト推定を行い、未設定時は不明として扱います。

ログ容量は `--log-max-bytes`（既定10MB）と `--log-backup-count`（既定5世代）で
制限できます。

本番運用ではログファイルのサイズ上限・世代数を設定し、推定コストは請求額では
ないことを確認してください。デバッグログは障害調査時だけ有効化し、調査終了後は
無効化します。

## 開発プロセス

本リポジトリは
[llm-project-template](https://github.com/nn0cl/llm-project-template) の
協調開発ストラテジーを適用しています。

- `AGENTS.md` – 全 coding agent 向けの運用契約。
- `docs/collaboration/README.ja.md` – テンプレート全体の日本語ガイド。
- `docs/collaboration/README.md` – テンプレート全体の英語ガイド。
- `docs/collaboration/adoption-guide.md` – 本リポジトリへの適用方法。

機能追加は AT-TDD に従います。受け入れ仕様は `docs/specs/`、計画は
`docs/issues/` と `docs/work-plans/` にあります。

## ライセンス

MIT License, Copyright (c) 2026 dstechnology co., ltd. See
[LICENSE](LICENSE).
