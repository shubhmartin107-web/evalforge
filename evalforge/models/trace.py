import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


class StepType(StrEnum):
    thought = "thought"
    tool_call = "tool_call"
    tool_result = "tool_result"
    output = "output"
    error = "error"
    system = "system"


class Step(BaseModel):
    id: str = Field(default_factory=_uuid)
    run_id: str
    step_number: int
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    step_type: StepType = StepType.thought
    content: str = ""
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: str | None = None
    token_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    state_snapshot: dict[str, Any] | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Trace(BaseModel):
    id: str = Field(default_factory=_uuid)
    run_id: str
    steps: list[Step] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_step(self, step: Step) -> None:
        self.steps.append(step)

    def total_tokens(self) -> int:
        return sum(s.token_count for s in self.steps)

    def total_cost(self) -> float:
        return sum(s.cost_usd for s in self.steps)

    def total_latency(self) -> float:
        return sum(s.latency_ms for s in self.steps)

    def step_count(self) -> int:
        return len(self.steps)
