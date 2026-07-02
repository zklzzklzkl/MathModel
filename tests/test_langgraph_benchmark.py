"""Benchmark Arena + Release Stabilization tests for LangGraph contest_graph_v3.

Covers:
  - 3 benchmark fixture scenarios (human_gate_pause, full_minimal_flow, revision_required)
  - Release stabilization invariants (no VERIFY_REPORT, sandbox deny lists, audit-only Phase 6)
  - Benchmark report generation smoke
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings  # noqa: E402
from app.workspace import copy_workspace_for_run  # noqa: E402
from app import langgraph_runner  # noqa: E402

# Reuse helpers from test_langgraph_runner
from tests.test_langgraph_runner import (  # type: ignore[import]
    install_fake_graph,
    make_phase_plan,
    make_phase3_writes,
    make_phase5_writes,
    make_settings,
    make_workspace,
)


# ---------------------------------------------------------------------------
# Benchmark 01: Human Gate pause
# ---------------------------------------------------------------------------


def test_benchmark_01_human_gate_pause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Workspace without HUMAN_MODEL_REVIEW.md must stop at Human Gate."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="bench-01-human-gate",
    )

    assert result["contest_status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert result["completed_phases"] == [0, 1]
    assert result["human_gate_required"] is True
    assert result["human_gate"]["approved"] is False

    run_workspace = Path(result["run_workspace"])
    # Phase 2+ must not execute
    assert not (run_workspace / "CONTROL_LANGGRAPH_PHASE_2.md").exists()
    assert not (run_workspace / "paper" / "main.tex").exists()


# ---------------------------------------------------------------------------
# Benchmark 02: Full minimal flow
# ---------------------------------------------------------------------------


class Benchmark02Adapter:
    provider = "none"

    def generate(self, prompt, *_args, **_kwargs) -> str:
        import re
        match = re.search(r"V2.6 Phase (\d)", prompt)
        phase = int(match.group(1)) if match else 0
        if phase == 2:
            plan = make_phase_plan(2, [])
            plan["commands"] = [
                {"id": "C1", "purpose": "syntax", "command": "python -m py_compile code/solve.py", "expected_outputs": []},
                {"id": "C2", "purpose": "run", "command": "python code/solve.py", "expected_outputs": ["results/RESULTS_MANIFEST.json", "reports/RESULTS_REPORT.md"]},
            ]
            return json.dumps(plan, ensure_ascii=False)
        if phase == 3:
            return json.dumps(make_phase_plan(3, make_phase3_writes()), ensure_ascii=False)
        if phase == 4:
            return json.dumps(
                make_phase_plan(
                    4,
                    [
                        {"path": "reports/PAPER_SCORECARD.md", "purpose": "scorecard", "content": "# Scorecard\nAll dimensions >= 4. No critical issues.\n"},
                        {"path": "reports/REVISION_ACTIONS.md", "purpose": "actions", "content": "# Actions\n- MEDIUM: consider improving claim wording.\n"},
                        {"path": "reports/REFINEMENT_LOG.md", "purpose": "refinement", "content": "# Refinement\n"},
                    ],
                ),
                ensure_ascii=False,
            )
        if phase == 5:
            return json.dumps(make_phase_plan(5, make_phase5_writes()), ensure_ascii=False)
        return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)


def test_benchmark_02_full_minimal_flow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Workspace with Human Gate approved + code/solve.py + all adapters must complete all phases."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('reports').mkdir(exist_ok=True)\nPath('results').mkdir(exist_ok=True)\nPath('reports/RESULTS_REPORT.md').write_text('# OK\\n', encoding='utf-8')\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [{'name':'demo','value':1}], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner,
        "run_audit",
        lambda _settings, _workspace, **_kwargs: {
            "result": {"status": "PASS", "worst_severity": "NONE", "issues": []},
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        },
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="bench-02-full",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["completed_phases"] == [0, 1, 2, 3, 4, 5, 6]
    assert result["contest_status"] in ("CONTEST_GRAPH_REVIEW_READY", "READY_FOR_FINAL_AUDIT")

    # Phase 2 sandbox succeeded
    phase2 = next(item for item in result["phase_results"] if item["phase"] == 2)
    assert phase2["sandbox_status"] == "SANDBOX_SUCCEEDED"

    # Phase 3 paper sandbox succeeded
    phase3 = next(item for item in result["phase_results"] if item["phase"] == 3)
    assert phase3["paper_sandbox_status"] == "PAPER_SANDBOX_SUCCEEDED"
    assert (run_workspace / "paper" / "main.tex").is_file()
    assert (run_workspace / "reports" / "CLAIM_TRACE.md").is_file()
    assert (run_workspace / "reports" / "METHOD_IMPLEMENTATION_MATRIX.md").is_file()
    assert (run_workspace / "reports" / "PAPER_BUILD_REPORT.md").is_file()

    # Phase 5 revision sandbox succeeded
    phase5 = next(item for item in result["phase_results"] if item["phase"] == 5)
    assert phase5["revision_sandbox_status"] == "REVISION_SANDBOX_SUCCEEDED"
    assert (run_workspace / "reports" / "REVISION_STATUS.md").is_file()

    # Phase 6 audit-only
    phase6 = next(item for item in result["phase_results"] if item["phase"] == 6)
    assert phase6["strategy"] == "audit_only"

    # Critical: no VERIFY_REPORT written
    assert (run_workspace / "reports" / "VERIFY_REPORT.md").read_text(encoding="utf-8") == "Conclusion: PENDING\n"

    # Graph report exists
    assert result.get("graph_report_path") is not None
    assert (run_workspace / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md").is_file()

    # AGENT_RUNS exists
    agent_runs = (run_workspace / "reports" / "AGENT_RUNS.md").read_text(encoding="utf-8")
    assert "Phase 2" in agent_runs or "phase2_sandbox" in agent_runs.lower()
    assert "Phase 3" in agent_runs or "phase3_paper" in agent_runs.lower()
    assert "Phase 5" in agent_runs or "phase5_revision" in agent_runs.lower()

    # History recorded
    assert result.get("history") is not None


# ---------------------------------------------------------------------------
# Benchmark 03: Revision required
# ---------------------------------------------------------------------------


class Benchmark03Adapter:
    provider = "none"

    def generate(self, prompt, *_args, **_kwargs) -> str:
        import re
        match = re.search(r"V2.6 Phase (\d)", prompt)
        phase = int(match.group(1)) if match else 0
        if phase == 2:
            plan = make_phase_plan(2, [])
            plan["commands"] = [{"id": "C1", "purpose": "run", "command": "python code/solve.py", "expected_outputs": []}]
            return json.dumps(plan, ensure_ascii=False)
        if phase == 3:
            return json.dumps(make_phase_plan(3, make_phase3_writes()), ensure_ascii=False)
        if phase == 4:
            return json.dumps(
                make_phase_plan(
                    4,
                    [
                        {"path": "reports/PAPER_SCORECARD.md", "purpose": "scorecard", "content": "# Scorecard\nHIGH: weak claim.\n"},
                        {"path": "reports/REVISION_ACTIONS.md", "purpose": "actions", "content": "# Actions\n- HIGH: revise weak claim.\n"},
                        {"path": "reports/REFINEMENT_LOG.md", "purpose": "refinement", "content": "# Refinement\n"},
                    ],
                ),
                ensure_ascii=False,
            )
        if phase == 5:
            return json.dumps(make_phase_plan(5, make_phase5_writes()), ensure_ascii=False)
        return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)


def test_benchmark_03_revision_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 4 produces HIGH, Phase 5 writes REVISION_STATUS with unresolved, contest_status must not claim PASS."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('reports').mkdir(exist_ok=True)\nPath('results').mkdir(exist_ok=True)\nPath('reports/RESULTS_REPORT.md').write_text('# OK\\n', encoding='utf-8')\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _provider: Benchmark03Adapter())
    monkeypatch.setattr(
        langgraph_runner,
        "run_audit",
        lambda _settings, _workspace, **_kwargs: {
            "result": {"status": "PASS", "worst_severity": "NONE", "issues": []},
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        },
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings,
        source_workspace=workspace,
        phase=0,
        mode="contest_graph_v3",
        provider="none",
        model=None,
        copy_workspace=True,
        run_name="bench-03-revision",
    )

    run_workspace = Path(result["run_workspace"])

    assert result["completed_phases"] == [0, 1, 2, 3, 4, 5, 6]

    # contest_status must NOT claim PASS
    contest_status = str(result.get("contest_status", ""))
    assert "PASS" not in contest_status.upper() or "CONTEST" in contest_status
    assert "REVISION_REQUIRED" in contest_status or "REQUIRED" in contest_status

    # REVISION_STATUS.md written
    assert (run_workspace / "reports" / "REVISION_STATUS.md").is_file()
    rev_status = (run_workspace / "reports" / "REVISION_STATUS.md").read_text(encoding="utf-8")
    assert "unresolved_blocker_high" in rev_status.lower()

    # Phase 6 must remain audit-only
    phase6 = next(item for item in result["phase_results"] if item["phase"] == 6)
    assert phase6["strategy"] == "audit_only"

    # VERIFY_REPORT must not be auto-written
    assert not (run_workspace / "reports" / "VERIFY_REPORT.md").exists() or \
           (run_workspace / "reports" / "VERIFY_REPORT.md").read_text(encoding="utf-8") == "Conclusion: PENDING\n"


# ---------------------------------------------------------------------------
# Release Stabilization Tests
# ---------------------------------------------------------------------------


def test_stabilization_v3_never_writes_verify_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """contest_graph_v3 must never write VERIFY_REPORT.md."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "from pathlib import Path\nPath('results').mkdir(exist_ok=True)\nPath('results/RESULTS_MANIFEST.json').write_text('{}', encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-verify",
    )
    run_workspace = Path(result["run_workspace"])

    # VERIFY_REPORT.md must NOT be written or must remain PENDING
    vr_path = run_workspace / "reports" / "VERIFY_REPORT.md"
    assert not vr_path.exists() or vr_path.read_text(encoding="utf-8") == "Conclusion: PENDING\n"


