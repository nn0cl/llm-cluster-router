# LISS-0018: Fallback routing Green implementation

## Metadata

- Local issue ID: LISS-0018
- GitHub issue: none
- Status: wont_do
- Phase: docs-only
- Type: feature
- Priority: high
- Owner/agent: AI agent
- Related branch: feature/fallback-routing

## Summary

Do not implement configured `fallback_profiles`; runtime provider fallback is
prohibited.

## Acceptance Notes

- No production fallback code is added.
- Retry exhaustion returns the selected provider's classified error.

## Dependencies

- Parent: none
- Depends on: none
- Blocks: none
- Related: `docs/specs/fallback-routing.md`, `docs/work-plans/fallback-routing.md`

## Verification

- No implementation verification; issue is cancelled.
