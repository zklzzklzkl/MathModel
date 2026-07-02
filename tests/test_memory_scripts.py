from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_memory_log_appends_structured_event(tmp_path: Path) -> None:
    memory_root = tmp_path / "memory"
    event_file = memory_root / "events.jsonl"

    output = run_cmd(
        "scripts/memory_log.py",
        "--memory-root",
        str(memory_root),
        "--event-type",
        "experiment_failed",
        "--phase",
        "mm-data-experiment",
        "--severity",
        "HIGH",
        "--summary",
        "GA failed to satisfy capacity constraints",
        "--tag",
        "optimization",
        "--tag",
        "ga",
        "--source-file",
        "reports/EXPERIMENT_LOG.md",
        "--json",
    )

    payload = json.loads(output.stdout)
    assert payload["event_type"] == "experiment_failed"
    assert event_file.exists()
    events = [json.loads(line) for line in event_file.read_text(encoding="utf-8").splitlines()]
    assert len(events) == 1
    assert events[0]["summary"] == "GA failed to satisfy capacity constraints"
    assert events[0]["tags"] == ["optimization", "ga"]
    assert events[0]["source_files"] == ["reports/EXPERIMENT_LOG.md"]


def test_memory_brief_filters_events_and_summaries(tmp_path: Path) -> None:
    memory_root = tmp_path / "memory"
    memory_root.mkdir()
    (memory_root / "events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_type": "experiment_failed",
                        "timestamp": "2026-07-02T00:00:00+00:00",
                        "phase": "mm-data-experiment",
                        "severity": "HIGH",
                        "summary": "GA failed on capacity constraints",
                        "tags": ["optimization", "ga"],
                        "source_files": ["reports/EXPERIMENT_LOG.md"],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "event_type": "human_advice",
                        "timestamp": "2026-07-02T01:00:00+00:00",
                        "phase": "mm-contest-review",
                        "severity": "LOW",
                        "summary": "Improve abstract wording",
                        "tags": ["paper"],
                        "source_files": ["reports/PAPER_SCORECARD.md"],
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )
    (memory_root / "model_lessons.md").write_text(
        "# Model Lessons\n\n- optimization: always check capacity constraints after solving.\n",
        encoding="utf-8",
    )

    output = run_cmd(
        "scripts/memory_brief.py",
        "--memory-root",
        str(memory_root),
        "--query",
        "optimization capacity",
        "--max-events",
        "3",
    )

    assert "GA failed on capacity constraints" in output.stdout
    assert "always check capacity constraints" in output.stdout
    assert "Improve abstract wording" not in output.stdout


def test_memory_distill_extracts_revision_and_failure_lessons(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    reports = workspace / "reports"
    reports.mkdir(parents=True)
    (reports / "REVISION_ACTIONS.md").write_text(
        """# Revision Actions

| ID | Issue | Severity | Source Panel | Required Fix | Scope | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | Core prediction figure lacks test-set metrics | HIGH | visualization-reviewer | Add MAE/RMSE and redraw test comparison | figures | resolved |
""",
        encoding="utf-8",
    )
    (reports / "EXPERIMENT_LOG.md").write_text(
        """# Experiment Log

## Failed Attempt

- model_route_rejected: Neural network was rejected because sample size was too small.
- experiment_failed: Genetic algorithm produced infeasible allocations under capacity constraints.
""",
        encoding="utf-8",
    )
    memory_root = tmp_path / "memory"

    output = run_cmd(
        "scripts/memory_distill.py",
        "--workspace",
        str(workspace),
        "--memory-root",
        str(memory_root),
        "--json",
    )

    payload = json.loads(output.stdout)
    assert payload["events_written"] >= 2
    assert (memory_root / "reviewer_lessons.md").exists()
    assert (memory_root / "failed_approaches.md").exists()
    reviewer_lessons = (memory_root / "reviewer_lessons.md").read_text(encoding="utf-8")
    failed_approaches = (memory_root / "failed_approaches.md").read_text(encoding="utf-8")
    assert "Core prediction figure lacks test-set metrics" in reviewer_lessons
    assert "Neural network was rejected" in failed_approaches
    assert "Genetic algorithm produced infeasible allocations" in failed_approaches
