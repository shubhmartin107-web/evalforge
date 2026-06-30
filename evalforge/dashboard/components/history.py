import gradio as gr

from ...diagnostics.insights import generate_insights
from ...storage.db import init_db
from ...storage.repository import EvaluationRepository, RunRepository

_PAGE_SIZE = 25


def create_history_tab(tab: gr.Tab):
    init_db()
    run_repo = RunRepository()
    eval_repo = EvaluationRepository()

    with gr.Row():
        eval_filter = gr.Dropdown(label="Filter by Benchmark", interactive=True)
        status_filter = gr.Radio(choices=["All", "Completed", "Failed"], value="All", label="Status", interactive=True)
        with gr.Column(scale=0, min_width=120):
            page_info = gr.Markdown("Page 1")
            with gr.Row():
                prev_btn = gr.Button("◀", scale=0, min_width=40)
                next_btn = gr.Button("▶", scale=0, min_width=40)

    history_table = gr.Dataframe(
        headers=["Run ID", "Benchmark", "Status", "Score", "Cost", "Steps", "Latency", "Date"],
        datatype=["str", "str", "str", "number", "number", "number", "number", "str"],
        label="",
        interactive=False,
        wrap=True,
    )

    gr.Markdown("### Run Details")
    run_selector = gr.Dropdown(label="Select Run ID", interactive=True)
    run_details = gr.Markdown("_Select a run to view details_")

    current_page = gr.State(0)

    def update_list(eval_name, status, page):
        all_runs = run_repo.find_all(limit=200)
        evals = eval_repo.find_all()
        eval_options = {e.name: e.id for e in evals}

        filtered = all_runs
        if eval_name and eval_name != "All" and eval_name in eval_options:
            filtered = [r for r in filtered if r.evaluation_id == eval_options[eval_name]]
        if status == "Completed":
            filtered = [r for r in filtered if r.status == "completed"]
        elif status == "Failed":
            filtered = [r for r in filtered if r.status == "failed"]

        offset = page * _PAGE_SIZE
        page_runs = filtered[offset : offset + _PAGE_SIZE]
        total_pages = max(1, (len(filtered) + _PAGE_SIZE - 1) // _PAGE_SIZE)

        data = []
        for r in page_runs:
            st = (
                "✅ Completed"
                if r.status == "completed" and r.metrics.success
                else "❌ Failed"
                if r.status == "failed"
                else "⏳ Running"
            )
            data.append(
                [
                    r.id[:12],
                    r.evaluation_id[:8],
                    st,
                    round(r.metrics.success_score, 2),
                    round(r.metrics.total_cost_usd, 6),
                    r.metrics.step_count,
                    f"{r.metrics.total_latency_ms:.0f}ms",
                    r.created_at[:10] if r.created_at else "",
                ]
            )
        ids = [r.id[:12] for r in page_runs]
        pi = f"Page {page + 1} of {total_pages} ({len(filtered)} runs)"
        dropdown_choices = ids if ids else ["_None_"]
        return data, pi, gr.Dropdown(choices=dropdown_choices, value=None if not ids else ids[0]), page

    def next_page(eval_name, status, page):
        all_runs_count = len(run_repo.find_all(limit=200))
        max_page = max(0, (all_runs_count - 1) // _PAGE_SIZE)
        new_page = min(max_page, page + 1)
        return update_list(eval_name, status, new_page)

    def prev_page(eval_name, status, page):
        new_page = max(0, page - 1)
        return update_list(eval_name, status, new_page)

    def show_run_details(run_id_prefix):
        if not run_id_prefix or run_id_prefix == "_None_":
            return "_Select a run to view details_"
        run = run_repo.find_by_id(run_id_prefix) if len(run_id_prefix) > 8 else None
        if not run:
            try:
                all_runs = run_repo.find_all(limit=200)
                run = next((r for r in all_runs if r.id.startswith(run_id_prefix)), None)
            except StopIteration:
                return "_Run not found_"
        if not run:
            return "_Run not found_"
        diagnostics = run.diagnostics or []
        insight = generate_insights(run, diagnostics)
        return f"**Run ID**: `{run.id}`\n\n{insight}"

    def init_data():
        return update_list("All", "All", 0)

    tab.select(init_data, None, [history_table, page_info, run_selector, current_page])
    eval_filter.change(
        update_list, [eval_filter, status_filter, current_page], [history_table, page_info, run_selector, current_page]
    )
    status_filter.change(
        update_list, [eval_filter, status_filter, current_page], [history_table, page_info, run_selector, current_page]
    )
    prev_btn.click(
        prev_page, [eval_filter, status_filter, current_page], [history_table, page_info, run_selector, current_page]
    )
    next_btn.click(
        next_page, [eval_filter, status_filter, current_page], [history_table, page_info, run_selector, current_page]
    )
    run_selector.change(show_run_details, [run_selector], [run_details])
