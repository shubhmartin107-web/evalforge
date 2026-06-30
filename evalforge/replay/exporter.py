import json
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..models.diagnostics import Diagnostic
from ..models.run import Run
from ..models.trace import Trace


def export_run_to_json(run: Run, trace: Trace | None = None, diagnostics: list[Diagnostic] | None = None) -> str:
    data = {
        "export_version": "1.0",
        "exported_at": datetime.now(UTC).isoformat(),
        "run": run.model_dump(),
        "trace": trace.model_dump() if trace else None,
        "diagnostics": [d.model_dump() for d in (diagnostics or [])],
    }
    return json.dumps(data, indent=2, default=str)


def export_run_to_markdown(run: Run, trace: Trace | None = None, diagnostics: list[Diagnostic] | None = None) -> str:
    lines = [
        "# EvalForge Run Report",
        "",
        f"**Run ID**: `{run.id}`",
        f"**Status**: {run.status}",
        f"**Created**: {run.created_at}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Success | {'✅' if run.metrics.success else '❌'} |",
        f"| Score | {run.metrics.success_score:.2f} |",
        f"| Steps | {run.metrics.step_count} |",
        f"| Tool Calls | {run.metrics.tool_call_count} |",
        f"| Errors | {run.metrics.error_count} |",
        f"| Total Tokens | {run.metrics.total_tokens} |",
        f"| Total Cost | ${run.metrics.total_cost_usd:.6f} |",
        f"| Total Latency | {run.metrics.total_latency_ms:.0f}ms |",
        f"| Efficiency | {run.metrics.efficiency_score:.1f}% |",
    ]

    if diagnostics:
        lines.extend(
            [
                "",
                "## Diagnostics",
                "",
            ]
        )
        for d in diagnostics:
            sv_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}
            lines.append(f"- {sv_icon.get(d.severity.value, '•')} **{d.title}**")
            lines.append(f"  - Category: {d.category.value}")
            lines.append(f"  - {d.description}")
            if d.recommendation:
                lines.append(f"  - *Suggestion: {d.recommendation}*")

    if trace and trace.steps:
        lines.extend(
            [
                "",
                f"## Trace ({len(trace.steps)} steps)",
                "",
            ]
        )
        for step in trace.steps:
            step_icon = {
                "thought": "💭",
                "tool_call": "🔧",
                "tool_result": "📥",
                "output": "📤",
                "error": "❌",
                "system": "⚙️",
            }.get(step.step_type.value, "•")
            lines.append(f"### Step {step.step_number}: {step_icon} {step.step_type.value}")
            if step.content:
                lines.append("")
                lines.append("```")
                lines.append(step.content[:500])
                lines.append("```")
            if step.tool_name:
                lines.append("")
                lines.append(f"- **Tool**: `{step.tool_name}`")
            if step.tool_output:
                lines.append(f"- **Result**: {step.tool_output[:200]}")
            if step.error_message:
                lines.append(f"- **Error**: {step.error_message}")
            lines.append("")

    return "\n".join(lines)


_TEMPLATE_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))


def export_run_to_html(run: Run, trace: Trace | None = None, diagnostics: list[Diagnostic] | None = None) -> str:
    template = _jinja_env.get_template("report.html")
    steps = trace.steps if trace else []
    return template.render(run=run, steps=steps, diagnostics=diagnostics or [])
