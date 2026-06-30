import gradio as gr
import plotly.graph_objects as go

from ...diagnostics.insights import generate_comparison_insight
from ...storage.db import init_db
from ...storage.repository import RunRepository


def create_comparison_tab(tab: gr.Tab):
    init_db()
    run_repo = RunRepository()

    with gr.Row():
        run_a = gr.Dropdown(label="Run A", interactive=True)
        run_b = gr.Dropdown(label="Run B", interactive=True)

    compare_btn = gr.Button("Compare", variant="primary")

    with gr.Row():
        with gr.Column():
            metrics_a = gr.Markdown("_Select Run A_")
        with gr.Column():
            metrics_b = gr.Markdown("_Select Run B_")

    comparison_chart = gr.Plot(label="Metrics Comparison")
    radar_chart = gr.Plot(label="Radar Comparison")
    comparison_insight = gr.Markdown("_Select two runs and click Compare_")

    def load_choices():
        all_runs = run_repo.find_all(limit=100)
        choices = [
            f"{r.id[:12]} - Score: {r.metrics.success_score:.2f} - ${r.metrics.total_cost_usd:.6f}" for r in all_runs
        ]
        return (gr.Dropdown(choices=choices or ["_No runs_"]), gr.Dropdown(choices=choices or ["_No runs_"]))

    def compare(run_a_label, run_b_label):
        if not run_a_label or not run_b_label or "_No runs_" in (run_a_label, run_b_label):
            return "_Select Run A_", "_Select Run B_", None, None, "_Select two runs_"
        run_a_id = run_a_label.split(" - ")[0]
        run_b_id = run_b_label.split(" - ")[0]
        all_runs = run_repo.find_all(limit=100)
        ra = next((r for r in all_runs if r.id.startswith(run_a_id)), None)
        rb = next((r for r in all_runs if r.id.startswith(run_b_id)), None)
        if not ra or not rb:
            return "_Run not found_", "_Run not found_", None, None, "_Error loading runs_"

        def fmt(r):
            return f"""**Run ID**: `{r.id}`
**Status**: {"✅ Success" if r.metrics.success else "❌ Failed"}
**Score**: {r.metrics.success_score:.2f}
**Cost**: ${r.metrics.total_cost_usd:.6f}
**Tokens**: {r.metrics.total_tokens}
**Steps**: {r.metrics.step_count}
**Tool Calls**: {r.metrics.tool_call_count}
**Errors**: {r.metrics.error_count}
**Latency**: {r.metrics.total_latency_ms:.0f}ms
**Efficiency**: {r.metrics.efficiency_score:.1f}%"""

        categories = ["Score", "Steps", "Tool Calls", "Errors", "Cost ($)", "Latency (s)", "Efficiency"]
        ra_vals = [
            ra.metrics.success_score * 100,
            ra.metrics.step_count,
            ra.metrics.tool_call_count,
            ra.metrics.error_count,
            ra.metrics.total_cost_usd * 1000,
            ra.metrics.total_latency_ms / 1000,
            ra.metrics.efficiency_score,
        ]
        rb_vals = [
            rb.metrics.success_score * 100,
            rb.metrics.step_count,
            rb.metrics.tool_call_count,
            rb.metrics.error_count,
            rb.metrics.total_cost_usd * 1000,
            rb.metrics.total_latency_ms / 1000,
            rb.metrics.efficiency_score,
        ]

        fig = go.Figure()
        fig.add_trace(go.Bar(name=f"Run A ({ra.id[:8]})", x=categories, y=ra_vals, marker_color="#2563eb"))
        fig.add_trace(go.Bar(name=f"Run B ({rb.id[:8]})", x=categories, y=rb_vals, marker_color="#f59e0b"))
        fig.update_layout(
            barmode="group",
            height=400,
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
        )

        radar = go.Figure()
        radar.add_trace(
            go.Scatterpolar(
                r=[
                    ra.metrics.success_score * 100,
                    ra.metrics.efficiency_score,
                    max(0, 100 - ra.metrics.error_count * 20),
                    max(0, 100 - ra.metrics.total_cost_usd * 10000),
                    max(0, 100 - ra.metrics.total_latency_ms / 100),
                ],
                theta=["Success", "Efficiency", "Reliability", "Cost", "Speed"],
                fill="toself",
                name=f"Run A ({ra.id[:8]})",
                line_color="#2563eb",
            )
        )
        radar.add_trace(
            go.Scatterpolar(
                r=[
                    rb.metrics.success_score * 100,
                    rb.metrics.efficiency_score,
                    max(0, 100 - rb.metrics.error_count * 20),
                    max(0, 100 - rb.metrics.total_cost_usd * 10000),
                    max(0, 100 - rb.metrics.total_latency_ms / 100),
                ],
                theta=["Success", "Efficiency", "Reliability", "Cost", "Speed"],
                fill="toself",
                name=f"Run B ({rb.id[:8]})",
                line_color="#f59e0b",
            )
        )
        radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=400,
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=20, b=20),
        )

        insight = generate_comparison_insight([ra, rb])
        return fmt(ra), fmt(rb), fig, radar, insight

    tab.select(load_choices, None, [run_a, run_b])
    compare_btn.click(
        compare, [run_a, run_b], [metrics_a, metrics_b, comparison_chart, radar_chart, comparison_insight]
    )
