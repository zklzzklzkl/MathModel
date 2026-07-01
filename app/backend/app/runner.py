from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .config import Settings


def run_command(args: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )


def run_audit(settings: Settings, workspace: Path, nature: str = "auto") -> dict[str, Any]:
    completed = run_command(
        [
            settings.python_executable,
            str(settings.audit_script),
            "--workspace",
            str(workspace),
            "--nature-enabled",
            nature,
        ],
        settings.mathmodel_root,
    )
    result: dict[str, Any]
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {"status": "ERROR", "issues": [], "summary": {}, "raw": completed.stdout}
    return {
        "result": result,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def run_benchmark(settings: Settings) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mm-benchmark-") as tmp:
        json_out = Path(tmp) / "benchmark.json"
        completed = run_command(
            [
                settings.python_executable,
                str(settings.benchmark_script),
                "--root",
                str(settings.examples_root / "2022C"),
                "--json-out",
                str(json_out),
            ],
            settings.mathmodel_root,
        )
        results: list[dict[str, Any]] = []
        if json_out.is_file():
            try:
                raw = json.loads(json_out.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    results = raw
            except json.JSONDecodeError:
                results = []
    return {
        "results": results,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def run_scaffold(settings: Settings, workspace: Path, payload: Any) -> dict[str, Any]:
    if workspace.exists() and any(workspace.iterdir()) and not payload.force:
        raise HTTPException(status_code=409, detail="Workspace already exists; use force to overwrite scaffold files")
    args = [
        settings.python_executable,
        str(settings.scaffold_script),
        str(workspace),
        "--contest",
        payload.contest,
        "--engine",
        payload.engine,
        "--language",
        payload.language,
        "--subproblems",
        payload.subproblems,
        "--figure-backend",
        payload.figure_backend,
        "--nature",
        payload.nature,
    ]
    if payload.force:
        args.append("--force")
    completed = run_command(args, settings.mathmodel_root)
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Scaffold did not return JSON: {completed.stderr}") from exc
    if completed.returncode != 0:
        raise HTTPException(status_code=500, detail=completed.stderr or completed.stdout)
    return {
        "parsed": parsed,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
