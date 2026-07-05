# AI Work Trace

## Request

- Date: 2026-07-05
- User request: Continue from the profile-routing refactor to the next issue
  (LISS-0004).
- Current phase: Fast Path, docs-only.

## Context Ledger

- Included: LISS-0004 acceptance notes, `docs/specs/profile-based-routing.md`,
  the Green/Refactor manager implementation (`resolve_routing_profile`,
  `choose_configured_profile_host`), existing routing tests, and the docs
  files listed in the acceptance notes.
- Omitted: pricing/reasoning-cost model catalog examples (left as the still-
  open Referee decision point), fallback-routing design, and any provider
  network calls.
- Assumptions: None beyond the Referee's explicit answer below.
- Open decisions: Whether to add a pricing/reasoning-cost model catalog to the
  docs (unchanged from LISS-0004's original open point).

## Ambiguity Resolved

- The spec's own "Ambiguities" section asked whether `routing_guidance`
  should remain a calling-agent hint or be replaced by executable
  `routing.profiles`. Asked the Referee directly; the Referee said to
  determine the correct behavior from file timestamps. Trace timestamps show
  `routing_guidance` was added at 20:33 (`configure-claude-codex-targets`,
  explicitly "does not implement manager-level profile routing"), while
  executable `routing.profiles` was implemented later in Green (20:57) and
  Refactor (20:59). Conclusion: `routing.profiles` is the newer, accepted,
  executable mechanism; `routing_guidance` is kept as older, calling-agent-only
  descriptive guidance, not read by the manager.

## Routing

- Model/assistant/tool: Fast Path documentation edits with deterministic
  checks only.
- Reason: Mechanical, local doc/config updates that do not change tested
  behavior.
- Privacy constraints: No secrets or private provider data were read or
  copied.

## Cost / Reasoning Control

- Operating path: Fast Path.
- Files read: LISS-0004, profile-based-routing spec, manager script, routing
  tests, README.md, README.ja.md, SKILL.md, agent_system_prompt.md,
  agent_tool_schema.json, ollama_cluster_config.sample.json, install_skill.py.
- Context intentionally omitted: unrelated docs, real provider credentials,
  runtime provider status.
- Deterministic checks used: JSON validation, unittest, Python compile checks,
  shell syntax check, and a direct call to `install_skill.validate_source`.
- Escalation reason: None; stayed within Fast Path.
- Avoided LLM work: Did not call any configured LLM provider.
- Rework caused by AI output: None.

## Referee Decisions

- Keep `routing_guidance` and add `routing.profiles` side by side (see
  Ambiguity Resolved above), determined by timestamp precedence per the
  Referee's instruction.

## Verification

- Commands/checks:
  - `python3 -m json.tool references/ollama_cluster_config.sample.json`
  - `python3 -m json.tool references/agent_tool_schema.json`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_ollama_cluster_router_skill.py`
  - `bash -n scripts/setup_skill.sh`
  - `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/install_skill.py tests/test_ollama_cluster_router_skill.py`
  - `install_skill.validate_source(Path("."))` called directly to confirm
    `SKILL.md` and required files still validate.
- Result: All checks passed. Unit test count is 12 (unchanged).

## Changed Files

- `references/ollama_cluster_config.sample.json`
- `references/agent_tool_schema.json`
- `references/agent_system_prompt.md`
- `SKILL.md`
- `README.md`
- `docs/issues/LISS-0004-routing-docs-install-verification.md`
- `docs/collaboration/traces/2026-07-05-routing-docs-install-verification.md`

## Next Safe Action

- Referee reviews the doc/config wording and decides the still-open point:
  whether to add a pricing/reasoning-cost model catalog example.

## Follow-Up: Model Routing Catalog (same day)

- User request: Assume the manager routes per-SaaS by task/model. Summarize
  currently known models with difficulty/reasoning depth in docs, and adjust
  the sample config for overall cost-minimal, reasonably efficient routing.
  This resolves the "still open" point above.
- Context ledger: Included the existing four `task_complexity` names already
  named in `SKILL.md` (`easy`, `standard`, `hard`, `agentic`), the models
  already named in this repo (`qwen2.5-coder:7b`, `gpt-5.4`,
  `claude-sonnet-4-5`), and the sample config's existing host `priority`
  ordering (local free hosts highest, then paid providers descending).
  Omitted: real pricing figures, benchmark scores, and any model not already
  referenced in this repo, since none of those are verifiable from repo
  content and would be guesses.
- New file: `docs/architecture/model-routing-catalog.md`. Uses relative cost
  tier (free/paid-low/paid-higher) and relative reasoning depth
  (shallow/moderate/deep) instead of numbers, and explicitly scopes itself to
  models already named in the repo to avoid inventing a model catalog.
- Config change: added a `standard` profile
  (`{"provider": "openai", "model": "gpt-5.4"}`) to `routing.profiles` and a
  matching `routing_guidance.standard` entry in
  `references/ollama_cluster_config.sample.json`, closing the gap where
  `SKILL.md` named a `standard` complexity level with no matching executable
  profile. `default_profile` stays `easy` (free local tier), so cost
  minimization is the default when no profile is requested.
- Doc updates: `README.md` and `SKILL.md` now point at the catalog and state
  the cost-minimization principle (escalate one tier at a time, starting from
  `easy`).
- Verification: re-ran the same JSON validation, unit tests (12, unchanged),
  and `install_skill.validate_source` check; all passed.
- Changed files (this follow-up): `docs/architecture/model-routing-catalog.md`
  (new), `references/ollama_cluster_config.sample.json`, `README.md`,
  `SKILL.md`, `docs/issues/LISS-0004-routing-docs-install-verification.md`,
  this trace file.
- Next safe action: Referee reviews the catalog's cost-tier/reasoning-depth
  judgments and the new `standard` profile choice of `openai`/`gpt-5.4`.
