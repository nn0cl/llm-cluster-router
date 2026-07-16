# Work Plan: Manager Module Split

## Goal

Split `scripts/ollama_cluster_manager.py` into reviewable modules following
`docs/architecture/manager-split-plan.md` without changing external behavior.

## Scope

- In:
  - Incremental Phase 3 Refactor slices listed in the split plan.
  - Preserved CLI, MCP, and test contracts.
  - Documentation updates for new module locations after each slice.
- Out:
  - Behavior changes not covered by an accepted spec.
  - New dependencies.
  - Renaming environment variables or sample config filenames.

## Issue Graph

| Issue | Status | Depends on | Blocks | Branch |
| --- | --- | --- | --- | --- |
| LISS-0017 | done | Referee split-plan approval | LISS-0020 | feature/sakana-ollama-interchangeability |
| LISS-0020 | done | LISS-0017 | LISS-0021 | feature/sakana-ollama-interchangeability |
| LISS-0021 | done | LISS-0020 | LISS-0022 | feature/sakana-ollama-interchangeability |
| LISS-0022 | in_progress | LISS-0021 | - | feature/sakana-ollama-interchangeability |

## Recommended Order

1. Referee reviews `docs/architecture/manager-split-plan.md`.
2. Do not add fallback routing; the withdrawn fallback proposal is recorded in
   `docs/work-plans/fallback-routing.md`.
3. LISS-0017: extract types and safety helpers.
4. LISS-0020: extract routing policy without fallback behavior.
5. LISS-0021: extract provider adapters and thin CLI shell.
6. Run full unit and compile checks after every slice.

## Current Next Issue

- LISS-0022: move orchestration to `scripts/router/manager.py` and keep the
  public CLI module as a compatibility shell.

## Verification Plan

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/ollama_cluster_manager.py scripts/mcp_server.py scripts/install_skill.py`
- `bash -n scripts/setup_skill.sh`
