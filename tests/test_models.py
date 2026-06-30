"""Tests for EvalForge data models."""

from evalforge.models import (
    Evaluation, TaskDefinition, SuccessCriteria, GradingType,
    Run, Step, StepType, Trace,
    RunMetrics, BenchmarkMetrics,
    Diagnostic, Severity, DiagnosticCategory,
    ProviderConfig, AgentConfig, ProviderType,
)


class TestModels:
    def test_evaluation_creation(self):
        e = Evaluation(name="test", description="test eval")
        assert e.id is not None
        assert e.name == "test"
        assert e.grading_type == GradingType.deterministic
        assert len(e.tasks) == 0

    def test_task_definition(self):
        t = TaskDefinition(
            name="my-task",
            instructions="Do something",
            success_criteria=[SuccessCriteria(description="check", type="contains", expected="ok")],
        )
        assert t.name == "my-task"
        assert len(t.success_criteria) == 1
        assert t.success_criteria[0].expected == "ok"

    def test_success_criteria(self):
        sc = SuccessCriteria(description="must contain x", type="contains", expected="x")
        assert sc.type == "contains"
        assert sc.weight == 1.0

    def test_run_creation(self):
        r = Run(evaluation_id="e1", task_id="t1")
        assert r.status == "pending"
        assert r.metrics is not None
        assert r.metrics.success == False

    def test_step_creation(self):
        s = Step(run_id="r1", step_number=1, step_type=StepType.thought, content="thinking")
        assert s.step_type == StepType.thought
        assert s.content == "thinking"

    def test_trace(self):
        trace = Trace(run_id="r1")
        step = Step(run_id="r1", step_number=1, step_type=StepType.thought, content="test")
        trace.add_step(step)
        assert len(trace.steps) == 1
        assert trace.step_count() == 1

    def test_run_metrics(self):
        m = RunMetrics(
            success=True,
            success_score=0.85,
            total_cost_usd=0.05,
            total_tokens=1500,
            step_count=10,
        )
        assert m.success == True
        assert m.success_score == 0.85

    def test_benchmark_metrics(self):
        bm = BenchmarkMetrics(total_runs=10, successful_runs=7, avg_success_rate=0.7)
        assert bm.total_runs == 10
        assert bm.successful_runs == 7

    def test_diagnostic(self):
        d = Diagnostic(
            run_id="r1",
            severity=Severity.warning,
            category=DiagnosticCategory.looping,
            title="Loop detected",
            description="Agent looped 5 times",
            recommendation="Add termination condition",
        )
        assert d.severity == Severity.warning
        assert d.category == DiagnosticCategory.looping

    def test_provider_config(self):
        pc = ProviderConfig(provider=ProviderType.deepseek, model="deepseek-chat")
        assert pc.provider == ProviderType.deepseek
        assert pc.temperature == 0.7

    def test_agent_config(self):
        ac = AgentConfig(name="test-agent")
        assert ac.name == "test-agent"
        assert ac.max_steps == 50

    def test_evaluation_with_tasks(self):
        tasks = [
            TaskDefinition(name="t1", instructions="do 1"),
            TaskDefinition(name="t2", instructions="do 2"),
        ]
        e = Evaluation(name="multi", tasks=tasks)
        assert len(e.tasks) == 2

    def test_grading_type_enum(self):
        assert GradingType.deterministic.value == "deterministic"
        assert GradingType.llm_as_judge.value == "llm_as_judge"

    def test_step_type_enum(self):
        assert StepType.thought.value == "thought"
        assert StepType.tool_call.value == "tool_call"
