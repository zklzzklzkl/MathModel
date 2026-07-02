# MathModelAgent V2.6

面向全国大学生数学建模竞赛、MCM/ICM 等建模赛事的 AI Agent 工作流系统。

MathModelAgent 不是一个传统软件项目，而是一套以 **Skill 工作流、Codex/Claude Code 子代理、本地 RAG 能力层、证据追踪、论文评审门禁** 为核心的数学建模竞赛生产线。目标不是让 AI 直接“写一篇看起来像论文的文本”，而是把赛题理解、模型选择、代码实验、图表生成、论文写作、评审修订和最终验收拆成可审计、可复盘、可人工把关的阶段。

```text
Current Workflow: V2.6
Active Pipeline: 1 orchestrator + 7 phase skills
Archived Pipeline: V1, preserved under archive/v1/
Core Principle: workspace files are the shared memory, chat history is not the state source
LangGraph Runtime: contest_graph_v3 (safe closed-loop: Human Gate → Phase 2 sandbox → Phase 3 paper → Phase 4 review → Phase 5 revision → Phase 6 audit-only) + Benchmark Arena
```

---

## What V2.6 Adds

V2.6 的重点是把原有 V2 高分论文流水线扩展成“能力层 + 管控台 + 证据闭环”的系统：

1. **本地 RAG 能力底座**  
   通过 8 个本地知识库为题型识别、模型路由、模型卡、代码模板、图表模板、论文表达和评审反馈提供检索支持。

2. **证据驱动的论文生成**  
   论文中的核心结论必须能回溯到模型决策、代码结果、图表或结果清单，避免“模型写得高级，证据支撑不足”的竞赛硬伤。

3. **V2 阶段门禁**  
   每个阶段输出结构化工作文件和 gate 文件，状态只能在满足条件后推进。

4. **本地 Control Center**  
   `app/` 提供 FastAPI + Vue 3 的本地管理台，默认 Manual-first，不直接越权操控外部 harness。

5. **评委视角审查**  
   引入反模板审查、5 分钟评委快审、图表证据图谱、来源质量分级和修订闭环。

---

## System Overview

```text
MathModelAgent V2.6
│
├── Skill Pipeline
│   ├── mm-start-contest-v2       # Orchestrator
│   ├── mm-problem-intake         # Phase 0: problem and data intake
│   ├── mm-model-strategy         # Phase 1: model strategy and human gate
│   ├── mm-data-experiment        # Phase 2: coding, results, visualization
│   ├── mm-paper-build            # Phase 3: paper construction and claim trace
│   ├── mm-contest-review         # Phase 4: contest-style review
│   ├── mm-revision-integrator    # Phase 5: revision loop
│   └── mm-final-verify           # Phase 6: final acceptance
│
├── Capability Layer
│   ├── local RAG knowledge base
│   ├── model method cards
│   ├── problem type router
│   ├── anti-template review
│   ├── judge skim review
│   ├── figure evidence map
│   └── source quality policy
│
├── Evidence Layer
│   ├── RESULTS_MANIFEST.json
│   ├── CLAIM_TRACE.md
│   ├── METHOD_IMPLEMENTATION_MATRIX.md
│   ├── FIGURE_AUDIT.md
│   └── PAPER_SCORECARD.md
│
└── Control Center
    ├── FastAPI backend
    ├── Vue 3 + Vite frontend
    └── Manual / Codex / Claude Code / OpenCode prompt preparation
```

---

## Core Design Principles

### 1. File-based state management

Contest state lives in the workspace, not in chat history.

Skills and subagents communicate through durable files such as `PROBLEM_BRIEF.md`, `MODELING_DECISION.md`, `RESULTS_MANIFEST.json`, `CLAIM_TRACE.md`, and `VERIFY_REPORT.md`.

This makes the workflow easier to resume, audit, debug and compare across contest runs.

### 2. Human-confirmed modeling route

AI may propose and review candidate routes, but the final modeling route must pass the human confirmation gate before coding begins.

This is intentional. In mathematical modeling contests, a wrong early modeling route can make every later artifact beautifully wrong.

### 3. Evidence before writing

The paper stage should not invent results. It reads from code outputs, figures, result manifests and claim trace files.

A claim without evidence is either weakened, rewritten or blocked by review.

### 4. Review is not decoration

The system contains independent review roles: model reviewer, devil's advocate, visualization reviewer, contest reviewer and final integrator.

They are used to catch weak assumptions, template abuse, unsupported claims, poor figures, missing validation and submission risks.

---

## V2.6 Workflow

