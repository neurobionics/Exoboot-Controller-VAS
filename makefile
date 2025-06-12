SHELL = /bin/bash

.PHONY: lint

lint:
	pyclean .
	ruff check --fix
	pylint --recursive=y .
	mypy --install-types --non-interactive .
	mypy .
	bandit -c pyproject.toml -r .