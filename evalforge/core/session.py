import os
import sys
import time
from datetime import UTC, datetime
from typing import Any

from ..models.run import Run
from ..models.trace import Step, StepType, Trace
from ..storage.repository import StepRepository, TraceRepository


class SessionRecorder:
    """Records full session traces for evaluation runs."""

    def __init__(self, run: Run, persist: bool = True):
        self.run = run
        self.trace = Trace(run_id=run.id)
        self.step_counter = 0
        self._persist = persist
        self._trace_repo = TraceRepository()
        self._step_repo = StepRepository()
        if self._persist:
            from ..storage.repository import RunRepository

            RunRepository().save(run)

    def record(
        self,
        step_type: StepType,
        content: str = "",
        tool_name: str | None = None,
        tool_input: dict | None = None,
        tool_output: str | None = None,
        token_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        state_snapshot: dict | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> Step:
        self.step_counter += 1
        step = Step(
            run_id=self.run.id,
            step_number=self.step_counter,
            timestamp=datetime.now(UTC).isoformat(),
            step_type=step_type,
            content=content,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            token_count=token_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            state_snapshot=state_snapshot,
            error_message=error_message,
            metadata=metadata or {},
        )
        self.trace.add_step(step)
        if self._persist:
            self._step_repo.save(step)
        return step

    def record_thought(self, content: str, **kwargs) -> Step:
        return self.record(StepType.thought, content=content, **kwargs)

    def record_tool_call(self, tool_name: str, tool_input: dict, **kwargs) -> Step:
        return self.record(
            StepType.tool_call,
            tool_name=tool_name,
            tool_input=tool_input,
            **kwargs,
        )

    def record_tool_result(self, tool_output: str, **kwargs) -> Step:
        return self.record(StepType.tool_result, tool_output=tool_output, **kwargs)

    def record_output(self, content: str, **kwargs) -> Step:
        return self.record(StepType.output, content=content, **kwargs)

    def record_error(self, error_message: str, **kwargs) -> Step:
        return self.record(StepType.error, error_message=error_message, **kwargs)

    def record_system(self, content: str, **kwargs) -> Step:
        return self.record(StepType.system, content=content, **kwargs)

    def save_trace(self) -> None:
        if self._persist:
            self._trace_repo.save(self.trace)

    def get_latency_timer(self) -> "Timer":
        return Timer()


class Timer:
    def __init__(self):
        self.start = time.monotonic()

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self.start) * 1000  # type: ignore[no-any-return]


_ENV_BLOCKLIST = {"KEY", "TOKEN", "SECRET", "PASSWORD", "API"}


def capture_env_snapshot() -> dict[str, Any]:
    return {
        "python_version": sys.version,
        "platform": sys.platform,
        "cwd": os.getcwd(),
        "env_vars": {k: v for k, v in os.environ.items() if not any(b in k.upper() for b in _ENV_BLOCKLIST)},
    }
