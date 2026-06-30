"""Tests for safety benchmark suite."""

from evalforge.benchmarks.safety.sycophancy import create_sycophancy_eval
from evalforge.benchmarks.safety.bias import create_bias_eval
from evalforge.benchmarks.safety.harmful_output import create_harmful_output_eval
from evalforge.benchmarks.safety.jailbreak import create_jailbreak_eval
from evalforge.benchmarks.registry import _safety_benchmarks


class TestSycophancyEval:
    def test_create(self):
        eval = create_sycophancy_eval()
        assert eval.name == "sycophancy-detection"
        assert len(eval.tasks) == 2
        assert "safety" in eval.tags
        assert "sycophancy" in eval.tags

    def test_tasks_have_criteria(self):
        eval = create_sycophancy_eval()
        for task in eval.tasks:
            assert len(task.success_criteria) > 0
            assert "safety" in task.tags


class TestBiasEval:
    def test_create(self):
        eval = create_bias_eval()
        assert eval.name == "bias-detection"
        assert len(eval.tasks) == 2

    def test_tags(self):
        eval = create_bias_eval()
        assert "fairness" in eval.tags


class TestHarmfulOutputEval:
    def test_create(self):
        eval = create_harmful_output_eval()
        assert eval.name == "harmful-output-detection"
        assert len(eval.tasks) == 3

    def test_refusal_checks(self):
        eval = create_harmful_output_eval()
        for task in eval.tasks:
            has_refusal = any("cannot" in c.expected for c in task.success_criteria)
            has_regex = any(c.type == "regex" for c in task.success_criteria)
            assert has_refusal or has_regex


class TestJailbreakEval:
    def test_create(self):
        eval = create_jailbreak_eval()
        assert eval.name == "jailbreak-resistance"
        assert len(eval.tasks) == 3

    def test_prompt_injection_tags(self):
        eval = create_jailbreak_eval()
        for task in eval.tasks:
            assert "prompt-injection" in task.tags


class TestRegistry:
    def test_safety_benchmarks_registered(self):
        benchmarks = _safety_benchmarks()
        assert len(benchmarks) == 4
        names = [b.name for b in benchmarks]
        assert "sycophancy-detection" in names
        assert "bias-detection" in names
        assert "harmful-output-detection" in names
        assert "jailbreak-resistance" in names

    def test_env_snapshot_blocklist(self):
        import os
        from evalforge.core.session import capture_env_snapshot, _ENV_BLOCKLIST

        os.environ["__TEST_MY_KEY__"] = "should_not_appear"
        os.environ["__TEST_MY_TOKEN__"] = "should_not_appear"
        os.environ["__TEST_SAFE_VAR__"] = "should_appear"
        try:
            snapshot = capture_env_snapshot()
            env_vars = snapshot["env_vars"]
            assert "__TEST_MY_KEY__" not in env_vars
            assert "__TEST_MY_TOKEN__" not in env_vars
            assert "__TEST_SAFE_VAR__" in env_vars
        finally:
            del os.environ["__TEST_MY_KEY__"]
            del os.environ["__TEST_MY_TOKEN__"]
            del os.environ["__TEST_SAFE_VAR__"]
