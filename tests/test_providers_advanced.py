"""Advanced mock-based provider tests using httpx.MockTransport."""

import json
import pytest
import httpx
from evalforge.providers.factory import create_provider
from evalforge.providers.response import make_success_response, make_error_response
from evalforge.storage.db import init_db, reset_db


@pytest.fixture(autouse=True)
def db_setup():
    init_db()
    yield
    reset_db()


# ---------------------------------------------------------------------------
# Response helpers – additional scenarios beyond existing tests
# ---------------------------------------------------------------------------

class TestProviderResponseAdvanced:

    def test_make_success_with_raw(self):
        raw = {"id": "chatcmpl-xyz", "object": "chat.completion"}
        resp = make_success_response(
            content="Hi", model="m", input_tokens=5, output_tokens=8, raw=raw,
        )
        assert resp["raw"] == raw
        assert resp["raw"]["id"] == "chatcmpl-xyz"

    def test_make_success_empty_content(self):
        resp = make_success_response(content="", model="m")
        assert resp["content"] == ""
        assert resp["tool_calls"] == []

    def test_make_error_with_tokens(self):
        resp = make_error_response(error="rate limited", model="m", input_tokens=10, output_tokens=5)
        assert resp["error"] == "rate limited"
        assert resp["usage"]["input_tokens"] == 10
        assert resp["usage"]["output_tokens"] == 5
        assert resp["cost_usd"] == 0.0

    def test_make_error_no_tokens(self):
        resp = make_error_response(error="fail", model="m")
        assert resp["usage"] == {"input_tokens": 0, "output_tokens": 0}
        assert resp["raw"] == {}


# ---------------------------------------------------------------------------
# Factory – string-based creation
# ---------------------------------------------------------------------------

class TestFactoryCreateProvider:

    def test_create_deepseek_with_api_key(self):
        p = create_provider("deepseek", api_key="sk-test")
        assert p.name == "deepseek"
        assert p.api_key == "sk-test"

    def test_create_gemini_with_api_key(self):
        p = create_provider("gemini", api_key="gk-test")
        assert p.name == "gemini"
        assert p.api_key == "gk-test"

    def test_create_groq_with_api_key(self):
        p = create_provider("groq", api_key="gsk-test")
        assert p.name == "groq"
        assert p.api_key == "gsk-test"

    def test_create_ollama_with_base_url(self):
        p = create_provider("ollama", base_url="http://custom:11434")
        assert p.name == "ollama"
        assert p.base_url == "http://custom:11434"

    def test_create_anthropic_with_api_key(self):
        p = create_provider("anthropic", api_key="sk-ant-test")
        assert p.name == "anthropic"
        assert p.api_key == "sk-ant-test"

    def test_create_openai_with_api_key(self):
        p = create_provider("openai", api_key="sk-openai-test")
        assert p.name == "openai"
        assert p.api_key == "sk-openai-test"


# ---------------------------------------------------------------------------
# DeepSeekProvider.chat
# ---------------------------------------------------------------------------

class TestDeepSeekChat:

    def test_chat_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["model"] == "deepseek-chat"
            assert body["messages"] == [{"role": "user", "content": "hello"}]
            assert request.headers["Authorization"] == "Bearer sk-deepseek"
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Hi there!", "tool_calls": []}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20},
                },
            )

        provider = create_provider("deepseek", api_key="sk-deepseek")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hello"}])
        assert resp["content"] == "Hi there!"
        assert resp["model"] == "deepseek-chat"
        assert resp["usage"]["input_tokens"] == 10
        assert resp["usage"]["output_tokens"] == 20
        assert "raw" in resp

    def test_count_tokens(self):
        provider = create_provider("deepseek", api_key="sk-d")
        n = provider.count_tokens("hello world")
        assert n > 0


# ---------------------------------------------------------------------------
# GeminiProvider.chat
# ---------------------------------------------------------------------------

