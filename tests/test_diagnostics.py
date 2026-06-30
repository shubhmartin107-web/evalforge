"""Tests for diagnostics engine."""

from evalforge.models import Step, StepType, RunMetrics, Run
from evalforge.diagnostics.heuristics import (
    detect_looping,
    detect_context_window_exhaustion,
    detect_cost_overrun,
    detect_tool_selection_issues,
    detect_reasoning_failures,
    run_all_heuristics,
)
from evalforge.diagnostics.insights import generate_insights, generate_comparison_insight
from evalforge.diagnostics.analyzer import DiagnosticAnalyzer


def make_step(run_id, num, step_type=StepType.thought, **kwargs):
    return Step(run_id=run_id, step_number=num, step_type=step_type, **kwargs)


class TestHeuristics:
    def test_detect_looping(self):
        steps = [make_step("r1", i, StepType.tool_call, tool_name="search") for i in range(6)]
        results = detect_looping(steps, threshold=5)
        assert len(results) >= 1
        assert results[0].category.value == "looping"

    def test_no_looping(self):
        steps = [make_step("r1", i, StepType.thought, content="thinking") for i in range(10)]
        results = detect_looping(steps, threshold=5)
        assert len(results) == 0

    def test_context_window_exhaustion(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="x", token_count=900),
            make_step("r1", 2, StepType.thought, content="x", token_count=900),
        ]
        results = detect_context_window_exhaustion(steps, max_context=1000)
        assert len(results) >= 1

    def test_no_context_issue(self):
        steps = [make_step("r1", 1, StepType.thought, content="x", token_count=100)]
        results = detect_context_window_exhaustion(steps, max_context=10000)
        assert len(results) == 0

    def test_cost_overrun(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="x", cost_usd=0.06),
            make_step("r1", 2, StepType.thought, content="x", cost_usd=0.05),
        ]
        results = detect_cost_overrun(steps, max_cost=0.10)
        assert len(results) >= 1

    def test_tool_selection_issues(self):
        steps = [
            make_step("r1", 1, StepType.tool_call, tool_name="search", tool_input={}),
            make_step("r1", 2, StepType.error, tool_name="search", error_message="failed"),
            make_step("r1", 3, StepType.tool_call, tool_name="search", tool_input={}),
            make_step("r1", 4, StepType.error, tool_name="search", error_message="failed"),
        ]
        results = detect_tool_selection_issues(steps)
        assert len(results) >= 1

    def test_reasoning_failures(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="thinking"),
            make_step("r1", 2, StepType.error, error_message="Something went wrong"),
        ]
        results = detect_reasoning_failures(steps)
        assert len(results) >= 1

    def test_run_all_heuristics(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="x", token_count=50),
            make_step("r1", 2, StepType.tool_call, tool_name="search", token_count=50),
            make_step("r1", 3, StepType.tool_call, tool_name="search", token_count=50),
            make_step("r1", 4, StepType.tool_call, tool_name="search", token_count=50),
            make_step("r1", 5, StepType.tool_call, tool_name="search", token_count=50),
            make_step("r1", 6, StepType.tool_call, tool_name="search", token_count=50),
        ]
        results = run_all_heuristics(steps)
        assert len(results) >= 1


class TestInsights:
    def test_generate_insights_success(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=True, success_score=0.95, step_count=5))
        insight = generate_insights(run, [])
        assert "completed successfully" in insight

    def test_generate_insights_failure(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=False, success_score=0.2, step_count=3))
        insight = generate_insights(run, [])
        assert "failed" in insight

    def test_generate_comparison(self):
        runs = [
            Run(evaluation_id="e1", task_id="t1", status="completed",
                metrics=RunMetrics(success=True, success_score=0.9, total_cost_usd=0.01)),
            Run(evaluation_id="e1", task_id="t1", status="completed",
                metrics=RunMetrics(success=False, success_score=0.3, total_cost_usd=0.05)),
        ]
        insight = generate_comparison_insight(runs)
        assert "Comparison" in insight
        assert "0.9" in insight


class TestAnalyzer:
    def test_summarize_failure(self):
        run = Run(evaluation_id="e1", task_id="t1", error_message="API error")
        from evalforge.models.diagnostics import Diagnostic, Severity, DiagnosticCategory
        diag = Diagnostic(
            run_id="r1",
            severity=Severity.warning,
            category=DiagnosticCategory.tool_selection,
            title="Tool error",
            description="Tool failed",
            recommendation="Fix tool",
        )
        analyzer = DiagnosticAnalyzer()
        summary = analyzer.summarize_failure(run, [diag])
        assert "Tool error" in summary
