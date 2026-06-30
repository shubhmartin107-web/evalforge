"""Tests for replay and export."""

from evalforge.models import Run, Trace, Step, StepType, RunMetrics, Diagnostic, Severity, DiagnosticCategory
from evalforge.replay.player import ReplayPlayer
from evalforge.replay.renderer import render_step_cli, render_trace_cli
from evalforge.replay.exporter import export_run_to_json, export_run_to_markdown, export_run_to_html


def make_step(run_id, num, step_type=StepType.thought, **kwargs):
    return Step(run_id=run_id, step_number=num, step_type=step_type, **kwargs)


class TestPlayer:
    def test_get_step(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="test"),
            make_step("r1", 2, StepType.tool_call, tool_name="search"),
        ]
        trace = Trace(run_id="r1", steps=steps)
        player = ReplayPlayer()
        step = player.get_step(trace, 0)
        assert step is not None
        assert step.step_number == 1
        assert player.get_step(trace, 10) is None

    def test_get_step_range(self):
        steps = [make_step("r1", i, StepType.thought) for i in range(10)]
        trace = Trace(run_id="r1", steps=steps)
        player = ReplayPlayer()
        result = player.get_step_range(trace, 2, 5)
        assert len(result) == 3

    def test_get_step_context(self):
        steps = [make_step("r1", i, StepType.thought, content=f"step {i}") for i in range(10)]
        trace = Trace(run_id="r1", steps=steps)
        player = ReplayPlayer()
        ctx = player.get_step_context(trace, 5, window=2)
        assert ctx["current_step"] is not None
        assert ctx["total_steps"] == 10
        assert len(ctx["context_steps"]) == 5

    def test_get_step_summary(self):
        step = make_step("r1", 1, StepType.tool_call, tool_name="search", content="", latency_ms=100, token_count=50)
        player = ReplayPlayer()
        summary = player.get_step_summary(step)
        assert summary["type"] == "tool_call"
        assert summary["tool_name"] == "search"
        assert summary["latency_ms"] == 100

    def test_find_failure_points(self):
        steps = [make_step("r1", i, StepType.thought) for i in range(5)]
        trace = Trace(run_id="r1", steps=steps)
        diag = Diagnostic(
            run_id="r1", severity=Severity.error, category=DiagnosticCategory.general,
            title="Fail", description="desc", step_index=2,
        )
        player = ReplayPlayer()
        points = player.find_failure_points(trace, [diag])
        assert len(points) == 1
        assert points[0]["step_index"] == 2


class TestRenderer:
    def test_render_step(self):
        step = make_step("r1", 1, StepType.thought, content="I am thinking")
        output = render_step_cli(step)
        assert "💭" in output
        assert "Step 1" in output
        assert "thinking" in output

    def test_render_tool_call(self):
        step = make_step("r1", 2, StepType.tool_call, tool_name="search", tool_input={"q": "hello"}, latency_ms=500)
        output = render_step_cli(step)
        assert "🔧" in output
        assert "search" in output

    def test_render_trace(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="think"),
            make_step("r1", 2, StepType.output, content="done"),
        ]
        output = render_trace_cli(steps)
        assert "Trace: 2 steps" in output


class TestExporter:
    def test_export_json(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=True, success_score=1.0))
        result = export_run_to_json(run)
        assert '"export_version"' in result
        assert '"run"' in result
        assert '"success_score"' in result

    def test_export_markdown(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=True, success_score=0.85))
        steps = [make_step("r1", 1, StepType.thought, content="test")]
        trace = Trace(run_id="r1", steps=steps)
        diag = Diagnostic(run_id="r1", severity=Severity.info, category=DiagnosticCategory.general, title="Info")
        result = export_run_to_markdown(run, trace, [diag])
        assert "EvalForge Run Report" in result
        assert "Metrics" in result
        assert "Diagnostics" in result
        assert "Trace" in result

    def test_export_html(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=True, success_score=0.9))
        result = export_run_to_html(run)
        assert "<html" in result
        assert "EvalForge Report" in result
