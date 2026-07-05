# LISS-0002: Profile Routing Green Implementation

## Metadata

- Local issue ID: LISS-0002
- Title: Profile routing Green implementation
- Status: review
- Phase: phase-2-green
- Type: feature-implementation
- Priority: high
- Owner or agent: AI agent
- Related GitHub issue: none
- Parent issue: none
- Depends on: LISS-0001 reviewed Red tests
- Blocks: LISS-0003, LISS-0004
- Related branch: feature/profile-based-routing

## Acceptance Notes

- Implement only enough routing logic to pass reviewed Phase 1 tests.
- Preserve current model-based routing when no `routing_profile` or
  `task_complexity` is present.
- Keep provider execution behavior unchanged.
- Return routing evidence in metadata when profile routing is used.
- Do not add provider model-list API calls or new dependencies.

## Result

- Added minimal routing profile resolution in the manager.
- Preserved current model-based routing when no routing hint is present.
- Returned `routing_profile` or `task_complexity` metadata when profile
  routing is used.
- Verification passed: 12 unit tests, Python compile checks, JSON validation,
  and shell syntax check.

## Referee Decision Points

- Approve Phase 2 Green only after reviewing Red tests.
- Decide whether the implementation may update the sample config contract from
  `routing_guidance` to executable `routing.profiles`.
