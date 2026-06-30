# Contributing to EvalForge

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Create a feature branch: `git checkout -b feature/my-feature`

## Development

Run tests before submitting:
```bash
python3 -m pytest tests/ -v --tb=short
```

Run linting:
```bash
ruff check evalforge/
```

Type checking:
```bash
mypy evalforge/
```

## Code Style

- Follow existing code patterns
- Type-annotate all function signatures
- Avoid adding comments unless necessary for clarity
- Keep functions focused and small
- Write tests for new features

## Pull Request Process

1. Ensure all tests pass
2. Add tests for any new functionality
3. Update documentation if needed
4. Submit a PR with a clear description of the changes
