# MathModel Control Center v3

Control Center v3 is the simplified local UI for MathModelAgent. It replaces the old dashboard-heavy layout with a chat-like workflow console:

```text
choose workspace -> upload source files -> run recommended graph -> read status messages -> handle human gate -> inspect generated artifacts
```

It still uses the same FastAPI backend, V2 skills, LangGraph Runtime, audit scripts and copied run workspace safety model. The UI change is intentionally a product-layer simplification, not a new execution engine.

## What Changed

| Area | v2 behavior | v3 behavior |
|---|---|---|
| Navigation | Many developer-oriented pages | Three primary entries: Start, Workspaces, Settings |
| Main screen | Dashboard cards, long issue lists | Chat-style activity stream plus one priority blocker |
| Prompts/Harness | Visible as normal workflow | Moved to advanced diagnostics; recommended path is LangGraph Runtime |
| Human Gate | User had to find review files manually | Summary dialog with AI discussion, then explicit human review write |
| Workspaces | Mostly add-only | Archive/restore source workspaces; archive or permanently delete run copies |
| JSON fragility | Direct model JSON parsing | LLM output passes through a tolerant JSON preprocessor before schema validation |

## Primary Workflow

1. Open `app/start.bat`.
2. Select or create a source workspace.
3. Upload problem statements and attachments in Settings.
4. Click the primary `Start recommended flow` button.
5. Read the activity stream and the top priority blocker.
6. If the workflow pauses at Human Gate, open the review dialog, discuss risks, and explicitly write the human decision.
7. Inspect generated reports in the preview pane or historical run copies.

The default run path remains `contest_graph_v3` with `copy_workspace=true`. Source workspaces are protected by copied run workspaces.

## Human Gate Dialog

The Human Gate dialog is not a simple approve/reject switch. It shows:

- model route summary
- model review excerpt
- figure plan excerpt
- detected risks
- suggested questions
- an AI-assisted discussion area
- a final human decision form

The AI discussion endpoint does not write `reports/HUMAN_MODEL_REVIEW.md`. Only the explicit review action writes that file, and the user must choose:

- `approved`
- `needs_revision`
- `rejected`

This preserves the hard Human Gate: the system does not silently approve its own model route.

## Workspace Management

The Workspaces view separates:

- Source workspaces
- Archived source workspaces
- Historical run workspaces

Rules:

- Example workspaces are read-only and cannot be archived.
- Source workspaces under `WORKSPACE_ROOT` can be archived to `.archive/`.
- Archived workspaces can be restored.
- Run workspaces can be archived under `runs/.archive/`.
- Permanent run deletion requires typing the exact run name.

These operations are backend-validated and stay inside the configured workspace roots.

## JSON Preprocessor

Real LLM providers often return JSON with harmless wrappers or formatting defects. v3 adds a backend JSON preprocessor before PhasePlan schema validation.

It can handle:

- Markdown fenced JSON blocks
- leading/trailing prose around a JSON object
- UTF-8 BOM
- trailing commas
- raw control characters accepted by Python JSON `strict=False`

It still does not accept invalid plans silently. If parsing or schema validation fails, LangGraph writes:

```text
reports/LANGGRAPH_RAW_MODEL_OUTPUT.md
reports/LANGGRAPH_JSON_PREPROCESS_REPORT.md
reports/LANGGRAPH_RUN_REPORT.md
```

The run stays reviewable instead of collapsing into an opaque frontend error.

## Safety Boundaries

Control Center v3 keeps the existing safety boundaries:

- no `contest_graph_v4`
- no automatic `VERIFY_REPORT.md`
- no bypass of `HUMAN_MODEL_REVIEW.md`
- no API key storage in the frontend
- no WebSocket or streaming side channel
- no direct mutation of source workspace outputs by recommended runs
- no changes to `skills/`

Single phase execution still only supports P1 and P4. Other phases should use Dry Run or the recommended `contest_graph_v3` flow.

## Validation

Useful validation commands:

```powershell
cd app/frontend
npm run build

cd ../..
python -m pytest -q
git diff --check
git status --short --branch
```

If you only want to check the UI and LangGraph API path:

```powershell
python -m pytest tests/test_langgraph_api.py tests/test_safe_langgraph_benchmark_api.py -q
python -m pytest tests/test_workspace_management_api.py tests/test_human_gate_api.py tests/test_json_preprocessor.py -q
```