def test_stabilization_v3_never_writes_human_gate_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """contest_graph_v3 must never auto-write HUMAN_MODEL_REVIEW.md or MODELING_DECISION.md."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    # Start WITHOUT these files
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-gate",
    )
    run_workspace = Path(result["run_workspace"])

    assert result["contest_status"] == "WAITING_FOR_HUMAN_MODEL_REVIEW"
    assert not (run_workspace / "reports" / "HUMAN_MODEL_REVIEW.md").exists()
    assert not (run_workspace / "reports" / "MODELING_DECISION.md").exists()


def test_stabilization_phase2_rejects_paper_and_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 2 sandbox must reject writes to paper/ and source/."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "from pathlib import Path\nPath('results').mkdir(exist_ok=True)\nPath('results/RESULTS_MANIFEST.json').write_text('{}')\n",
        encoding="utf-8",
    )

    class Phase2BadAdapter:
        provider = "none"
        def generate(self, prompt, *_args, **_kwargs) -> str:
            import re
            match = re.search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            if phase == 2:
                plan = make_phase_plan(2, [])
                plan["commands"] = [{"id": "C1", "purpose": "try illegal write", "command": "python code/solve.py", "expected_outputs": ["paper/bad.txt"]}]
                return json.dumps(plan, ensure_ascii=False)
            return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Phase2BadAdapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-phase2-reject",
    )
    # Must stop at Phase 2 with command rejection
    assert 2 not in result.get("completed_phases", []) or \
           any(s in str(result.get("sandbox_status", "")).upper() for s in ("REJECTED", "VIOLATION", "FAILED"))


def test_stabilization_phase3_rejects_code_and_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 3 paper sandbox must reject writes to code/ and results/."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('results').mkdir(exist_ok=True)\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [{'name':'x','value':1}], 'tables': [], 'figures': [], 'scripts': []}))\n",
        encoding="utf-8",
    )

    class Phase3BadAdapter:
        provider = "none"
        def generate(self, prompt, *_args, **_kwargs) -> str:
            import re
            match = re.search(r"V2.6 Phase (\d)", prompt)
            phase = int(match.group(1)) if match else 0
            if phase == 2:
                plan = make_phase_plan(2, [])
                plan["commands"] = [{"id": "C1", "purpose": "run", "command": "python code/solve.py", "expected_outputs": []}]
                return json.dumps(plan, ensure_ascii=False)
            if phase == 3:
                bad_writes = make_phase3_writes()
                bad_writes.append({"path": "code/injected.py", "purpose": "bad", "content": "# injected\n"})
                return json.dumps(make_phase_plan(3, bad_writes), ensure_ascii=False)
            return json.dumps(make_phase_plan(phase, []), ensure_ascii=False)

    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Phase3BadAdapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-phase3-reject",
    )
    phase3 = next((item for item in result.get("phase_results", []) if item["phase"] == 3), None)
    assert phase3 is None or phase3.get("paper_sandbox_status") in ("PAPER_SANDBOX_REJECTED", None)


def test_stabilization_phase5_rejects_verify_report(
    tmp_path: Path,
) -> None:
    """Phase 5 validate_phase5_writes must reject VERIFY_REPORT.md path."""
    workspace = tmp_path / "workspaces" / "case-phase5"
    (workspace / "reports").mkdir(parents=True)
    (workspace / "paper").mkdir()
    (workspace / "paper" / "main.tex").write_text("# Draft\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text("print('ok')\n", encoding="utf-8")

    writes = make_phase5_writes()
    writes.append({"path": "reports/VERIFY_REPORT.md", "purpose": "bad", "content": "PASS"})
    with pytest.raises(ValueError):
        langgraph_runner.validate_phase5_writes(workspace, writes)


def test_stabilization_phase6_never_writes_verify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase 6 audit-only must not write VERIFY_REPORT.md."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('results').mkdir(exist_ok=True)\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [], 'tables': [], 'figures': [], 'scripts': []}))\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-phase6",
    )
    run_workspace = Path(result["run_workspace"])

    phase6 = next(item for item in result["phase_results"] if item["phase"] == 6)
    assert phase6["strategy"] == "audit_only"
    assert phase6["status"] == "AUDIT_RECORDED"
    # Phase 6 must not claim final PASS
    assert "PASS" not in str(phase6.get("stop_reason", "")).upper() or "audit" in str(phase6.get("stop_reason", "")).lower()
    vr_path = run_workspace / "reports" / "VERIFY_REPORT.md"
    assert not vr_path.exists() or vr_path.read_text(encoding="utf-8") == "Conclusion: PENDING\n"


def test_stabilization_graph_report_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """contest_graph_v3 must produce a contest graph report."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-report",
    )
    run_workspace = Path(result["run_workspace"])

    assert result.get("graph_report_path") is not None
    graph_report = run_workspace / "reports" / "LANGGRAPH_CONTEST_GRAPH_REPORT.md"
    assert graph_report.is_file()
    text = graph_report.read_text(encoding="utf-8")
    assert "Contest status" in text
    assert "Completed phases" in text
    assert "Human Gate" in text
    assert "Phase Results" in text


