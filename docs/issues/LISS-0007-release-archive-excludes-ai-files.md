# LISS-0007: Release archives exclude AI-operating files

## Metadata

- Local issue ID: LISS-0007
- GitHub issue: none
- Status: done
- Phase: docs-only
- Type: tooling
- Priority: medium
- Owner/agent: AI agent
- Related branch: feature/release-archive

## Summary

- When releasing this repository, AI-agent operating instructions
  (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and internal
  AI-TDD process directories under `docs/`) should not appear in
  distribution archives. Provide two mechanisms: `.gitattributes`
  `export-ignore` (covers GitHub Release auto-generated archives for free)
  and a build script (covers manual distribution and vendoring, including
  the case where a consumer adds this repo as a git submodule and gets a
  plain `git clone` that does NOT respect `export-ignore`).

## Acceptance Notes

- Add `.gitattributes` marking as `export-ignore`: `AGENTS.md`, `CLAUDE.md`,
  `.github/copilot-instructions.md`, `docs/at-tdd/`, `docs/collaboration/`,
  `docs/templates/`, `docs/issues/`, `docs/work-plans/`, `docs/evaluation/`.
  Keep `docs/architecture/` and `docs/specs/` (they document the router
  itself, not AI operating process).
- Add `scripts/build_release_archive.sh`: wraps `git archive` to produce
  `dist/llm-cluster-router-<short-sha>.tar.gz` and `.zip`. Must not
  duplicate the exclusion list; it relies entirely on `.gitattributes`.
- `dist/` must be ignored by git.
- Document both mechanisms, and the submodule caveat, in `README.md`.
- Verify the exclusion actually works via `git archive`/the build script,
  not just by reading `.gitattributes`.

## Dependencies

- Parent: none
- Depends on: none
- Blocks: none
- Related: none

## Referee Decision Points

- Resolved: exclude the full AI-operating file set (Option 1 of the choices
  presented), keeping `docs/architecture/` and `docs/specs/` as router
  design documentation.

## Context

- Included: existing `docs/` tree structure, `.github/` contents.
- Omitted: CI wiring for automated release builds (not requested; GitHub's
  own tag-archive generation already covers the primary case for free).
- Assumptions: A git submodule consumer gets a plain `git clone`/checkout,
  not a `git archive` export, so `.gitattributes` does not apply to that
  path — confirmed this is the reason a separate build script is also
  needed, not just `.gitattributes` alone.

## References

- `git archive` and `.gitattributes` `export-ignore` behavior verified
  directly in this session (see Verification), not assumed from memory.

## Work Notes

- `.gitattributes` `export-ignore` for a directory only takes effect once
  the `.gitattributes` file itself is committed (or `--worktree-attributes`
  is passed to `git archive`). Verified both cases in this session before
  committing, to avoid shipping a `.gitattributes` that silently does
  nothing.
- `scripts/build_release_archive.sh` accepts an optional ref argument
  (defaults to `HEAD`), so a specific tag/commit can be archived without
  checking it out first.

## Verification

- `bash -n scripts/build_release_archive.sh`: passed.
- Confirmed `.gitattributes` had no effect before being committed
  (everything still present in the test archive), then confirmed
  `--worktree-attributes` picks up the uncommitted file, then committed and
  confirmed plain `git archive HEAD` (no flag) now excludes the right paths
  — this is the exact mechanism GitHub's Release tarball generation uses.
- Ran `scripts/build_release_archive.sh`, extracted both the `.tar.gz` and
  `.zip` outputs, and confirmed `AGENTS.md`, `CLAUDE.md`,
  `.github/copilot-instructions.md`, and all six targeted `docs/`
  subdirectories are absent, while `README.md`, `docs/architecture/`, and
  `docs/specs/` are present.
