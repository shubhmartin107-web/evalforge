import re

from .base import BaseGrader, GradingResult


class CodeGrader(BaseGrader):
    name = "code"

    def evaluate(
        self,
        agent_output: str,
        expected: str | None = None,
        criterion_type: str = "contains",
        **kwargs,
    ) -> GradingResult:
        if not agent_output:
            return GradingResult(passed=False, score=0.0, description="Empty agent output")

        if criterion_type == "exact_match":
            if expected is None:
                return GradingResult(passed=False, score=0.0, description="No expected value for exact_match")
            passed = agent_output.strip() == expected.strip()

        elif criterion_type == "contains":
            if expected is None:
                return GradingResult(passed=False, score=0.0, description="No expected value for contains")
            passed = expected in agent_output

        elif criterion_type == "regex":
            if expected is None:
                return GradingResult(passed=False, score=0.0, description="No pattern for regex")
            try:
                passed = bool(re.search(expected, agent_output))
            except re.error:
                return GradingResult(passed=False, score=0.0, description=f"Invalid regex pattern: {expected}")

        elif criterion_type == "python_exec":
            passed = self._evaluate_python_exec(agent_output, expected)

        elif criterion_type == "unit_test":
            passed = self._evaluate_unit_test(agent_output, expected or "")

        else:
            return GradingResult(passed=False, score=0.0, description=f"Unknown criterion type: {criterion_type}")

        score = 1.0 if passed else 0.0
        return GradingResult(
            passed=passed,
            score=score,
            description=f"{criterion_type}: expected={expected}",
            criterion_type=criterion_type,
        )

    def _evaluate_python_exec(self, code: str, test_code: str | None = None) -> bool:
        if not code:
            return False
        try:
            compiled = compile(code, "<eval>", "exec")
            namespace: dict[str, object] = {}
            exec(compiled, namespace)
            if test_code:
                exec(compile(test_code, "<test>", "exec"), namespace)
            return True
        except Exception:
            return False

    def _evaluate_unit_test(self, code: str, test_code: str) -> bool:
        import io
        from contextlib import redirect_stderr, redirect_stdout

        try:
            full_code = f"{code}\n\n{test_code}"
            compiled = compile(full_code, "<test>", "exec")
            namespace: dict[str, object] = {}
            f_out = io.StringIO()
            f_err = io.StringIO()
            with redirect_stdout(f_out), redirect_stderr(f_err):
                exec(compiled, namespace)
            return True
        except Exception:
            return False
