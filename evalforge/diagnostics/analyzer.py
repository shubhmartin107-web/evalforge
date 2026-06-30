from ..models.diagnostics import Diagnostic
from ..models.run import Run
from ..models.trace import Trace
from ..storage.repository import DiagnosticRepository, TraceRepository
from .heuristics import run_all_heuristics
from .insights import generate_insights


class DiagnosticAnalyzer:
    """Performs automated root-cause analysis on evaluation runs."""

    def __init__(self):
        self._trace_repo = TraceRepository()
        self._diag_repo = DiagnosticRepository()

    def analyze_run(
        self,
        run: Run,
        trace: Trace | None = None,
        max_context: int = 32000,
        max_cost: float = 0.10,
        timeout_ms: float = 300000,
    ) -> list[Diagnostic]:
        if trace is None:
            trace = self._trace_repo.find_by_run_id(run.id)

        if trace is None or not trace.steps:
            return []

        diagnostics = run_all_heuristics(
            trace.steps,
            max_context=max_context,
            max_cost=max_cost,
            timeout_ms=timeout_ms,
        )

        for d in diagnostics:
            d.run_id = run.id
            self._diag_repo.save(d)

        return diagnostics

    def get_insights(self, run: Run, diagnostics: list[Diagnostic]) -> str:
        return generate_insights(run, diagnostics)

    def summarize_failure(self, run: Run, diagnostics: list[Diagnostic]) -> str:
        if run.status == "completed" and run.metrics.success:
            return "Run completed successfully."

        errors = [d for d in diagnostics if d.severity.value in ("error", "critical")]
        if errors:
            primary = errors[0]
            return f"Primary failure: {primary.title}. {primary.recommendation}"

        warnings = [d for d in diagnostics if d.severity.value == "warning"]
        if warnings:
            primary = warnings[0]
            return f"Issue detected: {primary.title}. {primary.recommendation}"

        if run.error_message:
            return f"Error: {run.error_message}"

        return "No specific diagnostics generated."
