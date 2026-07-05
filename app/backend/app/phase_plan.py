from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RagQuerySpec(BaseModel):
    library: str
    query: str
    core_only: bool = False
    reason: str


class PlannedStep(BaseModel):
    id: str
    title: str
    description: str
    reads: list[str] = Field(default_factory=list)
    writes: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    requires_human: bool = False


class RiskItem(BaseModel):
    severity: str
    risk: str
    mitigation: str


class HumanGateSpec(BaseModel):
    gate_file: str
    required: bool = True
    reason: str


class FileWriteSpec(BaseModel):
    path: str
    purpose: str
    content: str


class CommandSpec(BaseModel):
    id: str
    purpose: str
    command: str
    expected_outputs: list[str] = Field(default_factory=list)


class PhasePlan(BaseModel):
    phase: int = Field(ge=0, le=6)
    phase_name: str
    summary: str
    required_inputs: list[str] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)
    planned_steps: list[PlannedStep] = Field(default_factory=list)
    rag_queries: list[RagQuerySpec] = Field(default_factory=list)
    source_quality_requirements: list[str] = Field(default_factory=list)
    human_gates: list[HumanGateSpec] = Field(default_factory=list)
    risk_register: list[RiskItem] = Field(default_factory=list)
    expected_artifacts: list[str] = Field(default_factory=list)
    do_not_do: list[str] = Field(default_factory=list)
    next_action: str
    file_writes: list[FileWriteSpec] = Field(default_factory=list)
    commands: list[CommandSpec] = Field(default_factory=list)

    @field_validator("phase", mode="before")
    @classmethod
    def parse_phase(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            m = re.search(r"\d+", str(v))
            if m:
                return int(m.group(0))
        raise ValueError(f"Cannot parse phase from: {v}")

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()
