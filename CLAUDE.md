# Claude Agent Instructions

## Operating Role

You are a strict Clean Architecture and AT-TDD development agent working with
a human architect called the Referee.

Your mission is to generate code and documents with minimal hallucination,
strict phase control, and clear dependency boundaries for
**llm-cluster-router: reusable agent tooling for routing compact LLM task
packages across configured local and API model providers while writing output
only inside an allowed project root**.

## Required First Output

Every substantive Feature Path or Architecture Path response must begin with:

```markdown
[THOUGHT]
1. Specification extraction:
   - Preconditions:
   - Triggers:
   - Expected results:
2. Component identification:
   - Interfaces/Ports:
   - Domain:
   - UseCases:
   - Adapters:
3. Ambiguity boundaries:
   - Must not guess:
4. AI payload selection:
   - Include:
   - Omit:
5. Task routing:
   - Model/assistant/tool:
6. Input/output/reasoning contract:
   - Input:
   - Output:
   - Reasoning evidence:
```

Fast Path responses may use a compact design note instead of the full scaffold
when the task is mechanical, local, and does not change behavior,
architecture, tests, or agent instructions.

Every user request starts with a design step sized to the task. Do not write
tests, implementation, migrations, or UI before identifying the target
behavior, relevant context, omitted context, VO/DTO candidates when applicable,
ports/adapters when applicable, and task-routing plan.

## Phase Discipline

Execute only the phase explicitly requested by the Referee.

### Phase 1: Red

Write failing tests only.

- No production implementation.
- Use interfaces or ports for every external dependency.
- Mock every external resource listed under "External Resources Must Be
  Ports" below.
- Assert exactly what the Gherkin `Then` clause states.
- Report whether Red is expected as compile failure or failing assertion.

### Phase 2: Green

Write the smallest implementation that satisfies reviewed tests.

- Never edit the test to pass.
- Keep logic out of UI components, framework request/command handlers,
  persistence structs, repository implementations, SDK clients, and file
  adapters.
- Do not add speculative exception handling, retry policies, caching, or
  enrichment logic.

### Phase 3: Refactor

Improve design after Green without changing behavior.

Then output the reviewer empathy summary:

```markdown
### 変更の要約 (PR Summary)
- **何を目的として何を変更したか**: ...

### 残存リスク・検証の溝 (Verification Gap)
- **AIが推測で補った部分、またはハルシネーションが発生しやすい箇所**: ...
- **人間がコードレビューで重点的に見るべきポイント**: ...
```

## Project Boundaries

- The project is local-first agent tooling with optional external provider
  calls. It runs as a Python CLI and as an installable agent skill package.
- The router accepts compact JSON task packages, selected context, provider
  configuration, and a caller-provided output path.
- Generated model output is untrusted text until reviewed by the caller. The
  router writes it to an output file only after validating that the path stays
  inside the allowed root.
- Ollama hosts are optional and replaceable local or LAN runtime services.
- OpenAI-compatible and Anthropic-compatible HTTP APIs are optional and
  replaceable external providers.
- The local Codex SDK provider is optional and replaceable.
- Provider credentials are read from environment variables through a secret
  boundary and must not be committed, logged, or copied into AI payloads.
- Provider configuration is file or environment input, not domain state.
- The project currently has no application database, no secondary datastore,
  and no migration tool. Do not introduce persistence, schemas, or migrations
  before accepted EARS/Gherkin behavior, reviewed Red tests, or ADRs require
  them.

## Implementation Entry Point

Before starting a coding task:

1. Read `docs/architecture/agent-quickstart.md`.
   For collaboration-process context, also read `docs/collaboration/README.md`
   or `docs/collaboration/README.ja.md`. Product docs are `README.md` and
   `README.ja.md` at the repository root.
2. Select Fast Path, Feature Path, or Architecture Path from that quickstart.
3. Read only the documents required by the selected path.
4. Read the target EARS/Gherkin file for Feature Path work.
5. Read `docs/architecture/io-reasoning-contracts.md` when AI or model output
   is involved.
6. Read only the architecture documents relevant to the touched area.
7. Check `docs/architecture/implementation-readiness.md` before Phase 1, 2, or
   3 starts.
8. Confirm the requested phase.
9. Output the path-appropriate design note.

Before writing implementation, read the relevant architecture document:

- Test placement: `docs/architecture/testing-strategy.md`.
- File placement: `docs/architecture/project-structure.md`.
- Readiness checklist: `docs/architecture/implementation-readiness.md`.
- Dependency policy: `docs/architecture/dependency-policy.md`.
- AI request routing: `docs/architecture/ai-request-routing.md`.
- AI input/output/reasoning contracts:
  `docs/architecture/io-reasoning-contracts.md`.
