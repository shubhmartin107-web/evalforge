from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..core.engine import EvaluationEngine
from ..models.provider import AgentConfig, ProviderConfig, ProviderType
from ..providers.factory import create_provider
from ..storage.repository import EvaluationRepository

console = Console()


def run_command(
    evaluation: str,
    provider: str = "deepseek",
    model: str | None = None,
    seed: int | None = None,
) -> None:
    eval_repo = EvaluationRepository()

    try:
        eval_obj = eval_repo.find_by_id(evaluation)
        if eval_obj is None:
            evals = [e for e in eval_repo.find_all() if e.name == evaluation]
            if evals:
                eval_obj = evals[0]
    except Exception:
        pass

    if eval_obj is None:
        evals = [e for e in eval_repo.find_all() if e.name == evaluation]
        if not evals:
            rprint(f"[red]❌ Evaluation not found: {evaluation}[/red]")
            return
        eval_obj = evals[0]

    rprint(f"[blue]🔍 Running evaluation: [bold]{eval_obj.name}[/bold][/blue]")
    rprint(f"   Tasks: {len(eval_obj.tasks)}")

    try:
        provider_instance = create_provider(provider)
    except Exception as e:
        rprint(f"[red]❌ Failed to create provider '{provider}': {e}[/red]")
        return

    if model:
        provider_instance.default_model = model

    agent_config = AgentConfig(
        provider=ProviderConfig(
            provider=ProviderType(provider),
            model=model or provider_instance.default_model,
        ),
    )

    engine = EvaluationEngine(provider=provider_instance)

    with console.status("Running evaluation..."):
        runs = engine.run(eval_obj, agent_config=agent_config, seed=seed)

    table = Table(title=f"Results: {eval_obj.name}")
    table.add_column("Task", style="cyan")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Steps", justify="right")
    table.add_column("Tokens", justify="right")

    for run in runs:
        icon = "✅" if run.metrics.success else "❌"
        table.add_row(
            run.task_id[:8],
            f"{icon} {run.status}",
            f"{run.metrics.success_score:.2f}",
            f"${run.metrics.total_cost_usd:.6f}",
            str(run.metrics.step_count),
            str(run.metrics.total_tokens),
        )

    console.print(table)

    total_cost = sum(r.metrics.total_cost_usd for r in runs)
    success_count = sum(1 for r in runs if r.metrics.success)
    rprint(f"\n[bold]Summary:[/bold] {success_count}/{len(runs)} passed | Total cost: ${total_cost:.6f}")
