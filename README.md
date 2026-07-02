# MathModelAgent V2.5

数学建模竞赛全流程自动化 —— Skill + Codex 子代理混合工作流，底层由本地 RAG 知识库提供题型识别、模型路由、模型卡、代码模板、图表证据、论文表达和评审反馈能力。

**Workflow**: V2.5 (8 skills + capability layer + shared references + tools)
**Archived**: V1 pipeline → `archive/v1/`
**Version**: 2.5

---

## Capability Layer（比赛能力底座）

V2.5 新增本地 RAG 知识库层，为每个 V2 阶段提供可检索、可引用、可评测的领域知识：

```
知识库层（8 库，ChromaDB + SQLite）
  │
  ├── 历年国赛题库     → mm-problem-intake
  ├── 历年美赛题库     → mm-problem-intake
  ├── 优秀论文库       → mm-paper-build, mm-contest-review
  ├── 常规模型库       → mm-model-strategy
  ├── 代码模板库       → mm-data-experiment
  ├── 图表模板库       → mm-data-experiment
  ├── 论文表达模板库   → mm-paper-build
  └── 评分评审库       → mm-contest-review, mm-final-verify
```

**RAG 引用规则**：RAG 不直接回答最终结论，必须返回命中文档、来源路径、可信度、适用阶段、推荐用法和禁用/风险提示。详见 `skills/_references/rag_usage_contract.md`。

**技术默认**：
- 向量库：ChromaDB persistent local store
- 元数据账本：SQLite（source, license, year, contest, problem_id, chunk_id, hash, tags）
- Embedding：BAAI/bge-m3（降级备选 bge-small-zh-v1.5）
- 检索：BM25 + dense hybrid（rerank 接口预留）

### 能力路由与审查

| 能力文件 | 用途 | 调用阶段 |
|----------|------|----------|
| `problem_type_router.md` | 输入题面 → 输出主/子题型、首选模型、基准模型、备选模型、不推荐模型、验证方法、推荐图表 | `mm-problem-intake`, `mm-model-strategy` |
| `model_method_cards.md` | 每张卡包含场景、数据要求、核心公式、baseline、advanced model、验证指标、常见扣分点、图表建议、代码模板入口 | `mm-model-strategy` |
| `anti_template_review.md` | 检查 AHP/TOPSIS/神经网络/遗传算法/PCA/聚类是否被滥用 | `mm-model-strategy`, `mm-contest-review` |
| `judge_skim_review_protocol.md` | 模拟评委 5 分钟快审摘要、目录、关键图、创新点、结论 | `mm-contest-review` |
| `rag_usage_contract.md` | RAG 引用契约：source citation、可信度、阶段用法、风险提示 | 全阶段 |

---

## Control Center（本地全栈管理台）

`app/` 提供了 Manual-first、harness-agnostic 的本地管控台：

- **Backend**: FastAPI
- **Frontend**: Vue 3 + Vite
- **Harness targets**: Manual / Codex / Claude Code / OpenCode
- **Safe default**: Managed 执行使用工作区副本，不直接修改原始工作区

```powershell
cd app
.\start.bat
```

打开 `http://127.0.0.1:5173`。入门指南见 `docs/control-center-beginner-guide.md`。

---

## Capability Updates

- `skills/_references/source_quality_policy.md`: S/A/B/C/D source quality and core-evidence rules.
- `skills/_references/figure_evidence_map.md`: claim -> figure -> data -> metric -> caption evidence map.
- `skills/_references/executable_model_templates.md`: executable model templates for route-to-code handoff.
- `skills/_references/evaluator_optimizer_protocol.md`: file-state refinement loop and `reports/REFINEMENT_LOG.md`.
- `scripts/memory_log.py`, `scripts/memory_brief.py`, `scripts/memory_distill.py`: local experience-memory capture, briefing, and distillation.

## Architecture