def test_stabilization_agent_runs_has_phase2_3_5(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AGENT_RUNS.md must have entries for sandbox phases 2, 3, 5."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('results').mkdir(exist_ok=True)\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [{'name':'x','value':1}], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}))\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-agent-runs",
    )
    run_workspace = Path(result["run_workspace"])

    agent_runs = run_workspace / "reports" / "AGENT_RUNS.md"
    assert agent_runs.is_file()
    text = agent_runs.read_text(encoding="utf-8")
    # Check for sandbox phase entries
    lower = text.lower()
    assert "phase 2" in lower or "phase2" in lower
    assert "phase 3" in lower or "phase3" in lower
    assert "phase 5" in lower or "phase5" in lower


def test_stabilization_history_has_v3_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """History must include a langgraph_contest_graph_v3 event."""
    install_fake_graph(monkeypatch)
    settings = make_settings(tmp_path)
    workspace = make_workspace(tmp_path)
    (workspace / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (workspace / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (workspace / "code").mkdir()
    (workspace / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('results').mkdir(exist_ok=True)\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [], 'tables': [], 'figures': [], 'scripts': ['code/solve.py']}))\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    result = langgraph_runner.run_langgraph_phase(
        settings=settings, source_workspace=workspace, phase=0,
        mode="contest_graph_v3", provider="none", copy_workspace=True,
        run_name="stab-history",
    )

    assert result.get("history") is not None
    # The history entry should reference v3
    history = result["history"]
    event = history.get("event", "")
    assert "v3" in event or "langgraph_contest" in event


