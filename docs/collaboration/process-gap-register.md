# AI-TDD Collaboration Gap Register

This register tracks collaboration-process gaps. It intentionally avoids
application-internal design.

## Purpose

Keep the AI-TDD plus human collaboration scheme honest by making missing
process controls visible.

## How to Use This Register

When starting a new project from this template, the gaps below are already
resolved by the included documents — keep them as a record of what the process
covers. Add a new entry whenever you find a real collaboration-process gap
(not an application feature gap) that this template does not yet address, and
resolve it the same way these were resolved: write the missing document, link
it here, and mark the status `resolved`.

## Gaps Covered By This Template

### 1. Definition of Done

Status: resolved.

Why it matters:

- Agents need a clear stopping point for each phase.
- Referees need a quick approval checklist.

Resolution:

- Use `docs/collaboration/definition-of-done.md`.

### 2. Prompt and Instruction Change Control

Status: resolved.

Why it matters:

- Agent behavior depends on prompts, instruction files, templates, and ADRs.
- Changes to these files can silently alter development behavior.

Resolution:

- Use `docs/collaboration/prompt-instruction-change-control.md`.
- See `docs/architecture/adr/0006-prompt-instruction-change-control.md`.
- CI enforces that a pull request changing a contract file also adds a trace
  under `docs/collaboration/traces/`.

### 3. AI Work Trace Log

Status: resolved.

Why it matters:

- Handoff notes capture a task ending, but not always the sequence of important
  choices during a task.

Resolution:

- Use `docs/collaboration/ai-work-trace-log.md`.
- Store traces under `docs/collaboration/traces/`.
- Use `docs/templates/ai-work-trace.md`.

### 4. Evaluation and Golden Examples

Status: resolved.

Why it matters:

- AI-generated tests, summaries, and extraction outputs need regression checks.
- Without golden examples, quality can drift while still sounding plausible.

Resolution:

- Use `docs/collaboration/evaluation-and-golden-examples.md`.
- Store examples under `docs/evaluation/golden-examples/`.
- Store criteria under `docs/evaluation/criteria/`.

### 5. Model and Tool Capability Matrix

Status: resolved.

Why it matters:

- Tasks should route to the right model or tool, but the concrete matrix
  needs to be explicit rather than assumed.

Resolution:

- Use `docs/collaboration/model-tool-capability-matrix.md`.

### 6. Privacy and Context Budget Policy

Status: resolved.

Why it matters:

- Payload minimization is a goal, but needs a numeric or categorical budget to
  be enforceable.

Resolution:

- Use `docs/collaboration/privacy-context-budget-policy.md`.

### 7. AI Failure and Recovery Procedure

Status: future.

Why it matters:

- The process says when to stop, but not how to recover from a bad AI turn.

Needed:

- How to identify a contaminated phase.
- How to preserve user changes.
- How to restart from last trusted artifact.
- How to document rejected AI output.

### 8. Branch, Commit, and PR Discipline

Status: resolved.

Why it matters:

- AI-assisted work needs branch/commit conventions, not just a PR template.

Resolution:

- Use `docs/collaboration/branch-commit-pr-discipline.md`.

### 9. Local Issue and Work Plan Management

Status: resolved.

Why it matters:

- Planning needs issue dependencies and work order before coding starts.
- GitHub Issues may not be available during local or offline planning.

Resolution:

- Use `docs/collaboration/local-issue-planning.md`.
- Store local issues under `docs/issues/`.
- Store multi-issue plans under `docs/work-plans/`.

## Current Assessment

Ready enough to start design intake and Phase 1 work once the project's
architecture documents are filled in.

Not yet mature enough for high-volume parallel agents without adding AI
failure and recovery procedure (gap 7).
