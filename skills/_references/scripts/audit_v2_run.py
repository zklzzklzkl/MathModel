"""Read-only V2 workspace audit for figure and paper-quality regressions.

This script is intentionally conservative. It does not modify the contest
workspace; it reports issues that should be copied into VERIFY_REPORT.md and
REVISION_ACTIONS.md by mm-final-verify.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import resolve_nature_figure


AUDIT_REQUIRED_COLUMNS = [
    "Figure",
    "Inserted",
    "Opens",
    "Readable Text",
    "Labels/Units",
    "Backend Match",
    "Vector Export",
    "Source Data Trace",
    "Stats/Legend",
    "Caption Supports Claim",
    "Status",
    "Required Fix",
]

DATA_ARCHETYPE_WORDS = (
    "bar",
    "box",
    "heatmap",
    "matrix",
    "scatter",
    "line",
    "curve",
    "network",
    "roc",
    "pca",
    "rank",
    "distribution",
    "quantitative",
)

NON_DATA_ARCHETYPE_WORDS = ("flow", "diagram", "schematic", "framework", "process")


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> Any:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def add_issue(issues: list[dict[str, str]], severity: str, code: str, message: str, evidence: str) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "evidence": evidence,
        }
    )


def severity_rank(severity: str) -> int:
    return {"BLOCKER": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(severity, 0)


def resolve_manifest_path(workspace: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return workspace / path


def detect_nature(workspace: Path, mode: str) -> dict[str, Any]:
    if mode == "yes":
        return {"available": True, "mode": "forced"}
    if mode == "no":
        return {"available": False, "mode": "disabled"}

    checked: list[str] = []
    for root in resolve_nature_figure.candidate_roots(workspace):
        resolved = root.expanduser().resolve()
        checked.append(str(resolved))
        ok, layout, skill_dir, missing = resolve_nature_figure.validate_root(resolved)
        if ok:
            return {
                "available": True,
                "mode": "auto",
                "root": str(resolved),
                "layout": layout,
                "nature_figure": str(skill_dir),
                "checked": checked,
                "required_files_missing": [],
            }
    return {
        "available": False,
        "mode": "auto",
        "root": None,
        "layout": None,
        "nature_figure": None,
        "checked": checked,
        "required_files_missing": resolve_nature_figure.REQUIRED_SKILL_FILES,
    }


def parse_plan_rows(text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 8 or cells[0].lower() == "figure id":
            continue
        rows[cells[0].lower()] = {
            "id": cells[0],
            "core_conclusion": cells[1],
            "archetype": cells[2],
            "backend": cells[3],
            "source_data": cells[4],
            "stats": cells[5],
            "intended_section": cells[6],
            "supports_claim": cells[7],
            "raw": stripped,
        }

    current_id: str | None = None
    current: dict[str, str] = {}
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if heading:
            if current_id and current:
                rows[current_id.lower()] = {"id": current_id, **current}
            current_id = heading.group(1).strip()
            current = {"raw": line.strip()}
            continue
        if current_id:
            match = re.match(r"^-\s+([A-Za-z0-9_/-]+):\s*(.*)$", line.strip())
            if match:
                key = match.group(1).strip().lower()
                value = match.group(2).strip()
                current[key] = value
                if key == "figure_archetype":
                    current["archetype"] = value
                elif key == "source_data_needed":
                    current["source_data"] = value
                elif key == "statistics_needed":
                    current["stats"] = value
    if current_id and current:
        rows[current_id.lower()] = {"id": current_id, **current}
    return rows


def figure_id_variants(entry: dict[str, Any], fig_path: Path) -> set[str]:
    entry_id = str(entry.get("id", "")).lower()
    stem = fig_path.stem.lower()
    variants = {
        entry_id,
        stem,
        stem.replace("_", ""),
    }
    for raw in (entry_id, stem):
        match = re.match(r"^(f\d+)", raw)
        if match:
            variants.add(match.group(1))
    return {item for item in variants if item}


def find_plan_row(entry: dict[str, Any], fig_path: Path, plan_rows: dict[str, dict[str, str]]) -> dict[str, str]:
    variants = figure_id_variants(entry, fig_path)
    for key, row in plan_rows.items():
        compact_key = key.replace("_", "")
        if key in variants or compact_key in variants:
            return row
        if any(variant.startswith(key) or variant.startswith(compact_key) for variant in variants):
            return row
    return {}


def is_data_archetype(archetype: str) -> bool:
    lower = archetype.lower()
    if any(word in lower for word in NON_DATA_ARCHETYPE_WORDS):
        return False
    return any(word in lower for word in DATA_ARCHETYPE_WORDS)


def sibling_bundle(path: Path) -> list[str]:
    exts = [".svg", ".pdf", ".tif", ".tiff", ".png"]
    return [str(path.with_suffix(ext)) for ext in exts if path.with_suffix(ext).is_file()]


def bundle_has_vector(paths: list[str]) -> bool:
    return any(Path(item).suffix.lower() in {".svg", ".pdf"} for item in paths)


def parse_audit_columns(text: str) -> list[str]:
    for line in text.splitlines():
        if line.strip().startswith("| Figure |"):
            return [cell.strip() for cell in line.strip().strip("|").split("|")]
    return []


def pdf_page_count(workspace: Path) -> int | None:
    candidates = list((workspace / "paper").glob("*.pdf"))
    if not candidates:
        return None
    try:
        import fitz  # type: ignore
    except Exception:
        verify = read_text(workspace / "reports" / "VERIFY_REPORT.md")
        match = re.search(r"(\d+)\s*(?:pages|页)", verify, re.IGNORECASE)
        return int(match.group(1)) if match else None
    try:
        doc = fitz.open(candidates[0])
        return int(doc.page_count)
    except Exception:
        return None


def conclusion_is_pass(text: str) -> bool:
    return bool(re.search(r"(conclusion|结论)\s*[:：]?\s*\*{0,2}PASS\b", text, re.IGNORECASE))


def normalize_manifest(manifest: Any, issues: list[dict[str, str]], final_workspace: bool) -> dict[str, list[Any]]:
    if isinstance(manifest, dict):
        normalized: dict[str, list[Any]] = {}
        for key in ("metrics", "tables", "figures", "scripts"):
            value = manifest.get(key, [])
            if isinstance(value, list):
                normalized[key] = value
            else:
                normalized[key] = []
                add_issue(
                    issues,
                    "HIGH",
                    f"manifest_{key}_invalid",
                    f"Manifest field `{key}` must be a list.",
                    "results/RESULTS_MANIFEST.json",
                )
        return normalized

    if isinstance(manifest, list):
        add_issue(
            issues,
            "HIGH",
            "manifest_schema_legacy",
            "RESULTS_MANIFEST.json uses the legacy list schema; V2.3 requires an object with metrics, tables, figures, and scripts.",
            "results/RESULTS_MANIFEST.json",
        )
        return {"metrics": manifest, "tables": [], "figures": [], "scripts": []}

    if final_workspace:
        add_issue(
            issues,
            "BLOCKER",
            "manifest_schema_invalid",
            "RESULTS_MANIFEST.json is missing or is not valid JSON.",
            "results/RESULTS_MANIFEST.json",
        )
    return {"metrics": [], "tables": [], "figures": [], "scripts": []}


def audit_workspace(workspace: Path, nature_mode: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    reports = workspace / "reports"
    manifest_raw = load_json(workspace / "results" / "RESULTS_MANIFEST.json")
    plan_text = read_text(reports / "FIGURE_PLAN.md")
    audit_text = read_text(reports / "FIGURE_AUDIT.md")
    verify_text = read_text(reports / "VERIFY_REPORT.md")
    scorecard_text = read_text(reports / "PAPER_SCORECARD.md")
    revision_actions_text = read_text(reports / "REVISION_ACTIONS.md")
    final_workspace = bool((workspace / "paper").is_dir() or verify_text or scorecard_text)

    nature = detect_nature(workspace, nature_mode)
    nature_available = bool(nature.get("available"))
    plan_rows = parse_plan_rows(plan_text)

    manifest = normalize_manifest(manifest_raw, issues, final_workspace)
    figures = manifest["figures"]
    if final_workspace and not figures:
        add_issue(
            issues,
            "HIGH",
            "manifest_figures_missing",
            "Final workspaces must trace paper figures through manifest.figures.",
            "results/RESULTS_MANIFEST.json",
        )

    audit_columns = parse_audit_columns(audit_text)
    missing_audit_columns = [col for col in AUDIT_REQUIRED_COLUMNS if col not in audit_columns]
    if nature_available and final_workspace and missing_audit_columns:
        add_issue(
            issues,
            "HIGH",
            "figure_audit_columns_missing",
            "FIGURE_AUDIT.md lacks required V2.3/Nature audit columns.",
            ", ".join(missing_audit_columns),
        )

    for entry in figures:
        if not isinstance(entry, dict):
            continue
        raw_path = str(entry.get("path", ""))
        if not raw_path:
            add_issue(issues, "HIGH", "figure_path_missing", "Figure entry has no path.", json.dumps(entry, ensure_ascii=False))
            continue
        fig_path = resolve_manifest_path(workspace, raw_path)
        plan_row = find_plan_row(entry, fig_path, plan_rows)
        backend = str(entry.get("backend") or plan_row.get("backend") or "")
        archetype = str(entry.get("archetype") or plan_row.get("archetype") or "")
        is_data = is_data_archetype(archetype)
        bundle = entry.get("export_bundle")
        bundle_paths: list[str] = []
        if isinstance(bundle, list):
            bundle_paths.extend(str(item) for item in bundle)
        elif isinstance(bundle, dict):
            bundle_paths.extend(str(value) for value in bundle.values())
        bundle_paths.extend(sibling_bundle(fig_path))
        bundle_paths = sorted(set(bundle_paths))

        if not fig_path.is_file():
            add_issue(issues, "BLOCKER", "figure_file_missing", "Manifest figure path does not resolve.", raw_path)
            continue

        if "pillow" in backend.lower() and is_data:
            add_issue(
                issues,
                "HIGH",
                "pillow_data_figure",
                "Pillow is not accepted as a Nature data-figure backend.",
                f"{entry.get('id', fig_path.stem)} backend={backend} archetype={archetype}",
            )

        if fig_path.suffix.lower() == ".png" and not bundle_has_vector(bundle_paths):
            add_issue(
                issues,
                "HIGH",
                "png_only_core_figure",
                "Core figure is PNG-only; SVG/PDF vector export is required when feasible.",
                raw_path,
            )

        if nature_available:
            missing_meta = []
            if not (entry.get("source_data") or plan_row.get("source_data")):
                missing_meta.append("source_data")
            if not entry.get("script"):
                missing_meta.append("script")
            if not (entry.get("backend") or plan_row.get("backend")):
                missing_meta.append("backend")
            if not (entry.get("contract_id") or plan_row):
                missing_meta.append("contract_id_or_plan_row")
            if not bundle_has_vector(bundle_paths):
                missing_meta.append("svg_pdf_export")
            if missing_meta:
                add_issue(
                    issues,
                    "HIGH",
                    "manifest_figure_contract_incomplete",
                    "Core figure lacks required V2.3 manifest/contract metadata.",
                    f"{entry.get('id', fig_path.stem)} missing={','.join(missing_meta)}",
                )

    page_count = pdf_page_count(workspace)
    pass_claimed = conclusion_is_pass(verify_text) or conclusion_is_pass(scorecard_text)
    subproblem_count = len(re.findall(r"问题[一二三四五六七八九十0-9]", read_text(workspace / "PROBLEM_BRIEF.md")))
    if subproblem_count < 4:
        subproblem_count = max(subproblem_count, len(re.findall(r"Q[1-9]", plan_text)))

    if page_count is not None and subproblem_count >= 4 and page_count < 8:
        severity = "BLOCKER" if page_count <= 5 else "HIGH"
        add_issue(
            issues,
            severity,
            "paper_too_short_for_formal_contest",
            "Formal multi-question contest paper is too compressed for a high-score submission.",
            f"pages={page_count}, subproblems>={subproblem_count}",
        )

    unresolved_high = []
    for line in revision_actions_text.splitlines():
        if ("| HIGH " in line or "| BLOCKER " in line) and "resolved" not in line.lower():
            unresolved_high.append(line.strip())
    if unresolved_high:
        add_issue(
            issues,
            "BLOCKER",
            "unresolved_high_revision",
            "Unresolved BLOCKER/HIGH revision actions cannot be treated as PASS.",
            " ; ".join(unresolved_high[:3]),
        )

    if pass_claimed and any(severity_rank(issue["severity"]) >= severity_rank("HIGH") for issue in issues):
        add_issue(
            issues,
            "BLOCKER",
            "false_pass_claim",
            "VERIFY_REPORT.md or PAPER_SCORECARD.md claims PASS despite HIGH/BLOCKER audit findings.",
            "reports/VERIFY_REPORT.md; reports/PAPER_SCORECARD.md",
        )

    worst = max((severity_rank(issue["severity"]) for issue in issues), default=0)
    status = "PASS" if worst == 0 else "FAIL"
    return {
        "workspace": str(workspace),
        "status": status,
        "worst_severity": next((name for name, rank in {"BLOCKER": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.items() if rank == worst), "NONE"),
        "nature": nature,
        "summary": {
            "figures": len(figures),
            "metrics": len(manifest["metrics"]),
            "tables": len(manifest["tables"]),
            "scripts": len(manifest["scripts"]),
            "paper_pages": page_count,
            "pass_claimed": pass_claimed,
            "issue_count": len(issues),
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".", help="Contest workspace to audit")
    parser.add_argument("--nature-enabled", choices=["auto", "yes", "no"], default="auto")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    result = audit_workspace(workspace, args.nature_enabled)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
