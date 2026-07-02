# TDD Evidence: MathModel Capability Memory And Trusted RAG

## Source Plan

Derived from the user-provided plan: MathModel experience memory, trusted RAG source quality, executable templates, figure evidence map, and evaluator-optimizer loop.

## User Journeys

- As a model-strategy skill, I want RAG hits to include source quality and allowed use, so core modeling evidence cannot silently rely on weak sources.
- As an experiment skill, I want code-template use to require adaptation evidence, so templates do not pollute real data analysis.
- As a contest workflow, I want failures and review lessons distilled into local memory, so future projects learn from reflection and repair.

## RED Evidence

Command:

```powershell
python -m pytest tests -q
```

Result before implementation:

```text
6 failed, 4 passed
```

Expected failures were:

- missing `memory_log.py`, `memory_brief.py`, `memory_distill.py`;
- missing RAG ledger fields: `source_quality`, `source_type`, `allowed_use`, `quality_reason`;
- missing `rag_query.py --core-only`.

## GREEN Evidence

Commands:

```powershell
python -m py_compile scripts\rag_ingest.py scripts\rag_query.py scripts\memory_log.py scripts\memory_brief.py scripts\memory_distill.py scripts\new_v2_workspace.py skills\_references\scripts\audit_v2_run.py
python -m pytest tests -q
```

Result:

```text
10 passed in 3.56s
```

## Test Specification

| # | What is guaranteed | Test file or command | Type | Result |
| --- | --- | --- | --- | --- |
| 1 | RAG ingest records source quality ledger fields for official problem sources. | `tests/test_rag_source_quality.py::test_ingest_records_source_quality_ledger_fields` | integration | PASS |
| 2 | RAG query returns source quality, allowed use, quality reason, and core evidence flag. | `tests/test_rag_source_quality.py::test_query_returns_source_quality_and_core_evidence_policy` | integration | PASS |
| 3 | `--core-only` filters out non-S/A sources. | `tests/test_rag_source_quality.py::test_query_core_only_filters_out_non_core_sources` | integration | PASS |
| 4 | Experience memory can append structured raw events. | `tests/test_memory_scripts.py::test_memory_log_appends_structured_event` | integration | PASS |
| 5 | Experience briefing filters events and committed summaries by query. | `tests/test_memory_scripts.py::test_memory_brief_filters_events_and_summaries` | integration | PASS |
| 6 | Memory distill extracts reviewer lessons and failed approaches from workspace artifacts. | `tests/test_memory_scripts.py::test_memory_distill_extracts_revision_and_failure_lessons` | integration | PASS |

## Known Gaps

- No coverage percentage command exists for this repository.
- Skill-document behavior is contract-tested by file review and script tests, not by a full contest E2E run.
- `audit_v2_run.py` now has additional hard checks, but no separate unit test file yet.
