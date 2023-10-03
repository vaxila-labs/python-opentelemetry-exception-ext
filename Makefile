build:
	rm -rf dist/*
	python -m build

upload:
	twine upload --config-file ./.pypirc dist/*

test:
	pytest .

lint:
	pylint src/

black:
	black .

check_all: test lint black

local_install:
	pip install -e .
