# Source Quality Policy

This policy defines how local RAG sources can be used in MathModel V2.

## Quality Levels

| Level | Meaning | Core Evidence |
| --- | --- | --- |
| `S` | Official contest statement, official rule, official attachment, official data source. | allowed |
| `A` | Excellent paper, authoritative textbook, classic paper, trusted institutional data source, curated model card. | allowed |
| `B` | High-quality blog, open-source code, contest experience note, code/figure/writing template. | auxiliary only |
| `C` | Forum discussion, unverified note, personal summary. | risk signal only |
| `D` | Unknown, untraceable, likely wrong, or source-conflicted material. | risk signal only |

## Hard Rules

1. `S/A` may support core modeling facts, route selection, formula choice, and paper claims.
2. `B` may provide implementation structure, checklist hints, examples, or reviewer cues, but cannot be cited as the core reason for a model choice.
3. `C/D` may only trigger caution, further checking, or a revision action. They must not enter core modeling evidence.
4. If a lower-quality source conflicts with the current problem statement or data audit, the current problem statement and data audit win.
5. Any artifact using RAG evidence must keep the source path, source quality, allowed use, and risk note.

## Ledger Fields

`scripts/rag_ingest.py` records these fields in the SQLite ledger:

| Field | Required | Meaning |
| --- | --- | --- |
| `source_quality` | yes | `S/A/B/C/D` source class. |
| `source_type` | yes | e.g. `official_problem`, `excellent_paper`, `model_card`, `code_template`. |
| `verified_by` | yes | human, script, or policy that assigned the level. |
| `last_verified_at` | yes | timestamp or date of source-quality assignment. |
| `allowed_use` | yes | `core_evidence`, `auxiliary_only`, or `risk_signal_only`. |
| `quality_reason` | yes | short reason for the assigned source quality. |

`scripts/rag_query.py` must return:

- `source_quality`
- `source_type`
- `allowed_use`
- `quality_reason`
- `core_evidence_allowed`

Use `python scripts/rag_query.py "<query>" --core-only` when a phase needs only `S/A` evidence.

## Default Library Mapping

| Library | Default Quality | Default Type | Allowed Use |
| --- | --- | --- | --- |
| `cumcm_problems` | `S` | `official_problem` | core evidence |
| `mcm_icm_problems` | `S` | `official_problem` | core evidence |
| `excellent_papers` | `A` | `excellent_paper` | core evidence after fit check |
| `model_methods` | `A` | `model_card` | core evidence after data-fit check |
| `code_templates` | `B` | `code_template` | auxiliary only |
| `figure_templates` | `B` | `figure_template` | auxiliary only |
| `paper_expression` | `B` | `writing_template` | auxiliary only |
| `review_rubrics` | `B` | `review_rubric` | auxiliary only unless official |

Front matter may explicitly set `source_quality`, `source_type`, `verified_by`, `last_verified_at`, and `quality_reason`. It may not relax the hard rule: `B/C/D` sources are never core evidence.

## Phase Requirements

- `mm-problem-intake`: core problem facts should come from the current problem files or `S` official problem sources.
- `mm-model-strategy`: core route evidence must be `S/A`; `B` model examples can only suggest checks or implementation patterns.
- `mm-data-experiment`: `code_templates` hits are `B`; using them requires `reports/TEMPLATE_ADAPTATION_LOG.md`.
- `mm-paper-build`: final paper claims must trace to current results or `S/A` evidence. Expression templates cannot become factual claims.
- `mm-contest-review` and `mm-final-verify`: any core claim relying on `C/D` is at least `HIGH`; if the claim is central, it is `BLOCKER`.
