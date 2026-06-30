import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


class GradingType(StrEnum):
    deterministic = "deterministic"
    llm_as_judge = "llm_as_judge"
    hybrid = "hybrid"


class SuccessCriteria(BaseModel):
    id: str = Field(default_factory=_uuid)
    description: str
    type: str = "exact_match"  # exact_match, contains, regex, llm_judge, callable
    expected: str | None = None
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskDefinition(BaseModel):
    id: str = Field(default_factory=_uuid)
    name: str
    description: str = ""
    instructions: str
    success_criteria: list[SuccessCriteria] = Field(default_factory=list)
    expected_output: str | None = None
    max_steps: int = 50
    max_tokens: int = 10000
    timeout_seconds: int = 300
    required_tools: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class Evaluation(BaseModel):
    id: str = Field(default_factory=_uuid)
    name: str
    description: str = ""
    tasks: list[TaskDefinition] = Field(default_factory=list)
    grading_type: GradingType = GradingType.deterministic
    judge_config: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
