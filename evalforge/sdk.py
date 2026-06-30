"""EvalForge Python SDK — Programmatic interface for evaluations."""

from .core.engine import EvaluationEngine
from .diagnostics.analyzer import DiagnosticAnalyzer
from .models.diagnostics import Diagnostic
from .models.evaluation import Evaluation, GradingType, SuccessCriteria, TaskDefinition
from .models.provider import AgentConfig
from .models.run import Run
from .providers.base import ProviderBase
from .providers.factory import create_provider
from .replay.exporter import export_run_to_html, export_run_to_json, export_run_to_markdown
from .replay.player import ReplayPlayer
from .storage.db import init_db, reset_db
from .storage.repository import (
    DiagnosticRepository,
    EvaluationRepository,
    RunRepository,
    TraceRepository,
)


class EvalForge:
    """Main SDK entry point for EvalForge.

    Usage:
        ef = EvalForge(provider='deepseek')
        eval_obj = ef.create_evaluation(name='My Eval', tasks=[...])
        runs = ef.run(eval_obj)
        ef.serve()
    """

    def __init__(
        self,
        provider: ProviderBase | str | None = None,
        db_path: str | None = None,
        judge_provider: ProviderBase | str | None = None,
    ):
        if db_path:
            import os

            os.environ["EVALFORGE_DB_PATH"] = db_path
        init_db()

        if isinstance(provider, str):
            self.provider = create_provider(provider)
        else:
            self.provider = provider  # type: ignore[assignment]

        if isinstance(judge_provider, str):
            self.judge_provider = create_provider(judge_provider)
        elif judge_provider is not None:
            self.judge_provider = judge_provider
        else:
            self.judge_provider = self.provider

        self.engine = EvaluationEngine(
            provider=self.provider,
            judge_provider=self.judge_provider,
        )
        self.eval_repo = EvaluationRepository()
        self.run_repo = RunRepository()
        self.trace_repo = TraceRepository()
        self.diag_repo = DiagnosticRepository()
        self.analyzer = DiagnosticAnalyzer()
        self.player = ReplayPlayer()

    def create_evaluation(
        self,
        name: str,
        tasks: list[TaskDefinition],
        description: str = "",
        grading_type: GradingType = GradingType.deterministic,
    ) -> Evaluation:
        eval_obj = Evaluation(
            name=name,
            description=description,
            tasks=tasks,
            grading_type=grading_type,
        )
        self.eval_repo.save(eval_obj)
        return eval_obj

    def create_task(
        self,
        name: str,
        instructions: str,
        success_criteria: list[SuccessCriteria] | None = None,
        description: str = "",
        max_steps: int = 50,
    ) -> TaskDefinition:
        return TaskDefinition(
            name=name,
            description=description,
            instructions=instructions,
            success_criteria=success_criteria or [],
            max_steps=max_steps,
        )

    def create_criterion(
        self,
        description: str,
        type: str = "contains",
        expected: str | None = None,
        weight: float = 1.0,
    ) -> SuccessCriteria:
        return SuccessCriteria(
            description=description,
            type=type,
            expected=expected,
            weight=weight,
        )

    def run(
        self,
        evaluation: Evaluation | str,
        agent_config: AgentConfig | None = None,
        agent_function=None,
        seed: int | None = None,
    ) -> list[Run]:
        return self.engine.run(
            evaluation,
            agent_config=agent_config,
            agent_function=agent_function,
            seed=seed,
        )

    def run_trials(
        self,
        evaluation: Evaluation | str,
        n_trials: int = 5,
        agent_config: AgentConfig | None = None,
        agent_function=None,
    ) -> dict:
        """Run multiple trials of an evaluation and compute pass@k metrics."""
        from .core.metrics import compute_trial_metrics

        all_runs = []
        for trial in range(n_trials):
            runs = self.run(
                evaluation,
                agent_config=agent_config,
                agent_function=agent_function,
            )
            all_runs.extend(runs)

        per_task: dict[str, list] = {}
        for r in all_runs:
            per_task.setdefault(r.task_id, []).append(r)

        results = {}
        for task_id, runs in per_task.items():
            metrics_list = [r.metrics for r in runs]
            trial_metrics = compute_trial_metrics(metrics_list)
            trial_metrics["runs"] = runs
            results[task_id] = trial_metrics

        return results

    def get_evaluation(self, evaluation_id: str) -> Evaluation | None:
        return self.eval_repo.find_by_id(evaluation_id)

    def get_run(self, run_id: str) -> Run | None:
        return self.run_repo.find_by_id(run_id)

    def get_trace(self, run_id: str):
        return self.trace_repo.find_by_run_id(run_id)

    def analyze(self, run_id: str) -> list[Diagnostic]:
        run = self.get_run(run_id)
        if not run:
            return []
        trace = self.get_trace(run_id)
        return self.analyzer.analyze_run(run, trace)

    def list_evaluations(self) -> list[Evaluation]:
        return self.eval_repo.find_all()

    def list_runs(self, limit: int = 100) -> list[Run]:
        return self.run_repo.find_all(limit=limit)

    def export(self, run_id: str, format: str = "markdown") -> str:
        run = self.get_run(run_id)
        trace = self.get_trace(run_id)
        diags = self.diag_repo.find_by_run_id(run_id)
        if run is None:
            return f"Run {run_id} not found"
        if format == "json":
            return export_run_to_json(run, trace, diags)
        elif format == "html":
            return export_run_to_html(run, trace, diags)
        return export_run_to_markdown(run, trace, diags)

    def serve(self, host: str = "0.0.0.0", port: int = 7860, share: bool = False):
        from .dashboard.app import create_app

        dashboard = create_app()
        dashboard.launch(server_name=host, server_port=port, share=share)

    def reset(self):
        reset_db()


__all__ = ["EvalForge"]
