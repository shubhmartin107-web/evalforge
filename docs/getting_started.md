# Getting Started with EvalForge

## Installation

```bash
# Install from source
git clone https://github.com/anthropics/evalforge.git
cd evalforge
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

Or using Docker:

```bash
docker compose up -d
# Open http://localhost:7860
```

## Quick Start with the SDK

### Step 1: Initialize EvalForge

```python
from evalforge import EvalForge

ef = EvalForge(provider="deepseek")
```

This initializes the SQLite database and prepares the provider for API calls.

### Step 2: Define a Task

```python
task = ef.create_task(
    name="hello-world",
    instructions="Write a Python function that prints 'Hello, World!'",
    success_criteria=[
        ef.create_criterion("must print hello", "contains", "Hello"),
        ef.create_criterion("must define a function", "contains", "def "),
    ],
)
```

### Step 3: Create an Evaluation

```python
evaluation = ef.create_evaluation(
    name="My First Benchmark",
    description="Testing basic code generation",
    tasks=[task],
)
```

### Step 4: Run the Evaluation

```python
runs = ef.run(evaluation)
```

### Step 5: Analyze Results

```python
for run in runs:
    print(f"Run {run.id[:8]}:")
    print(f"  Status: {run.status}")
    print(f"  Score: {run.metrics.success_score:.2f}")
    print(f"  Cost: ${run.metrics.total_cost_usd:.6f}")
    print(f"  Steps: {run.metrics.step_count}")
    print(f"  Tokens: {run.metrics.total_tokens}")

    # Get automated diagnostics
    diagnostics = ef.analyze(run.id)
    for d in diagnostics:
        print(f"  ⚠ {d.severity.value}: {d.title}")

    # Export report
    report = ef.export(run.id, format="markdown")
```

## Quick Start with the CLI

```bash
# List available benchmarks
evalforge list

# Run a benchmark
evalforge run "simple-code-gen" --provider deepseek

# See runs
evalforge list-runs

# Export a specific run
evalforge export <run-id> --format html -o report.html

# Launch the dashboard
evalforge serve
```

## Quick Start with the Dashboard

```bash
evalforge serve
# Open http://localhost:7860
```

The dashboard provides:
- **Dashboard tab** — Overview statistics and charts
- **History tab** — Browse all runs with filtering
- **Replay tab** — Step through any run visually
- **Compare tab** — Side-by-side run comparison
- **Benchmarks tab** — Create, view, and run benchmarks
- **Reports tab** — Export runs in multiple formats

## Configuring Providers

Set environment variables in a `.env` file:

```bash
DEEPSEEK_API_KEY=sk-...
GEMINI_API_KEY=...
GROQ_API_KEY=gsk_...

# Optional: customize default provider
EVALFORGE_PROVIDER=deepseek
EVALFORGE_MODEL=deepseek-chat
```

Or pass config when creating the SDK:

```python
from evalforge import EvalForge
from evalforge.models import ProviderConfig, AgentConfig

config = AgentConfig(
    provider=ProviderConfig(
        provider="gemini",
        model="gemini-1.5-flash",
        temperature=0.3,
    ),
)

ef = EvalForge(provider="gemini")
runs = ef.run(evaluation, agent_config=config)
```

## Custom Agent Functions

You're not limited to LLM providers — you can evaluate any agent function:

```python
def my_agent(instructions, criteria, record_step):
    """Your agent receives task instructions and can record steps."""
    record_step("thought", content="Starting to process the task...")
    
    # Call your agent framework here
    result = my_agent_framework.run(instructions)
    
    record_step("output", content=result)
    return result

ef = EvalForge()
runs = ef.run(evaluation, agent_function=my_agent)
```

## Example: Complete Workflow

```python
from evalforge import EvalForge

ef = EvalForge(provider="deepseek")

tasks = [
    ef.create_task(
        name="reverse-string",
        instructions="Write a Python function that reverses a string. Only output code.",
        success_criteria=[
            ef.create_criterion("defines reverse_string", "contains", "def reverse_string"),
            ef.create_criterion("uses return", "contains", "return"),
        ],
    ),
    ef.create_task(
        name="is-palindrome",
        instructions="Write a Python function that checks if a string is a palindrome.",
        success_criteria=[
            ef.create_criterion("defines is_palindrome", "contains", "def is_palindrome"),
            ef.create_criterion("returns boolean", "regex", r"return\s+(True|False|b)"),
        ],
    ),
]

evaluation = ef.create_evaluation(
    name="Python Coding Challenge",
    description="Two basic Python coding tasks",
    tasks=tasks,
)

runs = ef.run(evaluation)

for task, run in zip(tasks, runs):
    success = "✅ PASS" if run.metrics.success else "❌ FAIL"
    print(f"{task.name}: {success} (score: {run.metrics.success_score:.2f})")

print(f"\nTotal cost: ${sum(r.metrics.total_cost_usd for r in runs):.6f}")
