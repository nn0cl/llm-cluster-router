# ADR 0005: Local Issue Planning

## Status

Accepted

## Context

The project uses AI-TDD plus human Referee collaboration. Planning needs issue
relationships, work order, branch scope, and phase gates. GitHub Issues are
useful, but early or offline planning should not require GitHub network access.

Agents also need a repository-local artifact that can be read during design
intake.

## Decision

Support issues in both GitHub and local Markdown files.

Local issues live under:

```text
docs/issues/
```

Multi-issue work plans live under:

```text
docs/work-plans/
```

Use local issue IDs with the `LISS-0000` format. Local issue files should
record status, phase, dependencies, blockers, related branch, acceptance notes,
and Referee decision points.

Before feature work starts, agents should identify issue dependencies and create
or update a work plan. Work should proceed from the next unblocked issue.

## Consequences

Positive:

- Planning works before GitHub setup or without network access.
- Issue dependencies are visible to AI agents during design intake.
- Branch scope can be tied to issue scope.
- GitHub Issues can remain lightweight while local files preserve planning
  detail.

Negative:

- Local and GitHub issue metadata can drift.
- Requires discipline to update issue status and dependencies.

## Enforcement

Code review should reject:

- feature branches without a related issue or explicit Referee waiver.
- work started on issues with unresolved dependencies.
- local issue IDs reused for different work.
- PRs that omit local issue or GitHub issue references when applicable.
