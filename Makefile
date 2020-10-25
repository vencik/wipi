.PHONY: setup init mypy test

setup:
	pyenv install --verbose --skip-existing
	pyenv local
	poetry config virtualenvs.in-project true

init:
	poetry install

mypy:
	poetry run mypy wipi --no-strict-optional --ignore-missing-imports --junit-xml=test/mypy.xml

test:
	poetry run pytest test --junit-xml=tests/results.xml
