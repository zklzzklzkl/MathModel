from __future__ import annotations

import json
import os
import sqlite3
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


def write_sample(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_ingest_records_source_quality_ledger_fields(tmp_path: Path) -> None:
    source = tmp_path / "source"
    db_path = tmp_path / "rag.sqlite3"
    write_sample(
        source / "cumcm_problems" / "official_problem.md",
        """---
library: cumcm_problems
year: 2026
contest: CUMCM
problem_id: A
tags: [official, problem]
---

# Official problem statement
This official problem statement defines the contest task and attachment requirements.
""",
    )

    run_cmd("scripts/rag_ingest.py", "--source", str(source), "--db", str(db_path), "--vector-store", "none")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM chunks").fetchone()
        assert row["source_quality"] == "S"
        assert row["source_type"] == "official_problem"
        assert row["allowed_use"] == "core_evidence"
        assert row["quality_reason"]
        assert "last_verified_at" in row.keys()
        assert "verified_by" in row.keys()
    finally:
        conn.close()


def test_query_returns_source_quality_and_core_evidence_policy(tmp_path: Path) -> None:
    source = tmp_path / "source"
    db_path = tmp_path / "rag.sqlite3"
    write_sample(
        source / "cumcm_problems" / "official_problem.md",
        """---
library: cumcm_problems
year: 2026
contest: CUMCM
problem_id: A
tags: [official, problem]
---

# Official problem statement
This official problem statement defines the contest task and attachment requirements.
""",
    )
    write_sample(
        source / "code_templates" / "optimization_template.md",
        """---
library: code_templates
tags: [optimization, python, template]
---

# Optimization template
Use this only as a structure for variable mapping, constraints, metrics, and solver steps.
""",
    )
    write_sample(
        source / "review_rubrics" / "forum_note.md",
        """---
library: review_rubrics
source_quality: C
source_type: forum_note
quality_reason: Unverified forum discussion.
tags: [review, risk]
---

# Forum judging note
This note may inspire a risk check but must not become core modeling evidence.
""",
    )

    run_cmd("scripts/rag_ingest.py", "--source", str(source), "--db", str(db_path), "--vector-store", "none")

    official = json.loads(
        run_cmd(
            "scripts/rag_query.py",
            "official problem attachment requirements",
            "--library",
            "cumcm_problems",
            "--db",
            str(db_path),
            "--json",
        ).stdout
    )["hits"][0]
    assert official["source_quality"] == "S"
    assert official["allowed_use"] == "core_evidence"
    assert official["core_evidence_allowed"] is True
    assert official["quality_reason"]

    template = json.loads(
        run_cmd(
            "scripts/rag_query.py",
            "optimization template constraints solver",
            "--library",
            "code_templates",
            "--db",
            str(db_path),
            "--json",
        ).stdout
    )["hits"][0]
    assert template["source_quality"] == "B"
    assert template["allowed_use"] == "auxiliary_only"
    assert template["core_evidence_allowed"] is False

    forum_note = json.loads(
        run_cmd(
            "scripts/rag_query.py",
            "forum judging note risk",
            "--library",
            "review_rubrics",
            "--db",
            str(db_path),
            "--json",
        ).stdout
    )["hits"][0]
    assert forum_note["source_quality"] == "C"
    assert forum_note["allowed_use"] == "risk_signal_only"
    assert forum_note["core_evidence_allowed"] is False


def test_query_core_only_filters_out_non_core_sources(tmp_path: Path) -> None:
    source = tmp_path / "source"
    db_path = tmp_path / "rag.sqlite3"
    write_sample(
        source / "excellent_papers" / "paper_case.md",
        """---
library: excellent_papers
tags: [prediction, optimization]
---

# High score paper case
The paper case explains a prediction and optimization route with validation evidence.
""",
    )
    write_sample(
        source / "code_templates" / "same_topic.md",
        """---
library: code_templates
tags: [prediction, optimization]
---

# Code skeleton
The code skeleton explains a prediction and optimization route implementation shape.
""",
    )
    run_cmd("scripts/rag_ingest.py", "--source", str(source), "--db", str(db_path), "--vector-store", "none")

    result = json.loads(
        run_cmd(
            "scripts/rag_query.py",
            "prediction optimization route validation",
            "--db",
            str(db_path),
            "--core-only",
            "--json",
        ).stdout
    )
    assert result["hit_count"] == 1
    assert result["hits"][0]["library_id"] == "excellent_papers"
    assert result["hits"][0]["source_quality"] == "A"
