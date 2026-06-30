"""EvalForge Quickstart Example.

Run: python examples/quickstart.py
"""

from evalforge import EvalForge

# Initialize with your preferred provider
# (set DEEPSEEK_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY in .env)
ef = EvalForge(provider="deepseek")

# Define a coding task
task = ef.create_task(
    name="reverse-string",
    instructions=(
        "Write a Python function called `reverse_string` that takes a string "
        "and returns it reversed. Provide only the function code."
    ),
    success_criteria=[
        ef.create_criterion("defines reverse_string function", "contains", "def reverse_string"),
        ef.create_criterion("uses return statement", "contains", "return"),
        ef.create_criterion("has proper string handling", "contains", "["),
    ],
)

# Create an evaluation
evaluation = ef.create_evaluation(
    name="Quickstart Demo",
    description="Basic coding task evaluation",
    tasks=[task],
)

print(f"Created evaluation: {evaluation.name} ({evaluation.id})")
print(f"Tasks: {len(evaluation.tasks)}")
print()

# Run the evaluation (requires API key or Ollama running locally)
print("Running evaluation (this will call the LLM)...")
runs = ef.run(evaluation)

for run in runs:
    status = "✅ PASS" if run.metrics.success else "❌ FAIL"
    print(f"\n  Run: {run.id[:12]}")
    print(f"  Status: {status}")
    print(f"  Score: {run.metrics.success_score:.2f}")
    print(f"  Cost: ${run.metrics.total_cost_usd:.6f}")
    print(f"  Steps: {run.metrics.step_count}")
    print(f"  Tokens: {run.metrics.total_tokens}")
    print(f"  Latency: {run.metrics.total_latency_ms:.0f}ms")

    # Analyze for diagnostics
    diagnostics = ef.analyze(run.id)
    if diagnostics:
        print(f"  Diagnostics ({len(diagnostics)}):")
        for d in diagnostics:
            print(f"    - {d.severity.value}: {d.title}")

print()
print("Done! View full results in the dashboard: evalforge serve")
