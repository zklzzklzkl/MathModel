#!/usr/bin/env python
"""Append structured MathModel experience-memory events.

Raw events are local runtime data by default. Distilled summaries can be
committed, but events.jsonl should stay ignored because it may contain project
paths, failure details, or human advice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY_ROOT = REPO_ROOT / "memory"

EVENT_TYPES = {
    "model_route_rejected",
    "experiment_failed",
    "template_adapted",
    "validation_failed",
    "figure_evidence_failed",
    "review_action_created",
    "revision_resolved",
    "human_advice",
    "final_retrospective",
}
SEVERITIES = {"BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"}


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_id(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append an experience-memory event.")
    parser.add_argument("--memory-root", type=Path, default=DEFAULT_MEMORY_ROOT)
    parser.add_argument("--event-type", required=True, choices=sorted(EVENT_TYPES))
    parser.add_argument("--workspace", default="")
    parser.add_argument("--phase", default="")
    parser.add_argument("--severity", default="INFO", choices=sorted(SEVERITIES))
    parser.add_argument("--summary", required=True)
    parser.add_argument("--details", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--source-file", action="append", default=[])
    parser.add_argument("--artifact", default="")
    parser.add_argument("--lesson", default="")
    parser.add_argument("--status", default="open")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def build_event(args: argparse.Namespace) -> dict[str, Any]:
    timestamp = utc_now()
    event: dict[str, Any] = {
        "timestamp": timestamp,
        "event_type": args.event_type,
        "workspace": args.workspace,
        "phase": args.phase,
        "severity": args.severity,
        "summary": args.summary.strip(),
        "details": args.details.strip(),
        "tags": [tag.strip() for tag in args.tag if tag.strip()],
        "source_files": [path.strip() for path in args.source_file if path.strip()],
        "artifact": args.artifact.strip(),
        "lesson": args.lesson.strip(),
        "status": args.status.strip() or "open",
    }
    event["id"] = stable_id(event)
    return event


def append_event(memory_root: Path, event: dict[str, Any]) -> Path:
    memory_root.mkdir(parents=True, exist_ok=True)
    event_file = memory_root / "events.jsonl"
    with event_file.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event_file


def main() -> None:
    configure_stdout()
    args = parse_args()
    event = build_event(args)
    event_file = append_event(args.memory_root, event)
    if args.json:
        print(json.dumps(event, ensure_ascii=False, indent=2))
    else:
        print(f"Logged {event['event_type']} event to {event_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
