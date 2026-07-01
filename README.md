# MathModelAgent V2.4

数学建模竞赛全流程自动化 —— Skill + Codex 子代理混合工作流，覆盖赛题分析、建模策略、代码实验、图表生成、论文撰写、评审修订与最终验收。

**Workflow**: V2.4 (8 skills + shared references + tools)
**Archived**: V1 pipeline → `archive/v1/`
**Version**: 2.4

---

## Control Center（本地全栈管理台）

`app/` 提供了一个 Manual-first、harness-agnostic 的本地管控台：

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

## Architecture

```
mm-start-contest-v2 (Orchestrator)
  │
  ├─ Phase 0: mm-problem-intake ────── problem-analyst + data-auditor
  │     Gate: INTAKE_GATE.md
  │
  ├─ Phase 1: mm-model-strategy ────── model-reviewer + devils-advocate (+ optional ARS)
  │     Gate: HUMAN_MODEL_REVIEW.md (mandatory human confirmation)
  │
  ├─ Phase 2: mm-data-experiment ───── experiment-coder + visualization-reviewer
  │     Gate: RESULTS_MANIFEST.json, FIGURE_AUDIT.md
  │
  ├─ Phase 3: mm-paper-build ───────── paper-writer + claim-trace + method-matrix
  │     Gate: CLAIM_TRACE.md, METHOD_IMPLEMENTATION_MATRIX.md
  │
  ├─ Phase 4: mm-contest-review ────── contest-reviewer + multi-review-panel
  │     Gate: PAPER_SCORECARD.md (all dimensions >= 4)
  │
  ├─ Phase 5: mm-revision-integrator ─ revision loop (BLOCKER/HIGH/MEDIUM/LOW)
  │     Gate: REVISION_STATUS.md (no unresolved BLOCKER/HIGH)
  │
  └─ Phase 6: mm-final-verify ──────── final-integrator (+ optional ARS integrity)
        Gate: VERIFY_REPORT.md = PASS
```

V1 legacy pipeline has been archived to `archive/v1/`. Use only for historical reference.

### V2 vs V1

| Aspect | V1 (archived) | V2 (active) |
|--------|---------------|-------------|
| State management | Chat history | File-based workspace artifacts |
| Review | Self-review only | Independent subagent review panels |
| Model approval | Auto-proceed | Mandatory human confirmation gate |
| Scoring | None | 10-dimension contest rubric (0-5) |
| Claim tracking | Not enforced | CLAIM_TRACE.md with strength labels |
| Figure audit | None | FIGURE_AUDIT.md with FAIL tracking |
| Method alignment | Not checked | METHOD_IMPLEMENTATION_MATRIX.md |
| Revision loop | None | mm-revision-integrator |
| ARS integration | None | Optional deep-review layer |
| Nature Figure | None | Hard quality gate for core figures |

---

## File Structure

```
├── mathmodelagent.skills.sh.json    # Skills manifest (V2 + tools + _references)
├── CLAUDE.md                        # Project-level AI config
├── FILE_RELATIONSHIP_MAP.md         # Complete dependency graph
├── AGENTS.md                        # Agent orchestration config
│
├── skills/
│   ├── _references/                 # Shared knowledge base (14 files + 10 agent profiles)
│   │   ├── v2_pipeline_contract.md   # V2 stage gates, artifacts, completion criteria
│   │   ├── codex_subagent_protocol.md  # Subagent roles, parallelism, logging
│   │   ├── workflow_state_contract.md  # Persistence context & gates
│   │   ├── contest_score_rubric.md     # 10-dimension, 0-5 scoring
│   │   ├── paper_benchmark_profile.md  # Weak-vs-high-score gap profile
│   │   ├── figure_quality_standard.md  # Figure quality & audit
│   │   ├── model_method_cards.md       # Modeling route cards
│   │   ├── agent_review_protocol.md    # Unified review format (PASS/CONDITIONAL_PASS/FAIL)
│   │   ├── ars_v2_integration_guide.md         # Optional ARS integration
│   │   ├── nature_figure_integration_guide.md  # Optional Nature Figure integration
│   │   ├── agent_profiles/          # 10 reusable agent role prompts
│   │   └── scripts/
│   │       ├── audit_v2_run.py      # V2 read-only final audit
│   │       └── resolve_nature_figure.py  # Nature Figure availability check
│   │
│   ├── mm-start-contest-v2/         # V2 Orchestrator entry
│   ├── mm-problem-intake/           # V2 Phase 0: Problem & data intake
│   ├── mm-model-strategy/           # V2 Phase 1: Modeling strategy
│   ├── mm-data-experiment/          # V2 Phase 2: Experiment & visualization
│   ├── mm-paper-build/              # V2 Phase 3: Paper construction
│   ├── mm-contest-review/           # V2 Phase 4: High-score benchmark review
│   ├── mm-revision-integrator/      # V2 Phase 5: Revision loop
│   ├── mm-final-verify/             # V2 Phase 6: Final acceptance
│   │
│   ├── 5writing/templates/          # 34 contest templates (Typst + LaTeX, 17 contest types x2)
│   └── doctor/                      # Environment check & dependency install
│
├── app/                             # Control Center (FastAPI + Vue 3/Vite)
│   ├── backend/
│   ├── frontend/
│   └── start.bat
│
├── scripts/
│   ├── audit_benchmark.py           # Batch audit examples → PASS/FAIL table
│   └── new_v2_workspace.py          # Create a V2 workspace skeleton
│
├── docs/
│   ├── control-center-beginner-guide.md
│   └── control-center-ui-spec.md
│
├── examples/                        # Example contest workspaces
│   └── 2022C/                       # V2 benchmark (CUMCM 2022 Problem C)
│       └── BENCHMARK.md
│
├── workspaces/                      # Active contest workspaces
└── archive/v1/                      # Archived V1 pipeline
```

