"""Tests for the EvalForge CLI."""

import pytest
from typer.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock, PropertyMock

from evalforge.cli.main import app
from evalforge.storage.db import init_db, reset_db
from evalforge.storage.repository import EvaluationRepository, RunRepository, TraceRepository, DiagnosticRepository
from evalforge.models import (
    Evaluation, TaskDefinition, SuccessCriteria, GradingType,
    Run, Step, StepType, RunMetrics,
    Diagnostic, Severity, DiagnosticCategory, Trace,
)
from evalforge.providers.base import ProviderBase


class MockProvider(ProviderBase):
    name = "mock"
    default_model = "mock-model"

    def __init__(self):
        self.responses = iter([])
        self.chat_calls = []

    def chat(self, messages, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        self.chat_calls.append(messages)
        content = next(self.responses, "mock response")
        return {
            "content": content,
            "tool_calls": [],
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "cost_usd": 0.0,
            "model": self.default_model,
        }

    def count_tokens(self, text, model=None):
        return len(text) // 4


@pytest.fixture(autouse=True)
def db():
    init_db()
    yield
    reset_db()


runner = CliRunner()


class TestInit:
    def test_init_command_output(self):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "EvalForge initialized" in result.stdout

    def test_init_can_be_called_multiple_times(self):
        result1 = runner.invoke(app, ["init"])
        result2 = runner.invoke(app, ["init"])
        assert result1.exit_code == 0
        assert result2.exit_code == 0


class TestRun:
    @patch("evalforge.cli.run.create_provider")
    @patch("evalforge.cli.run.EvaluationEngine")
    def test_run_with_evaluation_id(self, mock_engine_cls, mock_create_provider):
        mock_provider = MockProvider()
        mock_provider.responses = iter(["hello"])
        mock_create_provider.return_value = mock_provider

        task = TaskDefinition(name="test-task", instructions="say hello")
        eval_obj = Evaluation(name="test-eval", tasks=[task])

        eval_repo = EvaluationRepository()
        eval_repo.save(eval_obj)

        mock_engine = MagicMock()
        run = Run(
            evaluation_id=eval_obj.id, task_id=task.id, status="completed",
            metrics=RunMetrics(success=True, success_score=1.0, step_count=1,
                              total_cost_usd=0.0, total_tokens=30),
        )
        mock_engine.run.return_value = [run]
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["run", eval_obj.id, "--provider", "deepseek"])
        assert result.exit_code == 0

    @patch("evalforge.cli.run.create_provider")
    @patch("evalforge.cli.run.EvaluationEngine")
    def test_run_with_evaluation_name(self, mock_engine_cls, mock_create_provider):
        mock_provider = MockProvider()
        mock_provider.responses = iter(["hello"])
        mock_create_provider.return_value = mock_provider

        task = TaskDefinition(name="test-task", instructions="say hello")
        eval_obj = Evaluation(name="test-eval", tasks=[task])

        eval_repo = EvaluationRepository()
        eval_repo.save(eval_obj)

        mock_engine = MagicMock()
        run = Run(
            evaluation_id=eval_obj.id, task_id=task.id, status="completed",
            metrics=RunMetrics(success=True, success_score=1.0, step_count=1,
                              total_cost_usd=0.0, total_tokens=30),
        )
        mock_engine.run.return_value = [run]
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, ["run", "test-eval", "--provider", "deepseek"])
        assert result.exit_code == 0

    @patch("evalforge.cli.run.create_provider")
    @patch("evalforge.cli.run.EvaluationEngine")
    def test_run_with_model_and_seed(self, mock_engine_cls, mock_create_provider):
        mock_provider = MockProvider()
        mock_provider.responses = iter(["hello"])
        mock_create_provider.return_value = mock_provider

        task = TaskDefinition(name="test-task", instructions="say hello")
        eval_obj = Evaluation(name="test-eval", tasks=[task])

        eval_repo = EvaluationRepository()
        eval_repo.save(eval_obj)

        mock_engine = MagicMock()
        mock_engine.run.return_value = []
        mock_engine_cls.return_value = mock_engine

        result = runner.invoke(app, [
            "run", eval_obj.id, "--provider", "deepseek",
            "--model", "deepseek-chat", "--seed", "42",
        ])
        assert result.exit_code == 0

    @patch("evalforge.cli.run.create_provider")
    def test_run_evaluation_not_found(self, mock_create_provider):
        result = runner.invoke(app, ["run", "nonexistent-eval"])
        assert result.exit_code == 0
        assert "not found" in result.stdout.lower() or "❌" in result.stdout


