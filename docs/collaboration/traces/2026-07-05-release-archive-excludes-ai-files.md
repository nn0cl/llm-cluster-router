# AI Work Trace

## Request

- Date: 2026-07-05
- User request: When releasing this repository, exclude AI-agent operating
  instructions (AGENTS.md, etc.) from the output. Asked for method
  recommendations, then whether a git submodule clone would bypass that,
  then proposed doing both `.gitattributes` export-ignore and a shell
  script producing a compressed archive.
- Current phase: docs-only / Fast Path tooling, LISS-0007.

## Context Ledger

- Included: current `docs/` tree structure, `.github/` contents,
  `scripts/setup_skill.sh` and `scripts/setup_mcp_venv.sh` for shell-script
  style conventions.
- Omitted: CI automation for release builds (not requested).
- Assumptions: none beyond the explicitly confirmed exclusion scope (see
  Referee Decisions).

## Routing

- Model/assistant/tool: exploratory Q&A first (git archive vs submodule
  behavior), then direct Fast Path implementation once scope was confirmed.
- Reason: The user asked "what method" (exploratory) before committing to
  an approach, per this project's design-first practice.
- Privacy constraints: none applicable.

## Cost / Reasoning Control

- Operating path: Fast Path (docs/config/script, no behavior change to
  `OllamaClusterManager` or the MCP adapter).
- Files read: see Context Ledger.
- Context intentionally omitted: unrelated docs.
- Deterministic checks used: `bash -n`, `git archive` run three times under
  different conditions (uncommitted `.gitattributes` with no flag, with
  `--worktree-attributes`, and after committing) to prove the mechanism
  actually works rather than assuming from `.gitattributes` documentation,
  plus a real extraction and file-presence check of both `.tar.gz` and
  `.zip` outputs.
- Escalation reason: none.
- Avoided LLM work: did not call any configured LLM provider.
- Rework caused by AI output: none.

## Referee Decisions

- Asked which paths count as "AI-operating files" to exclude, since the
  boundary is a judgment call, not something derivable from code. Referee
  chose the full AI-operating file set: `AGENTS.md`, `CLAUDE.md`,
  `.github/copilot-instructions.md`, `docs/at-tdd/`, `docs/collaboration/`,
  `docs/templates/`, `docs/issues/`, `docs/work-plans/`, `docs/evaluation/`.
  `docs/architecture/` and `docs/specs/` are kept as router design docs.

## Verification

- Commands/checks:
  - `bash -n scripts/build_release_archive.sh`
  - `git archive -o test.tar.gz HEAD` before committing `.gitattributes`:
    confirmed exclusion did NOT apply yet (proves the "must be committed,
    or use --worktree-attributes" caveat is real, not assumed).
  - `git archive --worktree-attributes -o test2.tar.gz HEAD`: confirmed
    exclusion applies to the uncommitted file.
  - Committed `.gitattributes`, then `git archive -o test3.tar.gz HEAD`
    (no flag): confirmed exclusion applies by default once committed — the
    same mechanism GitHub Release tarball generation uses.
  - Ran `scripts/build_release_archive.sh`, extracted both `.tar.gz` and
    `.zip`, confirmed `AGENTS.md`/`CLAUDE.md`/`.github/copilot-instructions.md`
    and all six targeted `docs/` subdirectories are absent, while
    `README.md`, `docs/architecture/`, and `docs/specs/` are present.
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`:
    16 tests, 3 skipped (mcp not installed in the main environment), 0
    failures — confirms this change did not affect existing behavior.
  - `install_skill.validate_source(Path("."))`: still passes.
- Result: All checks passed.

## Changed Files

- `.gitattributes` (new, committed separately as `87f7621`)
- `scripts/build_release_archive.sh` (new)
- `.gitignore` (added `dist/`)
- `README.md` (new "Release Archives" section)
- `docs/issues/LISS-0007-release-archive-excludes-ai-files.md` (new)
- `docs/collaboration/traces/2026-07-05-release-archive-excludes-ai-files.md`
  (this file)

## Next Safe Action

- Referee reviews the exclusion list and the `scripts/build_release_archive.sh`
  naming/output convention (`dist/llm-cluster-router-<short-sha>.{tar.gz,zip}`),
  then decides whether to commit and push.
