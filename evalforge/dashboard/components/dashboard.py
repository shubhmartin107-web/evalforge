from datetime import UTC, datetime

import gradio as gr
import plotly.graph_objects as go

from ...storage.db import init_db
from ...storage.repository import EvaluationRepository, RunRepository


def create_dashboard_tab(tab: gr.Tab):
    init_db()
    run_repo = RunRepository()
    eval_repo = EvaluationRepository()

    header = gr.Markdown("Loading...")
    stats = gr.Markdown("Loading...")
    with gr.Row():
        score_plot = gr.Plot(label="Run Scores", show_label=False)
        cost_plot = gr.Plot(label="Cost Over Time", show_label=False)
    recent = gr.Markdown("Loading...")

    def update_dashboard():
        runs = run_repo.find_all(limit=100)
        evals = eval_repo.find_all()

        total_runs = len(runs)
        success_runs = sum(1 for r in runs if r.metrics.success)
        failed_runs = total_runs - success_runs
        total_cost = sum(r.metrics.total_cost_usd for r in runs)
        total_evals = len(evals)
        success_rate = (success_runs / total_runs * 100) if total_runs > 0 else 0

        fig_s = go.Figure()
        fig_c = go.Figure()
        if runs:
            dates = [r.created_at[:10] for r in runs]
            costs = [r.metrics.total_cost_usd for r in runs]
            scores = [r.metrics.success_score * 100 for r in runs]
            fig_c.add_trace(
                go.Scatter(
                    x=dates,
                    y=costs,
                    mode="lines+markers",
                    name="Cost ($)",
                    line=dict(color="#2563eb", width=2),
                    marker=dict(size=6),
                )
            )
            fig_c.update_layout(
                title="Cost Over Time",
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig_s.add_trace(
                go.Bar(
                    x=list(range(len(scores))),
                    y=scores,
                    name="Score %",
                    marker_color=["#059669" if s >= 50 else "#dc2626" for s in scores],
                )
            )
            fig_s.update_layout(
                title="Run Scores",
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )
        else:
            fig_c.add_annotation(text="No runs yet", showarrow=False, font=dict(size=16, color="#94a3b8"))
            fig_c.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            fig_s.add_annotation(text="No runs yet", showarrow=False, font=dict(size=16, color="#94a3b8"))
            fig_s.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))

        h = f"# EvalForge Dashboard\n*{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*"
        s = f"""<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
  <div class="stat-card"><div style="font-size:28px;font-weight:700;">{total_runs}</div><div style="font-size:12px;color:#64748b;">Total Runs</div></div>
  <div class="stat-card"><div style="font-size:28px;font-weight:700;color:#059669;">{success_runs}</div><div style="font-size:12px;color:#64748b;">Successful</div></div>
  <div class="stat-card"><div style="font-size:28px;font-weight:700;color:#dc2626;">{failed_runs}</div><div style="font-size:12px;color:#64748b;">Failed</div></div>
  <div class="stat-card"><div style="font-size:28px;font-weight:700;">${total_cost:.4f}</div><div style="font-size:12px;color:#64748b;">Total Cost</div></div>
  <div class="stat-card"><div style="font-size:28px;font-weight:700;">{success_rate:.1f}%</div><div style="font-size:12px;color:#64748b;">Success Rate</div></div>
  <div class="stat-card"><div style="font-size:28px;font-weight:700;">{total_evals}</div><div style="font-size:12px;color:#64748b;">Benchmarks</div></div>
</div>"""
        r = "### Recent Runs\n\n"
        if runs:
            r += "| Run ID | Status | Score | Cost | Steps |\n|---|---|---|---|---|\n"
            for rn in runs[:10]:
                icon = "✅" if rn.metrics.success else "❌"
                r += f"| `{rn.id[:8]}` | {icon} | {rn.metrics.success_score:.2f} | ${rn.metrics.total_cost_usd:.6f} | {rn.metrics.step_count} |\n"
        else:
            r += "_No runs yet. Run an evaluation from the Benchmarks tab._\n"
        return h, s, fig_s, fig_c, r

    tab.select(update_dashboard, None, [header, stats, score_plot, cost_plot, recent])
