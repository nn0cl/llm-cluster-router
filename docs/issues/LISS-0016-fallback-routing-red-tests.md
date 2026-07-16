# LISS-0016: Fallback routing Red tests

## Metadata

- Local issue ID: LISS-0016
- GitHub issue: none
- Status: wont_do
- Phase: docs-only
- Type: feature
- Priority: high
- Owner/agent: AI agent
- Related branch: feature/fallback-routing

## Summary

Withdraw the proposed fallback-routing Red tests because runtime provider
fallback is prohibited.

## Acceptance Notes

- No fallback tests remain in the active test suite.
- No production implementation is permitted by this issue.

## Dependencies

- Parent: none
- Depends on: Referee approval of `docs/specs/fallback-routing.md`
- Blocks: none
- Related: `docs/work-plans/fallback-routing.md`

## Referee Decision Points

- Resolved 2026-07-16: runtime fallback to another provider or mock provider is
  prohibited.

## Work Notes

- Related branch: `feature/fallback-routing`
- Issue closed as `wont_do`; production code was not changed.

## Verification

- No implementation verification; the proposed tests were removed from the
  active test file.
