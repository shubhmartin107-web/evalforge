"""Tests for metrics computation."""

from evalforge.models import Step, StepType, RunMetrics
from evalforge.core.metrics import compute_metrics, compute_benchmark_metrics


def make_step(run_id, num, step_type=StepType.thought, **kwargs):
    return Step(run_id=run_id, step_number=num, step_type=step_type, **kwargs)


class TestMetrics:
    def test_compute_metrics_empty(self):
        metrics = compute_metrics([], success=False)
        assert metrics.step_count == 0
        assert metrics.success == False

    def test_compute_metrics_basic(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="x", token_count=100, input_tokens=50, output_tokens=50, latency_ms=200),
        ]
        metrics = compute_metrics(steps, success=True, success_score=1.0)
        assert metrics.step_count == 1
        assert metrics.total_tokens == 100
        assert metrics.total_latency_ms == 200.0
        assert metrics.success == True
        assert metrics.success_score == 1.0

    def test_compute_metrics_multi_step(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="x", token_count=50, latency_ms=100),
            make_step("r1", 2, StepType.tool_call, tool_name="search", token_count=30, latency_ms=500),
            make_step("r1", 3, StepType.tool_result, tool_output="result", token_count=20, latency_ms=50),
        ]
        metrics = compute_metrics(steps, success=True, success_score=0.8)
        assert metrics.step_count == 3
        assert metrics.total_tokens == 100
        assert metrics.total_latency_ms == 650.0
        assert metrics.tool_call_count == 1

    def test_compute_metrics_with_cost(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="x", token_count=100, cost_usd=0.001),
        ]
        metrics = compute_metrics(steps, success=True, success_score=1.0)
        assert metrics.total_cost_usd == 0.001

    def test_compute_benchmark_metrics(self):
        metrics_list = [
            RunMetrics(success=True, success_score=1.0, total_cost_usd=0.01, total_latency_ms=1000, total_tokens=500, step_count=3),
            RunMetrics(success=True, success_score=0.8, total_cost_usd=0.02, total_latency_ms=2000, total_tokens=800, step_count=5),
            RunMetrics(success=False, success_score=0.2, total_cost_usd=0.03, total_latency_ms=3000, total_tokens=1200, step_count=7),
        ]
        result = compute_benchmark_metrics(metrics_list)
        assert result["total_runs"] == 3
        assert result["successful_runs"] == 2
        assert result["failed_runs"] == 1
        import pytest
        assert result["avg_success_rate"] == pytest.approx(2/3, rel=1e-3)

    def test_efficiency_score(self):
        steps = [
            make_step("r1", 1, StepType.thought, content="x", token_count=100, latency_ms=100),
        ]
        metrics = compute_metrics(steps, success=True, success_score=1.0)
        assert metrics.efficiency_score > 0