```
mm-start-contest-v2 (Orchestrator)
  │
  ├─ Phase 0: mm-problem-intake ────── problem-analyst + data-auditor (+ RAG 题库)
  │     Gate: INTAKE_GATE.md
  │
  ├─ Phase 1: mm-model-strategy ────── model-reviewer + devils-advocate (+ RAG 路由器/模型卡/反模板)
  │     Gate: HUMAN_MODEL_REVIEW.md (mandatory human confirmation)
  │
  ├─ Phase 2: mm-data-experiment ───── experiment-coder + visualization-reviewer (+ RAG 代码/图表模板)
  │     Gate: RESULTS_MANIFEST.json, FIGURE_AUDIT.md
  │
  ├─ Phase 3: mm-paper-build ───────── paper-writer + claim-trace (+ RAG 优秀论文/表达模板)
  │     Gate: CLAIM_TRACE.md, METHOD_IMPLEMENTATION_MATRIX.md
  │
  ├─ Phase 4: mm-contest-review ────── contest-reviewer + multi-panel (+ RAG 评审库/judge-skim)
  │     Gate: PAPER_SCORECARD.md (all dimensions >= 4)
  │
  ├─ Phase 5: mm-revision-integrator ─ revision loop (BLOCKER/HIGH/MEDIUM/LOW)
  │     Gate: REVISION_STATUS.md (no unresolved BLOCKER/HIGH)
  │
  └─ Phase 6: mm-final-verify ──────── final-integrator (+ optional ARS integrity)
        Gate: VERIFY_REPORT.md = PASS
```

V1 legacy pipeline archived at `archive/v1/`.

---

## File Structure

```
├── mathmodelagent.skills.sh.json    # Skills manifest (V2 + tools + _references)
├── CLAUDE.md                        # Project-level AI config
├── FILE_RELATIONSHIP_MAP.md         # Complete dependency graph
├── AGENTS.md                        # Agent orchestration config
│
├── knowledge/                       # ★ V2.5: 本地 RAG 知识库索引与样例
│   ├── README.md                    # Knowledge base overview & schema
│   ├── libraries.json               # 8-library configuration
│   ├── samples/                     # Structured samples per library
│   │   ├── cumcm_problems/          # 国赛题库样例
│   │   ├── mcm_icm_problems/        # 美赛题库样例
│   │   ├── high_score_papers/       # 高分论文结构样例
│   │   ├── model_methods/           # 模型方法卡样例
│   │   ├── code_templates/          # 代码模板样例
│   │   ├── figure_templates/        # 图表模板样例
│   │   ├── paper_expression/        # 论文表达样例
│   │   └── review_rubrics/          # 评分评审样例
│   └── source_notes/                # Import source documentation
│
├── skills/
│   ├── _references/                 # Shared knowledge base + capability layer
│   │   ├── v2_pipeline_contract.md          # V2 stage gates & completion criteria
│   │   ├── codex_subagent_protocol.md       # Subagent roles, parallelism, logging
│   │   ├── workflow_state_contract.md       # Persistence context & gates
│   │   ├── contest_score_rubric.md          # 10-dimension, 0-5 scoring
│   │   ├── paper_benchmark_profile.md       # Weak-vs-high-score gap profile
│   │   ├── figure_quality_standard.md       # Figure quality & audit
│   │   ├── agent_review_protocol.md         # Unified review format
│   │   ├── model_method_cards.md            # ★ Expanded: 8 model families with full cards
│   │   ├── problem_type_router.md           # ★ New: problem-type → model mapping
│   │   ├── anti_template_review.md          # ★ New: anti-template abuse checker
│   │   ├── judge_skim_review_protocol.md    # ★ New: 5-minute judge skim review
│   │   ├── rag_usage_contract.md            # ★ New: RAG citation & trust rules
│   │   ├── ars_v2_integration_guide.md      # Optional ARS integration
│   │   ├── nature_figure_integration_guide.md  # Optional Nature Figure integration
│   │   ├── agent_profiles/          # 10 reusable agent role prompts
│   │   └── scripts/
│   │       ├── audit_v2_run.py      # V2 read-only final audit
│   │       └── resolve_nature_figure.py  # Nature Figure check
│   │
│   ├── mm-start-contest-v2/         # V2: Orchestrator entry
│   ├── mm-problem-intake/           # V2: Phase 0 — Problem & data intake
│   ├── mm-model-strategy/           # V2: Phase 1 — Modeling strategy
│   ├── mm-data-experiment/          # V2: Phase 2 — Experiment & visualization
│   ├── mm-paper-build/              # V2: Phase 3 — Paper construction
│   ├── mm-contest-review/           # V2: Phase 4 — High-score review
│   ├── mm-revision-integrator/      # V2: Phase 5 — Revision loop
│   ├── mm-final-verify/             # V2: Phase 6 — Final acceptance
│   │
│   ├── 5writing/templates/          # 34 contest templates (Typst + LaTeX)
│   └── doctor/                      # Environment check & dependency install
│
├── scripts/
│   ├── rag_ingest.py                # ★ New: Ingest sources into 8 RAG libraries
│   ├── rag_query.py                 # ★ New: Query RAG with source-grounded hits
│   ├── import_zhanwen_mathmodel.py  # Import reference material
│   ├── audit_benchmark.py           # Batch audit examples → PASS/FAIL table
│   └── new_v2_workspace.py          # Create a V2 workspace skeleton
│
├── tests/
│   └── test_rag_scripts.py          # RAG script tests
│
├── app/                             # Control Center (FastAPI + Vue 3/Vite)
│   ├── backend/
│   ├── frontend/
│   └── start.bat
│
├── docs/
│   ├── control-center-beginner-guide.md
│   └── control-center-ui-spec.md
│
├── examples/                        # Example contest workspaces
├── workspaces/                      # Active contest workspaces
└── archive/v1/                      # Archived V1 pipeline
```

