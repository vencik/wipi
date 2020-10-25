.PHONY: setup init

setup:
	pyenv install --verbose --skip-existing
	pyenv local
	poetry config virtualenvs.in-project true

init:
	poetry install
