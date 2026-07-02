#!/usr/bin/env python
"""Distill MathModel workspace artifacts into experience-memory summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY_ROOT = REPO_ROOT / "memory"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_id(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Distill project artifacts into memory summaries.")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--memory-root", type=Path, default=DEFAULT_MEMORY_ROOT)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_markdown_table(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if cells and cells[0].lower() in {"id", "action id"}:
            continue
        rows.append(cells)
    return rows


def make_event(
    event_type: str,
    summary: str,
    workspace: Path,
    phase: str,
    severity: str,
    source_files: list[str],
    tags: list[str] | None = None,
    lesson: str = "",
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "timestamp": utc_now(),
        "event_type": event_type,
        "workspace": str(workspace.resolve()),
        "phase": phase,
        "severity": severity,
        "summary": summary.strip(),
        "details": "",
        "tags": tags or [],
        "source_files": source_files,
        "artifact": "",
        "lesson": lesson.strip(),
        "status": "distilled",
    }
    event["id"] = stable_id(event)
    return event


def append_events(memory_root: Path, events: list[dict[str, Any]]) -> int:
    if not events:
        return 0
    memory_root.mkdir(parents=True, exist_ok=True)
    event_file = memory_root / "events.jsonl"
    with event_file.open("a", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return len(events)


def append_unique(path: Path, heading: str, lines: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_text(path)
    if not existing.strip():
        existing = f"# {heading}\n\n"
    added = 0
    content = existing.rstrip() + "\n"
    for line in lines:
        normalized = line.strip()
        if not normalized:
            continue
        if normalized not in existing:
            content += f"- {normalized}\n"
            added += 1
    if added:
        path.write_text(content + "\n", encoding="utf-8")
    elif not path.exists():
        path.write_text(existing, encoding="utf-8")
    return added


def distill_revision_actions(workspace: Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = workspace / "reports" / "REVISION_ACTIONS.md"
    text = read_text(path)
    events: list[dict[str, Any]] = []
    lessons: list[str] = []
    for cells in parse_markdown_table(text):
        if len(cells) < 7:
            continue
        action_id, issue, severity, source_panel, required_fix, scope, status = cells[:7]
        if not issue:
            continue
        event_type = "revision_resolved" if status.lower() == "resolved" else "review_action_created"
        summary = f"{issue} -> {required_fix}".strip()
        lessons.append(f"{severity} {source_panel}: {issue}; fix: {required_fix}; status: {status}.")
        events.append(
            make_event(
                event_type=event_type,
                summary=summary,
                workspace=workspace,
                phase="mm-contest-review",
                severity=severity.upper() if severity else "INFO",
                source_files=["reports/REVISION_ACTIONS.md"],
                tags=[scope, source_panel, action_id],
                lesson=summary,
            )
        )
    return events, lessons


def distill_experiment_failures(workspace: Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = workspace / "reports" / "EXPERIMENT_LOG.md"
    text = read_text(path)
    events: list[dict[str, Any]] = []
    lessons: list[str] = []
    pattern = re.compile(r"^\s*[-*]\s*(model_route_rejected|experiment_failed|validation_failed)\s*:\s*(.+)$", re.I)
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        event_type = match.group(1).lower()
        summary = match.group(2).strip()
        severity = "HIGH" if event_type in {"experiment_failed", "validation_failed"} else "MEDIUM"
        lessons.append(f"{event_type}: {summary}")
        events.append(
            make_event(
                event_type=event_type,
                summary=summary,
                workspace=workspace,
                phase="mm-data-experiment",
                severity=severity,
                source_files=["reports/EXPERIMENT_LOG.md"],
                tags=["experiment", "failure"],
                lesson=summary,
            )
        )
    return events, lessons


def write_retrospective(workspace: Path, review_lessons: list[str], failed_lessons: list[str]) -> Path:
    reports = workspace / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / "PROJECT_RETROSPECTIVE.md"
    lines = [
        "# Project Retrospective",
        "",
        "Conclusion: distilled from current project artifacts.",
        "",
        "## Effective Routes",
        "",
        "- Record manually after final human review when a route proves useful.",
        "",
        "## Failed Routes",
        "",
    ]
    lines.extend(f"- {lesson}" for lesson in failed_lessons)
    if not failed_lessons:
        lines.append("- No failed route was found in current artifacts.")
    lines.extend(["", "## Review Lessons", ""])
    lines.extend(f"- {lesson}" for lesson in review_lessons)
    if not review_lessons:
        lines.append("- No review lesson was found in current artifacts.")
    lines.extend(
        [
            "",
            "## Human Advice",
            "",
            "- Add user feedback here before the next distill pass.",
            "",
            "## Memory Events",
            "",
            "- Raw events are stored in local `memory/events.jsonl`; distilled summaries are safe to commit after review.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def distill(workspace: Path, memory_root: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    memory_root.mkdir(parents=True, exist_ok=True)
    revision_events, review_lessons = distill_revision_actions(workspace)
    failure_events, failed_lessons = distill_experiment_failures(workspace)
    events = revision_events + failure_events
    events_written = append_events(memory_root, events)

    summary_lines = [
        f"{workspace.name}: {len(review_lessons)} review lessons, {len(failed_lessons)} failed approaches distilled."
    ]
    append_unique(memory_root / "summary.md", "Experience Memory Summary", summary_lines)
    append_unique(memory_root / "reviewer_lessons.md", "Reviewer Lessons", review_lessons)
    append_unique(memory_root / "failed_approaches.md", "Failed Approaches", failed_lessons)
    append_unique(memory_root / "model_lessons.md", "Model Lessons", failed_lessons)
    retrospective = write_retrospective(workspace, review_lessons, failed_lessons)

    return {
        "workspace": str(workspace),
        "memory_root": str(memory_root.resolve()),
        "events_written": events_written,
        "review_lessons": len(review_lessons),
        "failed_lessons": len(failed_lessons),
        "retrospective": str(retrospective),
    }


def main() -> None:
    configure_stdout()
    args = parse_args()
    result = distill(args.workspace, args.memory_root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Distilled {result['events_written']} events into {result['memory_root']}")
        print(f"Retrospective: {result['retrospective']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
