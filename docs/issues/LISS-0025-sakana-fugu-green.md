# LISS-0025: Sakana Fugu provider Green implementation

## Metadata

- Local issue ID: LISS-0025
- GitHub issue: none
- Status: done
- Phase: phase-2-green
- Type: feature
- Priority: high
- Owner/agent: AI agent
- Related branch: feature/sakana-ollama-interchangeability

## Summary

Implement the smallest readable Sakana Fugu adapter path and provider-neutral
DTOs needed to pass the reviewed Red tests.

## Acceptance Notes

- Support `provider: "sakana"`, default URL `https://api.sakana.ai`, model
  `fugu`, and `SAKANA_API_KEY`.
- Send Responses API requests through the existing replaceable HTTP boundary.
- Map Fugu output text and usage into the common result contract.
- Preserve existing Ollama behavior and public manager entry points.
- Do not add runtime fallback to another provider or a mock provider.
- Do not add SDK or real-network test dependencies.
- Do not edit reviewed Red tests to make them pass.

## Dependencies

- Parent: LISS-0023
- Depends on: LISS-0024 reviewed Red tests and provider adapter extraction
- Blocks: LISS-0026
- Related: LISS-0021, `docs/specs/sakana-ollama-interchangeability.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py`
