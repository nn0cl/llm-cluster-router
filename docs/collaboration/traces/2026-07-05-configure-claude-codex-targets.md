# AI Work Trace

## Request

- Date: 2026-07-05
- User request: Align files so Claude and Codex are configuration targets.
- Current phase: Architecture Path, configuration/documentation alignment.

## Context Ledger

- Included: sample cluster config, agent tool schema, skill instructions,
  agent system prompt, README, existing manager behavior, and existing tests.
- Omitted: profile-routing implementation, provider API calls, dependency
  adoption, secrets, and real provider status.
- Assumptions: Claude is represented by the existing `anthropic` provider key
  because the manager already implements Anthropic Messages API routing. Codex
  is represented by the existing `codex` provider key.
- Open decisions: Whether to implement manager-level routing profiles, rename
  Ollama-specific filenames, or add a model catalog with cost/reasoning
  metadata.

## Routing

- Model/assistant/tool: Architecture Path editing with deterministic checks.
- Reason: This changes agent-facing skill guidance and configuration examples.
- Privacy constraints: No secrets or private data were read or copied.

## Cost / Reasoning Control

- Operating path: Architecture Path.
- Files read: `references/ollama_cluster_config.sample.json`,
  `references/agent_tool_schema.json`, `SKILL.md`, `README.md`,
  `references/agent_system_prompt.md`, collaboration change-control rules, and
  existing tests.
- Context intentionally omitted: external provider docs, runtime credentials,
  and broad source redesign.
- Deterministic checks used: JSON validation, Python compile, unit tests,
  shell syntax check, and targeted search.
- Escalation reason: Skill guidance and configuration semantics changed.
- Avoided LLM work: Did not ask a provider to choose model names or pricing.
- Rework caused by AI output: None.

## Referee Decisions

- Treat Claude and Codex as configuration targets for the skill/router.

## Verification

- Commands/checks: validated sample config and tool schema JSON; ran unit
  tests; ran Python compile checks; ran shell syntax check; searched updated
  files for Claude/Codex configuration guidance; checked Git status.
- Result: JSON validation, unit tests, Python compile checks, and shell syntax
  check all passed. Updated files now document `anthropic` as the Claude
  provider target and `codex` as the Codex SDK provider target. Git still has
  previously copied collaboration files untracked and earlier tracked-file
  changes from this adoption session.

## Changed Files

- `README.md`
- `SKILL.md`
- `references/ollama_cluster_config.sample.json`
- `references/agent_tool_schema.json`
- `references/agent_system_prompt.md`
- `docs/collaboration/traces/2026-07-05-configure-claude-codex-targets.md`

## Next Safe Action

- Referee review of whether profile-based routing should be implemented in a
  separate Feature Path phase.

## Notes

- This pass documents task-profile guidance for the calling skill. It does not
  implement manager-level profile routing.
