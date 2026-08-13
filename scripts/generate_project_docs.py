#!/usr/bin/env python3
"""Generate the repository snapshot shared by README and the Obsidian vault.

This script intentionally uses only the Python standard library so it works in
GitHub Actions and on a fresh local checkout without an extra installation step.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SNAPSHOT = ROOT / "vault" / "Project Snapshot.md"
START = "<!-- GENERATED:START -->"
END = "<!-- GENERATED:END -->"
IGNORED_DIRECTORIES = {
    ".git",
    ".next",
    ".obsidian",
    "__pycache__",
    "chroma_data",
    "node_modules",
    "venv",
    ".venv",
}


def tracked_files() -> list[Path]:
    """Use Git's tracked files when possible; fall back to a safe file walk."""
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode == 0:
        return [ROOT / item for item in result.stdout.splitlines() if item]

    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in IGNORED_DIRECTORIES for part in path.parts)
    ]


def project_name() -> str:
    package_file = ROOT / "frontend" / "package.json"
    if package_file.exists():
        try:
            package = json.loads(package_file.read_text(encoding="utf-8"))
            if package.get("name") and package["name"] != "frontend":
                return str(package["name"])
        except json.JSONDecodeError:
            pass
    return ROOT.name.replace("_", " ").replace("-", " ").title()


def extension_summary(files: list[Path]) -> str:
    counts = Counter(path.suffix.lower() or "(no extension)" for path in files)
    entries = [f"`{extension}` ({count})" for extension, count in counts.most_common(8)]
    return ", ".join(entries) if entries else "No files found"


def top_level_summary(files: list[Path]) -> str:
    counts = Counter(
        path.relative_to(ROOT).parts[0]
        for path in files
        if len(path.relative_to(ROOT).parts) > 1
    )
    entries = [f"`{name}/` ({count})" for name, count in counts.most_common(10)]
    return ", ".join(entries) if entries else "No top-level directories found"


def git_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "not committed yet"


def snapshot_body() -> str:
    files = tracked_files()
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return f"""## Current repository snapshot

_Generated automatically on {timestamp}. Revision: `{git_revision()}`._

| Metric | Current value |
| --- | --- |
| Project | {project_name()} |
| Version-controlled files | {len(files)} |
| Top-level areas | {top_level_summary(files)} |
| Common file types | {extension_summary(files)} |

### Documentation automation

This snapshot is regenerated locally with `python scripts/generate_project_docs.py` and after every GitHub push by `.github/workflows/update-documentation.yml`.
"""


def update_readme(body: str) -> None:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise RuntimeError("README.md is missing the generated-content markers.")
    before, remainder = text.split(START, 1)
    _, after = remainder.split(END, 1)
    README.write_text(f"{before}{START}\n{body.rstrip()}\n{END}{after}", encoding="utf-8")


def update_snapshot(body: str) -> None:
    SNAPSHOT.write_text(
        "---\ntags:\n  - project\n  - generated\n---\n\n# Project Snapshot\n\n"
        f"{body}\n\n> [!note]\n> This file is generated. Add durable context to the other vault notes instead.\n",
        encoding="utf-8",
    )


def main() -> None:
    body = snapshot_body()
    update_readme(body)
    update_snapshot(body)


if __name__ == "__main__":
    main()
