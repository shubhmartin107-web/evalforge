def estimate_tokens(text: str) -> int:
    """Rough token estimation (~4 chars per token for English text)."""
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def count_tokens(text: str, model: str = "default") -> int:
    return estimate_tokens(text)
