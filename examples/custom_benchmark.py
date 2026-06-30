"""Creating a custom benchmark with EvalForge."""

from evalforge import EvalForge
from evalforge.models import Evaluation, TaskDefinition, SuccessCriteria

ef = EvalForge()

# Define multiple tasks
tasks = [
    TaskDefinition(
        name="hello-world",
        instructions="Write a Python program that prints 'Hello, World!'",
        success_criteria=[
            SuccessCriteria(type="contains", description="Must print hello", expected="Hello"),
            SuccessCriteria(type="contains", description="Must use print", expected="print"),
        ],
        tags=["beginner", "python"],
    ),
    TaskDefinition(
        name="fizzbuzz",
        instructions=(
            "Write a Python function that prints numbers 1 to 100, "
            "but for multiples of 3 print 'Fizz', for multiples of 5 print 'Buzz', "
            "and for multiples of both print 'FizzBuzz'."
        ),
        success_criteria=[
            SuccessCriteria(type="contains", description="Must define function", expected="def "),
            SuccessCriteria(type="contains", description="Must handle multiples of 3", expected="Fizz"),
            SuccessCriteria(type="contains", description="Must handle multiples of 5", expected="Buzz"),
        ],
        tags=["intermediate", "python"],
    ),
]

# Create the benchmark
benchmark = Evaluation(
    name="Python Interview Questions",
    description="Common Python coding interview questions",
    tasks=tasks,
    tags=["coding", "interview", "python"],
)

# Register it
ef.register_evaluation(benchmark)
print(f"Created benchmark: {benchmark.name} with {len(tasks)} tasks")
print(f"Benchmark ID: {benchmark.id}")
print()

# List all registered benchmarks
print("All benchmarks:")
for b in ef.list_evaluations():
    print(f"  - {b.name} ({len(b.tasks)} tasks)")
