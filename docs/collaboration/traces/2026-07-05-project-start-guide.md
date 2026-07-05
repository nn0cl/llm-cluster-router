# AI Work Trace

## Request

- Date: 2026-07-05
- User request: Clarify that the template must not predefine a target domain
  model, while adopted projects may design their domain model inside the
  template process. Add guidance for how to start and continue development.
- Current phase: Architecture Path / process documentation.

## Context Ledger

- Included: `README.ja.md`, `README.md`,
  `docs/collaboration/adoption-guide.md`, CI required file list, and existing
  collaboration/process guidance.
- Omitted: target-project domain examples, concrete stack choices, provider
  choices, database choices, private data.
- Assumptions: a separate guide is clearer than expanding the adoption guide
  into a full development manual.
- Open decisions: target projects may create stack-specific start guides later.

## Routing

- Model/assistant/tool: Codex for documentation edits; deterministic search and
  CI-sanity checks for verification.
- Reason: collaboration guidance and CI required files are changing.
- Privacy constraints: no private or external data used.

## Cost / Reasoning Control

- Operating path: Architecture Path.
- Files read: README/adoption/CI and related collaboration guidance.
- Context intentionally omitted: target implementation, concrete domain
  examples, external docs.
- Deterministic checks used: `rg` for wording checks and repository sanity
  check equivalent to `.github/workflows/ci.yml`.
- Escalation reason: the wording affects how future agents interpret domain
  modeling boundaries.
- Avoided LLM work: no target-specific model, stack, or architecture was
  invented.
- Rework caused by AI output: none.

## Referee Decisions

- User asked to fix the wording and add guidance.

## Verification

- Commands/checks:
  - `rg` for domain-model wording, guide references, and unresolved trace
    placeholders.
  - repository sanity check equivalent to `.github/workflows/ci.yml`.
- Result: passed.

## Changed Files

- `README.md`
- `README.ja.md`
- `.github/workflows/ci.yml`
- `docs/collaboration/adoption-guide.md`
- `docs/collaboration/project-start-guide.md`
- `docs/collaboration/traces/2026-07-05-project-start-guide.md`

## Next Safe Action

- Run deterministic checks and commit/push if requested.

## Notes

- The intended distinction is: the reusable template does not ship target
  domain models; adopted projects use the process to discover their own domain
  models from accepted behavior.
