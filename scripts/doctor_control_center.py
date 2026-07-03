"""Environment doctor for MathModel Control Center v2.

This script is intentionally read-only. It checks local tools, project files,
optional LangGraph/provider packages, and beginner documentation without
crashing on the first failure.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    status: str
    name: str
    detail: str
    required: bool = True


def run_command(args: list[str]) -> tuple[bool, str]:
    executable = shutil.which(args[0])
    if not executable:
        return False, "command not found"
    command: list[str] | str = [executable, *args[1:]]
    shell = False
    if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
        command = subprocess.list2cmdline(command)
        shell = True
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=shell,
        )
    except FileNotFoundError:
        return False, "command not found"
    output = (result.stdout or result.stderr).strip()
    return result.returncode == 0, output


def parse_node_version(text: str) -> tuple[int, int, int] | None:
    token = text.strip().lstrip("v").split()[0] if text.strip() else ""
    parts = token.split(".")
    if len(parts) < 2:
        return None
    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0
    except ValueError:
        return None
    return major, minor, patch


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def path_check(path: str, name: str, required: bool = True) -> Check:
    target = REPO_ROOT / path
    if target.exists():
        return Check("OK", name, str(target.relative_to(REPO_ROOT)), required)
    return Check("FAIL" if required else "WARN", name, f"missing: {path}", required)


def collect_checks() -> list[Check]:
    checks: list[Check] = []

    py_version = sys.version_info
    py_detail = f"Python {py_version.major}.{py_version.minor}.{py_version.micro} ({sys.executable})"
    checks.append(Check("OK" if py_version >= (3, 10) else "FAIL", "Python >= 3.10", py_detail))

    node_ok, node_out = run_command(["node", "--version"])
    node_version = parse_node_version(node_out) if node_ok else None
    node_good = bool(node_version and node_version >= (18, 0, 0))
    checks.append(Check("OK" if node_good else "FAIL", "Node.js >= 18", node_out or "node not found"))

    npm_ok, npm_out = run_command(["npm", "--version"])
    checks.append(Check("OK" if npm_ok else "FAIL", "npm", npm_out or "npm not found"))

    checks.extend(
        [
            path_check("app/backend/requirements.txt", "backend requirements"),
            path_check("app/backend/requirements-langgraph.txt", "LangGraph requirements", required=False),
            path_check("app/frontend/package.json", "frontend package.json"),
            path_check(".venv", "root .venv", required=False),
            path_check("app/frontend/node_modules", "frontend node_modules", required=False),
        ]
    )

    for module, required in [
        ("fastapi", True),
        ("uvicorn", True),
        ("langgraph", False),
        ("openai", False),
    ]:
        checks.append(
            Check(
                "OK" if module_available(module) else ("FAIL" if required else "WARN"),
                f"import {module}",
                "installed" if module_available(module) else "not installed",
                required,
            )
        )

    checks.extend(
        [
            path_check(".env", ".env", required=False),
            path_check(".env.example", ".env.example", required=False),
            path_check("workspaces", "workspace root", required=False),
            path_check("README.md", "README.md"),
            path_check("docs/frontend-beginner-guide.md", "beginner guide", required=False),
            path_check("docs/frontend-control-center-v2.md", "frontend control center docs", required=False),
        ]
    )

    return checks


def print_checks(checks: list[Check]) -> None:
    for check in checks:
        print(f"[{check.status}] {check.name}: {check.detail}")


def summarize(checks: list[Check]) -> int:
    required_failed = [c for c in checks if c.required and c.status == "FAIL"]
    optional_warnings = [c for c in checks if not c.required and c.status in {"WARN", "FAIL"}]

    print()
    if required_failed:
        print("Blocked:")
        print("- Missing Python/Node/core dependency or required project file.")
        for item in required_failed:
            print(f"- {item.name}: {item.detail}")
        return 2

    if optional_warnings:
        print("Partial:")
        print("- Control Center can use provider=none, but optional setup is incomplete.")
        for item in optional_warnings:
            print(f"- {item.name}: {item.detail}")
        return 0

    print("Ready:")
    print("- Control Center can be started locally.")
    return 0


def main() -> int:
    os.chdir(REPO_ROOT)
    print("MathModel Control Center Doctor")
    print(f"Repo: {REPO_ROOT}")
    print()
    checks = collect_checks()
    print_checks(checks)
    return summarize(checks)


if __name__ == "__main__":
    raise SystemExit(main())