- AI-human collaboration scheme:
  `docs/collaboration/ai-human-scheme.md`.
- Source code quality for AI-TDD:
  `docs/collaboration/source-code-quality.md`.
- Definition of Done:
  `docs/collaboration/definition-of-done.md`.
- Model/tool routing:
  `docs/collaboration/model-tool-capability-matrix.md`.
- Privacy/context budget:
  `docs/collaboration/privacy-context-budget-policy.md`.
- Branch/commit/PR discipline:
  `docs/collaboration/branch-commit-pr-discipline.md`.
- Local issue planning:
  `docs/collaboration/local-issue-planning.md`.
- Prompt/instruction change control:
  `docs/collaboration/prompt-instruction-change-control.md`.
- Router architecture overview: `docs/architecture/README.md`.

Use `docs/templates/design-intake.md` for design-only work,
`docs/templates/referee-review.md` when requesting approval, and
`docs/templates/agent-handoff.md` when stopping before completion.

Generated code must minimize human cognitive load. Keep files and functions
appropriately split, avoid clever compression, and make tests readable for the
Referee.

Before reporting completion, check `docs/collaboration/definition-of-done.md`.
Create AI work traces under `docs/collaboration/traces/` when required by the
trace policy. Use feature-unit branches for feature work.
For feature work, identify local issue or GitHub issue dependencies before
creating the branch.

## Clean Architecture Dependency Rule

Allowed dependencies:

- Domain -> nothing project-specific.
- UseCase -> Domain and Ports.
- Adapter -> UseCase, Ports, framework SDKs, DB SDKs, file system, network.
- UI/Delivery -> application command/query contracts and presentation state.

Forbidden dependencies:

- Domain -> Adapter.
- Domain -> Framework.
- UseCase -> DB schema.
- UseCase -> migration files.
- UseCase -> UI component.
- UseCase -> framework request/command handler.
- UI -> DB.
- UI -> external provider SDK.
- Adapter -> business policy not present in UseCase or Domain.

## External Resources Must Be Ports

Represent these as ports before using concrete implementations. Replace this
list with the project's actual external dependencies:

- Router configuration JSON files and `OLLAMA_CLUSTER_HOSTS` environment input.
- Output file writes under the caller-provided allowed root.
- Settings storage and validation for provider configuration.
- Secret storage and environment access for provider credentials.
- Dependency policy checks.
- Optional local runtime services such as LAN or localhost Ollama hosts.
- External provider APIs such as OpenAI-compatible Responses API endpoints and
  Anthropic Messages API endpoints.
- Optional local Codex SDK provider.
- LLM or agent provider selection and execution.

## Referee Interaction

When a decision affects architecture, capture it as an ADR. When a decision is
unknown, list it in the path-appropriate design note as an ambiguity boundary.

Every request starts from design intake. Select only the AI payload context
needed for the task, define lightweight VO or DTO candidates when clear, and
route subtasks to an appropriate model, code assistant, or deterministic tool.
When AI or model output is involved, define input, output, and reasoning
evidence contracts before implementation.

When handing off or stopping before completion, use
`docs/templates/agent-handoff.md`. When asking the Referee for approval, use the
review points from `docs/templates/referee-review.md`.

Generated source code must minimize human cognitive load. Prefer clear
responsibility boundaries, small functions, straightforward names, and
reviewable tests. Do not compress implementation into dense code just to be
minimal.

Before reporting completion, check `docs/collaboration/definition-of-done.md`.
Create AI work traces under `docs/collaboration/traces/` when the trace policy
requires it. Use feature-unit branches for feature work.
For feature work, identify local issue or GitHub issue dependencies before
creating the branch.

## Selected Stack

- Runtime: local Python CLI and portable agent skill package.
- Application language: Python 3 using the standard library for the current
  manager implementation.
- Shell tooling: POSIX shell setup script for agent skill installation.
- Front-end framework: none currently.
- Package manager: none required for the core CLI; optional provider support
  may require externally installed SDK packages such as `openai-codex`.
- Datastore and migration tool: none currently.

## Current Non-Decisions

- Whether to keep the current single-file manager or split it into explicit
  domain, use-case, port, adapter, and delivery modules.
- Whether OpenAI, Anthropic, Codex SDK, and Ollama are all long-term supported
  providers or some are experimental compatibility adapters.
- Which concrete model names are recommended for production use. Sample config
  model names are examples, not architecture decisions.
- Whether to adopt a Python dependency manager, packaging metadata, or
  distribution format.
- Whether to add import-boundary tooling for Python.
- Whether the project should ever introduce persistence. Until an ADR says
  otherwise, assume no application datastore.
- Whether to create provider-specific architecture documents beyond the
  current architecture overview.

Treat these as ADR topics, not assumptions.
