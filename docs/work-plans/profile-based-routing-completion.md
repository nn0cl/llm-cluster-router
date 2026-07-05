# Work Plan: Profile-Based LLM Routing

## Goal

- Complete routing support so the skill can classify a task and request a
  configured profile that selects Ollama, Claude, Codex, or OpenAI-compatible
  providers without relying on model-name guessing alone.

## Scope

- In:
  - Accepted spec for profile-based routing.
  - Phase 1 Red tests for profile and complexity routing.
  - Phase 2 minimal manager implementation.
  - Phase 3 refactor only after Green.
  - Documentation and install verification after behavior exists.
- Out:
  - Real provider network tests.
  - Automatic model pricing discovery.
  - Automatic SaaS model ranking.
  - New third-party dependencies.
  - Renaming existing Ollama-specific filenames or environment variables.

## Issue Graph

| Issue | Status | Depends on | Blocks | Branch |
| --- | --- | --- | --- | --- |
| LISS-0001 | proposed | Referee spec approval | LISS-0002, LISS-0003 | feature/profile-based-routing |
| LISS-0002 | proposed | LISS-0001 reviewed Red tests | LISS-0003, LISS-0004 | feature/profile-based-routing |
| LISS-0003 | proposed | LISS-0002 verified Green | LISS-0004 | feature/profile-based-routing |
| LISS-0004 | proposed | LISS-0002, optionally LISS-0003 | - | feature/profile-based-routing |

## Recommended Order

1. Referee reviews `docs/specs/profile-based-routing.md`.
2. Referee approves Phase 1 Red for LISS-0001.
3. Add failing tests only for explicit profile routing, complexity routing,
   preserved model routing, and unknown profile failure.
4. Referee reviews Red tests and approves Phase 2 Green.
5. Implement the smallest routing change that passes reviewed tests.
6. Run unit, compile, shell syntax, and JSON validation checks.
7. Referee approves Phase 3 Refactor if the Green implementation needs cleanup.
8. Update docs and install verification in LISS-0004.

## Current Next Issue

- Issue: LISS-0001
- Reason it is unblocked: The draft acceptance spec and work plan now exist.
- Referee approval needed: Approve the spec and Phase 1 Red before tests are
  written.

## Risks

- Profile routing can accidentally override current loaded-Ollama preference.
- `routing_guidance` examples may be mistaken for implemented manager behavior.
- Codex SDK behavior is optional and should remain testable without installing
  the SDK.
- Claude credentials must stay out of tests, traces, and examples.

## Verification Plan

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_ollama_cluster_router_skill.py`
- `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/install_skill.py`
- `python3 -m json.tool references/ollama_cluster_config.sample.json >/dev/null`
- `python3 -m json.tool references/agent_tool_schema.json >/dev/null`
- `bash -n scripts/setup_skill.sh`
