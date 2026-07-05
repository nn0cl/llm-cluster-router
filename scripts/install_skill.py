#!/usr/bin/env python3
import argparse
import json
import os
import shutil
from pathlib import Path


SKILL_NAME = "ollama-cluster-router"
REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "scripts/ollama_cluster_manager.py",
    "references/ollama_cluster_config.sample.json",
    "references/agent_tool_schema.json",
    "references/agent_system_prompt.md",
]


def default_codex_skills_dir():
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def skill_root_from_script():
    return Path(__file__).resolve().parents[1]


def validate_source(skill_root):
    missing = [path for path in REQUIRED_FILES if not (skill_root / path).is_file()]
    if missing:
        raise RuntimeError(f"missing required skill files: {', '.join(missing)}")

    skill_md = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    if not skill_md.startswith("---\n") or f"name: {SKILL_NAME}" not in skill_md:
        raise RuntimeError("SKILL.md frontmatter is missing the expected skill name")

    for relative_path in [
        "references/ollama_cluster_config.sample.json",
        "references/agent_tool_schema.json",
    ]:
        with (skill_root / relative_path).open(encoding="utf-8") as handle:
            json.load(handle)


def should_copy(path):
    if "__pycache__" in path.parts:
        return False
    if path.suffix == ".pyc":
        return False
    return path.is_file()


def install_skill(source_root, destination_root):
    target_root = destination_root / SKILL_NAME
    copied = []
    for source_path in sorted(source_root.rglob("*")):
        if not should_copy(source_path):
            continue
        relative_path = source_path.relative_to(source_root)
        target_path = target_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied.append(str(relative_path))
    return target_root, copied


def build_parser():
    parser = argparse.ArgumentParser(description="Install ollama-cluster-router skill.")
    parser.add_argument(
        "--destination",
        default=str(default_codex_skills_dir()),
        help="Skills directory to install into. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--source",
        default=str(skill_root_from_script()),
        help="Source skill directory. Defaults to this script's parent skill directory.",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    source_root = Path(args.source).expanduser().resolve()
    destination_root = Path(args.destination).expanduser().resolve()

    validate_source(source_root)
    target_root, copied = install_skill(source_root, destination_root)

    print(
        json.dumps(
            {
                "status": "installed",
                "skill": SKILL_NAME,
                "source": str(source_root),
                "target": str(target_root),
                "files_copied": copied,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
