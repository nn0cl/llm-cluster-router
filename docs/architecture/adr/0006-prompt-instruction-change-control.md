# ADR 0006: Prompt and Instruction Change Control

## Status

Accepted

## Context

`AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` are
near-duplicate operating contracts for different AI coding tools, together
with `docs/at-tdd/process.md`, `docs/collaboration/*.md`, and
`docs/templates/*.md`. Agent behavior depends directly on these files.

These files can drift from each other silently: one file can gain a required
read step that the others do not, and none of them require the
operating-contract files themselves to be reviewed with the same rigor as
application code. The AI Work Trace Log already asks for a trace when
contract files change, but that alone does not name the exact file set,
require Referee review specifically, or get enforced by CI.

This gap is tracked in `docs/collaboration/process-gap-register.md`.

## Decision

Adopt `docs/collaboration/prompt-instruction-change-control.md` as the
canonical definition of the agent operating contract file set.

- Name the exact files and glob patterns that count as the agent operating
  contract.
- Require Referee review, a stated reason, and a cross-file consistency
  check whenever a contract file changes.
- Require an AI work trace under `docs/collaboration/traces/` for every
  contract change, including small wording changes.
- Enforce the trace requirement in CI: a pull request that changes a
  contract file must also add a trace file.

## Consequences

Positive:

- Contract drift between `AGENTS.md`, `CLAUDE.md`, and
  `.github/copilot-instructions.md` becomes visible in review instead of
  silently changing agent behavior.
- Every contract change has a recorded reason and expected behavior change.
- CI gives an automated signal instead of relying only on Referee memory.

Negative:

- Adds a mandatory trace step even for small wording changes to contract
  files.
- Requires keeping the file list in
  `docs/collaboration/prompt-instruction-change-control.md` up to date as new
  contract-like files are introduced.

## Enforcement

Code review should reject:

- agent operating contract changes without a stated reason or Referee review.
- agent operating contract changes without an accompanying trace under
  `docs/collaboration/traces/`.
- agent operating contract changes that leave `AGENTS.md`, `CLAUDE.md`, and
  `.github/copilot-instructions.md` inconsistent with each other.

CI should reject:

- a pull request that changes a file listed in
  `docs/collaboration/prompt-instruction-change-control.md` without adding a
  trace file under `docs/collaboration/traces/`.
