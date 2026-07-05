# AI Work Trace

## Request

- Date: 2026-07-05
- User request: Add guidance so design and adoption consider vulnerability
  reports, version-specific implementation examples, troubleshooting depth,
  minimal real-file testing, and POC feasibility for libraries.
- Current phase: Architecture Path / process documentation.

## Context Ledger

- Included: dependency policy, implementation readiness checklist, project
  start guide, ADR template.
- Omitted: current vulnerability databases, specific libraries, package
  versions, external package documentation.
- Assumptions: this is a process rule; actual dependency adoption tasks must
  verify current advisory and version evidence at the time of adoption.
- Open decisions: target projects may choose stack-specific audit tools later.

## Routing

- Model/assistant/tool: Codex for documentation edits; deterministic search and
  repository sanity checks for verification.
- Reason: dependency adoption rules affect architecture and future agent
  behavior.
- Privacy constraints: no private data or external provider data used.

## Cost / Reasoning Control

- Operating path: Architecture Path.
- Files read: dependency policy, readiness checklist, project start guide, ADR
  template.
- Context intentionally omitted: package registries, vulnerability databases,
  provider documentation.
- Deterministic checks used: `rg` for adoption-checklist wording and
  repository sanity check equivalent to `.github/workflows/ci.yml`.
- Escalation reason: process rule changes affect future dependency decisions.
- Avoided LLM work: no specific dependency was evaluated or recommended.
- Rework caused by AI output: none.

## Referee Decisions

- User requested adding the dependency adoption considerations.

## Verification

- Commands/checks:
  - `rg` for dependency-adoption checklist terms and source-project residue.
  - repository sanity check equivalent to `.github/workflows/ci.yml`.
- Result: passed.

## Changed Files

- `docs/architecture/dependency-policy.md`
- `docs/architecture/implementation-readiness.md`
- `docs/collaboration/project-start-guide.md`
- `docs/collaboration/traces/2026-07-05-dependency-adoption-checklist.md`
- `docs/templates/adr.md`

## Next Safe Action

- Run deterministic checks and commit/push if accepted.

## Notes

- The rule intentionally avoids naming specific tools or libraries because
  target projects choose their stack after adoption.