---

## V2 Workspace Artifacts

Each contest run produces:

```
<workspace>/
├── plan.md                          # Execution plan with contest type, engine, language
├── todo.md                          # Phase checklist
├── WORKFLOW_STATE.md                # Current stage, completed, risks, decisions
├── PROBLEM_BRIEF.md                 # Structured problem restatement
├── DATA_AUDIT.md                    # Data fields, units, quality risks
├── reports/
│   ├── INTAKE_GATE.md               # Phase 0 gate (PASS/CONDITIONAL_PASS/FAIL)
│   ├── MODEL_CANDIDATES.md          # Candidate modeling routes
│   ├── MODEL_REVIEW_AI.md           # AI model review
│   ├── HUMAN_MODEL_REVIEW.md        # ★ Human confirmation (MANDATORY)
│   ├── MODELING_DECISION.md         # Final adopted route
│   ├── ANALYSIS_MODELING_REPORT.md  # Full formulas, algorithms, task list
│   ├── ANALYSIS_GATE.md             # Phase 1 gate
│   ├── FIGURE_PLAN.md               # Figure purpose, placement, captions
│   ├── EXPERIMENT_LOG.md            # Code execution log
│   ├── RESULTS_REPORT.md            # Result narrative
│   ├── FIGURE_AUDIT.md              # Figure quality audit
│   ├── CLAIM_TRACE.md               # Conclusion → evidence mapping
│   ├── METHOD_IMPLEMENTATION_MATRIX.md  # Route → code → paper alignment
│   ├── PAPER_BUILD_REPORT.md        # Paper construction summary
│   ├── PAPER_SCORECARD.md           # 10-dimension scores
│   ├── REVISION_ACTIONS.md          # Action items (BLOCKER/HIGH/MEDIUM/LOW)
│   ├── REVISION_STATUS.md           # Revision loop tracking
│   └── VERIFY_REPORT.md             # Final acceptance (PASS/CONDITIONAL_PASS/FAIL)
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
6. Paper compiles cleanly (LaTeX/Typst) and PDF opens without blank pages

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

| V2 Phase | ARS Agent | Purpose |
|----------|-----------|---------|
| `mm-model-strategy` | `methodology_reviewer_agent` | Methodology audit |
| `mm-data-experiment` | `visualization_agent` | Publication-quality figure critique |
| `mm-paper-build` | `argument_builder_agent` | Claim-Evidence-Reasoning chain check |
| `mm-contest-review` | `editorial_synthesizer_agent` | Synthesize review panels |
| `mm-final-verify` | `integrity_verification_agent` | Reference & citation integrity |

### Nature Figure

[Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) enhances scientific plotting. Set `NATURE_SKILLS_ROOT` env var. V2 treats it as a hard quality gate for core paper figures.

```bash
python skills/_references/scripts/resolve_nature_figure.py --workspace .
```

---

## Scripts

```bash
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

# Copy skills to Claude Code skills directory
cp -r skills/* ~/.claude/skills/

# Symlink for development
ln -s "$(pwd)/skills" ~/.claude/skills/mathmodel
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