```text
Bootstrap: mm-start-contest-v2
  │
  ├─ Phase 0: mm-problem-intake
  │    Agents: problem-analyst, data-auditor
  │    Outputs: PROBLEM_BRIEF.md, DATA_AUDIT.md, reports/INTAKE_GATE.md
  │
  ├─ Phase 1: mm-model-strategy
  │    Agents: model-strategist, model-reviewer, devils-advocate
  │    Outputs: MODEL_CANDIDATES.md, MODEL_REVIEW_AI.md,
  │             HUMAN_MODEL_REVIEW.md, MODELING_DECISION.md,
  │             ANALYSIS_MODELING_REPORT.md, ANALYSIS_GATE.md,
  │             FIGURE_PLAN.md
  │
  ├─ Phase 2: mm-data-experiment
  │    Agents: experiment-coder, visualization-reviewer
  │    Outputs: code/, figures/, results/RESULTS_MANIFEST.json,
  │             EXPERIMENT_LOG.md, RESULTS_REPORT.md, FIGURE_AUDIT.md
  │
  ├─ Phase 3: mm-paper-build
  │    Agents: paper-writer, claim traceability check
  │    Outputs: paper/, CLAIM_TRACE.md,
  │             METHOD_IMPLEMENTATION_MATRIX.md, PAPER_BUILD_REPORT.md
  │
  ├─ Phase 4: mm-contest-review
  │    Agents: contest-reviewer, devils-advocate,
  │            visualization-reviewer, model-reviewer
  │    Outputs: PAPER_SCORECARD.md, REVISION_ACTIONS.md
  │
  ├─ Phase 5: mm-revision-integrator
  │    Purpose: repair BLOCKER / HIGH / important MEDIUM issues
  │    Outputs: revised artifacts, REVISION_STATUS.md
  │
  └─ Phase 6: mm-final-verify
       Agent: final-integrator
       Output: VERIFY_REPORT.md
```

A contest run is complete only when `VERIFY_REPORT.md = PASS` and all hard gates are satisfied.

---

## Capability Layer: Local RAG Knowledge Base

`knowledge/` stores the local RAG configuration, samples and source notes. Large raw files and private contest data should stay local and must not be committed.

```text
knowledge/
├── README.md
├── libraries.json
├── samples/
│   ├── cumcm_problems/
│   ├── mcm_icm_problems/
│   ├── high_score_papers/
│   ├── model_methods/
│   ├── code_templates/
│   ├── figure_templates/
│   ├── paper_expression/
│   └── review_rubrics/
└── source_notes/
```

### Eight libraries

| Library | Purpose |
|---|---|
| `cumcm_problems` | 历年国赛题库、题型标签、隐含评分点 |
| `mcm_icm_problems` | 美赛题面、赛道、英文表达、常见模型路线 |
| `excellent_papers` | 高分论文结构、摘要、图表、模型路线、结论表达 |
| `model_methods` | 评价、预测、优化、机理、图论、统计、仿真、多目标决策等模型卡 |
| `code_templates` | Python/R/MATLAB 清洗、建模、验证、可视化脚本 |
| `figure_templates` | 推荐图、图表审计标准、caption 写法、证据图谱 |
| `paper_expression` | 摘要、问题重述、假设、公式说明、结果分析、灵敏度分析 |
| `review_rubrics` | 评分标准、评委快审、扣分点、反模板审查、高低分差距 |

### RAG quick start

```powershell
# Index built-in samples without external vector store
python scripts\rag_ingest.py --source knowledge\samples --vector-store none

# Query all libraries
python scripts\rag_query.py "综合评价类题目 TOPSIS 权重 稳定性"

# Query a specific library
python scripts\rag_query.py "预测 优化 混合题 约束 验证" --library model_methods

# JSON output for agent consumption
python scripts\rag_query.py "评委 快审 摘要 关键图 结论" --library review_rubrics --json
```

Optional local vector store:

```powershell
pip install chromadb sentence-transformers
python scripts\rag_ingest.py --source knowledge\raw --vector-store chroma --embedding-mode sentence-transformer --embedding-model BAAI/bge-m3
```

RAG is advisory. It provides evidence, candidate routes and review hints. Final modeling decisions still go through `mm-model-strategy`, human review and later contest-style checks.

---

## Control Center

`app/` provides a local full-stack control center for V2 workspaces.

```text
Backend: FastAPI, default http://127.0.0.1:8000
Frontend: Vue 3 + Vite, default http://127.0.0.1:5173
Harness mode: Manual-first
Supported targets: Manual, Codex, Claude Code, OpenCode prompt preparation
Safety policy: prepare copied run workspaces by default
```

Start on Windows:

```powershell
cd app
.\start.bat
```

Then open:

```text
http://127.0.0.1:5173
```

Beginner guide:

```text
docs/control-center-beginner-guide.md
```

The Control Center can create or inspect workspaces, read artifacts, generate phase prompts, check phase readiness, prepare safe copied runs and generate revision tasks.

---

## Repository Structure

