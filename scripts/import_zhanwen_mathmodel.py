#!/usr/bin/env python
"""Curate a local zhanwen/MathModel checkout into the MathModel RAG raw area.

This script copies useful source files from a downloaded `zhanwen/MathModel`
folder into `knowledge/raw/zhanwen_mathmodel/<library_id>/...`.

It never modifies the source folder. The copied raw materials are intentionally
ignored by Git; only this script and the generated source note are meant to be
committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(r"C:\Users\zklzk\Downloads\Compressed\MathModel-master\MathModel-master")
DEFAULT_DEST = REPO_ROOT / "knowledge" / "raw" / "zhanwen_mathmodel"
DEFAULT_REPORT = REPO_ROOT / "knowledge" / "source_notes" / "zhanwen_mathmodel_import.md"

SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".tex",
    ".cls",
    ".m",
    ".csv",
}

SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
SKIP_EXTENSIONS = {
    ".aux",
    ".log",
    ".out",
    ".toc",
    ".synctex.gz",
    ".zip",
    ".rar",
    ".gz",
    ".ttf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".exe",
}

MODEL_TOP_LEVELS = {
    "数学建模算法",
    "现代算法",
    "数学建模基础篇",
    "数学建模技巧篇",
    "教材及课件",
    "本科生数学建模",
}

REVIEW_TOP_LEVEL_FILES = {
    "README.md",
    "比赛心得.md",
    "选题、命题介绍分析.md",
    "数学建模竞赛网上资源.md",
}

MODEL_TOP_LEVEL_FILES = {
    "数学建模应掌握的十类算法.md",
}


@dataclass
class Candidate:
    source_path: Path
    relpath: str
    library_id: str
    reason: str
    year: int | None
    is_paper_pdf: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import zhanwen/MathModel materials into local RAG raw area.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--paper-pdf-limit", type=int, default=120, help="Curated limit for excellent-paper PDFs.")
    parser.add_argument("--full-papers", action="store_true", help="Copy all paper PDFs instead of applying the limit.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite existing copied files.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def extract_year(text: str) -> int | None:
    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def sanitize_component(value: str, max_len: int = 80) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    value = re.sub(r"\s+", " ", value).strip().strip(".")
    if not value:
        value = "item"
    return value[:max_len]


def relpath_for(source_root: Path, path: Path) -> str:
    return path.resolve().relative_to(source_root.resolve()).as_posix()


def first_part(relpath: str) -> str:
    return relpath.split("/", 1)[0]


def infer_library(relpath: str, path: Path) -> tuple[str | None, str]:
    top = first_part(relpath)
    name = path.name
    suffix = path.suffix.lower()

    if name in MODEL_TOP_LEVEL_FILES:
        return "model_methods", "top-level model-method note"
    if name in REVIEW_TOP_LEVEL_FILES:
        return "review_rubrics", "top-level contest/review note"

    if suffix in {".tex", ".cls"}:
        return "paper_expression", "latex template source"
    if suffix == ".m" or "Matlab" in relpath or "MATLAB" in relpath:
        return "code_templates", "matlab/code template source"

    if "国赛试题" in relpath or "数学建模相关文件" in relpath:
        return "cumcm_problems", "contest problem statement or attachment"
    if "美赛" in relpath and ("题" in relpath or "Problem" in relpath):
        return "mcm_icm_problems", "mcm/icm problem or result source"

    if "国赛论文" in relpath or "美赛论文" in relpath:
        return "excellent_papers", "excellent contest paper"

    if top in MODEL_TOP_LEVELS:
        return "model_methods", "model-method textbook or courseware"

    if "论文模版" in relpath or "论文模板" in relpath or "Latex模版" in relpath or "LaTex" in relpath:
        return "paper_expression", "paper template or submission instruction"

    if "最终获奖名单" in relpath:
        return "review_rubrics", "award-list scoring context"

    if "Mind" in relpath:
        return "figure_templates", "mind-map visual structure"

    return None, "not selected by curation rules"


def is_supported_file(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return False
    suffix = path.suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return False
    if path.name.lower().endswith(".synctex.gz"):
        return False
    return suffix in SUPPORTED_EXTENSIONS


def collect_candidates(source_root: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    for path in source_root.rglob("*"):
        if not path.is_file() or not is_supported_file(path):
            continue
        relpath = relpath_for(source_root, path)
        library_id, reason = infer_library(relpath, path)
        if not library_id:
            continue
        candidates.append(
            Candidate(
                source_path=path,
                relpath=relpath,
                library_id=library_id,
                reason=reason,
                year=extract_year(relpath),
                is_paper_pdf=library_id == "excellent_papers" and path.suffix.lower() == ".pdf",
            )
        )
    return candidates


def paper_priority(candidate: Candidate) -> tuple[int, int, str]:
    text = candidate.relpath
    year = candidate.year or 0
    score = 0
    for keyword in ("优秀", "Outstanding", "Finalist", "Meritorious", "一等奖", "特等奖", "O奖"):
        if keyword.lower() in text.lower():
            score += 10
    if "其他奖项" in text:
        score -= 2
    return (year, score, text)


def apply_paper_limit(candidates: list[Candidate], full_papers: bool, paper_pdf_limit: int) -> list[Candidate]:
    if full_papers:
        return candidates
    paper_pdfs = [candidate for candidate in candidates if candidate.is_paper_pdf]
    selected_ids = {id(candidate) for candidate in candidates if not candidate.is_paper_pdf}
    for candidate in sorted(paper_pdfs, key=paper_priority, reverse=True)[:paper_pdf_limit]:
        selected_ids.add(id(candidate))
    return [candidate for candidate in candidates if id(candidate) in selected_ids]


def destination_for(dest_root: Path, candidate: Candidate) -> Path:
    top = sanitize_component(first_part(candidate.relpath), 36)
    year = str(candidate.year or "undated")
    stem = sanitize_component(candidate.source_path.stem, 88)
    suffix = candidate.source_path.suffix
    prefix = stable_hash(candidate.relpath)
    filename = f"{year}_{prefix}_{stem}{suffix}"
    return dest_root / candidate.library_id / top / filename


def copy_candidates(candidates: Iterable[Candidate], dest_root: Path, force: bool, dry_run: bool) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for candidate in candidates:
        dest = destination_for(dest_root, candidate)
        status = "planned"
        digest = ""
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and not force:
                status = "exists"
            else:
                shutil.copy2(candidate.source_path, dest)
                status = "copied"
            digest = sha256_file(dest)
        manifest.append(
            {
                "library_id": candidate.library_id,
                "reason": candidate.reason,
                "source_path": str(candidate.source_path),
                "source_relpath": candidate.relpath,
                "dest_path": str(dest),
                "dest_relpath": dest.relative_to(REPO_ROOT).as_posix() if dest.is_absolute() else str(dest),
                "size_bytes": candidate.source_path.stat().st_size,
                "year": candidate.year,
                "sha256": digest,
                "status": status,
            }
        )
    return manifest


def write_manifest(dest_root: Path, manifest: list[dict[str, object]], dry_run: bool) -> Path | None:
    if dry_run:
        return None
    path = dest_root / "zhanwen_mathmodel_manifest.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for item in manifest:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    return path


def write_report(report_path: Path, source: Path, dest: Path, manifest: list[dict[str, object]], manifest_path: Path | None, dry_run: bool) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    by_library = Counter(str(item["library_id"]) for item in manifest)
    bytes_by_library: dict[str, int] = defaultdict(int)
    for item in manifest:
        bytes_by_library[str(item["library_id"])] += int(item["size_bytes"])
    lines = [
        "# zhanwen/MathModel Local Import",
        "",
        f"Generated at: `{utc_now()}`",
        f"Source: `{source}`",
        f"Destination: `{dest}`",
        f"Mode: `{'dry-run' if dry_run else 'copied'}`",
        "",
        "## Why Raw Files Are Local Only",
        "",
        "The downloaded repository does not include an explicit LICENSE/COPYING file in the inspected local copy. Raw PDFs, papers, templates, and attachments are therefore kept under `knowledge/raw/`, which is ignored by Git. Commit this note, the import script, and local RAG configuration; do not commit the copied third-party raw files unless licensing is later confirmed.",
        "",
        "## Imported Counts",
        "",
        "| Library | Files | MB |",
        "| --- | ---: | ---: |",
    ]
    for library_id, count in sorted(by_library.items()):
        mb = bytes_by_library[library_id] / 1024 / 1024
        lines.append(f"| `{library_id}` | {count} | {mb:.2f} |")
    lines.extend(
        [
            "",
            "## Local Manifest",
            "",
            f"- Manifest: `{manifest_path}`" if manifest_path else "- Manifest: not written in dry-run mode.",
            "",
            "## Next Commands",
            "",
            "```powershell",
            "python scripts\\rag_ingest.py --source knowledge\\raw\\zhanwen_mathmodel --vector-store none",
            "python scripts\\rag_query.py \"综合评价 TOPSIS 权重 稳定性\" --library model_methods",
            "python scripts\\rag_query.py \"评委 快审 摘要 关键图 结论\" --library review_rubrics",
            "```",
            "",
            "For full excellent-paper import, rerun:",
            "",
            "```powershell",
            f"python scripts\\import_zhanwen_mathmodel.py --source \"{source}\" --full-papers",
            "```",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_stdout()
    args = parse_args()
    source = args.source.resolve()
    if not source.exists():
        raise SystemExit(f"Source does not exist: {source}")
    candidates = collect_candidates(source)
    selected = apply_paper_limit(candidates, args.full_papers, args.paper_pdf_limit)
    manifest = copy_candidates(selected, args.dest.resolve(), args.force, args.dry_run)
    manifest_path = write_manifest(args.dest.resolve(), manifest, args.dry_run)
    write_report(args.report.resolve(), source, args.dest.resolve(), manifest, manifest_path, args.dry_run)
    summary = {
        "source": str(source),
        "dest": str(args.dest.resolve()),
        "candidates_seen": len(candidates),
        "files_selected": len(selected),
        "files_copied_or_existing": len(manifest),
        "paper_pdf_limit": "full" if args.full_papers else args.paper_pdf_limit,
        "report": str(args.report.resolve()),
        "manifest": str(manifest_path) if manifest_path else None,
        "by_library": Counter(str(item["library_id"]) for item in manifest),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=dict))
    else:
        print(f"Selected {len(selected)} files from {len(candidates)} candidates.")
        print(f"Destination: {args.dest.resolve()}")
        print(f"Report: {args.report.resolve()}")
        if manifest_path:
            print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
