"""Tests for remaining uncovered modules."""

import os
import json
from datetime import datetime, timezone

from evalforge.storage.db import init_db, reset_db, get_db_path, serialize, deserialize, close_connection
from evalforge.storage.repository import TaskDefinitionRepository, StepRepository
from evalforge.utils.cost import estimate_cost, format_cost, MODEL_PRICING
from evalforge.utils.tokenizer import estimate_tokens, count_tokens
from evalforge.models.trace import Trace, Step, StepType
from evalforge.models.run import Run
from evalforge.models.run import RunMetrics
from evalforge.diagnostics.heuristics import detect_timeout, detect_efficiency_issues, detect_hallucination_patterns, run_all_heuristics
from evalforge.diagnostics.analyzer import DiagnosticAnalyzer
from evalforge.diagnostics.insights import generate_insights
from evalforge.replay.player import ReplayPlayer
from evalforge.replay.renderer import render_step_for_gradio, render_metrics_summary
from evalforge.benchmarks.registry import register_benchmark, register_all, _coding_benchmarks, _research_benchmarks, _tool_use_benchmarks
from evalforge.models.evaluation import Evaluation, TaskDefinition as EvalTaskDef
from evalforge.models.diagnostics import Diagnostic


class TestUtilsCost:
    def test_model_pricing_structure(self):
        assert "deepseek-chat" in MODEL_PRICING
        assert "claude-3-5-sonnet-20241022" in MODEL_PRICING
        for model, prices in MODEL_PRICING.items():
            assert "input" in prices
            assert "output" in prices

    def test_estimate_cost(self):
        cost = estimate_cost(1000, 500, "deepseek-chat")
        assert cost > 0
        assert cost < 1.0

    def test_estimate_cost_unknown_model(self):
        cost = estimate_cost(1000, 500, "unknown-model")
        assert cost >= 0

    def test_format_cost_small(self):
        assert "0.0001" in format_cost(0.0001)

    def test_format_cost_zero(self):
        assert "0.00" in format_cost(0.0)


class TestUtilsTokenizer:
    def test_estimate_tokens_empty(self):
        assert estimate_tokens("") == 0

    def test_estimate_tokens_short(self):
        assert estimate_tokens("hello") == 1

    def test_estimate_tokens_longer(self):
        n = estimate_tokens("hello world this is a test")
        assert n > 0

    def test_count_tokens_delegates(self):
        assert count_tokens("test", "deepseek-chat") == estimate_tokens("test")


class TestTraceHelpers:
    def test_total_tokens(self):
        t = Trace(run_id="r1")
        t.add_step(Step(run_id="r1", step_number=1, token_count=100))
        t.add_step(Step(run_id="r1", step_number=2, token_count=200))
        assert t.total_tokens() == 300

    def test_total_tokens_empty(self):
        t = Trace(run_id="r1")
        assert t.total_tokens() == 0

    def test_total_cost(self):
        t = Trace(run_id="r1")
        t.add_step(Step(run_id="r1", step_number=1, cost_usd=0.01))
        t.add_step(Step(run_id="r1", step_number=2, cost_usd=0.02))
        assert t.total_cost() == 0.03

    def test_total_latency(self):
        t = Trace(run_id="r1")
        t.add_step(Step(run_id="r1", step_number=1, latency_ms=100))
        t.add_step(Step(run_id="r1", step_number=2, latency_ms=200))
        assert t.total_latency() == 300

    def test_step_count(self):
        t = Trace(run_id="r1")
        assert t.step_count() == 0
        t.add_step(Step(run_id="r1", step_number=1))
        assert t.step_count() == 1


class TestHeuristicsRemaining:
    def test_detect_timeout_exceeded(self):
        steps = [
            Step(run_id="r1", step_number=1, latency_ms=200000),
            Step(run_id="r1", step_number=2, latency_ms=200000),
        ]
        diags = detect_timeout(steps, timeout_ms=300000)
        assert len(diags) == 1
        assert "timeout" in diags[0].category.value

    def test_detect_timeout_ok(self):
        steps = [
            Step(run_id="r1", step_number=1, latency_ms=100),
            Step(run_id="r1", step_number=2, latency_ms=200),
        ]
        diags = detect_timeout(steps, timeout_ms=300000)
        assert len(diags) == 0

    def test_detect_efficiency_low_tool_use(self):
        steps = [
            Step(run_id="r1", step_number=1, step_type=StepType.thought, content="a"),
            Step(run_id="r1", step_number=2, step_type=StepType.thought, content="b"),
            Step(run_id="r1", step_number=3, step_type=StepType.thought, content="c"),
            Step(run_id="r1", step_number=4, step_type=StepType.thought, content="d"),
            Step(run_id="r1", step_number=5, step_type=StepType.thought, content="e"),
            Step(run_id="r1", step_number=6, step_type=StepType.thought, content="f"),
            Step(run_id="r1", step_number=7, step_type=StepType.tool_call, tool_name="test"),
        ]
        diags = detect_efficiency_issues(steps)
        assert len(diags) == 1
        assert diags[0].category.value == "efficiency"

    def test_detect_efficiency_normal(self):
        steps = [
            Step(run_id="r1", step_number=1, step_type=StepType.thought, content="a"),
            Step(run_id="r1", step_number=2, step_type=StepType.tool_call, tool_name="t1"),
            Step(run_id="r1", step_number=3, step_type=StepType.tool_call, tool_name="t2"),
        ]
        diags = detect_efficiency_issues(steps)
        assert len(diags) == 0

    def test_detect_hallucination_markers(self):
        steps = [
            Step(run_id="r1", step_number=1, step_type=StepType.output,
                 content="I think the answer is X. I believe this is correct. As an AI, I cannot be certain. It is important to note that this might be wrong."),
        ]
        diags = detect_hallucination_patterns(steps)
        assert len(diags) == 1
        assert diags[0].category.value == "hallucination"

    def test_detect_hallucination_clean(self):
        steps = [
            Step(run_id="r1", step_number=1, step_type=StepType.output,
                 content="The answer is 42."),
        ]
        diags = detect_hallucination_patterns(steps)
        assert len(diags) == 0

    def test_run_all_heuristics_includes_new(self):
        steps = [
            Step(run_id="r1", step_number=1, step_type=StepType.thought, content="a", latency_ms=100),
            Step(run_id="r1", step_number=2, step_type=StepType.tool_call, tool_name="t1", latency_ms=100),
        ]
        diags = run_all_heuristics(steps)
        assert isinstance(diags, list)


