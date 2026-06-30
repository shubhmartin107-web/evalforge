from ..models.diagnostics import Diagnostic
from ..models.run import Run
from ..models.trace import Step, StepType, Trace
from ..storage.repository import RunRepository, TraceRepository


class ReplayPlayer:
    """Step-through session replay for evaluation runs."""

    def __init__(self):
        self._trace_repo = TraceRepository()
        self._run_repo = RunRepository()

    def load_run(self, run_id: str) -> tuple[Run | None, Trace | None]:
        run = self._run_repo.find_by_id(run_id)
        trace = self._trace_repo.find_by_run_id(run_id) if run else None
        return run, trace

    def get_step(self, trace: Trace, step_index: int) -> Step | None:
        if 0 <= step_index < len(trace.steps):
            return trace.steps[step_index]
        return None

    def get_step_range(self, trace: Trace, start: int, end: int) -> list[Step]:
        return trace.steps[start:end]

    def find_failure_points(self, trace: Trace, diagnostics: list[Diagnostic]) -> list[dict]:
        failure_points = []
        for d in diagnostics:
            if d.severity.value in ("error", "critical"):
                step = None
                if d.step_index is not None and d.step_index < len(trace.steps):
                    step = trace.steps[d.step_index]
                failure_points.append(
                    {
                        "diagnostic": d,
                        "step": step,
                        "step_index": d.step_index,
                    }
                )
        return failure_points

    def get_step_context(self, trace: Trace, step_index: int, window: int = 3) -> dict:
        start = max(0, step_index - window)
        end = min(len(trace.steps), step_index + window + 1)
        return {
            "current_step": self.get_step(trace, step_index),
            "context_steps": self.get_step_range(trace, start, end),
            "context_range": (start, end),
            "total_steps": len(trace.steps),
            "progress_pct": round((step_index + 1) / len(trace.steps) * 100, 1) if trace.steps else 0,
        }

    def get_step_summary(self, step: Step) -> dict:
        icon_map = {
            StepType.thought: "💭",
            StepType.tool_call: "🔧",
            StepType.tool_result: "📥",
            StepType.output: "📤",
            StepType.error: "❌",
            StepType.system: "⚙️",
        }
        return {
            "icon": icon_map.get(step.step_type, "•"),
            "type": step.step_type.value,
            "step_number": step.step_number,
            "preview": step.content[:100]
            if step.content
            else step.tool_output[:100]
            if step.tool_output
            else step.tool_name or "",
            "tool_name": step.tool_name,
            "token_count": step.token_count,
            "cost_usd": step.cost_usd,
            "latency_ms": step.latency_ms,
            "has_error": step.step_type == StepType.error,
        }
