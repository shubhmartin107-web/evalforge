"""Tests for grading engine."""

from evalforge.core.grading import grade_task, _evaluate_criterion
from evalforge.models import TaskDefinition, SuccessCriteria


class TestGrading:
    def test_exact_match_pass(self):
        sc = SuccessCriteria(description="exact match", type="exact_match", expected="hello world")
        result = _evaluate_criterion(sc, "hello world")
        assert result.passed == True
        assert result.score == 1.0

    def test_exact_match_fail(self):
        sc = SuccessCriteria(description="exact match", type="exact_match", expected="hello world")
        result = _evaluate_criterion(sc, "hello")
        assert result.passed == False

    def test_contains_pass(self):
        sc = SuccessCriteria(description="contains hello", type="contains", expected="hello")
        result = _evaluate_criterion(sc, "hello world")
        assert result.passed == True

    def test_contains_fail(self):
        sc = SuccessCriteria(description="contains hello", type="contains", expected="hello")
        result = _evaluate_criterion(sc, "goodbye world")
        assert result.passed == False

    def test_regex_pass(self):
        sc = SuccessCriteria(description="match number", type="regex", expected=r"\d+\.\d+")
        result = _evaluate_criterion(sc, "value is 3.14")
        assert result.passed == True

    def test_regex_fail(self):
        sc = SuccessCriteria(description="match number", type="regex", expected=r"\d+\.\d+")
        result = _evaluate_criterion(sc, "value is three")
        assert result.passed == False

    def test_grade_task_single_criterion(self):
        task = TaskDefinition(
            name="test",
            instructions="do x",
            success_criteria=[
                SuccessCriteria(description="contains ok", type="contains", expected="ok"),
            ],
        )
        score, results = grade_task(task, "this is ok")
        assert score == 1.0
        assert results[0]["passed"] == True

    def test_grade_task_multi_criteria(self):
        task = TaskDefinition(
            name="test",
            instructions="do x",
            success_criteria=[
                SuccessCriteria(description="c1", type="contains", expected="hello", weight=1.0),
                SuccessCriteria(description="c2", type="contains", expected="world", weight=1.0),
            ],
        )
        score, results = grade_task(task, "hello universe")
        assert score == 0.5
        assert results[0]["passed"] == True
        assert results[1]["passed"] == False

    def test_grade_empty_output(self):
        task = TaskDefinition(
            name="test",
            instructions="do x",
            success_criteria=[SuccessCriteria(description="c1", type="contains", expected="x")],
        )
        score, results = grade_task(task, "")
        assert score == 0.0

    def test_grade_weighted(self):
        task = TaskDefinition(
            name="test",
            instructions="do x",
            success_criteria=[
                SuccessCriteria(description="c1", type="contains", expected="hello", weight=2.0),
                SuccessCriteria(description="c2", type="contains", expected="world", weight=1.0),
            ],
        )
        score, results = grade_task(task, "hello world")
        assert score == 1.0

        score2, _ = grade_task(task, "hello universe")
        assert score2 == 2.0 / 3.0

    def test_llm_judge_criterion_returns_message(self):
        sc = SuccessCriteria(description="llm judge", type="llm_judge", expected="pass")
        result = _evaluate_criterion(sc, "any output")
        assert result.passed == False
        assert "require GradingType" in result.description

    def test_llm_as_judge_grading_type(self):
        task = TaskDefinition(
            name="test",
            instructions="Say hello world",
            success_criteria=[SuccessCriteria(description="says hello", type="contains", expected="hello")],
        )
        from evalforge.models.evaluation import GradingType
        score, results = grade_task(task, "hello world", grading_type=GradingType.llm_as_judge)
        assert score >= 0.0

    def test_callable_criterion_no_fn(self):
        sc = SuccessCriteria(description="custom check", type="callable", expected="anything")
        result = _evaluate_criterion(sc, "some output")
        assert result.passed == False

    def test_callable_criterion_with_fn(self):
        sc = SuccessCriteria(
            description="length > 5",
            type="callable",
            metadata={"fn": lambda x: len(x) > 5},
        )
        result = _evaluate_criterion(sc, "hello world")
        assert result.passed == True

        result2 = _evaluate_criterion(sc, "hi")
        assert result2.passed == False