---

## V2 Workspace Artifacts

```
<workspace>/
├── plan.md                          # Contest type, engine, language
├── todo.md                          # Phase checklist
├── WORKFLOW_STATE.md                # Current stage, completed, risks
├── PROBLEM_BRIEF.md                 # Structured problem restatement
├── DATA_AUDIT.md                    # Data fields, units, quality risks
├── reports/
│   ├── INTAKE_GATE.md               # Phase 0 gate
│   ├── MODEL_CANDIDATES.md          # Candidate modeling routes
│   ├── MODEL_REVIEW_AI.md           # AI model review
│   ├── HUMAN_MODEL_REVIEW.md        # ★ Human confirmation (MANDATORY)
│   ├── MODELING_DECISION.md         # Final adopted route
│   ├── ANALYSIS_MODELING_REPORT.md  # Full formulas, algorithms
│   ├── ANALYSIS_GATE.md             # Phase 1 gate
│   ├── FIGURE_PLAN.md               # Figure purpose, captions
│   ├── EXPERIMENT_LOG.md            # Code execution log
│   ├── RESULTS_REPORT.md            # Result narrative
│   ├── FIGURE_AUDIT.md              # Figure quality audit
│   ├── CLAIM_TRACE.md               # Conclusion → evidence mapping
│   ├── METHOD_IMPLEMENTATION_MATRIX.md  # Route → code → paper alignment
│   ├── PAPER_BUILD_REPORT.md        # Paper construction summary
│   ├── PAPER_SCORECARD.md           # 10-dimension scores
│   ├── REVISION_ACTIONS.md          # Action items
│   ├── REVISION_STATUS.md           # Revision tracking
│   └── VERIFY_REPORT.md             # Final acceptance
├── results/RESULTS_MANIFEST.json    # All citable metrics, figures
├── code/                            # Source code
├── figures/                         # Generated figures (PDF/SVG)
└── paper/                           # LaTeX or Typst paper
```

---

## Subagent Roles (10)

