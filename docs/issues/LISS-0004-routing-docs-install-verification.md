# LISS-0004: Routing Docs and Install Verification

## Metadata

- Local issue ID: LISS-0004
- Title: Routing docs and install verification
- Status: done
- Phase: docs-only
- Type: documentation
- Priority: medium
- Owner or agent: AI agent
- Related GitHub issue: none
- Parent issue: none
- Depends on: LISS-0002, and LISS-0003 if refactor changes public examples
- Blocks: none
- Related branch: feature/profile-based-routing

## Acceptance Notes

- Update README, `SKILL.md`, system prompt, sample config, and schema after the
  accepted behavior exists.
- Verify JSON resources parse.
- Verify install script still validates `SKILL.md` and required files.
- Keep examples honest about what the manager actually implements.

## Referee Decision Points

- Resolved: keep `routing_guidance` alongside the new executable
  `routing.profiles` config (documented as calling-agent-only guidance, not
  read by the manager), rather than replacing it.
- Resolved: docs include a relative-cost/reasoning-depth model catalog
  (`docs/architecture/model-routing-catalog.md`), scoped to models already
  named in this repo, without pricing numbers or benchmark scores. A new
  `standard` profile (`openai` / `gpt-5.4`) was added to
  `references/ollama_cluster_config.sample.json` so all four
  `task_complexity` levels used in `SKILL.md` have a matching executable
  profile, ordered cheapest-first for cost minimization.
- See
  `docs/collaboration/traces/2026-07-05-routing-docs-install-verification.md`
  and its follow-up entry for both decisions.
