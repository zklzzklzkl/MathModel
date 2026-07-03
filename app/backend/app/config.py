from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_env_file(path: Path, loaded: list[str]) -> None:
    if not path.is_file():
        return
    loaded.append(str(path))
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    mathmodel_root: Path
    workspace_root: Path
    examples_root: Path
    python_executable: str
    env_files_checked: list[str] = field(default_factory=list)
    env_files_loaded: list[str] = field(default_factory=list)

    @property
    def audit_script(self) -> Path:
        return self.mathmodel_root / "skills" / "_references" / "scripts" / "audit_v2_run.py"

    @property
    def benchmark_script(self) -> Path:
        return self.mathmodel_root / "scripts" / "audit_benchmark.py"

    @property
    def scaffold_script(self) -> Path:
        return self.mathmodel_root / "scripts" / "new_v2_workspace.py"


def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = _repo_root()
    checked = [str(backend_root / ".env"), str(repo_root / ".env")]
    loaded: list[str] = []
    _load_env_file(backend_root / ".env", loaded)
    _load_env_file(repo_root / ".env", loaded)

    root = Path(os.environ.get("MATHMODEL_ROOT", repo_root)).resolve()
    workspace_root_raw = os.environ.get("WORKSPACE_ROOT") or os.environ.get("MATHMODEL_WORKSPACE_ROOT") or root / "workspaces"
    return Settings(
        mathmodel_root=root,
        workspace_root=Path(workspace_root_raw).resolve(),
        examples_root=Path(os.environ.get("EXAMPLES_ROOT", root / "examples")).resolve(),
        python_executable=os.environ.get("PYTHON", "python"),
        env_files_checked=checked,
        env_files_loaded=loaded,
    )
