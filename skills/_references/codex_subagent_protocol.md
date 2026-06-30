# Codex Subagent Protocol

Use this protocol when a V2 skill introduces Codex subagents, official built-in agents, custom agents, parallel execution, thread viewing, inherited permissions, or per-agent model/reasoning settings.

## Role Of Subagents

Subagents are independent workers or reviewers. They do not own the workflow. The main skill remains the orchestrator and must integrate their results into durable files.

## Default Agent Profiles

Reusable profile prompts live in `agent_profiles/`. Use those files when creating custom agents or when prompting default Codex subagents.

When installed globally, the custom Codex agent names use the `mathmodel-*` prefix, for example `mathmodel-problem-analyst` and `mathmodel-contest-reviewer`. A running Codex session may not hot-load newly added agent TOML files; in that case, use built-in `default`, `worker`, or `explorer` agents with the matching `agent_profiles/` prompt, and use the `mathmodel-*` names after Codex reloads the agent registry.

| Agent | Purpose | Permissions | Reasoning |
| --- | --- | --- | --- |
| `problem-analyst` | independently parse problem, questions, objectives, constraints | read-only | medium |
| `data-auditor` | inspect data files, fields, units, missing values, risks | read-only | medium |
| `model-strategist` | create candidate mathematical modeling routes | read/write reports | high |
| `model-reviewer` | review model fit, rigor, implementation clarity | read-only | high |
| `devils-advocate` | find judge objections, weak assumptions, unsupported claims | read-only | high |
| `experiment-coder` | implement scripts, run experiments, generate outputs | write `code/`, `results/`, `figures/`, `reports/EXPERIMENT_LOG.md` | high |
| `visualization-reviewer` | review figure adequacy and paper usefulness | read-only | medium |
| `paper-writer` | draft or revise paper sections from approved evidence | write `paper/`, `CLAIM_TRACE.md` | high |
| `contest-reviewer` | score against contest/high-score rubric | read-only | high |
| `final-integrator` | integrate approved revisions and verify consistency | write paper and reports only | high |

If native custom agents are unavailable, use the same role names in prompts and log them as simulated subagent runs.

Installed custom agent mapping for future sessions or refreshed registries:

| Profile | Installed custom agent |
| --- | --- |
| `problem-analyst` | `mathmodel-problem-analyst` |
| `data-auditor` | `mathmodel-data-auditor` |
| `model-strategist` | `mathmodel-strategist` |
| `model-reviewer` | `mathmodel-reviewer` |
| `devils-advocate` | `mathmodel-devils-advocate` |
| `experiment-coder` | `mathmodel-experiment-coder` |
| `visualization-reviewer` | `mathmodel-visualization-reviewer` |
| `paper-writer` | `mathmodel-paper-writer` |
| `contest-reviewer` | `mathmodel-contest-reviewer` |
| `final-integrator` | `mathmodel-final-integrator` |

## Official Built-In Agent Mapping

Use official Codex agents when they fit better than a custom role:

| Need | Preferred built-in |
| --- | --- |
| inspect project structure or trace existing code | `explorer` |
| implement a disjoint write scope | `worker` |
| review modified code or scripts | `code-reviewer` |
| evaluate an agent output or final response | `agent-evaluator` |
| architecture-level redesign | `architect` or `planner` |

For domain-specific math modeling review, use the custom profiles in `agent_profiles/` with `default`, `explorer`, or `worker` as the underlying agent type.

## Parallel Execution

Parallelize only tasks with independent inputs and disjoint write scopes.

Good parallel tasks:

- `problem-analyst` and `data-auditor`
- `model-reviewer` and `devils-advocate`
- figure quality review and paper structure review
- contest score review and final trace review

Do not parallelize:

- final model decision before human review
- code that writes the same script or output file
- paper integration while experiment outputs are still changing

## Thread Viewing And Logging

Record every subagent run in `reports/AGENT_RUNS.md`:

```markdown
## <timestamp> <agent-name>

- goal:
- input artifacts:
- model/reasoning:
- permission scope:
- output artifacts:
- conclusion:
- thread/id if available:
```

The orchestrator must summarize subagent conclusions. Do not paste long raw transcripts into the main context.

Simulated subagent runs must use the same log format. Set thread/id to `simulated` when no native thread exists.

## Permission Inheritance

Subagents inherit project permissions by default, but the prompt must state the intended scope:

- Review agents: "read files and write only your final report if asked."
- Coding agents: "write only under `code/`, `code/outputs/`, `figures/`, `results/`, and named reports."
- Paper agents: "write only under `paper/` and named claim/revision reports."

Never allow a subagent to delete unrelated files or overwrite user-provided source data.

## Model And Reasoning Defaults

Use the strongest available reasoning for:

- model strategy
- model review
- devil's advocate
- final verification

Use medium or default reasoning for:

- file inventory
- formatting checks
- straightforward figure review

Prefer different model families or providers for review if configured. If only one model is available, keep roles independent by limiting each subagent to its own task and artifacts.

## Prompt Pattern

Use concise prompts:

```text
You are <role>. Work in <workspace>. Read <input artifacts>. Produce <output>. 
Do not modify files outside <scope>. Do not rely on chat history. 
Judge against <reference>. Return PASS/FAIL and concrete fixes.
```
