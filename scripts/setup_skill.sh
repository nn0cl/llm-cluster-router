#!/usr/bin/env bash
# Set up the llm-cluster-router skill package for use by an agent CLI on
# this machine. The package itself (SKILL.md, scripts/, references/) stays a
# portable artifact under this repo; this script only wires it up as a
# discoverable skill somewhere else.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILL_NAME="llm-cluster-router"

MODE="symlink"
TARGETS=()
CODEX_DESTINATION=""

usage() {
  cat <<'EOF'
Usage: setup_skill.sh [options]

Wires up the llm-cluster-router skill package (this directory) so an
agent CLI can discover and use it. The package stays a single portable
artifact under skills/llm-cluster-router/; this script only creates
symlinks (or copies) pointing at it.

Targets (repeatable, at least one required):
  --claude-user              ~/.claude/skills/llm-cluster-router
                              (available to every Claude Code project for
                              this user).
  --claude-project <path>    <path>/.claude/skills/llm-cluster-router
                              (available to Claude Code only inside <path>).
  --codex [<dest>]           Delegates to scripts/install_skill.py. <dest>
                              defaults to $CODEX_HOME/skills or
                              ~/.codex/skills, matching install_skill.py's
                              own default. Always copies (Codex reads its
                              skills directory independently of this repo).
  --target <dir>             Install directly under <dir>/llm-cluster-router
                              (advanced / custom tool skills directories).

Options:
  --mode symlink|copy   Install mode for --claude-user/--claude-project/
                        --target (default: symlink). symlink keeps this
                        repo as the single source of truth and needs this
                        repo to stay in place; copy makes a frozen,
                        self-contained snapshot (use when moving to another
                        machine or repo).
  -h, --help            Show this help.

Examples:
  scripts/setup_skill.sh --claude-user
  scripts/setup_skill.sh --claude-project ~/Documents/git/other-repo
  scripts/setup_skill.sh --claude-user --codex
  scripts/setup_skill.sh --target ~/.some-tool/skills --mode copy
EOF
}

validate_source() {
  local missing=()
  for relative_path in \
    "SKILL.md" \
    "agents/openai.yaml" \
    "scripts/ollama_cluster_manager.py" \
    "references/ollama_cluster_config.sample.json" \
    "references/agent_tool_schema.json" \
    "references/agent_system_prompt.md"
  do
    if [ ! -f "${SKILL_ROOT}/${relative_path}" ]; then
      missing+=("${relative_path}")
    fi
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    echo "error: missing required skill files: ${missing[*]}" >&2
    exit 1
  fi
  if ! head -n1 "${SKILL_ROOT}/SKILL.md" | grep -q '^---$'; then
    echo "error: SKILL.md is missing frontmatter" >&2
    exit 1
  fi
  if ! grep -q "^name: ${SKILL_NAME}$" "${SKILL_ROOT}/SKILL.md"; then
    echo "error: SKILL.md frontmatter is missing 'name: ${SKILL_NAME}'" >&2
    exit 1
  fi
}

install_into() {
  local destination_root="$1" # e.g. ~/.claude/skills
  local target_path="${destination_root}/${SKILL_NAME}"

  mkdir -p "${destination_root}"

  if [ -e "${target_path}" ] || [ -L "${target_path}" ]; then
    if [ -L "${target_path}" ] && [ "$(readlink "${target_path}")" = "${SKILL_ROOT}" ]; then
      echo "already set up: ${target_path} -> ${SKILL_ROOT}"
      return 0
    fi
    echo "error: ${target_path} already exists and is not a symlink to ${SKILL_ROOT}" >&2
    echo "       remove it manually first if you want to replace it" >&2
    exit 1
  fi

  case "${MODE}" in
    symlink)
      ln -s "${SKILL_ROOT}" "${target_path}"
      echo "linked: ${target_path} -> ${SKILL_ROOT}"
      ;;
    copy)
      mkdir -p "${target_path}"
      # Copy contents (not the directory itself) so re-running is idempotent
      # and does not nest llm-cluster-router/llm-cluster-router.
      (cd "${SKILL_ROOT}" && tar cf - --exclude='__pycache__' --exclude='*.pyc' .) \
        | (cd "${target_path}" && tar xf -)
      echo "copied: ${target_path} (snapshot of ${SKILL_ROOT})"
      ;;
    *)
      echo "error: unknown --mode '${MODE}' (expected symlink or copy)" >&2
      exit 1
      ;;
  esac
}

run_codex_install() {
  local destination="$1"
  if [ -n "${destination}" ]; then
    python3 "${SKILL_ROOT}/scripts/install_skill.py" --destination "${destination}"
  else
    python3 "${SKILL_ROOT}/scripts/install_skill.py"
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --claude-user)
      TARGETS+=("claude-user")
      shift
      ;;
    --claude-project)
      if [ $# -lt 2 ]; then
        echo "error: --claude-project requires a path argument" >&2
        exit 1
      fi
      TARGETS+=("claude-project:$2")
      shift 2
      ;;
    --codex)
      TARGETS+=("codex")
      if [ $# -ge 2 ] && [[ "$2" != --* ]]; then
        CODEX_DESTINATION="$2"
        shift
      fi
      shift
      ;;
    --target)
      if [ $# -lt 2 ]; then
        echo "error: --target requires a directory argument" >&2
        exit 1
      fi
      TARGETS+=("target:$2")
      shift 2
      ;;
    --mode)
      if [ $# -lt 2 ]; then
        echo "error: --mode requires 'symlink' or 'copy'" >&2
        exit 1
      fi
      MODE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument '$1'" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ "${#TARGETS[@]}" -eq 0 ]; then
  echo "error: no target given" >&2
  usage >&2
  exit 1
fi

validate_source

for target in "${TARGETS[@]}"; do
  case "${target}" in
    claude-user)
      install_into "${HOME}/.claude/skills"
      ;;
    claude-project:*)
      project_path="${target#claude-project:}"
      project_path="$(cd "${project_path}" && pwd)"
      install_into "${project_path}/.claude/skills"
      ;;
    codex)
      run_codex_install "${CODEX_DESTINATION}"
      ;;
    target:*)
      install_into "${target#target:}"
      ;;
  esac
done
