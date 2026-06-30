import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


class Severity(StrEnum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class DiagnosticCategory(StrEnum):
    tool_selection = "tool_selection"
    context_window = "context_window"
    reasoning = "reasoning"
    hallucination = "hallucination"
    timeout = "timeout"
    looping = "looping"
    cost_overrun = "cost_overrun"
    efficiency = "efficiency"
    prompt_quality = "prompt_quality"
    general = "general"


class Diagnostic(BaseModel):
    id: str = Field(default_factory=_uuid)
    run_id: str
    severity: Severity = Severity.info
    category: DiagnosticCategory = DiagnosticCategory.general
    title: str = ""
    description: str = ""
    step_index: int | None = None
    recommendation: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
