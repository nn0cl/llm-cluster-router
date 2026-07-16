# LISS-0020: Routing policy extraction

## Metadata

- Local issue ID: LISS-0020
- Status: done
- Phase: phase-3-refactor
- Type: refactor
- Priority: high
- Related branch: feature/sakana-ollama-interchangeability

## Acceptance Notes

- Profile resolution and host priority selection live in `scripts/router/routing.py`.
- The routing module imports no provider adapter module.
- Runtime fallback is not introduced.
- Existing public manager behavior and tests remain unchanged.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
