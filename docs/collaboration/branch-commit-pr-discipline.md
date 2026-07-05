# Branch, Commit, and PR Discipline

This document defines Git workflow for AI-TDD collaboration.

## Branches

Create branches by feature or process task.

Recommended branch names:

```text
feature/<short-feature-name>
test/<short-behavior-name>
refactor/<short-area-name>
docs/<short-topic>
process/<short-process-topic>
chore/<short-maintenance-topic>
```

Rules:

- one branch should represent one feature, process change, or reviewable unit.
- feature branches should be tied to a local issue, GitHub issue, or explicit
  Referee waiver.
- do not mix unrelated documentation, tests, implementation, and refactor work.
- do not start Phase 2 implementation on a branch whose Phase 1 tests have not
  been reviewed.
- branch names should describe user-visible feature or process purpose, not the
  AI tool used.

## Commits

Prefer commits by phase:

```text
docs: add design intake for <topic>
test: add red tests for <behavior>
feat: implement <behavior>
refactor: clarify <area>
chore: update process tooling
```

Rules:

- keep commits reviewable.
- do not hide test changes inside implementation commits.
- mention AI assistance in PR notes when it materially shaped the change.
- never commit secrets or full exports of private data.

## Pull Requests

PRs should identify:

- current phase.
- Referee approval points.
- changed files.
- deterministic verification.
- whether tests were reviewed before implementation.
- whether AI payload included private context.

## Feature-Unit Branch Creation

When starting a new feature:

1. create or update local issue and work plan files.
2. verify issue dependencies are resolved or waived.
3. create or update the design intake.
4. create a feature branch.
5. add Phase 1 tests only.
6. wait for Referee review.
7. continue with Phase 2 on the same feature branch or a clearly linked branch.

Recommended command shape:

```text
git switch -c feature/<short-feature-name>
```

Use `docs/architecture/agent-quickstart.md` before making changes on the branch.

See `docs/collaboration/local-issue-planning.md` for local issue and dependency
rules.
