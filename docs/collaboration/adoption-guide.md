# Collaboration Template Adoption Guide

Use this guide after copying the collaboration template into a new or existing
repository. It is intentionally separate from the target repository README so
midway adoption does not overwrite product documentation.

For the benefits and tradeoffs of using the template, see
`docs/collaboration/template-benefits.md`.

## New Repository Adoption

1. Run `scripts/copy-ai-collaboration-files.sh --target <repo>`.
2. Fill generic placeholders in `AGENTS.md`, `CLAUDE.md`,
   `.github/copilot-instructions.md`, and `docs/architecture/README.md`.
3. Add the first target feature specification under `docs/specs/`.
4. Add only the stack-specific architecture documents that the project already
   needs.
5. Read `docs/collaboration/project-start-guide.md` for the first development
   loop.
6. Run `scripts/init-llm-context.sh <repo>` and paste the generated prompt into
   the first agent session.

## Midway Adoption

1. Run `scripts/copy-ai-collaboration-files.sh --target <repo> --dry-run`.
2. Run the copy without `--force` so existing target files remain unchanged.
3. Review skipped files and decide manually whether any target-owned document
   should adopt collaboration wording.
4. Keep accepted target architecture and feature specifications authoritative.
5. Use Fast Path for mechanical adoption cleanup, Feature Path for accepted
   feature work, and Architecture Path for process or boundary decisions.

## LLM Session Setup

Use `scripts/init-llm-context.sh <repo>` to print a compact first prompt.

The prompt instructs the agent to:

- read `AGENTS.md` and `docs/architecture/agent-quickstart.md`.
- select Fast Path, Feature Path, or Architecture Path.
- avoid introducing target stack, datastore, provider, or domain decisions
  without an accepted specification or ADR.
- stop when the target specification or requested phase is missing.

## Cost and Reasoning Control

Use `docs/collaboration/llm-cost-reduction.md` to keep LLM cost control
observable without adding heavy process. For substantial tasks, traces should
record the selected operating path, omitted context, deterministic checks, and
any escalation reason.

## Adoption Safety Rules

- Do not use this template to replace target project architecture.
- Do not ship target-specific domain models as part of the reusable template.
- Do design the target domain model after adoption, through target specs,
  reviewed tests, Referee decisions, and ADRs.
- Do not use `--force` unless the target owner has reviewed each overwrite.
- Do not treat placeholder examples as selected technology.
- Keep target secrets, private data, and full exports out of AI prompts.
- Prefer deterministic checks over AI reasoning for copy verification,
  formatting, parsing, and CI sanity.
