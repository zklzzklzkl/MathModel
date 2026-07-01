"""Live monitor for Claude Code running a MathModelAgent workflow.

The monitor is intentionally dependency-free. It watches the workspace, records
file changes, checks expected math-modeling workflow artifacts, and writes a
human-readable risk report.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import py_compile
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


WORKSPACE = Path(r"D:\WorkSpace_MathModel\workspace")
PROBLEM_PDF = Path(
    r"C:\Users\zklzk\xwechat_files\wxid_nn0sj7wymrcv22_9942\temp\RWTemp\2026-05"
    r"\5b6c4d63a18ef6935b5b8b3c15155806\C题(1).pdf"
)
ATTACHMENT_XLSX = Path(
    r"C:\Users\zklzk\xwechat_files\wxid_nn0sj7wymrcv22_9942\temp\RWTemp\2026-05"
    r"\5b6c4d63a18ef6935b5b8b3c15155806\附件(1).xlsx"
)

MONITOR_DIR = WORKSPACE / "_monitor"
STATUS_MD = MONITOR_DIR / "status.md"
EVENTS_JSONL = MONITOR_DIR / "events.jsonl"
SNAPSHOT_JSON = MONITOR_DIR / "snapshot.json"
RISK_MD = MONITOR_DIR / "risk_register.md"
EXPERIENCE_MD = MONITOR_DIR / "experience_summary.md"
REPORT_ENCODING = "utf-8-sig"
IGNORED_DIRS = {"_monitor", "__pycache__", ".git"}
IGNORED_FILES = {
    "monitor_claude_workflow.py",
    "run_monitor_once.bat",
    "run_monitor_live.bat",
}

CONTRACT_FILES = [
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
    "reports/VERIFY_REPORT.md",
]

FINAL_CANDIDATES = [
    "paper/main.typ",
    "paper/main.tex",
    "paper/main.pdf",
    "paper.typ",
    "paper.tex",
    "paper.pdf",
    "paper.docx",
    "res.md",
    "res.docx",
    "report.pdf",
]

PLACEHOLDER_PATTERNS = [
    "TODO",
    "PLACEHOLDER",
    "待补",
    "待填",
    "待完成",
    "示例数据",
    "xxx",
    "TBD",
]

MOJIBAKE_MARKERS = [
    "锛",
    "鐜",
    "绋",
    "璁",
    "寤",
    "浠",
    "闂",
    "妯",
    "骞",
    "鍖",
]


@dataclass
class Risk:
    severity: str
    area: str
    message: str
    evidence: str
    recommendation: str


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE)).replace("\\", "/")
    except ValueError:
        return str(path)


def ensure_monitor_dir() -> None:
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)


def list_files() -> list[Path]:
    if not WORKSPACE.exists():
        return []
    files: list[Path] = []
    for path in WORKSPACE.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(WORKSPACE).parts
        if any(part in IGNORED_DIRS for part in relative_parts):
            continue
        if rel(path) in IGNORED_FILES:
            continue
        files.append(path)
    return sorted(files)


def file_snapshot(files: Iterable[Path]) -> dict[str, dict[str, object]]:
    snap: dict[str, dict[str, object]] = {}
    for path in files:
        try:
            stat = path.stat()
        except OSError:
            continue
        snap[rel(path)] = {
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        }
    return snap


def load_previous_snapshot() -> dict[str, dict[str, object]]:
    if not SNAPSHOT_JSON.exists():
        return {}
    try:
        return json.loads(SNAPSHOT_JSON.read_text(encoding=REPORT_ENCODING))
    except Exception:
        return {}


def append_event(event: dict[str, object]) -> None:
    ensure_monitor_dir()
    with EVENTS_JSONL.open("a", encoding=REPORT_ENCODING) as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def record_changes(previous: dict[str, dict[str, object]], current: dict[str, dict[str, object]]) -> list[str]:
    changes: list[str] = []
    prev_keys = set(previous)
    curr_keys = set(current)
    for name in sorted(curr_keys - prev_keys):
        changes.append(f"created {name}")
    for name in sorted(prev_keys - curr_keys):
        changes.append(f"deleted {name}")
    for name in sorted(curr_keys & prev_keys):
        if previous[name].get("size") != current[name].get("size") or previous[name].get("mtime") != current[name].get("mtime"):
            changes.append(f"modified {name}")
    if changes:
        append_event({"time": now_iso(), "type": "file_changes", "changes": changes})
    return changes


def claude_processes() -> list[dict[str, str]]:
    try:
        raw = subprocess.check_output(["tasklist", "/fo", "csv", "/v"], text=True, encoding="utf-8", errors="replace")
    except Exception:
        return []
    rows = csv.DictReader(raw.splitlines())
    procs = []
    for row in rows:
        image = row.get("Image Name", "")
        title = row.get("Window Title", "")
        if "claude" in image.lower() or "claude" in title.lower():
            procs.append(
                {
                    "image": image,
                    "pid": row.get("PID", ""),
                    "status": row.get("Status", ""),
                    "title": title,
                }
            )
    return procs


def read_text(path: Path, max_chars: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        return ""


def text_files(files: list[Path]) -> list[Path]:
    exts = {".md", ".txt", ".py", ".csv", ".json", ".tex", ".typ", ".log"}
    return [p for p in files if p.suffix.lower() in exts and p.stat().st_size <= 2_000_000]


def detect_mojibake(text: str) -> int:
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def detect_placeholders(text: str) -> list[str]:
    hits = []
    upper = text.upper()
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.upper() in upper:
            hits.append(pattern)
    return hits


def compile_python(path: Path) -> str | None:
    try:
        py_compile.compile(str(path), doraise=True)
        return None
    except py_compile.PyCompileError as exc:
        return str(exc).splitlines()[-1]
    except Exception as exc:
        return str(exc)


def infer_phase(files: list[Path]) -> str:
    rels = {rel(p) for p in files}
    if any(name in rels for name in ["reports/VERIFY_REPORT.md", "paper/main.pdf", "res.docx"]):
        return "final_verification_or_complete"
    if any(name.startswith("paper/") for name in rels) or "reports/CLAIM_TRACE.md" in rels:
        return "writing"
    if "reports/DRAWIO_REPORT.md" in rels:
        return "drawio"
    if "results/RESULTS_MANIFEST.json" in rels or "reports/RESULTS_REPORT.md" in rels:
        return "coding_results"
    if "reports/ANALYSIS_MODELING_REPORT.md" in rels or "reports/MODELING_DECISIONS.md" in rels:
        return "analysis_modeling"
    if "reports/TRIAGE_REPORT.md" in rels or "PROBLEM_BRIEF.md" in rels:
        return "triage"
    if any(p.suffix.lower() == ".csv" for p in files) or any(p.name.startswith("problem_page") for p in files):
        return "input_extraction"
    return "not_started"


def evaluate(files: list[Path], stale_minutes: int) -> tuple[list[Risk], dict[str, object]]:
    risks: list[Risk] = []
    rels = {rel(p) for p in files}
    processes = claude_processes()
    now = time.time()

    if not WORKSPACE.exists():
        risks.append(Risk("CRITICAL", "workspace", "工作目录不存在。", str(WORKSPACE), "创建工作目录并重新启动流程。"))
    if not PROBLEM_PDF.exists():
        risks.append(Risk("CRITICAL", "input", "题目 PDF 不存在。", str(PROBLEM_PDF), "确认微信临时文件是否已被清理，复制题面到工作区。"))
    if not ATTACHMENT_XLSX.exists():
        risks.append(Risk("CRITICAL", "input", "附件 xlsx 不存在。", str(ATTACHMENT_XLSX), "确认微信临时文件是否已被清理，复制附件到工作区。"))
    if not processes:
        risks.append(Risk("HIGH", "runtime", "未检测到 Claude Code 进程。", "tasklist 中无 claude", "若需要实时监控，先启动 Claude Code 并在目标工作区运行。"))

    problem_pages = [p for p in files if p.name.startswith("problem_page") and p.suffix.lower() == ".txt"]
    if not problem_pages:
        risks.append(Risk("HIGH", "input_extraction", "未发现题面抽取文本。", "缺少 problem_page*.txt", "先把 PDF 题面可靠抽取为 UTF-8 文本，并校验公式和单位。"))
    else:
        combined = "\n".join(read_text(p) for p in problem_pages)
        if len(combined) < 1000:
            risks.append(Risk("MEDIUM", "input_extraction", "题面文本过短，可能抽取不完整。", f"chars={len(combined)}", "重新抽取 PDF 或补充人工校对文本。"))
        mojibake = detect_mojibake(combined)
        if mojibake > 20:
            risks.append(Risk("HIGH", "encoding", "题面文本存在明显乱码，可能影响题意理解。", f"mojibake_markers={mojibake}", "重新以正确编码/OCR 抽取题面，生成 PROBLEM_BRIEF.md 前必须人工校对。"))

    csvs = [p for p in files if p.suffix.lower() == ".csv"]
    if len(csvs) < 3:
        risks.append(Risk("MEDIUM", "data", "附件拆分出的 CSV 数量少于预期。", f"csv_count={len(csvs)}", "核对 Excel sheet 是否完整导出。"))

    for py in [p for p in files if p.suffix.lower() == ".py"]:
        err = compile_python(py)
        if err:
            risks.append(Risk("CRITICAL", "code", "Python 文件无法编译。", f"{rel(py)}: {err}", "先修复语法和编码问题，再运行建模代码。"))

    for contract in CONTRACT_FILES:
        if contract not in rels:
            severity = "HIGH" if contract in {"PROBLEM_BRIEF.md", "DATA_AUDIT.md", "WORKFLOW_STATE.md"} else "MEDIUM"
            risks.append(Risk(severity, "workflow_contract", "缺少上下文契约文件。", contract, "按 MathModelAgent workflow_state_contract 补齐该阶段产物。"))

    manifest = WORKSPACE / "results" / "RESULTS_MANIFEST.json"
    if manifest.exists():
        try:
            data = json.loads(read_text(manifest))
            if not data.get("metrics") and not data.get("figures"):
                risks.append(Risk("MEDIUM", "results", "RESULTS_MANIFEST.json 没有 metrics 或 figures。", rel(manifest), "把论文可引用的关键数值和图表来源写入 manifest。"))
        except Exception as exc:
            risks.append(Risk("HIGH", "results", "RESULTS_MANIFEST.json 不是合法 JSON。", str(exc), "修复 JSON 后再进入写作。"))

    final_files = [name for name in FINAL_CANDIDATES if name in rels]
    if not final_files:
        risks.append(Risk("MEDIUM", "deliverable", "尚未发现最终论文入口或输出。", ", ".join(FINAL_CANDIDATES), "流程完成前应生成 paper/main.* 或 res.md/res.docx/report.pdf。"))

    for path in text_files(files):
        text = read_text(path)
        placeholders = detect_placeholders(text)
        if placeholders:
            risks.append(Risk("MEDIUM", "content_quality", "文件中存在占位符或未完成标记。", f"{rel(path)}: {', '.join(placeholders)}", "进入最终验收前清理占位内容。"))
        mojibake = detect_mojibake(text)
        if mojibake > 30:
            risks.append(Risk("HIGH", "encoding", "文件存在明显乱码。", f"{rel(path)}: mojibake_markers={mojibake}", "重新生成或修复编码，避免论文和代码变量含义错乱。"))

    if files:
        latest = max(p.stat().st_mtime for p in files)
        age_min = (now - latest) / 60
        if processes and age_min > stale_minutes:
            risks.append(Risk("MEDIUM", "runtime", "Claude Code 仍在运行但工作区长时间无文件更新。", f"last_update_minutes={age_min:.1f}", "检查 Claude 是否卡住在等待输入、报错或长时间推理。"))

    summary = {
        "time": now_iso(),
        "workspace": str(WORKSPACE),
        "phase": infer_phase(files),
        "file_count": len(files),
        "claude_process_count": len(processes),
        "claude_processes": processes,
        "risk_count": len(risks),
        "critical_count": sum(1 for r in risks if r.severity == "CRITICAL"),
        "high_count": sum(1 for r in risks if r.severity == "HIGH"),
        "medium_count": sum(1 for r in risks if r.severity == "MEDIUM"),
    }
    return risks, summary


def write_reports(risks: list[Risk], summary: dict[str, object], changes: list[str]) -> None:
    ensure_monitor_dir()
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    risks_sorted = sorted(risks, key=lambda r: (severity_order.get(r.severity, 9), r.area, r.message))

    status_lines = [
        "# Claude Code 数学建模实时监控状态",
        "",
        f"- 更新时间：{summary['time']}",
        f"- 工作目录：`{summary['workspace']}`",
        f"- 推断阶段：`{summary['phase']}`",
        f"- 文件数：{summary['file_count']}",
        f"- Claude 进程数：{summary['claude_process_count']}",
        f"- 风险总数：{summary['risk_count']}（CRITICAL {summary['critical_count']} / HIGH {summary['high_count']} / MEDIUM {summary['medium_count']}）",
        "",
        "## 最近文件变化",
    ]
    if changes:
        status_lines.extend(f"- {c}" for c in changes[-30:])
    else:
        status_lines.append("- 本轮未检测到变化。")

    status_lines.extend(["", "## 当前最高风险"])
    if risks_sorted:
        for risk in risks_sorted[:12]:
            status_lines.append(f"- **{risk.severity} / {risk.area}**：{risk.message} 证据：`{risk.evidence}`")
    else:
        status_lines.append("- 暂未发现风险。")
    STATUS_MD.write_text("\n".join(status_lines) + "\n", encoding=REPORT_ENCODING)

    risk_lines = [
        "# 风险登记表",
        "",
        "| 严重性 | 区域 | 问题 | 证据 | 建议 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for risk in risks_sorted:
        risk_lines.append(
            f"| {risk.severity} | {risk.area} | {risk.message} | `{risk.evidence}` | {risk.recommendation} |"
        )
    RISK_MD.write_text("\n".join(risk_lines) + "\n", encoding=REPORT_ENCODING)

    experience_lines = [
        "# 监控经验与阶段性总结",
        "",
        f"更新时间：{summary['time']}",
        "",
        "## 已观察到的不足",
    ]
    if risks_sorted:
        by_area: dict[str, int] = {}
        for risk in risks_sorted:
            by_area[risk.area] = by_area.get(risk.area, 0) + 1
        for area, count in sorted(by_area.items(), key=lambda x: (-x[1], x[0])):
            experience_lines.append(f"- `{area}`：{count} 项风险。")
    else:
        experience_lines.append("- 暂未发现明显不足。")
    experience_lines.extend(
        [
            "",
            "## 当前经验",
            "- 数学建模流程必须先修正题面和数据编码，再进入建模与写作。",
            "- Python 代码应在每次生成后立即做语法编译检查，避免错误积累到最终阶段。",
            "- 论文数值必须通过 `RESULTS_MANIFEST.json` 统一追踪，不能依赖聊天记忆。",
            "",
            "## 下一步建议",
            "- 先处理 CRITICAL 和 HIGH 风险，再允许 Claude Code 进入下一阶段。",
            "- 若长时间没有文件更新，检查 Claude Code 是否卡在交互确认或报错。",
        ]
    )
    EXPERIENCE_MD.write_text("\n".join(experience_lines) + "\n", encoding=REPORT_ENCODING)

    append_event(
        {
            "time": summary["time"],
            "type": "evaluation",
            "summary": summary,
            "risks": [asdict(r) for r in risks_sorted],
        }
    )


def run_once(stale_minutes: int) -> dict[str, object]:
    ensure_monitor_dir()
    previous = load_previous_snapshot()
    files = list_files()
    current = file_snapshot(files)
    changes = record_changes(previous, current)
    risks, summary = evaluate(files, stale_minutes=stale_minutes)
    write_reports(risks, summary, changes)
    SNAPSHOT_JSON.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding=REPORT_ENCODING)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor Claude Code MathModelAgent workflow.")
    parser.add_argument("--once", action="store_true", help="Run a single scan and exit.")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds.")
    parser.add_argument("--max-minutes", type=int, default=0, help="Stop after N minutes; 0 means run until Ctrl+C.")
    parser.add_argument("--stale-minutes", type=int, default=15, help="Warn if Claude is running but workspace is stale.")
    args = parser.parse_args()

    if args.once:
        summary = run_once(args.stale_minutes)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    start = time.time()
    print(f"[{now_iso()}] Monitoring {WORKSPACE}")
    print(f"Reports: {MONITOR_DIR}")
    while True:
        summary = run_once(args.stale_minutes)
        print(
            f"[{summary['time']}] phase={summary['phase']} files={summary['file_count']} "
            f"risks={summary['risk_count']} critical={summary['critical_count']} high={summary['high_count']}"
        )
        if args.max_minutes and (time.time() - start) > args.max_minutes * 60:
            break
        time.sleep(max(5, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
