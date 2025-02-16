test: ## run tests quickly with the default Python
	pdm run pytest -x --ff -l tests

lint:
	pdm run ruff check src tests && pdm run black --check --quiet src tests && pdm run mypy src tests
