from pydantic import BaseModel


class RunMetrics(BaseModel):
    success: bool = False
    success_score: float = 0.0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_latency_ms: float = 0.0
    avg_step_latency_ms: float = 0.0
    step_count: int = 0
    tool_call_count: int = 0
    error_count: int = 0
    reasoning_quality_score: float | None = None
    efficiency_score: float = 0.0
    cost_efficiency_score: float = 0.0
    token_efficiency: float = 0.0


class BenchmarkMetrics(BaseModel):
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    avg_success_rate: float = 0.0
    avg_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    avg_tokens: float = 0.0
    avg_steps: float = 0.0
    total_cost_usd: float = 0.0
