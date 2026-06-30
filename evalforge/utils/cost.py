MODEL_PRICING: dict[str, dict[str, float]] = {
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.00030},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.00500},
    "gemini-2.0-flash": {"input": 0.00010, "output": 0.00040},
    "mixtral-8x7b-32768": {"input": 0.00024, "output": 0.00024},
    "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079},
    "llama-3.1-8b-instant": {"input": 0.00018, "output": 0.00018},
    "claude-3-5-sonnet-20241022": {"input": 0.00300, "output": 0.01500},
    "claude-3-5-haiku-20241022": {"input": 0.00080, "output": 0.00400},
    "gpt-4o": {"input": 0.00250, "output": 0.01000},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "ollama/default": {"input": 0.00000, "output": 0.00000},
}


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "deepseek-chat") -> float:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("deepseek-chat"))
    if pricing is None:
        return 0.0
    return (input_tokens * pricing["input"] / 1000) + (output_tokens * pricing["output"] / 1000)


def format_cost(cost_usd: float) -> str:
    if cost_usd < 0.001:
        return f"${cost_usd:.6f}"
    return f"${cost_usd:.4f}"
