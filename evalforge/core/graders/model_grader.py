from dataclasses import dataclass, field
from typing import Any

from .base import BaseGrader, GradingResult

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator judging an AI agent's output.
Evaluate the agent's response based on the following criteria:

Task Instructions:
{instructions}

Success Criteria:
{criteria}

Agent Output:
{agent_output}

---

Evaluate whether the agent's output meets the success criteria.
Respond with a JSON object containing:
- "passed": true/false (whether the criteria are met)
- "score": 0.0 to 1.0 (partial credit if partially met)
- "reasoning": a brief explanation of your evaluation

Your JSON response:"""


@dataclass
class JudgeConfig:
    provider: Any = None
    model: str = "deepseek-chat"
    prompt_template: str = JUDGE_PROMPT_TEMPLATE
    temperature: float = 0.1
    max_tokens: int = 512
    rubric: str | None = None
    pairwise: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelGrader(BaseGrader):
    name = "model"

    def __init__(self, config: JudgeConfig | None = None):
        self.config = config or JudgeConfig()

    def evaluate(
        self,
        agent_output: str,
        expected: str | None = None,
        **kwargs,
    ) -> GradingResult:
        if not agent_output:
            return GradingResult(passed=False, score=0.0, description="Empty agent output")

        result = self._call_judge(agent_output, kwargs.get("instructions", ""), kwargs.get("criteria", ""))
        return result

    def _call_judge(
        self,
        agent_output: str,
        instructions: str,
        criteria: str,
    ) -> GradingResult:
        if self.config.provider is None:
            return self._rule_based_fallback(agent_output, criteria)

        prompt = self.config.prompt_template.format(
            instructions=instructions,
            criteria=criteria,
            agent_output=agent_output[:4000],
        )

        try:
            response = self.config.provider.chat(
                messages=[{"role": "user", "content": prompt}],
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            content = response.get("content", "")

            import json
            import re

            json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                passed = data.get("passed", False)
                score = float(data.get("score", 0.0))
                reasoning = data.get("reasoning", "")
            else:
                passed = "pass" in content.lower() or "yes" in content.lower()
                score = 1.0 if passed else 0.0
                reasoning = content[:200]

            return GradingResult(
                passed=passed,
                score=score,
                description=f"LLM-as-judge evaluation using {self.config.model}",
                reasoning=reasoning,
            )
        except Exception as e:
            return self._rule_based_fallback(agent_output, criteria, error=str(e))

    def _rule_based_fallback(
        self,
        agent_output: str,
        criteria: str,
        error: str = "",
    ) -> GradingResult:
        passed = False
        reasoning = "Judge LLM call failed. Using fallback heuristic."

        if error:
            reasoning += f" Error: {error}"

        if criteria:
            criteria_lower = criteria.lower()
            keywords = ["must", "should", "need", "require"]
            for kw in keywords:
                if kw in criteria_lower:
                    parts = criteria.split(kw, 1)
                    if len(parts) > 1:
                        requirement = parts[1].strip().rstrip(".")
                        if requirement and requirement.lower() in agent_output.lower():
                            passed = True

        score = 1.0 if passed else 0.0
        return GradingResult(
            passed=passed,
            score=score,
            description="LLM-as-judge (fallback heuristic)",
            reasoning=reasoning,
        )
