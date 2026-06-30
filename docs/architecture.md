# EvalForge Architecture

## Overview

EvalForge is built as a modular, layered architecture designed for extensibility and clarity. Each layer has a single responsibility, and dependencies flow inward: UI → Engine → Models → Storage.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Dashboard│  │   CLI    │  │   SDK    │  │  Reports  │  │
│  │ (Gradio) │  │ (Typer)  │  │ (Python) │  │ (Export)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
└───────┼──────────────┼──────────────┼──────────────┼────────┘
        │              │              │              │
┌───────┼──────────────┼──────────────┼──────────────┼────────┐
│       ▼              ▼              ▼              ▼        │
│                    Core Engine                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Harness  │  │  Metrics │  │ Grading  │  │  Session  │  │
│  │          │  │          │  │          │  │ Recorder  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Providers Layer                          │   │
│  │  DeepSeek │ Gemini │ Groq │ Ollama │ Anthropic │ ... │   │
│  └──────────────────────────────────────────────────────┘   │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Diagnostics Layer                         │   │
│  │  Heuristics │ Analyzer │ Insights                     │   │
│  └──────────────────────────────────────────────────────┘   │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Replay Layer                              │   │
│  │  Player │ Renderer │ Exporter                         │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Storage Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ SQLite   │  │ Repos    │  │ Migrate  │                   │
│  │ (stdlib) │  │ (CRUD)   │  │          │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Evaluation Definition** — User defines an `Evaluation` with `TaskDefinition`s and `SuccessCriteria`
2. **Execution** — `EvaluationEngine` creates a `Run`, the `Harness` executes each task via a `Provider`
3. **Recording** — Every step is recorded by `SessionRecorder` into a `Trace` with full timing and cost
4. **Grading** — After execution, `grade_task` scores the output against `SuccessCriteria`
5. **Metrics** — `compute_metrics` calculates all run metrics from the trace
6. **Diagnostics** — `DiagnosticAnalyzer` runs heuristic analysis on the trace
7. **Replay** — `ReplayPlayer` loads the trace for step-through visualization
8. **Export** — `Exporter` converts runs to JSON, Markdown, or HTML

## Key Design Decisions

### SQLite over PostgreSQL
EvalForge uses SQLite (Python stdlib) for zero-dependency embedded storage. For single-user and small team usage, SQLite handles millions of rows efficiently. The repository pattern makes it trivial to swap in PostgreSQL or any other database.

### Gradio over React/Next.js
Gradio provides a production-quality UI built entirely in Python. No frontend build tooling, no npm, no separate deployment. This keeps the project accessible and maintainable while delivering a polished experience.

### Plugin Providers
The `ProviderBase` abstract class defines a simple interface: `chat()`, `count_tokens()`, and `from_env()`. Any LLM API can be integrated by implementing these three methods. Providers are instantiated via the `factory` module.

### Trace-first Architecture
Every evaluation run produces a complete `Trace` — a chronological list of `Step`s. This trace is the source of truth for metrics, diagnostics, replay, and export. This design enables all downstream features while keeping the data model simple.

## Module Reference

| Module | Responsibility |
|---|---|
| `core/engine.py` | Main orchestrator, manages evaluations and runs |
| `core/harness.py` | Task execution, agent interaction, error handling |
| `core/metrics.py` | RunMetrics and BenchmarkMetrics computation |
| `core/grading.py` | Success criteria evaluation (deterministic + LLM-as-judge) |
| `core/session.py` | Step recording, trace building, timing |
| `models/` | Pydantic data models for all entities |
| `storage/db.py` | SQLite connection management, schema creation |
| `storage/repository.py` | CRUD operations for all entity types |
| `providers/` | LLM API integrations (plugin architecture) |
| `diagnostics/` | Automated root-cause analysis |
| `replay/` | Session playback and export |
| `dashboard/` | Gradio UI components |
| `cli/` | Typer command-line interface |
| `benchmarks/` | Built-in benchmark task definitions |
