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


def count_rows(db_path: Path, table: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


def test_ingest_is_idempotent_and_keeps_required_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    db_path = tmp_path / "rag.sqlite3"
    write_sample(
        source / "model_methods" / "evaluation.md",
        """---
library: model_methods
year: 2026
contest: generic
problem_id: evaluation-test
tags: [evaluation, topsis, sensitivity]
license: project-authored
---

# 综合评价 TOPSIS 模型卡

综合评价类题目需要说明指标方向、权重来源和排名稳定性。
TOPSIS 必须和等权 baseline 比较，并做权重敏感性。
""",
    )

    for _ in range(2):
        run_cmd(
            "scripts/rag_ingest.py",
            "--source",
            str(source),
            "--db",
            str(db_path),
            "--vector-store",
            "none",
            "--json",
        )

    assert count_rows(db_path, "chunks") == 1
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM chunks").fetchone()
        assert row["library_id"] == "model_methods"
        assert row["source_path"]
        assert row["content_hash"]
        assert row["chunk_hash"]
        assert row["year"] == "2026"
        assert "topsis" in row["tags_json"]
    finally:
        conn.close()


def test_empty_files_are_skipped_and_logged(tmp_path: Path) -> None:
    source = tmp_path / "source"
    db_path = tmp_path / "rag.sqlite3"
    empty = source / "model_methods" / "empty.md"
    empty.parent.mkdir(parents=True, exist_ok=True)
    empty.write_text("", encoding="utf-8")

    output = run_cmd(
        "scripts/rag_ingest.py",
        "--source",
        str(source),
        "--db",
        str(db_path),
        "--vector-store",
        "none",
        "--json",
    )
    summary = json.loads(output.stdout)
    assert summary["files_skipped"] == 1
    assert count_rows(db_path, "ingest_errors") == 1


def test_query_returns_sourced_evaluation_hit(tmp_path: Path) -> None:
    source = tmp_path / "source"
    db_path = tmp_path / "rag.sqlite3"
    write_sample(
        source / "model_methods" / "evaluation.md",
        """---
library: model_methods
year: 2026
contest: generic
problem_id: evaluation-test
tags: [evaluation, topsis, entropy-weight, sensitivity]
license: project-authored
---

# 综合评价模型卡

综合评价、排序和风险评分可以使用熵权 TOPSIS。
必须说明权重、标准化和稳定性，并与 baseline 比较。
""",
    )
    run_cmd("scripts/rag_ingest.py", "--source", str(source), "--db", str(db_path), "--vector-store", "none")

    output = run_cmd(
        "scripts/rag_query.py",
        "综合评价 TOPSIS 权重 稳定性",
        "--library",
        "model_methods",
        "--db",
        str(db_path),
        "--json",
    )
    result = json.loads(output.stdout)
    assert result["hit_count"] >= 1
    hit = result["hits"][0]
    assert hit["library_id"] == "model_methods"
    assert hit["source_path"]
    assert hit["source_relpath"].endswith("evaluation.md")
    assert hit["confidence"] in {"high", "medium"}
    assert "risk_warning" in hit


def test_query_preserves_hybrid_prediction_optimization_route(tmp_path: Path) -> None:
    source = tmp_path / "source"
    db_path = tmp_path / "rag.sqlite3"
    write_sample(
        source / "model_methods" / "hybrid.md",
        """---
library: model_methods
year: 2026
contest: generic
problem_id: hybrid-test
tags: [prediction, optimization, hybrid, validation]
license: project-authored
---

# 预测 + 优化混合题模型卡

先预测需求、风险或流量，再把预测结果输入资源配置或调度优化。
基准模型包括历史均值和贪心分配，验证包括预测误差、约束可行性和情景敏感性。
""",
    )
    run_cmd("scripts/rag_ingest.py", "--source", str(source), "--db", str(db_path), "--vector-store", "none")

    output = run_cmd(
        "scripts/rag_query.py",
        "预测 优化 混合 约束 验证",
        "--library",
        "model_methods",
        "--db",
        str(db_path),
        "--json",
    )
    result = json.loads(output.stdout)
    assert result["hit_count"] == 1
    hit = result["hits"][0]
    assert "prediction" in hit["tags"]
    assert "optimization" in hit["tags"]
    assert "hybrid" in hit["tags"]
    assert "约束" in hit["snippet"] or "优化" in hit["snippet"]
