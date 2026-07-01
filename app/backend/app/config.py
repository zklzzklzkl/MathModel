from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
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
    _load_dotenv(backend_root / ".env")
    root = Path(os.environ.get("MATHMODEL_ROOT", _repo_root())).resolve()
    return Settings(
        mathmodel_root=root,
        workspace_root=Path(os.environ.get("WORKSPACE_ROOT", root / "workspaces")).resolve(),
        examples_root=Path(os.environ.get("EXAMPLES_ROOT", root / "examples")).resolve(),
        python_executable=os.environ.get("PYTHON", "python"),
    )
