"""Tests for storage layer."""

import pytest
from evalforge.storage.db import init_db, reset_db, get_db_path
from evalforge.storage.repository import (
    EvaluationRepository,
    RunRepository,
    TraceRepository,
    DiagnosticRepository,
    StepRepository,
)
from evalforge.models import Evaluation, TaskDefinition, Run, Trace, Step, StepType, Diagnostic


@pytest.fixture(autouse=True)
def db():
    init_db()
    yield
    reset_db()


class TestEvaluationRepository:
    def test_save_and_find(self):
        repo = EvaluationRepository()
        e = Evaluation(name="test", description="desc")
        repo.save(e)
        found = repo.find_by_id(e.id)
        assert found is not None
        assert found.name == "test"

    def test_find_all(self):
        repo = EvaluationRepository()
        repo.save(Evaluation(name="e1"))
        repo.save(Evaluation(name="e2"))
        all_evals = repo.find_all()
        assert len(all_evals) >= 2

    def test_delete(self):
        repo = EvaluationRepository()
        e = Evaluation(name="delete-me")
        repo.save(e)
        repo.delete(e.id)
        assert repo.find_by_id(e.id) is None

    def test_save_with_tasks(self):
        repo = EvaluationRepository()
        e = Evaluation(
            name="with-tasks",
            tasks=[TaskDefinition(name="t1", instructions="do something")],
        )
        repo.save(e)
        found = repo.find_by_id(e.id)
        assert found is not None
        assert len(found.tasks) == 1
        assert found.tasks[0].name == "t1"


class TestRunRepository:
    def test_save_and_find(self):
        repo = RunRepository()
        r = Run(evaluation_id="e1", task_id="t1", status="pending")
        repo.save(r)
        found = repo.find_by_id(r.id)
        assert found is not None
        assert found.status == "pending"

    def test_find_all(self):
        repo = RunRepository()
        repo.save(Run(evaluation_id="e1", task_id="t1"))
        repo.save(Run(evaluation_id="e2", task_id="t2"))
        all_runs = repo.find_all()
        assert len(all_runs) >= 2

    def test_find_by_evaluation(self):
        repo = RunRepository()
        repo.save(Run(evaluation_id="eval123", task_id="t1"))
        repo.save(Run(evaluation_id="eval123", task_id="t2"))
        repo.save(Run(evaluation_id="other", task_id="t3"))
        runs = repo.find_by_evaluation("eval123")
        assert len(runs) == 2

    def test_update_status(self):
        repo = RunRepository()
        r = Run(evaluation_id="e1", task_id="t1")
        repo.save(r)
        repo.update_status(r.id, "completed")
        found = repo.find_by_id(r.id)
        assert found.status == "completed"


class TestTraceRepository:
    def test_save_and_find(self):
        repo = TraceRepository()
        trace = Trace(run_id="r1")
        repo.save(trace)
        found = repo.find_by_run_id("r1")
        assert found is not None
        assert found.id == trace.id

    def test_save_with_steps(self):
        step_repo = StepRepository()
        repo = TraceRepository()
        trace = Trace(run_id="r1")
        step = Step(run_id="r1", step_number=1, step_type=StepType.thought, content="test")
        step_repo.save(step)
        trace.add_step(step)
        repo.save(trace)
        found = repo.find_by_run_id("r1")
        assert found is not None
        assert len(found.steps) == 1


class TestDiagnosticRepository:
    def test_save_and_find(self):
        repo = DiagnosticRepository()
        d = Diagnostic(run_id="r1", title="test diag")
        repo.save(d)
        found = repo.find_by_run_id("r1")
        assert len(found) == 1
        assert found[0].title == "test diag"
