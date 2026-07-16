# AI Work Trace

## Request

- Date: 2026-07-09
- User request: Relocate collaboration template READMEs under
  `docs/collaboration/`, restore English template guide, convert root README
  files to product documentation, and add agent pointers to the template docs.
- Current phase: Architecture Path, documentation relocation.

## Context Ledger

- Included: root `README.md`, `README.ja.md`, `AGENTS.md`, `CLAUDE.md`,
  `docs/collaboration/adoption-guide.md`, prior template content from
  `README.ja.md`, `docs/specs/fallback-routing.md` draft.
- Omitted: implementation changes to routing behavior, CI changes, GitHub
  issue sync.
- Assumptions: Product READMEs own router onboarding; collaboration READMEs
  own template/process onboarding. Upstream template repo URL is
  nn0cl/llm-project-template.
- Open decisions: whether `scripts/copy-ai-collaboration-files.sh` should copy
  template READMEs from `docs/collaboration/` in a future template release.

## Routing

- Model/assistant/tool: Architecture Path documentation editing with
  deterministic file inspection.
- Reason: Agent operating contract files and collaboration doc layout changed.
- Privacy constraints: No secrets or private data were read or copied.

## Cost / Reasoning Control

- Operating path: Architecture Path.
- Files read: root README files, AGENTS.md, CLAUDE.md, adoption-guide.md.
- Context intentionally omitted: full manager implementation, external web
  research.
- Deterministic checks used: file writes and link target selection.
- Escalation reason: Contract-file relocation requested by Referee.
- Avoided LLM work: Did not infer fallback implementation before spec review.

## Referee Decisions

- Move template Japanese guide to `docs/collaboration/README.ja.md`.
- Restore `docs/collaboration/README.md` as the English template guide.
- Make root `README.md` and `README.ja.md` product READMEs.
- Add agent pointers to the collaboration READMEs.
- Start fallback routing as an accepted spec under `docs/specs/`.

## Verification

- Commands/checks: created `references/example-task-package.json` for the new
  30-second demo command in README.
- Result: Demo path references an in-repo example task package.

## Changed Files

- `README.md`
- `README.ja.md`
- `docs/collaboration/README.md`
- `docs/collaboration/README.ja.md`
- `docs/specs/fallback-routing.md`
- `docs/collaboration/adoption-guide.md`
- `AGENTS.md`
- `CLAUDE.md`
- `references/example-task-package.json`
- `docs/collaboration/traces/2026-07-09-template-readme-relocation.md`

## Next Safe Action

- Referee review of product README wording and fallback spec ambiguities.
- Approve Phase 1 Red for fallback routing local issue LISS-0016.
