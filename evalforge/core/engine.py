from ..models.evaluation import Evaluation
from ..models.provider import AgentConfig
from ..models.run import Run
from ..providers.base import ProviderBase
from ..storage.repository import (
    EvaluationRepository,
    RunRepository,
    TraceRepository,
)
from .harness import EvaluationHarness


class EvaluationEngine:
    """Main orchestrator for running evaluations."""

    def __init__(
        self,
        provider: ProviderBase | None = None,
        judge_provider: ProviderBase | None = None,
    ):
        self.provider = provider
        self.judge_provider = judge_provider or provider
        self._eval_repo = EvaluationRepository()
        self._run_repo = RunRepository()
        self._trace_repo = TraceRepository()

    def register_evaluation(self, evaluation: Evaluation) -> Evaluation:
        self._eval_repo.save(evaluation)
        return evaluation

    def run(
        self,
        evaluation: Evaluation | str,
        agent_config: AgentConfig | None = None,
        agent_function=None,
        seed: int | None = None,
    ) -> list[Run]:
        if isinstance(evaluation, str):
            eval_obj = self._eval_repo.find_by_id(evaluation)
            if eval_obj is None:
                raise ValueError(f"Evaluation not found: {evaluation}")
        else:
            eval_obj = evaluation

        if self.provider is None and agent_function is None:
            raise ValueError("No provider or agent function configured")

        harness = EvaluationHarness(
            provider=self.provider,
            agent_function=agent_function,
            judge_provider=self.judge_provider,
        )
        runs = []
        for task in eval_obj.tasks:
            run = harness.run_task(task, eval_obj, agent_config=agent_config, seed=seed)
            runs.append(run)
        return runs

    def get_run(self, run_id: str) -> Run | None:
        return self._run_repo.find_by_id(run_id)

    def get_trace(self, run_id: str):
        return self._trace_repo.find_by_run_id(run_id)

    def list_evaluations(self) -> list[Evaluation]:
        return self._eval_repo.find_all()

    def list_runs(self, limit: int = 100, offset: int = 0) -> list[Run]:
        return self._run_repo.find_all(limit=limit, offset=offset)

    def get_evaluation(self, eval_id: str) -> Evaluation | None:
        return self._eval_repo.find_by_id(eval_id)

    def get_runs_for_evaluation(self, eval_id: str) -> list[Run]:
        return self._run_repo.find_by_evaluation(eval_id)

    def count_runs(self) -> int:
        return self._run_repo.count()
