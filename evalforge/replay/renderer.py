from ..models.trace import Step, StepType


def render_step_cli(step: Step) -> str:
    icon = {
        StepType.thought: "💭",
        StepType.tool_call: "🔧",
        StepType.tool_result: "📥",
        StepType.output: "📤",
        StepType.error: "❌",
        StepType.system: "⚙️",
    }.get(step.step_type, "•")

    lines = [f"{icon} Step {step.step_number} [{step.step_type.value}]"]

    if step.content:
        content = step.content[:500]
        lines.append(f"   {content}")

    if step.tool_name:
        lines.append(f"   Tool: {step.tool_name}")
    if step.tool_input:
        import json as _json

        lines.append(f"   Input: {_json.dumps(step.tool_input, default=str)[:200]}")
    if step.tool_output:
        lines.append(f"   Output: {step.tool_output[:200]}")
    if step.error_message:
        lines.append(f"   Error: {step.error_message}")

    details = []
    if step.token_count:
        details.append(f"{step.token_count}t")
    if step.cost_usd:
        details.append(f"${step.cost_usd:.6f}")
    if step.latency_ms:
        details.append(f"{step.latency_ms:.0f}ms")
    if details:
        lines.append(f"   ({', '.join(details)})")

    return "\n".join(lines)


def render_trace_cli(steps: list[Step], max_steps: int = 100) -> str:
    parts = [f"Trace: {len(steps)} steps"]
    for step in steps[:max_steps]:
        parts.append("")
        parts.append(render_step_cli(step))
    if len(steps) > max_steps:
        parts.append(f"\n... and {len(steps) - max_steps} more steps")
    return "\n".join(parts)


def render_step_for_gradio(step: Step) -> str:
    return render_step_cli(step)


def render_metrics_summary(metrics_dict: dict) -> str:
    lines = ["## Metrics Summary", ""]
    for key, value in metrics_dict.items():
        key_str = key.replace("_", " ").title()
        if isinstance(value, float):
            lines.append(f"- **{key_str}**: {value:.4f}")
        else:
            lines.append(f"- **{key_str}**: {value}")
    return "\n".join(lines)
