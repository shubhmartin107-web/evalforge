from ..models.evaluation import Evaluation, GradingType, SuccessCriteria, TaskDefinition
from ..storage.repository import EvaluationRepository


def register_benchmark(evaluation: Evaluation) -> Evaluation:
    repo = EvaluationRepository()
    repo.save(evaluation)
    return evaluation


def register_all() -> list[Evaluation]:
    benchmarks = []
    benchmarks.extend(_coding_benchmarks())
    benchmarks.extend(_research_benchmarks())
    benchmarks.extend(_tool_use_benchmarks())
    benchmarks.extend(_safety_benchmarks())
    for b in benchmarks:
        register_benchmark(b)
    return benchmarks


def _coding_benchmarks() -> list[Evaluation]:
    return [
        Evaluation(
            name="simple-code-gen",
            description="Generate a Python function to reverse a string",
            grading_type=GradingType.deterministic,
            tasks=[
                TaskDefinition(
                    name="reverse-string",
                    description="Write a Python function that reverses a string",
                    instructions="Write a Python function called `reverse_string` that takes a string and returns it reversed. Provide only the function code.",
                    success_criteria=[
                        SuccessCriteria(
                            type="contains",
                            description="Must contain 'def reverse_string'",
                            expected="def reverse_string",
                        ),
                        SuccessCriteria(type="contains", description="Must use return statement", expected="return"),
                    ],
                    tags=["coding", "python", "basic"],
                ),
            ],
        ),
        Evaluation(
            name="code-refactor",
            description="Refactor poorly written Python code to be cleaner and more efficient",
            grading_type=GradingType.deterministic,
            tasks=[
                TaskDefinition(
                    name="refactor-function",
                    description="Refactor a poorly written function",
                    instructions="Refactor this Python code to be cleaner and more efficient:\n\ndef calc(a,b,c):\n    x = a + b\n    y = x * c\n    z = y / 2\n    return z\n\nProvide the refactored version with explanation.",
                    success_criteria=[
                        SuccessCriteria(
                            type="contains", description="Must explain the refactoring", expected="explanation"
                        ),
                        SuccessCriteria(type="contains", description="Must provide improved code", expected="def "),
                    ],
                    tags=["coding", "refactoring"],
                ),
            ],
        ),
        Evaluation(
            name="debug-code",
            description="Find and fix bugs in provided code",
            grading_type=GradingType.deterministic,
            tasks=[
                TaskDefinition(
                    name="fix-bug",
                    description="Find and fix a bug in a function",
                    instructions="Find and fix the bug in this Python function:\n\ndef get_average(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total / len(numbers) if numbers else None\n\nThe function has a subtle bug when handling empty lists. Fix it and explain.",
                    success_criteria=[
                        SuccessCriteria(type="contains", description="Must identify the bug", expected="bug"),
                        SuccessCriteria(type="contains", description="Must provide fix", expected="return"),
                    ],
                    tags=["coding", "debugging"],
                ),
            ],
        ),
    ]


def _research_benchmarks() -> list[Evaluation]:
    return [
        Evaluation(
            name="research-summary",
            description="Summarize a technical concept accurately",
            grading_type=GradingType.deterministic,
            tasks=[
                TaskDefinition(
                    name="explain-concept",
                    description="Explain a technical concept clearly",
                    instructions="Explain what a 'vector database' is, how it works, and when you would use one. Provide a clear, accurate, and concise explanation (2-3 paragraphs).",
                    success_criteria=[
                        SuccessCriteria(
                            type="contains", description="Must mention vectors/embeddings", expected="vector"
                        ),
                        SuccessCriteria(
                            type="contains", description="Must mention similarity search", expected="similar"
                        ),
                        SuccessCriteria(type="contains", description="Must be reasonable length", expected=""),
                    ],
                    tags=["research", "explanation"],
                ),
            ],
        ),
        Evaluation(
            name="fact-checking",
            description="Verify factual claims and provide accurate information",
            grading_type=GradingType.deterministic,
            tasks=[
                TaskDefinition(
                    name="verify-claim",
                    description="Verify and respond to a factual claim",
                    instructions="A colleague claims: 'GPT-4 was released in 2021 and has 1 trillion parameters.' Is this accurate? If not, provide the correct information with your reasoning.",
                    success_criteria=[
                        SuccessCriteria(type="contains", description="Must identify inaccuracies", expected="not"),
                        SuccessCriteria(type="contains", description="Must be careful about dates", expected="2023"),
                    ],
                    tags=["research", "fact-checking"],
                ),
            ],
        ),
    ]


def _safety_benchmarks() -> list[Evaluation]:
    from .safety.bias import create_bias_eval
    from .safety.harmful_output import create_harmful_output_eval
    from .safety.jailbreak import create_jailbreak_eval
    from .safety.sycophancy import create_sycophancy_eval

    return [
        create_sycophancy_eval(),
        create_bias_eval(),
        create_harmful_output_eval(),
        create_jailbreak_eval(),
    ]


def _tool_use_benchmarks() -> list[Evaluation]:
    return [
        Evaluation(
            name="multi-step-workflow",
            description="Complete a multi-step research and analysis task",
            grading_type=GradingType.deterministic,
            tasks=[
                TaskDefinition(
                    name="analyze-trends",
                    description="Research and analyze technology trends",
                    instructions="You are a research analyst. Your task is to:\n1. Identify 3 major trends in AI agent development for 2026\n2. For each trend, explain why it matters\n3. Rank them by potential impact\n\nProvide a structured analysis.",
                    success_criteria=[
                        SuccessCriteria(type="contains", description="Must identify 3 trends", expected="1."),
                        SuccessCriteria(type="contains", description="Must explain impact", expected="impact"),
                        SuccessCriteria(
                            type="regex", description="Must have numbered or structured format", expected=r"\d+\."
                        ),
                    ],
                    tags=["tool-use", "multi-step", "analysis"],
                ),
            ],
        ),
        Evaluation(
            name="data-extraction",
            description="Extract and structure information from text",
            grading_type=GradingType.deterministic,
            tasks=[
                TaskDefinition(
                    name="extract-info",
                    description="Extract structured data from text",
                    instructions="Extract the following from this text and format as JSON:\n\n'ACME Corp reported Q3 revenue of $4.2 billion, up 15% YoY. Net income was $890 million. The company has 12,500 employees across 8 countries. CEO Jane Smith announced the results on October 25, 2025.'\n\nFields to extract: company_name, revenue_q3, revenue_growth_pct, net_income, employees, countries_count, ceo_name, announcement_date",
                    success_criteria=[
                        SuccessCriteria(type="contains", description="Must extract company name", expected="ACME"),
                        SuccessCriteria(type="contains", description="Must be in JSON format", expected="{"),
                        SuccessCriteria(type="contains", description="Must extract revenue", expected="4.2"),
                    ],
                    tags=["tool-use", "extraction"],
                ),
            ],
        ),
    ]
