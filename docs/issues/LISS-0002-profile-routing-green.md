# LISS-0002: Profile Routing Green Implementation

## Metadata

- Local issue ID: LISS-0002
- Title: Profile routing Green implementation
- Status: done
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

- Approve Phase 2 Green only after reviewing Red tests. (Approved: Referee
  continued to Phase 3 Refactor and then LISS-0004.)
- Resolved in LISS-0004: keep `routing_guidance` and add executable
  `routing.profiles` side by side rather than replacing it. See
  `docs/collaboration/traces/2026-07-05-routing-docs-install-verification.md`.
