from pathlib import Path

from rich import print as rprint

from ..replay.exporter import export_run_to_html, export_run_to_json, export_run_to_markdown
from ..storage.repository import DiagnosticRepository, RunRepository, TraceRepository


def export_command(run_id: str, format: str = "markdown", output: str | None = None) -> None:
    run_repo = RunRepository()
    trace_repo = TraceRepository()
    diag_repo = DiagnosticRepository()

    all_runs = run_repo.find_all(limit=100)
    run = next((r for r in all_runs if r.id.startswith(run_id)), None)
    if run is None:
        run = run_repo.find_by_id(run_id)

    if run is None:
        rprint(f"[red]❌ Run not found: {run_id}[/red]")
        return

    trace = trace_repo.find_by_run_id(run.id)
    diags = diag_repo.find_by_run_id(run.id)

    if format == "json":
        content = export_run_to_json(run, trace, diags)
        ext = ".json"
    elif format == "html":
        content = export_run_to_html(run, trace, diags)
        ext = ".html"
    else:
        content = export_run_to_markdown(run, trace, diags)
        ext = ".md"

    if output:
        out_path = Path(output)
    else:
        out_path = Path(f"evalforge_report_{run.id[:8]}{ext}")

    out_path.write_text(content)
    rprint(f"[green]✅ Report exported to [bold]{out_path}[/bold][/green]")
