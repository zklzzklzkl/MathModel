"""Locate and validate an optional nature-figure installation.

The script prints a compact JSON object for use by MathModelAgent skills.
It does not import or execute nature-skills code.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "manifest.yaml",
    "static/core/contract.md",
    "static/core/stance.md",
    "static/fragments/backend/python.md",
    "static/fragments/backend/r.md",
]

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
            Path.home() / ".codex" / "skills" / "nature-figure",
        ]
    )
    return roots


def validate_root(root: Path) -> tuple[bool, str | None, Path | None, list[str]]:
    """Validate supported nature-figure layouts.

    Supported roots:
    - nature-skills repository root containing skills/nature-figure/
    - Codex skills root containing nature-figure/
    - direct nature-figure skill directory
    """
    layouts = [
        ("nature-skills-repo", root / "skills" / "nature-figure", REQUIRED_SKILL_FILES),
        ("codex-skills-root", root / "nature-figure", REQUIRED_SKILL_FILES),
        ("direct-skill", root, REQUIRED_SKILL_FILES),
    ]
    best_layout: str | None = None
    best_skill_dir: Path | None = None
    best_missing: list[str] | None = None

    for layout, skill_dir, required in layouts:
        missing = [rel for rel in required if not (skill_dir / rel).is_file()]
        if not missing:
            return True, layout, skill_dir, []
        if best_missing is None or len(missing) < len(best_missing):
            best_layout = layout
            best_skill_dir = skill_dir
            best_missing = missing

    return False, best_layout, best_skill_dir, best_missing or REQUIRED_SKILL_FILES[:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".", help="Contest workspace or repository root")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    checked: list[str] = []

    for root in candidate_roots(workspace):
        resolved = root.expanduser().resolve()
        checked.append(str(resolved))
        ok, layout, skill_dir, missing = validate_root(resolved)
        if ok:
            print(
                json.dumps(
                    {
                        "available": True,
                        "root": str(resolved),
                        "layout": layout,
                        "nature_figure": str(skill_dir),
                        "required_files_missing": [],
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
                "layout": None,
                "nature_figure": None,
                "checked": checked,
                "required_files": REQUIRED_SKILL_FILES,
                "required_files_missing": REQUIRED_SKILL_FILES,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
