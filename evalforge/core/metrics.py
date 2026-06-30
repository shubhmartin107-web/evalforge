import math

from ..models.metrics import RunMetrics
from ..models.trace import Step, StepType
from ..utils.cost import estimate_cost


def compute_metrics(
    steps: list[Step],
    success: bool = False,
    success_score: float = 0.0,
    model: str = "deepseek-chat",
) -> RunMetrics:
    if not steps:
        return RunMetrics(
            success=success,
            success_score=success_score,
        )

    total_tokens = sum(s.token_count for s in steps)
    input_tokens = sum(s.input_tokens for s in steps)
    output_tokens = sum(s.output_tokens for s in steps)

    total_cost = sum(s.cost_usd for s in steps)
    if total_cost == 0.0 and total_tokens > 0:
        if input_tokens > 0 or output_tokens > 0:
            total_cost = estimate_cost(
                input_tokens or total_tokens // 2,
                output_tokens or total_tokens // 2,
                model,
            )

    total_latency = sum(s.latency_ms for s in steps)
    step_count = len(steps)
    tool_calls = len([s for s in steps if s.step_type == StepType.tool_call])
    errors = len([s for s in steps if s.step_type == StepType.error])

    avg_step_latency = total_latency / step_count if step_count > 0 else 0.0
    efficiency = success_score / max(step_count, 1) * 100.0
    cost_efficiency = success_score / max(total_cost, 0.0001)
    token_efficiency = success_score / max(total_tokens, 1) * 10000.0

    return RunMetrics(
        success=success,
        success_score=success_score,
        total_cost_usd=round(total_cost, 6),
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_latency_ms=round(total_latency, 2),
        avg_step_latency_ms=round(avg_step_latency, 2),
        step_count=step_count,
        tool_call_count=tool_calls,
        error_count=errors,
        reasoning_quality_score=None,
        efficiency_score=round(efficiency, 4),
        cost_efficiency_score=round(cost_efficiency, 4),
        token_efficiency=round(token_efficiency, 4),
    )


def compute_benchmark_metrics(runs_metrics: list[RunMetrics]) -> dict:
    n = len(runs_metrics)
    if n == 0:
        return {}

    successful = sum(1 for m in runs_metrics if m.success)
    return {
        "total_runs": n,
        "successful_runs": successful,
        "failed_runs": n - successful,
        "avg_success_rate": round(successful / n, 4),
        "avg_cost_usd": round(sum(m.total_cost_usd for m in runs_metrics) / n, 6),
        "avg_latency_ms": round(sum(m.total_latency_ms for m in runs_metrics) / n, 2),
        "avg_tokens": round(sum(m.total_tokens for m in runs_metrics) / n, 2),
        "avg_steps": round(sum(m.step_count for m in runs_metrics) / n, 2),
        "total_cost_usd": round(sum(m.total_cost_usd for m in runs_metrics), 6),
    }


def compute_pass_at_k(run_results: list[bool], k: int | None = None) -> float:
    """pass@k: probability at least one of k trials succeeds.

    Uses the unbiased estimator from Chen et al. (2021):
    pass@k = 1 - C(n - c, k) / C(n, k)
    where n = total trials, c = successful trials.
    """
    n = len(run_results)
    c = sum(1 for r in run_results if r)
    if k is None:
        k = min(n, 5)

    if n == 0 or c == 0:
        return 0.0
    if k >= n:
        return 1.0 if c > 0 else 0.0

    try:
        from math import comb

        return 1.0 - comb(n - c, k) / comb(n, k)
    except (ValueError, OverflowError):
        return 1.0 if c > 0 else 0.0


def compute_pass_power_k(run_results: list[bool], k: int | None = None) -> float:
    """pass^k: probability all k trials succeed (for production reliability)."""
    n = len(run_results)
    if k is None:
        k = min(n, 5)

    if n == 0:
        return 0.0
    if k > n:
        return 1.0 if all(run_results) else 0.0

    successes = sum(1 for r in run_results if r)
    if successes < k:
        return 0.0

    from math import comb

    try:
        return comb(successes, k) / comb(n, k)
    except (ValueError, OverflowError):
        return 1.0 if all(run_results) else 0.0


def compute_trial_metrics(trial_runs: list[RunMetrics]) -> dict:
    """Aggregate metrics across multiple trials for a single task."""
    if not trial_runs:
        return {}

    scores = [m.success_score for m in trial_runs]
    successes = [m.success for m in trial_runs]

    return {
        "n_trials": len(trial_runs),
        "n_successes": sum(successes),
        "pass_at_1": compute_pass_at_k(successes, k=1),
        "pass_at_3": compute_pass_at_k(successes, k=3),
        "pass_at_5": compute_pass_at_k(successes, k=5),
        "pass_power_3": compute_pass_power_k(successes, k=3),
        "pass_power_5": compute_pass_power_k(successes, k=5),
        "avg_score": sum(scores) / len(scores),
        "max_score": max(scores),
        "min_score": min(scores),
        "std_score": _std(scores),
        "total_cost": sum(m.total_cost_usd for m in trial_runs),
        "avg_cost": sum(m.total_cost_usd for m in trial_runs) / len(trial_runs),
    }


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)
