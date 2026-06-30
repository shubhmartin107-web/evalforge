<div align="center">
  <br/>
  <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);width:80px;height:80px;border-radius:20px;display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;">
    <span style="font-size:42px;color:white;font-weight:bold;">EF</span>
  </div>
  <h1 style="font-size:2.5em;margin:8px 0 4px;">EvalForge</h1>
  <p style="font-size:1.2em;color:#64748b;max-width:600px;margin:0 auto;">
    The Open Standard for Agent Evaluation & Benchmarking
  </p>
  <br/>
  <p>
    <a href="https://pypi.org/project/evalforge/"><img src="https://img.shields.io/pypi/v/evalforge?color=2563eb&style=flat-square" alt="PyPI"></a>
    <a href="https://pypi.org/project/evalforge/"><img src="https://img.shields.io/pypi/pyversions/evalforge?color=2563eb&style=flat-square" alt="Python"></a>
    <a href="https://github.com/shubhmartin107-web/evalforge/actions"><img src="https://img.shields.io/github/actions/workflow/status/shubhmartin107-web/evalforge/ci.yml?branch=main&style=flat-square" alt="CI"></a>
    <a href="https://codecov.io/gh/shubhmartin107-web/evalforge"><img src="https://img.shields.io/codecov/c/github/shubhmartin107-web/evalforge?style=flat-square" alt="Coverage"></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/shubhmartin107-web/evalforge?color=2563eb&style=flat-square" alt="License"></a>
    <a href="https://pypi.org/project/evalforge/"><img src="https://img.shields.io/pypi/v/evalforge?style=flat-square&color=2563eb" alt="PyPI"></a>
    <a href="https://pypi.org/project/evalforge/"><img src="https://img.shields.io/pypi/pyversions/evalforge?style=flat-square" alt="Python Versions"></a>
    <a href="https://github.com/shubhmartin107-web/evalforge"><img src="https://img.shields.io/github/stars/shubhmartin107-web/evalforge?style=flat-square&color=2563eb" alt="Stars"></a>
  </p>
  <br/>
  <p>
    <a href="#quickstart"><strong>Quickstart</strong></a> ·
    <a href="#why-evalforge"><strong>Why EvalForge</strong></a> ·
    <a href="#features"><strong>Features</strong></a> ·
    <a href="#architecture"><strong>Architecture</strong></a> ·
    <a href="#for-claude-code-users"><strong>For Claude Users</strong></a>
  </p>
  <br/>
</div>

---

**EvalForge** is a comprehensive, production-grade open-source platform for rigorously evaluating AI agents. It provides visual replay, deep diagnostics, reliability scoring, and actionable insights so you can confidently ship production agents.

> **Current agent evaluation is broken.** Simple pass/fail checks don't capture the complexity of multi-turn, tool-using agents. EvalForge fixes this with reproducible runs, full session traces, automated diagnostics, and a beautiful visual replay interface.

---

## Why EvalForge?

### The Problem
Building agents with Claude Code, LangGraph, CrewAI, or custom harnesses is exciting — but how do you know if they actually work? Most teams rely on:
- **Manual testing** — Run it a few times, see if it looks right
- **Simple pass/fail** — Did the agent produce *something*?
- **No reproducibility** — Different runs give different results
- **No diagnostics** — When it fails, you have no idea why

This isn't acceptable for production systems. Agents are non-deterministic, expensive to run, and fail in complex ways. You need rigorous evaluation infrastructure.

### The Solution
EvalForge provides everything you need to evaluate agents properly:

| Capability | What It Solves |
|---|---|
| **Reproducible Runs** | Full seed and environment capture for deterministic replay |
| **Session Recording** | Every thought, tool call, and output captured with timing |
| **Visual Replay** | Step through agent sessions to see exactly what happened |
| **Auto-Diagnostics** | Root-cause analysis: looping, context exhaustion, tool errors |
| **Comparison Views** | Side-by-side metrics across runs, models, and configurations |
| **Cost Analysis** | Track tokens and cost per run, identify expensive failures |
| **Standard Benchmarks** | Curated tasks for coding, research, and tool-use evaluation |

