# Stack-Specific Examples

These files are not part of the generic template. They are worked examples
taken from the project this template was extracted from (a Tauri + Rust +
React desktop app), kept here to show the *pattern* for filling in
`docs/architecture/project-structure.md`, `docs/architecture/dependency-policy.md`,
and per-directory `AGENTS.md` files.

Copy the pattern, not the content:

- `rust-agent-instructions.md` / `frontend-agent-instructions.md` show how to
  scope a directory-local `AGENTS.md` once a subproject exists.
- `deny.toml` / `dependency-cruiser.config.cjs` show how to wire a dependency
  policy tool into `docs/architecture/dependency-policy.md` and CI.

Delete this folder, or replace its contents with your own stack's examples,
once your project's real architecture documents exist.