class TestGeminiChat:

    def test_chat_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["contents"][0]["parts"][0]["text"] == "hello"
            assert request.headers["x-goog-api-key"] == "gk-test"
            return httpx.Response(
                200,
                json={
                    "candidates": [{"content": {"parts": [{"text": "Hello Gemini!"}]}}],
                    "usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 15},
                },
            )

        provider = create_provider("gemini", api_key="gk-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hello"}])
        assert resp["content"] == "Hello Gemini!"
        assert resp["usage"]["input_tokens"] == 7
        assert resp["usage"]["output_tokens"] == 15

    def test_count_tokens(self):
        provider = create_provider("gemini", api_key="gk-t")
        n = provider.count_tokens("hello world")
        assert n > 0


# ---------------------------------------------------------------------------
# GroqProvider.chat
# ---------------------------------------------------------------------------

class TestGroqChat:

    def test_chat_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["model"] == "mixtral-8x7b-32768"
            assert request.headers["Authorization"] == "Bearer gsk-test"
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Fast inference!"}}],
                    "usage": {"prompt_tokens": 8, "completion_tokens": 12},
                },
            )

        provider = create_provider("groq", api_key="gsk-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hi"}])
        assert resp["content"] == "Fast inference!"
        assert resp["usage"]["input_tokens"] == 8
        assert resp["usage"]["output_tokens"] == 12

    def test_count_tokens(self):
        provider = create_provider("groq", api_key="gsk-t")
        n = provider.count_tokens("hello world")
        assert n > 0


# ---------------------------------------------------------------------------
# OllamaProvider.chat
# ---------------------------------------------------------------------------

class TestOllamaChat:

    def test_chat_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["model"] == "llama3.1"
            assert body["stream"] is False
            return httpx.Response(
                200,
                json={
                    "model": "llama3.1",
                    "message": {"content": "Local model reply"},
                    "done": True,
                },
            )

        provider = create_provider("ollama", base_url="http://localhost:11434")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hello"}])
        assert resp["content"] == "Local model reply"
        assert resp["model"] == "llama3.1"
        assert resp["usage"]["input_tokens"] > 0
        assert resp["usage"]["output_tokens"] > 0

    def test_count_tokens(self):
        provider = create_provider("ollama")
        n = provider.count_tokens("hello world")
        assert n > 0


# ---------------------------------------------------------------------------
# AnthropicProvider.chat
# ---------------------------------------------------------------------------

