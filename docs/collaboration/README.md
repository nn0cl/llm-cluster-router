# LLM Project Template – Collaboration Guide

> Clean Architecture + AT-TDD + Referee-driven AI collaboration template.

[日本語ガイド](README.ja.md)

This document is the English entry point for the collaboration template applied
in this repository. It is separate from the product README at the repository
root so product documentation and process documentation do not overwrite each
other.

The formal operating contract for AI agents is `AGENTS.md`, `CLAUDE.md`, and
`.github/copilot-instructions.md`. Read those before coding.

## What this template is for

Use this template when you want to:

- keep AI-assisted development reviewable and phase-based, not ad-hoc chat.
- make Referee decisions and architecture changes explicit.
- keep business logic out of adapters, UI handlers, and provider clients.
- minimize AI context payloads and keep privacy and cost under control.
- record architecture decisions and AI work traces next to the code.

The template is intentionally local-first and stack-agnostic. It does not choose
your domain model, datastore, provider APIs, or LLMs. Those remain decisions
for each target project.

## Key ideas

- No implementation without a reviewed acceptance specification.
- No phase skipping. Use Phase 1 Red, Phase 2 Green, Phase 3 Refactor.
- Referee-driven decisions. Referees approve phase transitions and ADRs.
- Context minimization. Only send the context required for the task.
- AI output is untrusted text until reviewed and validated.
- Target project owns domain and stack choices. The template does not.

For details, see:

- `AGENTS.md` – agent operating contract.
- `CLAUDE.md` – Claude-specific instructions.
- `docs/architecture/README.md` – architecture overview.
- `docs/collaboration/definition-of-done.md` – phase-based completion rules.
- `docs/collaboration/template-benefits.md` – full benefit list.

## Operating paths

The template defines three operating paths. See
`docs/architecture/agent-quickstart.md` for the full rules.

- **Fast Path** – mechanical, local, low-risk work (typos, formatting, docs
  clarifications, deterministic checks). Use a compact design note instead of
  the full `[THOUGHT]` scaffold.
- **Feature Path** – feature work in AT-TDD phases:
  - Phase 1 Red: failing tests only, based on accepted specs.
  - Phase 2 Green: smallest readable implementation that passes reviewed tests.
  - Phase 3 Refactor: improve structure without changing behavior.
- **Architecture Path** – ADRs, prompt or instruction changes,
  privacy-sensitive routing, boundary changes, and process changes.

Each request starts with design intake sized to the selected path.

## Adopting the template into a target repo

See `docs/collaboration/adoption-guide.md` and
`docs/collaboration/project-start-guide.md` for full details.

In short:

1. Run `scripts/copy-ai-collaboration-files.sh --target /path/to/target-repo`.
2. Fill placeholders in `AGENTS.md`, `CLAUDE.md`,
   `.github/copilot-instructions.md`, and `docs/architecture/README.md`.
3. Add the first feature specification under `docs/specs/`.
4. Add only the architecture documents the target already needs.
5. Run `scripts/init-llm-context.sh .` in the target repo and paste the prompt
   into the first AI session.

For midway adoption into an existing project, use `--dry-run` first and avoid
`--force` unless the owner has reviewed every overwrite.

## How this relates to llm-cluster-router

`llm-cluster-router` is a concrete product that applies this template:

- It uses AT-TDD and Clean Architecture boundaries from this template.
- It treats external resources (providers, config, output paths) as ports.
- It documents AI request routing and reasoning contracts next to code.

The upstream template repository is
[nn0cl/llm-project-template](https://github.com/nn0cl/llm-project-template).
Read the collaboration docs here, then inspect this repository to see how they
are applied in a real project.
