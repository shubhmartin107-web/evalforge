import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from .diagnostics import Diagnostic
from .metrics import RunMetrics


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


class Run(BaseModel):
    id: str = Field(default_factory=_uuid)
    evaluation_id: str
    task_id: str
    status: str = "pending"  # pending, running, completed, failed
    agent_config: dict[str, Any] = Field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    seed: int | None = None
    env_snapshot: dict[str, Any] = Field(default_factory=dict)
    metrics: RunMetrics = Field(default_factory=RunMetrics)
    trace_id: str | None = None
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
