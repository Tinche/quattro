python := ""
covcleanup := "true"

lint:
	uv run -p python3.13 --group lint ruff check src/ tests bench
	uv run -p python3.13 --group lint black --check src tests docs/conf.py
	uv run -p python3.13 --group lint mypy src tests 

test *args="-x --ff tests":
    uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test pytest {{args}}

testall:
    just python=python3.9 test
    just python=python3.10 test
    just python=python3.11 test
    just python=python3.12 test
    just python=python3.13 test
    just python=python3.14 test
    just python=pypy3.9 test

cov *args="-x --ff tests":
    uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test coverage run -m pytest {{args}}
    {{ if covcleanup == "true" { "uv run coverage combine" } else { "" } }}
    {{ if covcleanup == "true" { "uv run coverage report" } else { "" } }}
    {{ if covcleanup == "true" { "@rm .coverage*" } else { "" } }}

covall:
    just python=python3.9 covcleanup=false cov
    just python=python3.10 covcleanup=false cov
    just python=python3.11 covcleanup=false cov
    just python=python3.12 covcleanup=false cov
    just python=python3.13 covcleanup=false cov
    just python=python3.14 covcleanup=false cov
    just python=pypy3.10 covcleanup=false cov
    uv run coverage combine
    uv run coverage report
    @rm .coverage*

docs:
	cd docs && make html