---

## Quickstart

```bash
# Install
pip install evalforge

# Run the dashboard
evalforge serve

# Or use in Python
```

### Using the SDK

```python
from evalforge import EvalForge

ef = EvalForge(provider="deepseek")

task = ef.create_task(
    name="reverse-string",
    instructions="Write a Python function that reverses a string. Return only the code.",
    success_criteria=[
        ef.create_criterion("must define function", "contains", "def "),
        ef.create_criterion("must use return", "contains", "return"),
    ],
)

evaluation = ef.create_evaluation(
    name="My First Eval",
    tasks=[task],
)

runs = ef.run(evaluation)
for run in runs:
    print(f"Score: {run.metrics.success_score:.2f}")
    print(f"Cost: ${run.metrics.total_cost_usd:.6f}")

# Get automated diagnostics
diagnostics = ef.analyze(runs[0].id)
for d in diagnostics:
    print(f"- {d.severity.value}: {d.title}")

# Export report
report = ef.export(runs[0].id, format="html")
```

### Using the CLI

```bash
# List available benchmarks
evalforge list

# Run an evaluation
evalforge run "simple-code-gen" --provider deepseek

# View runs
evalforge list-runs

# Export a report
evalforge export <run-id> --format html -o report.html

# Start the dashboard
evalforge serve
```

### Using Docker

```bash
docker compose up
# Open http://localhost:7860
```

---

## Features

### 🎯 Core Evaluation Engine
- **Single & Multi-turn** — Evaluate both simple prompts and long-horizon agent sessions
- **Standardized Harness** — Clear task definitions, success criteria, and grading
- **Reproducible** — Full seeding and environment snapshot for every run
- **Rich Metrics** — Success rate, cost (tokens + USD), latency, step efficiency, reasoning quality, pass@k, pass^k
- **LLM-as-Judge** — Configurable grading using any provider (rubric, pairwise, hybrid)

### 🎬 Visual Replay & Diagnostics
- **Full Traces** — Every reasoning step, tool call, and output captured
- **Step-Through Interface** — Navigate any run step-by-step
- **Auto Root-Cause Analysis** — Detects looping, context exhaustion, tool errors, cost overruns, and more
- **Failure Highlighting** — Pinpoints exactly where and why the agent failed

### 📊 Dashboard
- **Modern UI** — Clean, responsive Gradio-based interface
- **History** — Browse all runs with filtering and details
- **Comparison** — Side-by-side analysis of runs, models, and configurations
- **Reports** — Export to JSON, Markdown, or HTML
- **Benchmark Overview** — Browse built-in benchmarks with descriptions and tags

### 🧪 Benchmark Suite
- **Coding Tasks** — Code generation, refactoring, debugging
- **Research Tasks** — Summarization, fact-checking, analysis
- **Tool-Use Tasks** — Multi-step workflows, data extraction
- **Safety Tasks** — Sycophancy detection, bias evaluation, harmful output, jailbreak resistance
- **Extensible** — Add your own benchmarks with simple Python configuration

### 🔒 Security
- **Secrets Filtering** — Env snapshots automatically exclude keys, tokens, passwords
- **Parameterized Queries** — All database operations use safe parameterization  
- **Vulnerability Reporting** — See [SECURITY.md](SECURITY.md) for our disclosure policy

### 🔌 Integrations
- **Provider Agnostic** — DeepSeek, Gemini, Groq, Ollama, Anthropic, OpenAI
- **Custom Providers** — Implement the `ProviderBase` interface for any LLM API
- **Custom Agents** — Use the harness with any agent function
- **Memory & Observability** — Hook into Memora, FlowLens, or any observability tool

---

## For Claude Code Users

EvalForge is designed with Claude Code and Claude Agent SDK users in mind. Here's how it helps:

