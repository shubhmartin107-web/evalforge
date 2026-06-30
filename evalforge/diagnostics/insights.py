from ..models.diagnostics import Diagnostic
from ..models.run import Run


def generate_insights(run: Run, diagnostics: list[Diagnostic]) -> str:
    parts = []

    if run.status == "completed" and run.metrics.success:
        parts.append(f"✅ Run completed successfully (score: {run.metrics.success_score:.2f})")
    else:
        parts.append(f"❌ Run failed (score: {run.metrics.success_score:.2f})")

    parts.append("")

    if run.metrics.step_count > 0:
        parts.append(
            f"**Execution**: {run.metrics.step_count} steps, {run.metrics.tool_call_count} tool calls, {run.metrics.error_count} errors"
        )
        parts.append(
            f"**Tokens**: {run.metrics.total_tokens} total ({run.metrics.input_tokens} in / {run.metrics.output_tokens} out)"
        )
        parts.append(f"**Cost**: ${run.metrics.total_cost_usd:.6f}")
        parts.append(
            f"**Latency**: {run.metrics.total_latency_ms:.0f}ms ({run.metrics.avg_step_latency_ms:.0f}ms/step)"
        )
        parts.append(f"**Efficiency**: {run.metrics.efficiency_score:.1f}%")

    if diagnostics:
        parts.append("")
        parts.append("**Diagnostics:**")
        for d in diagnostics:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}
            parts.append(f"  {icon.get(d.severity.value, '•')} **{d.title}** ({d.category.value})")
            if d.step_index is not None:
                parts.append(f"     → Step {d.step_index}: {d.description[:120]}")
            if d.recommendation:
                parts.append(f"     → Suggestion: {d.recommendation}")

    return "\n".join(parts)


def generate_comparison_insight(runs: list[Run]) -> str:
    if not runs:
        return "No runs to compare."

    best = max(runs, key=lambda r: r.metrics.success_score)
    worst = min(runs, key=lambda r: r.metrics.success_score)
    avg_score = sum(r.metrics.success_score for r in runs) / len(runs)
    avg_cost = sum(r.metrics.total_cost_usd for r in runs) / len(runs)

    parts = [
        f"**Comparison across {len(runs)} runs:**",
        f"  • Best score: {best.metrics.success_score:.2f} (run {best.id[:8]})",
        f"  • Worst score: {worst.metrics.success_score:.2f} (run {worst.id[:8]})",
        f"  • Average score: {avg_score:.2f}",
        f"  • Average cost: ${avg_cost:.6f}",
        f"  • Success rate: {sum(1 for r in runs if r.metrics.success)}/{len(runs)}",
    ]

    if best.metrics.success_score > worst.metrics.success_score:
        best.metrics.step_count - worst.metrics.step_count if hasattr(worst.metrics, "step_count") else 0
        if best.metrics.total_cost_usd < worst.metrics.total_cost_usd:
            parts.append(
                f"  • Best run was both cheaper (${best.metrics.total_cost_usd:.4f} vs ${worst.metrics.total_cost_usd:.4f}) and higher scoring"
            )

    return "\n".join(parts)
