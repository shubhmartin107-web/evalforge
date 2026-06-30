from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ..core.grading import grade_task
from ..core.metrics import compute_metrics
from ..core.session import SessionRecorder, capture_env_snapshot
from ..models.evaluation import Evaluation, TaskDefinition
from ..models.provider import AgentConfig
from ..models.run import Run
from ..models.trace import StepType
from ..providers.base import ProviderBase
from ..storage.repository import EvaluationRepository, RunRepository

AgentFunction = Callable[[str, list[dict[str, Any]], Callable], Any]


class EvaluationHarness:
    def __init__(
        self,
        provider: ProviderBase | None = None,
        agent_function: AgentFunction | None = None,
        judge_provider: ProviderBase | None = None,
    ):
        self.provider = provider
        self.agent_function = agent_function
        self.judge_provider = judge_provider or provider
        self._run_repo = RunRepository()
        self._eval_repo = EvaluationRepository()

    def run_task(
        self,
        task: TaskDefinition,
        evaluation: Evaluation,
        agent_config: AgentConfig | None = None,
        seed: int | None = None,
    ) -> Run:
        run = Run(
            evaluation_id=evaluation.id,
            task_id=task.id,
            status="running",
            agent_config=(agent_config.model_dump() if agent_config else {}),
            seed=seed,
            env_snapshot=capture_env_snapshot(),
            started_at=datetime.now(UTC).isoformat(),
        )
        self._run_repo.save(run)

        recorder = SessionRecorder(run)
        recorder.record_system(f"Starting task: {task.name}")
        recorder.record_system(f"Instructions: {task.instructions[:200]}...")

        try:
            agent_output = self._execute_agent(task, recorder, agent_config)
            agent_output_str = str(agent_output) if agent_output else ""

            recorder.record_output(agent_output_str)

            judge_config = evaluation.judge_config or {}
            if self.judge_provider:
                judge_config.setdefault("provider", self.judge_provider)
            success_score, grading_results = grade_task(task, agent_output_str, evaluation.grading_type, judge_config)
            success = success_score >= 0.5

            run.metrics = compute_metrics(
                recorder.trace.steps,
                success=success,
                success_score=success_score,
                model=(agent_config.provider.model if agent_config else "deepseek-chat"),
            )

            run.status = "completed"
            run.trace_id = recorder.trace.id
            run.completed_at = datetime.now(UTC).isoformat()

        except Exception as e:
            recorder.record_error(str(e))
            run.status = "failed"
            run.error_message = str(e)
            run.metrics = compute_metrics(recorder.trace.steps, success=False, success_score=0.0)
            run.completed_at = datetime.now(UTC).isoformat()

        recorder.save_trace()
        self._run_repo.save(run)
        return run

    def _execute_agent(
        self,
        task: TaskDefinition,
        recorder: SessionRecorder,
        agent_config: AgentConfig | None = None,
    ) -> str:
        if self.agent_function:
            return self._execute_custom_agent(task, recorder)
        elif self.provider:
            return self._execute_provider_agent(task, recorder, agent_config)
        else:
            raise ValueError("No agent function or provider configured")

    def _execute_provider_agent(
        self,
        task: TaskDefinition,
        recorder: SessionRecorder,
        agent_config: AgentConfig | None = None,
    ) -> str:
        messages = [{"role": "user", "content": task.instructions}]
        if agent_config and agent_config.system_prompt:
            messages.insert(0, {"role": "system", "content": agent_config.system_prompt})

        full_response = []
        for step_num in range(task.max_steps):
            timer = recorder.get_latency_timer()
            assert self.provider is not None
            response = self.provider.chat(
                messages=messages,
                model=(agent_config.provider.model if agent_config else None),
                temperature=(agent_config.provider.temperature if agent_config else 0.7),
                max_tokens=(agent_config.provider.max_tokens if agent_config else 4096),
            )
            latency = timer.elapsed_ms()

            error = response.get("error")
            if error:
                raise RuntimeError(f"Provider error: {error}")

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            input_tokens = response.get("usage", {}).get("input_tokens", 0)
            output_tokens = response.get("usage", {}).get("output_tokens", 0)
            token_count = input_tokens + output_tokens
            cost = response.get("cost_usd", 0.0)

            if content:
                recorder.record_thought(
                    content=content,
                    token_count=token_count,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency_ms=latency,
                )
                messages.append({"role": "assistant", "content": content})
                full_response.append(content)

            if tool_calls:
                for tc in tool_calls:
                    recorder.record_tool_call(
                        tool_name=tc.get("function", {}).get("name", "unknown"),
                        tool_input=tc.get("function", {}).get("arguments", {}),
                        latency_ms=0,
                    )
                    result = self.provider.execute_tool(tc) if self.provider else str(tc)
                    recorder.record_tool_result(
                        tool_output=str(result),
                        latency_ms=0,
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id", ""),
                            "content": str(result),
                        }
                    )

            if not tool_calls and content:
                break

            if step_num >= task.max_steps - 1:
                recorder.record_system("Max steps reached")
                break

        return "\n".join(full_response)

    def _execute_custom_agent(
        self,
        task: TaskDefinition,
        recorder: SessionRecorder,
    ) -> str:
        def record_step(step_type: str, **kwargs) -> None:
            st = StepType(step_type) if isinstance(step_type, str) else step_type
            recorder.record(st, **kwargs)

        assert self.agent_function is not None
        criteria_dicts = [c.model_dump() for c in task.success_criteria]
        result = self.agent_function(task.instructions, criteria_dicts, record_step)
        return str(result) if result else ""


def run_evaluation(
    evaluation: Evaluation,
    provider: ProviderBase | None = None,
    agent_function: AgentFunction | None = None,
    agent_config: AgentConfig | None = None,
    seed: int | None = None,
    judge_provider: ProviderBase | None = None,
) -> list[Run]:
    harness = EvaluationHarness(
        provider=provider,
        agent_function=agent_function,
        judge_provider=judge_provider,
    )
    runs = []
    for task in evaluation.tasks:
        run = harness.run_task(task, evaluation, agent_config=agent_config, seed=seed)
        runs.append(run)
    return runs
