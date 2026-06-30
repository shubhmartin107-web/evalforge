"""Tests for provider implementations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from evalforge.providers.factory import create_provider
from evalforge.providers.retry import with_retry, exponential_backoff, should_retry
from evalforge.providers.response import make_success_response, make_error_response


class TestRetry:
    def test_should_retry_429(self):
        assert should_retry(429) == True

    def test_should_retry_500(self):
        assert should_retry(500) == True

    def test_should_retry_200(self):
        assert should_retry(200) == False

    def test_should_retry_400(self):
        assert should_retry(400) == False

    def test_exponential_backoff_increases(self):
        t1 = exponential_backoff(0, base_delay=1.0, jitter=False)
        t2 = exponential_backoff(1, base_delay=1.0, jitter=False)
        t3 = exponential_backoff(2, base_delay=1.0, jitter=False)
        assert t1 < t2 < t3

    def test_exponential_backoff_respects_max(self):
        t = exponential_backoff(10, base_delay=1.0, max_delay=5.0, jitter=False)
        assert t <= 5.0

    def test_exponential_backoff_jitter(self):
        delays = [exponential_backoff(0, base_delay=1.0, jitter=True) for _ in range(5)]
        assert all(0.5 <= d <= 1.5 for d in delays)

    def test_with_retry_success_first_try(self):
        mock_fn = MagicMock(return_value="ok")
        decorated = with_retry(max_retries=3)(mock_fn)
        assert decorated() == "ok"
        mock_fn.assert_called_once()

    def test_with_retry_success_after_retries(self):
        mock_fn = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "ok"])
        decorated = with_retry(max_retries=3, base_delay=0.01)(mock_fn)
        assert decorated() == "ok"
        assert mock_fn.call_count == 3

    def test_with_retry_exhausted(self):
        mock_fn = MagicMock(side_effect=Exception("always fail"))
        decorated = with_retry(max_retries=2, base_delay=0.01)(mock_fn)
        with pytest.raises(Exception, match="always fail"):
            decorated()
        assert mock_fn.call_count == 3


class TestProviderFactory:
    def test_create_deepseek(self):
        p = create_provider("deepseek")
        assert p.name == "deepseek"
        assert p.default_model == "deepseek-chat"

    def test_create_gemini(self):
        p = create_provider("gemini")
        assert p.name == "gemini"

    def test_create_groq(self):
        p = create_provider("groq")
        assert p.name == "groq"

    def test_create_ollama(self):
        p = create_provider("ollama", base_url="http://localhost:11434")
        assert p.name == "ollama"

    def test_create_anthropic(self):
        p = create_provider("anthropic")
        assert p.name == "anthropic"

    def test_create_openai(self):
        p = create_provider("openai")
        assert p.name == "openai"

    def test_create_unknown(self):
        with pytest.raises((ValueError, Exception)):
            create_provider("unknown_provider_xyz")

    def test_create_from_string(self):
        p = create_provider("deepseek")
        assert p.name == "deepseek"


class TestProviderResponse:
    def test_make_success_response(self):
        resp = make_success_response(
            content="hello",
            model="test-model",
            input_tokens=10,
            output_tokens=20,
        )
        assert resp["content"] == "hello"
        assert resp["model"] == "test-model"
        assert resp["usage"]["input_tokens"] == 10
        assert resp["usage"]["output_tokens"] == 20
        assert resp["cost_usd"] >= 0

    def test_make_success_tool_calls(self):
        resp = make_success_response(
            content="",
            model="test-model",
            tool_calls=[{"id": "call_1", "function": {"name": "search"}}],
        )
        assert len(resp["tool_calls"]) == 1
        assert resp["tool_calls"][0]["function"]["name"] == "search"

    def test_make_error_response(self):
        resp = make_error_response(error="API key invalid", model="test-model")
        assert resp["error"] == "API key invalid"
        assert resp["content"] == ""
        assert resp["cost_usd"] == 0.0


class TestLLMJudgeIntegration:
    def test_model_grader_rule_fallback(self):
        from evalforge.core.graders.model_grader import ModelGrader, JudgeConfig
        grader = ModelGrader(config=JudgeConfig())
        result = grader.evaluate(
            "hello world",
            instructions="Say hello",
            criteria="Must say hello",
        )
        assert result.score >= 0.0

    def test_llm_judge_via_grading_type(self):
        from evalforge.core.grading import grade_task
        from evalforge.models import TaskDefinition, SuccessCriteria
        from evalforge.models.evaluation import GradingType

        task = TaskDefinition(
            name="test",
            instructions="say hello",
            success_criteria=[SuccessCriteria(description="says hello", type="contains", expected="hello")],
        )
        score, results = grade_task(task, "hello world", grading_type=GradingType.llm_as_judge)
        assert score >= 0.0
        assert len(results) > 0
