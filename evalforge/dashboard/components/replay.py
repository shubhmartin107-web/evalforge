import gradio as gr

from ...replay.player import ReplayPlayer
from ...storage.db import init_db
from ...storage.repository import DiagnosticRepository, RunRepository, TraceRepository


def create_replay_tab(tab: gr.Tab):
    init_db()
    run_repo = RunRepository()
    trace_repo = TraceRepository()
    diag_repo = DiagnosticRepository()
    ReplayPlayer()

    run_select = gr.Dropdown(label="Select Run to Replay", interactive=True)

    with gr.Row():
        with gr.Column(scale=1):
            step_slider = gr.Slider(minimum=1, maximum=10, value=1, step=1, label="Step", interactive=True)
            with gr.Row():
                prev_btn = gr.Button("◀ Previous", variant="secondary", scale=1)
                next_btn = gr.Button("Next ▶", variant="primary", scale=1)
            gr.Markdown("### Diagnostics")
            diagnostics_display = gr.Markdown("_No diagnostics_")

        with gr.Column(scale=3):
            step_display = gr.Markdown("_Select a run to begin replay_")
            progress = gr.HTML()

    state = gr.State({"run_id": None, "max_steps": 0, "steps": [], "diagnostics": []})

    def load_runs():
        all_runs = run_repo.find_all(limit=100)
        choices = [
            f"{r.id[:12]} - Score: {r.metrics.success_score:.2f} - ${r.metrics.total_cost_usd:.6f}" for r in all_runs
        ]
        empty = "_No runs available_" if not choices else None
        return gr.Dropdown(choices=choices if choices else ["_No runs_"], value=empty)

    def load_run(label):
        if not label or label == "_No runs_":
            return (
                "Select a run",
                gr.Slider(minimum=1, maximum=10, value=1),
                "<div>...</div>",
                "_No diagnostics_",
                state.value,
            )
        run_id = label.split(" - ")[0] if " - " in label else label
        run = (
            run_repo.find_by_id(run_id)
            if len(run_id) > 8
            else next((r for r in run_repo.find_all(limit=100) if r.id.startswith(run_id)), None)
        )
        if not run:
            return (
                "_Run not found_",
                gr.Slider(minimum=1, maximum=10, value=1),
                "<div>...</div>",
                "_No diagnostics_",
                state.value,
            )

        trace = trace_repo.find_by_run_id(run.id)
        diags = diag_repo.find_by_run_id(run.id)
        steps = trace.steps if trace else []
        max_steps = max(len(steps), 1)

        diag_text = _format_diagnostics(diags) if diags else "_No diagnostics_"
        new_state = {"run_id": run.id, "max_steps": max_steps, "steps": steps, "diagnostics": diags}
        if steps:
            step_md = _render_step_md(steps[0], 0, max_steps)
            prog = _progress_html(1, max_steps)
            return step_md, gr.Slider(minimum=1, maximum=max_steps, value=1), prog, diag_text, new_state
        return (
            "_No steps recorded_",
            gr.Slider(minimum=1, maximum=max_steps, value=1),
            _progress_html(0, max_steps),
            diag_text,
            new_state,
        )

    def update_step(step_num, state_data):
        if not state_data or not state_data.get("steps"):
            return "_No steps_", "<div>...</div>"
        steps = state_data["steps"]
        max_s = state_data["max_steps"]
        idx = max(0, min(int(step_num) - 1, len(steps) - 1))
        if idx < len(steps):
            return _render_step_md(steps[idx], idx, max_s), _progress_html(idx + 1, max_s)
        return "_Step not found_", "<div>...</div>"

    def prev_step(step_val, state_data):
        new_val = max(1, int(step_val) - 1)
        md, prog = update_step(new_val, state_data)
        return new_val, md, prog

    def next_step(step_val, state_data):
        new_val = min(state_data.get("max_steps", 1), int(step_val) + 1)
        md, prog = update_step(new_val, state_data)
        return new_val, md, prog

    tab.select(load_runs, None, run_select)
    run_select.change(load_run, [run_select], [step_display, step_slider, progress, diagnostics_display, state])
    step_slider.change(update_step, [step_slider, state], [step_display, progress])
    prev_btn.click(prev_step, [step_slider, state], [step_slider, step_display, progress])
    next_btn.click(next_step, [step_slider, state], [step_slider, step_display, progress])


def _render_step_md(step, idx, total) -> str:
    icon_map = {"thought": "💭", "tool_call": "🔧", "tool_result": "📥", "output": "📤", "error": "❌", "system": "⚙️"}
    icon = icon_map.get(step.step_type.value, "•")
    md = [f"# Step {step.step_number} of {total} {icon}", f"**Type**: `{step.step_type.value}`", ""]
    if step.content:
        md.append("**Reasoning/Content:**")
        md.append(f"```\n{step.content}\n```")
        md.append("")
    if step.tool_name:
        md.append(f"**Tool Used**: `{step.tool_name}`")
    if step.tool_input:
        import json

        md.append("**Tool Input**:")
        md.append(f"```json\n{json.dumps(step.tool_input, indent=2, default=str)}\n```")
        md.append("")
    if step.tool_output:
        md.append("**Tool Output**:")
        md.append(f"```\n{step.tool_output[:500]}\n```")
        md.append("")
    if step.error_message:
        md.append(f"**Error**: `{step.error_message}`")
    details = []
    if step.token_count:
        details.append(f"🔤 {step.token_count} tokens")
    if step.cost_usd:
        details.append(f"💰 ${step.cost_usd:.6f}")
    if step.latency_ms:
        details.append(f"⏱ {step.latency_ms:.0f}ms")
    if details:
        md.append("")
        md.append(" | ".join(details))
    return "\n".join(md)


def _progress_html(current, total) -> str:
    pct = (current / total) * 100 if total > 0 else 0
    color = "#059669" if pct == 100 else "#2563eb"
    return f"""<div style="width:100%;background:#e2e8f0;border-radius:6px;height:10px;overflow:hidden;">
        <div style="width:{pct}%;background:{color};border-radius:6px;height:10px;transition:width 0.3s;"></div>
    </div><p style="text-align:center;font-size:12px;color:#64748b;margin-top:4px;">Step {current} of {total}</p>"""


def _format_diagnostics(diags) -> str:
    lines = []
    for d in diags:
        icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}
        lines.append(f"{icon.get(d.severity.value, '•')} **{d.title}**")
        lines.append(f"  - {d.description[:120]}")
        if d.step_index is not None:
            lines.append(f"  - Occurs at step {d.step_index}")
        if d.recommendation:
            lines.append(f"  - 💡 {d.recommendation}")
        lines.append("")
    return "\n".join(lines)