class TestList:
    def test_list_empty(self):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No evaluations found" in result.stdout

    def test_list_with_evals(self):
        eval_repo = EvaluationRepository()
        eval_repo.save(Evaluation(name="test-eval-a", tasks=[
            TaskDefinition(name="t1", instructions="do it"),
        ]))
        eval_repo.save(Evaluation(name="test-eval-b", tasks=[]))

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "test-eval-a" in result.stdout
        assert "test-eval-b" in result.stdout

    def test_list_with_limit(self):
        eval_repo = EvaluationRepository()
        for i in range(5):
            eval_repo.save(Evaluation(name=f"eval-{i}", tasks=[]))
        result = runner.invoke(app, ["list", "--limit", "3"])
        assert result.exit_code == 0


class TestListRuns:
    def test_list_runs_empty(self):
        result = runner.invoke(app, ["list-runs"])
        assert result.exit_code == 0
        assert "No runs found" in result.stdout

    def test_list_runs_with_runs(self):
        run_repo = RunRepository()
        run_repo.save(Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        ))
        run_repo.save(Run(
            evaluation_id="e2", task_id="t2", status="failed",
            metrics=RunMetrics(
                success=False, success_score=0.0, step_count=1,
                tool_call_count=0, error_count=1, total_tokens=50,
                total_cost_usd=0.0, total_latency_ms=200.0,
                avg_step_latency_ms=200.0, efficiency_score=0.0,
            ),
        ))

        result = runner.invoke(app, ["list-runs"])
        assert result.exit_code == 0
        assert "completed" in result.stdout
        assert "failed" in result.stdout

    def test_list_runs_with_eval_filter(self):
        run_repo = RunRepository()
        run_repo.save(Run(evaluation_id="specific-eval", task_id="t1", status="completed",
                         metrics=RunMetrics(success=True, success_score=1.0, step_count=1)))
        run_repo.save(Run(evaluation_id="other-eval", task_id="t2", status="pending",
                         metrics=RunMetrics()))

        result = runner.invoke(app, ["list-runs", "--eval", "specific-eval"])
        assert result.exit_code == 0


class TestExport:
    def test_export_markdown(self):
        run_repo = RunRepository()
        trace_repo = TraceRepository()
        diag_repo = DiagnosticRepository()

        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        run_repo.save(run)

        result = runner.invoke(app, ["export", run.id, "--format", "markdown"])
        assert result.exit_code == 0
        assert "Report exported" in result.stdout

    def test_export_json(self):
        run_repo = RunRepository()
        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        run_repo.save(run)

        result = runner.invoke(app, ["export", run.id, "--format", "json"])
        assert result.exit_code == 0
        assert "Report exported" in result.stdout

    def test_export_html(self):
        run_repo = RunRepository()
        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        run_repo.save(run)

        result = runner.invoke(app, ["export", run.id, "--format", "html"])
        assert result.exit_code == 0
        assert "Report exported" in result.stdout

    def test_export_with_output_path(self):
        run_repo = RunRepository()
        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        run_repo.save(run)

        result = runner.invoke(app, [
            "export", run.id, "--format", "markdown", "--output", "/tmp/test_export.md",
        ])
        assert result.exit_code == 0
        assert "Report exported" in result.stdout

    def test_export_run_not_found(self):
        result = runner.invoke(app, ["export", "nonexistent"])
        assert result.exit_code == 0
        assert "not found" in result.stdout.lower() or "❌" in result.stdout


class TestServe:
    @patch("evalforge.dashboard.app.create_app")
    def test_serve_defaults(self, mock_create_app):
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        result = runner.invoke(app, ["serve"])
        assert result.exit_code == 0
        mock_create_app.assert_called_once()
        mock_app.launch.assert_called_once_with(
            server_name="0.0.0.0", server_port=7860, share=False,
        )

    @patch("evalforge.dashboard.app.create_app")
    def test_serve_custom_host_port(self, mock_create_app):
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "7890"])
        assert result.exit_code == 0
        mock_app.launch.assert_called_once_with(
            server_name="127.0.0.1", server_port=7890, share=False,
        )

    @patch("evalforge.dashboard.app.create_app")
    def test_serve_with_share(self, mock_create_app):
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        result = runner.invoke(app, ["serve", "--share"])
        assert result.exit_code == 0
        mock_app.launch.assert_called_once_with(
            server_name="0.0.0.0", server_port=7860, share=True,
        )