```text
├── README.md
├── AGENTS.md                         # Codex-facing project guidance
├── CLAUDE.md                         # Claude Code-facing project guidance
├── FILE_RELATIONSHIP_MAP.md          # Full dependency graph and execution logic
├── mathmodelagent.skills.sh.json     # Skill manifest
│
├── knowledge/                        # V2.6 local RAG knowledge base
│   ├── README.md
│   ├── libraries.json
│   ├── samples/
│   └── source_notes/
│
├── skills/
│   ├── _references/                  # Shared contracts, rubrics, method cards, protocols
│   │   ├── v2_pipeline_contract.md
│   │   ├── workflow_state_contract.md
│   │   ├── codex_subagent_protocol.md
│   │   ├── contest_score_rubric.md
│   │   ├── paper_benchmark_profile.md
│   │   ├── figure_quality_standard.md
│   │   ├── agent_review_protocol.md
│   │   ├── model_method_cards.md
│   │   ├── problem_type_router.md
│   │   ├── anti_template_review.md
│   │   ├── judge_skim_review_protocol.md
│   │   ├── rag_usage_contract.md
│   │   ├── source_quality_policy.md
│   │   ├── figure_evidence_map.md
│   │   ├── executable_model_templates.md
│   │   ├── evaluator_optimizer_protocol.md
│   │   ├── agent_profiles/
│   │   └── scripts/
│   │
│   ├── mm-start-contest-v2/
│   ├── mm-problem-intake/
│   ├── mm-model-strategy/
│   ├── mm-data-experiment/
│   ├── mm-paper-build/
│   ├── mm-contest-review/
│   ├── mm-revision-integrator/
│   ├── mm-final-verify/
│   ├── 5writing/templates/           # Typst and LaTeX contest templates
│   ├── doctor/
│   └── typst-author/
│
├── scripts/
│   ├── rag_ingest.py
│   ├── rag_query.py
│   ├── import_zhanwen_mathmodel.py
│   ├── audit_benchmark.py
│   ├── new_v2_workspace.py
│   ├── memory_log.py
│   ├── memory_brief.py
│   └── memory_distill.py
│
├── app/                              # Local Control Center
│   ├── backend/
│   ├── frontend/
│   └── start.bat
│
├── docs/
│   ├── control-center-beginner-guide.md
│   └── control-center-ui-spec.md
│
├── examples/                         # Sanitized example contest workspaces
├── workspaces/                       # Local active contest workspaces, normally ignored
└── archive/v1/                       # Archived V1 legacy pipeline
```

---

## Workspace Artifacts

A V2 workspace should contain the following artifacts:

```text
<workspace>/
├── plan.md
├── todo.md
├── WORKFLOW_STATE.md
├── PROBLEM_BRIEF.md
├── DATA_AUDIT.md
├── reports/
│   ├── INTAKE_GATE.md
│   ├── MODEL_CANDIDATES.md
│   ├── MODEL_REVIEW_AI.md
│   ├── HUMAN_MODEL_REVIEW.md
│   ├── MODELING_DECISION.md
│   ├── ANALYSIS_MODELING_REPORT.md
│   ├── ANALYSIS_GATE.md
│   ├── FIGURE_PLAN.md
│   ├── EXPERIMENT_LOG.md
│   ├── RESULTS_REPORT.md
│   ├── FIGURE_AUDIT.md
│   ├── CLAIM_TRACE.md
│   ├── METHOD_IMPLEMENTATION_MATRIX.md
│   ├── PAPER_BUILD_REPORT.md
│   ├── PAPER_SCORECARD.md
│   ├── REVISION_ACTIONS.md
│   ├── REVISION_STATUS.md
│   └── VERIFY_REPORT.md
├── results/
│   └── RESULTS_MANIFEST.json
├── code/
├── figures/
└── paper/
```

---

## Subagent Roles

| Agent | Purpose | Permissions | Reasoning |
|---|---|---|---|
| `problem-analyst` | Parse problem, subquestions, objectives, constraints | read-only | medium |
| `data-auditor` | Inspect data files, fields, units, missingness and anomalies | read-only | medium |
| `model-strategist` | Generate candidate modeling routes | write `reports/` | high |
| `model-reviewer` | Review model fit, rigor and feasibility | read-only | high |
| `devils-advocate` | Attack weak assumptions and find hidden risks | read-only | high |
| `experiment-coder` | Implement scripts, run experiments, save outputs | write `code/`, `results/`, `figures/` | high |
| `visualization-reviewer` | Review figure quality, readability and evidence value | read-only | medium |
| `paper-writer` | Draft and revise paper sections | write `paper/` and selected reports | high |
| `contest-reviewer` | Score against contest rubric | read-only | high |
| `final-integrator` | Verify consistency and final submission readiness | write `paper/` and `reports/` | high |

Profiles live in:

```text
skills/_references/agent_profiles/
```

