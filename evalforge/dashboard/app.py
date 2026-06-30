import gradio as gr

from ..storage.db import init_db
from .components.benchmarks import create_benchmarks_tab
from .components.comparison import create_comparison_tab
from .components.dashboard import create_dashboard_tab
from .components.history import create_history_tab
from .components.replay import create_replay_tab
from .components.reports import create_reports_tab
from .theme import create_theme


def create_app() -> gr.Blocks:
    init_db()

    theme = create_theme()

    with gr.Blocks(
        title="EvalForge - Agent Evaluation Platform",
        theme=theme,
        css=_get_css(),
    ) as app:
        gr.Markdown(
            """
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
                <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;color:white;font-weight:bold;">EF</div>
                <div>
                    <span style="font-size:24px;font-weight:700;color:#1e293b;">EvalForge</span>
                    <span style="font-size:14px;color:#64748b;margin-left:8px;">Agent Evaluation & Benchmarking Platform</span>
                </div>
            </div>
            """
        )

        with gr.Tabs():
            with gr.Tab("Dashboard") as tab1:
                create_dashboard_tab(tab1)
            with gr.Tab("History") as tab2:
                create_history_tab(tab2)
            with gr.Tab("Replay") as tab3:
                create_replay_tab(tab3)
            with gr.Tab("Compare") as tab4:
                create_comparison_tab(tab4)
            with gr.Tab("Benchmarks") as tab5:
                create_benchmarks_tab(tab5)
            with gr.Tab("Reports") as tab6:
                create_reports_tab(tab6)

        gr.Markdown(
            """
            <div style="text-align:center;padding:16px 0;color:#94a3b8;font-size:12px;">
                EvalForge v1.0.0 — Open Source Agent Evaluation Platform
            </div>
            """
        )

    return app


def _get_css() -> str:
    return """
    .gradio-container { max-width: 1400px !important; margin: 0 auto; }
    .tabs { margin-top: 0; }
    .tab-nav { background: white; border-bottom: 1px solid #e2e8f0; padding: 0 16px; }
    .tab-nav button { border: none; background: none; padding: 12px 16px; cursor: pointer; font-size: 14px; color: #64748b; border-bottom: 2px solid transparent; }
    .tab-nav button:hover { color: #1e293b; }
    .tab-nav button.selected { color: #2563eb; border-bottom-color: #2563eb; }
    footer { display: none !important; }
    h1, h2, h3 { margin-top: 0; }
    .stat-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .stat-card h3 { font-size: 28px; margin: 0; }
    .stat-card p { color: #64748b; margin: 4px 0 0 0; font-size: 14px; }
    """


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
