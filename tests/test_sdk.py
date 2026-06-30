"""Tests for the EvalForge SDK."""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from evalforge.sdk import EvalForge
from evalforge.models import (
    Evaluation, TaskDefinition, SuccessCriteria, GradingType,
    Run, Trace, Step, StepType, RunMetrics,
    Diagnostic, Severity, DiagnosticCategory,
)
from evalforge.storage.db import init_db, reset_db
from evalforge.providers.base import ProviderBase
from evalforge.core.metrics import RunMetrics


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


class TestEvalForge:
    def test_init_default(self):
        ef = EvalForge()
        assert ef.provider is None
        assert ef.judge_provider is None
        assert ef.engine is not None
        assert ef.engine.provider is None

    def test_init_with_provider_instance(self):
        provider = MockProvider()
        ef = EvalForge(provider=provider)
        assert ef.provider is provider
        assert ef.judge_provider is provider
        assert ef.engine.provider is provider

    def test_init_with_string_provider(self):
        with patch("evalforge.sdk.create_provider") as mock_create:
            mock_provider = MockProvider()
            mock_create.return_value = mock_provider
            ef = EvalForge(provider="deepseek")
            mock_create.assert_called_once_with("deepseek")
            assert ef.provider is mock_provider

    def test_init_with_judge_provider(self):
        provider = MockProvider()
        judge = MockProvider()
        ef = EvalForge(provider=provider, judge_provider=judge)
        assert ef.provider is provider
        assert ef.judge_provider is judge

    def test_init_with_judge_provider_string(self):
        provider = MockProvider()
        with patch("evalforge.sdk.create_provider") as mock_create:
            mock_judge = MockProvider()
            mock_create.side_effect = [mock_judge]
            ef = EvalForge(provider=provider, judge_provider="anthropic")
            mock_create.assert_called_once_with("anthropic")
            assert ef.judge_provider is mock_judge

    def test_init_with_db_path(self):
        import os
        provider = MockProvider()
        original = os.environ.get("EVALFORGE_DB_PATH")
        try:
            ef = EvalForge(provider=provider, db_path="/tmp/test_evalforge_sdk.db")
            assert os.environ.get("EVALFORGE_DB_PATH") == "/tmp/test_evalforge_sdk.db"
        finally:
            if original is None:
                os.environ.pop("EVALFORGE_DB_PATH", None)
            else:
                os.environ["EVALFORGE_DB_PATH"] = original

    def test_init_repos_and_components(self):
        provider = MockProvider()
        ef = EvalForge(provider=provider)
        assert ef.eval_repo is not None
        assert ef.run_repo is not None
        assert ef.trace_repo is not None
        assert ef.diag_repo is not None
        assert ef.analyzer is not None
        assert ef.player is not None

    def test_create_evaluation(self):
        provider = MockProvider()
        ef = EvalForge(provider=provider)
        task = TaskDefinition(name="test-task", instructions="do something")
        eval_obj = ef.create_evaluation(
            name="test-eval",
            tasks=[task],
            description="test description",
            grading_type=GradingType.deterministic,
        )
        assert eval_obj.name == "test-eval"
        assert eval_obj.description == "test description"
        assert len(eval_obj.tasks) == 1
        assert eval_obj.tasks[0].name == "test-task"
        found = ef.eval_repo.find_by_id(eval_obj.id)
        assert found is not None
        assert found.name == "test-eval"

    def test_create_task(self):
        ef = EvalForge()
        task = ef.create_task(
            name="my-task",
            instructions="Do the thing",
            description="A task description",
            max_steps=30,
        )
        assert task.name == "my-task"
        assert task.instructions == "Do the thing"
        assert task.description == "A task description"
        assert task.max_steps == 30
        assert task.success_criteria == []

    def test_create_task_with_criteria(self):
        ef = EvalForge()
        criteria = [
            SuccessCriteria(description="must contain hello", type="contains", expected="hello"),
        ]
        task = ef.create_task(
            name="task-with-criteria",
            instructions="say hello",
            success_criteria=criteria,
        )
        assert len(task.success_criteria) == 1
        assert task.success_criteria[0].expected == "hello"

    def test_create_criterion(self):
        ef = EvalForge()
        criterion = ef.create_criterion(
            description="must contain hello",
            type="contains",
            expected="hello",
            weight=2.0,
        )
        assert criterion.description == "must contain hello"
        assert criterion.type == "contains"
        assert criterion.expected == "hello"
        assert criterion.weight == 2.0

    def test_create_criterion_defaults(self):
        ef = EvalForge()
        criterion = ef.create_criterion(description="some check")
        assert criterion.type == "contains"
        assert criterion.expected is None
        assert criterion.weight == 1.0

    def test_run(self):
        provider = MockProvider()
        provider.responses = iter(["hello world"])
        ef = EvalForge(provider=provider)
        task = TaskDefinition(name="test", instructions="say hello")
        eval_obj = ef.create_evaluation(name="test", tasks=[task])
        runs = ef.run(eval_obj)
        assert len(runs) == 1
        assert runs[0].status == "completed"
        assert runs[0].metrics.success_score >= 0.0

    def test_run_with_string_id(self):
        provider = MockProvider()
        provider.responses = iter(["hello"])
        ef = EvalForge(provider=provider)
        task = TaskDefinition(name="test", instructions="say hello")
        eval_obj = ef.create_evaluation(name="test", tasks=[task])
        runs = ef.run(eval_obj.id)
        assert len(runs) == 1
        assert runs[0].status == "completed"

    def test_run_with_agent_function(self):
        ef = EvalForge()
        task = TaskDefinition(name="test", instructions="do it")
        eval_obj = ef.create_evaluation(name="test", tasks=[task])

        def my_agent(instructions, criteria, record_step):
            record_step("thought", content="thinking")
            return "custom result"

        runs = ef.run(eval_obj, agent_function=my_agent)
        assert len(runs) == 1
        assert runs[0].status == "completed"

    def test_run_with_seed(self):
        provider = MockProvider()
        provider.responses = iter(["hello"])
        ef = EvalForge(provider=provider)
        task = TaskDefinition(name="test", instructions="say hello")
        eval_obj = ef.create_evaluation(name="test", tasks=[task])
        runs = ef.run(eval_obj, seed=42)
        assert len(runs) == 1

    def test_run_trials(self):
        provider = MockProvider()
        provider.responses = iter(["hello", "world"])
        ef = EvalForge(provider=provider)
        task = TaskDefinition(name="test", instructions="say hello")
        eval_obj = ef.create_evaluation(name="test", tasks=[task])
        results = ef.run_trials(eval_obj, n_trials=2)
        assert task.id in results
        assert results[task.id]["n_trials"] == 2
        assert "runs" in results[task.id]
        assert len(results[task.id]["runs"]) == 2

    def test_run_trials_single_trial(self):
        provider = MockProvider()
        provider.responses = iter(["hello"])
        ef = EvalForge(provider=provider)
        task = TaskDefinition(name="test", instructions="say hello")
        eval_obj = ef.create_evaluation(name="test", tasks=[task])
        results = ef.run_trials(eval_obj, n_trials=1)
        assert results[task.id]["n_trials"] == 1

    def test_get_run_found(self):
        ef = EvalForge(provider=MockProvider())
        run = Run(evaluation_id="e1", task_id="t1", status="completed")
        ef.run_repo.save(run)
        found = ef.get_run(run.id)
        assert found is not None
        assert found.id == run.id
        assert found.status == "completed"

    def test_get_run_not_found(self):
        ef = EvalForge(provider=MockProvider())
        found = ef.get_run("nonexistent")
        assert found is None

    def test_get_trace_found(self):
        ef = EvalForge(provider=MockProvider())
        trace = Trace(run_id="r1")
        ef.trace_repo.save(trace)
        found = ef.get_trace("r1")
        assert found is not None
        assert found.id == trace.id

    def test_get_trace_not_found(self):
        ef = EvalForge(provider=MockProvider())
        found = ef.get_trace("nonexistent")
        assert found is None

    def test_analyze_run_not_found(self):
        ef = EvalForge(provider=MockProvider())
        diags = ef.analyze("nonexistent")
        assert diags == []

    def test_analyze_no_trace(self):
        ef = EvalForge(provider=MockProvider())
        run = Run(evaluation_id="e1", task_id="t1", status="completed")
        ef.run_repo.save(run)
        diags = ef.analyze(run.id)
        assert diags == []

    def test_analyze_with_trace(self):
        ef = EvalForge(provider=MockProvider())
        run = Run(evaluation_id="e1", task_id="t1", status="completed")
        ef.run_repo.save(run)
        trace = Trace(run_id=run.id, steps=[
            Step(run_id=run.id, step_number=1, step_type=StepType.thought, content="thinking"),
        ])
        ef.trace_repo.save(trace)
        diags = ef.analyze(run.id)
        assert isinstance(diags, list)

    def test_list_evaluations_empty(self):
        ef = EvalForge(provider=MockProvider())
        evals = ef.list_evaluations()
        assert evals == []

    def test_list_evaluations(self):
        ef = EvalForge(provider=MockProvider())
        ef.create_evaluation(name="e1", tasks=[])
        ef.create_evaluation(name="e2", tasks=[])
        evals = ef.list_evaluations()
        assert len(evals) >= 2
        names = [e.name for e in evals]
        assert "e1" in names
        assert "e2" in names

    def test_list_runs_empty(self):
        ef = EvalForge(provider=MockProvider())
        runs = ef.list_runs()
        assert runs == []

    def test_list_runs(self):
        ef = EvalForge(provider=MockProvider())
        ef.run_repo.save(Run(evaluation_id="e1", task_id="t1", status="completed"))
        ef.run_repo.save(Run(evaluation_id="e2", task_id="t2", status="pending"))
        runs = ef.list_runs()
        assert len(runs) >= 2

    def test_list_runs_with_limit(self):
        ef = EvalForge(provider=MockProvider())
        for i in range(5):
            ef.run_repo.save(Run(evaluation_id=f"e{i}", task_id=f"t{i}", status="pending"))
        runs = ef.list_runs(limit=3)
        assert len(runs) <= 3

    def test_export_markdown(self):
        ef = EvalForge(provider=MockProvider())
        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        ef.run_repo.save(run)
        output = ef.export(run.id, format="markdown")
        assert isinstance(output, str)
        assert "EvalForge Run Report" in output
        assert run.id in output

    def test_export_json(self):
        ef = EvalForge(provider=MockProvider())
        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        ef.run_repo.save(run)
        import json
        output = ef.export(run.id, format="json")
        data = json.loads(output)
        assert data["run"]["status"] == "completed"
        assert data["run"]["id"] == run.id

    def test_export_html(self):
        ef = EvalForge(provider=MockProvider())
        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        ef.run_repo.save(run)
        output = ef.export(run.id, format="html")
        assert isinstance(output, str)
        assert len(output) > 0

    def test_export_default_format(self):
        ef = EvalForge(provider=MockProvider())
        run = Run(
            evaluation_id="e1", task_id="t1", status="completed",
            metrics=RunMetrics(
                success=True, success_score=0.85, step_count=5,
                tool_call_count=3, error_count=1, total_tokens=1000,
                total_cost_usd=0.01, total_latency_ms=5000.0,
                avg_step_latency_ms=1000.0, efficiency_score=75.0,
            ),
        )
        ef.run_repo.save(run)
        output = ef.export(run.id)
        assert "EvalForge Run Report" in output

    def test_reset_clears_data(self):
        ef = EvalForge(provider=MockProvider())
        ef.create_evaluation(name="test", tasks=[])
        assert len(ef.list_evaluations()) > 0
        ef.reset()
        assert len(ef.list_evaluations()) == 0

    def test_reset_then_create(self):
        ef = EvalForge(provider=MockProvider())
        ef.create_evaluation(name="before", tasks=[])
        ef.reset()
        ef.create_evaluation(name="after", tasks=[])
        evals = ef.list_evaluations()
        assert len(evals) == 1
        assert evals[0].name == "after"

    def test_serve(self):
        ef = EvalForge(provider=MockProvider())
        with patch("evalforge.dashboard.app.create_app") as mock_create_app:
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            ef.serve(host="127.0.0.1", port=7890, share=False)
            mock_create_app.assert_called_once()
            mock_app.launch.assert_called_once_with(
                server_name="127.0.0.1", server_port=7890, share=False,
            )
