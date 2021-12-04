.PHONY: test lint

test: ## run tests quickly with the default Python
	pytest -x --ff tests

lint:
	black --check src tests --quiet && flake8 src tests && mypy src tests
