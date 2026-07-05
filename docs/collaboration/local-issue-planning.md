# Local Issue Planning

Issues can be managed in GitHub and as local Markdown files.

Local issue files are useful when:

- planning offline.
- preparing work before a GitHub repository is connected.
- letting AI agents reason about issue dependencies without network access.
- keeping feature-unit branch planning close to the repository.

GitHub Issues remain useful for remote collaboration, notifications, and public
review. Local issues are the repository-native planning ledger.

## Location

Store local issues under:

```text
docs/issues/
```

Store multi-issue work plans under:

```text
docs/work-plans/
```

Keep `.gitkeep` files in both folders so they exist before the first issue or
plan is created.

## Issue File Naming

Use stable local IDs:

```text
LISS-0001-short-title.md
LISS-0002-short-title.md
```

`LISS` means local issue. Do not reuse IDs.

When a GitHub Issue exists, add its number or URL in the local issue metadata.

## Required Issue Fields

Each local issue should record:

- local issue ID.
- title.
- status.
- phase.
- type.
- priority.
- owner or agent.
- related GitHub issue when available.
- parent issue when any.
- depends on.
- blocks.
- related branch.
- acceptance notes.
- Referee decision points.

## Dependency Rules

Use issue dependencies to define work order before implementation.

Allowed dependency meanings:

- `depends_on`: this issue should not start before the listed issue is done or
  explicitly waived.
- `blocks`: listed issues are blocked by this issue.
- `parent`: this issue is part of a larger work item.
- `related`: useful context, but not an ordering constraint.

Agents must not start work on an issue with unresolved `depends_on` entries
unless the Referee explicitly waives the dependency.

## Planning Flow

Before starting feature work:

1. create or update local issues.
2. identify issue dependencies.
3. create a work plan under `docs/work-plans/`.
4. select the next unblocked issue.
5. create a feature-unit branch for that issue or feature slice.
6. run design intake.

## Status Values

Use:

- `proposed`
- `ready`
- `in_progress`
- `blocked`
- `review`
- `done`
- `wont_do`

## Phase Values

Use:

- `phase-0-design`
- `phase-1-red`
- `phase-2-green`
- `phase-3-refactor`
- `docs-only`
- `process-only`

## Synchronization with GitHub Issues

When both local and GitHub issues exist:

- keep the local issue as the detailed planning artifact.
- keep GitHub Issue title, status, and links aligned when practical.
- include the GitHub Issue URL in the local issue.
- include the local issue ID in the GitHub Issue or PR text.

Do not require GitHub network access for local planning.

## Review Rule

Referee review is required when:

- issue dependencies are unclear.
- an issue is split or merged.
- work starts despite unresolved dependencies.
- the planned branch scope does not match the issue scope.
