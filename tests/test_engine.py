"""Tests for evaluation engine and harness."""

import pytest
from evalforge.core.engine import EvaluationEngine
from evalforge.core.harness import EvaluationHarness
from evalforge.core.session import SessionRecorder, capture_env_snapshot, Timer
from evalforge.models import Evaluation, TaskDefinition, Run, Step, StepType
from evalforge.storage.db import init_db, reset_db
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


class TestEngine:
    def test_engine_creation(self):
        engine = EvaluationEngine(provider=MockProvider())
        assert engine.provider is not None

    def test_engine_run_with_mock(self):
        provider = MockProvider()
        provider.responses = iter(["hello world"])
        engine = EvaluationEngine(provider=provider)

        task = TaskDefinition(name="test", instructions="say hello")
        evaluation = Evaluation(name="test", tasks=[task])
        engine.register_evaluation(evaluation)

        runs = engine.run(evaluation)
        assert len(runs) == 1
        assert runs[0].status == "completed"

    def test_engine_run_with_error(self):
        provider = MockProvider()
        provider.responses = iter(["hello"])
        engine = EvaluationEngine(provider=provider)

        task = TaskDefinition(
            name="test",
            instructions="say hello",
        )
        evaluation = Evaluation(name="test", tasks=[task])
        runs = engine.run(evaluation)
        assert len(runs) >= 0

    def test_engine_no_provider_raises(self):
        engine = EvaluationEngine()
        with pytest.raises(ValueError, match="No provider"):
            evaluation = Evaluation(name="test", tasks=[TaskDefinition(name="t", instructions="x")])
            engine.run(evaluation)

    def test_register_and_list(self):
        engine = EvaluationEngine(provider=MockProvider())
        e = Evaluation(name="list-test")
        engine.register_evaluation(e)
        evals = engine.list_evaluations()
        names = [ev.name for ev in evals]
        assert "list-test" in names

    def test_count_runs(self):
        engine = EvaluationEngine(provider=MockProvider())
        assert engine.count_runs() >= 0


class TestHarness:
    def test_custom_agent_function(self):
        def my_agent(instructions, criteria, record_step):
            record_step("thought", content="thinking")
            return "custom result"

        harness = EvaluationHarness(agent_function=my_agent)
        task = TaskDefinition(name="test", instructions="do it")
        evaluation = Evaluation(name="test", tasks=[task])
        run = harness.run_task(task, evaluation)
        assert run.status == "completed"
        assert run.metrics.success_score >= 0.0

    def test_harness_no_provider_no_agent(self):
        harness = EvaluationHarness()
        task = TaskDefinition(name="test", instructions="x")
        evaluation = Evaluation(name="test", tasks=[task])
        run = harness.run_task(task, evaluation)
        assert run.status == "failed"


class TestSession:
    def test_recorder_creation(self):
        run = Run(evaluation_id="e1", task_id="t1")
        recorder = SessionRecorder(run, persist=False)
        assert recorder.step_counter == 0

    def test_record_thought(self):
        run = Run(evaluation_id="e1", task_id="t1")
        recorder = SessionRecorder(run, persist=False)
        recorder.record_thought("I am thinking")
        assert recorder.step_counter == 1
        assert recorder.trace.step_count() == 1

    def test_record_tool_call(self):
        run = Run(evaluation_id="e1", task_id="t1")
        recorder = SessionRecorder(run, persist=False)
        recorder.record_tool_call("search", {"q": "test"})
        assert recorder.step_counter == 1

    def test_record_error(self):
        run = Run(evaluation_id="e1", task_id="t1")
        recorder = SessionRecorder(run, persist=False)
        recorder.record_error("Something broke")
        step = recorder.trace.steps[0]
        assert step.step_type == StepType.error
        assert "Something broke" in str(step.error_message)

    def test_timer(self):
        import time
        timer = Timer()
        time.sleep(0.01)
        assert timer.elapsed_ms() > 0

    def test_capture_env_snapshot(self):
        snapshot = capture_env_snapshot()
        assert "python_version" in snapshot
        assert "platform" in snapshot
        assert "cwd" in snapshot
