# LISS-0017: Manager types and safety extraction

## Metadata

- Local issue ID: LISS-0017
- GitHub issue: none
- Status: done
- Phase: phase-3-refactor
- Type: refactor
- Priority: high
- Owner/agent: AI agent
- Related branch: feature/sakana-ollama-interchangeability

## Summary

First slice of the manager module split: move shared datatypes and output-path /
fence-stripping helpers out of `scripts/ollama_cluster_manager.py` without
changing behavior.

## Acceptance Notes

- Create `scripts/router/models.py` and `scripts/router/safety.py` per
  `docs/architecture/manager-split-plan.md`.
- `OllamaClusterManager` public behavior remains unchanged.
- All existing tests pass without assertion edits.
- No routing or provider behavior changes in this issue.

## Dependencies

- Parent: none
- Depends on: Referee approval of `docs/architecture/manager-split-plan.md`
- Blocks: LISS-0020
- Related: `docs/work-plans/manager-module-split.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py`