| Agent | Purpose | Permissions | Reasoning |
|-------|---------|-------------|-----------|
| `problem-analyst` | Parse problem, questions, objectives | read-only | medium |
| `data-auditor` | Inspect data files, fields, quality | read-only | medium |
| `model-strategist` | Create candidate modeling routes | write reports/ | high |
| `model-reviewer` | Review model fit, rigor, clarity | read-only | high |
| `devils-advocate` | Find objections, weak assumptions | read-only | high |
| `experiment-coder` | Implement scripts, run experiments | write code/results/figures | high |
| `visualization-reviewer` | Review figure adequacy | read-only | medium |
| `paper-writer` | Draft/revise paper sections | write paper/ + reports | high |
| `contest-reviewer` | Score against contest rubric | read-only | high |
| `final-integrator` | Integrate revisions, verify consistency | write paper/ + reports | high |

Profiles at `skills/_references/agent_profiles/`. Custom agent names use `mathmodel-*` prefix.

---

## Gates & Completion Criteria

Each gate outputs `PASS | CONDITIONAL_PASS | FAIL`.

**Project is complete** only when `VERIFY_REPORT.md = PASS` and ALL of:

1. All contest score dimensions >= 4 (or justified N/A)
2. No unresolved `BLOCKER` or `HIGH` items in `REVISION_ACTIONS.md`
3. `FIGURE_AUDIT.md` has no FAIL status for inserted paper figures
4. `METHOD_IMPLEMENTATION_MATRIX.md` has no `not_implemented` core methods
5. `CLAIM_TRACE.md` has no `missing` core claims, no weak claims stated as strong
6. Paper compiles cleanly and PDF opens without blank pages

---

## Contest Score Rubric (10 Dimensions, 0-5)

| Dimension | Description |
|-----------|-------------|
| Problem understanding | Questions, constraints, evaluation criteria |
| Data understanding | Files, fields, units, missing values |
| Modeling fit | Method matches data and question type |
| Mathematical rigor | Variables, formulas, objectives, constraints |
| Implementation | Reproducible code, aligned with modeling |
| Result validity | Error analysis, sensitivity, robustness |
| Visualization | Figures support reasoning, inserted in paper |
| Writing structure | Complete contest paper structure |
| Claim traceability | Claims map to results, figures, decisions |
| Submission readiness | No placeholders, compiles cleanly |

**Rating**: 5=strong high-score, 4=acceptable, 3=visibly weak, 2=significant loss, 1=mostly missing, 0=absent

---

## Templates (34 variants, 17 contest types)

**Chinese (zh/):** CUMCM, ChangSanJiao, HuaShuBei, HuaweiBei, HuaZhongBei, MathorCup, APMCM, ShuWeiBei, WuYiBei, DianGongBei, DongSanSheng, Stats, MCM, Default

**English (en/):** MCM/ICM, APMCM, Default

Each contest has **both** Typst and LaTeX templates under `skills/5writing/templates/`.

---

## Optional Integrations

### ARS (Academic Research Suite)

[Academic Research Suite](https://github.com/Imbad0202/academic-research-skills) provides deeper audits. Set `ARS_ROOT` to enable. Advisory-only — never a hard dependency.

### Nature Figure

[Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) enhances scientific plotting. Set `NATURE_SKILLS_ROOT` env var.

---

## Scripts

```bash
# RAG knowledge ingestion & query (V2.5)
python scripts/rag_ingest.py --source <dir> --library <library_name>
python scripts/rag_query.py --query "<query>" --libraries <names>

# Create a new V2 workspace
python scripts/new_v2_workspace.py workspace/my-contest --contest CUMCM --engine LaTeX --language 中文

# Audit a contest run
python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>

# Batch audit benchmark examples
python scripts/audit_benchmark.py --root examples/2022C
```

---

## Installation

```bash
git clone https://github.com/zklzzklzkl/MathModel.git MathModelAgent
cd MathModelAgent

# RAG dependencies
pip install chromadb sentence-transformers

# Copy skills to Claude Code skills directory
cp -r skills/* ~/.claude/skills/
```

---

## Usage

```
/mm-start-contest-v2    Start V2 workflow
/doctor                 Check environment & install dependencies
```

V1 is archived (`archive/v1/`). Do not use for new contests.

---

## License

CC-BY-NC 4.0
