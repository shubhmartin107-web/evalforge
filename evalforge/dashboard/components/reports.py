import gradio as gr

from ...replay.exporter import export_run_to_html, export_run_to_json, export_run_to_markdown
from ...storage.db import init_db
from ...storage.repository import DiagnosticRepository, RunRepository, TraceRepository


def create_reports_tab(tab: gr.Tab):
    init_db()
    run_repo = RunRepository()
    trace_repo = TraceRepository()
    diag_repo = DiagnosticRepository()

    run_select = gr.Dropdown(label="Select Run to Export", interactive=True)

    with gr.Tabs():
        with gr.Tab("Markdown"):
            md_preview = gr.Markdown("_Select a run_")
            md_copy = gr.Textbox(label="Markdown Content", lines=15, interactive=False)

        with gr.Tab("JSON"):
            json_preview = gr.Textbox(label="JSON Content", lines=20, interactive=False)

        with gr.Tab("HTML"):
            html_preview = gr.HTML("_Select a run_")
            html_copy = gr.Textbox(label="HTML Content", lines=15, interactive=False)

    def load_choices():
        all_runs = run_repo.find_all(limit=100)
        choices = [f"{r.id[:12]} - Score: {r.metrics.success_score:.2f}" for r in all_runs]
        return gr.Dropdown(choices=choices or ["_No runs_"])

    def generate_reports(label):
        if not label or label == "_No runs_":
            return "_Select a run_", "", "_Select a run_", "", "_Select a run_", ""
        run_id = label.split(" - ")[0]
        run = run_repo.find_by_id(run_id) if len(run_id) > 8 else None
        if not run:
            all_runs = run_repo.find_all(limit=100)
            run = next((r for r in all_runs if r.id.startswith(run_id)), None)
        if not run:
            return "_Run not found_", "", "_Run not found_", "", "_Run not found_", ""

        trace = trace_repo.find_by_run_id(run.id)
        diags = diag_repo.find_by_run_id(run.id)
        md = export_run_to_markdown(run, trace, diags)
        js = export_run_to_json(run, trace, diags)
        html = export_run_to_html(run, trace, diags)
        return md, md, js, html, html, html

    tab.select(load_choices, None, run_select)
    run_select.change(
        generate_reports, [run_select], [md_preview, md_copy, json_preview, html_preview, html_copy, html_copy]
    )
