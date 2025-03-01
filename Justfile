test: ## run tests quickly with the default Python
	uv run pytest -x --ff -l tests

lint:
	uv run ruff check src tests && uv run black --check src tests && uv run mypy src tests

docs:
	cd docs && make html
