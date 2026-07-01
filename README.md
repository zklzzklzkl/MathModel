# MathModelAgent V2.3

数学建模竞赛全流程自动化 Skills —— 从赛题分析、建模设计、代码实验、图表生成到论文撰写与最终验收。

**Version**: 2.3
**Architecture**: Skill + Codex Subagent Hybrid Workflow  
**Active workflow**: V2.3 (8 V2 skills + shared references + tools). V1 is archived under `archive/v1/`.

## MathModel Control Center

This repository now includes a local full-stack Control Center under `app/`.

- Backend: FastAPI
- Frontend: Vue 3 + Vite
- Mode: Manual-first, harness-agnostic
- Supported prompt targets: Manual, Codex, Claude Code, OpenCode
- Safety default: prepare copied run workspaces instead of mutating the original workspace through a managed adapter

Beginner guide:

- `docs/control-center-beginner-guide.md`

Quick start:

```powershell
cd D:\WorkSpace_MathModel\app
.\start.bat
```

Open:

```text
http://127.0.0.1:5173
```

---

## Architecture Overview

```
V2 Workflow (High-Score Paper Oriented + Codex Subagents)

mm-start-contest-v2 (Orchestrator)
  │
  ├─[Phase 0]─ mm-problem-intake ──────── problem-analyst + data-auditor
  │     Gate: INTAKE_GATE ── PASS/CONDITIONAL_PASS/FAIL
  │
  ├─[Phase 1]─ mm-model-strategy ──────── model-reviewer + devils-advocate (+ optional ARS)
  │     Gate: HUMAN_MODEL_REVIEW.md (mandatory human confirmation)
  │
  ├─[Phase 2]─ mm-data-experiment ─────── experiment-coder + visualization-reviewer
  │     Gate: RESULTS_MANIFEST.json
  │
  ├─[Phase 3]─ mm-paper-build ─────────── claim-trace + method-matrix (+ optional ARS)
  │     Gate: FIGURE_AUDIT.md, CLAIM_TRACE.md
  │
  ├─[Phase 4]─ mm-contest-review ──────── multi-review-panel (+ optional ARS editorial synthesis)
  │     Gate: PAPER_SCORECARD.md (all dimensions >= 4)
  │
  ├─[Phase 5]─ mm-revision-integrator ──── revision loop (BLOCKER/HIGH/MEDIUM/LOW)
  │     Gate: REVISION_STATUS.md (no unresolved BLOCKER/HIGH)
  │
  └─[Phase 6]─ mm-final-verify ────────── final-integrator (+ optional ARS integrity checks)
        Gate: VERIFY_REPORT.md = PASS
```

### V1 Legacy Linear Pipeline

```
archive/v1/skills/0problem-triage → ... → archive/v1/skills/6verity
```

### Key Differences: V2 vs V1

| Aspect | V1 | V2 |
|--------|----|----|
| State management | Chat history | File-based workspace |
| Review | Self-review only | Independent subagent review panels |
| Model approval | Auto-proceed | Mandatory human confirmation gate |
| Scoring | None | 10-dimension contest rubric (0-5) |
| Claim tracking | Not enforced | CLAIM_TRACE.md with strength labels |
| Figure audit | None | FIGURE_AUDIT.md with FAIL tracking |
| Method alignment | Not checked | METHOD_IMPLEMENTATION_MATRIX.md |
| ARS integration | None | Optional deep-review layer |

---

## File Structure