class TestDiagnosticAnalyzer:
    def test_analyze_run_no_trace(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=True, success_score=1.0))
        analyzer = DiagnosticAnalyzer()
        diags = analyzer.analyze_run(run, trace=None)
        assert diags == []

    def test_get_insights(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=True, success_score=0.95, step_count=5, tool_call_count=3, error_count=0,
                                     total_tokens=1000, input_tokens=600, output_tokens=400, total_cost_usd=0.01,
                                     total_latency_ms=5000, avg_step_latency_ms=1000.0, efficiency_score=80.0))
        diags = [Diagnostic(run_id=run.id, severity="info", category="general", title="Test", description="desc")]
        analyzer = DiagnosticAnalyzer()
        text = analyzer.get_insights(run, diags)
        assert "score:" in text
        assert "Test" in text

    def test_summarize_failure_success(self):
        run = Run(evaluation_id="e1", task_id="t1", status="completed",
                  metrics=RunMetrics(success=True, success_score=1.0))
        analyzer = DiagnosticAnalyzer()
        assert "completed" in analyzer.summarize_failure(run, [])

    def test_summarize_failure_errors(self):
        run = Run(evaluation_id="e1", task_id="t1", status="failed",
                  metrics=RunMetrics(success=False, success_score=0.0))
        analyzer = DiagnosticAnalyzer()
        diags = [Diagnostic(run_id=run.id, severity="error", category="reasoning", title="Error!", description="fail")]
        text = analyzer.summarize_failure(run, diags)
        assert "Error" in text


class TestReplayPlayer:
    def test_load_run_not_found(self):
        player = ReplayPlayer()
        run, trace = player.load_run("nonexistent")
        assert run is None
        assert trace is None

    def test_get_step_summary(self):
        step = Step(run_id="r1", step_number=1, step_type=StepType.thought, content="test", token_count=50)
        player = ReplayPlayer()
        summary = player.get_step_summary(step)
        assert summary["step_number"] == 1
        assert summary["type"] == "thought"
        assert summary["token_count"] == 50


class TestRendererRemaining:
    def test_render_step_for_gradio(self):
        step = Step(run_id="r1", step_number=1, step_type=StepType.thought, content="test")
        out = render_step_for_gradio(step)
        assert "test" in out

    def test_render_metrics_summary(self):
        metrics = {
            "success_score": 0.85,
            "total_cost_usd": 0.01,
            "total_tokens": 1000,
            "step_count": 5,
        }
        out = render_metrics_summary(metrics)
        assert "85" in out


class TestBenchmarkRegistry:
    def test_coding_benchmarks(self):
        benchmarks = _coding_benchmarks()
        assert len(benchmarks) == 3
        names = [b.name for b in benchmarks]
        assert "simple-code-gen" in names

    def test_research_benchmarks(self):
        benchmarks = _research_benchmarks()
        assert len(benchmarks) == 2
        names = [b.name for b in benchmarks]
        assert "research-summary" in names

    def test_tool_use_benchmarks(self):
        benchmarks = _tool_use_benchmarks()
        assert len(benchmarks) == 2
        names = [b.name for b in benchmarks]
        assert "multi-step-workflow" in names

    def test_register_benchmark(self):
        init_db()
        reset_db()
        init_db()
        eval_obj = Evaluation(name="test-register", description="test")
        result = register_benchmark(eval_obj)
        assert result.id == eval_obj.id

    def test_register_all(self):
        init_db()
        reset_db()
        init_db()
        benchmarks = register_all()
        assert len(benchmarks) >= 11


class TestStorageDB:
    def test_get_db_path_default(self):
        path = get_db_path()
        assert str(path).endswith("evalforge.db")

    def test_get_db_path_env(self):
        os.environ["EVALFORGE_DB_PATH"] = "/tmp/test_evalforge.db"
        try:
            path = get_db_path()
            assert str(path) == "/tmp/test_evalforge.db"
        finally:
            del os.environ["EVALFORGE_DB_PATH"]

    def test_serialize_deserialize_roundtrip(self):
        data = {"key": "value", "nested": [1, 2, 3]}
        s = serialize(data)
        d = deserialize(s)
        assert d == data

    def test_deserialize_none(self):
        assert deserialize(None) == {}

    def test_deserialize_invalid(self):
        assert deserialize("not valid json{{{") == {}

    def test_serialize_none(self):
        s = serialize(None)
        d = deserialize(s)
        assert d is None

    def test_close_and_reconnect(self):
        close_connection()
        from evalforge.storage.db import get_connection
        conn = get_connection()
        assert conn is not None
        close_connection()


class TestTaskDefinitionRepository:
    def test_save_and_retrieve(self):
        init_db()
        reset_db()
        init_db()
        repo = TaskDefinitionRepository()
        from evalforge.models.evaluation import TaskDefinition
        task = TaskDefinition(name="test-task", description="test", instructions="do something")
        repo.save(task)
