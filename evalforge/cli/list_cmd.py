from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..storage.repository import EvaluationRepository, RunRepository

console = Console()


def list_command(limit: int = 20) -> None:
    eval_repo = EvaluationRepository()
    evals = eval_repo.find_all()

    if not evals:
        rprint("[yellow]No evaluations found. Create one with 'evalforge create' or from the dashboard.[/yellow]")
        return

    table = Table(title=f"Evaluations ({len(evals)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Tasks")
    table.add_column("Grading")
    table.add_column("Created")

    for e in evals[:limit]:
        table.add_row(
            e.id[:12],
            e.name,
            str(len(e.tasks)),
            e.grading_type.value,
            e.created_at[:10] if e.created_at else "",
        )

    console.print(table)


def list_runs_command(limit: int = 20, evaluation_id: str | None = None) -> None:
    run_repo = RunRepository()

    if evaluation_id:
        runs = run_repo.find_by_evaluation(evaluation_id)
    else:
        runs = run_repo.find_all(limit=limit)

    if not runs:
        rprint("[yellow]No runs found.[/yellow]")
        return

    table = Table(title=f"Runs ({len(runs)})")
    table.add_column("Run ID", style="cyan")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Steps", justify="right")
    table.add_column("Latency", justify="right")
    table.add_column("Date")

    for r in runs:
        icon = "✅" if r.metrics.success else "❌" if r.status == "completed" else "⏳"
        table.add_row(
            r.id[:12],
            f"{icon} {r.status}",
            f"{r.metrics.success_score:.2f}",
            f"${r.metrics.total_cost_usd:.6f}",
            str(r.metrics.step_count),
            f"{r.metrics.total_latency_ms:.0f}ms",
            r.created_at[:10] if r.created_at else "",
        )

    console.print(table)
