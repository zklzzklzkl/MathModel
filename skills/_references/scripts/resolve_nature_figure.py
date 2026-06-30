"""Locate and validate an optional nature-figure installation.

The script prints a compact JSON object for use by MathModelAgent skills.
It does not import or execute nature-skills code.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


REQUIRED_RELATIVE_FILES = [
    "skills/nature-figure/SKILL.md",
    "skills/nature-figure/manifest.yaml",
    "skills/nature-figure/static/core/contract.md",
    "skills/nature-figure/static/core/stance.md",
    "skills/nature-figure/static/fragments/backend/python.md",
    "skills/nature-figure/static/fragments/backend/r.md",
]


def candidate_roots(workspace: Path) -> list[Path]:
    roots: list[Path] = []
    env_root = os.environ.get("NATURE_SKILLS_ROOT")
    if env_root:
        roots.append(Path(env_root))

    roots.extend(
        [
            workspace / "nature-skills",
            workspace.parent / "nature-skills",
            Path.home() / "Downloads" / "Compressed" / "nature-skills-main" / "nature-skills-main",
            Path.home() / ".codex" / "skills",
        ]
    )
    return roots


def validate_root(root: Path) -> tuple[bool, list[str]]:
    missing = [rel for rel in REQUIRED_RELATIVE_FILES if not (root / rel).is_file()]
    return not missing, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".", help="Contest workspace or repository root")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    checked: list[str] = []

    for root in candidate_roots(workspace):
        resolved = root.expanduser().resolve()
        checked.append(str(resolved))
        ok, missing = validate_root(resolved)
        if ok:
            print(
                json.dumps(
                    {
                        "available": True,
                        "root": str(resolved),
                        "nature_figure": str(resolved / "skills" / "nature-figure"),
                        "checked": checked,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

    print(
        json.dumps(
            {
                "available": False,
                "root": None,
                "nature_figure": None,
                "checked": checked,
                "required_files": REQUIRED_RELATIVE_FILES,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
