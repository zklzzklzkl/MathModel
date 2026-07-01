#!/usr/bin/env python
"""Query the local MathModel RAG ledger with source-grounded results.

This is a retrieval primitive, not a chatbot. It returns local evidence chunks
with source paths, confidence, stage fit, recommended use, and risk warnings.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from rag_ingest import DEFAULT_CONFIG, DEFAULT_DB, load_libraries


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query local MathModel RAG libraries.")
    parser.add_argument("query", help="Search query or task description.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--library", action="append", help="Restrict to one or more library ids.")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--min-score", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--show-text", action="store_true", help="Include longer chunk text in Markdown output.")
    return parser.parse_args()


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(
            f"RAG ledger not found: {db_path}\n"
            "Run: python scripts\\rag_ingest.py --source knowledge\\samples"
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def cjk_ngrams(text: str) -> list[str]:
    terms: list[str] = []
    for run in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        if len(run) <= 8:
            terms.append(run)
        for size in (2, 3, 4):
            for index in range(0, max(0, len(run) - size + 1)):
                terms.append(run[index : index + size])
    return terms


def tokenize(query: str) -> list[str]:
    terms: list[str] = []
    for token in re.findall(r"[A-Za-z0-9_+#.-]+", query.lower()):
        if len(token) >= 2:
            terms.append(token)
    terms.extend(cjk_ngrams(query))
    deduped: list[str] = []
    for term in terms:
        if term and term not in deduped:
            deduped.append(term)
    return deduped


def count_occurrences(haystack: str, needle: str) -> int:
    if not needle:
        return 0
    return haystack.count(needle)


def lexical_score(row: sqlite3.Row, terms: list[str]) -> float:
    title = (row["title"] or "").lower()
    text = (row["text"] or "").lower()
    tags = " ".join(json.loads(row["tags_json"] or "[]")).lower()
    score = 0.0
    for term in terms:
        term_lower = term.lower()
        title_hits = count_occurrences(title, term_lower)
        tag_hits = count_occurrences(tags, term_lower)
        text_hits = count_occurrences(text, term_lower)
        score += min(title_hits, 3) * 4.0
        score += min(tag_hits, 3) * 3.0
        score += min(text_hits, 8) * 1.0
    # Short, precise chunks are usually better context than massive pasted PDFs.
    length = max(len(text), 1)
    score *= 1.0 + min(0.3, 400.0 / length)
    return score


def confidence(score: float, best_score: float) -> str:
    if score <= 0:
        return "none"
    relative = score / best_score if best_score else 0
    if relative >= 0.78 and score >= 8:
        return "high"
    if relative >= 0.45 and score >= 4:
        return "medium"
    return "low"


def normalized_score(score: float, best_score: float) -> float:
    if best_score <= 0:
        return 0.0
    return round(min(1.0, score / best_score), 3)


def snippet(text: str, terms: list[str], max_chars: int = 260) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_chars:
        return clean
    lower = clean.lower()
    first_hit = None
    for term in terms:
        index = lower.find(term.lower())
        if index >= 0 and (first_hit is None or index < first_hit):
            first_hit = index
    if first_hit is None:
        return clean[:max_chars].rstrip() + "..."
    start = max(0, first_hit - 80)
    end = min(len(clean), start + max_chars)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(clean) else ""
    return prefix + clean[start:end].strip() + suffix


def fetch_rows(conn: sqlite3.Connection, libraries: list[str] | None) -> list[sqlite3.Row]:
    if libraries:
        placeholders = ", ".join("?" for _ in libraries)
        return conn.execute(f"SELECT * FROM chunks WHERE library_id IN ({placeholders})", libraries).fetchall()
    return conn.execute("SELECT * FROM chunks").fetchall()


def query_ledger(db_path: Path, query: str, libraries: list[str] | None, limit: int, min_score: float) -> dict[str, Any]:
    conn = connect(db_path)
    terms = tokenize(query)
    rows = fetch_rows(conn, libraries)
    scored: list[tuple[float, sqlite3.Row]] = []
    for row in rows:
        score = lexical_score(row, terms)
        if score >= min_score:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    best = scored[0][0] if scored else 0.0
    hits = []
    for score, row in scored[:limit]:
        tags = json.loads(row["tags_json"] or "[]")
        hits.append(
            {
                "chunk_id": row["chunk_id"],
                "library_id": row["library_id"],
                "source_path": row["source_path"],
                "source_relpath": row["source_relpath"],
                "title": row["title"],
                "score": normalized_score(score, best),
                "raw_score": round(score, 3),
                "confidence": confidence(score, best),
                "stage": row["stage"],
                "license": row["license"],
                "year": row["year"],
                "contest": row["contest"],
                "problem_id": row["problem_id"],
                "tags": tags,
                "recommended_use": row["recommended_use"],
                "risk_warning": row["risk_warning"],
                "snippet": snippet(row["text"], terms),
                "text": row["text"],
            }
        )
    return {
        "query": query,
        "terms": terms,
        "libraries": libraries or "all",
        "hit_count": len(hits),
        "hits": hits,
    }


def markdown_result(result: dict[str, Any], config_path: Path, show_text: bool) -> str:
    libraries = load_libraries(config_path)
    lines = [f"# RAG Query Result", "", f"Query: `{result['query']}`", ""]
    if not result["hits"]:
        lines.extend(
            [
                "No sourced hits were found.",
                "",
                "Run ingestion first or add more local documents. Do not answer from RAG without sources.",
            ]
        )
        return "\n".join(lines)
    for index, hit in enumerate(result["hits"], start=1):
        library = libraries.get(hit["library_id"])
        library_name = library.name if library else hit["library_id"]
        lines.extend(
            [
                f"## {index}. {hit['title']}",
                "",
                f"- Library: `{hit['library_id']}` ({library_name})",
                f"- Source: `{hit['source_relpath']}`",
                f"- Confidence: `{hit['confidence']}` (score {hit['score']})",
                f"- Stage: `{hit['stage']}`",
                f"- Tags: {', '.join(hit['tags']) if hit['tags'] else 'none'}",
                f"- Recommended use: {hit['recommended_use']}",
                f"- Risk: {hit['risk_warning']}",
                "",
                hit["text"] if show_text else hit["snippet"],
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def main() -> None:
    configure_stdout()
    args = parse_args()
    result = query_ledger(
        db_path=args.db,
        query=args.query,
        libraries=args.library,
        limit=args.limit,
        min_score=args.min_score,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(markdown_result(result, args.config, args.show_text))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