class TestAnthropicChat:

    def test_chat_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["model"] == "claude-3-5-haiku-20241022"
            assert "system" not in body
            assert request.headers["x-api-key"] == "sk-ant-test"
            assert request.headers["anthropic-version"] == "2023-06-01"
            return httpx.Response(
                200,
                json={
                    "content": [{"type": "text", "text": "Claude says hello"}],
                    "usage": {"input_tokens": 12, "output_tokens": 25},
                },
            )

        provider = create_provider("anthropic", api_key="sk-ant-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hello"}])
        assert resp["content"] == "Claude says hello"
        assert resp["usage"]["input_tokens"] == 12
        assert resp["usage"]["output_tokens"] == 25

    def test_chat_with_system_message(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["system"] == "Be helpful"
            return httpx.Response(
                200,
                json={
                    "content": [{"type": "text", "text": "Got it!"}],
                    "usage": {"input_tokens": 5, "output_tokens": 3},
                },
            )

        provider = create_provider("anthropic", api_key="sk-ant-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "ok"},
        ])
        assert resp["content"] == "Got it!"

    def test_chat_with_thinking_block(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["thinking"] == {"type": "enabled", "budget_tokens": 1000}
            return httpx.Response(
                200,
                json={
                    "content": [
                        {"type": "thinking", "thinking": "Let me think..."},
                        {"type": "text", "text": "Here is the answer."},
                    ],
                    "usage": {"input_tokens": 10, "output_tokens": 30},
                },
            )

        provider = create_provider("anthropic", api_key="sk-ant-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat(
            [{"role": "user", "content": "think hard"}],
            thinking_budget=1000,
        )
        assert "<thinking>Let me think...</thinking>" in resp["content"]
        assert "Here is the answer." in resp["content"]

    def test_chat_with_tool_use(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_01",
                            "name": "get_weather",
                            "input": {"city": "NYC"},
                        },
                    ],
                    "usage": {"input_tokens": 15, "output_tokens": 10},
                },
            )

        provider = create_provider("anthropic", api_key="sk-ant-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "weather?"}])
        assert len(resp["tool_calls"]) == 1
        assert resp["tool_calls"][0]["function"]["name"] == "get_weather"

    def test_count_tokens(self):
        provider = create_provider("anthropic", api_key="sk-ant-t")
        n = provider.count_tokens("hello world")
        assert n > 0


# ---------------------------------------------------------------------------
# AnthropicProvider.chat_stream
# ---------------------------------------------------------------------------

class TestAnthropicChatStream:

    def test_chat_stream_yields_lines(self):
        sse_body = (
            'event: message_start\n'
            'data: {"type":"message_start","message":{"id":"msg_1"}}\n\n'
            'event: content_block_delta\n'
            'data: {"type":"content_block_delta","delta":{"text":"Hello"}}\n\n'
            'event: message_stop\n'
            'data: {"type":"message_stop"}\n\n'
        )

        def handler(request: httpx.Request) -> httpx.Response:
            assert "stream" in json.loads(request.read())
            return httpx.Response(200, text=sse_body)

        provider = create_provider("anthropic", api_key="sk-ant-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        lines = list(provider.chat_stream([{"role": "user", "content": "hi"}]))
        assert len(lines) >= 3
        assert any('"type":"message_start"' in l for l in lines)
        assert any('"type":"message_stop"' in l for l in lines)

    def test_chat_stream_skips_empty_lines(self):
        sse_body = (
            'event: ping\n'
            'data: {}\n\n'
            '\n'
            'event: message_stop\n'
            'data: {"type":"message_stop"}\n\n'
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=sse_body)

        provider = create_provider("anthropic", api_key="sk-ant-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        lines = list(provider.chat_stream([{"role": "user", "content": "hi"}]))
        assert all(l.strip() for l in lines)


# ---------------------------------------------------------------------------
# OpenAIProvider.chat
# ---------------------------------------------------------------------------

class TestOpenAIChat:

    def test_chat_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["model"] == "gpt-4o-mini"
            assert request.headers["Authorization"] == "Bearer sk-openai-test"
            assert request.url.path == "/v1/chat/completions"
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "OpenAI reply", "tool_calls": []}}],
                    "usage": {"prompt_tokens": 9, "completion_tokens": 18},
                },
            )

        provider = create_provider("openai", api_key="sk-openai-test")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hello"}])
        assert resp["content"] == "OpenAI reply"
        assert resp["usage"]["input_tokens"] == 9
        assert resp["usage"]["output_tokens"] == 18

    def test_chat_custom_base_url(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url).startswith("https://custom.openai.com")
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Custom URL"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            )

        provider = create_provider("openai", api_key="sk-test", base_url="https://custom.openai.com/v1")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hi"}])
        assert resp["content"] == "Custom URL"

    def test_count_tokens(self):
        provider = create_provider("openai", api_key="sk-t")
        n = provider.count_tokens("hello world")
        assert n > 0


# ---------------------------------------------------------------------------
# @with_retry – HTTP-level retries via MockTransport
# ---------------------------------------------------------------------------

class TestWithRetryHTTP:

    def test_retry_eventually_succeeds(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return httpx.Response(500, json={"error": "server error"})
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "finally ok"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            )

        provider = create_provider("deepseek", api_key="sk-retry")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        resp = provider.chat([{"role": "user", "content": "hello"}])
        assert resp["content"] == "finally ok"
        assert call_count == 3

    def test_retry_exhausted_raises(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"error": "unavailable"})

        provider = create_provider("deepseek", api_key="sk-retry")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        with pytest.raises(httpx.HTTPStatusError):
            provider.chat([{"role": "user", "content": "hello"}])

    def test_retry_non_retryable_status(self):
        """400 is not retryable; retry logic still retries, verify final raise."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "bad request"})

        provider = create_provider("deepseek", api_key="sk-retry")
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        with pytest.raises(httpx.HTTPStatusError):
            provider.chat([{"role": "user", "content": "hello"}])
