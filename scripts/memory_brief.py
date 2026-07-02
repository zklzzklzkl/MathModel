#!/usr/bin/env python
"""Generate a small stage briefing from local MathModel experience memory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY_ROOT = REPO_ROOT / "memory"
SUMMARY_FILES = [
    "summary.md",
    "failed_approaches.md",
    "model_lessons.md",
    "reviewer_lessons.md",
]


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a concise experience-memory briefing.")
    parser.add_argument("--memory-root", type=Path, default=DEFAULT_MEMORY_ROOT)
    parser.add_argument("--query", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--event-type", action="append", default=[])
    parser.add_argument("--max-events", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def tokenize(text: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9_+-]+|[\u4e00-\u9fff]{2,}", text.lower())
    deduped: list[str] = []
    for term in terms:
        if term not in deduped:
            deduped.append(term)
    return deduped


def load_events(memory_root: Path) -> list[dict[str, Any]]:
    event_file = memory_root / "events.jsonl"
    if not event_file.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in event_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def event_text(event: dict[str, Any]) -> str:
    parts = [
        str(event.get("event_type", "")),
        str(event.get("phase", "")),
        str(event.get("severity", "")),
        str(event.get("summary", "")),
        str(event.get("details", "")),
        str(event.get("lesson", "")),
        " ".join(str(tag) for tag in event.get("tags", [])),
        " ".join(str(path) for path in event.get("source_files", [])),
    ]
    return " ".join(parts).lower()


def score_text(text: str, terms: list[str]) -> int:
    if not terms:
        return 1
    lower = text.lower()
    return sum(1 for term in terms if term in lower)


def matching_summary_lines(memory_root: Path, terms: list[str]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for name in SUMMARY_FILES:
        path = memory_root / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if score_text(stripped, terms) > 0:
                matches.append({"file": name, "line": stripped})
    return matches


def build_brief(args: argparse.Namespace) -> dict[str, Any]:
    terms = tokenize(args.query)
    required_tags = {tag.lower() for tag in args.tag}
    required_event_types = {event_type.lower() for event_type in args.event_type}
    scored_events: list[tuple[int, dict[str, Any]]] = []
    for event in load_events(args.memory_root):
        tags = {str(tag).lower() for tag in event.get("tags", [])}
        if required_tags and not required_tags.intersection(tags):
            continue
        if required_event_types and str(event.get("event_type", "")).lower() not in required_event_types:
            continue
        score = score_text(event_text(event), terms)
        if score > 0:
            scored_events.append((score, event))
    scored_events.sort(key=lambda item: (item[0], str(item[1].get("timestamp", ""))), reverse=True)
    return {
        "query": args.query,
        "terms": terms,
        "summary_matches": matching_summary_lines(args.memory_root, terms),
        "events": [event for _, event in scored_events[: args.max_events]],
    }


def markdown_brief(brief: dict[str, Any]) -> str:
    lines = ["# Experience Memory Brief", "", f"Query: `{brief['query']}`", ""]
    if brief["summary_matches"]:
        lines.append("## Distilled Lessons")
        for match in brief["summary_matches"]:
            lines.append(f"- `{match['file']}`: {match['line']}")
        lines.append("")
    if brief["events"]:
        lines.append("## Matching Events")
        for event in brief["events"]:
            tags = ", ".join(event.get("tags", [])) or "none"
            source_files = ", ".join(event.get("source_files", [])) or "none"
            lines.extend(
                [
                    f"- [{event.get('severity', 'INFO')}] {event.get('event_type', '')}: {event.get('summary', '')}",
                    f"  phase: `{event.get('phase', '')}`; tags: {tags}; source: {source_files}",
                ]
            )
        lines.append("")
    if not brief["summary_matches"] and not brief["events"]:
        lines.append("No relevant memory found. Continue from current artifacts and record new lessons if needed.")
    return "\n".join(lines).rstrip()


def main() -> None:
    configure_stdout()
    args = parse_args()
    brief = build_brief(args)
    if args.json:
        print(json.dumps(brief, ensure_ascii=False, indent=2))
    else:
        print(markdown_brief(brief))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
