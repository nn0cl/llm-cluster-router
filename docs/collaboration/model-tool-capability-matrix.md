# Model and Tool Capability Matrix

Use this matrix to route AI-TDD collaboration tasks. It does not name specific
commercial models; it defines capability classes.

## Capability Classes

### Deterministic Tool

Use for:

- formatting.
- linting.
- dependency checks.
- tests.
- container/infra config validation.
- YAML parsing.
- import-boundary checks.

Referee approval:

- not required unless the tool changes files beyond the task scope.

### Code Assistant

Use for:

- small code completions.
- narrow test skeletons from clear Gherkin.
- mechanical edits with obvious local context.
- renaming within one module.

Referee approval:

- required before phase transition, not for every completion.

### Lightweight Reasoning Model

Use for:

- design intake drafts.
- VO/DTO naming review.
- checklist completion.
- summarizing changed files.
- drafting handoff notes.

Referee approval:

- required when the output changes process rules or accepted tests.

### Strong Reasoning Agent

Use for:

- architecture boundary analysis.
- ambiguous requirements.
- ADR drafting.
- cross-file refactor planning.
- privacy-sensitive routing.
- resolving conflicts between instructions.

Referee approval:

- required for ADR acceptance and phase transitions.

## Routing Table

| Task | Preferred route | Referee approval |
| --- | --- | --- |
| Mechanical file or wording edit | Deterministic tool or code assistant | not normally |
| One-file local code change with clear spec | Code assistant plus deterministic tests | after verification |
| Design intake | Lightweight reasoning model | before next phase |
| Phase 1 Red tests | Code assistant or strong reasoning agent | before Phase 2 |
| Phase 2 Green implementation | Code assistant with deterministic tests | after verification |
| Phase 3 refactor | Strong reasoning agent plus deterministic tests | before merge |
| Instruction changes | Strong reasoning agent | required |
| Prompt/template changes | Strong reasoning agent | required |
| YAML validation | Deterministic tool | not normally |
| Dependency checks | Deterministic tool | not normally |
| Privacy-sensitive context routing | Strong reasoning agent | required |

## Escalation Rules

Start with the cheapest safe route.
When a trace is required, record the starting route and escalation reason using
the cost/reasoning control fields in `docs/templates/ai-work-trace.md`.

Escalate to a stronger reasoning agent when:

- requirements are ambiguous or conflict with an accepted spec.
- more than one architectural boundary is touched.
- agent instructions, collaboration rules, or ADRs change.
- private or large context may be needed.
- deterministic verification contradicts the current plan.

Stay with a code assistant or deterministic tool when:

- the task touches one module or document section.
- the target behavior is already specified.
- no external provider, datastore, or architecture decision is needed.
- verification can be done by tests, linting, parsing, or search.

## Privacy Constraints

Use local or deterministic tools when:

- local-only mode applies.
- the content involved is private user data.
- excerpts contain personal or confidential notes.
- provider terms are unknown.

Escalate to Referee before using external AI with sensitive context.