Custom Codex agent names use the `mathmodel-*` prefix, for example `mathmodel-experiment-coder`.

---

## Gates and Completion Criteria

Each gate returns one of:

```text
PASS
CONDITIONAL_PASS
FAIL
```

The project is complete only when all of the following are true:

1. `VERIFY_REPORT.md = PASS`
2. All contest score dimensions are `>= 4`, unless explicitly marked as justified N/A
3. `REVISION_ACTIONS.md` has no unresolved `BLOCKER` or `HIGH` items
4. `FIGURE_AUDIT.md` has no failed paper figures
5. `METHOD_IMPLEMENTATION_MATRIX.md` has no unimplemented core methods
6. `CLAIM_TRACE.md` has no missing core claims and no weak claims stated as strong
7. The paper compiles cleanly and the final PDF opens correctly
8. Internal workflow files are not leaked into the final paper text

---

## Contest Score Rubric

The default contest review uses 10 dimensions, each scored from 0 to 5.

| Dimension | What it checks |
|---|---|
| Problem understanding | Questions, assumptions, constraints, evaluation criteria |
| Data understanding | Files, fields, units, missing values, anomalies |
| Modeling fit | Whether methods match the data and question type |
| Mathematical rigor | Variables, formulas, objectives, constraints, derivations |
| Implementation | Reproducible code and alignment with the approved model |
| Result validity | Error analysis, sensitivity, robustness and sanity checks |
| Visualization | Figures support reasoning and appear in the paper |
| Writing structure | Complete contest paper structure and coherent narrative |
| Claim traceability | Claims map to results, figures, code or decisions |
| Submission readiness | No placeholders, no broken compilation, no obvious leakage |

Rating guide:

```text
5 = strong high-score quality
4 = acceptable contest-quality baseline
3 = visibly weak
2 = significant score loss
1 = mostly missing
0 = absent
```

---

## Templates

`skills/5writing/templates/` contains Typst and LaTeX templates for 17 contest types.

Chinese templates:

```text
CUMCM, ChangSanJiao, HuaShuBei, HuaweiBei, HuaZhongBei,
MathorCup, APMCM, ShuWeiBei, WuYiBei, DianGongBei,
DongSanSheng, Stats, MCM, Default
```

English templates:

```text
MCM/ICM, APMCM, Default
```

Each contest type has both Typst and LaTeX variants where available.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/zklzzklzkl/MathModel.git MathModelAgent
cd MathModelAgent
```

Install optional RAG dependencies:

```bash
pip install chromadb sentence-transformers
```

Install Control Center backend dependencies:

```bash
cd app/backend
pip install -e .
```

For Claude Code skills, copy skills into your local skills directory if needed:

```bash
cp -r skills/* ~/.claude/skills/
```

On Windows PowerShell, adapt the destination path to your local Claude Code or Codex skill location.

---

## Quick Usage

### 1. Create a new workspace

```bash
python scripts/new_v2_workspace.py workspaces/my-contest --contest CUMCM --engine LaTeX --language 中文
```

### 2. Start the V2 workflow in an agent harness

```text
/mm-start-contest-v2
```

### 3. Run final audit

```bash
python skills/_references/scripts/audit_v2_run.py --workspace workspaces/my-contest
```

### 4. Batch-audit benchmark examples

```bash
python scripts/audit_benchmark.py --root examples/2022C
```

### 5. Use the Control Center

```powershell
cd app
.\start.bat
```

Open:

```text
http://127.0.0.1:5173
```

---

## Optional Integrations

### ARS: Academic Research Suite

ARS can provide deeper methodology and editorial audits. Set `ARS_ROOT` to enable. It is advisory-only and should not be treated as a hard dependency.

### Nature Figure

Nature Figure integration can strengthen scientific plotting quality. Set `NATURE_SKILLS_ROOT` if installed.

Typical checks:

```bash
python skills/_references/scripts/resolve_nature_figure.py --workspace .
python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>
```

PNG-only or Pillow-generated data figures should not be accepted as core evidence figures when vector-quality output is required.

---

## Safety and Data Policy

Do not commit private contest data, large raw PDFs, local vector stores, local databases, runtime logs or generated private workspaces.

Normally ignored or local-only paths include:

```text
workspaces/
knowledge/raw/
knowledge/.local/
examples/**/source/
examples/**/runs/
**/control-center-history.jsonl
.env
.venv
node_modules/
dist/
```

Commit only sanitized examples, scripts, templates, contracts and source notes.

---

## Current Project Status

V2.6 is the active workflow version.

V1 is archived under `archive/v1/` and should not be used for new contests.

This repository is best understood as a contest-oriented AI workflow framework. The most important deliverable is not a single script, but a reproducible workspace containing model decisions, code results, figures, evidence traces, review reports and a final compiled paper.

---

## License

CC-BY-NC 4.0
