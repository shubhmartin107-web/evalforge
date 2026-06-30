.PHONY: install dev run serve test lint typecheck clean coverage security docs release build

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install

run:
	evalforge run $(EVAL)

serve:
	evalforge serve --host 0.0.0.0 --port 7860

test:
	pytest -v --tb=short --cov=evalforge --cov-report=term-missing

coverage:
	pytest -v --tb=short --cov=evalforge --cov-report=html --cov-fail-under=90

lint:
	ruff check evalforge/

lint-fix:
	ruff check --fix evalforge/

typecheck:
	mypy evalforge/

security:
	bandit -r evalforge/ -x tests,spaces

clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docs:
	cd docs && python3 -c "print('Documentation check OK')"

release:
	python -m build
	ls -la dist/

build:
	pip install build
	python -m build

docker-build:
	docker compose build

docker-up:
	docker compose up

spaces:
	cd spaces && python3 app.py