```
├── mathmodelagent.skills.sh.json    # Skills manifest
├── skills/                          # All skill definitions
│   ├── _references/                 # Shared knowledge base (12 refs + 10 agent profiles)
│   │   ├── SKILL.md                 # Reference index
│   │   ├── v2_pipeline_contract.md  # V2 stage gates, artifacts, completion criteria
│   │   ├── codex_subagent_protocol.md # Subagent roles, parallelism, logging
│   │   ├── workflow_state_contract.md # V2 persistence context & gates
│   │   ├── contest_score_rubric.md  # 0-5 scoring, 10 dimensions, hard-fail conditions
│   │   ├── paper_benchmark_profile.md # Weak-vs-high-score gap profile
│   │   ├── figure_quality_standard.md # Metadata, quality checks, audit status
│   │   ├── model_method_cards.md    # Prediction/evaluation/optimization/statistics/simulation
│   │   ├── agent_review_protocol.md # Unified review format (PASS/CONDITIONAL_PASS/FAIL)
│   │   ├── ars_v2_integration_guide.md # Optional Academic Research Suite integration
│   │   ├── agent_profiles/          # 10 reusable agent role prompts
│   │   └── scripts/
│   │       ├── audit_v2_run.py
│   │       └── resolve_nature_figure.py
│   │
│   ├── 5writing/templates/          # 17 contest templates (Typst + LaTeX)
│   ├── doctor/SKILL.md              # Environment check & dependency install
│   │
│   ├── mm-start-contest-v2/         # V2: Orchestrator entry
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   ├── mm-problem-intake/           # V2: Problem & data intake
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   ├── mm-model-strategy/           # V2: Model candidate generation & review
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   ├── mm-data-experiment/          # V2: Experiment code, results, figures
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   ├── mm-paper-build/              # V2: Paper construction with figures
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   ├── mm-contest-review/           # V2: High-score benchmark review
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   ├── mm-final-verify/             # V2: Final acceptance
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   └── mm-revision-integrator/      # V2: Post-review revision loop
│       └── SKILL.md
│
└── examples/                        # Example contest workspaces
    └── 2022C/                       # Benchmark examples for V2.3 audits
└── archive/v1/                      # Archived V1 workflow and writing_check.sh
└── scripts/
    ├── audit_benchmark.py           # Batch audit examples
    └── new_v2_workspace.py          # Create a V2 workspace skeleton
```

---

## V2 Workflow Artifacts

```
<contest-workspace>/
├── plan.md                          # Execution plan
├── todo.md                          # Task checklist
├── WORKFLOW_STATE.md                # Current stage, completed, risks
├── PROBLEM_BRIEF.md                 # Problem restatement & decomposition
├── DATA_AUDIT.md                    # Data fields, units, quality, risks
├── reports/
│   ├── AGENT_RUNS.md                # Subagent execution log
│   ├── INTAKE_GATE.md               # Phase 0 gate result
│   ├── MODEL_CANDIDATES.md          # Candidate modeling routes
│   ├── MODEL_REVIEW_AI.md           # AI model review
│   ├── HUMAN_MODEL_REVIEW.md        # Human confirmation (MANDATORY)
│   ├── MODELING_DECISION.md         # Final model choices
│   ├── ANALYSIS_MODELING_REPORT.md  # Full modeling report
│   ├── ANALYSIS_GATE.md             # Phase 1 gate result
│   ├── EXPERIMENT_LOG.md            # Code execution log
│   ├── RESULTS_REPORT.md            # Results explanation
│   ├── FIGURE_PLAN.md               # Figure metadata & placement
│   ├── FIGURE_AUDIT.md              # Figure quality audit
│   ├── CLAIM_TRACE.md               # Conclusion-to-evidence mapping
│   ├── PAPER_BUILD_REPORT.md        # Paper construction report
│   ├── PAPER_SCORECARD.md           # Contest rubric scores (0-5)
│   ├── REVISION_ACTIONS.md          # Revision action items
│   ├── REVISION_STATUS.md           # Revision loop status
│   ├── METHOD_IMPLEMENTATION_MATRIX.md  # Route-to-code alignment
│   └── VERIFY_REPORT.md             # Final acceptance report
├── results/
│   └── RESULTS_MANIFEST.json        # All citable numeric results, figures
├── code/                            # Source code
│   └── outputs/                     # Generated data
├── figures/                         # Generated figures (PDF)
└── paper/                           # LaTeX or Typst paper
```

---

## Codex Subagent Roles

| Agent | Purpose | Permissions | Reasoning |
|-------|---------|-------------|-----------|
| `problem-analyst` | Parse problem, questions, objectives | read-only | medium |
| `data-auditor` | Inspect data files, fields, quality | read-only | medium |
| `model-strategist` | Create candidate modeling routes | read/write reports | high |
| `model-reviewer` | Review model fit, rigor, clarity | read-only | high |
| `devils-advocate` | Find objections, weak assumptions | read-only | high |
| `experiment-coder` | Implement scripts, run experiments | write code/results/figures | high |
| `visualization-reviewer` | Review figure adequacy | read-only | medium |
| `paper-writer` | Draft/revise paper sections | write paper/ + reports | high |
| `contest-reviewer` | Score against contest rubric | read-only | high |
| `final-integrator` | Integrate revisions, verify consistency | write paper + reports | high |

