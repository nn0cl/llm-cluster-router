# LISS-0027: Sakana interchangeability refactor and documentation

## Metadata

- Local issue ID: LISS-0027
- GitHub issue: none
- Status: review
- Phase: phase-3-refactor
- Type: refactor
- Priority: medium
- Owner/agent: AI agent
- Related branch: feature/sakana-ollama-interchangeability

## Summary

Update provider mapping and documentation after behavior is Green. The public
manager surface is preserved; orchestration and CLI thinning remain tracked by
LISS-0022.

## Acceptance Notes

- `OllamaClusterManager` remains the public compatibility surface.
- Routing policy does not import provider adapters.
- Provider adapters do not implement fallback or cost-tier policy.
- Ollama and Sakana paths are readable and separately testable.
- Configuration and documentation describe `sakana` / `fugu` and
  `SAKANA_API_KEY` without committing secrets.
- Configuration documents retry count 0–3, default 3, and the no-fallback
  policy.
- Behavior and test assertions remain unchanged.
- Final review includes remaining error, cache, privacy, and provider drift
  risks.

## Dependencies

- Parent: LISS-0023
- Depends on: LISS-0026 verified Green
- Blocks: none
- Related: `docs/architecture/manager-split-plan.md`,
  `docs/architecture/README.md`, `README.md`, `README.ja.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py scripts/install_skill.py`
- `python3 -m json.tool references/ollama_cluster_config.sample.json >/dev/null`
- `python3 -m json.tool references/agent_tool_schema.json >/dev/null`
- `git diff --check`
