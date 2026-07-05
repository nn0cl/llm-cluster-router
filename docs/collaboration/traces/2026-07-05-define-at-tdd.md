# AI Work Trace

## Request

- Date: 2026-07-05
- User request: Define what this project means by AT-TDD.
- Current phase: Architecture Path / terminology clarification.

## Context Ledger

- Included: `docs/at-tdd/process.md`, `README.md`, `README.ja.md`, and search
  results for AT-TDD references.
- Omitted: external methodology sources, target-project implementation,
  provider choices, private data.
- Assumptions: the intended definition is a repository-local shorthand for an
  ATDD + TDD hybrid workflow, not an industry-standard standalone method name.
- Open decisions: none.

## Routing

- Model/assistant/tool: Codex for documentation edits; deterministic search
  checks for verification.
- Reason: terminology affects agent and human interpretation of the workflow.
- Privacy constraints: no private data used.

## Cost / Reasoning Control

- Operating path: Architecture Path.
- Files read: README files, AT-TDD process document, AT-TDD reference search.
- Context intentionally omitted: external sources and unrelated docs.
- Deterministic checks used: `rg` for AT-TDD references and repository sanity
  check equivalent to `.github/workflows/ci.yml`.
- Escalation reason: process terminology clarification.
- Avoided LLM work: no broad methodology rewrite or new phase model was
  introduced.
- Rework caused by AI output: none.

## Referee Decisions

- User asked to define the term.

## Verification

- Commands/checks:
  - `rg` for AT-TDD definition references and source-project residue.
  - repository sanity check equivalent to `.github/workflows/ci.yml`.
- Result: passed.

## Changed Files

- `README.md`
- `README.ja.md`
- `docs/at-tdd/process.md`
- `docs/collaboration/traces/2026-07-05-define-at-tdd.md`

## Next Safe Action

- Run deterministic checks and commit/push if requested.

## Notes

- The definition keeps the existing Red/Green/Refactor phase discipline intact.
