"""Check MathModelAgent persistent context contract files.

This lightweight verifier is intended for the final verification skill. It only
checks file presence and obvious JSON validity; domain correctness still needs
the model's review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = [
    "PROBLEM_BRIEF.md",
    "DATA_AUDIT.md",
    "WORKFLOW_STATE.md",
    "reports/TRIAGE_REPORT.md",
    "reports/ANALYSIS_MODELING_REPORT.md",
    "reports/MODELING_DECISIONS.md",
    "reports/ANALYSIS_GATE.md",
    "reports/EXPERIMENT_LOG.md",
    "results/RESULTS_MANIFEST.json",
    "reports/RESULTS_REPORT.md",
    "reports/FIGURE_PLAN.md",
    "reports/CLAIM_TRACE.md",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Project root to check")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    missing: list[str] = []
    empty: list[str] = []

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.exists():
            missing.append(rel)
            continue
        if path.is_file() and path.stat().st_size == 0:
            empty.append(rel)

    manifest = root / "results" / "RESULTS_MANIFEST.json"
    manifest_error = ""
    if manifest.exists() and manifest.stat().st_size > 0:
        try:
            json.loads(manifest.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            manifest_error = str(exc)

    if missing:
        print("MISSING:")
        for rel in missing:
            print(f"- {rel}")
    if empty:
        print("EMPTY:")
        for rel in empty:
            print(f"- {rel}")
    if manifest_error:
        print(f"INVALID_JSON: results/RESULTS_MANIFEST.json: {manifest_error}")

    if missing or empty or manifest_error:
        return 1

    print("PASS: context contract files exist and manifest JSON is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
