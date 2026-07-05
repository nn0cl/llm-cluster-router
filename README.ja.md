# LLM Project Template 日本語ガイド

[English README](README.md)

これは `README.md` の逐語訳ではありません。日本語話者がこのテンプレートを
導入・運用するときに、判断を迷いやすい点を短く確認するための入口です。
正式な運用契約は `AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md`
と `docs/` 配下の各文書を参照してください。

## これは何か

このリポジトリは、Clean Architecture と AT-TDD を前提に、人間の Referee と
複数の AI coding agent が協調するためのテンプレートです。

このリポジトリでの **AT-TDD** は、独立した標準手法名ではなく、
**ATDD + TDD のハイブリッド運用**を指す repo 内の呼び名です。受け入れ仕様から
失敗する test を作り、review 済み test に基づいて最小実装し、Green 確認後に
Refactor します。

このテンプレート配布物は、アプリケーションの仕様、技術スタック、DB、外部 API、
LLM provider、ドメインモデルを事前には決めません。それらは導入後に、導入先
リポジトリの仕様・ADR・Referee 判断・アーキテクチャ文書に基づいて決めます。

## 大事な考え方

- 仕様なしで実装しない。
- Phase を飛ばさない。
- 人間の Referee が phase transition、ADR、曖昧な判断を承認する。
- AI に渡す context は最小限にする。
- 高度な reasoning が本当に必要だったかを trace に軽く残す。
- AI output は信頼済みデータとして扱わず、構造・根拠・review status を確認する。
- 導入先の README、仕様、アーキテクチャをテンプレートで上書きしない。

## これを使うと何が良いか

このテンプレートの価値は、AI との開発を場当たり的な chat ではなく、
review 可能な engineering workflow に寄せることです。

期待できる効果:

- 仕様が曖昧なまま AI が実装を推測することを減らす。
- Red / Green / Refactor の phase 飛ばしを減らす。
- adapter、UI、provider client、persistence に business logic が隠れるのを防ぐ。
- Fast Path / Feature Path / Architecture Path で、強い reasoning の使いすぎを抑える。
- AI に渡す context を小さくし、privacy と cost を管理しやすくする。
- dependency 採用時に、脆弱性、対象 version の実装例、troubleshooting、実ファイルでの
  最小 test、POC 可否を確認しやすくする。
- handoff や再開時に、仕様・ADR・trace から状況を追いやすくする。

詳しくは `docs/collaboration/template-benefits.md` を参照してください。

## 作業 path の使い分け

このテンプレートは、毎回 AI に重い reasoning をさせないために 3 つの path を
使い分けます。

大きめの作業では `docs/collaboration/llm-cost-reduction.md` に沿って、
選んだ path、読んだファイル、あえて省いた context、deterministic check、
強い reasoning へ escalation した理由を短く trace に残します。

### Fast Path

機械的で局所的な作業に使います。

例:

- typo 修正。
- README の短い補足。
- shell script の構文確認。
- ファイルコピーの dry-run。
- formatter、linter、search、test など deterministic tool で確認できる作業。

Fast Path では full `[THOUGHT]` は不要です。compact design note で、scope、
読んだ context、省いた context、実行する deterministic check を示します。

### Feature Path

AT-TDD の Phase 1/2/3 に使います。

- Phase 1: Red。失敗する test だけを書く。
- Phase 2: Green。review 済み test を通す最小実装だけを書く。
- Phase 3: Refactor。挙動を変えずに読みやすさと境界を整える。

Feature Path では target spec、phase rule、関連 architecture document を読み、
full `[THOUGHT]` を出します。

### Architecture Path

ADR、prompt/instruction 変更、privacy-sensitive routing、境界判断、process 変更に
使います。プロジェクト方針を変える場合は Referee approval が必要です。

## 新規リポジトリへ導入する

テンプレート側で実行します。

```bash
scripts/copy-ai-collaboration-files.sh --target /path/to/target-repo
```

placeholder を少し埋める場合:

```bash
scripts/copy-ai-collaboration-files.sh \
  --target /path/to/target-repo \
  --project-name "Example Product" \
  --domain-summary "one-line target project summary" \
  --stack "backend language, frontend framework, package manager"
```

導入後、target repo で初回 LLM session 用 prompt を作ります。

```bash
cd /path/to/target-repo
scripts/init-llm-context.sh .
```

出力された prompt を、そのリポジトリの最初の AI session に貼ります。

## 既存リポジトリへ途中導入する

まず dry-run します。

```bash
scripts/copy-ai-collaboration-files.sh --target /path/to/existing-repo --dry-run
```

問題なければ `--force` なしで実行します。デフォルトでは既存ファイルを
上書きしません。既存の product README や architecture document は導入先が
所有する文書として保持します。

導入先でのオンボーディングは `docs/collaboration/adoption-guide.md` を見ます。

## 導入後に最初に埋めるもの

1. `AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md` の project 名や
   stack placeholder。
2. `docs/architecture/README.md` の project-specific な説明。
3. `docs/specs/` 配下の最初の EARS/Gherkin specification。
4. 必要になった architecture document。必要になるまで作りすぎない。
5. 外部 resource 一覧。DB、settings、secret storage、外部 API、LLM provider など。

## プロジェクトを始める・進める

詳しい手順は `docs/collaboration/project-start-guide.md` にあります。

最初の流れ:

1. テンプレートを導入する。
2. project 名、stack、境界、未決定事項を placeholder に記入する。
3. 最初の仕様を `docs/specs/` に EARS/Gherkin で書く。
4. 外部 resource を ports にする候補として列挙する。
5. Feature Path の Phase 0 design intake で、必要な domain model 候補を整理する。
6. Referee が Phase 1 Red を承認してから test を書く。

開発中の流れ:

1. issue または no-issue reason を確認する。
2. `docs/architecture/agent-quickstart.md` を読んで path を選ぶ。
3. Feature Path では target spec と関連 architecture document を読む。
4. path に合った design note を出す。
5. 承認された phase だけを実行する。
6. deterministic verification を走らせる。
7. 必要なら trace と cost/reasoning control を残す。
8. phase gate で Referee review を受ける。

ドメインモデルは、この流れの中で決めて構いません。むしろ導入後のプロジェクト
では、仕様と review 済み test に基づいて domain model を育てることが想定されて
います。

## やってはいけないこと

- テンプレート配布物や導入スクリプトに、導入先固有の domain model を含める。
- 仕様・ADR・Referee 判断なしに、AI が domain model を推測で決める。
- placeholder 例を、そのまま技術選定として扱う。
- Feature Path で review 前に Phase 2 へ進む。
- Fast Path で仕様変更、architecture 変更、agent instruction 変更をする。
- `--force` で既存文書をまとめて上書きする。
- private data、secret、`.env` 全文を AI prompt に入れる。

## 迷ったら

- ただの局所作業なら Fast Path。
- accepted spec に対する実装作業なら Feature Path。
- 方針や境界を変えるなら Architecture Path。
- path が曖昧なら Architecture Path に寄せて、Referee に判断を求めます。
