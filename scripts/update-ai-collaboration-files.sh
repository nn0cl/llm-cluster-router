#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/update-ai-collaboration-files.sh --target PATH [options]

Pulls later AI-human collaboration template updates into a repository that
already adopted the template (via copy-ai-collaboration-files.sh).

Unlike the initial copy, this performs a 3-way merge per file:
  base   = the template file as of the target's recorded sync commit
  ours   = the target's current file (keeps target customizations)
  theirs = the template's current file

Files the target intentionally deleted since the last sync are left deleted
unless the template also changed them, in which case they are flagged for a
manual decision instead of being silently restored. Files listed in the
target's .collaboration-template-ignore are never touched.

This script never commits to the target's trunk branch. It creates a
dedicated branch, commits the merged result there, and (when possible) opens
a pull request, per docs/collaboration/branch-commit-pr-discipline.md.

Options:
  --target PATH        Target repository directory. Required.
  --source PATH         Local checkout of the template repository to pull
                        updates from. Defaults to this script's own repo.
  --branch-prefix TEXT  Branch name prefix. Default: process/update-collab-template
  --no-pr               Create the branch and commit locally; skip pushing
                        and opening a PR even if `gh` is available.
  --dry-run             Report planned actions without changing anything.
  -h, --help            Show this help.
USAGE
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

target=""
source_repo="$repo_root"
branch_prefix="process/update-collab-template"
no_pr=false
dry_run=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      target="${2:-}"
      shift 2
      ;;
    --source)
      source_repo="${2:-}"
      shift 2
      ;;
    --branch-prefix)
      branch_prefix="${2:-}"
      shift 2
      ;;
    --no-pr)
      no_pr=true
      shift
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$target" ]; then
  echo "--target is required." >&2
  usage >&2
  exit 2
fi

if [ ! -d "$target" ]; then
  echo "Target directory does not exist: $target" >&2
  exit 1
fi

target="$(cd "$target" && pwd)"
source_repo="$(cd "$source_repo" && pwd)"

if ! git -C "$target" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Target is not a git repository: $target" >&2
  exit 1
fi

if ! git -C "$source_repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Source is not a git repository: $source_repo" >&2
  exit 1
fi

if [ "$dry_run" != true ] && [ -n "$(git -C "$target" status --porcelain)" ]; then
  echo "Target has uncommitted changes; commit, stash, or clean before syncing." >&2
  exit 1
fi

marker="$target/.collaboration-template-version"
if [ ! -f "$marker" ]; then
  echo "Missing $marker." >&2
  echo "Run scripts/copy-ai-collaboration-files.sh once to adopt the template before updating." >&2
  exit 1
fi

old_ref="$(sed -n 's/^ref:[[:space:]]*//p' "$marker" | head -n1)"
if [ -z "$old_ref" ]; then
  echo "Could not read 'ref:' from $marker." >&2
  exit 1
fi

if ! git -C "$source_repo" cat-file -e "${old_ref}^{commit}" 2>/dev/null; then
  echo "Recorded ref $old_ref is not reachable in $source_repo." >&2
  echo "Fetch full history in the source checkout and retry." >&2
  exit 1
fi

new_ref="$(git -C "$source_repo" rev-parse HEAD)"

if [ "$old_ref" = "$new_ref" ]; then
  echo "Target is already synced to $new_ref. Nothing to do."
  exit 0
fi

ignore_file="$target/.collaboration-template-ignore"
ignore_patterns=()
if [ -f "$ignore_file" ]; then
  while IFS= read -r line; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
    [ -z "$line" ] && continue
    ignore_patterns+=("$line")
  done < "$ignore_file"
fi

is_ignored() {
  local rel="$1"
  local pattern
  for pattern in "${ignore_patterns[@]+"${ignore_patterns[@]}"}"; do
    # shellcheck disable=SC2254
    case "$rel" in
      $pattern) return 0 ;;
    esac
  done
  return 1
}

