from typing import Any

from ..utils.cost import estimate_cost


def make_success_response(
    content: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    tool_calls: list[dict] | None = None,
    raw: dict | None = None,
) -> dict[str, Any]:
    cost = estimate_cost(input_tokens, output_tokens, model)
    return {
        "content": content,
        "tool_calls": tool_calls or [],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
        "cost_usd": round(cost, 8),
        "model": model,
        "raw": raw or {},
    }


def make_error_response(
    error: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> dict[str, Any]:
    return {
        "content": "",
        "tool_calls": [],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
        "cost_usd": 0.0,
        "error": error,
        "model": model,
        "raw": {},
    }
