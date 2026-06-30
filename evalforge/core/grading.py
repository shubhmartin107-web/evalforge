from typing import Any

from ..models.evaluation import GradingType, SuccessCriteria, TaskDefinition
from .graders.base import GradingResult
from .graders.code_grader import CodeGrader
from .graders.model_grader import JudgeConfig, ModelGrader

_code_grader = CodeGrader()


def grade_task(
    task: TaskDefinition,
    agent_output: str,
    grading_type: GradingType = GradingType.deterministic,
    judge_config: dict[str, Any] | None = None,
) -> tuple[float, list[dict]]:
    if grading_type == GradingType.llm_as_judge:
        return _llm_judge_grading(task, agent_output, judge_config)
    elif grading_type == GradingType.hybrid:
        return _hybrid_grading(task, agent_output, judge_config)
    else:
        return _deterministic_grading(task, agent_output)


def _deterministic_grading(task: TaskDefinition, agent_output: str) -> tuple[float, list[dict]]:
    results = []
    total_weight = sum(c.weight for c in task.success_criteria) or 1.0
    weighted_score = 0.0

    if not task.success_criteria:
        score = 1.0 if agent_output else 0.0
        return score, [
            {
                "criterion_id": "default",
                "description": "Output exists",
                "passed": bool(agent_output),
                "weight": 1.0,
                "score": score,
            }
        ]

    for criterion in task.success_criteria:
        result = _evaluate_criterion(criterion, agent_output)
        weighted_score += result.score * criterion.weight
        results.append(
            {
                "criterion_id": criterion.id,
                "description": criterion.description,
                "passed": result.passed,
                "weight": criterion.weight,
                "score": result.score,
                "reasoning": result.reasoning,
            }
        )

    final_score = weighted_score / total_weight
    return final_score, results


def _llm_judge_grading(
    task: TaskDefinition,
    agent_output: str,
    judge_config: dict[str, Any] | None = None,
) -> tuple[float, list[dict]]:
    config = _build_judge_config(judge_config)
    grader = ModelGrader(config)

    criteria_str = "\n".join(f"- {c.description} (type: {c.type})" for c in task.success_criteria)
    result = grader.evaluate(
        agent_output,
        instructions=task.instructions,
        criteria=criteria_str,
    )

    results = [
        {
            "criterion_id": "llm_judge",
            "description": "LLM-as-judge overall evaluation",
            "passed": result.passed,
            "weight": 1.0,
            "score": result.score,
            "reasoning": result.reasoning,
        }
    ]

    return result.score, results


def _hybrid_grading(
    task: TaskDefinition,
    agent_output: str,
    judge_config: dict[str, Any] | None = None,
) -> tuple[float, list[dict]]:
    det_score, det_results = _deterministic_grading(task, agent_output)

    config = _build_judge_config(judge_config)
    grader = ModelGrader(config)
    criteria_str = "\n".join(f"- {c.description} (type: {c.type})" for c in task.success_criteria)
    judge_result = grader.evaluate(
        agent_output,
        instructions=task.instructions,
        criteria=criteria_str,
    )

    combined_score = (det_score + judge_result.score) / 2.0
    combined_results = det_results + [
        {
            "criterion_id": "llm_judge",
            "description": "LLM-as-judge (hybrid mode)",
            "passed": judge_result.passed,
            "weight": 1.0,
            "score": judge_result.score,
            "reasoning": judge_result.reasoning,
        }
    ]

    return combined_score, combined_results


def _evaluate_criterion(criterion: SuccessCriteria, agent_output: str) -> GradingResult:
    if not agent_output:
        return GradingResult(passed=False, score=0.0, description=criterion.description)

    if criterion.type == "llm_judge":
        return GradingResult(
            passed=False,
            score=0.0,
            description="Individual llm_judge criteria require GradingType.llm_as_judge or hybrid",
        )

    if criterion.type == "callable":
        if criterion.metadata and "fn" in criterion.metadata:
            try:
                passed = bool(criterion.metadata["fn"](agent_output))
                return GradingResult(
                    passed=passed,
                    score=1.0 if passed else 0.0,
                    description=criterion.description,
                )
            except Exception as e:
                return GradingResult(
                    passed=False,
                    score=0.0,
                    description=criterion.description,
                    reasoning=f"Callable raised: {e}",
                )
        return GradingResult(
            passed=False,
            score=0.0,
            description="callable criterion requires 'fn' in metadata",
        )

    return _code_grader.evaluate(
        agent_output,
        expected=criterion.expected,
        criterion_type=criterion.type,
    )


def _build_judge_config(judge_config: dict[str, Any] | None = None) -> JudgeConfig:
    if judge_config is None:
        return JudgeConfig()
    return JudgeConfig(
        model=judge_config.get("model", "deepseek-chat"),
        temperature=judge_config.get("temperature", 0.1),
        max_tokens=judge_config.get("max_tokens", 512),
        rubric=judge_config.get("rubric"),
        pairwise=judge_config.get("pairwise", False),
    )
