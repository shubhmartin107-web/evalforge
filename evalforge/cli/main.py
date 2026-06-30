import typer
from rich import print as rprint
from rich.console import Console

from ..storage.db import init_db
from .export_cmd import export_command
from .list_cmd import list_command, list_runs_command
from .run import run_command

app = typer.Typer(
    name="evalforge",
    help="EvalForge — Agent Evaluation & Benchmarking Platform",
    add_completion=False,
)
console = Console()


@app.callback()
def main_callback(
    ctx: typer.Context,
    db_path: str = typer.Option(None, "--db-path", help="Path to EvalForge database"),
):
    ctx.ensure_object(dict)
    if db_path:
        import os
        os.environ["EVALFORGE_DB_PATH"] = db_path
    init_db()


@app.command()
def init():
    """Initialize EvalForge database and config."""
    init_db()
    rprint("[green]✅ EvalForge initialized successfully![/green]")
    from ..storage.db import get_db_path
    rprint(f"   Database ready at [bold]{get_db_path()}[/bold]")


@app.command()
def run(
    evaluation: str = typer.Argument(..., help="Evaluation name or ID"),
    provider: str = typer.Option(
        "deepseek", "--provider", "-p", help="Provider: deepseek, gemini, groq, ollama, anthropic"
    ),
    model: str = typer.Option("", "--model", "-m", help="Model name"),
    seed: int = typer.Option(None, "--seed", "-s", help="Random seed for reproducibility"),
):
    """Run an evaluation."""
    run_command(evaluation, provider, model if model else None, seed)


@app.command()
def list(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of items to show"),
):
    """List evaluations."""
    list_command(limit)


@app.command("list-runs")
def list_runs(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of runs to show"),
    evaluation_id: str = typer.Option(None, "--eval", "-e", help="Filter by evaluation ID"),
):
    """List evaluation runs."""
    list_runs_command(limit, evaluation_id)


@app.command()
def export(
    run_id: str = typer.Argument(..., help="Run ID to export"),
    format: str = typer.Option("markdown", "--format", "-f", help="Export format: json, markdown, html"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export a run report."""
    export_command(run_id, format, output)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(7860, "--port", "-p", help="Port to bind to"),
    share: bool = typer.Option(False, "--share", help="Create a public link"),
):
    """Start the EvalForge dashboard."""
    from ..dashboard.app import create_app

    dashboard = create_app()
    rprint(f"[green]🚀 Starting EvalForge dashboard at http://{host}:{port}[/green]")
    if share:
        rprint("[yellow]🌍 Creating public link...[/yellow]")
    dashboard.launch(server_name=host, server_port=port, share=share)


if __name__ == "__main__":
    app()
