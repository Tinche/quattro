.PHONY: test lint

test: ## run tests quickly with the default Python
	pytest -x --ff -l tests

lint:
	black --check --quiet src tests && isort --check --quiet src tests && mypy src tests && flake8 src tests
