# Changelog

All notable changes to EvalForge are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-30

### Added

- **Safety benchmarks**: sycophancy detection, bias detection, harmful output detection, jailbreak resistance (Sprint 3)
- **LLM-as-Judge**: Graders module with ModelGrader, CodeGrader, JudgeConfig; rubric, pairwise, and hybrid grading modes
- **pass@k / pass^k metrics**: Unbiased estimator (Chen et al. 2021); run_trials() in SDK
- **Enterprise providers**: Retry with exponential backoff + jitter for all providers; OpenAI provider
- **Anthropic provider**: Streaming, thinking blocks, tool use, cost tracking
- **Radar charts**: Spider/radar comparison view in the Compare tab (Sprint 4)
- **Dynamic data loading**: All dashboard tabs now load data lazily on tab selection (Sprint 4)
- **Pagination**: History tab paginates runs 25 per page with prev/next (Sprint 4)
- **Jinja2 HTML reports**: Proper Jinja2 template replaces fragile string-munging (Sprint 4)
- **Environment blocklist**: capture_env_snapshot() filters KEY/TOKEN/SECRET/PASSWORD/API (Sprint 3)
- **CI/CD**: GitHub Actions with test matrix, lint, import checks; dependabot config
- **Full documentation**: SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, architecture docs, integration guides

### Changed

- **Dual trace storage removed**: Steps stored only in `steps` table; `traces` metadata-only (Sprint 4)
- **FOREIGN KEY constraints removed** from SQLite schema; application-layer integrity only
- **Security posture**: Env var blocklist expanded; parameterized queries throughout

### Fixed

- Diagnostic metadata deserialization from string to dict in repository layer
- Harness now gracefully handles missing provider/agent config without ValueError
- Gemini API key moved from URL to `x-goog-api-key` header

## [0.1.0] - 2026-06-01

### Added

- Initial project skeleton (Phase 0)
- Pydantic models for all evaluation entities (Phase 1)
- SQLite storage with full CRUD (Phase 1)
- Core evaluation engine, harness, session recording (Phase 2)
- Diagnostics engine with 8 heuristic analyzers (Phase 3)
- Replay engine and JSON/Markdown/HTML exporters (Phase 4)
- Gradio dashboard with 6 tabs (Phase 5)
- Typer CLI and unified Python SDK (Phase 6)
- 7 built-in benchmark tasks across coding, research, tool-use (Phase 7)
- 92+ tests covering all core functionality (Phase 8)
