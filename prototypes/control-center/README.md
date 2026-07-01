# MathModel Control Center Prototype

This is a static UI prototype for the harness-agnostic MathModelAgent V2.3 control center.

Open `index.html` directly in a browser. It does not start a backend and does not mutate any workspace files.

## Purpose

- Validate the workspace-first UI layout before choosing a frontend stack.
- Show how V2.3 phases, gate artifacts, audit issues, prompts, and benchmark runs fit together.
- Keep the control center independent from any single harness such as Codex, Claude Code, or OpenCode.

## Next Implementation Step

Build the first real backend read API:

- `GET /api/workspaces`
- `GET /api/workspaces/{id}/summary`
- `GET /api/workspaces/{id}/artifacts`
- `GET /api/workspaces/{id}/artifacts/{path}`
- `POST /api/workspaces/{id}/audit`
- `POST /api/workspaces/{id}/prompt`

The UI should continue to treat local workspace files as the source of truth.