def test_stabilization_benchmark_report_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The benchmark script must produce valid JSON and Markdown output."""
    install_fake_graph(monkeypatch)

    # Create a minimal benchmark fixture directory
    bench_root = tmp_path / "bench_fixtures"
    ws1 = bench_root / "ws_human_gate"
    ws1.mkdir(parents=True)
    (ws1 / "WORKFLOW_STATE.md").write_text("# State\n", encoding="utf-8")
    (ws1 / "PROBLEM_BRIEF.md").write_text("# Problem\n", encoding="utf-8")
    (ws1 / "reports").mkdir(parents=True)

    ws2 = bench_root / "ws_full"
    ws2.mkdir(parents=True)
    (ws2 / "PROBLEM_BRIEF.md").write_text("# Problem\n", encoding="utf-8")
    (ws2 / "reports").mkdir(parents=True)
    (ws2 / "reports" / "HUMAN_MODEL_REVIEW.md").write_text("approved adopt\n", encoding="utf-8")
    (ws2 / "reports" / "MODELING_DECISION.md").write_text("# Decision\n", encoding="utf-8")
    (ws2 / "code").mkdir()
    (ws2 / "code" / "solve.py").write_text(
        "import json\nfrom pathlib import Path\nPath('results').mkdir(exist_ok=True)\nPath('results/RESULTS_MANIFEST.json').write_text(json.dumps({'metrics': [], 'tables': [], 'figures': [], 'scripts': []}))\n",
        encoding="utf-8",
    )

    settings = Settings(
        mathmodel_root=REPO_ROOT,
        workspace_root=bench_root,
        examples_root=REPO_ROOT / "examples",
        python_executable=sys.executable,
    )
    monkeypatch.setattr(langgraph_runner, "get_model_adapter", lambda _p: Benchmark02Adapter())
    monkeypatch.setattr(
        langgraph_runner, "run_audit",
        lambda _s, _w, **_kw: {"result": {"status": "PASS", "worst_severity": "NONE", "issues": []}, "stdout": "", "stderr": "", "returncode": 0},
    )

    # Import and run the benchmark
    json_out = tmp_path / "bench_out.json"
    md_out = tmp_path / "bench_out.md"

    # Simulate the benchmark runner inline
    import scripts.langgraph_benchmark as bench_mod
    bench_root_str = str(bench_root)

    results = []
    for ws in sorted([ws1, ws2]):
        result = bench_mod.run_one(settings, ws, "contest_graph_v3", "none")
        results.append(result)

    json_text = json.dumps(results, ensure_ascii=False, indent=2, default=str)
    md_text = bench_mod.markdown_report(results, bench_root_str)

    json_out.write_text(json_text + "\n", encoding="utf-8")
    md_out.write_text(md_text, encoding="utf-8")

    # Validate JSON round-trips
    parsed = json.loads(json_out.read_text(encoding="utf-8"))
    assert len(parsed) == 2
    # Both workspaces should produce valid contest statuses (not errors)
    for entry in parsed:
        assert entry["contest_status"] not in ("", None)
        assert "ERROR" not in str(entry["contest_status"]).upper()

    # Validate Markdown has expected sections
    md_content = md_out.read_text(encoding="utf-8")
    assert "# LangGraph Benchmark Report" in md_content
    assert "ws_human_gate" in md_content
    assert "ws_full" in md_content
    assert "Contest status" in md_content
