# LLM Cost and Reasoning Control

This document defines lightweight practices for reducing unnecessary use of
high-capability LLM coding services. It does not define billing integration,
model pricing, or telemetry infrastructure.

## Goal

Reduce avoidable LLM cost by making agents:

- choose the smallest safe operating path.
- prefer deterministic tools for facts and verification.
- avoid broad context loading.
- record why stronger reasoning was needed.
- make rework visible when AI output caused it.

## Non-Goals

- Tracking exact token counts.
- Choosing specific commercial models.
- Building a centralized cost dashboard.
- Requiring private prompts, provider logs, or billing exports in the repo.

## Cost Control Signals

Each substantial trace should record:

- `Operating path`: Fast Path, Feature Path, or Architecture Path.
- `Files read`: approximate count or short list.
- `Context intentionally omitted`: important context classes that were not
  loaded.
- `Deterministic checks used`: commands, tests, formatters, linters, or search.
- `Escalation reason`: why a stronger model or deeper reasoning was needed.
- `Avoided LLM work`: work handled by tools, existing specs, or narrow context.
- `Rework caused by AI output`: none, minor, or a short description.

Keep these entries short. The goal is trend visibility, not accounting
precision.

## Review Questions

During review, ask:

- Could this have used Fast Path?
- Did the agent read more files than the task needed?
- Was a deterministic tool available for a fact the model reasoned about?
- Was escalation to a stronger reasoning agent justified?
- Did missing specification or unclear phase cause avoidable rework?

## Healthy Trends

Over time, a project should see:

- more mechanical work completed through Fast Path.
- fewer architecture-path escalations for local edits.
- traces that clearly explain why strong reasoning was used.
- fewer broad context dumps.
- fewer changes caused by guessed requirements.

## Warning Signs

Investigate when:

- many traces say the operating path was Architecture Path for small edits.
- agents repeatedly read whole directories for local changes.
- verification is described in prose but no deterministic check was run.
- AI output causes repeated rework or test changes.
- Referee review repeatedly rejects work for phase or scope drift.
