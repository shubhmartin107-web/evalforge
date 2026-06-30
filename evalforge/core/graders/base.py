from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GradingResult:
    passed: bool
    score: float
    description: str = ""
    criterion_id: str = ""
    weight: float = 1.0
    reasoning: str = ""
    criterion_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseGrader(ABC):
    name: str = "base"

    @abstractmethod
    def evaluate(self, agent_output: str, expected: str | None = None, **kwargs) -> GradingResult: ...