### Evaluating Claude Code Sessions
Claude Code performs complex, multi-step tasks with tool use. EvalForge captures the full session:
- **Every tool call** (file edits, bash commands, web searches) is recorded
- **Reasoning traces** show how Claude arrived at decisions
- **Cost tracking** shows exactly how many tokens each step used
- **Diagnostics** identify when Claude gets stuck in loops or makes poor tool selections

### Example: Evaluating a Claude-Powered Agent

```python
from evalforge import EvalForge

ef = EvalForge()

def my_claude_agent(instructions, criteria, record_step):
    """Your agent function — compatible with any framework."""
    # Record reasoning and tool calls as they happen
    record_step("thought", content="Analyzing the task...")
    result = call_claude_api(instructions)
    record_step("output", content=result)
    return result

evaluation = ef.create_evaluation(
    name="Claude Agent Eval",
    tasks=[ef.create_task(
        name="code-review",
        instructions="Review this code for bugs...",
        success_criteria=[ef.create_criterion("found at least one bug", "contains", "bug")],
    )],
)

runs = ef.run(evaluation, agent_function=my_claude_agent)
```

### What You Get
- **Confidence** — Know your Claude agent works before deploying
- **Debugging** — Step through failures to see exactly where Claude went wrong
- **Optimization** — Track costs and latency to optimize prompts and tool use
- **Regression Testing** — Re-run evaluations after prompt changes to catch regressions

---

## Architecture

```
evalforge/
├── core/           # Evaluation engine, harness, metrics, session recording
├── models/         # Pydantic data models
├── storage/        # SQLite persistence layer
├── providers/      # LLM provider implementations
├── dashboard/      # Gradio UI
├── replay/         # Session playback engine
├── diagnostics/    # Root-cause analysis engine
├── benchmarks/     # Built-in benchmark tasks
├── cli/            # Typer-based command-line interface
└── sdk.py          # Unified Python SDK
```

**Key design decisions:**
- **SQLite** — Zero-dependency embedded storage, no external database needed
- **Gradio** — Fast, beautiful UI without frontend complexity
- **Plugin Providers** — Add any LLM API by extending `ProviderBase`
- **Trace-first** — Every evaluation produces a full trace for replay and analysis

---

## Supported Providers

| Provider | Free Tier | Models | Cost |
|---|---|---|---|
| **DeepSeek** | No | deepseek-chat, deepseek-reasoner | ~$0.14/M tokens |
| **Google Gemini** | ✅ Yes | gemini-1.5-flash, gemini-1.5-pro | Free tier available |
| **Groq** | ✅ Yes | mixtral, llama-3.1 | Free tier available |
| **Ollama** | ✅ Local | Any local model | Free (local) |
| **Anthropic** | No | claude-3.5-sonnet, claude-3.5-haiku | ~$3/M tokens |
| **OpenAI** | No | gpt-4o, gpt-4o-mini | ~$2.5/M tokens |

---

## Integrations

### Memory Systems (Memora)
EvalForge can evaluate agents that use persistent memory:
- Track memory retrieval accuracy across turns
- Measure context relevance scores
- Detect memory corruption or hallucination patterns

### Observability (FlowLens)
Export traces to FlowLens or any OpenTelemetry-compatible backend:
- Full trace visualization in your observability platform
- Cost attribution by agent step
- Performance monitoring across evaluation runs

### Custom Agents
Any agent framework can be evaluated:
- **LangGraph** — Wrap your graph execution in an agent function
- **CrewAI** — Evaluate crew outputs against success criteria  
- **AutoGen** — Multi-agent conversation evaluation
- **Custom** — Any Python function that takes instructions and returns output

---

## Development

```bash
git clone https://github.com/shubhmartin107-web/evalforge.git
cd evalforge
pip install -e ".[dev]"
```

Run tests:
```bash
pytest -v
```

---

## License

MIT — See [LICENSE](LICENSE) for details.

---

<div align="center">
  <p style="color:#64748b;font-size:14px;">
    Built for the agentic AI community · 
    <a href="https://github.com/shubhmartin107-web/evalforge">GitHub</a> · 
    <a href="https://huggingface.co/spaces">Try on HF Spaces</a>
  </p>
</div>
