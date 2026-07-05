# LISS-0001: Profile Routing Red Tests

## Metadata

- Local issue ID: LISS-0001
- Title: Profile routing Red tests
- Status: done
- Phase: phase-1-red
- Type: feature-test
- Priority: high
- Owner or agent: AI agent
- Related GitHub issue: none
- Parent issue: none
- Depends on: Referee approval of `docs/specs/profile-based-routing.md`
- Blocks: LISS-0002, LISS-0003
- Related branch: feature/profile-based-routing

## Acceptance Notes

- Add failing tests only.
- Cover explicit `routing_profile` selection for Claude.
- Cover `task_complexity` selection for Codex.
- Cover current model-based routing when no routing hint is present.
- Cover unknown profile failure before provider execution.
- Mock provider calls through the existing fake HTTP client or local test
  doubles. Do not call real providers.

## Result

- Added Phase 1 Red tests for profile-based Claude routing, complexity-based
  Codex routing, existing no-hint model routing, and unknown profile failure.
- Red state was confirmed before Phase 2: 12 tests ran with 3 expected
  failures.

## Referee Decision Points

- Approve Phase 1 Red.
- Confirm the proposed config contract under
  `docs/specs/profile-based-routing.md`.
- Decide whether fallback behavior is in scope for the first feature slice.