# shellcheck source=lib/collaboration-template-paths.sh
source "$script_dir/lib/collaboration-template-paths.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

added=()
updated=()
merged=()
conflicts=()
needs_decision=()
collisions=()
ignored=()
unchanged_count=0

# Classifies a relative path as a numbered ADR or local-issue file. On match,
# sets numbered_class_dir/_num/_kind and returns 0; otherwise returns 1.
# Two different files "at the same number" (e.g. an unrelated project ADR
# 0007 and this template's own ADR 0007) diff as unrelated adds under plain
# path comparison, so this class needs its own collision check.
classify_numbered_file() {
  local rel="$1"
  numbered_class_dir=""
  numbered_class_num=""
  numbered_class_kind=""
  case "$rel" in
    docs/architecture/adr/[0-9][0-9][0-9][0-9]-*.md)
      numbered_class_dir="docs/architecture/adr"
      numbered_class_num="$(basename "$rel" | cut -c1-4)"
      numbered_class_kind="adr"
      return 0
      ;;
    docs/issues/LISS-[0-9][0-9][0-9][0-9]-*.md)
      numbered_class_dir="docs/issues"
      numbered_class_num="$(basename "$rel" | sed -n 's/^LISS-\([0-9][0-9][0-9][0-9]\)-.*/\1/p')"
      numbered_class_kind="liss"
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# Prints the basename of an existing target file with the same number but a
# different slug, if any, and returns 0. Returns 1 if none is found.
find_number_collision() {
  local dir="$1" num="$2" kind="$3" own_basename="$4"
  local f bn
  [ -d "$target/$dir" ] || return 1
  for f in "$target/$dir"/*; do
    [ -f "$f" ] || continue
    bn="$(basename "$f")"
    [ "$bn" = "$own_basename" ] && continue
    case "$kind" in
      adr)
        case "$bn" in
          "$num"-*.md) echo "$bn"; return 0 ;;
        esac
        ;;
      liss)
        case "$bn" in
          LISS-"$num"-*.md) echo "$bn"; return 0 ;;
        esac
        ;;
    esac
  done
  return 1
}

# Prints the lowest unused number (zero-padded to 4 digits) in the target's
# own sequence for the given numbered-file class.
next_free_number() {
  local dir="$1" kind="$2"
  local max=0 f bn n
  if [ -d "$target/$dir" ]; then
    for f in "$target/$dir"/*; do
      [ -f "$f" ] || continue
      bn="$(basename "$f")"
      case "$kind" in
        adr) n="$(echo "$bn" | sed -n 's/^\([0-9][0-9][0-9][0-9]\)-.*/\1/p')" ;;
        liss) n="$(echo "$bn" | sed -n 's/^LISS-\([0-9][0-9][0-9][0-9]\)-.*/\1/p')" ;;
      esac
      [ -z "$n" ] && continue
      n=$((10#$n))
      [ "$n" -gt "$max" ] && max=$n
    done
  fi
  printf '%04d' $((max + 1))
}

list_files() {
  local base="$1"
  local rel="$2"
  local full="$base/$rel"
  [ -e "$full" ] || return 0
  if [ -d "$full" ]; then
    while IFS= read -r file_rel; do
      if is_collaboration_template_excluded "$file_rel"; then
        continue
      fi
      echo "$file_rel"
    done < <(cd "$base" && find "$rel" -type f)
  else
    if ! is_collaboration_template_excluded "$rel"; then
      echo "$rel"
    fi
  fi
}

process_file() {
  local rel="$1"

  if is_ignored "$rel"; then
    ignored+=("$rel")
    return
  fi

  local theirs_file="$source_repo/$rel"
  local ours_file="$target/$rel"
  local base_content=""
  local base_missing=false

  if ! base_content="$(git -C "$source_repo" show "$old_ref:$rel" 2>/dev/null)"; then
    base_missing=true
  fi

  if [ ! -e "$theirs_file" ]; then
    return
  fi

  if [ ! -e "$ours_file" ]; then
    if [ "$base_missing" = true ]; then
      added+=("$rel")
      if classify_numbered_file "$rel"; then
        local own_bn collision_bn
        own_bn="$(basename "$rel")"
        if collision_bn="$(find_number_collision "$numbered_class_dir" "$numbered_class_num" "$numbered_class_kind" "$own_bn")"; then
          local suggestion
          suggestion="$(next_free_number "$numbered_class_dir" "$numbered_class_kind")"
          collisions+=("$rel collides with existing $numbered_class_dir/$collision_bn (same number, different document) -- renumber one of them; next free number in target's sequence: $suggestion")
        fi
      fi
      if [ "$dry_run" != true ]; then
        mkdir -p "$(dirname "$ours_file")"
        cp "$theirs_file" "$ours_file"
      fi
    else
      if [ "$base_content" = "$(cat "$theirs_file")" ]; then
        : # target deleted it on purpose, upstream never changed it since: respect deletion.
      else
        needs_decision+=("$rel (deleted locally, changed upstream since last sync)")
      fi
    fi
    return
  fi

  local ours_content theirs_content
  ours_content="$(cat "$ours_file")"
  theirs_content="$(cat "$theirs_file")"

  if [ "$base_missing" = false ] && [ "$ours_content" = "$base_content" ] && [ "$theirs_content" = "$base_content" ]; then
    unchanged_count=$((unchanged_count + 1))
    return
  fi

  if [ "$ours_content" = "$theirs_content" ]; then
    unchanged_count=$((unchanged_count + 1))
    return
  fi

  if [ "$base_missing" = false ] && [ "$ours_content" = "$base_content" ]; then
    updated+=("$rel")
    if [ "$dry_run" != true ]; then
      cp "$theirs_file" "$ours_file"
    fi
    return
  fi

  if [ "$base_missing" = false ] && [ "$theirs_content" = "$base_content" ]; then
    unchanged_count=$((unchanged_count + 1))
    return
  fi

  local base_tmp="$workdir/base"
  local ours_tmp="$workdir/ours"
  local theirs_tmp="$workdir/theirs"
  if [ "$base_missing" = true ]; then
    : > "$base_tmp"
  else
    git -C "$source_repo" show "$old_ref:$rel" > "$base_tmp"
  fi
  cp "$ours_file" "$ours_tmp"
  cp "$theirs_file" "$theirs_tmp"

  local merge_status=0
  git merge-file -p -L "ours (target)" -L "base (last sync)" -L "theirs (template)" \
    "$ours_tmp" "$base_tmp" "$theirs_tmp" > "$workdir/merged" 2>/dev/null || merge_status=$?

  if [ "$merge_status" -eq 0 ]; then
    merged+=("$rel")
  else
    conflicts+=("$rel")
  fi

  if [ "$dry_run" != true ]; then
    mkdir -p "$(dirname "$ours_file")"
    cp "$workdir/merged" "$ours_file"
  fi
}

for rel in "${collaboration_template_paths[@]}"; do
  while IFS= read -r file_rel; do
    [ -z "$file_rel" ] && continue
    process_file "$file_rel"
  done < <(list_files "$source_repo" "$rel")
done

print_list() {
  local title="$1"
  shift
  [ "$#" -eq 0 ] && return
  echo "$title"
  local item
  for item in "$@"; do
    echo "  - $item"
  done
}

echo "Source: $source_repo ($old_ref -> $new_ref)"
echo "Target: $target"
echo
print_list "Added (new upstream files):" "${added[@]+"${added[@]}"}"
print_list "Updated (target had not customized):" "${updated[@]+"${updated[@]}"}"
print_list "Merged cleanly (target customization preserved):" "${merged[@]+"${merged[@]}"}"
print_list "CONFLICTS (manual resolution required, markers left in file):" "${conflicts[@]+"${conflicts[@]}"}"
print_list "NUMBER COLLISIONS (manual renumbering required):" "${collisions[@]+"${collisions[@]}"}"
print_list "NEEDS DECISION (deleted locally, changed upstream):" "${needs_decision[@]+"${needs_decision[@]}"}"
if [ "${#needs_decision[@]}" -gt 0 ]; then
  echo "  Hint: before restoring any item above, check whether the target already"
  echo "  has the same content under a different filename (e.g. a renumbered ADR or"
  echo "  local issue) elsewhere in the repository -- it may be a rename, not a"
  echo "  real deletion."
fi
print_list "Ignored (per .collaboration-template-ignore):" "${ignored[@]+"${ignored[@]}"}"
echo "Unchanged: $unchanged_count file(s)"

total_changes=$(( ${#added[@]} + ${#updated[@]} + ${#merged[@]} + ${#conflicts[@]} ))

if [ "$dry_run" = true ]; then
  echo
  echo "Dry run: no branch, commit, or PR created."
  exit 0
fi

if [ "$total_changes" -eq 0 ]; then
  echo
  echo "No file changes to apply; only advancing the sync marker."
fi

branch_name="${branch_prefix}-$(date +%Y%m%d)-${new_ref:0:8}"
if git -C "$target" show-ref --verify --quiet "refs/heads/$branch_name"; then
  echo "Branch $branch_name already exists in target; delete it or rerun with a different --branch-prefix." >&2
  exit 1
fi

git -C "$target" switch -c "$branch_name"

source_origin="$(git -C "$source_repo" remote get-url origin 2>/dev/null || echo "$source_repo")"
cat > "$marker" <<MARKER
# Records which commit of the AI-human collaboration template this project
# last synced against. Read by scripts/update-ai-collaboration-files.sh.
# Do not edit by hand except to correct the source.
source: $source_origin
ref: $new_ref
MARKER

git -C "$target" add -A
git -C "$target" commit -m "chore: sync collaboration template to ${new_ref:0:8}

Added: ${#added[@]}, updated: ${#updated[@]}, merged: ${#merged[@]}, conflicts: ${#conflicts[@]}, number collisions: ${#collisions[@]}, needs decision: ${#needs_decision[@]}.
See PR description or this commit's file list for details." >/dev/null

echo
echo "Committed sync on branch $branch_name."

if [ "${#conflicts[@]}" -gt 0 ] || [ "${#collisions[@]}" -gt 0 ] || [ "${#needs_decision[@]}" -gt 0 ]; then
  echo "Manual resolution needed before merging (see CONFLICTS / NUMBER COLLISIONS / NEEDS DECISION above)."
fi

if [ "$no_pr" = true ]; then
  echo "Skipping PR creation (--no-pr). Push and open a PR manually per docs/collaboration/branch-commit-pr-discipline.md."
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Push and open a PR manually:"
  echo "  git -C \"$target\" push -u origin $branch_name"
  exit 0
fi

if ! git -C "$target" remote get-url origin >/dev/null 2>&1; then
  echo "Target has no 'origin' remote. Push and open a PR manually once one is configured."
  exit 0
fi

git -C "$target" push -u origin "$branch_name"

pr_body="$(cat <<BODY
Sync from collaboration template ${old_ref:0:8} -> ${new_ref:0:8}.

- Added: ${#added[@]}
- Updated: ${#updated[@]}
- Merged (target customization preserved): ${#merged[@]}
- Conflicts needing manual resolution: ${#conflicts[@]}
- Number collisions needing manual renumbering: ${#collisions[@]}
- Needs decision (deleted locally, changed upstream): ${#needs_decision[@]}
- Ignored: ${#ignored[@]}

This branch follows docs/collaboration/branch-commit-pr-discipline.md: it
must pass CI before merge and should not be merged with unresolved conflict
markers, unresolved NUMBER COLLISIONS, or unresolved NEEDS DECISION items.
BODY
)"

(cd "$target" && gh pr create --title "chore: sync collaboration template to ${new_ref:0:8}" --body "$pr_body")
