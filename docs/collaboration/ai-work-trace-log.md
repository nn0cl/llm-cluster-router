# AI Work Trace Log

AI work traces record the important process choices made during AI-assisted
development. They are not application logs and must not contain secrets or
full exports of private data.

## Location

Store task traces under:

```text
docs/collaboration/traces/
```

Use one Markdown file per substantial task:

```text
YYYY-MM-DD-short-task-name.md
```

Keep `docs/collaboration/traces/.gitkeep` so the folder exists before the first
trace is created.

## When Required

Create or update a trace when:

- a task changes agent instructions, templates, ADRs, or collaboration rules.
- a task spans more than one phase.
- a task uses external AI, cloud providers, or non-default model routing.
- a task is paused and another agent may resume it.
- the Referee asks for an audit trail.

Trace is optional for tiny documentation-only changes when the final response
already includes enough context.

## Trace Contents

Each trace should include:

- user request.
- current phase.
- included context.
- omitted context.
- model, assistant, or deterministic tool routing.
- operating path and cost/reasoning control signals.
- Referee decisions.
- assumptions.
- open decisions.
- verification run.
- changed files.
- next safe action.

See `docs/collaboration/llm-cost-reduction.md` for the lightweight cost and
reasoning control fields used in traces.

## Privacy Rules

Do not put these in a trace:

- secrets or API keys.
- full `.env` values.
- full exports of private user or business data.
- provider raw responses unless explicitly approved.

Use short excerpts and source references instead.