Installed custom agent names use `mathmodel-*` prefix (e.g., `mathmodel-problem-analyst`).

---

## Gates & Completion Criteria

Each stage gate produces: `PASS` | `CONDITIONAL_PASS` | `FAIL`

The project is **complete** only when `VERIFY_REPORT.md` = `PASS` and ALL of:

1. All contest score dimensions >= 4 (or justified N/A)
2. No unresolved `BLOCKER` or `HIGH` items in `REVISION_ACTIONS.md`
3. `FIGURE_AUDIT.md` has no FAIL for inserted paper figures
4. `METHOD_IMPLEMENTATION_MATRIX.md` shows no unimplemented core methods
5. No weak claims stated as strong conclusions
6. No unresolved `BLOCKER` items in `REVISION_ACTIONS.md`

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

## Supported Contests (Templates)

**Chinese (zh/):** CUMCM (国赛), ChangSanJiao (长三角), HuaShuBei (华数杯), HuaweiBei (华为杯), HuaZhongBei (华中杯), MathorCup, APMCM, ShuWeiBei (数维杯), WuYiBei (五一杯), DianGongBei (电工杯), DongSanSheng (东三省), Stats (统计建模), MCM, Default

**English (en/):** MCM/ICM, APMCM, Default

Each contest has both **Typst** and **LaTeX** templates.

---

## Optional ARS Integration

The [Academic Research Suite (ARS)](https://github.com/Imbad0202/academic-research-skills) can enhance V2 with deeper audits. Set `ARS_ROOT` to enable. ARS is advisory-only — never a hard dependency.

| V2 Stage | ARS Agent | Purpose |
|----------|-----------|---------|
| `mm-model-strategy` | `methodology_reviewer_agent` | Methodology audit |
| `mm-data-experiment` | `visualization_agent` | Publication-quality figure critique |
| `mm-paper-build` | `argument_builder_agent` | Claim-Evidence-Reasoning chain check |
| `mm-contest-review` | `editorial_synthesizer_agent` | Synthesize review panels |
| `mm-final-verify` | `integrity_verification_agent` | Reference & citation integrity |

---

## Optional Nature Figure Integration

[Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) can enhance V2 scientific plotting through `nature-figure`. Set `NATURE_SKILLS_ROOT` to a full `nature-skills` checkout, or keep the downloaded archive at `Downloads/Compressed/nature-skills-main/nature-skills-main`.

When enabled, MathModelAgent still owns the workflow. In V2.3, `nature-figure` is a hard quality gate for core paper figures: figure contracts, Python/R backend discipline, SVG/PDF export bundles, source-data traceability, and extended `FIGURE_AUDIT.md` checks must all be recorded before final `PASS`. PNG-only or Pillow-generated data figures are treated as revision issues, not publication-ready evidence.

Use the resolver to check availability:

```bash
python skills/_references/scripts/resolve_nature_figure.py --workspace .
```

See `skills/_references/nature_figure_integration_guide.md` and `examples/nature-figure-v2/`.

Run the V2.3 read-only audit on a contest workspace:

```bash
python skills/_references/scripts/audit_v2_run.py --workspace <contest-workspace>
```

Run the example benchmark:

```bash
python scripts/audit_benchmark.py --root examples/2022C
```

Create a fresh V2 workspace:

```bash
python scripts/new_v2_workspace.py workspace/my-contest --contest CUMCM --engine LaTeX --language 中文
```

---

## Installation

```bash
# Clone the repo
git clone <repo-url> MathModelAgent
cd MathModelAgent

# Copy skills to Claude Code skills directory
cp -r skills/* ~/.claude/skills/

# Or symlink for development
ln -s "$(pwd)/skills" ~/.claude/skills/mathmodel
```

---

## Usage

Start V2 workflow:
```
/mm-start-contest-v2
```

V1 is archived. Use only for historical reference:
```
archive/v1/skills/1start-mathmodel/SKILL.md
```

Check environment:
```
/doctor
```

---

## License

CC-BY-NC 4.0

## Author

张凯乐
